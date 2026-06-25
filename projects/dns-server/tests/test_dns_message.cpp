/**
 * @file test_dns_message.cpp
 * @brief DNS 报文测试
 */

#include "protocol/dns_message.h"

#include <iostream>
#include <cassert>
#include <cstring>

using namespace dns;

void test_header_serialize() {
    std::cout << "Test: Header serialize/deserialize... ";

    DnsHeader header;
    header.id = 0x1234;
    header.qr = true;
    header.opcode = Opcode::QUERY;
    header.aa = true;
    header.tc = false;
    header.rd = true;
    header.ra = true;
    header.rcode = ResponseCode::NO_ERROR;
    header.qdcount = 1;
    header.ancount = 2;
    header.nscount = 1;
    header.arcount = 0;

    auto data = header.serialize();
    assert(data.size() == DNS_HEADER_SIZE);

    auto result = DnsHeader::deserialize(data);
    assert(result.has_value());
    assert(result->id == 0x1234);
    assert(result->qr == true);
    assert(result->opcode == Opcode::QUERY);
    assert(result->aa == true);
    assert(result->tc == false);
    assert(result->rd == true);
    assert(result->ra == true);
    assert(result->rcode == ResponseCode::NO_ERROR);
    assert(result->qdcount == 1);
    assert(result->ancount == 2);
    assert(result->nscount == 1);
    assert(result->arcount == 0);

    std::cout << "PASS" << std::endl;
}

void test_name_serialize() {
    std::cout << "Test: Name serialize/deserialize... ";

    DnsName name("www.example.com");
    auto data = name.serialize();
    assert(!data.empty());
    assert(data.back() == 0);  // 结束标记

    auto result = DnsName::deserialize(data, 0);
    assert(result.has_value());
    assert(result->first.to_string() == "www.example.com");

    std::cout << "PASS" << std::endl;
}

void test_name_root() {
    std::cout << "Test: Root name... ";

    DnsName name(".");
    assert(name.empty());

    DnsName root("");
    auto data = root.serialize();
    assert(data.size() == 1);
    assert(data[0] == 0);

    std::cout << "PASS" << std::endl;
}

void test_question_serialize() {
    std::cout << "Test: Question serialize/deserialize... ";

    DnsQuestion question;
    question.name = DnsName("example.com");
    question.type = RecordType::A;
    question.qclass = QueryClass::IN;

    auto data = question.serialize();
    assert(!data.empty());

    auto result = DnsQuestion::deserialize(data, 0);
    assert(result.has_value());
    assert(result->first.name.to_string() == "example.com");
    assert(result->first.type == RecordType::A);
    assert(result->first.qclass == QueryClass::IN);

    std::cout << "PASS" << std::endl;
}

