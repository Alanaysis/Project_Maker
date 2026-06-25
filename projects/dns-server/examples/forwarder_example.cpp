/**
 * @file forwarder_example.cpp
 * @brief DNS 转发器示例
 *
 * 演示如何创建和运行一个 DNS 转发器
 */

#include "application/dns_forwarder.h"
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

    std::cout << "=== DNS Forwarder Example ===" << std::endl;

    // 配置转发器
    ForwarderConfig config;
    config.server_config.bind_address = "127.0.0.1";
    config.server_config.port = 5356;
    config.server_config.thread_pool_size = 4;

    // 上游服务器
    config.upstream_servers = {
        "8.8.8.8",      // Google DNS
        "8.8.4.4",      // Google DNS
        "1.1.1.1",      // Cloudflare DNS
        "1.0.0.1",      // Cloudflare DNS
    };

    // 转发策略
    config.strategy = ForwardStrategy::ROUND_ROBIN;

    // 缓存配置
    config.enable_cache = true;
    config.cache_config.max_entries = 5000;
    config.cache_config.min_ttl = 30;

    // 创建转发器
    DnsForwarder forwarder(config);

    // 启动转发器
    if (!forwarder.start()) {
        std::cerr << "Failed to start forwarder" << std::endl;
        return 1;
    }

    std::cout << "DNS Forwarder started on 127.0.0.1:5356" << std::endl;
    std::cout << "Upstream servers:" << std::endl;
    for (const auto& server : config.upstream_servers) {
        std::cout << "  - " << server << std::endl;
    }
    std::cout << "Strategy: Round Robin" << std::endl;
    std::cout << "Press Ctrl+C to stop" << std::endl;

    // 运行直到收到信号
    while (running) {
        std::this_thread::sleep_for(std::chrono::seconds(5));

        auto stats = forwarder.get_stats();
        std::cout << "\rQueries: " << stats.queries_received
                  << " | Processed: " << stats.queries_processed
                  << " | Failed: " << stats.queries_failed << std::flush;
    }

    std::cout << std::endl;

    forwarder.stop();
    std::cout << "Forwarder stopped" << std::endl;

    return 0;
}
