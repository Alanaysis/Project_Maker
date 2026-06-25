#pragma once

/**
 * @file dns_message.h
 * @brief DNS 报文格式定义
 *
 * 实现 DNS 协议的核心报文结构，包括：
 * - DNS 报头 (Header)
 * - 查询部分 (Question)
 * - 资源记录 (Resource Record)
 * - 报文序列化/反序列化
 *
 * 参考: RFC 1035 - Domain Names - Implementation and Specification
 */

#include <cstdint>
#include <string>
#include <vector>
#include <array>
#include <memory>
#include <span>
#include <optional>
#include <variant>

namespace dns {

// ============================================================================
// DNS 报文常量
// ============================================================================

constexpr uint16_t DNS_PORT = 53;
constexpr uint16_t DNS_HEADER_SIZE = 12;
constexpr uint16_t DNS_MAX_UDP_SIZE = 512;
constexpr uint16_t DNS_MAX_MESSAGE_SIZE = 4096;
constexpr uint16_t DNS_LABEL_MAX_LENGTH = 63;
constexpr uint16_t DNS_NAME_MAX_LENGTH = 255;

// ============================================================================
// DNS 记录类型 (RFC 1035, RFC 3596, RFC 2782, etc.)
// ============================================================================

enum class RecordType : uint16_t {
    A       = 1,    // IPv4 地址
    NS      = 2,    // 域名服务器
    CNAME   = 5,    // 规范名称
    SOA     = 6,    // 授权开始
    PTR     = 12,   // 指针记录 (反向解析)
    MX      = 15,   // 邮件交换
    TXT     = 16,   // 文本记录
    AAAA    = 28,   // IPv6 地址
    SRV     = 33,   // 服务记录
    OPT     = 41,   // EDNS0 选项
    AXFR    = 252,  // 区域传输 (全量)
    IXFR    = 253,  // 区域传输 (增量)
    ANY     = 255,  // 任意记录
};

// DNS 记录类型字符串转换
const char* record_type_to_string(RecordType type);
RecordType string_to_record_type(const std::string& str);

// ============================================================================
// DNS 查询类 (QCLASS)
// ============================================================================

enum class QueryClass : uint16_t {
    IN  = 1,    // Internet
    CS  = 2,    // CSNET (已废弃)
    CH  = 3,    // Chaos
    HS  = 4,    // Hesiod
    ANY = 255,  // 任意类
};

// ============================================================================
// DNS 响应码 (RCODE)
// ============================================================================

enum class ResponseCode : uint8_t {
    NO_ERROR        = 0,  // 无错误
    FORMAT_ERROR    = 1,  // 报文格式错误
    SERVER_FAILURE  = 2,  // 服务器失败
    NAME_ERROR      = 3,  // 域名不存在 (NXDOMAIN)
    NOT_IMPLEMENTED = 4,  // 未实现
    REFUSED         = 5,  // 拒绝查询
};

const char* response_code_to_string(ResponseCode code);

// ============================================================================
// DNS 操作码 (OPCODE)
// ============================================================================

enum class Opcode : uint8_t {
    QUERY  = 0,  // 标准查询
    IQUERY = 1,  // 反向查询 (已废弃)
    STATUS = 2,  // 服务器状态请求
    NOTIFY = 4,  // 区域变更通知 (RFC 1996)
    UPDATE = 5,  // 动态更新 (RFC 2136)
};

// ============================================================================
// DNS 报头 (Header)
// ============================================================================

/**
 * DNS 报头结构 (12 字节)
 *
 *   0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                      ID                         |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE    |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    QDCOUNT                       |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    ANCOUNT                       |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    NSCOUNT                       |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    ARCOUNT                       |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 */
struct DnsHeader {
    uint16_t id = 0;           // 事务 ID
    bool qr = false;           // 查询/响应标志 (0=查询, 1=响应)
    Opcode opcode = Opcode::QUERY;  // 操作码
    bool aa = false;           // 授权回答
    bool tc = false;           // 截断标志
    bool rd = false;           // 期望递归
    bool ra = false;           // 可用递归
    uint8_t z = 0;             // 保留字段 (必须为 0)
    ResponseCode rcode = ResponseCode::NO_ERROR;  // 响应码
    uint16_t qdcount = 0;     // 查询数
    uint16_t ancount = 0;     // 回答数
    uint16_t nscount = 0;     // 授权数
    uint16_t arcount = 0;     // 附加数

    // 序列化为网络字节序
    std::vector<uint8_t> serialize() const;

    // 从网络字节序反序列化
    static std::optional<DnsHeader> deserialize(std::span<const uint8_t> data);
};

// ============================================================================
// DNS 域名 (Name)
// ============================================================================

/**
 * DNS 域名表示
 *
 * 支持两种编码格式：
 * - 标签序列: [length][label]...[0]
 * - 压缩指针: [0xC0][offset]
 */
class DnsName {
public:
    DnsName() = default;
    explicit DnsName(const std::string& name);

