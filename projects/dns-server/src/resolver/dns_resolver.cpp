/**
 * @file dns_resolver.cpp
 * @brief DNS 解析器实现
 *
 * 实现 DNS 解析功能，包括：
 * - 递归解析
 * - 迭代解析
 * - 反向解析
 * - 转发机制
 */

#include "resolver/dns_resolver.h"
#include "monitoring/dns_monitor.h"

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <netdb.h>
#include <cstring>
#include <algorithm>
#include <random>

namespace dns {

// ============================================================================
// ResolveResult 实现
// ============================================================================

std::optional<std::string> ResolveResult::get_a_record() const {
    for (const auto& rr : answers) {
        if (rr.type == RecordType::A &&
            std::holds_alternative<std::array<uint8_t, 4>>(rr.rdata)) {
            const auto& addr = std::get<std::array<uint8_t, 4>>(rr.rdata);
            char buf[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, addr.data(), buf, sizeof(buf));
            return std::string(buf);
        }
    }
    return std::nullopt;
}

std::optional<std::string> ResolveResult::get_aaaa_record() const {
    for (const auto& rr : answers) {
        if (rr.type == RecordType::AAAA &&
            std::holds_alternative<std::array<uint8_t, 16>>(rr.rdata)) {
            const auto& addr = std::get<std::array<uint8_t, 16>>(rr.rdata);
            char buf[INET6_ADDRSTRLEN];
            inet_ntop(AF_INET6, addr.data(), buf, sizeof(buf));
            return std::string(buf);
        }
    }
    return std::nullopt;
}

std::vector<std::pair<uint16_t, std::string>>
ResolveResult::get_mx_records() const {
    std::vector<std::pair<uint16_t, std::string>> mx_records;

    for (const auto& rr : answers) {
        if (rr.type == RecordType::MX &&
            std::holds_alternative<std::vector<uint8_t>>(rr.rdata)) {
            const auto& data = std::get<std::vector<uint8_t>>(rr.rdata);
            if (data.size() >= 2) {
                uint16_t preference = (static_cast<uint16_t>(data[0]) << 8) |
                                       data[1];
                auto name_result = DnsName::deserialize(data, 2);
                if (name_result) {
                    mx_records.emplace_back(preference,
                                            name_result->first.to_string());
                }
            }
        }
    }

    std::sort(mx_records.begin(), mx_records.end());
    return mx_records;
}

std::optional<std::string> ResolveResult::get_cname_record() const {
    for (const auto& rr : answers) {
        if (rr.type == RecordType::CNAME &&
            std::holds_alternative<DnsName>(rr.rdata)) {
            return std::get<DnsName>(rr.rdata).to_string();
        }
    }
    return std::nullopt;
}

// ============================================================================
// DnsQuerier 实现
// ============================================================================

DnsQuerier::DnsQuerier() {}

DnsQuerier::~DnsQuerier() {}

std::optional<DnsMessage> DnsQuerier::query_udp(
    const std::string& server,
    const DnsMessage& query,
    std::chrono::seconds timeout) {

    int sock = create_udp_socket(server, DNS_PORT);
    if (sock < 0) {
        return std::nullopt;
    }

    // 序列化查询
    auto data = query.serialize();

    // 发送查询
    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(DNS_PORT);
    inet_pton(AF_INET, server.c_str(), &addr.sin_addr);

    ssize_t sent = sendto(sock, data.data(), data.size(), 0,
                          reinterpret_cast<struct sockaddr*>(&addr),
                          sizeof(addr));
    if (sent < 0) {
        close(sock);
        return std::nullopt;
    }

    // 设置接收超时
    struct timeval tv{};
    tv.tv_sec = timeout.count();
    tv.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    // 接收响应
    uint8_t buffer[DNS_MAX_MESSAGE_SIZE];
    ssize_t received = recv(sock, buffer, sizeof(buffer), 0);
    close(sock);

    if (received <= 0) {
        return std::nullopt;
    }

    // 解析响应
    return DnsMessage::deserialize(
        std::span<const uint8_t>(buffer, received));
}

std::optional<DnsMessage> DnsQuerier::query_tcp(
    const std::string& server,
    const DnsMessage& query,
    std::chrono::seconds timeout) {

    int sock = create_tcp_socket(server, DNS_PORT);
    if (sock < 0) {
        return std::nullopt;
    }

    // 序列化查询
    auto data = query.serialize();

    // 发送长度前缀
    uint16_t length = htons(static_cast<uint16_t>(data.size()));
    if (send(sock, &length, 2, 0) < 0) {
        close(sock);
        return std::nullopt;
    }

    // 发送查询
    if (send(sock, data.data(), data.size(), 0) < 0) {
        close(sock);
        return std::nullopt;
    }

    // 设置接收超时
    struct timeval tv{};
    tv.tv_sec = timeout.count();
    tv.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    // 接收长度
    uint16_t resp_length;
    if (recv(sock, &resp_length, 2, MSG_WAITALL) != 2) {
        close(sock);
        return std::nullopt;
    }
    resp_length = ntohs(resp_length);

    // 接收响应
    std::vector<uint8_t> buffer(resp_length);
    ssize_t received = recv(sock, buffer.data(), resp_length, MSG_WAITALL);
    close(sock);

    if (received != resp_length) {
        return std::nullopt;
    }

    return DnsMessage::deserialize(buffer);
}

std::optional<DnsMessage> DnsQuerier::query(
    const std::string& server,
    const DnsMessage& query,
    std::chrono::seconds timeout) {

    // 先尝试 UDP
    auto response = query_udp(server, query, timeout);
    if (response && response->header().tc) {
        // UDP 响应被截断，回退到 TCP
        DNS_LOG_DEBUG("DnsQuerier", "UDP response truncated, falling back to TCP");
        response = query_tcp(server, query, timeout);
    }
    return response;
}

int DnsQuerier::create_udp_socket(const std::string& server, uint16_t port) {
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        return -1;
    }
    return sock;
}

