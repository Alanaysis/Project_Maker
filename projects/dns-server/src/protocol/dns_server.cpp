/**
 * @file dns_server.cpp
 * @brief DNS 服务器核心实现
 *
 * 实现 DNS 服务器的网络层，包括：
 * - UDP/TCP 监听
 * - 请求分发
 * - 并发处理
 * - 异步 I/O
 */

#include "protocol/dns_server.h"
#include "monitoring/dns_monitor.h"

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <cstring>
#include <iostream>
#include <algorithm>

namespace dns {

// ============================================================================
// UdpServer 实现
// ============================================================================

UdpServer::UdpServer(const DnsServerConfig& config) : config_(config) {}

UdpServer::~UdpServer() {
    stop();
}

bool UdpServer::start(DnsRequestHandler handler) {
    handler_ = handler;

    // 创建 UDP 套接字
    socket_fd_ = socket(AF_INET, SOCK_DGRAM, 0);
    if (socket_fd_ < 0) {
        DNS_LOG_ERROR("UdpServer", "Failed to create UDP socket: " +
                      std::string(strerror(errno)));
        return false;
    }

    // 设置地址重用
    int opt = 1;
    setsockopt(socket_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // 绑定地址
    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(config_.port);
    inet_pton(AF_INET, config_.bind_address.c_str(), &addr.sin_addr);

    if (bind(socket_fd_, reinterpret_cast<struct sockaddr*>(&addr),
             sizeof(addr)) < 0) {
        DNS_LOG_ERROR("UdpServer", "Failed to bind UDP socket: " +
                      std::string(strerror(errno)));
        close(socket_fd_);
        socket_fd_ = -1;
        return false;
    }

    // 设置非阻塞
    int flags = fcntl(socket_fd_, F_GETFL, 0);
    fcntl(socket_fd_, F_SETFL, flags | O_NONBLOCK);

    running_ = true;

    // 启动工作线程
    for (size_t i = 0; i < config_.thread_pool_size; i++) {
        workers_.emplace_back(&UdpServer::worker_thread, this);
    }

    // 启动接收线程
    receive_thread_ = std::thread(&UdpServer::receive_loop, this);

    DNS_LOG_INFO("UdpServer", "UDP server started on " +
                 config_.bind_address + ":" + std::to_string(config_.port));
    return true;
}

void UdpServer::stop() {
    running_ = false;
    stop_workers_ = true;

    if (receive_thread_.joinable()) {
        receive_thread_.join();
    }

    queue_cv_.notify_all();
    for (auto& worker : workers_) {
        if (worker.joinable()) {
            worker.join();
        }
    }

    if (socket_fd_ >= 0) {
        close(socket_fd_);
        socket_fd_ = -1;
    }

    DNS_LOG_INFO("UdpServer", "UDP server stopped");
}

void UdpServer::receive_loop() {
    constexpr size_t BUF_SIZE = 4096;
    uint8_t buffer[BUF_SIZE];

    while (running_) {
        struct pollfd pfd{};
        pfd.fd = socket_fd_;
        pfd.events = POLLIN;

        int ret = poll(&pfd, 1, 100);  // 100ms 超时
        if (ret <= 0) continue;

        struct sockaddr_in client_addr{};
        socklen_t addr_len = sizeof(client_addr);

        ssize_t n = recvfrom(socket_fd_, buffer, BUF_SIZE, 0,
                             reinterpret_cast<struct sockaddr*>(&client_addr),
                             &addr_len);
        if (n <= 0) continue;

        // 获取客户端信息
        char ip_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, ip_str, sizeof(ip_str));
        uint16_t port = ntohs(client_addr.sin_port);

        // 复制数据并提交任务
        std::vector<uint8_t> data(buffer, buffer + n);
        std::string client_ip(ip_str);

        submit_task([this, data, client_ip, port]() {
            process_request(data, client_ip, port);
        });
    }
}

void UdpServer::process_request(const std::vector<uint8_t>& data,
                                 const std::string& client_addr,
                                 uint16_t client_port) {
    auto start = std::chrono::steady_clock::now();

    // 解析请求
    auto request = DnsMessage::deserialize(data);
    if (!request) {
        DNS_LOG_WARN("UdpServer", "Failed to parse DNS request from " +
                     client_addr);
        return;
    }

    // 调用处理器
    DnsMessage response;
    try {
        response = handler_(*request, client_addr, client_port);
    } catch (const std::exception& e) {
        DNS_LOG_ERROR("UdpServer", "Error handling request: " +
                      std::string(e.what()));
        response = DnsMessage::create_response(*request,
                                                ResponseCode::SERVER_FAILURE);
    }

    // 序列化响应
    auto response_data = response.serialize();

    // 如果超过 UDP 最大长度，设置截断标志
    if (response_data.size() > DNS_MAX_UDP_SIZE) {
        response.header().tc = true;
        response_data = response.serialize();
        response_data.resize(DNS_MAX_UDP_SIZE);
    }

    // 发送响应
    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(client_port);
    inet_pton(AF_INET, client_addr.c_str(), &addr.sin_addr);

    sendto(socket_fd_, response_data.data(), response_data.size(), 0,
           reinterpret_cast<struct sockaddr*>(&addr), sizeof(addr));

    // 记录统计
    auto end = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
        end - start);
    double response_time_ms = duration.count() / 1000.0;

