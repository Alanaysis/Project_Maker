/**
 * @file zone_manager.cpp
 * @brief DNS 区域管理实现
 *
 * 实现 DNS 区域管理功能，包括：
 * - 区域文件解析
 * - 区域传输 (AXFR/IXFR)
 * - 动态更新
 * - SOA 记录管理
 */

#include "zone/zone_manager.h"
#include "monitoring/dns_monitor.h"

#include <fstream>
#include <sstream>
#include <algorithm>
#include <regex>
#include <cstring>
#include <arpa/inet.h>

namespace dns {

// ============================================================================
// ZoneType 转换
// ============================================================================

const char* zone_type_to_string(ZoneType type) {
    switch (type) {
        case ZoneType::PRIMARY:   return "PRIMARY";
        case ZoneType::SECONDARY: return "SECONDARY";
        case ZoneType::STUB:      return "STUB";
        case ZoneType::FORWARD:   return "FORWARD";
        default:                  return "UNKNOWN";
    }
}

// ============================================================================
// SoaData 实现
// ============================================================================

std::vector<uint8_t> SoaData::serialize() const {
    std::vector<uint8_t> data;

    // MNAME
    auto mname_data = mname.serialize();
    data.insert(data.end(), mname_data.begin(), mname_data.end());

    // RNAME
    auto rname_data = rname.serialize();
    data.insert(data.end(), rname_data.begin(), rname_data.end());

    // Serial
    data.push_back((serial >> 24) & 0xFF);
    data.push_back((serial >> 16) & 0xFF);
    data.push_back((serial >> 8) & 0xFF);
    data.push_back(serial & 0xFF);

    // Refresh
    data.push_back((refresh >> 24) & 0xFF);
    data.push_back((refresh >> 16) & 0xFF);
    data.push_back((refresh >> 8) & 0xFF);
    data.push_back(refresh & 0xFF);

    // Retry
    data.push_back((retry >> 24) & 0xFF);
    data.push_back((retry >> 16) & 0xFF);
    data.push_back((retry >> 8) & 0xFF);
    data.push_back(retry & 0xFF);

    // Expire
    data.push_back((expire >> 24) & 0xFF);
    data.push_back((expire >> 16) & 0xFF);
    data.push_back((expire >> 8) & 0xFF);
    data.push_back(expire & 0xFF);

    // Minimum
    data.push_back((minimum >> 24) & 0xFF);
    data.push_back((minimum >> 16) & 0xFF);
    data.push_back((minimum >> 8) & 0xFF);
    data.push_back(minimum & 0xFF);

    return data;
}

std::optional<SoaData> SoaData::deserialize(std::span<const uint8_t> data) {
    if (data.size() < 20) {
        return std::nullopt;
    }

    SoaData soa;
    size_t pos = 0;

    // MNAME
    auto mname_result = DnsName::deserialize(data, pos);
    if (!mname_result) return std::nullopt;
    soa.mname = mname_result->first;
    pos += mname_result->second;

    // RNAME
    auto rname_result = DnsName::deserialize(data, pos);
    if (!rname_result) return std::nullopt;
    soa.rname = rname_result->first;
    pos += rname_result->second;

    if (pos + 20 > data.size()) return std::nullopt;

    // Serial
    soa.serial = (static_cast<uint32_t>(data[pos]) << 24) |
                 (static_cast<uint32_t>(data[pos + 1]) << 16) |
                 (static_cast<uint32_t>(data[pos + 2]) << 8) |
                 static_cast<uint32_t>(data[pos + 3]);
    pos += 4;

    // Refresh
    soa.refresh = (static_cast<uint32_t>(data[pos]) << 24) |
                  (static_cast<uint32_t>(data[pos + 1]) << 16) |
                  (static_cast<uint32_t>(data[pos + 2]) << 8) |
                  static_cast<uint32_t>(data[pos + 3]);
    pos += 4;

    // Retry
    soa.retry = (static_cast<uint32_t>(data[pos]) << 24) |
                (static_cast<uint32_t>(data[pos + 1]) << 16) |
                (static_cast<uint32_t>(data[pos + 2]) << 8) |
                static_cast<uint32_t>(data[pos + 3]);
    pos += 4;

    // Expire
    soa.expire = (static_cast<uint32_t>(data[pos]) << 24) |
                 (static_cast<uint32_t>(data[pos + 1]) << 16) |
                 (static_cast<uint32_t>(data[pos + 2]) << 8) |
                 static_cast<uint32_t>(data[pos + 3]);
    pos += 4;

    // Minimum
    soa.minimum = (static_cast<uint32_t>(data[pos]) << 24) |
                  (static_cast<uint32_t>(data[pos + 1]) << 16) |
                  (static_cast<uint32_t>(data[pos + 2]) << 8) |
                  static_cast<uint32_t>(data[pos + 3]);

    return soa;
}

void SoaData::increment_serial() {
    serial++;
}

// ============================================================================
// Zone 实现
// ============================================================================

Zone::Zone(const std::string& name, ZoneType type)
    : name_(name), type_(type) {
    // 设置默认 SOA
    soa_data_.mname = DnsName("ns1." + name);
    soa_data_.rname = DnsName("admin." + name);
    soa_data_.serial = 1;
}

std::optional<ResourceRecord> Zone::get_soa() const {
    std::lock_guard<std::mutex> lock(mutex_);

    ResourceRecord rr;
    rr.name = DnsName(name_);
    rr.type = RecordType::SOA;
    rr.rclass = QueryClass::IN;
    rr.ttl = soa_data_.minimum;
    rr.rdata = soa_data_.serialize();
    rr.rdlength = static_cast<uint16_t>(
        std::get<std::vector<uint8_t>>(rr.rdata).size());

    return rr;
}

void Zone::set_soa(const SoaData& soa) {
    std::lock_guard<std::mutex> lock(mutex_);
    soa_data_ = soa;
}

std::vector<ResourceRecord> Zone::get_records(const std::string& name,
                                                RecordType type) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto name_it = records_.find(name);
    if (name_it == records_.end()) {
        return {};
    }

