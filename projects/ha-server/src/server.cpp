/**
 * @file server.cpp
 * @brief 服务器核心实现
 *
 * 实现高可用服务器的核心逻辑：
 * - 事件循环（epoll）
 * - 请求接收和转发
 * - 负载均衡
 * - 故障转移
 *
 * ⭐ 重点：理解事件驱动架构
 * 💡 思考：为什么选择 epoll 而不是 select 或 poll？
 */

#include "../include/server.h"
#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <signal.h>

namespace ha_server {

Server::Server(const ServerConfig& config)
    : config_(config)
    , listen_fd_(-1)
    , epoll_fd_(-1) {
    // 创建负载均衡器
    balancer_ = LoadBalancerFactory::create(config_.balancer_type);
}

Server::~Server() {
    stop();
}

/**
 * 启动服务器
 *
 * 初始化步骤：
 * 1. 初始化监听 socket
 * 2. 初始化 epoll
 * 3. 启动事件循环线程
 * 4. 启动健康检查
 *
 * ⭐ 重点：
 * - 忽略 SIGPIPE 信号，避免写入已关闭连接时崩溃
 * - 设置 socket 选项，允许地址重用
 */
bool Server::start() {
    if (running_.load()) {
        log_message(LogLevel::WARNING, "Server is already running");
        return false;
    }

    // 忽略 SIGPIPE 信号
    signal(SIGPIPE, SIG_IGN);

    // 初始化监听 socket
    if (!init_listen_socket()) {
        log_message(LogLevel::ERROR, "Failed to initialize listen socket");
        return false;
    }

    // 初始化 epoll
    if (!init_epoll()) {
        log_message(LogLevel::ERROR, "Failed to initialize epoll");
        close(listen_fd_);
        return false;
    }

    running_.store(true);

    // 启动事件循环线程
    event_thread_ = std::thread(&Server::event_loop, this);

    // 启动健康检查
    auto healthy_backends = backend_manager_.get_healthy_backends();
    if (!healthy_backends.empty()) {
        health_checker_ = std::make_unique<HealthChecker>(
            healthy_backends, config_.health_check);
        health_checker_->start();
    }

    log_message(LogLevel::INFO, "Server started on " + config_.host +
                ":" + std::to_string(config_.port));
    log_message(LogLevel::INFO, "Balancer: " + balancer_->name());
    log_message(LogLevel::INFO, "Worker threads: " +
                std::to_string(config_.worker_threads));

    return true;
}

/**
 * 停止服务器
 *
 * 停止所有组件并清理资源。
 */
void Server::stop() {
    if (!running_.load()) {
        return;
    }

    running_.store(false);

    // 停止健康检查
    if (health_checker_) {
        health_checker_->stop();
    }

    // 等待事件循环线程结束
    if (event_thread_.joinable()) {
        event_thread_.join();
    }

    // 关闭连接
    if (epoll_fd_ >= 0) {
        close(epoll_fd_);
        epoll_fd_ = -1;
    }

    if (listen_fd_ >= 0) {
        close(listen_fd_);
        listen_fd_ = -1;
    }

    // 清理连接池
    pool_manager_.clear_all();

    log_message(LogLevel::INFO, "Server stopped");
}

void Server::add_backend(const std::string& host, int port, int weight) {
    backend_manager_.add_backend(host, port, weight);

    // 初始化时所有后端标记为健康
    auto* backend = backend_manager_.get_backend(host + ":" + std::to_string(port));
    if (backend) {
        backend->mark_healthy();
    }
}

void Server::set_balancer(BalancerType type) {
    balancer_ = LoadBalancerFactory::create(type);
}

/**
 * 初始化监听 socket
 *
 * 创建 socket，绑定地址，开始监听。
 *
 * ⭐ 重点：
 * - SO_REUSEADDR 允许地址重用
 * - 设置非阻塞模式
 */
bool Server::init_listen_socket() {
    // 创建 socket
    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        log_message(LogLevel::ERROR, "Failed to create socket: " +
                    std::string(strerror(errno)));
        return false;
    }

    // 设置地址重用
    if (set_reuse_addr(listen_fd_) < 0) {
        log_message(LogLevel::WARNING, "Failed to set SO_REUSEADDR");
    }

    // 设置非阻塞
    if (set_nonblocking(listen_fd_) < 0) {
        log_message(LogLevel::ERROR, "Failed to set non-blocking");
        close(listen_fd_);
        return false;
    }

    // 绑定地址
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(config_.port);
    inet_pton(AF_INET, config_.host.c_str(), &addr.sin_addr);

