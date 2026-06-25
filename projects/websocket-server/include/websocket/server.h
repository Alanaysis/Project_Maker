#pragma once
/**
 * @file server.h
 * @brief WebSocket 服务器
 *
 * 基于 epoll 的高性能 WebSocket 服务器实现。
 * 支持：
 * - 多客户端并发连接
 * - WebSocket 协议完整实现
 * - 房间系统
 * - 消息路由
 * - 心跳检测
 * - 安全特性
 */

#include "common.h"
#include "connection.h"
#include "room.h"
#include "router.h"
#include "security.h"

#include <sys/epoll.h>

namespace ws {

/**
 * @brief 服务器配置
 */
struct ServerConfig {
    std::string host = "0.0.0.0";       // 监听地址
    uint16_t    port = 8080;             // 监听端口
    size_t      max_connections = 1024;  // 最大连接数
    int         heartbeat_interval_ms = 30000;  // 心跳间隔（毫秒）
    int         heartbeat_timeout_ms = 60000;   // 心跳超时（毫秒）
    size_t      max_message_size = 1048576;     // 最大消息大小 (1MB)
    std::string server_name = "WebSocket-Server/1.0";  // 服务器名称
};

/**
 * @brief WebSocket 服务器
 *
 * 主要功能：
 * 1. 监听 TCP 连接
 * 2. 处理 WebSocket 握手
 * 3. 管理所有连接
 * 4. 路由消息到处理器
 * 5. 管理房间系统
 */
class Server {
public:
    /**
     * @brief 构造函数
     * @param config 服务器配置
     */
    explicit Server(const ServerConfig& config = ServerConfig{});
    ~Server();

    // 禁止拷贝
    Server(const Server&) = delete;
    Server& operator=(const Server&) = delete;

    // ========================================================================
    // 生命周期
    // ========================================================================

    /**
     * @brief 启动服务器
     * @return 是否成功启动
     */
    bool start();

    /**
     * @brief 停止服务器
     */
    void stop();

    /**
     * @brief 运行事件循环（阻塞）
     */
    void run();

    /**
     * @brief 处理一次事件循环（非阻塞）
     * @param timeout_ms 超时时间（毫秒）
     */
    void poll(int timeout_ms = 100);

    /**
     * @brief 服务器是否正在运行
     */
    bool is_running() const { return running_.load(); }

    // ========================================================================
    // 事件回调设置
    // ========================================================================

    void set_on_open(std::function<void(ConnectionPtr)> callback) {
        callbacks_.on_open = std::move(callback);
    }

    void set_on_message(std::function<void(ConnectionPtr, const Message&)> callback) {
        callbacks_.on_message = std::move(callback);
    }

    void set_on_close(std::function<void(ConnectionPtr, CloseCode, const std::string&)> callback) {
        callbacks_.on_close = std::move(callback);
    }

    void set_on_error(std::function<void(ConnectionPtr, const std::string&)> callback) {
        callbacks_.on_error = std::move(callback);
    }

    // ========================================================================
    // 连接管理
    // ========================================================================

    /**
     * @brief 获取所有连接
     */
    std::vector<ConnectionPtr> get_connections() const;

    /**
     * @brief 根据 ID 获取连接
     */
    ConnectionPtr get_connection(uint64_t id) const;

    /**
     * @brief 获取连接数量
     */
    size_t connection_count() const;

    /**
     * @brief 关闭所有连接
     */
    void close_all(CloseCode code = CloseCode::GoingAway, const std::string& reason = "");

    // ========================================================================
    // 消息广播
    // ========================================================================

    /**
     * @brief 广播文本消息给所有连接
     */
    void broadcast_text(const std::string& text);

    /**
     * @brief 广播二进制消息给所有连接
     */
    void broadcast_binary(const std::vector<uint8_t>& data);

    /**
     * @brief 广播消息给所有连接（排除指定连接）
     */
    void broadcast_text(const std::string& text, ConnectionPtr exclude);

    // ========================================================================
    // 房间系统
    // ========================================================================

    /**
     * @brief 获取房间管理器
     */
    RoomManager& room_manager() { return room_manager_; }

    /**
     * @brief 广播消息到指定房间
     */
    void broadcast_to_room(const std::string& room_name, const std::string& text);

    // ========================================================================
    // 消息路由
    // ========================================================================

    /**
     * @brief 获取消息路由器
     */
    Router& router() { return router_; }

    // ========================================================================
    // 安全
    // ========================================================================

    /**
     * @brief 获取安全管理器
     */
    SecurityManager& security() { return security_; }

    // ========================================================================
    // 配置
    // ========================================================================

    /**
     * @brief 获取服务器配置
     */
    const ServerConfig& config() const { return config_; }

private:
    /**
     * @brief 创建监听套接字
     */
    bool create_listener();

    /**
     * @brief 接受新连接
     */
    void accept_connection();

    /**
     * @brief 处理连接的可读事件
     */
    void handle_connection_read(ConnectionPtr conn);

    /**
     * @brief 处理连接的可写事件
     */
    void handle_connection_write(ConnectionPtr conn);

    /**
     * @brief 关闭连接
     */
    void remove_connection(ConnectionPtr conn);

    /**
     * @brief 设置 epoll 事件
     */
    void epoll_add(int fd, uint32_t events);
    void epoll_mod(int fd, uint32_t events);
    void epoll_del(int fd);

    /**
     * @brief 心跳检测
     */
    void check_heartbeat();

    // 配置
    ServerConfig config_;

    // 网络
    int listen_fd_ = -1;
    int epoll_fd_ = -1;

    // 运行状态
    std::atomic<bool> running_{false};

    // 连接管理
    mutable std::mutex connections_mutex_;
    std::unordered_map<uint64_t, ConnectionPtr> connections_;
    std::unordered_map<int, uint64_t> fd_to_conn_id_;

    // 事件回调
    ConnectionCallbacks callbacks_;

    // 子系统
    RoomManager room_manager_;
    Router router_;
    SecurityManager security_;

    // 心跳
    int64_t last_heartbeat_check_ = 0;

    // epoll 事件缓冲区
    static constexpr int MAX_EVENTS = 1024;
    struct epoll_event events_[MAX_EVENTS];
};

} // namespace ws
