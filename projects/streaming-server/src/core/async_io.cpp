/**
 * @file async_io.cpp
 * @brief 异步 I/O 实现
 */

#include "streaming/core/async_io.hpp"
#include "streaming/monitor/logger.hpp"

#include <sys/epoll.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>
#include <algorithm>

namespace streaming {

// ============================================================================
// EventLoop 实现
// ============================================================================

EventLoop::EventLoop() = default;

EventLoop::~EventLoop() {
    shutdown();
}

bool EventLoop::initialize() {
    epoll_fd_ = epoll_create1(0);
    if (epoll_fd_ < 0) {
        LOG_ERROR("Failed to create epoll fd");
        return false;
    }

    LOG_DEBUG("EventLoop initialized");
    return true;
}

void EventLoop::shutdown() {
    stop();

    if (epoll_fd_ >= 0) {
        ::close(epoll_fd_);
        epoll_fd_ = -1;
    }

    std::lock_guard<std::mutex> lock(fd_mutex_);
    fd_contexts_.clear();

    LOG_DEBUG("EventLoop shutdown");
}

bool EventLoop::add_fd(int fd, IoEventType type, IoCallback callback) {
    if (epoll_fd_ < 0) return false;

    std::lock_guard<std::mutex> lock(fd_mutex_);

    auto& ctx = fd_contexts_[fd];
    switch (type) {
        case IoEventType::Read:
            ctx.read_callback = std::move(callback);
            break;
        case IoEventType::Write:
            ctx.write_callback = std::move(callback);
            break;
        case IoEventType::Error:
            ctx.error_callback = std::move(callback);
            break;
        case IoEventType::Close:
            ctx.close_callback = std::move(callback);
            break;
    }

    // 计算事件掩码
    uint32_t events = EPOLLIN;
    if (ctx.write_callback) events |= EPOLLOUT;

    struct epoll_event ev;
    ev.events = events | EPOLLET;
    ev.data.fd = fd;

    if (epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, fd, &ev) < 0) {
        // 可能已经存在，尝试修改
        if (epoll_ctl(epoll_fd_, EPOLL_CTL_MOD, fd, &ev) < 0) {
            LOG_ERROR("Failed to add fd to epoll");
            return false;
        }
    }

    return true;
}

bool EventLoop::remove_fd(int fd) {
    if (epoll_fd_ < 0) return false;

    epoll_ctl(epoll_fd_, EPOLL_CTL_DEL, fd, nullptr);

    std::lock_guard<std::mutex> lock(fd_mutex_);
    fd_contexts_.erase(fd);

    return true;
}

bool EventLoop::modify_fd(int fd, IoEventType type) {
    if (epoll_fd_ < 0) return false;

    std::lock_guard<std::mutex> lock(fd_mutex_);
    auto it = fd_contexts_.find(fd);
    if (it == fd_contexts_.end()) return false;

    uint32_t events = EPOLLIN;
    if (it->second.write_callback) events |= EPOLLOUT;

    struct epoll_event ev;
    ev.events = events | EPOLLET;
    ev.data.fd = fd;

    return epoll_ctl(epoll_fd_, EPOLL_CTL_MOD, fd, &ev) == 0;
}

void EventLoop::run() {
    running_ = true;

    while (running_) {
        process_events(100);
        process_timers();
    }
}

void EventLoop::run_once(int timeout_ms) {
    process_events(timeout_ms);
    process_timers();
}

void EventLoop::stop() {
    running_ = false;
}

void EventLoop::process_events(int timeout_ms) {
    if (epoll_fd_ < 0) return;

    const int MAX_EVENTS = 64;
    struct epoll_event events[MAX_EVENTS];

    int n = epoll_wait(epoll_fd_, events, MAX_EVENTS, timeout_ms);
    if (n < 0) {
        if (errno != EINTR) {
            LOG_ERROR("epoll_wait failed");
        }
        return;
    }

    total_events_ += n;

    for (int i = 0; i < n; ++i) {
        int fd = events[i].data.fd;
        uint32_t revents = events[i].events;

        std::lock_guard<std::mutex> lock(fd_mutex_);
        auto it = fd_contexts_.find(fd);
        if (it == fd_contexts_.end()) continue;

        auto& ctx = it->second;

        // 处理错误
        if (revents & (EPOLLERR | EPOLLHUP)) {
            if (ctx.close_callback) {
                IoEvent event{fd, IoEventType::Close, {}};
                ctx.close_callback(event);
            }
            continue;
        }

        // 处理可读
        if (revents & EPOLLIN) {
            if (ctx.read_callback) {
                IoEvent event{fd, IoEventType::Read, {}};
                ctx.read_callback(event);
                total_callbacks_++;
            }
        }

        // 处理可写
        if (revents & EPOLLOUT) {
            if (ctx.write_callback) {
                IoEvent event{fd, IoEventType::Write, {}};
                ctx.write_callback(event);
                total_callbacks_++;
            }
        }
    }
}

