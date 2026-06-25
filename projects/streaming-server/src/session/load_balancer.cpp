/**
 * @file load_balancer.cpp
 * @brief 负载均衡器实现（简化）
 */

#include "streaming/session/load_balancer.hpp"
#include "streaming/monitor/logger.hpp"

#include <random>
#include <algorithm>

namespace streaming {

// ============================================================================
// LoadBalancer 实现
// ============================================================================

LoadBalancer::LoadBalancer() = default;
LoadBalancer::~LoadBalancer() = default;

bool LoadBalancer::initialize(LoadBalanceAlgorithm algorithm) {
    algorithm_ = algorithm;

    if (algorithm == LoadBalanceAlgorithm::ConsistentHash) {
        consistent_hash_ = std::make_unique<ConsistentHash>();
    }

    health_checker_ = std::make_unique<HealthChecker>();

    LOG_INFO("LoadBalancer initialized");
    return true;
}

void LoadBalancer::add_node(ClusterNodePtr node) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    nodes_.push_back(node);

    if (consistent_hash_) {
        consistent_hash_->add_node(node->node_id, node->weight);
    }

    if (health_checker_) {
        health_checker_->add_check(node);
    }
}

void LoadBalancer::remove_node(const std::string& node_id) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);

    nodes_.erase(
        std::remove_if(nodes_.begin(), nodes_.end(),
                      [&node_id](const ClusterNodePtr& n) {
                          return n->node_id == node_id;
                      }),
        nodes_.end()
    );

    if (consistent_hash_) {
        consistent_hash_->remove_node(node_id);
    }
}

ClusterNodePtr LoadBalancer::select_node(const std::string& key) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);

    if (nodes_.empty()) return nullptr;

    switch (algorithm_) {
        case LoadBalanceAlgorithm::RoundRobin:
            return select_round_robin();
        case LoadBalanceAlgorithm::LeastConnections:
            return select_least_connections();
        case LoadBalanceAlgorithm::WeightedRoundRobin:
            return select_weighted_round_robin();
        case LoadBalanceAlgorithm::Random:
            return select_random();
        case LoadBalanceAlgorithm::ConsistentHash:
            return select_consistent_hash(key);
        case LoadBalanceAlgorithm::LeastResponseTime:
            return select_least_response_time();
        default:
            return select_round_robin();
    }
}

std::vector<ClusterNodePtr> LoadBalancer::get_all_nodes() const {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    return nodes_;
}

std::vector<ClusterNodePtr> LoadBalancer::get_healthy_nodes() const {
    std::lock_guard<std::mutex> lock(nodes_mutex_);

    std::vector<ClusterNodePtr> healthy;
    for (const auto& node : nodes_) {
        if (node->state == NodeState::Healthy) {
            healthy.push_back(node);
        }
    }
    return healthy;
}

void LoadBalancer::update_node_state(const std::string& node_id, NodeState state) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);

    for (auto& node : nodes_) {
        if (node->node_id == node_id) {
            node->state = state;
            break;
        }
    }
}

void LoadBalancer::update_node_stats(const std::string& node_id,
                                     uint32_t connections,
                                     double cpu,
                                     double memory,
                                     double bandwidth,
                                     double response_time) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);

    for (auto& node : nodes_) {
        if (node->node_id == node_id) {
            node->current_connections = connections;
            node->cpu_usage = cpu;
            node->memory_usage = memory;
            node->bandwidth_usage = bandwidth;
            node->response_time = response_time;
            break;
        }
    }
}

void LoadBalancer::start_health_check() {
    if (health_checker_) {
        health_checker_->start();
    }
}

void LoadBalancer::stop_health_check() {
    if (health_checker_) {
        health_checker_->stop();
    }
}

ClusterNodePtr LoadBalancer::select_round_robin() {
    if (nodes_.empty()) return nullptr;

    uint32_t index = round_robin_index_ % nodes_.size();
    round_robin_index_++;
    return nodes_[index];
}