    auto type_it = name_it->second.find(type);
    if (type_it == name_it->second.end()) {
        return {};
    }

    return type_it->second;
}

std::vector<ResourceRecord> Zone::get_all_records(
    const std::string& name) const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<ResourceRecord> result;
    auto name_it = records_.find(name);
    if (name_it != records_.end()) {
        for (const auto& [type, records] : name_it->second) {
            result.insert(result.end(), records.begin(), records.end());
        }
    }
    return result;
}

bool Zone::add_record(const ResourceRecord& record) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto name = record.name.to_string();
    records_[name][record.type].push_back(record);
    return true;
}

bool Zone::remove_record(const std::string& name, RecordType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto name_it = records_.find(name);
    if (name_it == records_.end()) {
        return false;
    }

    return name_it->second.erase(type) > 0;
}

bool Zone::remove_record(const ResourceRecord& record) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto name = record.name.to_string();
    auto name_it = records_.find(name);
    if (name_it == records_.end()) {
        return false;
    }

    auto type_it = name_it->second.find(record.type);
    if (type_it == name_it->second.end()) {
        return false;
    }

    auto& records = type_it->second;
    auto it = std::find_if(records.begin(), records.end(),
        [&record](const ResourceRecord& r) {
            return r.rdata_to_string() == record.rdata_to_string();
        });

    if (it != records.end()) {
        records.erase(it);
        if (records.empty()) {
            name_it->second.erase(type_it);
        }
        return true;
    }

    return false;
}

std::vector<ResourceRecord> Zone::get_all_records() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<ResourceRecord> result;

    // 添加 SOA 记录 (直接访问 soa_data_ 避免死锁)
    ResourceRecord soa_rr;
    soa_rr.name = DnsName(name_);
    soa_rr.type = RecordType::SOA;
    soa_rr.rclass = QueryClass::IN;
    soa_rr.ttl = soa_data_.minimum;
    soa_rr.rdata = soa_data_.serialize();
    soa_rr.rdlength = static_cast<uint16_t>(
        std::get<std::vector<uint8_t>>(soa_rr.rdata).size());
    result.push_back(soa_rr);

    // 添加所有记录
    for (const auto& [name, type_map] : records_) {
        for (const auto& [type, records] : type_map) {
            result.insert(result.end(), records.begin(), records.end());
        }
    }

    return result;
}

