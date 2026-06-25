/**
 * @file async_io.cpp
 * @brief 异步 I/O 和性能优化实现
 *
 * 实现：
 * - epoll 事件循环
 * - 线程池
 * - 连接池
 * - 异步 DNS 查询
 */

#include "performance/async_io.h"
#include "resolver/dns_resolver.h"
#include "monitoring/dns_monitor.h"

#include <sys/epoll.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>
#include <algorithm>

namespace dns {

// ============================================================================
// EventLoop 实现
// ============================================================================

EventLoop::EventLoop() {
    init_epoll();
}

EventLoop::~EventLoop() {
    stop();
    if (epoll_fd_ >= 0) {
        close(epoll_fd_);
    }
}

void EventLoop::init_epoll() {
#ifdef __linux__
    epoll_fd_ = epoll_create1(0);
    if (epoll_fd_ < 0) {
        DNS_LOG_ERROR("EventLoop", "Failed to create epoll: " +
                      std::string(strerror(errno)));
    }
#else
    // macOS/BSD 使用 kqueue
    epoll_fd_ = kqueue();
#endif
}

bool EventLoop::register_event(int fd, EventType type,
                                EventCallback callback) {
    if (epoll_fd_ < 0) return false;

    struct epoll_event ev{};
    ev.data.fd = fd;

    switch (type) {
        case EventType::READ:  ev.events = EPOLLIN; break;
        case EventType::WRITE: ev.events = EPOLLOUT; break;
        case EventType::ERROR: ev.events = EPOLLERR; break;
        default: ev.events = EPOLLIN; break;
    }

    if (epoll_ctl(epoll_fd_, EPOLL_CTL_ADD, fd, &ev) < 0) {
        DNS_LOG_ERROR("EventLoop", "Failed to register event: " +
                      std::string(strerror(errno)));
        return false;
    }

    std::lock_guard<std::mutex> lock(events_mutex_);
    events_[fd] = {callback, type};
    return true;
}

bool EventLoop::modify_event(int fd, EventType type,
                              EventCallback callback) {
    if (epoll_fd_ < 0) return false;

    struct epoll_event ev{};
    ev.data.fd = fd;

    switch (type) {
        case EventType::READ:  ev.events = EPOLLIN; break;
        case EventType::WRITE: ev.events = EPOLLOUT; break;
        case EventType::ERROR: ev.events = EPOLLERR; break;
        default: ev.events = EPOLLIN; break;
    }

    if (epoll_ctl(epoll_fd_, EPOLL_CTL_MOD, fd, &ev) < 0) {
        return false;
    }

    std::lock_guard<std::mutex> lock(events_mutex_);
    events_[fd] = {callback, type};
    return true;
}

bool EventLoop::unregister_event(int fd) {
    if (epoll_fd_ < 0) return false;

    epoll_ctl(epoll_fd_, EPOLL_CTL_DEL, fd, nullptr);

    std::lock_guard<std::mutex> lock(events_mutex_);
    events_.erase(fd);
    return true;
}

void EventLoop::run() {
    running_ = true;

    constexpr int MAX_EVENTS = 64;
    struct epoll_event events[MAX_EVENTS];

    while (running_) {
        // 计算超时
        int timeout_ms = 1000;  // 默认 1 秒

        {
            std::lock_guard<std::mutex> lock(timeout_mutex_);
            if (!timeouts_.empty()) {
                auto now = std::chrono::steady_clock::now();
                auto& next = timeouts_.top();
                auto diff = std::chrono::duration_cast<std::chrono::milliseconds>(
                    next.expire_at - now);
                timeout_ms = std::max(0, static_cast<int>(diff.count()));
            }
        }

        int nfds = epoll_wait(epoll_fd_, events, MAX_EVENTS, timeout_ms);
        if (nfds < 0) {
            if (errno == EINTR) continue;
            break;
        }

        // 处理事件
        for (int i = 0; i < nfds; i++) {
            int fd = events[i].data.fd;
            EventType type = EventType::READ;

            if (events[i].events & EPOLLIN) type = EventType::READ;
            else if (events[i].events & EPOLLOUT) type = EventType::WRITE;
            else if (events[i].events & EPOLLERR) type = EventType::ERROR;

            std::lock_guard<std::mutex> lock(events_mutex_);
            auto it = events_.find(fd);
            if (it != events_.end()) {
                it->second.callback(fd, type);
            }
        }

        // 处理超时
        {
            std::lock_guard<std::mutex> lock(timeout_mutex_);
            auto now = std::chrono::steady_clock::now();
            while (!timeouts_.empty() && timeouts_.top().expire_at <= now) {
                auto callback = timeouts_.top().callback;
                timeouts_.pop();
                callback();
            }
        }
    }
}

void EventLoop::stop() {
    running_ = false;
}

void EventLoop::set_timeout(std::chrono::milliseconds timeout,
                             std::function<void()> callback) {
    std::lock_guard<std::mutex> lock(timeout_mutex_);
    timeouts_.push({
        std::chrono::steady_clock::now() + timeout,
        std::move(callback)
    });
}

// ============================================================================
// ThreadPool 实现
// ============================================================================

ThreadPool::ThreadPool(size_t threads) {
    for (size_t i = 0; i < threads; i++) {
        workers_.emplace_back(&ThreadPool::worker_thread, this);
    }
}

ThreadPool::~ThreadPool() {
    shutdown();
}

template<typename F, typename... Args>
auto ThreadPool::submit(F&& f, Args&&... args)
    -> std::future<std::invoke_result_t<F, Args...>> {

    using return_type = std::invoke_result_t<F, Args...>;

    auto task = std::make_shared<std::packaged_task<return_type()>>(
        std::bind(std::forward<F>(f), std::forward<Args>(args)...)
    );

    std::future<return_type> result = task->get_future();

    {
        std::unique_lock<std::mutex> lock(mutex_);

        if (stop_) {
            throw std::runtime_error("ThreadPool is stopped");
        }

        tasks_.emplace([task]() { (*task)(); });
        active_tasks_++;
    }

    condition_.notify_one();
    return result;
}

size_t ThreadPool::queue_size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return tasks_.size();
}