ClusterNodePtr LoadBalancer::select_least_connections() {
    if (nodes_.empty()) return nullptr;

    ClusterNodePtr min_node = nullptr;
    uint32_t min_connections = UINT32_MAX;

    for (const auto& node : nodes_) {
        if (node->state == NodeState::Healthy &&
            node->current_connections < min_connections) {
            min_connections = node->current_connections;
            min_node = node;
        }
    }

    return min_node ? min_node : nodes_[0];
}

ClusterNodePtr LoadBalancer::select_weighted_round_robin() {
    if (nodes_.empty()) return nullptr;

    // 简化的加权轮询
    uint32_t index = weighted_round_robin_index_ % nodes_.size();
    weighted_round_robin_index_++;
    return nodes_[index];
}

ClusterNodePtr LoadBalancer::select_random() {
    if (nodes_.empty()) return nullptr;

    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(0, nodes_.size() - 1);

    return nodes_[dist(gen)];
}

ClusterNodePtr LoadBalancer::select_consistent_hash(const std::string& key) {
    if (!consistent_hash_ || nodes_.empty()) return nullptr;

    std::string node_id = consistent_hash_->get_node(key);

    for (auto& node : nodes_) {
        if (node->node_id == node_id) {
            return node;
        }
    }

    return nodes_[0];
}

ClusterNodePtr LoadBalancer::select_least_response_time() {
    if (nodes_.empty()) return nullptr;

    ClusterNodePtr min_node = nullptr;
    double min_time = 1e9;

    for (const auto& node : nodes_) {
        if (node->state == NodeState::Healthy &&
            node->response_time < min_time) {
            min_time = node->response_time;
            min_node = node;
        }
    }

    return min_node ? min_node : nodes_[0];
}

// ============================================================================
// ConsistentHash 实现
// ============================================================================

ConsistentHash::ConsistentHash(uint32_t virtual_nodes) : virtual_nodes_(virtual_nodes) {}
ConsistentHash::~ConsistentHash() = default;

void ConsistentHash::add_node(const std::string& node_id, uint32_t weight) {
    std::lock_guard<std::mutex> lock(mutex_);

    uint32_t vnodes = virtual_nodes_ * weight;
    for (uint32_t i = 0; i < vnodes; ++i) {
        std::string key = node_id + "#" + std::to_string(i);
        uint32_t h = hash(key);
        ring_[h] = node_id;
    }
}

void ConsistentHash::remove_node(const std::string& node_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto it = ring_.begin(); it != ring_.end();) {
        if (it->second == node_id) {
            it = ring_.erase(it);
        } else {
            ++it;
        }
    }
}

std::string ConsistentHash::get_node(const std::string& key) const {
    std::lock_guard<std::mutex> lock(mutex_);

    if (ring_.empty()) return "";

    uint32_t h = hash(key);
    auto it = ring_.lower_bound(h);

    if (it == ring_.end()) {
        it = ring_.begin();
    }

    return it->second;
}

std::vector<std::string> ConsistentHash::get_nodes(const std::string& key, uint32_t count) const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<std::string> result;
    if (ring_.empty()) return result;

    uint32_t h = hash(key);
    auto it = ring_.lower_bound(h);

    std::unordered_set<std::string> seen;
    uint32_t found = 0;

    while (found < count && !seen.empty() == false) {
        if (it == ring_.end()) {
            it = ring_.begin();
        }

        if (seen.find(it->second) == seen.end()) {
            result.push_back(it->second);
            seen.insert(it->second);
            found++;
        }

        ++it;

        if (it == ring_.end()) {
            it = ring_.begin();
        }

        // 防止无限循环
        if (seen.size() >= ring_.size()) break;
    }

    return result;
}

uint32_t ConsistentHash::hash(const std::string& key) const {
    // 简单的哈希函数
    uint32_t h = 0;
    for (char c : key) {
        h = h * 31 + c;
    }
    return h;
}

// ============================================================================
// HealthChecker 实现
// ============================================================================

HealthChecker::HealthChecker() = default;
HealthChecker::~HealthChecker() { stop(); }

void HealthChecker::add_check(ClusterNodePtr node) {
    std::lock_guard<std::mutex> lock(mutex_);
    nodes_[node->node_id] = node;
}

void HealthChecker::remove_check(const std::string& node_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    nodes_.erase(node_id);
}

