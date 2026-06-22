/**
 * @file load_balancer.cpp
 * @brief 负载均衡器实现
 *
 * 实现三种负载均衡算法：
 * 1. 轮询 (Round Robin)
 * 2. 加权轮询 (Weighted Round Robin)
 * 3. 最少连接 (Least Connections)
 */

#include "../include/load_balancer.h"
#include <algorithm>
#include <stdexcept>

namespace ha_server {

// ============================================================================
// 轮询负载均衡器实现
// ============================================================================

/**
 * 轮询算法实现
 *
 * 使用原子操作保证线程安全。
 * 每次选择下一个后端，循环往复。
 *
 * ⭐ 重点：atomic 操作保证线程安全
 * 💡 思考：fetch_add 的内存序参数有什么作用？
 */
Backend* RoundRobinBalancer::select_backend(const std::vector<Backend*>& backends) {
    if (backends.empty()) {
        return nullptr;
    }

    // 使用原子操作获取索引
    // fetch_add 返回旧值，然后取模
    int index = current_index_.fetch_add(1, std::memory_order_relaxed) % backends.size();
    return backends[index];
}

// ============================================================================
// 加权轮询负载均衡器实现
// ============================================================================

/**
 * 平滑加权轮询算法实现
 *
 * 算法描述：
 * 1. 每个后端有配置权重 weight 和当前权重 current_weight
 * 2. 每次选择 current_weight 最大的后端
 * 3. 选中后：current_weight -= total_weight
 * 4. 每轮：所有后端 current_weight += weight
 *
 * 示例（权重 5:3:2）：
 *   初始：A=5, B=3, C=2 → 选择 A
 *   A=-5, B=6, C=4 → 选择 B
 *   A=0, B=-4, C=6 → 选择 C
 *   A=5, B=2, C=1 → 选择 A
 *   ...
 *
 * ⭐ 重点：平滑加权轮询避免请求突刺
 * 💡 思考：为什么需要平滑？直接按权重比例分配有什么问题？
 */
Backend* WeightedRoundRobinBalancer::select_backend(const std::vector<Backend*>& backends) {
    if (backends.empty()) {
        return nullptr;
    }

    // 计算总权重
    int total_weight = 0;
    for (auto* backend : backends) {
        total_weight += backend->weight;
    }

    if (total_weight == 0) {
        // 所有权重为 0，退化为轮询
        return backends[0];
    }

    // 找到 current_weight 最大的后端
    Backend* best = nullptr;
    for (auto* backend : backends) {
        // 增加当前权重
        backend->current_weight += backend->weight;

        if (!best || backend->current_weight > best->current_weight) {
            best = backend;
        }
    }

    // 选中后减去总权重
    if (best) {
        best->current_weight -= total_weight;
    }

    return best;
}

// ============================================================================
// 最少连接负载均衡器实现
// ============================================================================

/**
 * 最少连接算法实现
 *
 * 选择当前活跃连接数最少的后端。
 * 这种算法可以自动适应不同后端的负载情况。
 *
 * ⭐ 重点：active_connections 的原子性
 * 💡 思考：最少连接 vs 加权最少连接有什么区别？
 */
Backend* LeastConnectionsBalancer::select_backend(const std::vector<Backend*>& backends) {
    if (backends.empty()) {
        return nullptr;
    }

    Backend* best = nullptr;
    int min_connections = INT32_MAX;

    for (auto* backend : backends) {
        int connections = backend->get_active_connections();
        if (connections < min_connections) {
            min_connections = connections;
            best = backend;
        }
    }

    return best;
}

// ============================================================================
// 负载均衡器工厂实现
// ============================================================================

std::unique_ptr<LoadBalancer> LoadBalancerFactory::create(BalancerType type) {
    switch (type) {
        case BalancerType::RoundRobin:
            return std::make_unique<RoundRobinBalancer>();
        case BalancerType::WeightedRoundRobin:
            return std::make_unique<WeightedRoundRobinBalancer>();
        case BalancerType::LeastConnections:
            return std::make_unique<LeastConnectionsBalancer>();
        default:
            throw std::invalid_argument("Unknown balancer type");
    }
}

std::unique_ptr<LoadBalancer> LoadBalancerFactory::create(const std::string& name) {
    if (name == "round_robin") {
        return create(BalancerType::RoundRobin);
    } else if (name == "weighted_round_robin") {
        return create(BalancerType::WeightedRoundRobin);
    } else if (name == "least_connections") {
        return create(BalancerType::LeastConnections);
    } else {
        throw std::invalid_argument("Unknown balancer name: " + name);
    }
}

} // namespace ha_server
