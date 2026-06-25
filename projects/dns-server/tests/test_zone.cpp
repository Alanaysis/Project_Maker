/**
 * @file test_zone.cpp
 * @brief DNS 区域管理测试
 */

#include "zone/zone_manager.h"

#include <iostream>
#include <cassert>

using namespace dns;

void test_zone_creation() {
    std::cout << "Test: Zone creation... ";

    Zone zone("example.com", ZoneType::PRIMARY);
    assert(zone.name() == "example.com");
    assert(zone.type() == ZoneType::PRIMARY);
    assert(zone.record_count() == 0);

    std::cout << "PASS" << std::endl;
}

void test_zone_add_record() {
    std::cout << "Test: Zone add record... ";

    Zone zone("example.com");

    ResourceRecord rr;
    rr.name = DnsName("www.example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;
    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    assert(zone.add_record(rr));
    assert(zone.record_count() == 1);

    // 查询记录
    auto records = zone.get_records("www.example.com", RecordType::A);
    assert(records.size() == 1);
    assert(records[0].type == RecordType::A);

    std::cout << "PASS" << std::endl;
}

void test_zone_multiple_records() {
    std::cout << "Test: Zone multiple records... ";

    Zone zone("example.com");

    // 添加 A 记录
    ResourceRecord a_rr;
    a_rr.name = DnsName("www.example.com");
    a_rr.type = RecordType::A;
    a_rr.rclass = QueryClass::IN;
    a_rr.ttl = 3600;
    std::array<uint8_t, 4> a_addr = {93, 184, 216, 34};
    a_rr.rdata = a_addr;
    zone.add_record(a_rr);

    // 添加 AAAA 记录
    ResourceRecord aaaa_rr;
    aaaa_rr.name = DnsName("www.example.com");
    aaaa_rr.type = RecordType::AAAA;
    aaaa_rr.rclass = QueryClass::IN;
    aaaa_rr.ttl = 3600;
    std::array<uint8_t, 16> aaaa_addr = {
        0x26, 0x06, 0x28, 0x00, 0x02, 0x20, 0x00, 0x01,
        0x02, 0x48, 0x18, 0x93, 0x25, 0xc8, 0x19, 0x46
    };
    aaaa_rr.rdata = aaaa_addr;
    zone.add_record(aaaa_rr);

    assert(zone.record_count() == 2);

    // 查询所有记录
    auto all = zone.get_all_records("www.example.com");
    assert(all.size() == 2);

    std::cout << "PASS" << std::endl;
}

void test_zone_remove_record() {
    std::cout << "Test: Zone remove record... ";

    Zone zone("example.com");

    ResourceRecord rr;
    rr.name = DnsName("www.example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;
    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    zone.add_record(rr);
    assert(zone.record_count() == 1);

    // 删除记录
    assert(zone.remove_record("www.example.com", RecordType::A));
    assert(zone.record_count() == 0);

    // 重复删除应该失败
    assert(!zone.remove_record("www.example.com", RecordType::A));

    std::cout << "PASS" << std::endl;
}

void test_zone_soa() {
    std::cout << "Test: Zone SOA record... ";

    Zone zone("example.com");

    // 设置 SOA
    SoaData soa;
    soa.mname = DnsName("ns1.example.com");
    soa.rname = DnsName("admin.example.com");
    soa.serial = 2024010101;
    soa.refresh = 3600;
    soa.retry = 900;
    soa.expire = 604800;
    soa.minimum = 86400;

    zone.set_soa(soa);

    // 获取 SOA
    auto soa_rr = zone.get_soa();
    assert(soa_rr.has_value());
    assert(soa_rr->type == RecordType::SOA);

    // 递增序列号
    zone.increment_serial();

    std::cout << "PASS" << std::endl;
}

void test_zone_has_name() {
    std::cout << "Test: Zone has name... ";

    Zone zone("example.com");

    ResourceRecord rr;
    rr.name = DnsName("www.example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;
    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    zone.add_record(rr);

    assert(zone.has_name("www.example.com"));
    assert(!zone.has_name("mail.example.com"));

    std::cout << "PASS" << std::endl;
}

void test_zone_file_parser() {
    std::cout << "Test: Zone file parser... ";

    std::string zone_content = R"(
$ORIGIN example.com.
$TTL 3600

@       IN  SOA   ns1.example.com. admin.example.com. (
                  2024010101  ; Serial
                  3600        ; Refresh
                  900         ; Retry
                  604800      ; Expire
                  86400       ; Minimum TTL
                  )

@       IN  NS    ns1.example.com.
@       IN  NS    ns2.example.com.

ns1     IN  A     192.168.1.1
ns2     IN  A     192.168.1.2

www     IN  A     93.184.216.34
mail    IN  A     192.168.1.10

@       IN  MX    10 mail.example.com.
)";

    ZoneFileParser parser;
    auto zone = parser.parse_string(zone_content, "example.com");
    assert(zone.has_value());

    auto& z = *zone;
    assert(z->name() == "example.com");

    // 检查记录
    auto ns_records = z->get_records("example.com", RecordType::NS);
    assert(ns_records.size() == 2);

    auto a_records = z->get_records("ns1.example.com", RecordType::A);
    assert(a_records.size() == 1);

    auto mx_records = z->get_records("example.com", RecordType::MX);
    assert(mx_records.size() == 1);

    std::cout << "PASS" << std::endl;
}

void test_zone_manager() {
    std::cout << "Test: Zone manager... ";

    ZoneManager manager;

    // 创建区域
    auto zone = std::make_unique<Zone>("example.com");
    zone->add_record([&]() {
        ResourceRecord rr;
        rr.name = DnsName("www.example.com");
        rr.type = RecordType::A;
        rr.rclass = QueryClass::IN;
        rr.ttl = 3600;
        std::array<uint8_t, 4> addr = {93, 184, 216, 34};
        rr.rdata = addr;
        return rr;
    }());

    manager.add_zone(std::move(zone));

    // 查询
    auto records = manager.query("www.example.com", RecordType::A);
    assert(records.size() == 1);

    // 获取区域
    auto* z = manager.get_zone("example.com");
    assert(z != nullptr);
    assert(z->name() == "example.com");

    // 查找区域
    auto* found = manager.find_zone("www.example.com");
    assert(found != nullptr);

    // 获取区域名称列表
    auto names = manager.get_zone_names();
    assert(names.size() == 1);
    assert(names[0] == "example.com");

    std::cout << "PASS" << std::endl;
}

void test_soa_serialization() {
    std::cout << "Test: SOA serialization... ";

    SoaData soa;
    soa.mname = DnsName("ns1.example.com");
    soa.rname = DnsName("admin.example.com");
    soa.serial = 2024010101;
    soa.refresh = 3600;
    soa.retry = 900;
    soa.expire = 604800;
    soa.minimum = 86400;

    auto data = soa.serialize();
    assert(!data.empty());

    auto result = SoaData::deserialize(data);
    assert(result.has_value());
    assert(result->serial == 2024010101);
    assert(result->refresh == 3600);
    assert(result->retry == 900);
    assert(result->expire == 604800);
    assert(result->minimum == 86400);

    std::cout << "PASS" << std::endl;
}

int main() {
    std::cout << "=== DNS Zone Tests ===" << std::endl;

    test_zone_creation();
    test_zone_add_record();
    test_zone_multiple_records();
    test_zone_remove_record();
    test_zone_soa();
    test_zone_has_name();
    test_zone_file_parser();
    test_zone_manager();
    test_soa_serialization();

    std::cout << "\nAll tests passed!" << std::endl;
    return 0;
}