bool HealthChecker::check(ClusterNodePtr node) {
    // TCP 健康检查
    return check_tcp(node->host, node->port);
}

void HealthChecker::start() {
    if (running_) return;

    running_ = true;
    check_thread_ = std::thread(&HealthChecker::check_loop, this);

    LOG_INFO("HealthChecker started");
}

void HealthChecker::stop() {
    running_ = false;

    if (check_thread_.joinable()) {
        check_thread_.join();
    }

    LOG_INFO("HealthChecker stopped");
}

void HealthChecker::check_loop() {
    while (running_) {
        std::lock_guard<std::mutex> lock(mutex_);

        for (auto& [id, node] : nodes_) {
            NodeState old_state = node->state;
            NodeState new_state = check(node) ? NodeState::Healthy : NodeState::Unhealthy;

            if (old_state != new_state) {
                node->state = new_state;
                if (status_callback_) {
                    status_callback_(id, new_state);
                }
            }

            node->last_check = std::chrono::steady_clock::now();
        }

        std::this_thread::sleep_for(check_interval_);
    }
}

bool HealthChecker::check_tcp(const std::string& host, uint16_t port) {
    // 简化的 TCP 检查
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return false;

    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    inet_pton(AF_INET, host.c_str(), &addr.sin_addr);

    // 设置超时
    struct timeval tv;
    tv.tv_sec = 3;
    tv.tv_usec = 0;
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

    int ret = connect(fd, (struct sockaddr*)&addr, sizeof(addr));
    ::close(fd);

    return ret == 0;
}

bool HealthChecker::check_http(const std::string& url) {
    // HTTP 健康检查（简化）
    return true;
}

// ============================================================================
// ClusterManager 实现
// ============================================================================

ClusterManager::ClusterManager() = default;
ClusterManager::~ClusterManager() { stop(); }

bool ClusterManager::initialize(const std::string& node_id) {
    node_id_ = node_id;

    current_node_ = std::make_shared<ClusterNode>();
    current_node_->node_id = node_id;
    current_node_->state = NodeState::Healthy;

    LOG_INFO("ClusterManager initialized: node=" + node_id);
    return true;
}

void ClusterManager::add_node(ClusterNodePtr node) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    nodes_.push_back(node);
}

void ClusterManager::remove_node(const std::string& node_id) {
    std::lock_guard<std::mutex> lock(nodes_mutex_);

    nodes_.erase(
        std::remove_if(nodes_.begin(), nodes_.end(),
                      [&node_id](const ClusterNodePtr& n) {
                          return n->node_id == node_id;
                      }),
        nodes_.end()
    );
}

std::vector<ClusterNodePtr> ClusterManager::get_all_nodes() const {
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    return nodes_;
}

void ClusterManager::update_current_node_stats(const ServerStats& stats) {
    if (!current_node_) return;

    current_node_->current_connections = stats.active_connections;
    current_node_->cpu_usage = stats.cpu_usage;
    current_node_->memory_usage = stats.memory_usage;
    current_node_->bandwidth_usage = stats.bandwidth_usage;
}

void ClusterManager::broadcast(const std::string& message) {
    // 广播消息到所有节点
    std::lock_guard<std::mutex> lock(nodes_mutex_);
    for (const auto& node : nodes_) {
        if (node->node_id != node_id_) {
            send_to_node(node->node_id, message);
        }
    }
}

bool ClusterManager::send_to_node(const std::string& node_id, const std::string& message) {
    // 简化的消息发送
    return true;
}

void ClusterManager::start() {
    if (running_) return;

    running_ = true;
    heartbeat_thread_ = std::thread(&ClusterManager::heartbeat_loop, this);

    LOG_INFO("ClusterManager started");
}

void ClusterManager::stop() {
    running_ = false;

    if (heartbeat_thread_.joinable()) {
        heartbeat_thread_.join();
    }

    LOG_INFO("ClusterManager stopped");
}

void ClusterManager::heartbeat_loop() {
    while (running_) {
        // 发送心跳
        if (current_node_) {
            current_node_->last_heartbeat = std::chrono::steady_clock::now();
        }

        std::this_thread::sleep_for(std::chrono::seconds(10));
    }
}

} // namespace streaming
