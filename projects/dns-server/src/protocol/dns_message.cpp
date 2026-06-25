/**
 * @file dns_message.cpp
 * @brief DNS 报文格式实现
 *
 * 实现 DNS 协议的核心报文结构，包括：
 * - DNS 报头序列化/反序列化
 * - 域名编码/解码 (支持压缩)
 * - 资源记录解析
 * - 完整报文处理
 *
 * 参考: RFC 1035 - Domain Names - Implementation and Specification
 */

#include "protocol/dns_message.h"
#include <cstring>
#include <sstream>
#include <algorithm>
#include <arpa/inet.h>

namespace dns {

// ============================================================================
// 记录类型转换
// ============================================================================

const char* record_type_to_string(RecordType type) {
    switch (type) {
        case RecordType::A:     return "A";
        case RecordType::NS:    return "NS";
        case RecordType::CNAME: return "CNAME";
        case RecordType::SOA:   return "SOA";
        case RecordType::PTR:   return "PTR";
        case RecordType::MX:    return "MX";
        case RecordType::TXT:   return "TXT";
        case RecordType::AAAA:  return "AAAA";
        case RecordType::SRV:   return "SRV";
        case RecordType::OPT:   return "OPT";
        case RecordType::AXFR:  return "AXFR";
        case RecordType::IXFR:  return "IXFR";
        case RecordType::ANY:   return "ANY";
        default:                return "UNKNOWN";
    }
}

RecordType string_to_record_type(const std::string& str) {
    if (str == "A") return RecordType::A;
    if (str == "NS") return RecordType::NS;
    if (str == "CNAME") return RecordType::CNAME;
    if (str == "SOA") return RecordType::SOA;
    if (str == "PTR") return RecordType::PTR;
    if (str == "MX") return RecordType::MX;
    if (str == "TXT") return RecordType::TXT;
    if (str == "AAAA") return RecordType::AAAA;
    if (str == "SRV") return RecordType::SRV;
    if (str == "ANY") return RecordType::ANY;
    return RecordType::A;
}

const char* response_code_to_string(ResponseCode code) {
    switch (code) {
        case ResponseCode::NO_ERROR:        return "NOERROR";
        case ResponseCode::FORMAT_ERROR:    return "FORMERR";
        case ResponseCode::SERVER_FAILURE:  return "SERVFAIL";
        case ResponseCode::NAME_ERROR:      return "NXDOMAIN";
        case ResponseCode::NOT_IMPLEMENTED: return "NOTIMP";
        case ResponseCode::REFUSED:         return "REFUSED";
        default:                            return "UNKNOWN";
    }
}

// ============================================================================
// DnsHeader 实现
// ============================================================================

std::vector<uint8_t> DnsHeader::serialize() const {
    std::vector<uint8_t> data(DNS_HEADER_SIZE);

    // ID
    data[0] = (id >> 8) & 0xFF;
    data[1] = id & 0xFF;

    // Flags
    uint8_t flags1 = 0;
    if (qr) flags1 |= 0x80;
    flags1 |= (static_cast<uint8_t>(opcode) & 0x0F) << 3;
    if (aa) flags1 |= 0x04;
    if (tc) flags1 |= 0x02;
    if (rd) flags1 |= 0x01;
    data[2] = flags1;

    uint8_t flags2 = 0;
    if (ra) flags2 |= 0x80;
    flags2 |= (z & 0x07) << 4;
    flags2 |= static_cast<uint8_t>(rcode) & 0x0F;
    data[3] = flags2;

    // Counts
    data[4] = (qdcount >> 8) & 0xFF;
    data[5] = qdcount & 0xFF;
    data[6] = (ancount >> 8) & 0xFF;
    data[7] = ancount & 0xFF;
    data[8] = (nscount >> 8) & 0xFF;
    data[9] = nscount & 0xFF;
    data[10] = (arcount >> 8) & 0xFF;
    data[11] = arcount & 0xFF;

    return data;
}

std::optional<DnsHeader> DnsHeader::deserialize(std::span<const uint8_t> data) {
    if (data.size() < DNS_HEADER_SIZE) {
        return std::nullopt;
    }

    DnsHeader header;

    // ID
    header.id = (static_cast<uint16_t>(data[0]) << 8) | data[1];

    // Flags
    uint8_t flags1 = data[2];
    header.qr = (flags1 & 0x80) != 0;
    header.opcode = static_cast<Opcode>((flags1 >> 3) & 0x0F);
    header.aa = (flags1 & 0x04) != 0;
    header.tc = (flags1 & 0x02) != 0;
    header.rd = (flags1 & 0x01) != 0;

    uint8_t flags2 = data[3];
    header.ra = (flags2 & 0x80) != 0;
    header.z = (flags2 >> 4) & 0x07;
    header.rcode = static_cast<ResponseCode>(flags2 & 0x0F);

    // Counts
    header.qdcount = (static_cast<uint16_t>(data[4]) << 8) | data[5];
    header.ancount = (static_cast<uint16_t>(data[6]) << 8) | data[7];
    header.nscount = (static_cast<uint16_t>(data[8]) << 8) | data[9];
    header.arcount = (static_cast<uint16_t>(data[10]) << 8) | data[11];

    return header;
}

// ============================================================================
// DnsName 实现
// ============================================================================

DnsName::DnsName(const std::string& name) : name_(to_lower(name)) {}

void DnsName::set(const std::string& name) {
    name_ = to_lower(name);
}

size_t DnsName::label_count() const {
    if (name_.empty()) return 0;
    return std::count(name_.begin(), name_.end(), '.') + 1;
}

DnsName DnsName::parent() const {
    auto pos = name_.find('.');
    if (pos == std::string::npos) {
        return DnsName("");
    }
    return DnsName(name_.substr(pos + 1));
}

std::vector<uint8_t> DnsName::serialize(bool compress, size_t offset) const {
    std::vector<uint8_t> data;

    if (name_.empty() || name_ == ".") {
        data.push_back(0);  // 根域名
        return data;
    }

    // 分割标签
    std::string remaining = name_;
    while (!remaining.empty()) {
        auto pos = remaining.find('.');
        std::string label;
        if (pos == std::string::npos) {
            label = remaining;
            remaining.clear();
        } else {
            label = remaining.substr(0, pos);
            remaining = remaining.substr(pos + 1);
        }

        // 标签长度不能超过 63
        if (label.length() > DNS_LABEL_MAX_LENGTH) {
            label = label.substr(0, DNS_LABEL_MAX_LENGTH);
        }

        data.push_back(static_cast<uint8_t>(label.length()));
        data.insert(data.end(), label.begin(), label.end());
    }

    data.push_back(0);  // 结束标记
    return data;
}

std::optional<std::pair<DnsName, size_t>>
DnsName::deserialize(std::span<const uint8_t> data, size_t offset) {
    std::string name;
    size_t pos = offset;
    bool jumped = false;
    size_t jump_offset = 0;
    size_t original_pos = offset;
    int max_jumps = 10;  // 防止无限循环

    while (pos < data.size()) {
        uint8_t length = data[pos];

        // 压缩指针检测
        if ((length & 0xC0) == 0xC0) {
            if (pos + 1 >= data.size()) {
                return std::nullopt;
            }
            uint16_t pointer = ((length & 0x3F) << 8) | data[pos + 1];
            if (!jumped) {
                jump_offset = pos + 2;
            }
            pos = pointer;
            jumped = true;
            max_jumps--;
            if (max_jumps <= 0) {
                return std::nullopt;  // 防止循环引用
            }
            continue;
        }

        // 结束标记
        if (length == 0) {
            pos++;
            break;
        }

        // 标签
        if (pos + 1 + length > data.size()) {
            return std::nullopt;
        }

        if (!name.empty()) {
            name += '.';
        }
        name.append(reinterpret_cast<const char*>(&data[pos + 1]), length);
        pos += 1 + length;
    }

    // 计算消耗的字节数
    size_t consumed = jumped ? jump_offset - offset : pos - offset;

    return std::make_pair(DnsName(name), consumed);
}

bool DnsName::operator==(const DnsName& other) const {
    return name_ == other.name_;
}

bool DnsName::operator<(const DnsName& other) const {
    return name_ < other.name_;
}

bool DnsName::equal_ignore_case(const DnsName& a, const DnsName& b) {
    return to_lower(a.name_) == to_lower(b.name_);
}

std::string DnsName::to_lower(const std::string& s) {
    std::string result = s;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

// ============================================================================
// DnsQuestion 实现
// ============================================================================

std::vector<uint8_t> DnsQuestion::serialize(bool compress, size_t offset) const {
    std::vector<uint8_t> data;

    // 域名
    auto name_data = name.serialize(compress, offset);
    data.insert(data.end(), name_data.begin(), name_data.end());

    // 类型
    uint16_t type_val = static_cast<uint16_t>(type);
    data.push_back((type_val >> 8) & 0xFF);
    data.push_back(type_val & 0xFF);

    // 类
    uint16_t class_val = static_cast<uint16_t>(qclass);
    data.push_back((class_val >> 8) & 0xFF);
    data.push_back(class_val & 0xFF);

    return data;
}

std::optional<std::pair<DnsQuestion, size_t>>
DnsQuestion::deserialize(std::span<const uint8_t> data, size_t offset) {
    DnsQuestion question;
    size_t pos = offset;

    // 解析域名
    auto name_result = DnsName::deserialize(data, pos);
    if (!name_result) {
        return std::nullopt;
    }
    question.name = name_result->first;
    pos += name_result->second;

    // 检查剩余数据
    if (pos + 4 > data.size()) {
        return std::nullopt;
    }

    // 类型
    question.type = static_cast<RecordType>(
        (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1]);
    pos += 2;

    // 类
    question.qclass = static_cast<QueryClass>(
        (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1]);
    pos += 2;

    return std::make_pair(question, pos - offset);
}

// ============================================================================
// ResourceRecord 实现
// ============================================================================

std::vector<uint8_t> ResourceRecord::serialize(bool compress, size_t offset) const {
    std::vector<uint8_t> data;

    // 域名
    auto name_data = name.serialize(compress, offset);
    data.insert(data.end(), name_data.begin(), name_data.end());

    // 类型
    uint16_t type_val = static_cast<uint16_t>(type);
    data.push_back((type_val >> 8) & 0xFF);
    data.push_back(type_val & 0xFF);

    // 类
    uint16_t class_val = static_cast<uint16_t>(rclass);
    data.push_back((class_val >> 8) & 0xFF);
    data.push_back(class_val & 0xFF);

    // TTL
    data.push_back((ttl >> 24) & 0xFF);
    data.push_back((ttl >> 16) & 0xFF);
    data.push_back((ttl >> 8) & 0xFF);
    data.push_back(ttl & 0xFF);

    // 获取 RDATA
    auto rdata_bytes = get_rdata_bytes();

    // RDLENGTH
    uint16_t rdlength = static_cast<uint16_t>(rdata_bytes.size());
    data.push_back((rdlength >> 8) & 0xFF);
    data.push_back(rdlength & 0xFF);

    // RDATA
    data.insert(data.end(), rdata_bytes.begin(), rdata_bytes.end());

    return data;
}

std::optional<std::pair<ResourceRecord, size_t>>
ResourceRecord::deserialize(std::span<const uint8_t> data, size_t offset) {
    ResourceRecord rr;
    size_t pos = offset;

    // 解析域名
    auto name_result = DnsName::deserialize(data, pos);
    if (!name_result) {
        return std::nullopt;
    }
    rr.name = name_result->first;
    pos += name_result->second;

    // 检查剩余数据
    if (pos + 10 > data.size()) {
        return std::nullopt;
    }

    // 类型
    rr.type = static_cast<RecordType>(
        (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1]);
    pos += 2;

    // 类
    rr.rclass = static_cast<QueryClass>(
        (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1]);
    pos += 2;

    // TTL
    rr.ttl = (static_cast<uint32_t>(data[pos]) << 24) |
             (static_cast<uint32_t>(data[pos + 1]) << 16) |
             (static_cast<uint32_t>(data[pos + 2]) << 8) |
             static_cast<uint32_t>(data[pos + 3]);
    pos += 4;

    // RDLENGTH
    rr.rdlength = (static_cast<uint16_t>(data[pos]) << 8) | data[pos + 1];
    pos += 2;

    // 检查 RDATA 长度
    if (pos + rr.rdlength > data.size()) {
        return std::nullopt;
    }

    // 解析 RDATA
    std::span<const uint8_t> rdata_span(&data[pos], rr.rdlength);

    switch (rr.type) {
        case RecordType::A: {
            if (rr.rdlength == 4) {
                std::array<uint8_t, 4> addr;
                std::memcpy(addr.data(), rdata_span.data(), 4);
                rr.rdata = addr;
            }
            break;
        }
        case RecordType::AAAA: {
            if (rr.rdlength == 16) {
                std::array<uint8_t, 16> addr;
                std::memcpy(addr.data(), rdata_span.data(), 16);
                rr.rdata = addr;
            }
            break;
        }
        case RecordType::NS:
        case RecordType::CNAME: {
            auto name_result = DnsName::deserialize(data, pos);
            if (name_result) {
                rr.rdata = name_result->first;
            }
            break;
        }
        default: {
            // 以原始字节存储
            std::vector<uint8_t> raw(rdata_span.begin(), rdata_span.end());
            rr.rdata = raw;
            break;
        }
    }

    pos += rr.rdlength;

    return std::make_pair(rr, pos - offset);
}

std::vector<uint8_t> ResourceRecord::get_rdata_bytes() const {
    if (std::holds_alternative<std::array<uint8_t, 4>>(rdata)) {
        const auto& addr = std::get<std::array<uint8_t, 4>>(rdata);
        return std::vector<uint8_t>(addr.begin(), addr.end());
    }
    if (std::holds_alternative<std::array<uint8_t, 16>>(rdata)) {
        const auto& addr = std::get<std::array<uint8_t, 16>>(rdata);
        return std::vector<uint8_t>(addr.begin(), addr.end());
    }
    if (std::holds_alternative<DnsName>(rdata)) {
        return std::get<DnsName>(rdata).serialize();
    }
    if (std::holds_alternative<std::vector<uint8_t>>(rdata)) {
        return std::get<std::vector<uint8_t>>(rdata);
    }
    return {};
}

std::string ResourceRecord::rdata_to_string() const {
    switch (type) {
        case RecordType::A: {
            if (std::holds_alternative<std::array<uint8_t, 4>>(rdata)) {
                const auto& addr = std::get<std::array<uint8_t, 4>>(rdata);
                char buf[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, addr.data(), buf, sizeof(buf));
                return std::string(buf);
            }
            break;
        }
        case RecordType::AAAA: {
            if (std::holds_alternative<std::array<uint8_t, 16>>(rdata)) {
                const auto& addr = std::get<std::array<uint8_t, 16>>(rdata);
                char buf[INET6_ADDRSTRLEN];
                inet_ntop(AF_INET6, addr.data(), buf, sizeof(buf));
                return std::string(buf);
            }
            break;
        }
        case RecordType::NS:
        case RecordType::CNAME: {
            if (std::holds_alternative<DnsName>(rdata)) {
                return std::get<DnsName>(rdata).to_string();
            }
            break;
        }
        default: {
            // 显示十六进制
            auto bytes = get_rdata_bytes();
            std::ostringstream oss;
            oss << std::hex;
            for (auto b : bytes) {
                oss << static_cast<int>(b);
            }
            return oss.str();
        }
    }
    return "";
}

// ============================================================================
// DnsMessage 实现
// ============================================================================

std::vector<uint8_t> DnsMessage::serialize() const {
    std::vector<uint8_t> data;

    // 报头
    auto header_data = header_.serialize();
    data.insert(data.end(), header_data.begin(), header_data.end());

    // 查询部分
    for (const auto& q : questions_) {
        auto q_data = q.serialize();
        data.insert(data.end(), q_data.begin(), q_data.end());
    }

    // 回答部分
    for (const auto& rr : answers_) {
        auto rr_data = rr.serialize();
        data.insert(data.end(), rr_data.begin(), rr_data.end());
    }

    // 授权部分
    for (const auto& rr : authorities_) {
        auto rr_data = rr.serialize();
        data.insert(data.end(), rr_data.begin(), rr_data.end());
    }

    // 附加部分
    for (const auto& rr : additionals_) {
        auto rr_data = rr.serialize();
        data.insert(data.end(), rr_data.begin(), rr_data.end());
    }

    return data;
}

std::optional<DnsMessage> DnsMessage::deserialize(std::span<const uint8_t> data) {
    if (data.size() < DNS_HEADER_SIZE) {
        return std::nullopt;
    }

    DnsMessage message;

    // 解析报头
    auto header = DnsHeader::deserialize(data);
    if (!header) {
        return std::nullopt;
    }
    message.header_ = *header;

    size_t pos = DNS_HEADER_SIZE;

    // 解析查询部分
    for (uint16_t i = 0; i < message.header_.qdcount; i++) {
        auto q_result = DnsQuestion::deserialize(data, pos);
        if (!q_result) {
            return std::nullopt;
        }
        message.questions_.push_back(q_result->first);
        pos += q_result->second;
    }

    // 解析回答部分
    for (uint16_t i = 0; i < message.header_.ancount; i++) {
        auto rr_result = ResourceRecord::deserialize(data, pos);
        if (!rr_result) {
            return std::nullopt;
        }
        message.answers_.push_back(rr_result->first);
        pos += rr_result->second;
    }

    // 解析授权部分
    for (uint16_t i = 0; i < message.header_.nscount; i++) {
        auto rr_result = ResourceRecord::deserialize(data, pos);
        if (!rr_result) {
            return std::nullopt;
        }
        message.authorities_.push_back(rr_result->first);
        pos += rr_result->second;
    }

    // 解析附加部分
    for (uint16_t i = 0; i < message.header_.arcount; i++) {
        auto rr_result = ResourceRecord::deserialize(data, pos);
        if (!rr_result) {
            return std::nullopt;
        }
        message.additionals_.push_back(rr_result->first);
        pos += rr_result->second;
    }

    return message;
}

DnsMessage DnsMessage::create_query(const std::string& name,
                                     RecordType type,
                                     bool rd) {
    DnsMessage query;
    query.header_.id = static_cast<uint16_t>(rand() & 0xFFFF);
    query.header_.rd = rd;
    query.header_.qdcount = 1;

    DnsQuestion question;
    question.name = DnsName(name);
    question.type = type;
    question.qclass = QueryClass::IN;
    query.questions_.push_back(question);

    return query;
}

DnsMessage DnsMessage::create_response(const DnsMessage& query,
                                        ResponseCode rcode) {
    DnsMessage response;
    response.header_.id = query.header_.id;
    response.header_.qr = true;
    response.header_.rd = query.header_.rd;
    response.header_.ra = true;
    response.header_.rcode = rcode;
    response.questions_ = query.questions_;
    response.header_.qdcount = query.header_.qdcount;

    return response;
}

void DnsMessage::add_answer(ResourceRecord rr) {
    answers_.push_back(std::move(rr));
    header_.ancount = static_cast<uint16_t>(answers_.size());
}

void DnsMessage::add_authority(ResourceRecord rr) {
    authorities_.push_back(std::move(rr));
    header_.nscount = static_cast<uint16_t>(authorities_.size());
}

void DnsMessage::add_additional(ResourceRecord rr) {
    additionals_.push_back(std::move(rr));
    header_.arcount = static_cast<uint16_t>(additionals_.size());
}

void DnsMessage::set_response(ResponseCode rcode) {
    header_.qr = true;
    header_.ra = true;
    header_.rcode = rcode;
}

std::string DnsMessage::to_string() const {
    std::ostringstream oss;
    oss << "DNS Message (ID: 0x" << std::hex << header_.id << std::dec << ")\n";
    oss << "  QR: " << (header_.qr ? "Response" : "Query") << "\n";
    oss << "  Opcode: " << static_cast<int>(header_.opcode) << "\n";
    oss << "  RCODE: " << response_code_to_string(header_.rcode) << "\n";
    oss << "  Questions: " << header_.qdcount << "\n";
    oss << "  Answers: " << header_.ancount << "\n";
    oss << "  Authorities: " << header_.nscount << "\n";
    oss << "  Additionals: " << header_.arcount << "\n";

    for (const auto& q : questions_) {
        oss << "  Q: " << q.name.to_string() << " "
            << record_type_to_string(q.type) << "\n";
    }
    for (const auto& rr : answers_) {
        oss << "  A: " << rr.name.to_string() << " "
            << rr.ttl << " "
            << record_type_to_string(rr.type) << " "
            << rr.rdata_to_string() << "\n";
    }

    return oss.str();
}

} // namespace dns