size_t Zone::record_count() const {
    std::lock_guard<std::mutex> lock(mutex_);

    size_t count = 0;
    for (const auto& [name, type_map] : records_) {
        for (const auto& [type, records] : type_map) {
            count += records.size();
        }
    }
    return count;
}

bool Zone::has_name(const std::string& name) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return records_.find(name) != records_.end();
}

void Zone::increment_serial() {
    std::lock_guard<std::mutex> lock(mutex_);
    soa_data_.increment_serial();
}

// ============================================================================
// ZoneFileParser 实现
// ============================================================================

std::optional<std::unique_ptr<Zone>> ZoneFileParser::parse(
    const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        error_msg_ = "Cannot open file: " + filename;
        return std::nullopt;
    }

    std::string content((std::istreambuf_iterator<char>(file)),
                         std::istreambuf_iterator<char>());

    // 从文件名推断区域名
    std::string zone_name;
    auto pos = filename.find_last_of('/');
    if (pos != std::string::npos) {
        zone_name = filename.substr(pos + 1);
    } else {
        zone_name = filename;
    }
    // 去掉扩展名
    pos = zone_name.find_last_of('.');
    if (pos != std::string::npos) {
        zone_name = zone_name.substr(0, pos);
    }

    return parse_string(content, zone_name);
}

std::optional<std::unique_ptr<Zone>> ZoneFileParser::parse_string(
    const std::string& content,
    const std::string& zone_name) {

    auto zone = std::make_unique<Zone>(zone_name);
    std::string origin = zone_name;
    uint32_t default_ttl = 3600;
    std::string current_name = "@";

    std::istringstream stream(content);
    std::string line;
    size_t line_num = 0;

    std::string multi_line_buffer;
    bool in_multi_line = false;

    while (std::getline(stream, line)) {
        line_num++;

        // 去除注释
        auto comment_pos = line.find(';');
        if (comment_pos != std::string::npos) {
            line = line.substr(0, comment_pos);
        }

        // 去除首尾空白
        auto start = line.find_first_not_of(" \t");
        if (start == std::string::npos) {
            if (in_multi_line) {
                multi_line_buffer += " ";
            }
            continue;
        }
        auto end = line.find_last_not_of(" \t");
        line = line.substr(start, end - start + 1);

        if (line.empty()) {
            if (in_multi_line) {
                multi_line_buffer += " ";
            }
            continue;
        }

        // 处理多行记录（括号）
        if (in_multi_line) {
            multi_line_buffer += " " + line;
            if (line.find(')') != std::string::npos) {
                in_multi_line = false;
                // 去除括号
                std::string processed;
                for (char c : multi_line_buffer) {
                    if (c != '(' && c != ')') {
                        processed += c;
                    }
                }
                line = processed;
                multi_line_buffer.clear();
            } else {
                continue;
            }
        } else if (line.find('(') != std::string::npos && line.find(')') == std::string::npos) {
            in_multi_line = true;
            multi_line_buffer = line;
            continue;
        }

        // 处理 $ORIGIN 指令
        if (line.substr(0, 7) == "$ORIGIN") {
            origin = line.substr(8);
            // 去除空白
            start = origin.find_first_not_of(" \t");
            if (start != std::string::npos) {
                origin = origin.substr(start);
            }
            // 去除尾部点号
            if (!origin.empty() && origin.back() == '.') {
                origin.pop_back();
            }
            continue;
        }

        // 处理 $TTL 指令
        if (line.substr(0, 4) == "$TTL") {
            auto ttl_str = line.substr(4);
            // 去除空白
            auto ttl_start = ttl_str.find_first_not_of(" \t");
            if (ttl_start != std::string::npos) {
                ttl_str = ttl_str.substr(ttl_start);
            }
            auto ttl = parse_ttl(ttl_str);
            if (ttl) {
                default_ttl = *ttl;
            }
            continue;
        }

        // 处理 $INCLUDE 指令
        if (line.substr(0, 8) == "$INCLUDE") {
            // 暂不支持
            continue;
        }

        // 解析记录
        auto record = parse_line(line, origin, default_ttl);
        if (record) {
            zone->add_record(*record);
        } else {
            error_msg_ = "Parse error at line " + std::to_string(line_num) +
                         ": " + line;
            return std::nullopt;
        }
    }

    return zone;
}

