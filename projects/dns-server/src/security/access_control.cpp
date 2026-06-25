/**
 * @file access_control.cpp
 * @brief DNS 访问控制和安全特性实现
 *
 * 实现：
 * - TSIG 认证
 * - 访问控制列表 (ACL)
 * - 速率限制
 * - 查询过滤
 */

#include "security/access_control.h"
#include "monitoring/dns_monitor.h"

#include <openssl/hmac.h>
#include <openssl/evp.h>
#include <arpa/inet.h>
#include <algorithm>
#include <fstream>
#include <sstream>

namespace dns {

// ============================================================================
// TSIG 算法转换
// ============================================================================

const char* tsig_algorithm_to_string(TsigAlgorithm algo) {
    switch (algo) {
        case TsigAlgorithm::HMAC_MD5:    return "HMAC-MD5";
        case TsigAlgorithm::HMAC_SHA1:   return "HMAC-SHA1";
        case TsigAlgorithm::HMAC_SHA256: return "HMAC-SHA256";
        case TsigAlgorithm::HMAC_SHA512: return "HMAC-SHA512";
        default:                         return "UNKNOWN";
    }
}

TsigAlgorithm string_to_tsig_algorithm(const std::string& str) {
    if (str == "HMAC-MD5") return TsigAlgorithm::HMAC_MD5;
    if (str == "HMAC-SHA1") return TsigAlgorithm::HMAC_SHA1;
    if (str == "HMAC-SHA256") return TsigAlgorithm::HMAC_SHA256;
    if (str == "HMAC-SHA512") return TsigAlgorithm::HMAC_SHA512;
    return TsigAlgorithm::HMAC_MD5;
}

// ============================================================================
// TsigKey 实现
// ============================================================================

std::vector<uint8_t> TsigKey::compute_hmac(
    const std::vector<uint8_t>& data) const {
    const EVP_MD* md = nullptr;
    switch (algorithm) {
        case TsigAlgorithm::HMAC_MD5:    md = EVP_md5(); break;
        case TsigAlgorithm::HMAC_SHA1:   md = EVP_sha1(); break;
        case TsigAlgorithm::HMAC_SHA256: md = EVP_sha256(); break;
        case TsigAlgorithm::HMAC_SHA512: md = EVP_sha512(); break;
    }

    unsigned int len = EVP_MAX_MD_SIZE;
    std::vector<uint8_t> result(len);

    HMAC(md, secret.data(), static_cast<int>(secret.size()),
         data.data(), data.size(), result.data(), &len);

    result.resize(len);
    return result;
}

// ============================================================================
// TsigRecord 实现
// ============================================================================

std::vector<uint8_t> TsigRecord::serialize() const {
    std::vector<uint8_t> data;

    // Key Name
    DnsName key_name_obj(key_name);
    auto name_data = key_name_obj.serialize();
    data.insert(data.end(), name_data.begin(), name_data.end());

    // Time Signed (48 bits)
    data.push_back(static_cast<uint8_t>((time_signed >> 40) & 0xFF));
    data.push_back(static_cast<uint8_t>((time_signed >> 32) & 0xFF));
    data.push_back(static_cast<uint8_t>((time_signed >> 24) & 0xFF));
    data.push_back(static_cast<uint8_t>((time_signed >> 16) & 0xFF));
    data.push_back(static_cast<uint8_t>((time_signed >> 8) & 0xFF));
    data.push_back(static_cast<uint8_t>(time_signed & 0xFF));

    // Fudge
    data.push_back(static_cast<uint8_t>((fudge >> 8) & 0xFF));
    data.push_back(static_cast<uint8_t>(fudge & 0xFF));

    // MAC Size
    uint16_t mac_size = static_cast<uint16_t>(mac.size());
    data.push_back(static_cast<uint8_t>((mac_size >> 8) & 0xFF));
    data.push_back(static_cast<uint8_t>(mac_size & 0xFF));

    // MAC
    data.insert(data.end(), mac.begin(), mac.end());

    // Original ID
    data.push_back(static_cast<uint8_t>((original_id >> 8) & 0xFF));
    data.push_back(static_cast<uint8_t>(original_id & 0xFF));

    // Error
    data.push_back(static_cast<uint8_t>((error >> 8) & 0xFF));
    data.push_back(static_cast<uint8_t>(error & 0xFF));

    // Other Len
    uint16_t other_len = static_cast<uint16_t>(other.size());
    data.push_back(static_cast<uint8_t>((other_len >> 8) & 0xFF));
    data.push_back(static_cast<uint8_t>(other_len & 0xFF));

    // Other Data
    data.insert(data.end(), other.begin(), other.end());

    return data;
}

std::optional<TsigRecord> TsigRecord::deserialize(
    std::span<const uint8_t> data) {
    if (data.size() < 16) {
        return std::nullopt;
    }

    TsigRecord tsig;
    size_t pos = 0;

    // Key Name
    auto name_result = DnsName::deserialize(data, pos);
    if (!name_result) return std::nullopt;
    tsig.key_name = name_result->first.to_string();
    pos += name_result->second;

    if (pos + 10 > data.size()) return std::nullopt;

    // Time Signed
    tsig.time_signed = (static_cast<uint64_t>(data[pos]) << 40) |
                       (static_cast<uint64_t>(data[pos + 1]) << 32) |
                       (static_cast<uint64_t>(data[pos + 2]) << 24) |
                       (static_cast<uint64_t>(data[pos + 3]) << 16) |
                       (static_cast<uint64_t>(data[pos + 4]) << 8) |
                       static_cast<uint64_t>(data[pos + 5]);
    pos += 6;

    // Fudge
    tsig.fudge = (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1];
    pos += 2;

    // MAC Size
    uint16_t mac_size = (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1];
    pos += 2;

    if (pos + mac_size > data.size()) return std::nullopt;

    // MAC
    tsig.mac.assign(data.begin() + pos, data.begin() + pos + mac_size);
    pos += mac_size;

    if (pos + 6 > data.size()) return std::nullopt;

    // Original ID
    tsig.original_id = (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1];
    pos += 2;

    // Error
    tsig.error = (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1];
    pos += 2;

    // Other Len
    uint16_t other_len = (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1];
    pos += 2;

    if (pos + other_len > data.size()) return std::nullopt;

    // Other Data
    tsig.other.assign(data.begin() + pos, data.begin() + pos + other_len);

    return tsig;
}

// ============================================================================
// TsigAuth 实现
// ============================================================================

bool TsigAuth::add_key(const TsigKey& key) {
    std::lock_guard<std::mutex> lock(mutex_);
    keys_[key.name] = key;
    return true;
}

bool TsigAuth::remove_key(const std::string& key_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    return keys_.erase(key_name) > 0;
}

bool TsigAuth::sign_message(DnsMessage& message, const std::string& key_name) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = keys_.find(key_name);
    if (it == keys_.end()) {
        return false;
    }

