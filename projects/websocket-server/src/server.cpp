/**
 * @file server.cpp
 * @brief WebSocket 服务器实现
 *
 * 基于 epoll 的高性能 WebSocket 服务器实现。
 * 支持多客户端并发连接、消息路由、房间系统等功能。
 */

#include "websocket/server.h"
#include <sys/socket.h>
#include <sys/epoll.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>
#include <iostream>
#include <algorithm>

namespace ws {

// ============================================================================
// 构造和析构
// ============================================================================

Server::Server(const ServerConfig& config) : config_(config) {
    // 设置默认消息解析器
    router_.set_message_parser([](const Message& msg) -> std::pair<std::string, std::string> {
        if (msg.type == Opcode::Text) {
            std::string text = msg.text();
            auto action = SimpleJson::get(text, "action");
            auto path = SimpleJson::get(text, "path");
            return {
                path.value_or("default"),
                action.value_or("message")
            };
        }
        return {"default", "binary"};
    });
}

Server::~Server() {
    stop();
}

// ============================================================================
// 生命周期
// ============================================================================

bool Server::start() {
    if (running_.load()) {
        return false;
    }

    // 创建 epoll 实例
    epoll_fd_ = ::epoll_create1(0);
    if (epoll_fd_ < 0) {
        std::cerr << "Failed to create epoll instance" << std::endl;
        return false;
    }

    // 创建监听套接字
    if (!create_listener()) {
        ::close(epoll_fd_);
        epoll_fd_ = -1;
        return false;
    }

    // 添加监听套接字到 epoll
    epoll_add(listen_fd_, EPOLLIN);

    running_.store(true);
    std::cout << "WebSocket server started on " << config_.host << ":" << config_.port << std::endl;

    return true;
}

void Server::stop() {
    if (!running_.load()) {
        return;
    }

    running_.store(false);

    // 关闭所有连接
    close_all(CloseCode::GoingAway, "Server shutting down");

    // 关闭监听套接字
    if (listen_fd_ >= 0) {
        ::close(listen_fd_);
        listen_fd_ = -1;
    }

    // 关闭 epoll
    if (epoll_fd_ >= 0) {
        ::close(epoll_fd_);
        epoll_fd_ = -1;
    }

    std::cout << "WebSocket server stopped" << std::endl;
}

void Server::run() {
    while (running_.load()) {
        poll(100);
    }
}

void Server::poll(int timeout_ms) {
    if (!running_.load()) {
        return;
    }

    int nfds = ::epoll_wait(epoll_fd_, events_, MAX_EVENTS, timeout_ms);
    if (nfds < 0) {
        if (errno == EINTR) {
            return;
        }
        std::cerr << "epoll_wait error: " << strerror(errno) << std::endl;
        return;
    }

    for (int i = 0; i < nfds; ++i) {
        int fd = events_[i].data.fd;
        uint32_t ev = events_[i].events;

        if (fd == listen_fd_) {
            // 新连接
            accept_connection();
        } else {
            // 已有连接的事件
            std::lock_guard<std::mutex> lock(connections_mutex_);
            auto it = fd_to_conn_id_.find(fd);
            if (it == fd_to_conn_id_.end()) {
                continue;
            }

            auto conn_it = connections_.find(it->second);
            if (conn_it == connections_.end()) {
                continue;
            }

            auto conn = conn_it->second;

            if (ev & (EPOLLERR | EPOLLHUP)) {
                remove_connection(conn);
                continue;
            }

            if (ev & EPOLLIN) {
                handle_connection_read(conn);
            }

            if (ev & EPOLLOUT) {
                handle_connection_write(conn);
            }
        }
    }

    // 心跳检测
    check_heartbeat();
}

// ============================================================================
// 网络
// ============================================================================

bool Server::create_listener() {
    // 创建套接字
    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        std::cerr << "Failed to create socket: " << strerror(errno) << std::endl;
        return false;
    }