    DNS_LOG_DEBUG("UdpServer", "Query from " + client_addr + ": " +
                  request->questions()[0].name.to_string() + " -> " +
                  std::to_string(response.header().ancount) + " answers");
}

void UdpServer::worker_thread() {
    while (!stop_workers_) {
        std::function<void()> task;
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            queue_cv_.wait(lock, [this]() {
                return !task_queue_.empty() || stop_workers_;
            });

            if (stop_workers_ && task_queue_.empty()) {
                return;
            }

            task = std::move(task_queue_.front());
            task_queue_.pop();
        }
        task();
    }
}

void UdpServer::submit_task(std::function<void()> task) {
    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        task_queue_.push(std::move(task));
    }
    queue_cv_.notify_one();
}

// ============================================================================
// TcpServer 实现
// ============================================================================

TcpServer::TcpServer(const DnsServerConfig& config) : config_(config) {}

TcpServer::~TcpServer() {
    stop();
}

bool TcpServer::start(DnsRequestHandler handler) {
    handler_ = handler;

    // 创建 TCP 套接字
    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        DNS_LOG_ERROR("TcpServer", "Failed to create TCP socket: " +
                      std::string(strerror(errno)));
        return false;
    }

    // 设置地址重用
    int opt = 1;
    setsockopt(listen_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // 绑定地址
    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(config_.port);
    inet_pton(AF_INET, config_.bind_address.c_str(), &addr.sin_addr);

    if (bind(listen_fd_, reinterpret_cast<struct sockaddr*>(&addr),
             sizeof(addr)) < 0) {
        DNS_LOG_ERROR("TcpServer", "Failed to bind TCP socket: " +
                      std::string(strerror(errno)));
        close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    // 开始监听
    if (listen(listen_fd_, 128) < 0) {
        DNS_LOG_ERROR("TcpServer", "Failed to listen on TCP socket: " +
                      std::string(strerror(errno)));
        close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    running_ = true;
    accept_thread_ = std::thread(&TcpServer::accept_loop, this);

    DNS_LOG_INFO("TcpServer", "TCP server started on " +
                 config_.bind_address + ":" + std::to_string(config_.port));
    return true;
}

void TcpServer::stop() {
    running_ = false;

    if (accept_thread_.joinable()) {
        accept_thread_.join();
    }

    // 关闭所有连接
    {
        std::lock_guard<std::mutex> lock(connections_mutex_);
        for (auto& [fd, thread] : connections_) {
            close(fd);
            if (thread.joinable()) {
                thread.join();
            }
        }
        connections_.clear();
    }

    if (listen_fd_ >= 0) {
        close(listen_fd_);
        listen_fd_ = -1;
    }

    DNS_LOG_INFO("TcpServer", "TCP server stopped");
}

void TcpServer::accept_loop() {
    while (running_) {
        struct pollfd pfd{};
        pfd.fd = listen_fd_;
        pfd.events = POLLIN;

        int ret = poll(&pfd, 1, 100);
        if (ret <= 0) continue;

        struct sockaddr_in client_addr{};
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept(listen_fd_,
                               reinterpret_cast<struct sockaddr*>(&client_addr),
                               &addr_len);
        if (client_fd < 0) continue;

        // 检查连接数限制
        if (active_connections_ >= config_.max_connections) {
            close(client_fd);
            DNS_LOG_WARN("TcpServer", "Max connections reached, rejecting");
            continue;
        }

        char ip_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, ip_str, sizeof(ip_str));
        std::string client_ip(ip_str);

        // 在新线程中处理连接
        std::lock_guard<std::mutex> lock(connections_mutex_);
        connections_[client_fd] = std::thread(
            &TcpServer::handle_connection, this, client_fd, client_ip);
        active_connections_++;
    }
}

void TcpServer::handle_connection(int client_fd, const std::string& client_addr) {
    constexpr size_t BUF_SIZE = 4096;
    uint8_t buffer[BUF_SIZE];

    // 设置超时
    struct timeval tv{};
    tv.tv_sec = config_.tcp_timeout.count();
    tv.tv_usec = 0;
    setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

    while (running_) {
        // 读取长度前缀 (2 字节)
        uint16_t length;
        ssize_t n = recv(client_fd, &length, 2, MSG_WAITALL);
        if (n <= 0) break;

        length = ntohs(length);
        if (length > config_.max_message_size) {
            DNS_LOG_WARN("TcpServer", "Message too large from " + client_addr);
            break;
        }

        // 读取报文
        n = recv(client_fd, buffer, length, MSG_WAITALL);
        if (n <= 0) break;

        // 解析请求
        auto request = DnsMessage::deserialize(
            std::span<const uint8_t>(buffer, n));
        if (!request) {
            DNS_LOG_WARN("TcpServer", "Failed to parse request from " +
                         client_addr);
            break;
        }

        // 处理请求
        DnsMessage response;
        try {
            response = handler_(*request, client_addr, 0);
        } catch (const std::exception& e) {
            DNS_LOG_ERROR("TcpServer", "Error handling request: " +
                          std::string(e.what()));
            response = DnsMessage::create_response(*request,
                                                    ResponseCode::SERVER_FAILURE);
        }

        // 发送响应
        auto response_data = response.serialize();
        uint16_t resp_length = htons(static_cast<uint16_t>(response_data.size()));

        send(client_fd, &resp_length, 2, 0);
        send(client_fd, response_data.data(), response_data.size(), 0);
    }

    close(client_fd);
    active_connections_--;

    std::lock_guard<std::mutex> lock(connections_mutex_);
    connections_.erase(client_fd);
}

// ============================================================================
// DnsServer 实现
// ============================================================================

DnsServer::DnsServer(const DnsServerConfig& config) : config_(config) {}

DnsServer::~DnsServer() {
    stop();
}

void DnsServer::set_handler(DnsRequestHandler handler) {
    handler_ = std::move(handler);
}

bool DnsServer::start() {
    if (!handler_) {
        DNS_LOG_ERROR("DnsServer", "No request handler set");
        return false;
    }

    // 包装处理器以收集统计
    auto wrapped_handler = [this](const DnsMessage& request,
                                   const std::string& client_addr,
                                   uint16_t client_port) -> DnsMessage {
        auto start = std::chrono::steady_clock::now();
        bool is_tcp = (client_port == 0);

        DnsMessage response;
        try {
            response = handler_(request, client_addr, client_port);
        } catch (...) {
            response = DnsMessage::create_response(request,
                                                    ResponseCode::SERVER_FAILURE);
        }

        auto end = std::chrono::steady_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
            end - start);
        double response_time_ms = duration.count() / 1000.0;

        bool success = (response.header().rcode == ResponseCode::NO_ERROR);
        update_stats(success, response_time_ms, is_tcp);

        return response;
    };

    // 启动 UDP 服务器
    if (config_.enable_udp) {
        udp_server_ = std::make_unique<UdpServer>(config_);
        if (!udp_server_->start(wrapped_handler)) {
            DNS_LOG_ERROR("DnsServer", "Failed to start UDP server");
            return false;
        }
    }

    // 启动 TCP 服务器
    if (config_.enable_tcp) {
        tcp_server_ = std::make_unique<TcpServer>(config_);
        if (!tcp_server_->start(wrapped_handler)) {
            DNS_LOG_ERROR("DnsServer", "Failed to start TCP server");
            stop();
            return false;
        }
    }

    DNS_LOG_INFO("DnsServer", "DNS server started");
    return true;
}

void DnsServer::stop() {
    if (udp_server_) {
        udp_server_->stop();
    }
    if (tcp_server_) {
        tcp_server_->stop();
    }
    DNS_LOG_INFO("DnsServer", "DNS server stopped");
}

bool DnsServer::is_running() const {
    return (udp_server_ && udp_server_->is_running()) ||
           (tcp_server_ && tcp_server_->is_running());
}

DnsServer::Stats DnsServer::get_stats() const {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    return stats_;
}

void DnsServer::update_stats(bool success, double response_time_ms,
                               bool is_tcp) {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    stats_.queries_received++;
    if (success) {
        stats_.queries_processed++;
    } else {
        stats_.queries_failed++;
    }
    if (is_tcp) {
        stats_.tcp_queries++;
    } else {
        stats_.udp_queries++;
    }

    // 更新平均响应时间
    double total = stats_.avg_response_time_ms * (stats_.queries_received - 1);
    stats_.avg_response_time_ms = (total + response_time_ms) /
                                   stats_.queries_received;
}

} // namespace dns