std::optional<ResourceRecord> ZoneFileParser::parse_line(
    const std::string& line,
    const std::string& origin,
    uint32_t default_ttl) {

    std::istringstream stream(line);
    std::vector<std::string> tokens;
    std::string token;

    while (stream >> token) {
        tokens.push_back(token);
    }

    if (tokens.empty()) {
        return std::nullopt;
    }

    ResourceRecord rr;
    size_t pos = 0;

    // 解析名称
    if (tokens[pos] == "@") {
        rr.name = DnsName(origin);
        pos++;
    } else if (tokens[pos].back() == '.') {
        rr.name = DnsName(tokens[pos]);
        pos++;
    } else if (std::isdigit(tokens[pos][0])) {
        // 第一个 token 是 TTL
        auto ttl = parse_ttl(tokens[pos]);
        if (ttl) {
            rr.ttl = *ttl;
            pos++;
        }
    } else {
        rr.name = DnsName(expand_name(tokens[pos], origin, origin));
        pos++;
    }

    // 检查是否有 TTL
    if (pos < tokens.size() && std::isdigit(tokens[pos][0])) {
        auto ttl = parse_ttl(tokens[pos]);
        if (ttl) {
            rr.ttl = *ttl;
            pos++;
        }
    }

    // 检查是否有类
    if (pos < tokens.size()) {
        if (tokens[pos] == "IN") {
            rr.rclass = QueryClass::IN;
            pos++;
        } else if (tokens[pos] == "CH") {
            rr.rclass = QueryClass::CH;
            pos++;
        } else if (tokens[pos] == "HS") {
            rr.rclass = QueryClass::HS;
            pos++;
        }
    }

    // 解析类型
    if (pos >= tokens.size()) {
        return std::nullopt;
    }
    rr.type = string_to_record_type(tokens[pos]);
    pos++;

    // 解析 RDATA
    std::vector<std::string> rdata_tokens(tokens.begin() + pos,
                                           tokens.end());
    auto rdata = parse_rdata(rr.type, rdata_tokens, origin);
    if (!rdata) {
        return std::nullopt;
    }
    rr.rdata = *rdata;

    // 设置默认 TTL
    if (rr.ttl == 0) {
        rr.ttl = default_ttl;
    }

    return rr;
}

std::string ZoneFileParser::expand_name(const std::string& name,
                                         const std::string& origin,
                                         const std::string& current) const {
    if (name == "@") {
        return origin;
    }
    if (name.back() == '.') {
        return name.substr(0, name.length() - 1);
    }
    return name + "." + origin;
}

std::optional<uint32_t> ZoneFileParser::parse_ttl(const std::string& str) const {
    try {
        size_t pos;
        uint64_t value = std::stoull(str, &pos);

        if (pos < str.length()) {
            switch (str[pos]) {
                case 'S': case 's': break;
                case 'M': case 'm': value *= 60; break;
                case 'H': case 'h': value *= 3600; break;
                case 'D': case 'd': value *= 86400; break;
                case 'W': case 'w': value *= 604800; break;
                default: break;
            }
        }

        return static_cast<uint32_t>(std::min(value,
                                               static_cast<uint64_t>(UINT32_MAX)));
    } catch (...) {
        return std::nullopt;
    }
}

