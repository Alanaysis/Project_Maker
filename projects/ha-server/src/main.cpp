/**
 * @file main.cpp
 * @brief 主程序入口
 *
 * HA-Server 高可用服务器的主入口文件。
 * 支持命令行参数配置。
 */

#include "../include/server.h"
#include <iostream>
#include <string>
#include <signal.h>

using namespace ha_server;

static Server* g_server = nullptr;

void signal_handler(int sig) {
    if (g_server) {
        std::cout << "\nReceived signal " << sig << ", shutting down..." << std::endl;
        g_server->stop();
    }
}

void print_usage(const char* program) {
    std::cout << "Usage: " << program << " [options]" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -h, --host <host>       Listen host (default: 0.0.0.0)" << std::endl;
    std::cout << "  -p, --port <port>       Listen port (default: 8080)" << std::endl;
    std::cout << "  -w, --workers <n>       Worker threads (default: 4)" << std::endl;
    std::cout << "  -b, --backend <h:p:w>   Add backend (host:port:weight)" << std::endl;
    std::cout << "  --help                  Show this help" << std::endl;
    std::cout << std::endl;
    std::cout << "Example:" << std::endl;
    std::cout << "  " << program << " -p 8080 -b 127.0.0.1:8081:5 -b 127.0.0.1:8082:3" << std::endl;
}

int main(int argc, char* argv[]) {
    // 默认配置
    ServerConfig config;
    config.host = "0.0.0.0";
    config.port = 8080;
    config.worker_threads = 4;
    config.balancer_type = BalancerType::WeightedRoundRobin;

    // 后端列表
    struct BackendArg {
        std::string host;
        int port;
        int weight;
    };
    std::vector<BackendArg> backends;

    // 解析命令行参数
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];

        if (arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
        else if ((arg == "-h" || arg == "--host") && i + 1 < argc) {
            config.host = argv[++i];
        }
        else if ((arg == "-p" || arg == "--port") && i + 1 < argc) {
            config.port = std::stoi(argv[++i]);
        }
        else if ((arg == "-w" || arg == "--workers") && i + 1 < argc) {
            config.worker_threads = std::stoi(argv[++i]);
        }
        else if ((arg == "-b" || arg == "--backend") && i + 1 < argc) {
            std::string backend_str = argv[++i];
            // 解析 host:port:weight 格式
            size_t pos1 = backend_str.find(':');
            if (pos1 != std::string::npos) {
                size_t pos2 = backend_str.find(':', pos1 + 1);
                if (pos2 != std::string::npos) {
                    BackendArg ba;
                    ba.host = backend_str.substr(0, pos1);
                    ba.port = std::stoi(backend_str.substr(pos1 + 1, pos2 - pos1 - 1));
                    ba.weight = std::stoi(backend_str.substr(pos2 + 1));
                    backends.push_back(ba);
                }
            }
        }
        else {
            std::cerr << "Unknown option: " << arg << std::endl;
            print_usage(argv[0]);
            return 1;
        }
    }

    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 创建服务器
    Server server(config);
    g_server = &server;

    // 添加后端
    if (backends.empty()) {
        // 默认后端
        server.add_backend("127.0.0.1", 8081, 5);
        server.add_backend("127.0.0.1", 8082, 3);
        std::cout << "No backends specified, using defaults:" << std::endl;
        std::cout << "  127.0.0.1:8081 (weight=5)" << std::endl;
        std::cout << "  127.0.0.1:8082 (weight=3)" << std::endl;
    } else {
        for (const auto& ba : backends) {
            server.add_backend(ba.host, ba.port, ba.weight);
            std::cout << "Backend: " << ba.host << ":" << ba.port
                      << " (weight=" << ba.weight << ")" << std::endl;
        }
    }

    std::cout << std::endl;

    // 启动服务器
    if (!server.start()) {
        std::cerr << "Failed to start server!" << std::endl;
        return 1;
    }

    std::cout << "Server started on " << config.host << ":" << config.port << std::endl;
    std::cout << "Balancer: weighted_round_robin" << std::endl;
    std::cout << "Workers: " << config.worker_threads << std::endl;
    std::cout << std::endl;
    std::cout << "Press Ctrl+C to stop." << std::endl;

    // 等待服务器停止
    while (server.is_running()) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    return 0;
}
