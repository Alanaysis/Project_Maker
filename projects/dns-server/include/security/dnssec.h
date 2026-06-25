#pragma once

/**
 * @file dnssec.h
 * @brief DNSSEC 安全扩展
 *
 * 实现 DNSSEC 功能，包括：
 * - DNSKEY 记录
 * - RRSIG 记录
 * - DS 记录
 * - NSEC/NSEC3 记录
 * - 签名验证
 */

#include "../protocol/dns_message.h"
#include <string>
#include <vector>
#include <memory>
#include <cstdint>

namespace dns {

// ============================================================================
// DNSSEC 常量
// ============================================================================

constexpr uint8_t DNSSEC_ALGORITHM_RSASHA256 = 8;
constexpr uint8_t DNSSEC_ALGORITHM_RSASHA512 = 10;
constexpr uint8_t DNSSEC_ALGORITHM_ECDSAP256SHA256 = 13;
constexpr uint8_t DNSSEC_ALGORITHM_ECDSAP384SHA384 = 14;

constexpr uint8_t DNSSEC_DIGEST_SHA1 = 1;
constexpr uint8_t DNSSEC_DIGEST_SHA256 = 2;

// ============================================================================
// DNSSEC 记录类型 (扩展 RecordType)
// ============================================================================

enum class DnssecRecordType : uint16_t {
    DNSKEY = 48,
    RRSIG  = 46,
    DS     = 43,
    NSEC   = 47,
    NSEC3  = 50,
    NSEC3PARAM = 51,
};

// ============================================================================
// DNSKEY 记录
// ============================================================================

/**
 * DNSKEY 记录格式
 *
 *   0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    FLAGS                         |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |   PROTOCOL   |           ALGORITHM               |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * /                    PUBLIC KEY                     /
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 */
struct DnskeyRecord {
    uint16_t flags = 256;       // 标志 (256=ZSK, 257=KSK)
    uint8_t protocol = 3;       // 协议 (必须为 3)
    uint8_t algorithm = DNSSEC_ALGORITHM_RSASHA256;  // 算法
    std::vector<uint8_t> public_key;  // 公钥

    // 序列化
    std::vector<uint8_t> serialize() const;

    // 反序列化
    static std::optional<DnskeyRecord> deserialize(
        std::span<const uint8_t> data);

    // 计算密钥标签 (Key Tag)
    uint16_t key_tag() const;

    // 是否为 KSK (Key Signing Key)
    bool is_ksk() const { return flags & 0x0001; }

    // 是否为 ZSK (Zone Signing Key)
    bool is_zsk() const { return !(flags & 0x0001); }
};

// ============================================================================
// RRSIG 记录
// ============================================================================

/**
 * RRSIG 记录格式
 *
 *   0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    TYPE COVERED                   |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |           ALGORITHM      |       LABELS          |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    ORIGINAL TTL                   |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                SIGNATURE EXPIRATION               |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                SIGNATURE INCEPTION                |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    KEY TAG                         |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * /                   SIGNER'S NAME                   /
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * /                    SIGNATURE                      /
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 */
struct RrsigRecord {
    RecordType type_covered = RecordType::A;  // 覆盖的类型
    uint8_t algorithm = DNSSEC_ALGORITHM_RSASHA256;
    uint8_t labels = 0;               // 原始域名标签数
    uint32_t original_ttl = 0;        // 原始 TTL
    uint32_t signature_expiration = 0;  // 签名过期时间
    uint32_t signature_inception = 0;   // 签名开始时间
    uint16_t key_tag = 0;             // 密钥标签
    DnsName signer;                   // 签名者域名
    std::vector<uint8_t> signature;   // 签名数据

    // 序列化
    std::vector<uint8_t> serialize() const;

    // 反序列化
    static std::optional<RrsigRecord> deserialize(
        std::span<const uint8_t> data);