void ThreadPool::wait_all() {
    std::unique_lock<std::mutex> lock(mutex_);
    finished_condition_.wait(lock, [this]() {
        return tasks_.empty() && active_tasks_ == 0;
    });
}

void ThreadPool::shutdown() {
    {
        std::unique_lock<std::mutex> lock(mutex_);
        stop_ = true;
    }

    condition_.notify_all();

    for (auto& worker : workers_) {
        if (worker.joinable()) {
            worker.join();
        }
    }
}

void ThreadPool::worker_thread() {
    while (true) {
        std::function<void()> task;
        {
            std::unique_lock<std::mutex> lock(mutex_);
            condition_.wait(lock, [this]() {
                return stop_ || !tasks_.empty();
            });

            if (stop_ && tasks_.empty()) {
                return;
            }

            task = std::move(tasks_.front());
            tasks_.pop();
        }

        task();

        {
            std::lock_guard<std::mutex> lock(mutex_);
            active_tasks_--;
        }
        finished_condition_.notify_all();
    }
}

// ============================================================================
// ConnectionPool 实现
// ============================================================================

ConnectionPool::ConnectionPool(const std::string& server,
                                 uint16_t port,
                                 const ConnectionPoolConfig& config)
    : server_(server), port_(port), config_(config) {

    // 预创建最小连接数
    for (size_t i = 0; i < config_.min_connections; i++) {
        int fd = create_connection();
        if (fd >= 0) {
            idle_connections_.push_back(fd);
            total_connections_++;
        }
    }

    // 启动清理线程
    cleanup_thread_ = std::thread(&ConnectionPool::cleanup_idle, this);
}

ConnectionPool::~ConnectionPool() {
    shutdown();
}

int ConnectionPool::acquire() {
    std::lock_guard<std::mutex> lock(mutex_);

    // 尝试从空闲连接获取
    if (!idle_connections_.empty()) {
        int fd = idle_connections_.back();
        idle_connections_.pop_back();
        active_connections_[fd] = std::chrono::steady_clock::now();
        return fd;
    }

    // 创建新连接
    if (total_connections_ < config_.max_connections) {
        int fd = create_connection();
        if (fd >= 0) {
            active_connections_[fd] = std::chrono::steady_clock::now();
            total_connections_++;
            return fd;
        }
    }

    return -1;
}

void ConnectionPool::release(int fd) {
    std::lock_guard<std::mutex> lock(mutex_);

    active_connections_.erase(fd);
    idle_connections_.push_back(fd);
}

