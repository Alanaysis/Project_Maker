#pragma once

/**
 * @file dns_resolver.h
 * @brief DNS 解析器实现
 *
 * 实现 DNS 解析功能，包括：
 * - 递归解析
 * - 迭代解析
 * - 反向解析
 * - 转发机制
 */

#include "../protocol/dns_message.h"
#include "dns_cache.h"
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <optional>

namespace dns {

// ============================================================================
// 解析器配置
// ============================================================================

struct ResolverConfig {
    std::vector<std::string> forwarders;      // 转发服务器
    std::vector<std::string> root_servers;    // 根服务器
    bool enable_recursion = true;             // 启用递归
    bool enable_cache = true;                 // 启用缓存
    size_t max_retries = 3;                   // 最大重试次数
    std::chrono::seconds query_timeout{5};    // 查询超时
    size_t max_cname_depth = 10;              // CNAME 最大深度
    size_t max_redirects = 16;                // 最大重定向次数
};

// ============================================================================
// 解析结果
// ============================================================================

struct ResolveResult {
    ResponseCode status = ResponseCode::NO_ERROR;
    std::vector<ResourceRecord> answers;      // 回答记录
    std::vector<ResourceRecord> authorities;  // 授权记录
    std::vector<ResourceRecord> additionals;  // 附加记录
    bool from_cache = false;                  // 是否来自缓存
    std::chrono::milliseconds resolve_time{0}; // 解析耗时

    // 获取第一个 A 记录
    std::optional<std::string> get_a_record() const;

    // 获取第一个 AAAA 记录
    std::optional<std::string> get_aaaa_record() const;

    // 获取所有 MX 记录 (按优先级排序)
    std::vector<std::pair<uint16_t, std::string>> get_mx_records() const;

    // 获取第一个 CNAME 记录
    std::optional<std::string> get_cname_record() const;
};

// ============================================================================
// DNS 查询器 (底层网络查询)
// ============================================================================

class DnsQuerier {
public:
    DnsQuerier();
    ~DnsQuerier();

    // 发送 UDP 查询
    std::optional<DnsMessage> query_udp(const std::string& server,
                                         const DnsMessage& query,
                                         std::chrono::seconds timeout);

    // 发送 TCP 查询
    std::optional<DnsMessage> query_tcp(const std::string& server,
                                         const DnsMessage& query,
                                         std::chrono::seconds timeout);

    // 自动选择协议查询 (UDP 优先，截断时回退到 TCP)
    std::optional<DnsMessage> query(const std::string& server,
                                     const DnsMessage& query,
                                     std::chrono::seconds timeout);

private:
    // 创建 UDP 套接字
    int create_udp_socket(const std::string& server, uint16_t port);

    // 创建 TCP 套接字
    int create_tcp_socket(const std::string& server, uint16_t port);
};

// ============================================================================
// DNS 解析器
// ============================================================================

class DnsResolver {
public:
    explicit DnsResolver(const ResolverConfig& config = ResolverConfig{});
    ~DnsResolver();

    // 递归解析
    ResolveResult resolve(const std::string& name, RecordType type);

    // 迭代解析
    ResolveResult resolve_iterative(const std::string& name, RecordType type);

    // 反向解析 (IP -> 域名)
    ResolveResult reverse_resolve(const std::string& ip_addr);

    // 通过转发器解析
    ResolveResult resolve_via_forwarder(const std::string& name,
                                         RecordType type);

    // 清除缓存
    void clear_cache();

    // 获取缓存统计
    CacheStats get_cache_stats() const;

private:
    // 递归解析内部实现
    ResolveResult resolve_recursive(const std::string& name,
                                     RecordType type,
                                     size_t depth);

    // 查询权威服务器
    ResolveResult query_authoritative(const std::string& zone,
                                       const std::vector<ResourceRecord>& ns_records,
                                       const std::string& name,
                                       RecordType type);

    // 追踪 CNAME
    ResolveResult follow_cname(const std::string& cname_target,
                                RecordType type,
                                size_t depth);

    // 查找负责指定域名的权威服务器
    std::vector<ResourceRecord> find_authority(const std::string& name);

    // 提取 glue records
    std::vector<ResourceRecord> extract_glue_records(
        const std::vector<ResourceRecord>& ns_records,
        const std::vector<ResourceRecord>& additionals);

    ResolverConfig config_;
    DnsQuerier querier_;
    std::unique_ptr<DnsCache> cache_;
};

} // namespace dns
