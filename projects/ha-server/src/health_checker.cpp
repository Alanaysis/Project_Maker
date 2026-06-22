/**
 * @file health_checker.cpp
 * @brief 健康检查器实现
 *
 * 实现后端服务器的主动健康检查。
 * 使用 TCP 连接检测后端是否可用。
 *
 * ⭐ 重点：健康检查是高可用的核心机制
 * 💡 思考：如何避免网络抖动导致的误判？
 */

#include "../include/health_checker.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <cstring>

namespace ha_server {

HealthChecker::HealthChecker(std::vector<Backend*>& backends,
                             const HealthCheckConfig& config)
    : backends_(backends)
    , config_(config) {
}

HealthChecker::~HealthChecker() {
    stop();
}

void HealthChecker::start() {
    if (running_.load()) {
        return;
    }

    running_.store(true);
    check_thread_ = std::thread(&HealthChecker::check_loop, this);

    log_message(LogLevel::INFO, "Health checker started, interval=" +
                std::to_string(config_.interval.count()) + "ms");
}

void HealthChecker::stop() {
    if (!running_.load()) {
        return;
    }

    running_.store(false);
    if (check_thread_.joinable()) {
        check_thread_.join();
    }

    log_message(LogLevel::INFO, "Health checker stopped");
}

void HealthChecker::set_interval(std::chrono::milliseconds interval) {
    config_.interval = interval;
}

void HealthChecker::set_timeout(std::chrono::milliseconds timeout) {
    config_.timeout = timeout;
}

void HealthChecker::set_failure_threshold(int threshold) {
    config_.failure_threshold = threshold;
}

/**
 * 健康检查主循环
 *
 * 定期遍历所有后端，执行健康检查。
 * 根据检查结果更新后端状态。
 *
 * ⭐ 重点：
 * - 使用 sleep 实现定时检查
 * - 检查过程中不阻塞其他操作
 * - 使用引用访问后端列表
 */
void HealthChecker::check_loop() {
    while (running_.load()) {
        // 遍历所有后端执行检查
        for (auto* backend : backends_) {
            if (!running_.load()) {
                break;
            }

            bool healthy = check_backend(*backend);
            total_checks_.fetch_add(1);

            if (!healthy) {
                failed_checks_.fetch_add(1);
            }
        }

        // 等待下一次检查
        // 使用小间隔睡眠，以便快速响应停止信号
        auto sleep_end = std::chrono::steady_clock::now() + config_.interval;
        while (running_.load() && std::chrono::steady_clock::now() < sleep_end) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
}

/**
 * 检查单个后端的健康状态
 *
 * 尝试建立 TCP 连接，根据结果更新后端状态。
 * 使用连续失败阈值避免误判。
 *
 * ⭐ 重点：
 * - 连续失败阈值避免网络抖动导致的误判
 * - 连续成功阈值用于快速恢复
 * - 更新最后检查时间
 *
 * 💡 思考：
 * - TCP 检查 vs HTTP 检查各有什么优缺点？
 * - 如何检查后端的应用层健康状态？
 */
bool HealthChecker::check_backend(Backend& backend) {
    // 执行 TCP 检查
    bool healthy = tcp_check(backend.host, backend.port, config_.timeout);

    // 更新最后检查时间
    backend.last_check_time = std::chrono::steady_clock::now();

    if (healthy) {
        // 检查成功
        if (backend.status != BackendStatus::Healthy) {
            backend.consecutive_successes++;
            // 达到成功阈值，标记为健康
            if (backend.consecutive_successes >= config_.success_threshold) {
                backend.mark_healthy();
                log_message(LogLevel::INFO, "Backend " + backend.address() +
                           " is now HEALTHY");
            }
        } else {
            backend.consecutive_successes++;
        }
        backend.consecutive_failures = 0;
    } else {
        // 检查失败
        backend.consecutive_failures++;
        backend.consecutive_successes = 0;

        // 达到失败阈值，标记为不健康
        if (backend.consecutive_failures >= config_.failure_threshold) {
            if (backend.status != BackendStatus::Unhealthy) {
                backend.mark_unhealthy();
                log_message(LogLevel::WARNING, "Backend " + backend.address() +
                           " is now UNHEALTHY (consecutive failures: " +
                           std::to_string(backend.consecutive_failures) + ")");
            }
        }
    }

    return healthy;
}

/**
 * TCP 健康检查
 *
 * 尝试建立 TCP 连接到后端服务器。
 * 如果连接成功，说明后端可用。
 *
 * 实现步骤：
 * 1. 创建 socket
 * 2. 设置非阻塞模式
 * 3. 发起连接
 * 4. 使用 poll 等待连接完成
 * 5. 检查连接结果
 * 6. 关闭 socket
 *
 * ⭐ 重点：
 * - 非阻塞连接 + poll 实现超时控制
 * - 正确处理 EINPROGRESS 错误
 * - 及时关闭 socket 避免资源泄漏
 */
bool HealthChecker::tcp_check(const std::string& host, int port,
                               std::chrono::milliseconds timeout) {
    // 创建 socket
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        return false;
    }

    // 设置非阻塞模式
    int flags = fcntl(fd, F_GETFL, 0);
    fcntl(fd, F_SETFL, flags | O_NONBLOCK);

    // 构建地址
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    inet_pton(AF_INET, host.c_str(), &addr.sin_addr);

    // 发起非阻塞连接
    int ret = connect(fd, (struct sockaddr*)&addr, sizeof(addr));
    if (ret == 0) {
        // 连接立即成功
        close(fd);
        return true;
    }

    if (errno != EINPROGRESS) {
        // 连接立即失败
        close(fd);
        return false;
    }

    // 等待连接完成
    struct pollfd pfd;
    pfd.fd = fd;
    pfd.events = POLLOUT;

    ret = poll(&pfd, 1, timeout.count());
    if (ret <= 0) {
        // 超时或错误
        close(fd);
        return false;
    }

    // 检查连接结果
    int error = 0;
    socklen_t len = sizeof(error);
    getsockopt(fd, SOL_SOCKET, SO_ERROR, &error, &len);

    close(fd);
    return error == 0;
}

} // namespace ha_server
