#pragma once

/**
 * @file connection_pool.h
 * @brief 连接池管理
 *
 * 实现到后端服务器的连接池管理。
 * 连接池可以减少连接建立的开销，提高性能。
 *
 * ⭐ 重点：连接池是性能优化的关键
 * 💡 思考：连接池大小如何确定？（Little's Law: L = λW）
 */

#include "common.h"
#include <vector>
#include <mutex>
#include <chrono>
#include <string>

namespace ha_server {

/**
 * @brief 连接池配置
 */
struct ConnectionPoolConfig {
    size_t max_size = DEFAULT_POOL_SIZE;                      // 最大连接数
    size_t min_size = 1;                                       // 最小连接数
    std::chrono::milliseconds idle_timeout{60000};             // 空闲超时时间
    std::chrono::milliseconds connect_timeout{5000};           // 连接超时时间
};

/**
 * @brief 连接池
 *
 * 管理到单个后端服务器的连接。
 * 支持连接复用、超时回收、连接健康检查。
 *
 * 工作原理：
 * 1. 初始化时创建 min_size 个连接
 * 2. 请求到来时：
 *    a. 池中有空闲连接 → 复用
 *    b. 池中无空闲但未达上限 → 创建新连接
 *    c. 池满且无空闲 → 等待或返回失败
 * 3. 请求完成后：连接放回池中
 * 4. 定期清理超时的空闲连接
 *
 * ⭐ 重点：
 * - 连接复用减少握手开销
 * - 超时回收避免资源泄漏
 * - 线程安全保证并发访问
 *
 * 💡 思考：
 * - 连接池 vs 长连接 vs 短连接各有什么适用场景？
 * - 如何检测连接是否已经断开？
 * - 连接池的健康检查如何实现？
 */
class ConnectionPool {
public:
    /**
     * @brief 连接信息
     */
    struct Connection {
        int fd;                                              // socket 文件描述符
        std::chrono::steady_clock::time_point created_time;  // 创建时间
        std::chrono::steady_clock::time_point last_used_time;// 最后使用时间
        bool in_use;                                          // 是否正在使用
        bool valid;                                           // 是否有效
    };

    /**
     * @brief 构造函数
     * @param host 后端主机地址
     * @param port 后端端口号
     * @param config 连接池配置
     */
    ConnectionPool(const std::string& host, int port,
                   const ConnectionPoolConfig& config = {});

    /**
     * @brief 析构函数
     *
     * 关闭所有连接
     */
    ~ConnectionPool();

    /**
     * @brief 获取连接
     * @return 连接的 socket fd，失败返回 -1
     *
     * 优先复用空闲连接，没有空闲连接时创建新连接。
     */
    int acquire();

    /**
     * @brief 释放连接
     * @param fd 连接的 socket fd
     *
     * 将连接标记为空闲，可供其他请求复用。
     */
    void release(int fd);

    /**
     * @brief 移除连接
     * @param fd 连接的 socket fd
     *
     * 关闭并移除连接，通常在连接出错时调用。
     */
    void remove(int fd);

    /**
     * @brief 获取池大小
     * @return 当前连接总数
     */
    size_t size() const;

    /**
     * @brief 获取可用连接数
     * @return 空闲连接数
     */
    size_t available() const;

    /**
     * @brief 获取使用中的连接数
     * @return 使用中连接数
     */
    size_t in_use_count() const;

    /**
     * @brief 清理超时连接
     *
     * 移除空闲时间超过 idle_timeout 的连接。
     * 保持至少 min_size 个连接。
     */
    void cleanup_idle();

    /**
     * @brief 清空连接池
     *
     * 关闭所有连接
     */
    void clear();

private:
    /**
     * @brief 创建新连接
     * @return 连接的 socket fd，失败返回 -1
     */
    int create_connection();

    /**
     * @brief 关闭连接
     * @param fd 连接的 socket fd
     */
    void close_connection(int fd);

    std::string host_;
    int port_;
    ConnectionPoolConfig config_;
    mutable std::mutex mutex_;
    std::vector<Connection> connections_;
};

/**
 * @brief 连接池管理器
 *
 * 管理到所有后端的连接池。
 * 根据后端地址获取对应的连接池。
 */
class ConnectionPoolManager {
public:
    /**
     * @brief 获取或创建连接池
     * @param host 后端主机地址
     * @param port 后端端口号
     * @param config 连接池配置
     * @return 连接池引用
     */
    ConnectionPool* get_pool(const std::string& host, int port,
                             const ConnectionPoolConfig& config = {});

    /**
     * @brief 移除连接池
     * @param host 后端主机地址
     * @param port 后端端口号
     */
    void remove_pool(const std::string& host, int port);

    /**
     * @brief 清理所有空闲连接
     */
    void cleanup_all();

    /**
     * @brief 清空所有连接池
     */
    void clear_all();

private:
    std::string make_key(const std::string& host, int port) const;

    mutable std::mutex mutex_;
    std::unordered_map<std::string, std::unique_ptr<ConnectionPool>> pools_;
};

} // namespace ha_server