    // 设置非阻塞
    int flags = fcntl(listen_fd_, F_GETFL, 0);
    if (flags < 0 || fcntl(listen_fd_, F_SETFL, flags | O_NONBLOCK) < 0) {
        std::cerr << "Failed to set non-blocking: " << strerror(errno) << std::endl;
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    // 设置 SO_REUSEADDR
    int opt = 1;
    if (setsockopt(listen_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        std::cerr << "Failed to set SO_REUSEADDR: " << strerror(errno) << std::endl;
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    // 绑定地址
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(config_.port);

    if (config_.host == "0.0.0.0") {
        addr.sin_addr.s_addr = INADDR_ANY;
    } else {
        if (inet_pton(AF_INET, config_.host.c_str(), &addr.sin_addr) <= 0) {
            std::cerr << "Invalid address: " << config_.host << std::endl;
            ::close(listen_fd_);
            listen_fd_ = -1;
            return false;
        }
    }

    if (bind(listen_fd_, reinterpret_cast<struct sockaddr*>(&addr), sizeof(addr)) < 0) {
        std::cerr << "Failed to bind: " << strerror(errno) << std::endl;
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    // 开始监听
    if (listen(listen_fd_, SOMAXCONN) < 0) {
        std::cerr << "Failed to listen: " << strerror(errno) << std::endl;
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    return true;
}

void Server::accept_connection() {
    while (true) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept4(listen_fd_, reinterpret_cast<struct sockaddr*>(&client_addr),
                                &addr_len, SOCK_NONBLOCK);
        if (client_fd < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                break;  // 没有更多连接
            }
            std::cerr << "accept error: " << strerror(errno) << std::endl;
            break;
        }

        // 检查连接数限制
        {
            std::lock_guard<std::mutex> lock(connections_mutex_);
            if (connections_.size() >= config_.max_connections) {
                ::close(client_fd);
                std::cerr << "Max connections reached, rejecting new connection" << std::endl;
                continue;
            }
        }

        // 设置 TCP_NODELAY
        int opt = 1;
        setsockopt(client_fd, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt));

        // 创建连接对象
        auto conn = std::make_shared<Connection>(client_fd, this);

        // 设置回调
        ConnectionCallbacks cbs;
        cbs.on_open = [this](ConnectionPtr c) {
            if (callbacks_.on_open) {
                callbacks_.on_open(c);
            }
        };
        cbs.on_message = [this](ConnectionPtr c, const Message& msg) {
            // 安全检查
            if (!security_.validate_message(c, msg)) {
                return;
            }

            // 路由消息
            router_.route(c, msg);

            // 用户回调
            if (callbacks_.on_message) {
                callbacks_.on_message(c, msg);
            }
        };
        cbs.on_close = [this](ConnectionPtr c, CloseCode code, const std::string& reason) {
            // 从所有房间移除
            room_manager_.leave_all_rooms(c);

            // 用户回调
            if (callbacks_.on_close) {
                callbacks_.on_close(c, code, reason);
            }

            // 移除连接
            remove_connection(c);
        };
        cbs.on_error = [this](ConnectionPtr c, const std::string& error) {
            if (callbacks_.on_error) {
                callbacks_.on_error(c, error);
            }
        };
        conn->set_callbacks(cbs);

        // 添加到连接表
        {
            std::lock_guard<std::mutex> lock(connections_mutex_);
            connections_[conn->id()] = conn;
            fd_to_conn_id_[client_fd] = conn->id();
        }

        // 添加到 epoll
        epoll_add(client_fd, EPOLLIN | EPOLLET);

        std::cout << "New connection: " << conn->id()
                  << " from " << conn->remote_address()
                  << ":" << conn->remote_port() << std::endl;
    }
}

void Server::handle_connection_read(ConnectionPtr conn) {
    conn->handle_read();
}

void Server::handle_connection_write(ConnectionPtr conn) {
    conn->handle_write();

    // 写完后移除 EPOLLOUT
    epoll_mod(conn->fd(), EPOLLIN | EPOLLET);
}

void Server::remove_connection(ConnectionPtr conn) {
    std::lock_guard<std::mutex> lock(connections_mutex_);

    epoll_del(conn->fd());
    fd_to_conn_id_.erase(conn->fd());
    connections_.erase(conn->id());
}

// ============================================================================
// epoll 辅助
// ============================================================================

void Server::epoll_add(int fd, uint32_t events) {
    struct ::epoll_event ev;
    ev.events = events;
    ev.data.fd = fd;
    if (::epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, fd, &ev) < 0) {
        std::cerr << "epoll_ctl ADD failed: " << strerror(errno) << std::endl;
    }
}

void Server::epoll_mod(int fd, uint32_t events) {
    struct ::epoll_event ev;
    ev.events = events;
    ev.data.fd = fd;
    if (::epoll_ctl(epoll_fd_, EPOLL_CTL_MOD, fd, &ev) < 0) {
        std::cerr << "epoll_ctl MOD failed: " << strerror(errno) << std::endl;
    }
}

void Server::epoll_del(int fd) {
    if (::epoll_ctl(epoll_fd_, EPOLL_CTL_DEL, fd, nullptr) < 0) {
        std::cerr << "epoll_ctl DEL failed: " << strerror(errno) << std::endl;
    }
}

// ============================================================================
// 连接管理
// ============================================================================

std::vector<ConnectionPtr> Server::get_connections() const {
    std::lock_guard<std::mutex> lock(connections_mutex_);
    std::vector<ConnectionPtr> result;
    result.reserve(connections_.size());
    for (const auto& [id, conn] : connections_) {
        result.push_back(conn);
    }
    return result;
}

ConnectionPtr Server::get_connection(uint64_t id) const {
    std::lock_guard<std::mutex> lock(connections_mutex_);
    auto it = connections_.find(id);
    if (it != connections_.end()) {
        return it->second;
    }
    return nullptr;
}

size_t Server::connection_count() const {
    std::lock_guard<std::mutex> lock(connections_mutex_);
    return connections_.size();
}

void Server::close_all(CloseCode code, const std::string& reason) {
    std::lock_guard<std::mutex> lock(connections_mutex_);
    for (const auto& [id, conn] : connections_) {
        conn->close(code, reason);
    }
}

// ============================================================================
// 消息广播
// ============================================================================

void Server::broadcast_text(const std::string& text) {
    auto conns = get_connections();
    for (const auto& conn : conns) {
        if (conn->state() == ConnectionState::Open) {
            conn->send_text(text);
        }
    }
}

void Server::broadcast_binary(const std::vector<uint8_t>& data) {
    auto conns = get_connections();
    for (const auto& conn : conns) {
        if (conn->state() == ConnectionState::Open) {
            conn->send_binary(data);
        }
    }
}

void Server::broadcast_text(const std::string& text, ConnectionPtr exclude) {
    auto conns = get_connections();
    for (const auto& conn : conns) {
        if (conn->state() == ConnectionState::Open && conn != exclude) {
            conn->send_text(text);
        }
    }
}

void Server::broadcast_to_room(const std::string& room_name, const std::string& text) {
    room_manager_.broadcast_to_room(room_name, text);
}

// ============================================================================
// 心跳检测
// ============================================================================

void Server::check_heartbeat() {
    int64_t now = utils::timestamp_ms();

    // 检查是否需要发送心跳
    if (now - last_heartbeat_check_ < config_.heartbeat_interval_ms) {
        return;
    }

    last_heartbeat_check_ = now;

    auto conns = get_connections();
    for (const auto& conn : conns) {
        if (conn->state() != ConnectionState::Open) {
            continue;
        }

        // 检查是否超时
        if (now - conn->last_active_time() > config_.heartbeat_timeout_ms) {
            std::cout << "Connection " << conn->id() << " heartbeat timeout" << std::endl;
            conn->close(CloseCode::GoingAway, "Heartbeat timeout");
            continue;
        }

        // 发送 Ping
        conn->send_ping();
    }
}

} // namespace ws
