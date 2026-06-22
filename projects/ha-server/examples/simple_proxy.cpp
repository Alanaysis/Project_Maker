/**
 * @file simple_proxy.cpp
 * @brief 简单代理示例
 *
 * 演示如何使用 HA-Server 框架创建一个简单的反向代理。
 *
 * 使用方法：
 * 1. 启动后端服务器（例如使用 Python http.server）
 * 2. 编译并运行此示例
 * 3. 使用 curl 测试
 *
 * 示例：
 *   # 终端 1：启动后端服务器
 *   python3 -m http.server 8081
 *   python3 -m http.server 8082
 *
 *   # 终端 2：运行代理
 *   ./simple_proxy
 *
 *   # 终端 3：测试请求
 *   curl http://localhost:8080/
 */

#include "../include/server.h"
#include <iostream>
#include <signal.h>
#include <thread>
#include <chrono>

using namespace ha_server;

// 全局服务器指针，用于信号处理
static Server* g_server = nullptr;

/**
 * 信号处理函数
 *
 * 优雅关闭服务器
 */
void signal_handler(int sig) {
    if (g_server) {
        std::cout << "\nReceived signal " << sig << ", stopping server..." << std::endl;
        g_server->stop();
    }
}

/**
 * 打印统计信息
 */
void print_stats(Server& server) {
    auto stats = server.get_stats();
    std::cout << "\n=== Server Statistics ===" << std::endl;
    std::cout << "Total Requests:      " << stats.total_requests.load() << std::endl;
    std::cout << "Successful Requests: " << stats.successful_requests.load() << std::endl;
    std::cout << "Failed Requests:     " << stats.failed_requests.load() << std::endl;
    std::cout << "Active Connections:  " << stats.active_connections.load() << std::endl;
    std::cout << "Total Connections:   " << stats.total_connections.load() << std::endl;

    auto backends = server.get_backend_manager().get_all_backends();
    std::cout << "\n=== Backend Status ===" << std::endl;
    for (auto* backend : backends) {
        std::cout << backend->address() << ": "
                  << (backend->is_healthy() ? "HEALTHY" : "UNHEALTHY")
                  << " (connections=" << backend->get_active_connections()
                  << ", requests=" << backend->total_requests.load()
                  << ", failures=" << backend->failed_requests.load()
                  << ")" << std::endl;
    }
    std::cout << "========================" << std::endl;
}

int main(int argc, char* argv[]) {
    std::cout << "=== HA-Server Simple Proxy Example ===" << std::endl;
    std::cout << std::endl;

    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 创建服务器配置
    ServerConfig config;
    config.host = "0.0.0.0";
    config.port = 8080;
    config.worker_threads = 4;
    config.balancer_type = BalancerType::WeightedRoundRobin;

    // 健康检查配置
    config.health_check.enabled = true;
    config.health_check.interval = std::chrono::milliseconds(5000);
    config.health_check.timeout = std::chrono::milliseconds(3000);
    config.health_check.failure_threshold = 3;

    // 连接池配置
    config.pool_config.max_size = 50;
    config.pool_config.idle_timeout = std::chrono::milliseconds(60000);

    // 创建服务器
    Server server(config);
    g_server = &server;

    // 添加后端服务器
    // 这里添加两个本地后端，你可以根据实际情况修改
    server.add_backend("127.0.0.1", 8081, 5);  // 权重 5
    server.add_backend("127.0.0.1", 8082, 3);  // 权重 3

    std::cout << "Configuration:" << std::endl;
    std::cout << "  Listen: " << config.host << ":" << config.port << std::endl;
    std::cout << "  Balancer: weighted_round_robin" << std::endl;
    std::cout << "  Worker Threads: " << config.worker_threads << std::endl;
    std::cout << "  Health Check: " << (config.health_check.enabled ? "enabled" : "disabled") << std::endl;
    std::cout << std::endl;

    std::cout << "Backends:" << std::endl;
    std::cout << "  127.0.0.1:8081 (weight=5)" << std::endl;
    std::cout << "  127.0.0.1:8082 (weight=3)" << std::endl;
    std::cout << std::endl;

    // 启动服务器
    if (!server.start()) {
        std::cerr << "Failed to start server!" << std::endl;
        return 1;
    }

    std::cout << "Server started. Press Ctrl+C to stop." << std::endl;
    std::cout << std::endl;
    std::cout << "Test with:" << std::endl;
    std::cout << "  curl http://localhost:8080/" << std::endl;
    std::cout << std::endl;

    // 主循环：定期打印统计信息
    while (server.is_running()) {
        std::this_thread::sleep_for(std::chrono::seconds(10));
        if (server.is_running()) {
            print_stats(server);
        }
    }

    std::cout << "Server stopped." << std::endl;
    return 0;
}