    if (bind(listen_fd_, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        log_message(LogLevel::ERROR, "Failed to bind: " +
                    std::string(strerror(errno)));
        close(listen_fd_);
        return false;
    }

    // 开始监听
    if (listen(listen_fd_, SOMAXCONN) < 0) {
        log_message(LogLevel::ERROR, "Failed to listen: " +
                    std::string(strerror(errno)));
        close(listen_fd_);
        return false;
    }

    return true;
}

bool Server::init_epoll() {
    epoll_fd_ = epoll_create1(0);
    if (epoll_fd_ < 0) {
        log_message(LogLevel::ERROR, "Failed to create epoll: " +
                    std::string(strerror(errno)));
        return false;
    }

    // 将监听 socket 加入 epoll
    return epoll_add(listen_fd_, EPOLLIN);
}

/**
 * 事件循环
 *
 * 主线程运行的核心循环，处理所有 I/O 事件。
 *
 * ⭐ 重点：
 * - epoll_wait 等待事件
 * - 区分新连接和数据事件
 * - 使用非阻塞 I/O
 *
 * 💡 思考：
 * - epoll 的 ET 和 LT 模式有什么区别？
 * - 如何处理大量并发连接？
 */
void Server::event_loop() {
    while (running_.load()) {
        int nfds = epoll_wait(epoll_fd_, events_, MAX_EVENTS, 100);

        if (nfds < 0) {
            if (errno == EINTR) {
                continue;  // 被信号中断，继续
            }
            log_message(LogLevel::ERROR, "epoll_wait failed: " +
                        std::string(strerror(errno)));
            break;
        }

        for (int i = 0; i < nfds; i++) {
            if (events_[i].data.fd == listen_fd_) {
                // 新连接事件
                accept_connection();
            } else {
                // 数据事件
                handle_connection(events_[i].data.fd, events_[i].events);
            }
        }
    }
}

/**
 * 接受新连接
 *
 * 从监听 socket 接受新连接，设置非阻塞模式，加入 epoll。
 *
 * ⭐ 重点：
 * - accept4 直接设置非阻塞和 CLOEXEC
 * - 添加到 epoll 监听读事件
 */
void Server::accept_connection() {
    struct sockaddr_in client_addr;
    socklen_t addr_len = sizeof(client_addr);

    while (true) {
        int client_fd = accept4(listen_fd_, (struct sockaddr*)&client_addr,
                               &addr_len, SOCK_NONBLOCK | SOCK_CLOEXEC);
        if (client_fd < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                break;  // 没有更多连接
            }
            log_message(LogLevel::ERROR, "accept failed: " +
                        std::string(strerror(errno)));
            break;
        }

        // 添加到 epoll
        if (!epoll_add(client_fd, EPOLLIN)) {
            close(client_fd);
            continue;
        }

        stats_.total_connections.fetch_add(1);
        stats_.active_connections.fetch_add(1);
    }
}

/**
 * 处理连接事件
 *
 * 根据事件类型处理连接：
 * - EPOLLIN: 有数据可读
 * - EPOLLOUT: 可以写入
 * - EPOLLERR/EPOLLHUP: 连接错误
 */
void Server::handle_connection(int fd, uint32_t events) {
    if (events & (EPOLLERR | EPOLLHUP)) {
        close_connection(fd);
        return;
    }

    if (events & EPOLLIN) {
        handle_request(fd);
    }
}

/**
 * 处理客户端请求
 *
 * 读取并解析 HTTP 请求，然后转发到后端。
 *
 * ⭐ 重点：
 * - 非阻塞读取
 * - HTTP 解析
 * - 错误处理
 */
void Server::handle_request(int client_fd) {
    char buffer[4096];
    ssize_t n = read(client_fd, buffer, sizeof(buffer));

    if (n < 0) {
        if (errno == EAGAIN || errno == EWOULDBLOCK) {
            return;  // 没有数据
        }
        close_connection(client_fd);
        return;
    }

    if (n == 0) {
        // 连接关闭
        close_connection(client_fd);
        return;
    }

    stats_.total_requests.fetch_add(1);

    // 解析 HTTP 请求
    HttpRequest request;
    if (!HttpParser::parse_request(buffer, n, request)) {
        send_error_response(client_fd, 400, "Bad Request");
        return;
    }

    // 转发请求
    forward_request(client_fd, request);
}

/**
 * 转发请求到后端
 *
 * 核心转发逻辑：
 * 1. 选择健康的后端
 * 2. 获取连接
 * 3. 转发请求
 * 4. 读取响应
 * 5. 返回给客户端
 *
 * ⭐ 重点：
 * - 负载均衡选择后端
 * - 故障转移：后端不可用时选择其他后端
 * - 连接池复用
 *
 * 💡 思考：
 * - 如何处理超时？
 * - 如何实现重试机制？
 */