    const auto& key = it->second;

    // 创建 TSIG 记录
    TsigRecord tsig;
    tsig.key_name = key_name;
    tsig.time_signed = std::chrono::system_clock::now()
        .time_since_epoch().count() / 1000000;
    tsig.original_id = message.header().id;

    // 计算 MAC
    auto message_data = message.serialize();
    tsig.mac = key.compute_hmac(message_data);

    // 添加 TSIG 到附加记录
    ResourceRecord rr;
    rr.name = DnsName(key_name);
    rr.type = RecordType::OPT;  // 使用 OPT 类型表示 TSIG
    rr.rclass = QueryClass::ANY;
    rr.ttl = 0;
    rr.rdata = tsig.serialize();
    rr.rdlength = static_cast<uint16_t>(
        std::get<std::vector<uint8_t>>(rr.rdata).size());

    message.add_additional(rr);

    return true;
}

bool TsigAuth::verify_message(const DnsMessage& message) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 查找 TSIG 记录
    for (const auto& rr : message.additionals()) {
        if (rr.type == RecordType::OPT &&
            std::holds_alternative<std::vector<uint8_t>>(rr.rdata)) {
            auto tsig_data = std::get<std::vector<uint8_t>>(rr.rdata);
            auto tsig = TsigRecord::deserialize(tsig_data);
            if (!tsig) continue;

            auto it = keys_.find(tsig->key_name);
            if (it == keys_.end()) continue;

            const auto& key = it->second;

            // 验证 MAC
            auto message_data = message.serialize();
            auto expected_mac = key.compute_hmac(message_data);

            if (tsig->mac == expected_mac) {
                // 检查时间
                auto now = std::chrono::system_clock::now()
                    .time_since_epoch().count() / 1000000;
                int64_t diff = std::abs(static_cast<int64_t>(now) -
                                        static_cast<int64_t>(tsig->time_signed));
                if (diff <= tsig->fudge) {
                    return true;
                }
            }
        }
    }

    return false;
}