int DnsQuerier::create_tcp_socket(const std::string& server, uint16_t port) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        return -1;
    }

    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    inet_pton(AF_INET, server.c_str(), &addr.sin_addr);

    if (connect(sock, reinterpret_cast<struct sockaddr*>(&addr),
                sizeof(addr)) < 0) {
        close(sock);
        return -1;
    }

    return sock;
}

// ============================================================================
// DnsResolver 实现
// ============================================================================

DnsResolver::DnsResolver(const ResolverConfig& config) : config_(config) {
    if (config.enable_cache) {
        cache_ = std::make_unique<DnsCache>();
    }

    // 设置默认根服务器
    if (config.root_servers.empty()) {
        config_.root_servers = {
            "198.41.0.4",      // a.root-servers.net
            "199.9.14.201",    // b.root-servers.net
            "192.33.4.12",     // c.root-servers.net
            "199.7.91.13",     // d.root-servers.net
            "192.203.230.10",  // e.root-servers.net
        };
    }
}

DnsResolver::~DnsResolver() {}

ResolveResult DnsResolver::resolve(const std::string& name, RecordType type) {
    auto start = std::chrono::steady_clock::now();

    // 检查缓存
    if (cache_) {
        auto cached = cache_->get(name, type);
        if (cached) {
            ResolveResult result;
            result.status = ResponseCode::NO_ERROR;
            result.answers = cached->records;
            result.from_cache = true;
            DNS_LOG_DEBUG("DnsResolver", "Cache hit for " + name);
            return result;
        }

        // 检查负缓存
        if (cache_->is_negative_cached(name, type)) {
            ResolveResult result;
            result.status = ResponseCode::NAME_ERROR;
            result.from_cache = true;
            return result;
        }
    }

    ResolveResult result;

    // 优先使用转发器
    if (!config_.forwarders.empty()) {
        result = resolve_via_forwarder(name, type);
        if (result.status == ResponseCode::NO_ERROR) {
            goto done;
        }
    }

    // 执行递归解析
    if (config_.enable_recursion) {
        result = resolve_recursive(name, type, 0);
    } else {
        // 迭代解析
        result = resolve_iterative(name, type);
    }

done:
    auto end = std::chrono::steady_clock::now();
    result.resolve_time = std::chrono::duration_cast<
        std::chrono::milliseconds>(end - start);

    // 缓存结果
    if (cache_ && result.status == ResponseCode::NO_ERROR &&
        !result.answers.empty()) {
        uint32_t min_ttl = UINT32_MAX;
        for (const auto& rr : result.answers) {
            min_ttl = std::min(min_ttl, rr.ttl);
        }
        cache_->put(name, type, result.answers, min_ttl);
    } else if (cache_ && result.status == ResponseCode::NAME_ERROR) {
        cache_->put_negative(name, type, ResponseCode::NAME_ERROR);
    }

    return result;
}