    // 获取域名字符串
    const std::string& to_string() const { return name_; }

    // 设置域名
    void set(const std::string& name);

    // 检查是否为空
    bool empty() const { return name_.empty() || name_ == "."; }

    // 获取标签数
    size_t label_count() const;

    // 获取父域名
    DnsName parent() const;

    // 序列化 (支持压缩)
    std::vector<uint8_t> serialize(bool compress = false,
                                    size_t offset = 0) const;

    // 从缓冲区反序列化
    static std::optional<std::pair<DnsName, size_t>>
    deserialize(std::span<const uint8_t> data, size_t offset);

    // 比较操作
    bool operator==(const DnsName& other) const;
    bool operator!=(const DnsName& other) const { return !(*this == other); }
    bool operator<(const DnsName& other) const;

    // 大小写不敏感比较
    static bool equal_ignore_case(const DnsName& a, const DnsName& b);

private:
    std::string name_;
    static std::string to_lower(const std::string& s);
};

// ============================================================================
// DNS 查询部分 (Question)
// ============================================================================

struct DnsQuestion {
    DnsName name;                      // 查询域名
    RecordType type = RecordType::A;   // 查询类型
    QueryClass qclass = QueryClass::IN; // 查询类

    // 序列化
    std::vector<uint8_t> serialize(bool compress = false,
                                    size_t offset = 0) const;

    // 反序列化
    static std::optional<std::pair<DnsQuestion, size_t>>
    deserialize(std::span<const uint8_t> data, size_t offset);
};

// ============================================================================
// DNS 资源记录 (Resource Record)
// ============================================================================

/**
 * RDATA 变体类型
 */
using RdataVariant = std::variant<
    std::monostate,           // 空
    std::array<uint8_t, 4>,   // A 记录 (IPv4)
    std::array<uint8_t, 16>,  // AAAA 记录 (IPv6)
    DnsName,                  // NS, CNAME 记录
    std::vector<uint8_t>      // 其他 (MX, TXT, SRV, SOA 等)
>;

struct ResourceRecord {
    DnsName name;                       // 记录名称
    RecordType type = RecordType::A;    // 记录类型
    QueryClass rclass = QueryClass::IN; // 记录类
    uint32_t ttl = 0;                   // 生存时间 (秒)
    uint16_t rdlength = 0;              // RDATA 长度
    RdataVariant rdata;                 // 记录数据

    // 序列化
    std::vector<uint8_t> serialize(bool compress = false,
                                    size_t offset = 0) const;

    // 反序列化
    static std::optional<std::pair<ResourceRecord, size_t>>
    deserialize(std::span<const uint8_t> data, size_t offset);

    // 获取 RDATA 的原始字节
    std::vector<uint8_t> get_rdata_bytes() const;

    // 解析 RDATA 为可读字符串
    std::string rdata_to_string() const;
};

// ============================================================================
// DNS 报文 (Message)
// ============================================================================

class DnsMessage {
public:
    DnsMessage() = default;

    // 访问器
    DnsHeader& header() { return header_; }
    const DnsHeader& header() const { return header_; }

    std::vector<DnsQuestion>& questions() { return questions_; }
    const std::vector<DnsQuestion>& questions() const { return questions_; }

    std::vector<ResourceRecord>& answers() { return answers_; }
    const std::vector<ResourceRecord>& answers() const { return answers_; }

    std::vector<ResourceRecord>& authorities() { return authorities_; }
    const std::vector<ResourceRecord>& authorities() const { return authorities_; }

    std::vector<ResourceRecord>& additionals() { return additionals_; }
    const std::vector<ResourceRecord>& additionals() const { return additionals_; }

    // 序列化为完整的 DNS 报文
    std::vector<uint8_t> serialize() const;

    // 从字节流反序列化
    static std::optional<DnsMessage> deserialize(std::span<const uint8_t> data);

    // 创建查询报文
    static DnsMessage create_query(const std::string& name,
                                    RecordType type,
                                    bool rd = true);

    // 创建响应报文
    static DnsMessage create_response(const DnsMessage& query,
                                       ResponseCode rcode);

    // 添加回答记录
    void add_answer(ResourceRecord rr);

    // 添加授权记录
    void add_authority(ResourceRecord rr);

    // 添加附加记录
    void add_additional(ResourceRecord rr);

    // 设置为响应
    void set_response(ResponseCode rcode = ResponseCode::NO_ERROR);

    // 调试输出
    std::string to_string() const;

private:
    DnsHeader header_;
    std::vector<DnsQuestion> questions_;
    std::vector<ResourceRecord> answers_;
    std::vector<ResourceRecord> authorities_;
    std::vector<ResourceRecord> additionals_;
};

} // namespace dns
