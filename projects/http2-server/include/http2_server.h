#pragma once
/**
 * @file http2_server.h
 * @brief HTTP/2 服务器
 *
 * HTTP/2 服务器提供：
 * - TCP 监听和连接接受
 * - TLS 支持（可选）
 * - 静态文件服务
 * - 动态内容路由
 * - 中间件支持
 */

#include <cstdint>
#include <string>
#include <memory>
#include <functional>
#include <vector>
#include <map>
#include <atomic>
#include <thread>
#include <mutex>

#include "http2_connection.h"
#include "http2_request.h"
#include "http2_response.h"

namespace http2 {

// 路由匹配器
class Router {
public:
    // 注册路由
    void get(const std::string& path, RequestHandler handler);
    void post(const std::string& path, RequestHandler handler);
    void put(const std::string& path, RequestHandler handler);
    void del(const std::string& path, RequestHandler handler);
    void head(const std::string& path, RequestHandler handler);
    void options(const std::string& path, RequestHandler handler);
    void all(const std::string& path, RequestHandler handler);

    // 匹配路由
    RequestHandler match(HttpMethod method, const std::string& path) const;

    // 添加中间件
    using Middleware = std::function<bool(std::shared_ptr<HttpRequest>,
                                         std::shared_ptr<HttpResponse>,
                                         std::function<void()>)>;
    void use(Middleware middleware);

    // 执行中间件链
    bool execute_middleware(std::shared_ptr<HttpRequest> request,
                          std::shared_ptr<HttpResponse> response,
                          std::function<void()> final_handler);

private:
    struct Route {
        HttpMethod method;
        std::string path;
        RequestHandler handler;
    };

    std::vector<Route> routes_;
    std::vector<Middleware> middlewares_;
};

// 静态文件服务配置
struct StaticFileConfig {
    std::string root_dir;          // 根目录
    std::string index_file = "index.html";  // 默认文件
    bool enable_directory_listing = false;   // 是否允许目录列表
    int cache_max_age = 3600;                // 缓存时间（秒）
    std::map<std::string, std::string> mime_types;  // MIME 类型映射
};

// 服务器配置
struct ServerConfig {
    std::string host = "0.0.0.0";
    uint16_t port = 8080;
    int backlog = 128;
    int max_connections = 1000;
    int num_threads = 4;
    bool enable_tls = false;
    std::string cert_file;
    std::string key_file;
    ConnectionSettings connection_settings;
};

// HTTP/2 服务器类
class Http2Server {
public:
    Http2Server(const ServerConfig& config = ServerConfig());
    ~Http2Server();

    // 启动服务器
    bool start();

    // 停止服务器
    void stop();

    // 获取路由器
    Router& get_router() { return router_; }

    // 配置静态文件服务
    void serve_static(const std::string& mount_point, const StaticFileConfig& config);

    // 设置请求处理器
    void set_request_handler(RequestHandler handler) { request_handler_ = handler; }

    // 获取服务器状态
    bool is_running() const { return is_running_; }
    size_t get_connection_count() const;

private:
    ServerConfig config_;
    Router router_;
    StaticFileConfig static_config_;
    RequestHandler request_handler_;

    int listen_fd_ = -1;
    std::atomic<bool> is_running_{false};
    std::vector<std::thread> worker_threads_;
    std::vector<std::shared_ptr<Connection>> connections_;
    mutable std::mutex connections_mutex_;

    // 接受连接
    void accept_connections();

    // 处理连接
    void handle_connection(int client_fd);

    // 处理静态文件请求
    bool handle_static_file(std::shared_ptr<HttpRequest> request,
                           std::shared_ptr<HttpResponse> response);

    // 获取 MIME 类型
    std::string get_mime_type(const std::string& file_path) const;

    // 目录列表
    std::string generate_directory_listing(const std::string& dir_path, const std::string& url_path) const;

    // 初始化默认 MIME 类型
    void init_mime_types();

    // 默认请求处理器
    void default_request_handler(std::shared_ptr<HttpRequest> request,
                                std::shared_ptr<HttpResponse> response);

    // CORS 中间件
    bool cors_middleware(std::shared_ptr<HttpRequest> request,
                       std::shared_ptr<HttpResponse> response,
                       std::function<void()> next);

    std::map<std::string, std::string> mime_types_;
};

} // namespace http2