ResolveResult DnsResolver::resolve_recursive(const std::string& name,
                                              RecordType type,
                                              size_t depth) {
    // 防止无限递归
    if (depth > config_.max_cname_depth) {
        ResolveResult result;
        result.status = ResponseCode::SERVER_FAILURE;
        return result;
    }

    // 构造查询
    auto query = DnsMessage::create_query(name, type);

    // 查询根服务器
    std::vector<ResourceRecord> ns_records;
    for (const auto& root : config_.root_servers) {
        auto response = querier_.query(root, query, config_.query_timeout);
        if (response) {
            // 检查是否有回答
            if (!response->answers().empty()) {
                ResolveResult result;
                result.status = response->header().rcode;
                result.answers = response->answers();
                result.authorities = response->authorities();
                result.additionals = response->additionals();

                // 检查 CNAME
                if (type != RecordType::CNAME) {
                    for (const auto& rr : result.answers) {
                        if (rr.type == RecordType::CNAME &&
                            std::holds_alternative<DnsName>(rr.rdata)) {
                            auto cname = std::get<DnsName>(rr.rdata).to_string();
                            auto cname_result = follow_cname(cname, type,
                                                              depth + 1);
                            if (cname_result.status == ResponseCode::NO_ERROR) {
                                result.answers.insert(
                                    result.answers.end(),
                                    cname_result.answers.begin(),
                                    cname_result.answers.end());
                            }
                            break;
                        }
                    }
                }
                return result;
            }

            // 提取 NS 记录
            for (const auto& rr : response->authorities()) {
                if (rr.type == RecordType::NS) {
                    ns_records.push_back(rr);
                }
            }

            // 提取 glue records
            auto glue = extract_glue_records(ns_records,
                                              response->additionals());
            if (!glue.empty()) {
                // 使用 glue records 查询
                for (const auto& g : glue) {
                    if (g.type == RecordType::A &&
                        std::holds_alternative<std::array<uint8_t, 4>>(g.rdata)) {
                        const auto& addr = std::get<std::array<uint8_t, 4>>(g.rdata);
                        char ip[INET_ADDRSTRLEN];
                        inet_ntop(AF_INET, addr.data(), ip, sizeof(ip));

                        auto result = query_authoritative(
                            name, ns_records, name, type);
                        if (result.status == ResponseCode::NO_ERROR) {
                            return result;
                        }
                    }
                }
            }

            // 没有 glue records，递归查询 NS 地址
            for (const auto& ns : ns_records) {
                if (std::holds_alternative<DnsName>(ns.rdata)) {
                    auto ns_name = std::get<DnsName>(ns.rdata).to_string();
                    auto ns_resolve = resolve_recursive(ns_name, RecordType::A,
                                                         depth + 1);
                    if (!ns_resolve.answers.empty()) {
                        auto ns_ip = ns_resolve.get_a_record();
                        if (ns_ip) {
                            auto result = query_authoritative(
                                ns_name, ns_records, name, type);
                            if (result.status == ResponseCode::NO_ERROR) {
                                return result;
                            }
                        }
                    }
                }
            }
        }
    }

    ResolveResult result;
    result.status = ResponseCode::SERVER_FAILURE;
    return result;
}

ResolveResult DnsResolver::resolve_iterative(const std::string& name,
                                              RecordType type) {
    // 迭代解析：从根服务器开始，逐级向下查询
    auto query = DnsMessage::create_query(name, type);
    std::string current_server;

    // 从根服务器开始
    for (const auto& root : config_.root_servers) {
        auto response = querier_.query(root, query, config_.query_timeout);
        if (response) {
            current_server = root;
            break;
        }
    }

    if (current_server.empty()) {
        ResolveResult result;
        result.status = ResponseCode::SERVER_FAILURE;
        return result;
    }

    // 迭代查询
    for (size_t i = 0; i < config_.max_redirects; i++) {
        auto response = querier_.query(current_server, query,
                                        config_.query_timeout);
        if (!response) {
            continue;
        }

        // 有回答
        if (!response->answers().empty()) {
            ResolveResult result;
            result.status = response->header().rcode;
            result.answers = response->answers();
            result.authorities = response->authorities();
            result.additionals = response->additionals();
            return result;
        }

        // 找到下一级 NS
        bool found_next = false;
        for (const auto& rr : response->additionals()) {
            if (rr.type == RecordType::A &&
                std::holds_alternative<std::array<uint8_t, 4>>(rr.rdata)) {
                const auto& addr = std::get<std::array<uint8_t, 4>>(rr.rdata);
                char ip[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, addr.data(), ip, sizeof(ip));
                current_server = ip;
                found_next = true;
                break;
            }
        }

        if (!found_next) {
            // 尝试解析 NS 域名
            for (const auto& rr : response->authorities()) {
                if (rr.type == RecordType::NS &&
                    std::holds_alternative<DnsName>(rr.rdata)) {
                    auto ns_name = std::get<DnsName>(rr.rdata).to_string();
                    auto ns_result = resolve(ns_name, RecordType::A);
                    if (!ns_result.answers.empty()) {
                        auto ip = ns_result.get_a_record();
                        if (ip) {
                            current_server = *ip;
                            found_next = true;
                            break;
                        }
                    }
                }
            }
        }

        if (!found_next) {
            break;
        }
    }

    ResolveResult result;
    result.status = ResponseCode::SERVER_FAILURE;
    return result;
}

