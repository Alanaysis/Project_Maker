#ifndef DISASTER_RECOVERY_STORAGE_NETWORK_FAILURE_DETECTOR_H_
#define DISASTER_RECOVERY_STORAGE_NETWORK_FAILURE_DETECTOR_H_

#include <string>
#include <unordered_map>
#include <vector>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include "storage/types.h"

namespace disaster_recovery {
namespace network {

/**
 * @brief 节点信息（故障检测用）
 */
struct NodeMonitorInfo {
    NodeId id;                          // 节点ID
    NodeStatus status;                  // 节点状态
    std::chrono::system_clock::time_point last_heartbeat;  // 最后心跳时间
    std::chrono::system_clock::time_point last_response;   // 最后响应时间
    int missed_heartbeats;              // 连续丢失心跳数
    bool is_suspected;                  // 是否被怀疑故障
};

/**
 * @brief 故障检测器
 *
 * 使用心跳机制检测节点故障
 *
 * @note 实现简单的超时检测和Phi Accrual Failure Detector
 */
class FailureDetector {
public:
    /**
     * @brief 构造函数
     *
     * @param heartbeat_interval_ms 心跳间隔（毫秒）
     * @param heartbeat_timeout_ms 心跳超时（毫秒）
     * @param suspect_timeout_ms 怀疑超时（毫秒）
     */
    FailureDetector(int heartbeat_interval_ms = 5000,
                    int heartbeat_timeout_ms = 15000,
                    int suspect_timeout_ms = 30000);

    /**
     * @brief 析构函数
     */
    ~FailureDetector();

    /**
     * @brief 启动故障检测
     */
    void start();

    /**
     * @brief 停止故障检测
     */
    void stop();

    /**
     * @brief 注册节点
     *
     * @param node_id 节点ID
     */
    void registerNode(const NodeId& node_id);

    /**
     * @brief 移除节点
     *
     * @param node_id 节点ID
     */
    void removeNode(const NodeId& node_id);

    /**
     * @brief 报告心跳
     *
     * @param node_id 节点ID
     */
    void reportHeartbeat(const NodeId& node_id);

    /**
     * @brief 获取节点状态
     *
     * @param node_id 节点ID
     * @return 节点状态
     */
    NodeStatus getNodeStatus(const NodeId& node_id) const;

    /**
     * @brief 获取所有在线节点
     *
     * @return 在线节点ID列表
     */
    std::vector<NodeId> getOnlineNodes() const;

    /**
     * @brief 获取所有离线节点
     *
     * @return 离线节点ID列表
     */
    std::vector<NodeId> getOfflineNodes() const;

    /**
     * @brief 获取所有疑似故障节点
     *
     * @return 疑似故障节点ID列表
     */
    std::vector<NodeId> getSuspectedNodes() const;

    /**
     * @brief 检查节点是否在线
     *
     * @param node_id 节点ID
     * @return true 如果在线，false 否则
     */
    bool isNodeOnline(const NodeId& node_id) const;

    /**
     * @brief 获取节点监控信息
     *
     * @param node_id 节点ID
     * @return 节点监控信息
     */
    NodeMonitorInfo getNodeInfo(const NodeId& node_id) const;

    /**
     * @brief 获取所有节点监控信息
     *
     * @return 节点监控信息列表
     */
    std::vector<NodeMonitorInfo> getAllNodeInfo() const;

    /**
     * @brief 设置故障回调
     *
     * @param callback 回调函数
     */
    void setFailureCallback(std::function<void(const NodeId&)> callback);

    /**
     * @brief 设置恢复回调
     *
     * @param callback 回调函数
     */
    void setRecoveryCallback(std::function<void(const NodeId&)> callback);

    /**
     * @brief 获取心跳间隔
     *
     * @return 心跳间隔（毫秒）
     */
    int getHeartbeatInterval() const { return heartbeat_interval_ms_; }

    /**
     * @brief 获取心跳超时
     *
     * @return 心跳超时（毫秒）
     */
    int getHeartbeatTimeout() const { return heartbeat_timeout_ms_; }

    /**
     * @brief 获取怀疑超时
     *
     * @return 怀疑超时（毫秒）
     */
    int getSuspectTimeout() const { return suspect_timeout_ms_; }

private:
    int heartbeat_interval_ms_;  // 心跳间隔
    int heartbeat_timeout_ms_;   // 心跳超时
    int suspect_timeout_ms_;     // 怀疑超时

    // 节点监控信息
    mutable std::mutex mutex_;
    std::unordered_map<NodeId, NodeMonitorInfo> nodes_;

    // 检测线程
    std::thread detection_thread_;
    std::atomic<bool> running_;

    // 回调函数
    std::function<void(const NodeId&)> failure_callback_;
    std::function<void(const NodeId&)> recovery_callback_;

    /**
     * @brief 检测线程主循环
     */
    void detectionLoop();

    /**
     * @brief 检查超时
     */
    void checkTimeouts();

    /**
     * @brief 更新节点状态
     *
     * @param node 节点信息
     * @param now 当前时间
     */
    void updateNodeStatus(NodeMonitorInfo& node,
                          const std::chrono::system_clock::time_point& now);

    /**
     * @brief 计算Phi值
     *
     * Phi Accrual Failure Detector的Phi值计算
     *
     * @param node 节点信息
     * @param now 当前时间
     * @return Phi值
     */
    double calculatePhi(const NodeMonitorInfo& node,
                        const std::chrono::system_clock::time_point& now) const;
};

}  // namespace network
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_NETWORK_FAILURE_DETECTOR_H_
