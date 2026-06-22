#pragma once

/**
 * @file health_checker.h
 * @brief 健康检查器
 *
 * 实现后端服务器的健康检查机制。
 * 支持主动检查（定期探测）和被动检查（请求失败触发）。
 *
 * ⭐ 重点：健康检查是高可用的核心机制
 * 💡 思考：主动检查 vs 被动检查各有什么优缺点？
 */

#include "backend.h"
#include <thread>
#include <atomic>
#include <chrono>
#include <functional>

namespace ha_server {

/**
 * @brief 健康检查配置
 */
struct HealthCheckConfig {
    bool enabled = true;                                         // 是否启用
    std::chrono::milliseconds interval{DEFAULT_CHECK_INTERVAL_MS}; // 检查间隔
    std::chrono::milliseconds timeout{DEFAULT_TIMEOUT_MS};         // 超时时间
    int failure_threshold = DEFAULT_FAILURE_THRESHOLD;               // 失败阈值
    int success_threshold = 1;                                       // 成功阈值
};

/**
 * @brief 健康检查器
 *
 * 定期检查后端服务器的健康状态。
 * 当连续失败次数达到阈值时，标记后端为不健康。
 * 当后端恢复健康时，自动重新加入负载均衡。
 *
 * 工作流程：
 * 1. 启动检查线程
 * 2. 定时遍历所有后端
 * 3. 对每个后端执行健康检查
 * 4. 根据结果更新后端状态
 *
 * ⭐ 重点：如何避免网络抖动导致的误判？
 * 解决方案：使用连续失败阈值，而不是单次失败就标记为不健康
 *
 * 💡 思考：检查间隔设多少合适？
 * - 太短：增加网络开销
 * - 太长：故障检测延迟
 * - 建议：根据业务需求和网络环境调整
 */
class HealthChecker {
public:
    /**
     * @brief 构造函数
     * @param backends 后端列表引用
     * @param config 健康检查配置
     */
    HealthChecker(std::vector<Backend*>& backends, const HealthCheckConfig& config = {});

    /**
     * @brief 析构函数
     *
     * 自动停止检查线程
     */
    ~HealthChecker();

    /**
     * @brief 启动健康检查
     *
     * 创建并启动检查线程
     */
    void start();

    /**
     * @brief 停止健康检查
     *
     * 停止检查线程并等待其结束
     */
    void stop();

    /**
     * @brief 检查是否正在运行
     * @return 运行中返回 true
     */
    bool is_running() const { return running_.load(); }

    /**
     * @brief 设置检查间隔
     * @param interval 检查间隔
     */
    void set_interval(std::chrono::milliseconds interval);

    /**
     * @brief 设置超时时间
     * @param timeout 超时时间
     */
    void set_timeout(std::chrono::milliseconds timeout);

    /**
     * @brief 设置失败阈值
     * @param threshold 连续失败次数阈值
     */
    void set_failure_threshold(int threshold);

    /**
     * @brief 获取检查统计
     */
    uint64_t get_total_checks() const { return total_checks_.load(); }
    uint64_t get_failed_checks() const { return failed_checks_.load(); }

private:
    /**
     * @brief 检查线程主函数
     */
    void check_loop();

    /**
     * @brief 检查单个后端
     * @param backend 后端引用
     * @return 健康返回 true
     */
    bool check_backend(Backend& backend);

    /**
     * @brief TCP 健康检查
     * @param host 主机地址
     * @param port 端口号
     * @param timeout 超时时间
     * @return 连接成功返回 true
     */
    bool tcp_check(const std::string& host, int port,
                   std::chrono::milliseconds timeout);

    std::vector<Backend*>& backends_;
    HealthCheckConfig config_;
    std::thread check_thread_;
    std::atomic<bool> running_{false};
    std::atomic<uint64_t> total_checks_{0};
    std::atomic<uint64_t> failed_checks_{0};
};

} // namespace ha_server
