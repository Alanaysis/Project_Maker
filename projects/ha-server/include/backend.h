#pragma once

/**
 * @file backend.h
 * @brief 后端服务器管理
 *
 * 定义后端服务器的数据结构和管理类。
 * 后端服务器是实际处理请求的上游服务。
 */

#include "common.h"
#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <atomic>

namespace ha_server {

/**
 * @brief 后端服务器信息
 *
 * 包含后端服务器的地址、权重、状态等信息。
 * 这是负载均衡和健康检查的核心数据结构。
 */
struct Backend {
    std::string id;                    // 唯一标识
    std::string host;                  // 主机地址
    int port;                          // 端口号
    int weight;                        // 配置权重（用于加权轮询）
    int current_weight;                // 当前权重（算法运行时使用）
    BackendStatus status;              // 健康状态
    std::atomic<int> active_connections{0};   // 当前活跃连接数
    std::atomic<uint64_t> total_requests{0};  // 总请求数
    std::atomic<uint64_t> failed_requests{0}; // 失败请求数
    int consecutive_failures;          // 连续失败次数
    int consecutive_successes;         // 连续成功次数
    std::chrono::steady_clock::time_point last_check_time;  // 最后检查时间
    std::chrono::steady_clock::time_point last_response_time; // 最后响应时间

    /**
     * @brief 构造函数
     * @param h 主机地址
     * @param p 端口号
     * @param w 权重
     */
    Backend(const std::string& h, int p, int w = 1)
        : host(h)
        , port(p)
        , weight(w)
        , current_weight(0)
        , status(BackendStatus::Unknown)
        , consecutive_failures(0)
        , consecutive_successes(0)
    {
        id = host + ":" + std::to_string(port);
        last_check_time = std::chrono::steady_clock::now();
        last_response_time = std::chrono::steady_clock::now();
    }

    /**
     * @brief 获取地址字符串
     * @return 格式为 "host:port" 的地址
     */
    std::string address() const {
        return host + ":" + std::to_string(port);
    }

    /**
     * @brief 检查是否健康
     * @return 健康返回 true
     */
    bool is_healthy() const {
        return status == BackendStatus::Healthy;
    }

    /**
     * @brief 标记为健康
     */
    void mark_healthy() {
        status = BackendStatus::Healthy;
        consecutive_failures = 0;
        consecutive_successes++;
    }

    /**
     * @brief 标记为不健康
     */
    void mark_unhealthy() {
        status = BackendStatus::Unhealthy;
        consecutive_successes = 0;
        consecutive_failures++;
    }

    /**
     * @brief 增加活跃连接数
     */
    void increment_connections() {
        active_connections.fetch_add(1);
        total_requests.fetch_add(1);
    }

    /**
     * @brief 减少活跃连接数
     */
    void decrement_connections() {
        active_connections.fetch_sub(1);
    }

    /**
     * @brief 增加失败请求数
     */
    void increment_failures() {
        failed_requests.fetch_add(1);
    }

    /**
     * @brief 获取当前活跃连接数
     */
    int get_active_connections() const {
        return active_connections.load();
    }
};

/**
 * @brief 后端服务器管理器
 *
 * 管理所有后端服务器的添加、删除和状态查询。
 * 提供线程安全的后端访问接口。
 */
class BackendManager {
public:
    /**
     * @brief 添加后端服务器
     * @param host 主机地址
     * @param port 端口号
     * @param weight 权重
     * @return 添加的后端指针
     */
    Backend* add_backend(const std::string& host, int port, int weight = 1);

    /**
     * @brief 移除后端服务器
     * @param id 后端 ID
     * @return 成功返回 true
     */
    bool remove_backend(const std::string& id);

    /**
     * @brief 获取所有后端
     * @return 后端列表
     */
    std::vector<Backend*> get_all_backends();

    /**
     * @brief 获取健康的后端列表
     * @return 健康的后端列表
     */
    std::vector<Backend*> get_healthy_backends();

    /**
     * @brief 根据 ID 获取后端
     * @param id 后端 ID
     * @return 后端指针，不存在返回 nullptr
     */
    Backend* get_backend(const std::string& id);

    /**
     * @brief 获取后端数量
     * @return 后端总数
     */
    size_t size() const;

    /**
     * @brief 获取健康后端数量
     * @return 健康后端数量
     */
    size_t healthy_count() const;

private:
    mutable std::mutex mutex_;
    std::vector<std::unique_ptr<Backend>> backends_;
};

} // namespace ha_server
