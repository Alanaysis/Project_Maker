#pragma once

/**
 * @file access_control.h
 * @brief DNS 访问控制和安全特性
 *
 * 实现：
 * - TSIG 认证
 * - 访问控制列表 (ACL)
 * - 速率限制
 * - 查询过滤
 */

#include "../protocol/dns_message.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <mutex>
#include <chrono>
#include <atomic>
#include <functional>
#include <memory>

namespace dns {

// ============================================================================
// TSIG 认证 (RFC 2845)
// ============================================================================

/**
 * TSIG 算法
 */
enum class TsigAlgorithm {
    HMAC_MD5,
    HMAC_SHA1,
    HMAC_SHA256,
    HMAC_SHA512,
};

const char* tsig_algorithm_to_string(TsigAlgorithm algo);
TsigAlgorithm string_to_tsig_algorithm(const std::string& str);

/**
 * TSIG 密钥
 */
struct TsigKey {
    std::string name;               // 密钥名称
    TsigAlgorithm algorithm;        // 算法
    std::vector<uint8_t> secret;    // 密钥数据

    // 计算 HMAC
    std::vector<uint8_t> compute_hmac(const std::vector<uint8_t>& data) const;
};

/**
 * TSIG 记录
 */
struct TsigRecord {
    std::string key_name;           // 密钥名称
    uint64_t time_signed = 0;       // 签名时间
    uint16_t fudge = 300;           // 时间容差 (秒)
    std::vector<uint8_t> mac;       // MAC 值
    uint16_t original_id = 0;       // 原始事务 ID
    uint16_t error = 0;             // 错误码
    std::vector<uint8_t> other;     // 其他数据

    // 序列化为 RDATA
    std::vector<uint8_t> serialize() const;

    // 反序列化
    static std::optional<TsigRecord> deserialize(
        std::span<const uint8_t> data);
};

class TsigAuth {
public:
    TsigAuth() = default;
    ~TsigAuth() = default;

    // 添加密钥
    bool add_key(const TsigKey& key);

    // 删除密钥
    bool remove_key(const std::string& key_name);

    // 签名报文
    bool sign_message(DnsMessage& message, const std::string& key_name);

    // 验证报文
    bool verify_message(const DnsMessage& message);

    // 获取密钥
    const TsigKey* get_key(const std::string& key_name) const;

private:
    mutable std::mutex mutex_;
    std::unordered_map<std::string, TsigKey> keys_;
};

// ============================================================================
// 访问控制列表 (ACL)
// ============================================================================

/**
 * ACL 动作
 */
enum class AclAction {
    ALLOW,  // 允许
    DENY,   // 拒绝
    RECURSE_ONLY,  // 仅允许递归
};

/**
 * ACL 规则
 */
struct AclRule {
    std::string name;               // 规则名称
    AclAction action;               // 动作
    std::vector<std::string> networks;  // 网络列表 (CIDR)
    std::vector<RecordType> record_types;  // 允许的记录类型 (空=全部)
    bool allow_transfer = false;    // 允许区域传输
    bool allow_update = false;      // 允许动态更新
};

/**
 * ACL 管理器
 */
class AccessControlList {
public:
    AccessControlList() = default;
    ~AccessControlList() = default;

    // 添加规则
    void add_rule(const AclRule& rule);

    // 删除规则
    bool remove_rule(const std::string& name);

    // 检查查询权限
    bool check_query(const std::string& client_ip,
                     RecordType type) const;

    // 检查区域传输权限
    bool check_transfer(const std::string& client_ip) const;

    // 检查动态更新权限
    bool check_update(const std::string& client_ip) const;

    // 获取默认动作
    AclAction default_action() const { return default_action_; }

    // 设置默认动作
    void set_default_action(AclAction action) { default_action_ = action; }

private:
    // IP 匹配
    bool match_network(const std::string& ip,
                       const std::string& network) const;

    mutable std::mutex mutex_;
    std::vector<AclRule> rules_;
    AclAction default_action_ = AclAction::ALLOW;
};

// ============================================================================
// 速率限制
// ============================================================================

/**
 * 速率限制配置
 */
struct RateLimitConfig {
    size_t queries_per_second = 1000;    // 每秒查询数
    size_t queries_per_client = 100;     // 每客户端每秒查询数
    size_t burst_size = 50;              // 突发大小
    std::chrono::seconds window{1};      // 时间窗口
    size_t max_entries = 100000;         // 最大跟踪条目数
    std::chrono::seconds cleanup_interval{60};  // 清理间隔
};

/**
 * 速率限制器
 */
class RateLimiter {
public:
    explicit RateLimiter(const RateLimitConfig& config = RateLimitConfig{});
    ~RateLimiter();

    // 检查是否允许查询
    bool allow_query(const std::string& client_ip);

    // 检查全局速率
    bool check_global_rate();

    // 重置计数器
    void reset(const std::string& client_ip);

    // 清除所有计数器
    void clear();

    // 获取统计信息
    struct Stats {
        uint64_t total_allowed = 0;
        uint64_t total_denied = 0;
        size_t active_clients = 0;
    };
    Stats get_stats() const;

private:
    // 客户端速率跟踪
    struct ClientRate {
        size_t count = 0;
        std::chrono::steady_clock::time_point window_start;
        size_t burst_used = 0;
    };

    void cleanup_expired();

    RateLimitConfig config_;

    mutable std::mutex mutex_;
    std::unordered_map<std::string, ClientRate> client_rates_;
    size_t global_count_ = 0;
    std::chrono::steady_clock::time_point global_window_start_;

    std::atomic<uint64_t> total_allowed_{0};
    std::atomic<uint64_t> total_denied_{0};
};

// ============================================================================
// 查询过滤器
// ============================================================================

/**
 * 过滤规则类型
 */
enum class FilterAction {
    PASS,       // 通过
    DROP,       // 丢弃
    REFUSE,     // 拒绝 (返回 REFUSED)
    NXDOMAIN,   // 返回 NXDOMAIN
};

/**
 * 过滤规则
 */
struct FilterRule {
    std::string name;               // 规则名称
    FilterAction action;            // 动作
    std::vector<std::string> patterns;  // 匹配模式 (域名通配符)
    std::vector<RecordType> record_types;  // 记录类型过滤
};

/**
 * 查询过滤器
 */
class QueryFilter {
public:
    QueryFilter() = default;
    ~QueryFilter() = default;

    // 添加过滤规则
    void add_rule(const FilterRule& rule);

    // 删除过滤规则
    bool remove_rule(const std::string& name);

    // 检查查询
    FilterAction check(const std::string& name, RecordType type) const;

    // 加载黑名单文件
    bool load_blacklist(const std::string& filename);

    // 加载白名单文件
    bool load_whitelist(const std::string& filename);

private:
    // 通配符匹配
    bool match_pattern(const std::string& name,
                       const std::string& pattern) const;

    mutable std::mutex mutex_;
    std::vector<FilterRule> rules_;
    std::unordered_set<std::string> blacklist_;
    std::unordered_set<std::string> whitelist_;
};

} // namespace dns