std::optional<RdataVariant> ZoneFileParser::parse_rdata(
    RecordType type,
    const std::vector<std::string>& tokens,
    const std::string& origin) const {

    if (tokens.empty()) {
        return std::nullopt;
    }

    switch (type) {
        case RecordType::SOA: {
            // SOA 记录: MNAME RNAME SERIAL REFRESH RETRY EXPIRE MINIMUM
            if (tokens.size() < 7) return std::nullopt;
            std::vector<uint8_t> data;

            // MNAME
            auto mname = DnsName(expand_name(tokens[0], origin, origin));
            auto mname_data = mname.serialize();
            data.insert(data.end(), mname_data.begin(), mname_data.end());

            // RNAME
            auto rname = DnsName(expand_name(tokens[1], origin, origin));
            auto rname_data = rname.serialize();
            data.insert(data.end(), rname_data.begin(), rname_data.end());

            // SERIAL, REFRESH, RETRY, EXPIRE, MINIMUM
            for (int i = 2; i < 7; i++) {
                uint32_t value = static_cast<uint32_t>(std::stoul(tokens[i]));
                data.push_back((value >> 24) & 0xFF);
                data.push_back((value >> 16) & 0xFF);
                data.push_back((value >> 8) & 0xFF);
                data.push_back(value & 0xFF);
            }

            return data;
        }
        case RecordType::A: {
            if (tokens.size() < 1) return std::nullopt;
            struct in_addr addr;
            if (inet_pton(AF_INET, tokens[0].c_str(), &addr) != 1) {
                return std::nullopt;
            }
            std::array<uint8_t, 4> arr;
            std::memcpy(arr.data(), &addr.s_addr, 4);
            return arr;
        }
        case RecordType::AAAA: {
            if (tokens.size() < 1) return std::nullopt;
            struct in6_addr addr;
            if (inet_pton(AF_INET6, tokens[0].c_str(), &addr) != 1) {
                return std::nullopt;
            }
            std::array<uint8_t, 16> arr;
            std::memcpy(arr.data(), addr.s6_addr, 16);
            return arr;
        }
        case RecordType::NS:
        case RecordType::CNAME: {
            if (tokens.size() < 1) return std::nullopt;
            return DnsName(expand_name(tokens[0], origin, origin));
        }
        case RecordType::MX: {
            if (tokens.size() < 2) return std::nullopt;
            std::vector<uint8_t> data;
            uint16_t preference = static_cast<uint16_t>(std::stoi(tokens[0]));
            data.push_back((preference >> 8) & 0xFF);
            data.push_back(preference & 0xFF);
            auto name = DnsName(expand_name(tokens[1], origin, origin));
            auto name_data = name.serialize();
            data.insert(data.end(), name_data.begin(), name_data.end());
            return data;
        }
        case RecordType::TXT: {
            std::vector<uint8_t> data;
            for (const auto& t : tokens) {
                std::string text = t;
                // 去除引号
                if (text.front() == '"' && text.back() == '"') {
                    text = text.substr(1, text.length() - 2);
                }
                data.push_back(static_cast<uint8_t>(text.length()));
                data.insert(data.end(), text.begin(), text.end());
            }
            return data;
        }
        case RecordType::SRV: {
            if (tokens.size() < 4) return std::nullopt;
            std::vector<uint8_t> data;
            uint16_t priority = static_cast<uint16_t>(std::stoi(tokens[0]));
            uint16_t weight = static_cast<uint16_t>(std::stoi(tokens[1]));
            uint16_t port = static_cast<uint16_t>(std::stoi(tokens[2]));
            auto target = DnsName(expand_name(tokens[3], origin, origin));

            data.push_back((priority >> 8) & 0xFF);
            data.push_back(priority & 0xFF);
            data.push_back((weight >> 8) & 0xFF);
            data.push_back(weight & 0xFF);
            data.push_back((port >> 8) & 0xFF);
            data.push_back(port & 0xFF);
            auto target_data = target.serialize();
            data.insert(data.end(), target_data.begin(), target_data.end());
            return data;
        }
        default:
            return std::nullopt;
    }
}

// ============================================================================
// ZoneTransfer 实现
// ============================================================================

std::optional<std::unique_ptr<Zone>> ZoneTransfer::axfr(
    const std::string& server,
    const std::string& zone_name) {

    auto query = DnsMessage::create_query(zone_name, RecordType::AXFR);
    auto response = send_tcp_query(server, query);

    if (!response) {
        return std::nullopt;
    }

    auto zone = std::make_unique<Zone>(zone_name, ZoneType::SECONDARY);

    // 第一个报文必须是 SOA 记录
    if (response->answers().empty() ||
        response->answers()[0].type != RecordType::SOA) {
        return std::nullopt;
    }

    // 处理所有回答
    for (const auto& rr : response->answers()) {
        zone->add_record(rr);
    }

    return zone;
}