void test_a_record() {
    std::cout << "Test: A record... ";

    ResourceRecord rr;
    rr.name = DnsName("example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;

    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    auto data = rr.serialize();
    assert(!data.empty());

    auto result = ResourceRecord::deserialize(data, 0);
    assert(result.has_value());
    assert(result->first.type == RecordType::A);
    assert(result->first.ttl == 3600);
    bool is_a_record = std::holds_alternative<std::array<uint8_t, 4>>(result->first.rdata);
    assert(is_a_record);

    auto& result_addr = std::get<std::array<uint8_t, 4>>(result->first.rdata);
    assert(result_addr == addr);

    std::cout << "PASS" << std::endl;
}

void test_aaaa_record() {
    std::cout << "Test: AAAA record... ";

    ResourceRecord rr;
    rr.name = DnsName("example.com");
    rr.type = RecordType::AAAA;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;

    std::array<uint8_t, 16> addr = {
        0x26, 0x06, 0x28, 0x00, 0x02, 0x20, 0x00, 0x01,
        0x02, 0x48, 0x18, 0x93, 0x25, 0xc8, 0x19, 0x46
    };
    rr.rdata = addr;

    auto data = rr.serialize();
    assert(!data.empty());

    auto result = ResourceRecord::deserialize(data, 0);
    assert(result.has_value());
    assert(result->first.type == RecordType::AAAA);
    bool is_aaaa_record = std::holds_alternative<std::array<uint8_t, 16>>(result->first.rdata);
    assert(is_aaaa_record);

    std::cout << "PASS" << std::endl;
}

void test_cname_record() {
    std::cout << "Test: CNAME record... ";

    ResourceRecord rr;
    rr.name = DnsName("www.example.com");
    rr.type = RecordType::CNAME;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;
    rr.rdata = DnsName("example.com");

    auto data = rr.serialize();
    assert(!data.empty());

    auto result = ResourceRecord::deserialize(data, 0);
    assert(result.has_value());
    assert(result->first.type == RecordType::CNAME);
    assert(std::holds_alternative<DnsName>(result->first.rdata));
    assert(std::get<DnsName>(result->first.rdata).to_string() == "example.com");

    std::cout << "PASS" << std::endl;
}

void test_message_serialize() {
    std::cout << "Test: Message serialize/deserialize... ";

    // 创建查询
    auto query = DnsMessage::create_query("example.com", RecordType::A);
    auto data = query.serialize();
    assert(!data.empty());

    auto result = DnsMessage::deserialize(data);
    assert(result.has_value());
    assert(result->header().id == query.header().id);
    assert(result->header().qr == false);
    assert(result->header().rd == true);
    assert(result->questions().size() == 1);
    assert(result->questions()[0].name.to_string() == "example.com");
    assert(result->questions()[0].type == RecordType::A);

    std::cout << "PASS" << std::endl;
}

void test_response_create() {
    std::cout << "Test: Response creation... ";

    auto query = DnsMessage::create_query("example.com", RecordType::A);
    auto response = DnsMessage::create_response(query, ResponseCode::NO_ERROR);

    assert(response.header().id == query.header().id);
    assert(response.header().qr == true);
    assert(response.header().ra == true);
    assert(response.questions().size() == 1);

    // 添加回答
    ResourceRecord rr;
    rr.name = DnsName("example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;
    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    response.add_answer(rr);
    assert(response.answers().size() == 1);
    assert(response.header().ancount == 1);

    std::cout << "PASS" << std::endl;
}

void test_record_type_conversion() {
    std::cout << "Test: Record type conversion... ";

    assert(std::string(record_type_to_string(RecordType::A)) == "A");
    assert(std::string(record_type_to_string(RecordType::AAAA)) == "AAAA");
    assert(std::string(record_type_to_string(RecordType::MX)) == "MX");
    assert(std::string(record_type_to_string(RecordType::CNAME)) == "CNAME");
    assert(std::string(record_type_to_string(RecordType::NS)) == "NS");

    assert(string_to_record_type("A") == RecordType::A);
    assert(string_to_record_type("AAAA") == RecordType::AAAA);
    assert(string_to_record_type("MX") == RecordType::MX);
    assert(string_to_record_type("CNAME") == RecordType::CNAME);

    std::cout << "PASS" << std::endl;
}

void test_response_code_conversion() {
    std::cout << "Test: Response code conversion... ";

    assert(std::string(response_code_to_string(ResponseCode::NO_ERROR)) == "NOERROR");
    assert(std::string(response_code_to_string(ResponseCode::FORMAT_ERROR)) == "FORMERR");
    assert(std::string(response_code_to_string(ResponseCode::SERVER_FAILURE)) == "SERVFAIL");
    assert(std::string(response_code_to_string(ResponseCode::NAME_ERROR)) == "NXDOMAIN");
    assert(std::string(response_code_to_string(ResponseCode::REFUSED)) == "REFUSED");

    std::cout << "PASS" << std::endl;
}

void test_message_to_string() {
    std::cout << "Test: Message to string... ";

    auto query = DnsMessage::create_query("example.com", RecordType::A);
    auto str = query.to_string();
    assert(!str.empty());
    assert(str.find("example.com") != std::string::npos);

    std::cout << "PASS" << std::endl;
}

int main() {
    std::cout << "=== DNS Message Tests ===" << std::endl;

    test_header_serialize();
    test_name_serialize();
    test_name_root();
    test_question_serialize();
    test_a_record();
    test_aaaa_record();
    test_cname_record();
    test_message_serialize();
    test_response_create();
    test_record_type_conversion();
    test_response_code_conversion();
    test_message_to_string();

    std::cout << "\nAll tests passed!" << std::endl;
    return 0;
}
