/**
 * @file test_cache.cpp
 * @brief DNS 缓存测试
 */

#include "resolver/dns_cache.h"

#include <iostream>
#include <cassert>
#include <thread>
#include <chrono>

using namespace dns;

void test_basic_cache() {
    std::cout << "Test: Basic cache operations... ";

    DnsCache cache;

    // 创建测试记录
    ResourceRecord rr;
    rr.name = DnsName("example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;
    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    std::vector<ResourceRecord> records = {rr};

    // 插入缓存
    cache.put("example.com", RecordType::A, records, 3600);

    // 查询缓存
    auto result = cache.get("example.com", RecordType::A);
    assert(result.has_value());
    assert(result->records.size() == 1);
    assert(result->records[0].type == RecordType::A);

    // 未命中
    auto miss = cache.get("notfound.com", RecordType::A);
    assert(!miss.has_value());

    std::cout << "PASS" << std::endl;
}

void test_cache_expiry() {
    std::cout << "Test: Cache expiry... ";

    CacheConfig config;
    config.min_ttl = 1;  // 1 秒最小 TTL
    DnsCache cache(config);

    ResourceRecord rr;
    rr.name = DnsName("example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 1;

    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    std::vector<ResourceRecord> records = {rr};

    // 插入缓存 (1 秒 TTL)
    cache.put("example.com", RecordType::A, records, 1);

    // 立即查询应该命中
    auto result = cache.get("example.com", RecordType::A);
    assert(result.has_value());

    // 等待过期
    std::this_thread::sleep_for(std::chrono::seconds(2));

    // 过期后应该未命中
    auto expired = cache.get("example.com", RecordType::A);
    assert(!expired.has_value());

    std::cout << "PASS" << std::endl;
}

void test_cache_eviction() {
    std::cout << "Test: Cache eviction (LRU)... ";

    CacheConfig config;
    config.max_entries = 3;  // 最多 3 个条目
    DnsCache cache(config);

    // 插入 4 个条目
    for (int i = 0; i < 4; i++) {
        ResourceRecord rr;
        rr.name = DnsName("host" + std::to_string(i) + ".com");
        rr.type = RecordType::A;
        rr.rclass = QueryClass::IN;
        rr.ttl = 3600;

        std::array<uint8_t, 4> addr = {192, 168, 1, static_cast<uint8_t>(i)};
        rr.rdata = addr;

        std::vector<ResourceRecord> records = {rr};
        cache.put("host" + std::to_string(i) + ".com", RecordType::A,
                  records, 3600);
    }

    // 第一个条目应该被淘汰
    auto result = cache.get("host0.com", RecordType::A);
    assert(!result.has_value());

    // 其他条目应该存在
    auto result1 = cache.get("host1.com", RecordType::A);
    assert(result1.has_value());

    auto result2 = cache.get("host2.com", RecordType::A);
    assert(result2.has_value());

    auto result3 = cache.get("host3.com", RecordType::A);
    assert(result3.has_value());

    std::cout << "PASS" << std::endl;
}

void test_negative_cache() {
    std::cout << "Test: Negative cache... ";

    CacheConfig config;
    config.enable_negative_cache = true;
    config.negative_ttl = 60;
    DnsCache cache(config);

    // 插入负缓存
    cache.put_negative("notexist.com", RecordType::A, ResponseCode::NAME_ERROR);

    // 检查负缓存
    assert(cache.is_negative_cached("notexist.com", RecordType::A));

    // 未缓存的域名
    assert(!cache.is_negative_cached("other.com", RecordType::A));

    std::cout << "PASS" << std::endl;
}

void test_cache_stats() {
    std::cout << "Test: Cache statistics... ";

    DnsCache cache;

    ResourceRecord rr;
    rr.name = DnsName("example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;

    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    std::vector<ResourceRecord> records = {rr};

    // 插入并查询
    cache.put("example.com", RecordType::A, records, 3600);
    cache.get("example.com", RecordType::A);  // 命中
    cache.get("notfound.com", RecordType::A);  // 未命中

    auto stats = cache.get_stats();
    assert(stats.hits == 1);
    assert(stats.misses == 1);
    assert(stats.inserts == 1);
    assert(stats.current_size == 1);

    double expected_rate = 0.5;
    assert(std::abs(stats.hit_rate() - expected_rate) < 0.01);

    std::cout << "PASS" << std::endl;
}

void test_cache_remove() {
    std::cout << "Test: Cache remove... ";

    DnsCache cache;

    ResourceRecord rr;
    rr.name = DnsName("example.com");
    rr.type = RecordType::A;
    rr.rclass = QueryClass::IN;
    rr.ttl = 3600;

    std::array<uint8_t, 4> addr = {93, 184, 216, 34};
    rr.rdata = addr;

    std::vector<ResourceRecord> records = {rr};

    // 插入并删除
    cache.put("example.com", RecordType::A, records, 3600);
    assert(cache.size() == 1);

    cache.remove("example.com", RecordType::A);
    assert(cache.size() == 0);

    auto result = cache.get("example.com", RecordType::A);
    assert(!result.has_value());

    std::cout << "PASS" << std::endl;
}

void test_cache_clear() {
    std::cout << "Test: Cache clear... ";

    DnsCache cache;

    // 插入多个条目
    for (int i = 0; i < 10; i++) {
        ResourceRecord rr;
        rr.name = DnsName("host" + std::to_string(i) + ".com");
        rr.type = RecordType::A;
        rr.rclass = QueryClass::IN;
        rr.ttl = 3600;

        std::array<uint8_t, 4> addr = {192, 168, 1, static_cast<uint8_t>(i)};
        rr.rdata = addr;

        std::vector<ResourceRecord> records = {rr};
        cache.put("host" + std::to_string(i) + ".com", RecordType::A,
                  records, 3600);
    }

    assert(cache.size() == 10);

    // 清除所有
    cache.clear();
    assert(cache.size() == 0);

    std::cout << "PASS" << std::endl;
}

int main() {
    std::cout << "=== DNS Cache Tests ===" << std::endl;

    test_basic_cache();
    test_cache_expiry();
    test_cache_eviction();
    test_negative_cache();
    test_cache_stats();
    test_cache_remove();
    test_cache_clear();

    std::cout << "\nAll tests passed!" << std::endl;
    return 0;
}