std::optional<std::vector<ResourceRecord>> ZoneTransfer::ixfr(
    const std::string& server,
    const std::string& zone_name,
    uint32_t known_serial) {

    auto query = DnsMessage::create_query(zone_name, RecordType::IXFR);
    auto response = send_tcp_query(server, query);

    if (!response) {
        return std::nullopt;
    }

    return response->answers();
}

std::vector<DnsMessage> ZoneTransfer::handle_axfr_request(
    const DnsMessage& request,
    const Zone& zone) {

    std::vector<DnsMessage> responses;

    // 创建响应
    auto response = DnsMessage::create_response(request, ResponseCode::NO_ERROR);
    response.header().aa = true;

    // 添加所有记录
    auto records = zone.get_all_records();
    for (const auto& rr : records) {
        response.add_answer(ResourceRecord(rr));
    }

    responses.push_back(response);
    return responses;
}

std::vector<DnsMessage> ZoneTransfer::handle_ixfr_request(
    const DnsMessage& request,
    const Zone& zone,
    uint32_t client_serial) {

    std::vector<DnsMessage> responses;

    // 简化实现：返回完整区域
    return handle_axfr_request(request, zone);
}

std::optional<DnsMessage> ZoneTransfer::send_tcp_query(
    const std::string& server,
    const DnsMessage& query) {

    // 简化实现：使用系统 DNS 解析
    auto data = query.serialize();

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        return std::nullopt;
    }

    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(DNS_PORT);
    inet_pton(AF_INET, server.c_str(), &addr.sin_addr);

    if (connect(sock, reinterpret_cast<struct sockaddr*>(&addr),
                sizeof(addr)) < 0) {
        close(sock);
        return std::nullopt;
    }

    // 发送长度前缀
    uint16_t length = htons(static_cast<uint16_t>(data.size()));
    send(sock, &length, 2, 0);
    send(sock, data.data(), data.size(), 0);

    // 接收响应
    uint16_t resp_length;
    recv(sock, &resp_length, 2, MSG_WAITALL);
    resp_length = ntohs(resp_length);

    std::vector<uint8_t> buffer(resp_length);
    recv(sock, buffer.data(), resp_length, MSG_WAITALL);
    close(sock);

    return DnsMessage::deserialize(buffer);
}

// ============================================================================
// DynamicUpdate 实现
// ============================================================================

ResponseCode DynamicUpdate::handle_update(const DnsMessage& request,
                                           Zone& zone) {
    // 检查先决条件
    auto prereq_status = check_prerequisites(request.authorities(), zone);
    if (prereq_status != ResponseCode::NO_ERROR) {
        return prereq_status;
    }

    // 应用更新
    return apply_updates(request.authorities(), request.additionals(), zone);
}

ResponseCode DynamicUpdate::check_prerequisites(
    const std::vector<ResourceRecord>& prerequisites,
    const Zone& zone) {

    for (const auto& prereq : prerequisites) {
        auto name = prereq.name.to_string();

        if (prereq.ttl != 0) {
            // RRset 存在 (值无关)
            auto records = zone.get_records(name, prereq.type);
            if (records.empty()) {
                return ResponseCode::NAME_ERROR;
            }
        } else {
            // RRset 不存在
            auto records = zone.get_records(name, prereq.type);
            if (!records.empty()) {
                return ResponseCode::NAME_ERROR;
            }
        }
    }

    return ResponseCode::NO_ERROR;
}

ResponseCode DynamicUpdate::apply_updates(
    const std::vector<ResourceRecord>& updates,
    const std::vector<ResourceRecord>& additions,
    Zone& zone) {

    // 删除记录
    for (const auto& rr : updates) {
        if (rr.ttl == 0 && rr.rdata_to_string().empty()) {
            // 删除整个 RRset
            zone.remove_record(rr.name.to_string(), rr.type);
        } else if (rr.ttl == 0) {
            // 删除特定记录
            zone.remove_record(rr);
        }
    }

    // 添加记录
    for (const auto& rr : additions) {
        zone.add_record(rr);
    }

    // 递增序列号
    zone.increment_serial();

    return ResponseCode::NO_ERROR;
}

