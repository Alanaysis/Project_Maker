#pragma once

/**
 * @file common.h
 * @brief 公共定义和工具函数
 *
 * 包含项目中常用的类型定义、常量和工具函数。
 */

#include <string>
#include <vector>
#include <chrono>
#include <cstdint>
#include <memory>
#include <atomic>
#include <mutex>
#include <functional>
#include <iostream>
#include <cstring>
#include <algorithm>

// 网络相关头文件
#include <sys/socket.h>
#include <sys/epoll.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>

namespace ha_server {

// 常量定义
constexpr int MAX_EVENTS = 1024;           // epoll 最大事件数
constexpr int MAX_CONNECTIONS = 10000;     // 最大连接数
constexpr int DEFAULT_PORT = 8080;         // 默认端口
constexpr int DEFAULT_WORKER_THREADS = 4;  // 默认工作线程数
constexpr int DEFAULT_POOL_SIZE = 100;     // 默认连接池大小
constexpr int DEFAULT_CHECK_INTERVAL_MS = 5000;  // 默认健康检查间隔
constexpr int DEFAULT_TIMEOUT_MS = 3000;          // 默认超时时间
constexpr int DEFAULT_FAILURE_THRESHOLD = 3;      // 默认失败阈值

/**
 * @brief 日志级别
 */
enum class LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR
};

/**
 * @brief 后端服务器状态
 */
enum class BackendStatus {
    Unknown,    // 未知状态
    Healthy,    // 健康
    Unhealthy   // 不健康
};

/**
 * @brief 负载均衡算法类型
 */
enum class BalancerType {
    RoundRobin,          // 轮询
    WeightedRoundRobin,  // 加权轮询
    LeastConnections     // 最少连接
};

/**
 * @brief 服务器统计信息
 */
struct ServerStats {
    std::atomic<uint64_t> total_requests{0};
    std::atomic<uint64_t> successful_requests{0};
    std::atomic<uint64_t> failed_requests{0};
    std::atomic<uint64_t> active_connections{0};
    std::atomic<uint64_t> total_connections{0};

    ServerStats() = default;
    ServerStats(const ServerStats& other)
        : total_requests(other.total_requests.load())
        , successful_requests(other.successful_requests.load())
        , failed_requests(other.failed_requests.load())
        , active_connections(other.active_connections.load())
        , total_connections(other.total_connections.load())
    {}

    ServerStats& operator=(const ServerStats& other) {
        total_requests.store(other.total_requests.load());
        successful_requests.store(other.successful_requests.load());
        failed_requests.store(other.failed_requests.load());
        active_connections.store(other.active_connections.load());
        total_connections.store(other.total_connections.load());
        return *this;
    }
};

/**
 * @brief 设置 socket 为非阻塞模式
 * @param fd socket 文件描述符
 * @return 成功返回 0，失败返回 -1
 */
inline int set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) {
        return -1;
    }
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

/**
 * @brief 设置 socket 选项：允许地址重用
 * @param fd socket 文件描述符
 * @return 成功返回 0，失败返回 -1
 */
inline int set_reuse_addr(int fd) {
    int opt = 1;
    return setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
}

/**
 * @brief 获取当前时间戳（毫秒）
 * @return 当前时间戳
 */
inline int64_t now_ms() {
    auto now = std::chrono::steady_clock::now();
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()
    ).count();
}

/**
 * @brief 简单的日志输出函数
 * @param level 日志级别
 * @param message 日志消息
 */
inline void log_message(LogLevel level, const std::string& message) {
    const char* level_str = "";
    switch (level) {
        case LogLevel::DEBUG:   level_str = "[DEBUG]"; break;
        case LogLevel::INFO:    level_str = "[INFO]"; break;
        case LogLevel::WARNING: level_str = "[WARN]"; break;
        case LogLevel::ERROR:   level_str = "[ERROR]"; break;
    }

    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);

    std::cerr << level_str << " " << message << std::endl;
}

} // namespace ha_server
