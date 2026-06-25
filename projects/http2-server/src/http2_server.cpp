/**
 * @file http2_server.cpp
 * @brief HTTP/2 服务器实现
 */

#include "http2_server.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>
#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <filesystem>
#include <ctime>

namespace fs = std::filesystem;

namespace http2 {

// Router 实现

void Router::get(const std::string& path, RequestHandler handler) {
    routes_.push_back({HttpMethod::GET, path, handler});
}

void Router::post(const std::string& path, RequestHandler handler) {
    routes_.push_back({HttpMethod::POST, path, handler});
}

void Router::put(const std::string& path, RequestHandler handler) {
    routes_.push_back({HttpMethod::PUT, path, handler});
}

void Router::del(const std::string& path, RequestHandler handler) {
    routes_.push_back({HttpMethod::DELETE_, path, handler});
}

void Router::head(const std::string& path, RequestHandler handler) {
    routes_.push_back({HttpMethod::HEAD, path, handler});
}

void Router::options(const std::string& path, RequestHandler handler) {
    routes_.push_back({HttpMethod::OPTIONS, path, handler});
}

void Router::all(const std::string& path, RequestHandler handler) {
    routes_.push_back({HttpMethod::GET, path, handler});
    routes_.push_back({HttpMethod::POST, path, handler});
    routes_.push_back({HttpMethod::PUT, path, handler});
    routes_.push_back({HttpMethod::DELETE_, path, handler});
    routes_.push_back({HttpMethod::HEAD, path, handler});
    routes_.push_back({HttpMethod::OPTIONS, path, handler});
}

RequestHandler Router::match(HttpMethod method, const std::string& path) const {
    for (const auto& route : routes_) {
        if (route.method == method && route.path == path) {
            return route.handler;
        }
        // 简单的通配符匹配
        if (route.method == method && route.path.back() == '*') {
            std::string prefix = route.path.substr(0, route.path.size() - 1);
            if (path.substr(0, prefix.size()) == prefix) {
                return route.handler;
            }
        }
    }
    return nullptr;
}

void Router::use(Middleware middleware) {
    middlewares_.push_back(middleware);
}

bool Router::execute_middleware(std::shared_ptr<HttpRequest> request,
                               std::shared_ptr<HttpResponse> response,
                               std::function<void()> final_handler) {
    size_t index = 0;

    std::function<void()> next = [&]() {
        if (index < middlewares_.size()) {
            auto current_middleware = middlewares_[index++];
            if (!current_middleware(request, response, next)) {
                return;
            }
        } else {
            final_handler();
        }
    };

    next();
    return true;
}

// Http2Server 实现

Http2Server::Http2Server(const ServerConfig& config)
    : config_(config) {
    init_mime_types();
}

Http2Server::~Http2Server() {
    stop();
}

bool Http2Server::start() {
    // 创建 socket
    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        std::cerr << "Failed to create socket" << std::endl;
        return false;
    }