uint64_t EventLoop::add_timer(uint32_t interval_ms, TimerCallback callback, bool repeat) {
    std::lock_guard<std::mutex> lock(timer_mutex_);

    TimerInfo info;
    info.id = next_timer_id_++;
    info.interval_ms = interval_ms;
    info.callback = std::move(callback);
    info.repeat = repeat;
    info.next_fire = std::chrono::steady_clock::now() + std::chrono::milliseconds(interval_ms);

    timers_.push_back(info);
    return info.id;
}

void EventLoop::remove_timer(uint64_t timer_id) {
    std::lock_guard<std::mutex> lock(timer_mutex_);
    timers_.erase(
        std::remove_if(timers_.begin(), timers_.end(),
                       [timer_id](const TimerInfo& t) { return t.id == timer_id; }),
        timers_.end()
    );
}

void EventLoop::process_timers() {
    std::lock_guard<std::mutex> lock(timer_mutex_);

    auto now = std::chrono::steady_clock::now();
    std::vector<TimerInfo> expired;
    std::vector<TimerInfo> remaining;

    for (auto& timer : timers_) {
        if (now >= timer.next_fire) {
            expired.push_back(timer);
            if (timer.repeat) {
                timer.next_fire = now + std::chrono::milliseconds(timer.interval_ms);
                remaining.push_back(timer);
            }
        } else {
            remaining.push_back(timer);
        }
    }

    timers_ = std::move(remaining);

    // 在锁外执行回调
    for (auto& timer : expired) {
        if (timer.callback) {
            timer.callback();
        }
    }
}

// ============================================================================
// NonBlockingSocket 实现
// ============================================================================

int NonBlockingSocket::create_tcp_socket() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd >= 0) {
        set_non_blocking(fd);
        set_tcp_nodelay(fd);
    }
    return fd;
}

int NonBlockingSocket::create_udp_socket() {
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd >= 0) {
        set_non_blocking(fd);
    }
    return fd;
}

bool NonBlockingSocket::set_non_blocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags < 0) return false;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK) == 0;
}

bool NonBlockingSocket::set_reuse_addr(int fd) {
    int opt = 1;
    return setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) == 0;
}

bool NonBlockingSocket::set_reuse_port(int fd) {
    int opt = 1;
    return setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt)) == 0;
}

bool NonBlockingSocket::set_tcp_nodelay(int fd) {
    int opt = 1;
    return setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &opt, sizeof(opt)) == 0;
}

bool NonBlockingSocket::set_keep_alive(int fd) {
    int opt = 1;
    return setsockopt(fd, SOL_SOCKET, SO_KEEPALIVE, &opt, sizeof(opt)) == 0;
}

bool NonBlockingSocket::set_send_buffer_size(int fd, int size) {
    return setsockopt(fd, SOL_SOCKET, SO_SNDBUF, &size, sizeof(size)) == 0;
}

bool NonBlockingSocket::set_recv_buffer_size(int fd, int size) {
    return setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &size, sizeof(size)) == 0;
}

bool NonBlockingSocket::connect(int fd, const std::string& host, uint16_t port) {
    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);

    if (inet_pton(AF_INET, host.c_str(), &addr.sin_addr) <= 0) {
        return false;
    }

    int ret = ::connect(fd, (struct sockaddr*)&addr, sizeof(addr));
    if (ret < 0 && errno != EINPROGRESS) {
        return false;
    }

    return true;
}

bool NonBlockingSocket::bind_and_listen(int fd, const std::string& host, uint16_t port, int backlog) {
    set_reuse_addr(fd);

    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);

    if (host == "0.0.0.0") {
        addr.sin_addr.s_addr = INADDR_ANY;
    } else {
        if (inet_pton(AF_INET, host.c_str(), &addr.sin_addr) <= 0) {
            return false;
        }
    }

    if (::bind(fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        return false;
    }

    return ::listen(fd, backlog) == 0;
}

