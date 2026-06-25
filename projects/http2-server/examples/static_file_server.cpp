/**
 * @file static_file_server.cpp
 * @brief 静态文件服务器示例
 *
 * 本示例展示如何创建一个静态文件服务器，包括：
 * - 文件服务
 * - 目录列表
 * - MIME 类型检测
 * - 缓存控制
 */

#include "http2_server.h"
#include <iostream>
#include <fstream>
#include <sstream>
#include <signal.h>
#include <filesystem>

using namespace http2;
namespace fs = std::filesystem;

static Http2Server* g_server = nullptr;

void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        std::cout << "\nShutting down server..." << std::endl;
        if (g_server) {
            g_server->stop();
        }
    }
}

int main(int argc, char* argv[]) {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // 默认根目录
    std::string root_dir = "./public";
    int port = 8080;

    // 解析命令行参数
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "-r" || arg == "--root") {
            if (i + 1 < argc) {
                root_dir = argv[++i];
            }
        } else if (arg == "-p" || arg == "--port") {
            if (i + 1 < argc) {
                port = std::stoi(argv[++i]);
            }
        } else if (arg == "-h" || arg == "--help") {
            std::cout << "Usage: " << argv[0] << " [options]" << std::endl;
            std::cout << "Options:" << std::endl;
            std::cout << "  -r, --root <dir>   Root directory (default: ./public)" << std::endl;
            std::cout << "  -p, --port <port>  Port number (default: 8080)" << std::endl;
            std::cout << "  -h, --help         Show this help" << std::endl;
            return 0;
        }
    }

    // 检查根目录是否存在
    if (!fs::exists(root_dir)) {
        std::cout << "Creating root directory: " << root_dir << std::endl;
        fs::create_directories(root_dir);

        // 创建示例文件
        std::ofstream index_file(root_dir + "/index.html");
        index_file << R"(
<!DOCTYPE html>
<html>
<head>
    <title>Static File Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Welcome to Static File Server</h1>
    <p>This is the default index page.</p>
    <p>Edit files in the <code>)" << root_dir << R"(</code> directory.</p>
</body>
</html>
        )";
        index_file.close();

        // 创建示例 CSS 文件
        std::ofstream css_file(root_dir + "/style.css");
        css_file << R"(
body {
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    color: #333;
}

h1 {
    color: #007bff;
}
        )";
        css_file.close();

        // 创建示例 JS 文件
        std::ofstream js_file(root_dir + "/script.js");
        js_file << R"(
console.log('Static file server example');

document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded');
});
        )";
        js_file.close();
    }

    // 创建服务器配置
    ServerConfig config;
    config.host = "0.0.0.0";
    config.port = port;
    config.num_threads = 4;

    // 创建服务器
    Http2Server server(config);
    g_server = &server;

    // 配置静态文件服务
    StaticFileConfig static_config;
    static_config.root_dir = root_dir;
    static_config.index_file = "index.html";
    static_config.enable_directory_listing = true;
    static_config.cache_max_age = 3600;  // 1 小时缓存

    // 添加额外的 MIME 类型
    static_config.mime_types[".md"] = "text/markdown";
    static_config.mime_types[".yaml"] = "application/x-yaml";
    static_config.mime_types[".yml"] = "application/x-yaml";

    server.serve_static("/", static_config);

    // 添加自定义路由
    auto& router = server.get_router();

    // 健康检查端点
    router.get("/health", [](std::shared_ptr<HttpRequest> request,
                             std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");
        response->set_body("{\"status\": \"healthy\"}");
    });

    // 文件信息端点
    router.get("/api/file-info", [&root_dir](std::shared_ptr<HttpRequest> request,
                                             std::shared_ptr<HttpResponse> response) {
        std::string file = request->get_query_param("file");
        if (file.empty()) {
            response->set_status(HttpStatusCode::BAD_REQUEST);
            response->set_content_type("application/json");
            response->set_body("{\"error\": \"Missing file parameter\"}");
            return;
        }

        fs::path file_path = fs::path(root_dir) / file;
        if (!fs::exists(file_path)) {
            response->set_status(HttpStatusCode::NOT_FOUND);
            response->set_content_type("application/json");
            response->set_body("{\"error\": \"File not found\"}");
            return;
        }

        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");

        std::ostringstream json;
        json << "{";
        json << "\"name\": \"" << file_path.filename().string() << "\",";
        json << "\"size\": " << fs::file_size(file_path) << ",";
        json << "\"is_directory\": " << (fs::is_directory(file_path) ? "true" : "false") << ",";
        json << "\"extension\": \"" << file_path.extension().string() << "\"";
        json << "}";

        response->set_body(json.str());
    });

    // 启动服务器
    std::cout << "Starting static file server..." << std::endl;
    std::cout << "Root directory: " << root_dir << std::endl;
    std::cout << "Port: " << port << std::endl;

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
