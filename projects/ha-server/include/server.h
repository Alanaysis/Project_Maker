#pragma once

/**
 * @file server.h
 * @brief 服务器核心类
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

#include "common.h"
#include "backend.h"
#include "load_balancer.h"
#include "health_checker.h"
#include "connection_pool.h"
#include "http_parser.h"
#include <thread>
#include <vector>
#include <memory>
#include <atomic>
#include <functional>

namespace ha_server {

/**
 * @brief 服务器配置
 */
struct ServerConfig {
    std::string host = "0.0.0.0";           // 监听地址
    int port = DEFAULT_PORT;                  // 监听端口
    int worker_threads = DEFAULT_WORKER_THREADS;  // 工作线程数
    BalancerType balancer_type = BalancerType::RoundRobin;  // 负载均衡算法
    HealthCheckConfig health_check;           // 健康检查配置
    ConnectionPoolConfig pool_config;         // 连接池配置
};

/**
 * @brief 高可用服务器
 *
 * 核心服务器类，实现请求的接收、解析、负载均衡和转发。
 *
 * 架构设计：
 * 1. 主线程运行事件循环，接受新连接
 * 2. 工作线程池处理请求转发
 * 3. 健康检查线程监控后端状态
 *
 * 核心循环：
 * 请求接入 → 健康检查 → 负载均衡 → 请求转发 → 响应返回 → 故障转移
 *
 * ⭐ 重点：
 * - epoll 事件驱动模型
 * - 多线程协作
 * - 连接状态管理
 *
 * 💡 思考：
 * - 如何实现优雅关闭？
 * - 如何处理连接超时？
 * - 如何实现配置热更新？
 */
class Server {
public:
    /**
     * @brief 构造函数
     * @param config 服务器配置
     */
    explicit Server(const ServerConfig& config = {});

    /**
     * @brief 析构函数
     *
     * 自动停止服务器并清理资源
     */
    ~Server();

    /**
     * @brief 启动服务器
     * @return 成功返回 true
     *
     * 初始化 epoll、绑定端口、启动工作线程和健康检查。
     */
    bool start();

    /**
     * @brief 停止服务器
     *
     * 停止事件循环、工作线程和健康检查。
     */
    void stop();

    /**
     * @brief 检查服务器是否运行中
     * @return 运行中返回 true
     */
    bool is_running() const { return running_.load(); }

    /**
     * @brief 添加后端服务器
     * @param host 后端地址
     * @param port 后端端口
     * @param weight 权重
     */
    void add_backend(const std::string& host, int port, int weight = 1);

    /**
     * @brief 设置负载均衡算法
     * @param type 算法类型
     */
    void set_balancer(BalancerType type);

    /**
     * @brief 获取服务器统计
     * @return 统计信息
     */
    ServerStats get_stats() const { return stats_; }

    /**
     * @brief 获取后端管理器
     * @return 后端管理器引用
     */
    BackendManager& get_backend_manager() { return backend_manager_; }

private:
    /**
     * @brief 初始化监听 socket
     * @return 成功返回 true
     */
    bool init_listen_socket();

    /**
     * @brief 初始化 epoll
     * @return 成功返回 true
     */
    bool init_epoll();

    /**
     * @brief 事件循环
     *
     * 主线程运行的核心循环，处理所有 I/O 事件。
     */
    void event_loop();

    /**
     * @brief 接受新连接
     */
    void accept_connection();

    /**
     * @brief 处理连接事件
     * @param fd 连接 fd
     * @param events 事件类型
     */
    void handle_connection(int fd, uint32_t events);

    /**
     * @brief 处理客户端请求
     * @param client_fd 客户端 fd
     */
    void handle_request(int client_fd);

    /**
     * @brief 转发请求到后端
     * @param client_fd 客户端 fd
     * @param request HTTP 请求
     */
    void forward_request(int client_fd, const HttpRequest& request);

    /**
     * @brief 发送错误响应
     * @param client_fd 客户端 fd
     * @param status_code 状态码
     * @param message 错误消息
     */
    void send_error_response(int client_fd, int status_code, const std::string& message);

    /**
     * @brief 添加 fd 到 epoll
     * @param fd 文件描述符
     * @param events 关注的事件
     * @return 成功返回 true
     */
    bool epoll_add(int fd, uint32_t events);

    /**
     * @brief 修改 epoll 中的 fd
     * @param fd 文件描述符
     * @param events 新的事件
     * @return 成功返回 true
     */
    bool epoll_mod(int fd, uint32_t events);

    /**
     * @brief 从 epoll 中移除 fd
     * @param fd 文件描述符
     * @return 成功返回 true
     */
    bool epoll_del(int fd);

    /**
     * @brief 关闭连接
     * @param fd 文件描述符
     */
    void close_connection(int fd);

    ServerConfig config_;
    int listen_fd_ = -1;
    int epoll_fd_ = -1;
    struct epoll_event events_[MAX_EVENTS];

    std::atomic<bool> running_{false};
    std::thread event_thread_;
    std::vector<std::thread> worker_threads_;

    BackendManager backend_manager_;
    std::unique_ptr<LoadBalancer> balancer_;
    std::unique_ptr<HealthChecker> health_checker_;
    ConnectionPoolManager pool_manager_;
    ServerStats stats_;
};

} // namespace ha_server