int NonBlockingSocket::accept(int listen_fd, std::string& client_addr, uint16_t& client_port) {
    struct sockaddr_in addr;
    socklen_t addr_len = sizeof(addr);

    int fd = ::accept(listen_fd, (struct sockaddr*)&addr, &addr_len);
    if (fd >= 0) {
        set_non_blocking(fd);
        set_tcp_nodelay(fd);

        char addr_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &addr.sin_addr, addr_str, sizeof(addr_str));
        client_addr = addr_str;
        client_port = ntohs(addr.sin_port);
    }

    return fd;
}

ssize_t NonBlockingSocket::send(int fd, const Buffer& data) {
    return ::send(fd, data.data(), data.size(), MSG_NOSIGNAL);
}

ssize_t NonBlockingSocket::recv(int fd, Buffer& data, size_t max_size) {
    data.resize(max_size);
    ssize_t n = ::recv(fd, data.data(), max_size, 0);
    if (n > 0) {
        data.resize(n);
    } else {
        data.clear();
    }
    return n;
}

ssize_t NonBlockingSocket::sendto(int fd, const Buffer& data,
                                   const std::string& host, uint16_t port) {
    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    inet_pton(AF_INET, host.c_str(), &addr.sin_addr);

    return ::sendto(fd, data.data(), data.size(), 0,
                    (struct sockaddr*)&addr, sizeof(addr));
}

ssize_t NonBlockingSocket::recvfrom(int fd, Buffer& data,
                                     std::string& from_host, uint16_t& from_port) {
    struct sockaddr_in addr;
    socklen_t addr_len = sizeof(addr);

    data.resize(65536);
    ssize_t n = ::recvfrom(fd, data.data(), data.size(), 0,
                           (struct sockaddr*)&addr, &addr_len);

    if (n > 0) {
        data.resize(n);
        char addr_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &addr.sin_addr, addr_str, sizeof(addr_str));
        from_host = addr_str;
        from_port = ntohs(addr.sin_port);
    } else {
        data.clear();
    }

    return n;
}

// ============================================================================
// ConnectionManager 实现
// ============================================================================

ConnectionManager::ConnectionManager(std::shared_ptr<EventLoop> loop)
    : loop_(std::move(loop)) {}

ConnectionManager::~ConnectionManager() {
    close_all();
}

bool ConnectionManager::add_connection(int fd, IoCallback read_callback, IoCallback close_callback) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (connections_.count(fd)) {
        return false;
    }

    auto conn = std::make_shared<Connection>();
    conn->fd = fd;
    conn->read_callback = std::move(read_callback);
    conn->close_callback = std::move(close_callback);
    conn->last_active = std::chrono::steady_clock::now();

    connections_[fd] = conn;

    // 注册到事件循环
    if (loop_) {
        loop_->add_fd(fd, IoEventType::Read, [this, fd](const IoEvent& event) {
            std::lock_guard<std::mutex> lock(mutex_);
            auto it = connections_.find(fd);
            if (it != connections_.end() && it->second->read_callback) {
                it->second->read_callback(event);
                it->second->last_active = std::chrono::steady_clock::now();
            }
        });
    }

    return true;
}

void ConnectionManager::remove_connection(int fd) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = connections_.find(fd);
    if (it != connections_.end()) {
        if (it->second->close_callback) {
            IoEvent event{fd, IoEventType::Close, {}};
            it->second->close_callback(event);
        }
        connections_.erase(it);
    }

    if (loop_) {
        loop_->remove_fd(fd);
    }

    ::close(fd);
}

bool ConnectionManager::send(int fd, const Buffer& data) {
    ssize_t n = NonBlockingSocket::send(fd, data);
    return n == static_cast<ssize_t>(data.size());
}

uint32_t ConnectionManager::get_connection_count() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return static_cast<uint32_t>(connections_.size());
}

std::vector<int> ConnectionManager::get_connection_fds() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<int> fds;
    for (const auto& [fd, conn] : connections_) {
        fds.push_back(fd);
    }
    return fds;
}

void ConnectionManager::close_all() {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& [fd, conn] : connections_) {
        if (loop_) {
            loop_->remove_fd(fd);
        }
        ::close(fd);
    }

    connections_.clear();
}

} // namespace streaming
