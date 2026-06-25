/**
 * @file reverse_proxy.cpp
 * @brief 反向代理服务器示例
 *
 * 本示例展示如何创建一个反向代理服务器，包括：
 * - 请求转发
 * - 负载均衡
 * - 健康检查
 * - 错误处理
 */

#include "http2_server.h"
#include <iostream>
#include <sstream>
#include <signal.h>
#include <vector>
#include <atomic>
#include <random>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>

using namespace http2;

static Http2Server* g_server = nullptr;
static std::atomic<bool> g_running{true};

void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        std::cout << "\nShutting down server..." << std::endl;
        g_running = false;
        if (g_server) {
            g_server->stop();
        }
    }
}

// 后端服务器配置
struct BackendServer {
    std::string host;
    int port;
    std::atomic<bool> healthy{true};
    std::atomic<int> connections{0};

    BackendServer(const std::string& h, int p) : host(h), port(p) {}

    std::string address() const {
        return host + ":" + std::to_string(port);
    }
};

// 负载均衡策略
enum class LoadBalanceStrategy {
    ROUND_ROBIN,
    LEAST_CONNECTIONS,
    RANDOM
};

// 负载均衡器
class LoadBalancer {
public:
    LoadBalancer(LoadBalanceStrategy strategy = LoadBalanceStrategy::ROUND_ROBIN)
        : strategy_(strategy) {}

    void add_backend(const std::string& host, int port) {
        backends_.push_back(std::shared_ptr<BackendServer>(new BackendServer(host, port)));
    }

    std::shared_ptr<BackendServer> get_backend() {
        if (backends_.empty()) return nullptr;

        std::vector<std::shared_ptr<BackendServer>> healthy_backends;
        for (auto& backend : backends_) {
            if (backend->healthy) {
                healthy_backends.push_back(backend);
            }
        }

        if (healthy_backends.empty()) {
            return nullptr;
        }

        switch (strategy_) {
            case LoadBalanceStrategy::ROUND_ROBIN:
                return get_round_robin(healthy_backends);
            case LoadBalanceStrategy::LEAST_CONNECTIONS:
                return get_least_connections(healthy_backends);
            case LoadBalanceStrategy::RANDOM:
                return get_random(healthy_backends);
            default:
                return healthy_backends[0];
        }
    }

    const std::vector<std::shared_ptr<BackendServer>>& get_backends() const {
        return backends_;
    }

private:
    LoadBalanceStrategy strategy_;
    std::vector<std::shared_ptr<BackendServer>> backends_;
    std::atomic<size_t> round_robin_index_{0};
    std::random_device rd_;
    std::mt19937 gen_{rd_()};

    std::shared_ptr<BackendServer> get_round_robin(const std::vector<std::shared_ptr<BackendServer>>& backends) {
        size_t index = round_robin_index_++ % backends.size();
        return backends[index];
    }

    std::shared_ptr<BackendServer> get_least_connections(const std::vector<std::shared_ptr<BackendServer>>& backends) {
        auto min_it = std::min_element(backends.begin(), backends.end(),
            [](const auto& a, const auto& b) {
                return a->connections < b->connections;
            });
        return *min_it;
    }

    std::shared_ptr<BackendServer> get_random(const std::vector<std::shared_ptr<BackendServer>>& backends) {
        std::uniform_int_distribution<size_t> dist(0, backends.size() - 1);
        return backends[dist(gen_)];
    }
};

// 简单的 HTTP 客户端（用于代理请求）
class HttpClient {
public:
    struct Response {
        int status_code;
        std::map<std::string, std::string> headers;
        std::vector<uint8_t> body;
    };

    static Response request(const std::string& host, int port,
                           const std::string& method, const std::string& path,
                           const std::map<std::string, std::string>& headers = {},
                           const std::vector<uint8_t>& body = {}) {
        Response response;

        // 创建 socket
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            response.status_code = 500;
            return response;
        }

        // 连接后端
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        inet_pton(AF_INET, host.c_str(), &addr.sin_addr);

        if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            close(sock);
            response.status_code = 502;
            return response;
        }

        // 构造 HTTP/1.1 请求
        std::ostringstream request;
        request << method << " " << path << " HTTP/1.1\r\n";
        request << "Host: " << host << ":" << port << "\r\n";
        for (const auto& header : headers) {
            request << header.first << ": " << header.second << "\r\n";
        }
        if (!body.empty()) {
            request << "Content-Length: " << body.size() << "\r\n";
        }
        request << "\r\n";

        // 发送请求
        std::string request_str = request.str();
        send(sock, request_str.c_str(), request_str.size(), 0);
        if (!body.empty()) {
            send(sock, body.data(), body.size(), 0);
        }

        // 接收响应（简化实现）
        char buffer[4096];
        ssize_t n = recv(sock, buffer, sizeof(buffer), 0);
        if (n > 0) {
            // 解析响应（简化）
            response.status_code = 200;
            response.body.assign(buffer, buffer + n);
        } else {
            response.status_code = 502;
        }

        close(sock);
        return response;
    }
};

