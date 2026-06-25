/**
 * @file recursive_server_example.cpp
 * @brief 递归 DNS 服务器示例
 *
 * 演示如何创建和运行一个递归 DNS 服务器
 */

#include "application/recursive_server.h"
#include "monitoring/dns_monitor.h"

#include <iostream>
#include <signal.h>

using namespace dns;

static std::atomic<bool> running{true};

void signal_handler(int sig) {
    running = false;
}

int main() {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 配置日志
    Logger::instance().set_level(LogLevel::INFO);
    Logger::instance().add_sink(std::make_unique<ConsoleSink>());

    std::cout << "=== Recursive DNS Server Example ===" << std::endl;

    // 配置递归服务器
    RecursiveConfig config;
    config.server_config.bind_address = "127.0.0.1";
    config.server_config.port = 5355;
    config.server_config.thread_pool_size = 4;

    // 配置解析器
    config.resolver_config.enable_recursion = true;
    config.resolver_config.enable_cache = true;
    config.resolver_config.max_retries = 3;
    config.resolver_config.query_timeout = std::chrono::seconds(5);

    // 配置转发器 (使用公共 DNS)
    config.resolver_config.forwarders = {
        "8.8.8.8",      // Google DNS
        "8.8.4.4",      // Google DNS
        "1.1.1.1",      // Cloudflare DNS
    };

    // 配置缓存
    config.cache_config.max_entries = 10000;
    config.cache_config.min_ttl = 60;
    config.cache_config.max_ttl = 86400;

    // 创建服务器
    RecursiveServer server(config);

    // 启动服务器
    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }

    std::cout << "Recursive server started on 127.0.0.1:5355" << std::endl;
    std::cout << "Forwarders: 8.8.8.8, 8.8.4.4, 1.1.1.1" << std::endl;
    std::cout << "Press Ctrl+C to stop" << std::endl;

    // 运行直到收到信号
    while (running) {
        std::this_thread::sleep_for(std::chrono::seconds(10));

        // 显示统计信息
        auto stats = server.get_stats();
        auto cache_stats = server.get_cache_stats();

        std::cout << "\n=== Statistics ===" << std::endl;
        std::cout << "Queries received: " << stats.queries_received << std::endl;
        std::cout << "Queries processed: " << stats.queries_processed << std::endl;
        std::cout << "Queries failed: " << stats.queries_failed << std::endl;
        std::cout << "Cache size: " << cache_stats.current_size << std::endl;
        std::cout << "Cache hit rate: " << std::fixed << std::setprecision(1)
                  << (cache_stats.hit_rate() * 100) << "%" << std::endl;
    }

    server.stop();
    std::cout << "\nServer stopped" << std::endl;

    return 0;
}
