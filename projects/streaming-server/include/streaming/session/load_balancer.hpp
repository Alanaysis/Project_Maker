#pragma once

/**
 * @file load_balancer.hpp
 * @brief 负载均衡器
 *
 * 实现流媒体服务器的负载均衡，支持：
 * - 多种负载均衡算法
 * - 健康检查
 * - 动态权重调整
 * - 集群管理
 */

#include "streaming/types.hpp"
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>
#include <functional>
#include <chrono>

namespace streaming {

// 负载均衡算法
enum class LoadBalanceAlgorithm {
    RoundRobin,         // 轮询
    LeastConnections,   // 最少连接
    WeightedRoundRobin, // 加权轮询
    Random,             // 随机
    ConsistentHash,     // 一致性哈希
    LeastResponseTime   // 最少响应时间
};

// 节点状态
enum class NodeState {
    Healthy,
    Unhealthy,
    Draining,
    Unknown
};

// 集群节点信息
struct ClusterNode {
    std::string node_id;
    std::string host;
    uint16_t port = 0;
    NodeState state = NodeState::Unknown;
    uint32_t weight = 1;
    uint32_t current_connections = 0;
    uint32_t max_connections = 1000;
    double cpu_usage = 0.0;
    double memory_usage = 0.0;
    double bandwidth_usage = 0.0;
    double response_time = 0.0;
    Timestamp last_heartbeat;
    Timestamp last_check;

    // 统计
    uint64_t total_requests = 0;
    uint64_t total_errors = 0;
    uint64_t bytes_transferred = 0;
};

using ClusterNodePtr = std::shared_ptr<ClusterNode>;

/**
 * @brief 一致性哈希
 */
class ConsistentHash {
public:
    ConsistentHash(uint32_t virtual_nodes = 150);
    ~ConsistentHash();

    /**
     * @brief 添加节点
     * @param node_id 节点ID
     * @param weight 权重
     */
    void add_node(const std::string& node_id, uint32_t weight = 1);

    /**
     * @brief 移除节点
     * @param node_id 节点ID
     */
    void remove_node(const std::string& node_id);

    /**
     * @brief 获取节点
     * @param key 键
     * @return 节点ID
     */
    std::string get_node(const std::string& key) const;

    /**
     * @brief 获取多个节点
     * @param key 键
     * @param count 节点数量
     * @return 节点ID列表
     */
    std::vector<std::string> get_nodes(const std::string& key, uint32_t count) const;

private:
    uint32_t hash(const std::string& key) const;

    uint32_t virtual_nodes_;
    std::map<uint32_t, std::string> ring_;
    mutable std::mutex mutex_;
};

/**
 * @brief 健康检查器
 */
class HealthChecker {
public:
    HealthChecker();
    ~HealthChecker();

    /**
     * @brief 设置检查间隔
     * @param interval 检查间隔
     */
    void set_check_interval(std::chrono::seconds interval) { check_interval_ = interval; }

    /**
     * @brief 设置超时时间
     * @param timeout 超时时间
     */
    void set_timeout(std::chrono::seconds timeout) { timeout_ = timeout; }

    /**
     * @brief 添加检查项
     * @param node 节点
     */
    void add_check(ClusterNodePtr node);

    /**
     * @brief 移除检查项
     * @param node_id 节点ID
     */
    void remove_check(const std::string& node_id);

    /**
     * @brief 执行健康检查
     * @param node 节点
     * @return 是否健康
     */
    bool check(ClusterNodePtr node);

    /**
     * @brief 启动定期检查
     */
    void start();

    /**
     * @brief 停止定期检查
     */
    void stop();

    /**
     * @brief 设置状态回调
     */
    using StatusCallback = std::function<void(const std::string&, NodeState)>;
    void set_status_callback(StatusCallback callback) { status_callback_ = std::move(callback); }

private:
    void check_loop();
    bool check_tcp(const std::string& host, uint16_t port);
    bool check_http(const std::string& url);

    std::chrono::seconds check_interval_{10};
    std::chrono::seconds timeout_{5};

    std::unordered_map<std::string, ClusterNodePtr> nodes_;
    mutable std::mutex mutex_;

    std::thread check_thread_;
    std::atomic<bool> running_{false};

