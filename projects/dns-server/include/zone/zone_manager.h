#pragma once

/**
 * @file zone_manager.h
 * @brief DNS 区域管理
 *
 * 实现 DNS 区域管理功能，包括：
 * - 区域文件解析
 * - 区域传输 (AXFR/IXFR)
 * - 动态更新
 * - SOA 记录管理
 */

#include "../protocol/dns_message.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <filesystem>

namespace dns {

// ============================================================================
// 区域类型
// ============================================================================

enum class ZoneType {
    PRIMARY,    // 主区域
    SECONDARY,  // 从区域
    STUB,       // 存根区域
    FORWARD,    // 转发区域
};

const char* zone_type_to_string(ZoneType type);

// ============================================================================
// SOA 记录数据
// ============================================================================

struct SoaData {
    DnsName mname;        // 主域名服务器
    DnsName rname;        // 管理员邮箱
    uint32_t serial = 0;  // 序列号
    uint32_t refresh = 3600;  // 刷新间隔 (秒)
    uint32_t retry = 900;     // 重试间隔 (秒)
    uint32_t expire = 604800; // 过期时间 (秒)
    uint32_t minimum = 86400; // 最小 TTL (秒)

    // 序列化为 RDATA
    std::vector<uint8_t> serialize() const;

    // 反序列化
    static std::optional<SoaData> deserialize(std::span<const uint8_t> data);

    // 递增序列号
    void increment_serial();
};

// ============================================================================
// 区域配置
// ============================================================================

struct ZoneConfig {
    std::string zone_file;              // 区域文件路径
    ZoneType type = ZoneType::PRIMARY;  // 区域类型
    std::string zone_name;              // 区域名称
    bool allow_transfer = false;        // 允许区域传输
    std::vector<std::string> transfer_allowed;  // 允许传输的 IP
    bool allow_update = false;          // 允许动态更新
    std::vector<std::string> update_allowed;    // 允许更新的 IP
};

// ============================================================================
// 区域数据
// ============================================================================

class Zone {
public:
    explicit Zone(const std::string& name, ZoneType type = ZoneType::PRIMARY);
    ~Zone() = default;

    // 获取区域名称
    const std::string& name() const { return name_; }

    // 获取区域类型
    ZoneType type() const { return type_; }

    // 获取 SOA 记录
    std::optional<ResourceRecord> get_soa() const;

    // 设置 SOA 记录
    void set_soa(const SoaData& soa);

    // 获取记录
    std::vector<ResourceRecord> get_records(const std::string& name,
                                             RecordType type) const;

    // 获取指定域名的所有记录
    std::vector<ResourceRecord> get_all_records(const std::string& name) const;

    // 添加记录
    bool add_record(const ResourceRecord& record);

    // 删除记录
    bool remove_record(const std::string& name, RecordType type);

    // 删除指定记录
    bool remove_record(const ResourceRecord& record);

    // 获取所有记录 (用于区域传输)
    std::vector<ResourceRecord> get_all_records() const;

    // 获取记录数量
    size_t record_count() const;

    // 检查域名是否存在
    bool has_name(const std::string& name) const;

    // 增加序列号
    void increment_serial();

private:
    std::string name_;
    ZoneType type_;
    SoaData soa_data_;
    mutable std::mutex mutex_;

    // 记录存储: name -> type -> records
    using RecordMap = std::unordered_map<
        RecordType, std::vector<ResourceRecord>>;
    std::unordered_map<std::string, RecordMap> records_;
};

// ============================================================================
// 区域文件解析器
// ============================================================================

class ZoneFileParser {
public:
    ZoneFileParser() = default;
    ~ZoneFileParser() = default;

    // 解析区域文件
    std::optional<std::unique_ptr<Zone>> parse(const std::string& filename);

    // 解析区域文件内容
    std::optional<std::unique_ptr<Zone>> parse_string(
        const std::string& content,
        const std::string& zone_name);