    // 设置 socket 选项
    int opt = 1;
    setsockopt(listen_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // 绑定地址
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(config_.port);
    inet_pton(AF_INET, config_.host.c_str(), &addr.sin_addr);

    if (bind(listen_fd_, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        std::cerr << "Failed to bind to " << config_.host << ":" << config_.port << std::endl;
        close(listen_fd_);
        return false;
    }

    // 开始监听
    if (listen(listen_fd_, config_.backlog) < 0) {
        std::cerr << "Failed to listen" << std::endl;
        close(listen_fd_);
        return false;
    }

    is_running_ = true;
    std::cout << "HTTP/2 Server listening on " << config_.host << ":" << config_.port << std::endl;

    // 启动工作线程
    for (int i = 0; i < config_.num_threads; ++i) {
        worker_threads_.emplace_back(&Http2Server::accept_connections, this);
    }

    return true;
}

void Http2Server::stop() {
    is_running_ = false;

    if (listen_fd_ >= 0) {
        close(listen_fd_);
        listen_fd_ = -1;
    }

    for (auto& thread : worker_threads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }

    std::lock_guard<std::mutex> lock(connections_mutex_);
    for (auto& conn : connections_) {
        conn->stop();
    }
    connections_.clear();
}

size_t Http2Server::get_connection_count() const {
    std::lock_guard<std::mutex> lock(connections_mutex_);
    return connections_.size();
}

void Http2Server::accept_connections() {
    while (is_running_) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept(listen_fd_, (struct sockaddr*)&client_addr, &addr_len);
        if (client_fd < 0) {
            if (is_running_) {
                std::cerr << "Failed to accept connection" << std::endl;
            }
            continue;
        }

        // 检查连接数限制
        {
            std::lock_guard<std::mutex> lock(connections_mutex_);
            if (connections_.size() >= static_cast<size_t>(config_.max_connections)) {
                close(client_fd);
                continue;
            }
        }

        // 处理连接
        handle_connection(client_fd);
    }
}

void Http2Server::handle_connection(int client_fd) {
    auto connection = std::make_shared<Connection>(client_fd, true);

    // 设置请求处理器
    connection->set_request_handler([this](std::shared_ptr<HttpRequest> request,
                                          std::shared_ptr<HttpResponse> response) {
        // 执行中间件和路由
        router_.execute_middleware(request, response, [this, request, response]() {
            // 尝试路由匹配
            auto handler = router_.match(request->get_method(), request->get_path());
            if (handler) {
                handler(request, response);
            } else if (request_handler_) {
                request_handler_(request, response);
            } else if (!handle_static_file(request, response)) {
                // 404 Not Found
                response->set_status(HttpStatusCode::NOT_FOUND);
                response->set_content_type("text/html");
                response->set_body("<html><body><h1>404 Not Found</h1></body></html>");
            }
        });
    });

    // 添加到连接列表
    {
        std::lock_guard<std::mutex> lock(connections_mutex_);
        connections_.push_back(connection);
    }

    // 启动连接
    connection->start();
}

bool Http2Server::handle_static_file(std::shared_ptr<HttpRequest> request,
                                     std::shared_ptr<HttpResponse> response) {
    if (static_config_.root_dir.empty()) {
        return false;
    }

    std::string path = request->get_path();
    if (path == "/") {
        path = "/" + static_config_.index_file;
    }

    // 安全检查，防止目录遍历
    if (path.find("..") != std::string::npos) {
        return false;
    }

    fs::path file_path = fs::path(static_config_.root_dir) / path.substr(1);

    if (!fs::exists(file_path)) {
        return false;
    }

    if (fs::is_directory(file_path)) {
        if (static_config_.enable_directory_listing) {
            response->set_status(HttpStatusCode::OK);
            response->set_content_type("text/html");
            response->set_body(generate_directory_listing(file_path.string(), path));
            return true;
        }
        return false;
    }

    // 读取文件
    std::ifstream file(file_path, std::ios::binary);
    if (!file) {
        return false;
    }

    // 获取文件大小
    file.seekg(0, std::ios::end);
    size_t size = file.tellg();
    file.seekg(0, std::ios::beg);

    // 读取内容
    std::vector<uint8_t> content(size);
    file.read(reinterpret_cast<char*>(content.data()), size);

    // 设置响应
    response->set_status(HttpStatusCode::OK);
    response->set_content_type(get_mime_type(file_path.extension().string()));
    response->set_body(content);

    // 缓存控制
    if (static_config_.cache_max_age > 0) {
        response->set_cache_control("max-age=" + std::to_string(static_config_.cache_max_age));
    }

    return true;
}

std::string Http2Server::get_mime_type(const std::string& extension) const {
    auto it = mime_types_.find(extension);
    if (it != mime_types_.end()) {
        return it->second;
    }
    return "application/octet-stream";
}

std::string Http2Server::generate_directory_listing(const std::string& dir_path,
                                                    const std::string& url_path) const {
    std::ostringstream html;
    html << "<html><head><title>Directory listing for " << url_path << "</title></head>";
    html << "<body><h1>Directory listing for " << url_path << "</h1><ul>";

    try {
        for (const auto& entry : fs::directory_iterator(dir_path)) {
            std::string filename = entry.path().filename().string();
            std::string link = url_path;
            if (link.back() != '/') link += '/';
            link += filename;

            if (entry.is_directory()) {
                html << "<li><a href=\"" << link << "/\">" << filename << "/</a></li>";
            } else {
                html << "<li><a href=\"" << link << "\">" << filename << "</a></li>";
            }
        }
    } catch (const std::exception& e) {
        html << "<li>Error: " << e.what() << "</li>";
    }

    html << "</ul></body></html>";
    return html.str();
}

void Http2Server::serve_static(const std::string& mount_point, const StaticFileConfig& config) {
    static_config_ = config;
    // 实际实现中应该处理挂载点
}

void Http2Server::init_mime_types() {
    mime_types_[".html"] = "text/html";
    mime_types_[".htm"] = "text/html";
    mime_types_[".css"] = "text/css";
    mime_types_[".js"] = "application/javascript";
    mime_types_[".json"] = "application/json";
    mime_types_[".xml"] = "application/xml";
    mime_types_[".txt"] = "text/plain";
    mime_types_[".csv"] = "text/csv";
    mime_types_[".png"] = "image/png";
    mime_types_[".jpg"] = "image/jpeg";
    mime_types_[".jpeg"] = "image/jpeg";
    mime_types_[".gif"] = "image/gif";
    mime_types_[".svg"] = "image/svg+xml";
    mime_types_[".ico"] = "image/x-icon";
    mime_types_[".mp3"] = "audio/mpeg";
    mime_types_[".mp4"] = "video/mp4";
    mime_types_[".avi"] = "video/x-msvideo";
    mime_types_[".pdf"] = "application/pdf";
    mime_types_[".zip"] = "application/zip";
    mime_types_[".tar"] = "application/x-tar";
    mime_types_[".gz"] = "application/gzip";
    mime_types_[".woff"] = "font/woff";
    mime_types_[".woff2"] = "font/woff2";
    mime_types_[".ttf"] = "font/ttf";
    mime_types_[".otf"] = "font/otf";

    // 合并用户自定义的 MIME 类型
    for (const auto& pair : static_config_.mime_types) {
        mime_types_[pair.first] = pair.second;
    }
}

void Http2Server::default_request_handler(std::shared_ptr<HttpRequest> request,
                                          std::shared_ptr<HttpResponse> response) {
    response->set_status(HttpStatusCode::OK);
    response->set_content_type("application/json");

    std::ostringstream json;
    json << "{";
    json << "\"method\":\"" << request->get_method_string() << "\",";
    json << "\"path\":\"" << request->get_path() << "\",";
    json << "\"version\":\"HTTP/2\",";
    json << "\"status\":\"ok\"";
    json << "}";

    response->set_body(json.str());
}

bool Http2Server::cors_middleware(std::shared_ptr<HttpRequest> request,
                                  std::shared_ptr<HttpResponse> response,
                                  std::function<void()> next) {
    response->set_cors_headers();

    if (request->get_method() == HttpMethod::OPTIONS) {
        response->set_status(HttpStatusCode::NO_CONTENT);
        return false;  // 不继续执行后续中间件
    }

    next();
    return true;
}

} // namespace http2
