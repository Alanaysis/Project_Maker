/**
 * @file dns_client_example.cpp
 * @brief DNS 客户端示例
 *
 * 演示如何使用 DNS 解析器进行各种查询
 */

#include "resolver/dns_resolver.h"
#include "monitoring/dns_monitor.h"

#include <iostream>
#include <iomanip>

using namespace dns;

void print_separator() {
    std::cout << std::string(60, '-') << std::endl;
}

void query_and_print(DnsResolver& resolver,
                     const std::string& name,
                     RecordType type) {
    std::cout << "\nQuery: " << name << " "
              << record_type_to_string(type) << std::endl;
    print_separator();

    auto result = resolver.resolve(name, type);

    std::cout << "Status: " << response_code_to_string(result.status) << std::endl;
    std::cout << "From cache: " << (result.from_cache ? "Yes" : "No") << std::endl;
    std::cout << "Resolve time: " << result.resolve_time.count() << "ms" << std::endl;

    if (!result.answers.empty()) {
        std::cout << "\nAnswers (" << result.answers.size() << "):" << std::endl;
        for (const auto& rr : result.answers) {
            std::cout << "  " << rr.name.to_string()
                      << " " << rr.ttl
                      << " IN " << record_type_to_string(rr.type)
                      << " " << rr.rdata_to_string() << std::endl;
        }
    }

    if (!result.authorities.empty()) {
        std::cout << "\nAuthorities (" << result.authorities.size() << "):" << std::endl;
        for (const auto& rr : result.authorities) {
            std::cout << "  " << rr.name.to_string()
                      << " " << rr.ttl
                      << " IN " << record_type_to_string(rr.type)
                      << " " << rr.rdata_to_string() << std::endl;
        }
    }
}

int main() {
    // 配置日志
    Logger::instance().set_level(LogLevel::WARN);
    Logger::instance().add_sink(std::make_unique<ConsoleSink>());

    std::cout << "=== DNS Client Example ===" << std::endl;

    // 创建解析器
    ResolverConfig config;
    config.enable_recursion = true;
    config.enable_cache = true;
    config.forwarders = {"8.8.8.8", "1.1.1.1"};

    DnsResolver resolver(config);

    // 查询 A 记录
    query_and_print(resolver, "www.google.com", RecordType::A);

    // 查询 AAAA 记录
    query_and_print(resolver, "www.google.com", RecordType::AAAA);

    // 查询 MX 记录
    query_and_print(resolver, "google.com", RecordType::MX);

    // 查询 NS 记录
    query_and_print(resolver, "google.com", RecordType::NS);

    // 查询 TXT 记录
    query_and_print(resolver, "google.com", RecordType::TXT);

    // 查询 CNAME 记录
    query_and_print(resolver, "www.github.com", RecordType::CNAME);

    // 查询 SRV 记录
    query_and_print(resolver, "_http._tcp.example.com", RecordType::SRV);

    // 反向解析
    std::cout << "\n=== Reverse DNS ===" << std::endl;
    print_separator();
    auto reverse_result = resolver.reverse_resolve("8.8.8.8");
    std::cout << "Reverse lookup for 8.8.8.8:" << std::endl;
    std::cout << "Status: " << response_code_to_string(reverse_result.status) << std::endl;
    for (const auto& rr : reverse_result.answers) {
        std::cout << "  " << rr.name.to_string()
                  << " -> " << rr.rdata_to_string() << std::endl;
    }

    // 缓存统计
    auto cache_stats = resolver.get_cache_stats();
    std::cout << "\n=== Cache Statistics ===" << std::endl;
    print_separator();
    std::cout << "Hits: " << cache_stats.hits << std::endl;
    std::cout << "Misses: " << cache_stats.misses << std::endl;
    std::cout << "Hit rate: " << std::fixed << std::setprecision(1)
              << (cache_stats.hit_rate() * 100) << "%" << std::endl;
    std::cout << "Cache size: " << cache_stats.current_size << std::endl;

    return 0;
}