    // 获取错误信息
    const std::string& error_message() const { return error_msg_; }

private:
    // 解析单行记录
    std::optional<ResourceRecord> parse_line(const std::string& line,
                                              const std::string& origin,
                                              uint32_t default_ttl);

    // 展开域名
    std::string expand_name(const std::string& name,
                            const std::string& origin,
                            const std::string& current) const;

    // 解析 TTL
    std::optional<uint32_t> parse_ttl(const std::string& str) const;

    // 解析 RDATA
    std::optional<RdataVariant> parse_rdata(RecordType type,
                                             const std::vector<std::string>& tokens,
                                             const std::string& origin) const;

    std::string error_msg_;
};

// ============================================================================
// 区域传输
// ============================================================================

/**
 * 区域传输类型
 * - AXFR: 全量传输 (RFC 5936)
 * - IXFR: 增量传输 (RFC 1995)
 */
enum class TransferType {
    AXFR,  // 全量传输
    IXFR,  // 增量传输
};

class ZoneTransfer {
public:
    ZoneTransfer() = default;
    ~ZoneTransfer() = default;

    // 执行 AXFR 传输
    std::optional<std::unique_ptr<Zone>> axfr(const std::string& server,
                                               const std::string& zone_name);

    // 执行 IXFR 传输
    std::optional<std::vector<ResourceRecord>> ixfr(
        const std::string& server,
        const std::string& zone_name,
        uint32_t known_serial);

    // 发送 AXFR 请求 (服务端处理)
    static std::vector<DnsMessage> handle_axfr_request(
        const DnsMessage& request,
        const Zone& zone);

    // 发送 IXFR 请求 (服务端处理)
    static std::vector<DnsMessage> handle_ixfr_request(
        const DnsMessage& request,
        const Zone& zone,
        uint32_t client_serial);

private:
    // 通过 TCP 发送查询
    std::optional<DnsMessage> send_tcp_query(const std::string& server,
                                              const DnsMessage& query);
};

// ============================================================================
// 动态更新 (RFC 2136)
// ============================================================================

class DynamicUpdate {
public:
    DynamicUpdate() = default;
    ~DynamicUpdate() = default;

    // 处理动态更新请求
    static ResponseCode handle_update(const DnsMessage& request,
                                       Zone& zone);

private:
    // 预检更新部分
    static ResponseCode check_prerequisites(
        const std::vector<ResourceRecord>& prerequisites,
        const Zone& zone);

    // 执行更新
    static ResponseCode apply_updates(
        const std::vector<ResourceRecord>& updates,
        const std::vector<ResourceRecord>& additions,
        Zone& zone);
};

// ============================================================================
// 区域管理器
// ============================================================================

class ZoneManager {
public:
    ZoneManager() = default;
    ~ZoneManager() = default;

    // 加载区域文件
    bool load_zone(const ZoneConfig& config);

    // 添加区域
    bool add_zone(std::unique_ptr<Zone> zone);

    // 删除区域
    bool remove_zone(const std::string& zone_name);

    // 获取区域
    Zone* get_zone(const std::string& zone_name);

    // 查找负责指定域名的区域
    Zone* find_zone(const std::string& name);

    // 查询记录
    std::vector<ResourceRecord> query(const std::string& name,
                                       RecordType type);

    // 获取所有区域名称
    std::vector<std::string> get_zone_names() const;

    // 区域传输请求处理
    std::vector<DnsMessage> handle_transfer(const std::string& zone_name,
                                             TransferType type,
                                             uint32_t client_serial = 0);

    // 动态更新处理
    ResponseCode handle_update(const std::string& zone_name,
                                const DnsMessage& request);

    // 保存区域到文件
    bool save_zone(const std::string& zone_name,
                   const std::string& filename);

    // 重新加载区域
    bool reload_zone(const std::string& zone_name);

private:
    mutable std::mutex mutex_;
    std::unordered_map<std::string, std::unique_ptr<Zone>> zones_;
    std::unordered_map<std::string, ZoneConfig> configs_;
};

} // namespace dns