    StatusCallback status_callback_;
};

/**
 * @brief 负载均衡器
 */
class LoadBalancer {
public:
    LoadBalancer();
    ~LoadBalancer();

    /**
     * @brief 初始化负载均衡器
     * @param algorithm 负载均衡算法
     */
    bool initialize(LoadBalanceAlgorithm algorithm = LoadBalanceAlgorithm::RoundRobin);

    /**
     * @brief 添加节点
     */
    void add_node(ClusterNodePtr node);

    /**
     * @brief 移除节点
     */
    void remove_node(const std::string& node_id);

    /**
     * @brief 选择节点
     * @param key 用于一致性哈希的键
     * @return 选择的节点
     */
    ClusterNodePtr select_node(const std::string& key = "");

    /**
     * @brief 获取所有节点
     */
    std::vector<ClusterNodePtr> get_all_nodes() const;

    /**
     * @brief 获取健康节点
     */
    std::vector<ClusterNodePtr> get_healthy_nodes() const;

    /**
     * @brief 更新节点状态
     */
    void update_node_state(const std::string& node_id, NodeState state);

    /**
     * @brief 更新节点统计
     */
    void update_node_stats(const std::string& node_id,
                          uint32_t connections,
                          double cpu,
                          double memory,
                          double bandwidth,
                          double response_time);

    /**
     * @brief 启动健康检查
     */
    void start_health_check();

    /**
     * @brief 停止健康检查
     */
    void stop_health_check();

    /**
     * @brief 获取负载均衡算法
     */
    LoadBalanceAlgorithm get_algorithm() const { return algorithm_; }

private:
    ClusterNodePtr select_round_robin();
    ClusterNodePtr select_least_connections();
    ClusterNodePtr select_weighted_round_robin();
    ClusterNodePtr select_random();
    ClusterNodePtr select_consistent_hash(const std::string& key);
    ClusterNodePtr select_least_response_time();

    LoadBalanceAlgorithm algorithm_;
    std::vector<ClusterNodePtr> nodes_;
    mutable std::mutex nodes_mutex_;

    // 轮询索引
    uint32_t round_robin_index_ = 0;
    uint32_t weighted_round_robin_index_ = 0;

    // 一致性哈希
    std::unique_ptr<ConsistentHash> consistent_hash_;

    // 健康检查
    std::unique_ptr<HealthChecker> health_checker_;
};

/**
 * @brief 集群管理器
 *
 * 管理流媒体服务器集群。
 */
class ClusterManager {
public:
    ClusterManager();
    ~ClusterManager();

    /**
     * @brief 初始化集群管理器
     * @param node_id 当前节点ID
     */
    bool initialize(const std::string& node_id);

    /**
     * @brief 添加集群节点
     */
    void add_node(ClusterNodePtr node);

    /**
     * @brief 移除集群节点
     */
    void remove_node(const std::string& node_id);

    /**
     * @brief 获取当前节点
     */
    ClusterNodePtr get_current_node() const { return current_node_; }

    /**
     * @brief 获取所有节点
     */
    std::vector<ClusterNodePtr> get_all_nodes() const;

    /**
     * @brief 更新当前节点状态
     */
    void update_current_node_stats(const ServerStats& stats);

    /**
     * @brief 广播消息到其他节点
     */
    void broadcast(const std::string& message);

    /**
     * @brief 发送消息到指定节点
     */
    bool send_to_node(const std::string& node_id, const std::string& message);

    /**
     * @brief 启动集群服务
     */
    void start();

    /**
     * @brief 停止集群服务
     */
    void stop();

    /**
     * @brief 设置消息回调
     */
    using MessageCallback = std::function<void(const std::string&, const std::string&)>;
    void set_message_callback(MessageCallback callback) { message_callback_ = std::move(callback); }

private:
    void heartbeat_loop();
    void sync_loop();

    std::string node_id_;
    ClusterNodePtr current_node_;
    std::vector<ClusterNodePtr> nodes_;
    mutable std::mutex nodes_mutex_;

    std::thread heartbeat_thread_;
    std::thread sync_thread_;
    std::atomic<bool> running_{false};

    MessageCallback message_callback_;
};

} // namespace streaming