const TsigKey* TsigAuth::get_key(const std::string& key_name) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = keys_.find(key_name);
    if (it != keys_.end()) {
        return &it->second;
    }
    return nullptr;
}

// ============================================================================
// AccessControlList 实现
// ============================================================================

void AccessControlList::add_rule(const AclRule& rule) {
    std::lock_guard<std::mutex> lock(mutex_);
    rules_.push_back(rule);
}

bool AccessControlList::remove_rule(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = std::find_if(rules_.begin(), rules_.end(),
        [&name](const AclRule& r) { return r.name == name; });

    if (it != rules_.end()) {
        rules_.erase(it);
        return true;
    }
    return false;
}

bool AccessControlList::check_query(const std::string& client_ip,
                                      RecordType type) const {
    std::lock_guard<std::mutex> lock(mutex_);

    for (const auto& rule : rules_) {
        for (const auto& network : rule.networks) {
            if (match_network(client_ip, network)) {
                if (rule.action == AclAction::DENY) {
                    return false;
                }
                if (rule.action == AclAction::ALLOW) {
                    if (rule.record_types.empty()) {
                        return true;
                    }
                    for (auto allowed_type : rule.record_types) {
                        if (allowed_type == type) {
                            return true;
                        }
                    }
                    return false;
                }
            }
        }
    }

    return default_action_ == AclAction::ALLOW;
}

bool AccessControlList::check_transfer(const std::string& client_ip) const {
    std::lock_guard<std::mutex> lock(mutex_);

    for (const auto& rule : rules_) {
        if (!rule.allow_transfer) continue;
        for (const auto& network : rule.networks) {
            if (match_network(client_ip, network)) {
                return true;
            }
        }
    }

    return false;
}

bool AccessControlList::check_update(const std::string& client_ip) const {
    std::lock_guard<std::mutex> lock(mutex_);

    for (const auto& rule : rules_) {
        if (!rule.allow_update) continue;
        for (const auto& network : rule.networks) {
            if (match_network(client_ip, network)) {
                return true;
            }
        }
    }

    return false;
}

bool AccessControlList::match_network(const std::string& ip,
                                        const std::string& network) const {
    // 简化实现：支持简单的 IP 匹配
    if (network == "any" || network == "0.0.0.0/0") {
        return true;
    }

    // 检查是否有 CIDR
    auto slash_pos = network.find('/');
    if (slash_pos == std::string::npos) {
        return ip == network;
    }

    // CIDR 匹配
    std::string network_ip = network.substr(0, slash_pos);
    int prefix_len = std::stoi(network.substr(slash_pos + 1));

    struct in_addr addr1, addr2;
    inet_pton(AF_INET, ip.c_str(), &addr1);
    inet_pton(AF_INET, network_ip.c_str(), &addr2);

    uint32_t mask = htonl(~((1 << (32 - prefix_len)) - 1));
    return (addr1.s_addr & mask) == (addr2.s_addr & mask);
}

// ============================================================================
// RateLimiter 实现
// ============================================================================

RateLimiter::RateLimiter(const RateLimitConfig& config)
    : config_(config) {
    global_window_start_ = std::chrono::steady_clock::now();
}

RateLimiter::~RateLimiter() {}

