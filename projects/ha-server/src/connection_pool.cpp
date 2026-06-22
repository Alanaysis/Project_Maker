/**
 * @file connection_pool.cpp
 * @brief 连接池实现
 *
 * 实现到后端服务器的连接池管理。
 * 支持连接复用、超时回收、连接健康检查。
 *
 * ⭐ 重点：连接池是性能优化的关键
 * 💡 思考：连接池大小如何确定？（Little's Law: L = λW）
 */

#include "../include/connection_pool.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <algorithm>

namespace ha_server {

// ============================================================================
// ConnectionPool 实现
// ============================================================================

ConnectionPool::ConnectionPool(const std::string& host, int port,
                               const ConnectionPoolConfig& config)
    : host_(host)
    , port_(port)
    , config_(config) {
    log_message(LogLevel::INFO, "Connection pool created for " +
                host + ":" + std::to_string(port) +
                " max_size=" + std::to_string(config.max_size));
}

ConnectionPool::~ConnectionPool() {
    clear();
}

/**
 * 获取连接
 *
 * 优先复用空闲连接，没有空闲连接时创建新连接。
 *
 * ⭐ 重点：
 * - 线程安全：使用 mutex 保护
 * - 连接复用：减少握手开销
 * - 池满处理：返回 -1
 *
 * 💡 思考：
 * - 池满时应该等待还是直接失败？
 * - 如何实现等待机制？
 */
int ConnectionPool::acquire() {
    std::lock_guard<std::mutex> lock(mutex_);

    auto now = std::chrono::steady_clock::now();

    // 查找空闲连接
    for (auto& conn : connections_) {
        if (!conn.in_use && conn.valid) {
            // 检查连接是否超时
            auto idle_time = std::chrono::duration_cast<std::chrono::milliseconds>(
                now - conn.last_used_time);

            if (idle_time < config_.idle_timeout) {
                // 连接可用，复用
                conn.in_use = true;
                conn.last_used_time = now;
                return conn.fd;
            } else {
                // 连接超时，关闭并移除
                close_connection(conn.fd);
                conn.valid = false;
            }
        }
    }

    // 移除无效连接
    connections_.erase(
        std::remove_if(connections_.begin(), connections_.end(),
            [](const Connection& c) { return !c.valid; }),
        connections_.end());

    // 池未满，创建新连接
    if (connections_.size() < config_.max_size) {
        int fd = create_connection();
        if (fd >= 0) {
            Connection conn;
            conn.fd = fd;
            conn.created_time = now;
            conn.last_used_time = now;
            conn.in_use = true;
            conn.valid = true;
            connections_.push_back(conn);
            return fd;
        }
    }

    return -1;  // 池满或创建失败
}

/**
 * 释放连接
 *
 * 将连接标记为空闲，可供其他请求复用。
 *
 * ⭐ 重点：
 * - 只是标记为空闲，不关闭连接
 * - 更新最后使用时间
 */
void ConnectionPool::release(int fd) {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& conn : connections_) {
        if (conn.fd == fd && conn.valid) {
            conn.in_use = false;
            conn.last_used_time = std::chrono::steady_clock::now();
            return;
        }
    }
}

/**
 * 移除连接
 *
 * 关闭并移除连接，通常在连接出错时调用。
 */
void ConnectionPool::remove(int fd) {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& conn : connections_) {
        if (conn.fd == fd) {
            close_connection(conn.fd);
            conn.valid = false;
            break;
        }
    }

    // 移除无效连接
    connections_.erase(
        std::remove_if(connections_.begin(), connections_.end(),
            [](const Connection& c) { return !c.valid; }),
        connections_.end());
}

size_t ConnectionPool::size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return connections_.size();
}

size_t ConnectionPool::available() const {
    std::lock_guard<std::mutex> lock(mutex_);

    size_t count = 0;
    for (const auto& conn : connections_) {
        if (!conn.in_use && conn.valid) {
            count++;
        }
    }
    return count;
}