    // 检查签名是否有效 (时间范围)
    bool is_valid() const;
};

// ============================================================================
// DS 记录
// ============================================================================

/**
 * DS 记录格式
 *
 *   0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |                    KEY TAG                         |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * |           ALGORITHM      |       DIGEST TYPE      |
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 * /                      DIGEST                       /
 * +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 */
struct DsRecord {
    uint16_t key_tag = 0;           // 密钥标签
    uint8_t algorithm = DNSSEC_ALGORITHM_RSASHA256;
    uint8_t digest_type = DNSSEC_DIGEST_SHA256;
    std::vector<uint8_t> digest;    // 摘要

    // 序列化
    std::vector<uint8_t> serialize() const;

    // 反序列化
    static std::optional<DsRecord> deserialize(std::span<const uint8_t> data);

    // 计算 DS 记录 (从 DNSKEY)
    static DsRecord compute(const DnsName& name, const DnskeyRecord& key,
                            uint8_t digest_type = DNSSEC_DIGEST_SHA256);
};

// ============================================================================
// NSEC 记录 (Authenticated Denial of Existence)
// ============================================================================

struct NsecRecord {
    DnsName next_domain;               // 下一个域名
    std::vector<RecordType> types;     // 存在的记录类型

    // 序列化
    std::vector<uint8_t> serialize() const;

    // 反序列化
    static std::optional<NsecRecord> deserialize(std::span<const uint8_t> data);
};

// ============================================================================
// DNSSEC 签名器
// ============================================================================

class DnssecSigner {
public:
    DnssecSigner() = default;
    ~DnssecSigner() = default;

    // 生成密钥对
    struct KeyPair {
        DnskeyRecord public_key;
        std::vector<uint8_t> private_key;
    };
    static std::optional<KeyPair> generate_key(
        const DnsName& zone_name,
        uint8_t algorithm = DNSSEC_ALGORITHM_RSASHA256,
        bool is_ksk = false);

    // 签名记录集
    static std::optional<ResourceRecord> sign_rrset(
        const std::vector<ResourceRecord>& rrset,
        const DnskeyRecord& key,
        const std::vector<uint8_t>& private_key,
        uint32_t ttl);

    // 生成 DS 记录
    static ResourceRecord generate_ds(const DnsName& name,
                                       const DnskeyRecord& key);

    // 生成 NSEC 记录链
    static std::vector<ResourceRecord> generate_nsec_chain(
        const std::string& zone_name,
        const std::vector<std::string>& domain_names);
};

// ============================================================================
// DNSSEC 验证器
// ============================================================================

class DnssecValidator {
public:
    DnssecValidator() = default;
    ~DnssecValidator() = default;

    // 验证 RRSET 签名
    static bool verify_rrsig(const std::vector<ResourceRecord>& rrset,
                              const ResourceRecord& rrsig_record,
                              const ResourceRecord& dnskey_record);

    // 验证 DS 记录链
    static bool verify_ds_chain(const DsRecord& ds,
                                 const DnskeyRecord& dnskey);

    // 验证 NSEC 记录
    static bool verify_nsec(const std::string& query_name,
                             RecordType query_type,
                             const std::vector<ResourceRecord>& nsec_records);

    // 验证响应
    static bool verify_response(const DnsMessage& response,
                                 const std::vector<ResourceRecord>& trust_anchors);

private:
    // 验证 RSA 签名
    static bool verify_rsa(const std::vector<uint8_t>& data,
                            const std::vector<uint8_t>& signature,
                            const std::vector<uint8_t>& public_key);

    // 验证 ECDSA 签名
    static bool verify_ecdsa(const std::vector<uint8_t>& data,
                              const std::vector<uint8_t>& signature,
                              const std::vector<uint8_t>& public_key);

    // 计算摘要
    static std::vector<uint8_t> compute_digest(
        const std::vector<uint8_t>& data, uint8_t algorithm);
};

} // namespace dns