ResolveResult DnsResolver::reverse_resolve(const std::string& ip_addr) {
    // 构造反向查询域名
    std::string reverse_name;

    // 检查是 IPv4 还是 IPv6
    struct in_addr addr4;
    struct in6_addr addr6;

    if (inet_pton(AF_INET, ip_addr.c_str(), &addr4) == 1) {
        // IPv4 反向解析
        uint32_t ip = ntohl(addr4.s_addr);
        reverse_name = std::to_string(ip & 0xFF) + "." +
                       std::to_string((ip >> 8) & 0xFF) + "." +
                       std::to_string((ip >> 16) & 0xFF) + "." +
                       std::to_string((ip >> 24) & 0xFF) + ".in-addr.arpa";
    } else if (inet_pton(AF_INET6, ip_addr.c_str(), &addr6) == 1) {
        // IPv6 反向解析
        char buf[64];
        for (int i = 0; i < 16; i++) {
            snprintf(buf + i * 4, 5, "%x.%x.",
                     addr6.s6_addr[i] & 0x0F,
                     (addr6.s6_addr[i] >> 4) & 0x0F);
        }
        reverse_name = std::string(buf) + ".ip6.arpa";
    } else {
        ResolveResult result;
        result.status = ResponseCode::FORMAT_ERROR;
        return result;
    }

    return resolve(reverse_name, RecordType::PTR);
}

ResolveResult DnsResolver::resolve_via_forwarder(const std::string& name,
                                                   RecordType type) {
    auto query = DnsMessage::create_query(name, type);

    for (const auto& forwarder : config_.forwarders) {
        auto response = querier_.query(forwarder, query,
                                        config_.query_timeout);
        if (response) {
            ResolveResult result;
            result.status = response->header().rcode;
            result.answers = response->answers();
            result.authorities = response->authorities();
            result.additionals = response->additionals();
            return result;
        }
    }

    ResolveResult result;
    result.status = ResponseCode::SERVER_FAILURE;
    return result;
}

ResolveResult DnsResolver::follow_cname(const std::string& cname_target,
                                          RecordType type,
                                          size_t depth) {
    return resolve_recursive(cname_target, type, depth);
}

ResolveResult DnsResolver::query_authoritative(
    const std::string& zone,
    const std::vector<ResourceRecord>& ns_records,
    const std::string& name,
    RecordType type) {

    auto query = DnsMessage::create_query(name, type);

    for (const auto& ns : ns_records) {
        if (!std::holds_alternative<DnsName>(ns.rdata)) continue;

        auto ns_name = std::get<DnsName>(ns.rdata).to_string();

        // 解析 NS 地址
        auto ns_resolve = resolve(ns_name, RecordType::A);
        auto ns_ip = ns_resolve.get_a_record();
        if (!ns_ip) continue;

        // 查询权威服务器
        auto response = querier_.query(*ns_ip, query, config_.query_timeout);
        if (response) {
            ResolveResult result;
            result.status = response->header().rcode;
            result.answers = response->answers();
            result.authorities = response->authorities();
            result.additionals = response->additionals();
            return result;
        }
    }

    ResolveResult result;
    result.status = ResponseCode::SERVER_FAILURE;
    return result;
}

std::vector<ResourceRecord> DnsResolver::find_authority(
    const std::string& name) {
    // 查找最接近的权威 NS 记录
    std::string current = name;
    while (!current.empty()) {
        auto query = DnsMessage::create_query(current, RecordType::NS);
        for (const auto& root : config_.root_servers) {
            auto response = querier_.query(root, query, config_.query_timeout);
            if (response && !response->authorities().empty()) {
                return response->authorities();
            }
        }
        auto pos = current.find('.');
        if (pos == std::string::npos) break;
        current = current.substr(pos + 1);
    }
    return {};
}

std::vector<ResourceRecord> DnsResolver::extract_glue_records(
    const std::vector<ResourceRecord>& ns_records,
    const std::vector<ResourceRecord>& additionals) {

    std::vector<ResourceRecord> glue;

    for (const auto& ns : ns_records) {
        if (!std::holds_alternative<DnsName>(ns.rdata)) continue;
        auto ns_name = std::get<DnsName>(ns.rdata).to_string();

        for (const auto& rr : additionals) {
            if (rr.name.to_string() == ns_name &&
                rr.type == RecordType::A) {
                glue.push_back(rr);
            }
        }
    }

    return glue;
}

void DnsResolver::clear_cache() {
    if (cache_) {
        cache_->clear();
    }
}

CacheStats DnsResolver::get_cache_stats() const {
    if (cache_) {
        return cache_->get_stats();
    }
    return {};
}

} // namespace dns