size_t ConnectionPool::in_use_count() const {
    std::lock_guard<std::mutex> lock(mutex_);

    size_t count = 0;
    for (const auto& conn : connections_) {
        if (conn.in_use && conn.valid) {
            count++;
        }
    }
    return count;
}

/**
 * 清理超时连接
 *
 * 移除空闲时间超过 idle_timeout 的连接。
 * 保持至少 min_size 个连接。
 *
 * ⭐ 重点：
 * - 定期清理避免资源泄漏
 * - 保持最小连接数减少冷启动开销
 */
void ConnectionPool::cleanup_idle() {
    std::lock_guard<std::mutex> lock(mutex_);

    auto now = std::chrono::steady_clock::now();
    size_t valid_count = 0;

    for (auto& conn : connections_) {
        if (!conn.valid) {
            continue;
        }

        if (conn.in_use) {
            valid_count++;
            continue;
        }

        // 检查空闲时间
        auto idle_time = std::chrono::duration_cast<std::chrono::milliseconds>(
            now - conn.last_used_time);

        if (idle_time >= config_.idle_timeout && valid_count >= config_.min_size) {
            // 超时且超过最小连接数，关闭
            close_connection(conn.fd);
            conn.valid = false;
        } else {
            valid_count++;
        }
    }

    // 移除无效连接
    connections_.erase(
        std::remove_if(connections_.begin(), connections_.end(),
            [](const Connection& c) { return !c.valid; }),
        connections_.end());
}

void ConnectionPool::clear() {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& conn : connections_) {
        if (conn.valid) {
            close_connection(conn.fd);
        }
    }
    connections_.clear();
}

/**
 * 创建新连接
 *
 * 建立 TCP 连接到后端服务器。
 *
 * ⭐ 重点：
 * - 设置连接超时
 * - 正确处理连接错误
 * - 返回 socket fd
 */
int ConnectionPool::create_connection() {
    // 创建 socket
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        log_message(LogLevel::ERROR, "Failed to create socket: " +
                    std::string(strerror(errno)));
        return -1;
    }

    // 设置连接超时
    struct timeval tv;
    tv.tv_sec = config_.connect_timeout.count() / 1000;
    tv.tv_usec = (config_.connect_timeout.count() % 1000) * 1000;
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    // 构建地址
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port_);
    inet_pton(AF_INET, host_.c_str(), &addr.sin_addr);

    // 连接
    int ret = connect(fd, (struct sockaddr*)&addr, sizeof(addr));
    if (ret < 0) {
        log_message(LogLevel::ERROR, "Failed to connect to " +
                    host_ + ":" + std::to_string(port_) +
                    ": " + strerror(errno));
        close(fd);
        return -1;
    }

    return fd;
}

void ConnectionPool::close_connection(int fd) {
    if (fd >= 0) {
        close(fd);
    }
}

// ============================================================================
// ConnectionPoolManager 实现
// ============================================================================

ConnectionPool* ConnectionPoolManager::get_pool(const std::string& host, int port,
                                                 const ConnectionPoolConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);

    std::string key = make_key(host, port);
    auto it = pools_.find(key);
    if (it != pools_.end()) {
        return it->second.get();
    }

    // 创建新的连接池
    auto pool = std::make_unique<ConnectionPool>(host, port, config);
    ConnectionPool* ptr = pool.get();
    pools_[key] = std::move(pool);
    return ptr;
}

void ConnectionPoolManager::remove_pool(const std::string& host, int port) {
    std::lock_guard<std::mutex> lock(mutex_);

    std::string key = make_key(host, port);
    pools_.erase(key);
}

void ConnectionPoolManager::cleanup_all() {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& pair : pools_) {
        pair.second->cleanup_idle();
    }
}

void ConnectionPoolManager::clear_all() {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& pair : pools_) {
        pair.second->clear();
    }
    pools_.clear();
}

std::string ConnectionPoolManager::make_key(const std::string& host, int port) const {
    return host + ":" + std::to_string(port);
}

} // namespace ha_server
