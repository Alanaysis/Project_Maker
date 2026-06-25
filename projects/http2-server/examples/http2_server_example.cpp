/**
 * @file http2_server_example.cpp
 * @brief 基本 HTTP/2 服务器示例
 *
 * 本示例展示如何创建一个基本的 HTTP/2 服务器，包括：
 * - 路由注册
 * - 请求处理
 * - 响应生成
 */

#include "http2_server.h"
#include <iostream>
#include <sstream>
#include <signal.h>

using namespace http2;

// 全局服务器指针，用于信号处理
static Http2Server* g_server = nullptr;

// 信号处理函数
void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        std::cout << "\nShutting down server..." << std::endl;
        if (g_server) {
            g_server->stop();
        }
    }
}

int main() {
    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 创建服务器配置
    ServerConfig config;
    config.host = "0.0.0.0";
    config.port = 8080;
    config.num_threads = 4;
    config.max_connections = 1000;

    // 创建服务器
    Http2Server server(config);
    g_server = &server;

    // 获取路由器
    auto& router = server.get_router();

    // 添加 CORS 中间件
    router.use([&server](std::shared_ptr<HttpRequest> request,
                         std::shared_ptr<HttpResponse> response,
                         std::function<void()> next) {
        response->set_cors_headers();
        if (request->get_method() == HttpMethod::OPTIONS) {
            response->set_status(HttpStatusCode::NO_CONTENT);
            return false;
        }
        next();
        return true;
    });

    // 注册路由

    // 首页
    router.get("/", [](std::shared_ptr<HttpRequest> request,
                       std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("text/html");
        response->set_body(R"(
<!DOCTYPE html>
<html>
<head>
    <title>HTTP/2 Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .method { font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <h1>Welcome to HTTP/2 Server</h1>
    <p>This is a basic HTTP/2 server example.</p>
    <h2>Available Endpoints:</h2>
    <div class="endpoint"><span class="method">GET</span> / - This page</div>
    <div class="endpoint"><span class="method">GET</span> /api/hello - Hello API</div>
    <div class="endpoint"><span class="method">GET</span> /api/time - Current time</div>
    <div class="endpoint"><span class="method">POST</span> /api/echo - Echo request body</div>
    <div class="endpoint"><span class="method">GET</span> /api/headers - Show request headers</div>
</body>
</html>
        )");
    });

    // Hello API
    router.get("/api/hello", [](std::shared_ptr<HttpRequest> request,
                                std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");

        std::string name = request->get_query_param("name");
        if (name.empty()) name = "World";

        response->set_body("{\"message\": \"Hello, " + name + "!\"}");
    });

    // 时间 API
    router.get("/api/time", [](std::shared_ptr<HttpRequest> request,
                               std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");

        time_t now = time(nullptr);
        char buf[64];
        strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", localtime(&now));

        response->set_body("{\"time\": \"" + std::string(buf) + "\"}");
    });

    // Echo API
    router.post("/api/echo", [](std::shared_ptr<HttpRequest> request,
                                std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type(request->get_header("content-type"));
        response->set_body(request->get_body());
    });

    // Headers API
    router.get("/api/headers", [](std::shared_ptr<HttpRequest> request,
                                  std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");

        std::ostringstream json;
        json << "{";
        json << "\"method\": \"" << request->get_method_string() << "\",";
        json << "\"path\": \"" << request->get_path() << "\",";
        json << "\"headers\": {";

        bool first = true;
        for (const auto& header : request->get_headers()) {
            if (!first) json << ",";
            json << "\"" << header.first << "\": \"" << header.second << "\"";
            first = false;
        }

        json << "}}";
        response->set_body(json.str());
    });

    // User API (RESTful 示例)
    router.get("/api/users", [](std::shared_ptr<HttpRequest> request,
                                std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");
        response->set_body(R"({"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]})");
    });

    router.get("/api/users/:id", [](std::shared_ptr<HttpRequest> request,
                                    std::shared_ptr<HttpResponse> response) {
        // 简化处理，实际应该解析路径参数
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");
        response->set_body(R"({"id": 1, "name": "Alice", "email": "alice@example.com"})");
    });

    router.post("/api/users", [](std::shared_ptr<HttpRequest> request,
                                 std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::CREATED);
        response->set_content_type("application/json");
        response->set_body(R"({"id": 3, "name": "New User", "status": "created"})");
    });

    // 404 处理
    router.all("/api/*", [](std::shared_ptr<HttpRequest> request,
                            std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::NOT_FOUND);
        response->set_content_type("application/json");
        response->set_body("{\"error\": \"API endpoint not found\"}");
    });

    // 启动服务器
    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }

    std::cout << "Server started. Press Ctrl+C to stop." << std::endl;

    // 主线程等待
    while (server.is_running()) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    return 0;
}