void Server::forward_request(int client_fd, const HttpRequest& request) {
    // 获取健康的后端列表
    auto healthy_backends = backend_manager_.get_healthy_backends();

    if (healthy_backends.empty()) {
        send_error_response(client_fd, 503, "No healthy backends available");
        stats_.failed_requests.fetch_add(1);
        return;
    }

    // 使用负载均衡选择后端
    Backend* backend = balancer_->select_backend(healthy_backends);
    if (!backend) {
        send_error_response(client_fd, 503, "Failed to select backend");
        stats_.failed_requests.fetch_add(1);
        return;
    }

    // 获取连接池
    ConnectionPool* pool = pool_manager_.get_pool(
        backend->host, backend->port, config_.pool_config);

    // 获取连接
    bool direct_connection = false;
    int backend_fd = pool->acquire();
    if (backend_fd < 0) {
        // 连接池满或创建失败，尝试直接创建连接
        backend_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (backend_fd < 0) {
            send_error_response(client_fd, 502, "Failed to connect to backend");
            stats_.failed_requests.fetch_add(1);
            return;
        }

        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(backend->port);
        inet_pton(AF_INET, backend->host.c_str(), &addr.sin_addr);

        if (connect(backend_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            close(backend_fd);
            backend->increment_failures();
            send_error_response(client_fd, 502, "Failed to connect to backend");
            stats_.failed_requests.fetch_add(1);
            return;
        }

        direct_connection = true;
    }

    backend->increment_connections();

    // 转发请求
    std::string request_str = request.to_string();
    ssize_t sent = write(backend_fd, request_str.c_str(), request_str.size());

    if (sent < 0) {
        backend->increment_failures();
        backend->decrement_connections();
        if (direct_connection) {
            close(backend_fd);
        } else {
            pool->remove(backend_fd);
        }
        send_error_response(client_fd, 502, "Failed to forward request");
        stats_.failed_requests.fetch_add(1);
        return;
    }

    // 读取响应
    char response_buffer[8192];
    ssize_t received = read(backend_fd, response_buffer, sizeof(response_buffer));

    if (received <= 0) {
        backend->increment_failures();
        backend->decrement_connections();
        if (direct_connection) {
            close(backend_fd);
        } else {
            pool->remove(backend_fd);
        }
        send_error_response(client_fd, 502, "Failed to read response from backend");
        stats_.failed_requests.fetch_add(1);
        return;
    }

    // 发送响应给客户端
    ssize_t written = write(client_fd, response_buffer, received);

    backend->decrement_connections();
    stats_.successful_requests.fetch_add(1);

    // 释放连接回池
    if (direct_connection) {
        close(backend_fd);
    } else if (request.keep_alive) {
        pool->release(backend_fd);
    } else {
        pool->remove(backend_fd);
    }

    if (!request.keep_alive) {
        close_connection(client_fd);
    }
}

void Server::send_error_response(int client_fd, int status_code,
                                  const std::string& message) {
    HttpResponse response = HttpResponse::error_response(status_code, message);
    std::string response_str = response.to_string();
    write(client_fd, response_str.c_str(), response_str.size());
    close_connection(client_fd);
}

bool Server::epoll_add(int fd, uint32_t events) {
    struct epoll_event ev;
    ev.events = events;
    ev.data.fd = fd;

    if (epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, fd, &ev) < 0) {
        log_message(LogLevel::ERROR, "epoll_ctl ADD failed: " +
                    std::string(strerror(errno)));
        return false;
    }
    return true;
}

bool Server::epoll_mod(int fd, uint32_t events) {
    struct epoll_event ev;
    ev.events = events;
    ev.data.fd = fd;

    if (epoll_ctl(epoll_fd_, EPOLL_CTL_MOD, fd, &ev) < 0) {
        log_message(LogLevel::ERROR, "epoll_ctl MOD failed: " +
                    std::string(strerror(errno)));
        return false;
    }
    return true;
}

bool Server::epoll_del(int fd) {
    if (epoll_ctl(epoll_fd_, EPOLL_CTL_DEL, fd, nullptr) < 0) {
        log_message(LogLevel::ERROR, "epoll_ctl DEL failed: " +
                    std::string(strerror(errno)));
        return false;
    }
    return true;
}

void Server::close_connection(int fd) {
    epoll_del(fd);
    close(fd);
    stats_.active_connections.fetch_sub(1);
}

} // namespace ha_server
