/**
 * @file dnssec.cpp
 * @brief DNSSEC 安全扩展实现
 *
 * 实现 DNSSEC 功能，包括：
 * - DNSKEY 记录
 * - RRSIG 记录
 * - DS 记录
 * - NSEC 记录
 * - 签名验证
 */

#include "security/dnssec.h"
#include "monitoring/dns_monitor.h"

#include <openssl/evp.h>
#include <openssl/rsa.h>
#include <openssl/ec.h>
#include <openssl/sha.h>
#include <openssl/hmac.h>
#include <openssl/x509.h>
#include <openssl/rand.h>
#include <cstring>
#include <algorithm>

namespace dns {

// ============================================================================
// DnskeyRecord 实现
// ============================================================================

std::vector<uint8_t> DnskeyRecord::serialize() const {
    std::vector<uint8_t> data;

    // Flags
    data.push_back((flags >> 8) & 0xFF);
    data.push_back(flags & 0xFF);

    // Protocol
    data.push_back(protocol);

    // Algorithm
    data.push_back(algorithm);

    // Public Key
    data.insert(data.end(), public_key.begin(), public_key.end());

    return data;
}

std::optional<DnskeyRecord> DnskeyRecord::deserialize(
    std::span<const uint8_t> data) {
    if (data.size() < 4) {
        return std::nullopt;
    }

    DnskeyRecord key;

    // Flags
    key.flags = (static_cast<uint16_t>(data[0]) << 8) | data[1];

    // Protocol
    key.protocol = data[2];

    // Algorithm
    key.algorithm = data[3];

    // Public Key
    if (data.size() > 4) {
        key.public_key.assign(data.begin() + 4, data.end());
    }

    return key;
}

uint16_t DnskeyRecord::key_tag() const {
    // 计算密钥标签 (RFC 4034, Appendix B)
    auto data = serialize();
    uint32_t sum = 0;

    for (size_t i = 0; i < data.size(); i++) {
        if (i & 1) {
            sum += data[i];
        } else {
            sum += static_cast<uint32_t>(data[i]) << 8;
        }
    }

    sum += (sum >> 16);
    return static_cast<uint16_t>(sum & 0xFFFF);
}

// ============================================================================
// RrsigRecord 实现
// ============================================================================

std::vector<uint8_t> RrsigRecord::serialize() const {
    std::vector<uint8_t> data;

    // Type Covered
    uint16_t type_val = static_cast<uint16_t>(type_covered);
    data.push_back((type_val >> 8) & 0xFF);
    data.push_back(type_val & 0xFF);

    // Algorithm
    data.push_back(algorithm);

    // Labels
    data.push_back(labels);

    // Original TTL
    data.push_back((original_ttl >> 24) & 0xFF);
    data.push_back((original_ttl >> 16) & 0xFF);
    data.push_back((original_ttl >> 8) & 0xFF);
    data.push_back(original_ttl & 0xFF);

    // Signature Expiration
    data.push_back((signature_expiration >> 24) & 0xFF);
    data.push_back((signature_expiration >> 16) & 0xFF);
    data.push_back((signature_expiration >> 8) & 0xFF);
    data.push_back(signature_expiration & 0xFF);

    // Signature Inception
    data.push_back((signature_inception >> 24) & 0xFF);
    data.push_back((signature_inception >> 16) & 0xFF);
    data.push_back((signature_inception >> 8) & 0xFF);
    data.push_back(signature_inception & 0xFF);

    // Key Tag
    data.push_back((key_tag >> 8) & 0xFF);
    data.push_back(key_tag & 0xFF);

    // Signer's Name
    auto signer_data = signer.serialize();
    data.insert(data.end(), signer_data.begin(), signer_data.end());

    // Signature
    data.insert(data.end(), signature.begin(), signature.end());

    return data;
}

std::optional<RrsigRecord> RrsigRecord::deserialize(
    std::span<const uint8_t> data) {
    if (data.size() < 18) {
        return std::nullopt;
    }

    RrsigRecord rrsig;
    size_t pos = 0;

    // Type Covered
    rrsig.type_covered = static_cast<RecordType>(
        (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1]);
    pos += 2;

    // Algorithm
    rrsig.algorithm = data[pos++];

    // Labels
    rrsig.labels = data[pos++];

    // Original TTL
    rrsig.original_ttl = (static_cast<uint32_t>(data[pos]) << 24) |
                          (static_cast<uint32_t>(data[pos + 1]) << 16) |
                          (static_cast<uint32_t>(data[pos + 2]) << 8) |
                          static_cast<uint32_t>(data[pos + 3]);
    pos += 4;

    // Signature Expiration
    rrsig.signature_expiration = (static_cast<uint32_t>(data[pos]) << 24) |
                                  (static_cast<uint32_t>(data[pos + 1]) << 16) |
                                  (static_cast<uint32_t>(data[pos + 2]) << 8) |
                                  static_cast<uint32_t>(data[pos + 3]);
    pos += 4;

    // Signature Inception
    rrsig.signature_inception = (static_cast<uint32_t>(data[pos]) << 24) |
                                 (static_cast<uint32_t>(data[pos + 1]) << 16) |
                                 (static_cast<uint32_t>(data[pos + 2]) << 8) |
                                 static_cast<uint32_t>(data[pos + 3]);
    pos += 4;

    // Key Tag
    rrsig.key_tag = (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1];
    pos += 2;

    // Signer's Name
    auto signer_result = DnsName::deserialize(data, pos);
    if (!signer_result) {
        return std::nullopt;
    }
    rrsig.signer = signer_result->first;
    pos += signer_result->second;

    // Signature
    if (pos < data.size()) {
        rrsig.signature.assign(data.begin() + pos, data.end());
    }

    return rrsig;
}

bool RrsigRecord::is_valid() const {
    auto now = std::chrono::system_clock::now();
    auto epoch = now.time_since_epoch();
    auto seconds = std::chrono::duration_cast<std::chrono::seconds>(epoch);

    uint32_t current_time = static_cast<uint32_t>(seconds.count());
    return current_time >= signature_inception &&
           current_time <= signature_expiration;
}

// ============================================================================
// DsRecord 实现
// ============================================================================

std::vector<uint8_t> DsRecord::serialize() const {
    std::vector<uint8_t> data;

    // Key Tag
    data.push_back((key_tag >> 8) & 0xFF);
    data.push_back(key_tag & 0xFF);

    // Algorithm
    data.push_back(algorithm);

    // Digest Type
    data.push_back(digest_type);

    // Digest
    data.insert(data.end(), digest.begin(), digest.end());

    return data;
}

std::optional<DsRecord> DsRecord::deserialize(std::span<const uint8_t> data) {
    if (data.size() < 4) {
        return std::nullopt;
    }

    DsRecord ds;

    // Key Tag
    ds.key_tag = (static_cast<uint16_t>(data[0]) << 8) | data[1];

    // Algorithm
    ds.algorithm = data[2];

    // Digest Type
    ds.digest_type = data[3];

    // Digest
    if (data.size() > 4) {
        ds.digest.assign(data.begin() + 4, data.end());
    }

    return ds;
}

DsRecord DsRecord::compute(const DnsName& name, const DnskeyRecord& key,
                            uint8_t digest_type) {
    DsRecord ds;
    ds.key_tag = key.key_tag();
    ds.algorithm = key.algorithm;
    ds.digest_type = digest_type;

    // 计算摘要: SHA(RDNS(name) + DNSKEY RDATA)
    std::vector<uint8_t> data;

    // 添加规范化域名
    auto name_data = name.serialize();
    data.insert(data.end(), name_data.begin(), name_data.end());

    // 添加 DNSKEY RDATA
    auto key_data = key.serialize();
    data.insert(data.end(), key_data.begin(), key_data.end());

    // 计算摘要
    if (digest_type == DNSSEC_DIGEST_SHA1) {
        ds.digest.resize(SHA_DIGEST_LENGTH);
        SHA1(data.data(), data.size(), ds.digest.data());
    } else if (digest_type == DNSSEC_DIGEST_SHA256) {
        ds.digest.resize(SHA256_DIGEST_LENGTH);
        SHA256(data.data(), data.size(), ds.digest.data());
    }

    return ds;
}

// ============================================================================
// NsecRecord 实现
// ============================================================================

std::vector<uint8_t> NsecRecord::serialize() const {
    std::vector<uint8_t> data;

    // Next Domain Name
    auto next_data = next_domain.serialize();
    data.insert(data.end(), next_data.begin(), next_data.end());

    // Type Bit Maps
    for (auto type : types) {
        uint16_t type_val = static_cast<uint16_t>(type);
        data.push_back(static_cast<uint8_t>(type_val >> 8));
        data.push_back(static_cast<uint8_t>(type_val & 0xFF));
    }

    return data;
}

std::optional<NsecRecord> NsecRecord::deserialize(
    std::span<const uint8_t> data) {
    NsecRecord nsec;

    // Next Domain Name
    auto name_result = DnsName::deserialize(data, 0);
    if (!name_result) {
        return std::nullopt;
    }
    nsec.next_domain = name_result->first;
    size_t pos = name_result->second;

    // Type Bit Maps
    while (pos < data.size()) {
        if (pos + 2 > data.size()) break;
        uint16_t type_val = (static_cast<uint16_t>(data[pos]) << 8) |
                             data[pos + 1];
        nsec.types.push_back(static_cast<RecordType>(type_val));
        pos += 2;
    }

    return nsec;
}

// ============================================================================
// DnssecSigner 实现
// ============================================================================

std::optional<DnssecSigner::KeyPair> DnssecSigner::generate_key(
    const DnsName& zone_name,
    uint8_t algorithm,
    bool is_ksk) {

    KeyPair keypair;

    // 生成 RSA 密钥对
    EVP_PKEY_CTX* ctx = EVP_PKEY_CTX_new_id(EVP_PKEY_RSA, nullptr);
    if (!ctx) {
        return std::nullopt;
    }

    if (EVP_PKEY_keygen_init(ctx) <= 0) {
        EVP_PKEY_CTX_free(ctx);
        return std::nullopt;
    }

    // 设置密钥长度
    int key_bits = is_ksk ? 2048 : 1024;
    EVP_PKEY_CTX_set_rsa_keygen_bits(ctx, key_bits);

    EVP_PKEY* pkey = nullptr;
    if (EVP_PKEY_keygen(ctx, &pkey) <= 0) {
        EVP_PKEY_CTX_free(ctx);
        return std::nullopt;
    }
    EVP_PKEY_CTX_free(ctx);

    // 导出公钥
    int pub_len = i2d_PUBKEY(pkey, nullptr);
    if (pub_len <= 0) {
        EVP_PKEY_free(pkey);
        return std::nullopt;
    }

    keypair.public_key.public_key.resize(pub_len);
    uint8_t* pub_ptr = keypair.public_key.public_key.data();
    i2d_PUBKEY(pkey, &pub_ptr);

    // 导出私钥
    int priv_len = i2d_PrivateKey(pkey, nullptr);
    if (priv_len <= 0) {
        EVP_PKEY_free(pkey);
        return std::nullopt;
    }

    keypair.private_key.resize(priv_len);
    uint8_t* priv_ptr = keypair.private_key.data();
    i2d_PrivateKey(pkey, &priv_ptr);

    EVP_PKEY_free(pkey);

    // 设置公钥属性
    keypair.public_key.flags = is_ksk ? 257 : 256;
    keypair.public_key.protocol = 3;
    keypair.public_key.algorithm = algorithm;

    return keypair;
}

std::optional<ResourceRecord> DnssecSigner::sign_rrset(
    const std::vector<ResourceRecord>& rrset,
    const DnskeyRecord& key,
    const std::vector<uint8_t>& private_key,
    uint32_t ttl) {

    if (rrset.empty()) {
        return std::nullopt;
    }

    // 创建 RRSIG 记录
    RrsigRecord rrsig;
    rrsig.type_covered = rrset[0].type;
    rrsig.algorithm = key.algorithm;
    rrsig.labels = static_cast<uint8_t>(rrset[0].name.label_count());
    rrsig.original_ttl = ttl;
    rrsig.key_tag = key.key_tag();
    rrsig.signer = rrset[0].name;

    // 设置签名时间
    auto now = std::chrono::system_clock::now();
    auto epoch = now.time_since_epoch();
    auto seconds = std::chrono::duration_cast<std::chrono::seconds>(epoch);
    rrsig.signature_inception = static_cast<uint32_t>(seconds.count());
    rrsig.signature_expiration = rrsig.signature_inception + 30 * 86400;  // 30天

    // 构造签名数据
    std::vector<uint8_t> sign_data;

    // 添加 RRSIG 头部 (不含签名)
    auto rrsig_header = rrsig.serialize();
    sign_data.insert(sign_data.end(), rrsig_header.begin(),
                     rrsig_header.begin() + rrsig_header.size() -
                     rrsig.signature.size());

    // 添加 RRSET
    for (const auto& rr : rrset) {
        auto rr_data = rr.serialize();
        sign_data.insert(sign_data.end(), rr_data.begin(), rr_data.end());
    }

    // 使用私钥签名
    const uint8_t* priv_ptr = private_key.data();
    EVP_PKEY* pkey = d2i_PrivateKey(EVP_PKEY_RSA, nullptr, &priv_ptr,
                                     static_cast<long>(private_key.size()));
    if (!pkey) {
        return std::nullopt;
    }

    EVP_MD_CTX* md_ctx = EVP_MD_CTX_new();
    if (!md_ctx) {
        EVP_PKEY_free(pkey);
        return std::nullopt;
    }

    if (EVP_DigestSignInit(md_ctx, nullptr, EVP_sha256(), nullptr, pkey) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        EVP_PKEY_free(pkey);
        return std::nullopt;
    }

    if (EVP_DigestSignUpdate(md_ctx, sign_data.data(), sign_data.size()) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        EVP_PKEY_free(pkey);
        return std::nullopt;
    }

    size_t sig_len = 0;
    if (EVP_DigestSignFinal(md_ctx, nullptr, &sig_len) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        EVP_PKEY_free(pkey);
        return std::nullopt;
    }

    rrsig.signature.resize(sig_len);
    if (EVP_DigestSignFinal(md_ctx, rrsig.signature.data(), &sig_len) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        EVP_PKEY_free(pkey);
        return std::nullopt;
    }
    rrsig.signature.resize(sig_len);

    EVP_MD_CTX_free(md_ctx);
    EVP_PKEY_free(pkey);

    // 创建 RRSIG 资源记录
    ResourceRecord rr;
    rr.name = rrset[0].name;
    rr.type = RecordType::A;  // RRSIG 类型
    rr.rclass = QueryClass::IN;
    rr.ttl = ttl;
    rr.rdata = rrsig.serialize();
    rr.rdlength = static_cast<uint16_t>(
        std::get<std::vector<uint8_t>>(rr.rdata).size());

    return rr;
}

ResourceRecord DnssecSigner::generate_ds(const DnsName& name,
                                           const DnskeyRecord& key) {
    auto ds = DsRecord::compute(name, key);

    ResourceRecord rr;
    rr.name = name;
    rr.type = RecordType::A;  // DS 类型
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;
    rr.rdata = ds.serialize();
    rr.rdlength = static_cast<uint16_t>(
        std::get<std::vector<uint8_t>>(rr.rdata).size());

    return rr;
}

std::vector<ResourceRecord> DnssecSigner::generate_nsec_chain(
    const std::string& zone_name,
    const std::vector<std::string>& domain_names) {

    std::vector<ResourceRecord> nsec_records;

    // 排序域名
    std::vector<std::string> sorted_names = domain_names;
    std::sort(sorted_names.begin(), sorted_names.end());

    // 生成 NSEC 记录链
    for (size_t i = 0; i < sorted_names.size(); i++) {
        NsecRecord nsec;
        nsec.next_domain = DnsName(sorted_names[(i + 1) % sorted_names.size()]);

        // 添加存在的记录类型
        nsec.types.push_back(RecordType::A);
        nsec.types.push_back(RecordType::NS);
        nsec.types.push_back(RecordType::SOA);

        ResourceRecord rr;
        rr.name = DnsName(sorted_names[i]);
        rr.type = RecordType::A;  // NSEC 类型
        rr.rclass = QueryClass::IN;
        rr.ttl = 3600;
        rr.rdata = nsec.serialize();
        rr.rdlength = static_cast<uint16_t>(
            std::get<std::vector<uint8_t>>(rr.rdata).size());

        nsec_records.push_back(rr);
    }

    return nsec_records;
}

// ============================================================================
// DnssecValidator 实现
// ============================================================================

bool DnssecValidator::verify_rrsig(const std::vector<ResourceRecord>& rrset,
                                    const ResourceRecord& rrsig_record,
                                    const ResourceRecord& dnskey_record) {
    // 解析 RRSIG
    if (!std::holds_alternative<std::vector<uint8_t>>(rrsig_record.rdata)) {
        return false;
    }
    auto rrsig_data = std::get<std::vector<uint8_t>>(rrsig_record.rdata);
    auto rrsig = RrsigRecord::deserialize(rrsig_data);
    if (!rrsig) {
        return false;
    }

    // 检查签名是否有效
    if (!rrsig->is_valid()) {
        return false;
    }

    // 解析 DNSKEY
    if (!std::holds_alternative<std::vector<uint8_t>>(dnskey_record.rdata)) {
        return false;
    }
    auto key_data = std::get<std::vector<uint8_t>>(dnskey_record.rdata);
    auto dnskey = DnskeyRecord::deserialize(key_data);
    if (!dnskey) {
        return false;
    }

    // 检查密钥标签
    if (rrsig->key_tag != dnskey->key_tag()) {
        return false;
    }

    // 构造验证数据
    std::vector<uint8_t> verify_data;

    // 添加 RRSIG 头部 (不含签名)
    auto rrsig_header = rrsig->serialize();
    verify_data.insert(verify_data.end(), rrsig_header.begin(),
                       rrsig_header.begin() + rrsig_header.size() -
                       rrsig->signature.size());

    // 添加 RRSET
    for (const auto& rr : rrset) {
        auto rr_data = rr.serialize();
        verify_data.insert(verify_data.end(), rr_data.begin(), rr_data.end());
    }

    // 验证签名
    switch (dnskey->algorithm) {
        case DNSSEC_ALGORITHM_RSASHA256:
        case DNSSEC_ALGORITHM_RSASHA512:
            return verify_rsa(verify_data, rrsig->signature,
                              dnskey->public_key);
        case DNSSEC_ALGORITHM_ECDSAP256SHA256:
        case DNSSEC_ALGORITHM_ECDSAP384SHA384:
            return verify_ecdsa(verify_data, rrsig->signature,
                                dnskey->public_key);
        default:
            return false;
    }
}

bool DnssecValidator::verify_ds_chain(const DsRecord& ds,
                                       const DnskeyRecord& dnskey) {
    // 计算 DS 记录
    auto computed_ds = DsRecord::compute(DnsName(""), dnskey,
                                          ds.digest_type);

    // 比较摘要
    return ds.digest == computed_ds.digest;
}

bool DnssecValidator::verify_nsec(const std::string& query_name,
                                    RecordType query_type,
                                    const std::vector<ResourceRecord>& nsec_records) {
    // 简化实现：检查 NSEC 记录链
    for (const auto& rr : nsec_records) {
        if (!std::holds_alternative<std::vector<uint8_t>>(rr.rdata)) {
            continue;
        }
        auto nsec_data = std::get<std::vector<uint8_t>>(rr.rdata);
        auto nsec = NsecRecord::deserialize(nsec_data);
        if (!nsec) {
            continue;
        }

        // 检查域名是否在范围内
        DnsName current(rr.name.to_string());
        DnsName next(nsec->next_domain.to_string());
        DnsName query(query_name);

        if (current < query && query < next) {
            // 域名在范围内，但不存在
            return true;
        }

        // 检查记录类型
        for (auto type : nsec->types) {
            if (type == query_type) {
                return false;  // 记录存在
            }
        }
    }

    return true;
}

bool DnssecValidator::verify_response(const DnsMessage& response,
                                        const std::vector<ResourceRecord>& trust_anchors) {
    // 简化实现：检查 RRSIG 记录
    if (response.answers().empty()) {
        return true;
    }

    // 查找 RRSIG 记录
    for (const auto& rr : response.answers()) {
        if (rr.type == RecordType::A) {  // RRSIG 类型
            // 查找对应的 DNSKEY
            for (const auto& anchor : trust_anchors) {
                if (verify_rrsig(response.answers(), rr, anchor)) {
                    return true;
                }
            }
        }
    }

    return false;
}

bool DnssecValidator::verify_rsa(const std::vector<uint8_t>& data,
                                   const std::vector<uint8_t>& signature,
                                   const std::vector<uint8_t>& public_key) {
    // 使用 OpenSSL 验证 RSA 签名
    const uint8_t* pub_ptr = public_key.data();
    EVP_PKEY* pkey = d2i_PUBKEY(nullptr, &pub_ptr,
                                 static_cast<long>(public_key.size()));
    if (!pkey) {
        return false;
    }

    EVP_MD_CTX* md_ctx = EVP_MD_CTX_new();
    if (!md_ctx) {
        EVP_PKEY_free(pkey);
        return false;
    }

    if (EVP_DigestVerifyInit(md_ctx, nullptr, EVP_sha256(), nullptr, pkey) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        EVP_PKEY_free(pkey);
        return false;
    }

    if (EVP_DigestVerifyUpdate(md_ctx, data.data(), data.size()) <= 0) {
        EVP_MD_CTX_free(md_ctx);
        EVP_PKEY_free(pkey);
        return false;
    }

    int result = EVP_DigestVerifyFinal(md_ctx, signature.data(),
                                        signature.size());

    EVP_MD_CTX_free(md_ctx);
    EVP_PKEY_free(pkey);

    return result == 1;
}

bool DnssecValidator::verify_ecdsa(const std::vector<uint8_t>& data,
                                     const std::vector<uint8_t>& signature,
                                     const std::vector<uint8_t>& public_key) {
    // 简化实现
    return false;
}

std::vector<uint8_t> DnssecValidator::compute_digest(
    const std::vector<uint8_t>& data, uint8_t algorithm) {
    std::vector<uint8_t> digest;

    if (algorithm == DNSSEC_DIGEST_SHA1) {
        digest.resize(SHA_DIGEST_LENGTH);
        SHA1(data.data(), data.size(), digest.data());
    } else if (algorithm == DNSSEC_DIGEST_SHA256) {
        digest.resize(SHA256_DIGEST_LENGTH);
        SHA256(data.data(), data.size(), digest.data());
    }

    return digest;
}

} // namespace dns