void ConnectionPool::shutdown() {
    shutdown_ = true;

    if (cleanup_thread_.joinable()) {
        cleanup_thread_.join();
    }

    std::lock_guard<std::mutex> lock(mutex_);

    for (int fd : idle_connections_) {
        close(fd);
    }
    idle_connections_.clear();

    for (auto& [fd, time] : active_connections_) {
        close(fd);
    }
    active_connections_.clear();
}

size_t ConnectionPool::active_connections() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return active_connections_.size();
}

size_t ConnectionPool::idle_connections() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return idle_connections_.size();
}

int ConnectionPool::create_connection() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return -1;

    struct sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port_);
    inet_pton(AF_INET, server_.c_str(), &addr.sin_addr);

    // 设置连接超时
    struct timeval tv{};
    tv.tv_sec = config_.connect_timeout.count();
    tv.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    if (connect(sock, reinterpret_cast<struct sockaddr*>(&addr),
                sizeof(addr)) < 0) {
        close(sock);
        return -1;
    }

    return sock;
}

void ConnectionPool::cleanup_idle() {
    while (!shutdown_) {
        std::this_thread::sleep_for(std::chrono::seconds(60));

        std::lock_guard<std::mutex> lock(mutex_);
        auto now = std::chrono::steady_clock::now();

        auto it = idle_connections_.begin();
        while (it != idle_connections_.end()) {
            // 检查空闲时间 (简化实现)
            if (idle_connections_.size() > config_.min_connections) {
                close(*it);
                it = idle_connections_.erase(it);
                total_connections_--;
            } else {
                ++it;
            }
        }
    }
}

// ============================================================================
// AsyncDnsQuerier 实现
// ============================================================================

AsyncDnsQuerier::AsyncDnsQuerier(size_t concurrency)
    : pool_(concurrency) {}

AsyncDnsQuerier::~AsyncDnsQuerier() {
    shutdown();
}

void AsyncDnsQuerier::query_async(
    const std::string& server,
    const DnsMessage& request,
    std::chrono::seconds timeout,
    QueryCallback callback) {

    pending_queries_++;

    pool_.submit([this, server, request, timeout, callback]() {
        process_query(server, request, timeout, callback);
    });
}

void AsyncDnsQuerier::query_batch(
    const std::vector<std::pair<std::string, DnsMessage>>& queries,
    std::chrono::seconds timeout,
    std::function<void(std::vector<std::optional<DnsMessage>>)> callback) {

    auto results = std::make_shared<std::vector<std::optional<DnsMessage>>>(
        queries.size());
    auto completed = std::make_shared<std::atomic<size_t>>(0);

    for (size_t i = 0; i < queries.size(); i++) {
        query_async(queries[i].first, queries[i].second, timeout,
            [results, completed, callback, i, total = queries.size()]
            (std::optional<DnsMessage> response) {
                (*results)[i] = std::move(response);
                if (completed->fetch_add(1) + 1 == total) {
                    callback(std::move(*results));
                }
            });
    }
}

void AsyncDnsQuerier::wait_all() {
    std::unique_lock<std::mutex> lock(completion_mutex_);
    completion_cv_.wait(lock, [this]() {
        return pending_queries_ == 0;
    });
}

void AsyncDnsQuerier::shutdown() {
    pool_.shutdown();
    wait_all();
}

void AsyncDnsQuerier::process_query(
    const std::string& server,
    const DnsMessage& request,
    std::chrono::seconds timeout,
    QueryCallback callback) {

    DnsQuerier querier;
    auto response = querier.query(server, request, timeout);
    callback(response);

    pending_queries_--;
    completion_cv_.notify_all();
}

// ============================================================================
// MessageCompressor 实现
// ============================================================================

std::vector<uint8_t> MessageCompressor::compress(
    const std::vector<uint8_t>& message) {
    // DNS 报文压缩主要通过域名压缩实现
    // 这里返回原始报文（压缩已在序列化时处理）
    return message;
}

std::vector<uint8_t> MessageCompressor::decompress(
    const std::vector<uint8_t>& message) {
    // DNS 报文解压主要通过域名解压实现
    // 这里返回原始报文（解压已在反序列化时处理）
    return message;
}

bool MessageCompressor::needs_compression(
    const std::vector<uint8_t>& message) {
    return message.size() > DNS_MAX_UDP_SIZE;
}

} // namespace dns