int main(int argc, char* argv[]) {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 解析命令行参数
    int port = 8080;
    LoadBalanceStrategy strategy = LoadBalanceStrategy::ROUND_ROBIN;
    std::vector<std::pair<std::string, int>> backends;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-p" || arg == "--port") {
            if (i + 1 < argc) {
                port = std::stoi(argv[++i]);
            }
        } else if (arg == "-s" || arg == "--strategy") {
            if (i + 1 < argc) {
                std::string s = argv[++i];
                if (s == "round-robin") strategy = LoadBalanceStrategy::ROUND_ROBIN;
                else if (s == "least-connections") strategy = LoadBalanceStrategy::LEAST_CONNECTIONS;
                else if (s == "random") strategy = LoadBalanceStrategy::RANDOM;
            }
        } else if (arg == "-b" || arg == "--backend") {
            if (i + 1 < argc) {
                std::string backend = argv[++i];
                size_t colon = backend.find(':');
                if (colon != std::string::npos) {
                    std::string host = backend.substr(0, colon);
                    int backend_port = std::stoi(backend.substr(colon + 1));
                    backends.push_back({host, backend_port});
                }
            }
        } else if (arg == "-h" || arg == "--help") {
            std::cout << "Usage: " << argv[0] << " [options]" << std::endl;
            std::cout << "Options:" << std::endl;
            std::cout << "  -p, --port <port>        Port number (default: 8080)" << std::endl;
            std::cout << "  -s, --strategy <strategy> Load balance strategy (round-robin, least-connections, random)" << std::endl;
            std::cout << "  -b, --backend <host:port> Add backend server (can be used multiple times)" << std::endl;
            std::cout << "  -h, --help               Show this help" << std::endl;
            return 0;
        }
    }

    // 如果没有指定后端，使用默认后端
    if (backends.empty()) {
        backends.push_back({"127.0.0.1", 8081});
        backends.push_back({"127.0.0.1", 8082});
    }

    // 创建负载均衡器
    LoadBalancer lb(strategy);
    for (const auto& backend : backends) {
        lb.add_backend(backend.first, backend.second);
        std::cout << "Added backend: " << backend.first << ":" << backend.second << std::endl;
    }

    // 创建服务器
    ServerConfig config;
    config.host = "0.0.0.0";
    config.port = port;
    config.num_threads = 4;

    Http2Server server(config);
    g_server = &server;

    auto& router = server.get_router();

    // 健康检查端点
    router.get("/health", [&lb](std::shared_ptr<HttpRequest> request,
                                std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");

        std::ostringstream json;
        json << "{\"status\": \"healthy\", \"backends\": [";
        bool first = true;
        for (const auto& backend : lb.get_backends()) {
            if (!first) json << ",";
            json << "{\"address\": \"" << backend->address() << "\""
                 << ", \"healthy\": " << (backend->healthy ? "true" : "false")
                 << ", \"connections\": " << backend->connections << "}";
            first = false;
        }
        json << "]}";

        response->set_body(json.str());
    });

    // 代理所有请求
    router.all("/*", [&lb](std::shared_ptr<HttpRequest> request,
                           std::shared_ptr<HttpResponse> response) {
        // 获取后端服务器
        auto backend = lb.get_backend();
        if (!backend) {
            response->set_status(HttpStatusCode::SERVICE_UNAVAILABLE);
            response->set_content_type("application/json");
            response->set_body("{\"error\": \"No healthy backends available\"}");
            return;
        }

        // 增加连接计数
        backend->connections++;

        std::cout << "Proxying " << request->get_method_string() << " " << request->get_path()
                  << " to " << backend->address() << std::endl;

        // 转发请求
        auto proxy_response = HttpClient::request(
            backend->host,
            backend->port,
            request->get_method_string(),
            request->get_path(),
            request->get_headers(),
            request->get_body()
        );

        // 减少连接计数
        backend->connections--;

        // 返回响应
        response->set_status(static_cast<HttpStatusCode>(proxy_response.status_code));
        for (const auto& header : proxy_response.headers) {
            response->set_header(header.first, header.second);
        }
        response->set_body(proxy_response.body);
    });

    // 启动服务器
    std::cout << "Starting reverse proxy server..." << std::endl;
    std::cout << "Port: " << port << std::endl;
    std::cout << "Strategy: " << (strategy == LoadBalanceStrategy::ROUND_ROBIN ? "round-robin" :
                                  strategy == LoadBalanceStrategy::LEAST_CONNECTIONS ? "least-connections" :
                                  "random") << std::endl;

    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }

    std::cout << "Server started. Press Ctrl+C to stop." << std::endl;

    while (server.is_running()) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    return 0;
}
