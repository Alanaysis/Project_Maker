#pragma once

/**
 * @file load_balancer.h
 * @brief 负载均衡器接口和实现
 *
 * 定义负载均衡器的抽象接口和多种算法实现。
 * 负载均衡器负责从健康的后端中选择一个来处理请求。
 *
 * ⭐ 重点：理解不同负载均衡算法的适用场景
 * 💡 思考：如何根据实际场景选择合适的算法？
 */

#include "backend.h"
#include <vector>
#include <memory>
#include <atomic>

namespace ha_server {

/**
 * @brief 负载均衡器基类
 *
 * 所有负载均衡算法都继承此基类。
 * 使用策略模式，可以在运行时切换算法。
 *
 * 💡 设计模式：策略模式 (Strategy Pattern)
 * - 定义算法族，分别封装
 * - 使它们可以互相替换
 * - 算法变化独立于使用算法的客户
 */
class LoadBalancer {
public:
    virtual ~LoadBalancer() = default;

    /**
     * @brief 选择一个后端服务器
     * @param backends 可用的后端列表（已过滤不健康的后端）
     * @return 选中的后端指针，如果没有可用后端返回 nullptr
     *
     * ⭐ 重点：此函数需要线程安全
     */
    virtual Backend* select_backend(const std::vector<Backend*>& backends) = 0;

    /**
     * @brief 获取算法名称
     * @return 算法名称字符串
     */
    virtual std::string name() const = 0;

    /**
     * @brief 重置算法状态
     *
     * 某些算法（如轮询）需要维护内部状态，此方法用于重置。
     */
    virtual void reset() {}
};

/**
 * @brief 轮询负载均衡器 (Round Robin)
 *
 * 最简单的负载均衡算法，按顺序将请求分配到各后端。
 *
 * 算法描述：
 * 1. 维护一个全局索引 current_index
 * 2. 每次请求选择 backends[current_index % size]
 * 3. current_index++
 *
 * 时间复杂度：O(1)
 * 空间复杂度：O(1)
 *
 * 优点：简单、公平分配
 * 缺点：不考虑后端性能差异
 *
 * 适用场景：
 * - 后端服务器性能相近
 * - 请求处理时间相近
 * - 无特殊会话保持需求
 *
 * ⭐ 重点：使用原子操作保证线程安全
 */
class RoundRobinBalancer : public LoadBalancer {
public:
    Backend* select_backend(const std::vector<Backend*>& backends) override;

    std::string name() const override {
        return "round_robin";
    }

    void reset() override {
        current_index_.store(0);
    }

private:
    std::atomic<int> current_index_{0};
};

/**
 * @brief 加权轮询负载均衡器 (Weighted Round Robin)
 *
 * 根据后端权重分配请求，权重越高分配到的请求越多。
 * 使用平滑加权轮询算法，避免请求集中在某个后端。
 *
 * 算法描述（平滑加权轮询）：
 * 1. 每个后端有配置权重 weight 和当前权重 current_weight
 * 2. 每次选择 current_weight 最大的后端
 * 3. 选中后：current_weight -= total_weight
 * 4. 每轮：所有后端 current_weight += weight
 *
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 *
 * 优点：平滑分配、考虑权重
 * 缺点：需要遍历后端列表
 *
 * 适用场景：
 * - 后端服务器性能不同
 * - 需要按性能比例分配请求
 *
 * ⭐ 重点：平滑加权轮询避免请求突刺
 * 💡 思考：权重如何动态调整？
 */
class WeightedRoundRobinBalancer : public LoadBalancer {
public:
    Backend* select_backend(const std::vector<Backend*>& backends) override;

    std::string name() const override {
        return "weighted_round_robin";
    }

    void reset() override {
        // 不需要重置，每次选择时动态计算
    }
};

/**
 * @brief 最少连接负载均衡器 (Least Connections)
 *
 * 选择当前活跃连接数最少的后端，实现自适应负载均衡。
 *
 * 算法描述：
 * 1. 遍历所有健康的后端
 * 2. 选择 active_connections 最小的后端
 * 3. 如果有多个相同，选择第一个
 *
 * 时间复杂度：O(n)
 * 空间复杂度：O(1)
 *
 * 优点：自适应负载、自动平衡
 * 缺点：需要维护连接计数
 *
 * 适用场景：
 * - 请求处理时间差异大
 * - 需要动态负载均衡
 *
 * 💡 思考：最少连接 vs 加权最少连接有什么区别？
 */
class LeastConnectionsBalancer : public LoadBalancer {
public:
    Backend* select_backend(const std::vector<Backend*>& backends) override;

    std::string name() const override {
        return "least_connections";
    }
};

/**
 * @brief 负载均衡器工厂
 *
 * 根据类型创建对应的负载均衡器实例。
 * 使用工厂模式，简化负载均衡器的创建。
 */
class LoadBalancerFactory {
public:
    /**
     * @brief 创建负载均衡器
     * @param type 算法类型
     * @return 负载均衡器实例
     */
    static std::unique_ptr<LoadBalancer> create(BalancerType type);

    /**
     * @brief 创建负载均衡器
     * @param name 算法名称
     * @return 负载均衡器实例
     */
    static std::unique_ptr<LoadBalancer> create(const std::string& name);
};

} // namespace ha_server
