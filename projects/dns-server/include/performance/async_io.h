#pragma once

/**
 * @file async_io.h
 * @brief 异步 I/O 和性能优化
 *
 * 实现：
 * - epoll/kqueue 异步 I/O
 * - 事件循环
 * - 连接池
 * - 线程池
 */

#include "../protocol/dns_message.h"
#include <functional>
#include <memory>
#include <thread>
#include <vector>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <chrono>
#include <future>
#include <unordered_map>
#include <cstdint>

namespace dns {

// ============================================================================
// 事件类型
// ============================================================================

enum class EventType {
    READ,
    WRITE,
    ERROR,
    TIMEOUT,
};

// ============================================================================
// 事件回调
// ============================================================================

using EventCallback = std::function<void(int fd, EventType type)>;

// ============================================================================
// 事件循环 (基于 epoll/kqueue)
// ============================================================================

class EventLoop {
public:
    EventLoop();
    ~EventLoop();

    // 注册事件
    bool register_event(int fd, EventType type, EventCallback callback);

    // 修改事件
    bool modify_event(int fd, EventType type, EventCallback callback);

    // 删除事件
    bool unregister_event(int fd);

    // 运行事件循环
    void run();

    // 停止事件循环
    void stop();

    // 是否运行中
    bool is_running() const { return running_.load(); }

    // 设置超时回调
    void set_timeout(std::chrono::milliseconds timeout,
                     std::function<void()> callback);

private:
    void init_epoll();

    int epoll_fd_ = -1;
    std::atomic<bool> running_{false};
    std::thread loop_thread_;

    struct EventEntry {
        EventCallback callback;
        EventType type;
    };
    std::unordered_map<int, EventEntry> events_;
    std::mutex events_mutex_;

    // 超时管理
    struct TimeoutEntry {
        std::chrono::steady_clock::time_point expire_at;
        std::function<void()> callback;
        bool operator>(const TimeoutEntry& other) const {
            return expire_at > other.expire_at;
        }
    };
    std::priority_queue<TimeoutEntry, std::vector<TimeoutEntry>,
                        std::greater<>> timeouts_;
    std::mutex timeout_mutex_;
};

// ============================================================================
// 线程池
// ============================================================================

class ThreadPool {
public:
    explicit ThreadPool(size_t threads = std::thread::hardware_concurrency());
    ~ThreadPool();

    // 提交任务
    template<typename F, typename... Args>
    auto submit(F&& f, Args&&... args)
        -> std::future<std::invoke_result_t<F, Args...>>;

    // 获取队列大小
    size_t queue_size() const;

    // 获取线程数
    size_t thread_count() const { return workers_.size(); }

    // 等待所有任务完成
    void wait_all();

    // 停止线程池
    void shutdown();

private:
    void worker_thread();

    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;

    mutable std::mutex mutex_;
    std::condition_variable condition_;
    std::condition_variable finished_condition_;
    std::atomic<bool> stop_{false};
    std::atomic<size_t> active_tasks_{0};
};

// ============================================================================
// 连接池
// ============================================================================

struct ConnectionPoolConfig {
    size_t min_connections = 2;       // 最小连接数
    size_t max_connections = 10;      // 最大连接数
    std::chrono::seconds idle_timeout{300};  // 空闲超时
    std::chrono::seconds connect_timeout{5}; // 连接超时
    size_t max_retries = 3;           // 最大重试次数
};

class ConnectionPool {
public:
    explicit ConnectionPool(const std::string& server,
                            uint16_t port,
                            const ConnectionPoolConfig& config = ConnectionPoolConfig{});
    ~ConnectionPool();

    // 获取连接
    int acquire();

    // 释放连接
    void release(int fd);

    // 关闭连接池
    void shutdown();

    // 获取活跃连接数
    size_t active_connections() const;

    // 获取空闲连接数
    size_t idle_connections() const;

private:
    int create_connection();
    void cleanup_idle();

    std::string server_;
    uint16_t port_;
    ConnectionPoolConfig config_;

    mutable std::mutex mutex_;
    std::vector<int> idle_connections_;
    std::unordered_map<int, std::chrono::steady_clock::time_point> active_connections_;
    std::atomic<size_t> total_connections_{0};

    std::thread cleanup_thread_;
    std::atomic<bool> shutdown_{false};
};

// ============================================================================
// 异步 DNS 查询器
// ============================================================================

class AsyncDnsQuerier {
public:
    AsyncDnsQuerier(size_t concurrency = 10);
    ~AsyncDnsQuerier();

    // 异步查询
    using QueryCallback = std::function<void(std::optional<DnsMessage>)>;
    void query_async(const std::string& server,
                     const DnsMessage& request,
                     std::chrono::seconds timeout,
                     QueryCallback callback);

    // 批量查询
    void query_batch(const std::vector<std::pair<std::string, DnsMessage>>& queries,
                     std::chrono::seconds timeout,
                     std::function<void(std::vector<std::optional<DnsMessage>>)> callback);

    // 等待所有查询完成
    void wait_all();

    // 停止
    void shutdown();

private:
    void process_query(const std::string& server,
                       const DnsMessage& request,
                       std::chrono::seconds timeout,
                       QueryCallback callback);

    ThreadPool pool_;
    std::atomic<uint64_t> pending_queries_{0};
    std::mutex completion_mutex_;
    std::condition_variable completion_cv_;
};

// ============================================================================
// 压缩传输 (DNS Compression)
// ============================================================================

class MessageCompressor {
public:
    // 压缩 DNS 报文
    static std::vector<uint8_t> compress(const std::vector<uint8_t>& message);

    // 解压 DNS 报文
    static std::vector<uint8_t> decompress(const std::vector<uint8_t>& message);

    // 检查是否需要压缩
    static bool needs_compression(const std::vector<uint8_t>& message);
};

} // namespace dns
