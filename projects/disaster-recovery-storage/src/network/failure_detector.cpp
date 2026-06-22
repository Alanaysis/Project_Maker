#include "network/failure_detector.h"
#include <algorithm>
#include <cmath>

namespace disaster_recovery {
namespace network {

FailureDetector::FailureDetector(int heartbeat_interval_ms,
                                 int heartbeat_timeout_ms,
                                 int suspect_timeout_ms)
    : heartbeat_interval_ms_(heartbeat_interval_ms),
      heartbeat_timeout_ms_(heartbeat_timeout_ms),
      suspect_timeout_ms_(suspect_timeout_ms),
      running_(false) {
}

FailureDetector::~FailureDetector() {
    stop();
}

void FailureDetector::start() {
    if (running_) {
        return;
    }

    running_ = true;
    detection_thread_ = std::thread(&FailureDetector::detectionLoop, this);
}

void FailureDetector::stop() {
    if (!running_) {
        return;
    }

    running_ = false;
    if (detection_thread_.joinable()) {
        detection_thread_.join();
    }
}

void FailureDetector::registerNode(const NodeId& node_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    NodeMonitorInfo info;
    info.id = node_id;
    info.status = NodeStatus::ONLINE;
    info.last_heartbeat = std::chrono::system_clock::now();
    info.last_response = std::chrono::system_clock::now();
    info.missed_heartbeats = 0;
    info.is_suspected = false;

    nodes_[node_id] = info;
}

void FailureDetector::removeNode(const NodeId& node_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    nodes_.erase(node_id);
}

void FailureDetector::reportHeartbeat(const NodeId& node_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = nodes_.find(node_id);
    if (it != nodes_.end()) {
        auto now = std::chrono::system_clock::now();
        it->second.last_heartbeat = now;
        it->second.last_response = now;
        it->second.missed_heartbeats = 0;
        it->second.is_suspected = false;

        // 如果之前是离线状态，触发恢复回调
        if (it->second.status == NodeStatus::OFFLINE ||
            it->second.status == NodeStatus::SUSPECTED) {
            it->second.status = NodeStatus::ONLINE;
            if (recovery_callback_) {
                recovery_callback_(node_id);
            }
        }
    }
}

NodeStatus FailureDetector::getNodeStatus(const NodeId& node_id) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = nodes_.find(node_id);
    if (it != nodes_.end()) {
        return it->second.status;
    }
    return NodeStatus::OFFLINE;
}

std::vector<NodeId> FailureDetector::getOnlineNodes() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<NodeId> result;
    for (const auto& pair : nodes_) {
        if (pair.second.status == NodeStatus::ONLINE) {
            result.push_back(pair.first);
        }
    }
    return result;
}

std::vector<NodeId> FailureDetector::getOfflineNodes() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<NodeId> result;
    for (const auto& pair : nodes_) {
        if (pair.second.status == NodeStatus::OFFLINE) {
            result.push_back(pair.first);
        }
    }
    return result;
}

std::vector<NodeId> FailureDetector::getSuspectedNodes() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<NodeId> result;
    for (const auto& pair : nodes_) {
        if (pair.second.status == NodeStatus::SUSPECTED) {
            result.push_back(pair.first);
        }
    }
    return result;
}

bool FailureDetector::isNodeOnline(const NodeId& node_id) const {
    return getNodeStatus(node_id) == NodeStatus::ONLINE;
}

NodeMonitorInfo FailureDetector::getNodeInfo(const NodeId& node_id) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = nodes_.find(node_id);
    if (it != nodes_.end()) {
        return it->second;
    }

    // 返回默认值
    NodeMonitorInfo info;
    info.id = node_id;
    info.status = NodeStatus::OFFLINE;
    info.missed_heartbeats = 0;
    info.is_suspected = false;
    return info;
}

std::vector<NodeMonitorInfo> FailureDetector::getAllNodeInfo() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<NodeMonitorInfo> result;
    for (const auto& pair : nodes_) {
        result.push_back(pair.second);
    }
    return result;
}

void FailureDetector::setFailureCallback(
    std::function<void(const NodeId&)> callback) {
    failure_callback_ = callback;
}

void FailureDetector::setRecoveryCallback(
    std::function<void(const NodeId&)> callback) {
    recovery_callback_ = callback;
}

void FailureDetector::detectionLoop() {
    while (running_) {
        checkTimeouts();
        std::this_thread::sleep_for(
            std::chrono::milliseconds(heartbeat_interval_ms_));
    }
}

void FailureDetector::checkTimeouts() {
    std::lock_guard<std::mutex> lock(mutex_);

    auto now = std::chrono::system_clock::now();

    for (auto& pair : nodes_) {
        updateNodeStatus(pair.second, now);
    }
}

void FailureDetector::updateNodeStatus(
    NodeMonitorInfo& node,
    const std::chrono::system_clock::time_point& now) {
    // 计算自上次心跳以来的时间
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        now - node.last_heartbeat);
    auto elapsed_ms = duration.count();

    // 检查是否超过怀疑超时
    if (elapsed_ms > suspect_timeout_ms_) {
        // 标记为离线
        if (node.status != NodeStatus::OFFLINE) {
            node.status = NodeStatus::OFFLINE;
            node.is_suspected = false;
            if (failure_callback_) {
                failure_callback_(node.id);
            }
        }
    }
    // 检查是否超过心跳超时
    else if (elapsed_ms > heartbeat_timeout_ms_) {
        // 标记为疑似故障
        if (node.status != NodeStatus::SUSPECTED) {
            node.status = NodeStatus::SUSPECTED;
            node.is_suspected = true;
        }
        node.missed_heartbeats++;
    }
    // 检查是否超过心跳间隔
    else if (elapsed_ms > heartbeat_interval_ms_) {
        // 增加丢失心跳计数
        node.missed_heartbeats++;
    }
}

double FailureDetector::calculatePhi(
    const NodeMonitorInfo& node,
    const std::chrono::system_clock::time_point& now) const {
    // Phi Accrual Failure Detector
    // phi = -log10(1 - CDF(current_interval))
    // 这里简化实现，使用指数分布

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        now - node.last_heartbeat);
    auto elapsed_ms = duration.count();

    // 使用指数分布的CDF
    // lambda = 1 / mean_interval
    double mean_interval = heartbeat_interval_ms_;
    double lambda = 1.0 / mean_interval;
    double cdf = 1.0 - std::exp(-lambda * elapsed_ms);

    // 计算phi值
    if (cdf >= 1.0) {
        return 100.0;  // 极大值
    }

    double phi = -std::log10(1.0 - cdf);
    return phi;
}

}  // namespace network
}  // namespace disaster_recovery