bool RateLimiter::allow_query(const std::string& client_ip) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto now = std::chrono::steady_clock::now();

    auto it = client_rates_.find(client_ip);
    if (it == client_rates_.end()) {
        // 新客户端
        if (client_rates_.size() >= config_.max_entries) {
            cleanup_expired();
        }
        client_rates_[client_ip] = {1, now, 1};
        total_allowed_++;
        return true;
    }

    auto& rate = it->second;
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
        now - rate.window_start);

    if (elapsed >= config_.window) {
        // 重置窗口
        rate.count = 1;
        rate.window_start = now;
        rate.burst_used = 1;
        total_allowed_++;
        return true;
    }

    // 检查突发限制
    if (rate.burst_used >= config_.burst_size) {
        total_denied_++;
        return false;
    }

    // 检查速率限制
    if (rate.count >= config_.queries_per_client) {
        total_denied_++;
        return false;
    }

    rate.count++;
    rate.burst_used++;
    total_allowed_++;
    return true;
}

bool RateLimiter::check_global_rate() {
    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
        now - global_window_start_);

    if (elapsed >= config_.window) {
        global_count_ = 0;
        global_window_start_ = now;
    }

    if (global_count_ >= config_.queries_per_second) {
        return false;
    }

    global_count_++;
    return true;
}

void RateLimiter::reset(const std::string& client_ip) {
    std::lock_guard<std::mutex> lock(mutex_);
    client_rates_.erase(client_ip);
}

void RateLimiter::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    client_rates_.clear();
    global_count_ = 0;
}

RateLimiter::Stats RateLimiter::get_stats() const {
    Stats stats;
    stats.total_allowed = total_allowed_.load();
    stats.total_denied = total_denied_.load();
    stats.active_clients = client_rates_.size();
    return stats;
}

void RateLimiter::cleanup_expired() {
    auto now = std::chrono::steady_clock::now();

    for (auto it = client_rates_.begin(); it != client_rates_.end();) {
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - it->second.window_start);
        if (elapsed > config_.cleanup_interval) {
            it = client_rates_.erase(it);
        } else {
            ++it;
        }
    }
}

// ============================================================================
// QueryFilter 实现
// ============================================================================

void QueryFilter::add_rule(const FilterRule& rule) {
    std::lock_guard<std::mutex> lock(mutex_);
    rules_.push_back(rule);
}

bool QueryFilter::remove_rule(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = std::find_if(rules_.begin(), rules_.end(),
        [&name](const FilterRule& r) { return r.name == name; });

    if (it != rules_.end()) {
        rules_.erase(it);
        return true;
    }
    return false;
}

FilterAction QueryFilter::check(const std::string& name,
                                  RecordType type) const {
    std::lock_guard<std::mutex> lock(mutex_);

    // 检查黑名单
    if (blacklist_.count(name)) {
        return FilterAction::REFUSE;
    }

    // 检查白名单
    if (!whitelist_.empty() && !whitelist_.count(name)) {
        return FilterAction::REFUSE;
    }

    // 检查过滤规则
    for (const auto& rule : rules_) {
        for (const auto& pattern : rule.patterns) {
            if (match_pattern(name, pattern)) {
                if (!rule.record_types.empty()) {
                    bool type_match = false;
                    for (auto rt : rule.record_types) {
                        if (rt == type) {
                            type_match = true;
                            break;
                        }
                    }
                    if (!type_match) continue;
                }
                return rule.action;
            }
        }
    }

    return FilterAction::PASS;
}

bool QueryFilter::load_blacklist(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        return false;
    }

    std::string line;
    while (std::getline(file, line)) {
        if (line.empty() || line[0] == '#') continue;
        blacklist_.insert(line);
    }

    return true;
}

bool QueryFilter::load_whitelist(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        return false;
    }

    std::string line;
    while (std::getline(file, line)) {
        if (line.empty() || line[0] == '#') continue;
        whitelist_.insert(line);
    }

    return true;
}

bool QueryFilter::match_pattern(const std::string& name,
                                  const std::string& pattern) const {
    // 简单的通配符匹配
    if (pattern == "*") return true;

    if (pattern.front() == '*') {
        std::string suffix = pattern.substr(1);
        if (name.length() >= suffix.length()) {
            return name.compare(name.length() - suffix.length(),
                                suffix.length(), suffix) == 0;
        }
        return false;
    }

    return name == pattern;
}

} // namespace dns