// ============================================================================
// ZoneManager 实现
// ============================================================================

bool ZoneManager::load_zone(const ZoneConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);

    ZoneFileParser parser;
    auto zone = parser.parse(config.zone_file);
    if (!zone) {
        DNS_LOG_ERROR("ZoneManager", "Failed to load zone: " +
                      parser.error_message());
        return false;
    }

    auto name = (*zone)->name();
    configs_[name] = config;
    zones_[name] = std::move(*zone);

    DNS_LOG_INFO("ZoneManager", "Loaded zone: " + name);
    return true;
}

bool ZoneManager::add_zone(std::unique_ptr<Zone> zone) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto name = zone->name();
    zones_[name] = std::move(zone);
    return true;
}

bool ZoneManager::remove_zone(const std::string& zone_name) {
    std::lock_guard<std::mutex> lock(mutex_);

    zones_.erase(zone_name);
    configs_.erase(zone_name);
    return true;
}

Zone* ZoneManager::get_zone(const std::string& zone_name) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = zones_.find(zone_name);
    if (it != zones_.end()) {
        return it->second.get();
    }
    return nullptr;
}

Zone* ZoneManager::find_zone(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 查找最匹配的区域
    std::string current = name;
    while (!current.empty()) {
        auto it = zones_.find(current);
        if (it != zones_.end()) {
            return it->second.get();
        }
        auto pos = current.find('.');
        if (pos == std::string::npos) break;
        current = current.substr(pos + 1);
    }
    return nullptr;
}

std::vector<ResourceRecord> ZoneManager::query(const std::string& name,
                                                 RecordType type) {
    auto* zone = find_zone(name);
    if (!zone) {
        return {};
    }

    auto records = zone->get_records(name, type);

    // 如果没有找到记录，检查是否需要返回 SOA
    if (records.empty() && zone->has_name(name)) {
        auto soa = zone->get_soa();
        if (soa) {
            return {*soa};
        }
    }

    return records;
}

std::vector<std::string> ZoneManager::get_zone_names() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<std::string> names;
    for (const auto& [name, zone] : zones_) {
        names.push_back(name);
    }
    return names;
}

std::vector<DnsMessage> ZoneManager::handle_transfer(
    const std::string& zone_name,
    TransferType type,
    uint32_t client_serial) {

    auto* zone = get_zone(zone_name);
    if (!zone) {
        return {};
    }

    DnsMessage request;
    if (type == TransferType::AXFR) {
        return ZoneTransfer::handle_axfr_request(request, *zone);
    } else {
        return ZoneTransfer::handle_ixfr_request(request, *zone, client_serial);
    }
}

ResponseCode ZoneManager::handle_update(const std::string& zone_name,
                                          const DnsMessage& request) {
    auto* zone = get_zone(zone_name);
    if (!zone) {
        return ResponseCode::NAME_ERROR;
    }

    return DynamicUpdate::handle_update(request, *zone);
}

bool ZoneManager::save_zone(const std::string& zone_name,
                             const std::string& filename) {
    auto* zone = get_zone(zone_name);
    if (!zone) {
        return false;
    }

    std::ofstream file(filename);
    if (!file.is_open()) {
        return false;
    }

    // 写入 SOA
    auto soa = zone->get_soa();
    if (soa) {
        file << soa->name.to_string() << " IN SOA "
             << soa->rdata_to_string() << "\n";
    }

    // 写入所有记录
    auto records = zone->get_all_records();
    for (const auto& rr : records) {
        if (rr.type == RecordType::SOA) continue;
        file << rr.name.to_string() << " "
             << rr.ttl << " "
             << "IN "
             << record_type_to_string(rr.type) << " "
             << rr.rdata_to_string() << "\n";
    }

    return true;
}

bool ZoneManager::reload_zone(const std::string& zone_name) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto config_it = configs_.find(zone_name);
    if (config_it == configs_.end()) {
        return false;
    }

    ZoneFileParser parser;
    auto zone = parser.parse(config_it->second.zone_file);
    if (!zone) {
        return false;
    }

    zones_[zone_name] = std::move(*zone);
    return true;
}

} // namespace dns
