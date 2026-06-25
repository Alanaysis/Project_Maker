#pragma once

/**
 * @file async_io.hpp
 * @brief 异步 I/O 处理
 *
 * 实现异步 I/O 机制，支持：
 * - epoll/kqueue/select
 * - 非阻塞 socket
 * - 事件驱动
 * - I/O 多路复用
 */

#include "streaming/types.hpp"
#include <functional>
#include <memory>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>
#include <unordered_map>

namespace streaming {

// I/O 事件类型
enum class IoEventType {
    Read,
    Write,
    Error,
    Close
};

// I/O 事件
struct IoEvent {
    int fd;
    IoEventType type;
    Buffer data;
};

// I/O 回调
using IoCallback = std::function<void(const IoEvent&)>;

/**
 * @brief I/O 事件循环
 *
 * 基于 epoll/kqueue 的事件循环实现。
 * 支持水平触发和边缘触发模式。
 */
class EventLoop {
public:
    EventLoop();
    ~EventLoop();

    // 生命周期
    bool initialize();
    void shutdown();
    bool is_running() const { return running_; }

    // 事件注册
    bool add_fd(int fd, IoEventType type, IoCallback callback);
    bool remove_fd(int fd);
    bool modify_fd(int fd, IoEventType type);

    // 运行事件循环
    void run();
    void run_once(int timeout_ms = 1000);
    void stop();

    // 定时器
    using TimerCallback = std::function<void()>;
    uint64_t add_timer(uint32_t interval_ms, TimerCallback callback, bool repeat = false);
    void remove_timer(uint64_t timer_id);

    // 统计
    uint64_t get_total_events() const { return total_events_; }
    uint64_t get_total_callbacks() const { return total_callbacks_; }

private:
    void process_events(int timeout_ms);
    void process_timers();

    int epoll_fd_ = -1;
    std::atomic<bool> running_{false};

    // fd -> callback 映射
    struct FdContext {
        IoCallback read_callback;
        IoCallback write_callback;
        IoCallback error_callback;
        IoCallback close_callback;
    };
    std::unordered_map<int, FdContext> fd_contexts_;
    std::mutex fd_mutex_;

    // 定时器
    struct TimerInfo {
        uint64_t id;
        uint32_t interval_ms;
        TimerCallback callback;
        bool repeat;
        Timestamp next_fire;
    };
    std::vector<TimerInfo> timers_;
    std::mutex timer_mutex_;
    uint64_t next_timer_id_ = 1;

    // 统计
    std::atomic<uint64_t> total_events_{0};
    std::atomic<uint64_t> total_callbacks_{0};
};

/**
 * @brief 非阻塞 Socket 工具类
 */
class NonBlockingSocket {
public:
    /**
     * @brief 创建非阻塞 TCP socket
     * @return socket fd，失败返回 -1
     */
    static int create_tcp_socket();

    /**
     * @brief 创建非阻塞 UDP socket
     * @return socket fd，失败返回 -1
     */
    static int create_udp_socket();

    /**
     * @brief 设置 socket 为非阻塞
     * @return 是否成功
     */
    static bool set_non_blocking(int fd);

    /**
     * @brief 设置 socket 选项
     */
    static bool set_reuse_addr(int fd);
    static bool set_reuse_port(int fd);
    static bool set_tcp_nodelay(int fd);
    static bool set_keep_alive(int fd);
    static bool set_send_buffer_size(int fd, int size);
    static bool set_recv_buffer_size(int fd, int size);

    /**
     * @brief 连接到服务器
     * @return 是否成功
     */
    static bool connect(int fd, const std::string& host, uint16_t port);

    /**
     * @brief 绑定并监听
     * @return 是否成功
     */
    static bool bind_and_listen(int fd, const std::string& host, uint16_t port, int backlog = 128);

    /**
     * @brief 接受连接
     * @return 客户端 fd，失败返回 -1
     */
    static int accept(int listen_fd, std::string& client_addr, uint16_t& client_port);

    /**
     * @brief 发送数据
     * @return 发送的字节数，-1 表示错误
     */
    static ssize_t send(int fd, const Buffer& data);

    /**
     * @brief 接收数据
     * @return 接收的字节数，0 表示关闭，-1 表示错误
     */
    static ssize_t recv(int fd, Buffer& data, size_t max_size = 65536);

    /**
     * @brief 发送 UDP 数据
     * @return 发送的字节数
     */
    static ssize_t sendto(int fd, const Buffer& data, const std::string& host, uint16_t port);

    /**
     * @brief 接收 UDP 数据
     * @return 接收的字节数
     */
    static ssize_t recvfrom(int fd, Buffer& data, std::string& from_host, uint16_t& from_port);
};

/**
 * @brief 连接管理器
 */
class ConnectionManager {
public:
    ConnectionManager(std::shared_ptr<EventLoop> loop);
    ~ConnectionManager();

    // 添加/移除连接
    bool add_connection(int fd, IoCallback read_callback, IoCallback close_callback);
    void remove_connection(int fd);

    // 发送数据
    bool send(int fd, const Buffer& data);

    // 连接信息
    uint32_t get_connection_count() const;
    std::vector<int> get_connection_fds() const;

    // 关闭所有连接
    void close_all();

private:
    struct Connection {
        int fd;
        IoCallback read_callback;
        IoCallback close_callback;
        Buffer send_buffer;
        Timestamp last_active;
    };

    std::shared_ptr<EventLoop> loop_;
    std::unordered_map<int, std::shared_ptr<Connection>> connections_;
    mutable std::mutex mutex_;
};

} // namespace streaming
