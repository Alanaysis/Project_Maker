/**
 * @file load_balancer_example.cpp
 * @brief DNS 负载均衡器示例
 *
 * 演示如何创建和运行一个 DNS 负载均衡器
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

    std::cout << "=== DNS Load Balancer Example ===" << std::endl;

    // 配置负载均衡器
    LoadBalancerConfig config;
    config.server_config.bind_address = "127.0.0.1";
    config.server_config.port = 5357;

    // 后端服务器 (IP, 权重)
    config.backends = {
        {"8.8.8.8", 10},      // Google DNS - 高权重
        {"8.8.4.4", 10},      // Google DNS - 高权重
        {"1.1.1.1", 5},       // Cloudflare DNS - 中权重
        {"1.0.0.1", 5},       // Cloudflare DNS - 中权重
        {"9.9.9.9", 2},       // Quad9 DNS - 低权重
    };

    // 健康检查配置
    config.health_check_domain = "health.example.com";
    config.health_check_interval = std::chrono::seconds(30);
    config.enable_weighted = true;

    // 创建负载均衡器
    DnsLoadBalancer lb(config);

    // 启动负载均衡器
    if (!lb.start()) {
        std::cerr << "Failed to start load balancer" << std::endl;
        return 1;
    }

    std::cout << "DNS Load Balancer started on 127.0.0.1:5357" << std::endl;
    std::cout << "Backends:" << std::endl;
    for (const auto& [addr, weight] : config.backends) {
        std::cout << "  - " << addr << " (weight: " << weight << ")" << std::endl;
    }
    std::cout << "Strategy: Weighted Round Robin" << std::endl;
    std::cout << "Health check interval: 30s" << std::endl;
    std::cout << "Press Ctrl+C to stop" << std::endl;

    // 运行直到收到信号
    while (running) {
        std::this_thread::sleep_for(std::chrono::seconds(10));

        // 显示后端状态
        auto status = lb.get_backend_status();
        std::cout << "\n=== Backend Status ===" << std::endl;
        for (const auto& s : status) {
            std::cout << s.address
                      << " | Weight: " << s.weight
                      << " | Healthy: " << (s.healthy ? "Yes" : "No")
                      << " | Requests: " << s.requests
                      << " | Avg time: " << std::fixed << std::setprecision(2)
                      << s.avg_response_time_ms << "ms"
                      << std::endl;
        }
    }

    lb.stop();
    std::cout << "\nLoad balancer stopped" << std::endl;

    return 0;
}
