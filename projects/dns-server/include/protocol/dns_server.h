#pragma once

/**
 * @file dns_server.h
 * @brief DNS 服务器核心实现
 *
 * 实现 DNS 服务器的网络层，包括：
 * - UDP/TCP 监听
 * - 请求分发
 * - 并发处理
 * - 异步 I/O
 */

#include "dns_message.h"
#include <functional>
#include <memory>
#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <queue>
#include <condition_variable>
#include <unordered_map>
#include <chrono>

namespace dns {

// ============================================================================
// DNS 请求处理回调
// ============================================================================

using DnsRequestHandler = std::function<DnsMessage(const DnsMessage& request,
                                                     const std::string& client_addr,
                                                     uint16_t client_port)>;

// ============================================================================
// DNS 服务器配置
// ============================================================================

struct DnsServerConfig {
    std::string bind_address = "0.0.0.0";  // 绑定地址
    uint16_t port = 53;                     // 监听端口
    size_t thread_pool_size = 4;            // 线程池大小
    size_t max_connections = 1000;          // 最大连接数
    size_t max_message_size = 4096;         // 最大报文大小
    bool enable_udp = true;                 // 启用 UDP
    bool enable_tcp = true;                 // 启用 TCP
    std::chrono::seconds tcp_timeout{30};   // TCP 超时
    std::chrono::seconds query_timeout{5};  // 查询超时
};

// ============================================================================
// UDP 服务器
// ============================================================================

class UdpServer {
public:
    explicit UdpServer(const DnsServerConfig& config);
    ~UdpServer();

    // 启动服务器
    bool start(DnsRequestHandler handler);

    // 停止服务器
    void stop();

    // 是否运行中
    bool is_running() const { return running_.load(); }

private:
    void receive_loop();
    void process_request(const std::vector<uint8_t>& data,
                         const std::string& client_addr,
                         uint16_t client_port);

    DnsServerConfig config_;
    int socket_fd_ = -1;
    std::atomic<bool> running_{false};
    std::thread receive_thread_;
    DnsRequestHandler handler_;

    // 线程池
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> task_queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;
    std::atomic<bool> stop_workers_{false};

    void worker_thread();
    void submit_task(std::function<void()> task);
};

// ============================================================================
// TCP 服务器
// ============================================================================

class TcpServer {
public:
    explicit TcpServer(const DnsServerConfig& config);
    ~TcpServer();

    // 启动服务器
    bool start(DnsRequestHandler handler);

    // 停止服务器
    void stop();

    // 是否运行中
    bool is_running() const { return running_.load(); }

private:
    void accept_loop();
    void handle_connection(int client_fd, const std::string& client_addr);

    DnsServerConfig config_;
    int listen_fd_ = -1;
    std::atomic<bool> running_{false};
    std::thread accept_thread_;
    DnsRequestHandler handler_;

    // 连接管理
    std::mutex connections_mutex_;
    std::unordered_map<int, std::thread> connections_;
    std::atomic<size_t> active_connections_{0};
};

// ============================================================================
// DNS 服务器
// ============================================================================

class DnsServer {
public:
    explicit DnsServer(const DnsServerConfig& config = DnsServerConfig{});
    ~DnsServer();

    // 设置请求处理器
    void set_handler(DnsRequestHandler handler);

    // 启动服务器
    bool start();

    // 停止服务器
    void stop();

    // 是否运行中
    bool is_running() const;

    // 获取统计信息
    struct Stats {
        uint64_t queries_received = 0;
        uint64_t queries_processed = 0;
        uint64_t queries_failed = 0;
        uint64_t udp_queries = 0;
        uint64_t tcp_queries = 0;
        double avg_response_time_ms = 0.0;
    };
    Stats get_stats() const;

private:
    DnsServerConfig config_;
    DnsRequestHandler handler_;
    std::unique_ptr<UdpServer> udp_server_;
    std::unique_ptr<TcpServer> tcp_server_;

    // 统计信息
    mutable std::mutex stats_mutex_;
    Stats stats_;
    void update_stats(bool success, double response_time_ms, bool is_tcp);
};

} // namespace dns
