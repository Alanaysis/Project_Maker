#pragma once

/**
 * @file scheduler.h
 * @brief 任务调度器
 *
 * 本文件定义了任务调度相关的类和接口。
 *
 * ⭐ 重点: 理解不同调度策略的原理和适用场景
 * 💡 思考: 如何实现一个高效的自适应调度器？
 */

#include "core.h"
#include "task.h"
#include "device.h"
#include <string>
#include <vector>
#include <memory>
#include <queue>
#include <functional>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>

namespace heterogeneous {

/**
 * @brief 调度器基类
 *
 * ⭐ 重点: 理解调度器的设计
 *
 * 调度器负责将任务分配到合适的设备上执行。
 * 不同的调度策略适用于不同的场景。
 *
 * 💡 思考: 调度器如何平衡公平性和效率？
 */
class Scheduler {
public:
    /**
     * @brief 构造函数
     * @param config 调度器配置
     */
    explicit Scheduler(const SchedulerConfig& config = SchedulerConfig());

    /**
     * @brief 虚析构函数
     */
    virtual ~Scheduler();

    /**
     * @brief 初始化调度器
     * @return true 如果初始化成功
     */
    virtual bool initialize();

    /**
     * @brief 关闭调度器
     */
    virtual void shutdown();

    /**
     * @brief 调度任务
     * @param task 任务指针
     * @return 分配的设备指针
     */
    virtual std::shared_ptr<Device> schedule(std::shared_ptr<Task> task) = 0;

    /**
     * @brief 提交任务
     * @param task 任务指针
     * @return true 如果提交成功
     */
    bool submit_task(std::shared_ptr<Task> task);

    /**
     * @brief 等待任务完成
     * @param task_id 任务 ID
     * @param timeout 超时时间
     * @return true 如果任务完成
     */
    bool wait_for_task(const std::string& task_id,
                       std::chrono::milliseconds timeout = std::chrono::milliseconds::max());

    /**
     * @brief 等待所有任务完成
     */
    void wait_for_all();

    /**
     * @brief 取消任务
     * @param task_id 任务 ID
     * @return true 如果取消成功
     */
    bool cancel_task(const std::string& task_id);

    /**
     * @brief 获取调度统计
     */
    SchedulingStats get_stats() const;

    /**
     * @brief 获取配置
     */
    const SchedulerConfig& config() const { return config_; }

    /**
     * @brief 更新配置
     * @param config 新配置
     */
    void update_config(const SchedulerConfig& config);

protected:
    /**
     * @brief 选择最优设备
     * @param task 任务指针
     * @return 设备指针
     */
    std::shared_ptr<Device> select_device(std::shared_ptr<Task> task);

    /**
     * @brief 执行任务
     * @param task 任务指针
     * @param device 设备指针
     */
    void execute_task(std::shared_ptr<Task> task, std::shared_ptr<Device> device);

    /**
     * @brief 调度线程函数
     */
    void scheduling_thread_func();

    SchedulerConfig config_;
    std::shared_ptr<DeviceManager> device_manager_;

    // 任务队列
    struct TaskEntry {
        std::shared_ptr<Task> task;
        std::chrono::steady_clock::time_point submit_time;

        bool operator<(const TaskEntry& other) const {
            // 优先级高的排在前面
            if (task->priority() != other.task->priority()) {
                return task->priority() < other.task->priority();
            }
            // 同优先级按提交时间排序
            return submit_time > other.submit_time;
        }
    };
    std::priority_queue<TaskEntry> task_queue_;
    std::mutex queue_mutex_;
    std::condition_variable queue_cv_;

    // 任务完成通知
    std::unordered_map<std::string, std::promise<void>> task_promises_;
    std::mutex promise_mutex_;

    // 调度线程
    std::thread scheduling_thread_;
    std::atomic<bool> running_{false};

    // 统计信息
    SchedulingStats stats_;
    mutable std::mutex stats_mutex_;
};

/**
 * @brief 轮询调度器
 *
 * ⭐ 重点: 理解轮询调度的原理
 *
 * 轮询调度是最简单的调度策略，将任务轮流分配给各设备。
 * 优点: 简单公平
 * 缺点: 不考虑设备负载和任务特性
 *
 * 💡 思考: 轮询调度在什么场景下表现良好？
 */
class RoundRobinScheduler : public Scheduler {
public:
    RoundRobinScheduler(const SchedulerConfig& config = SchedulerConfig());
    ~RoundRobinScheduler() override = default;

    std::shared_ptr<Device> schedule(std::shared_ptr<Task> task) override;

private:
    size_t current_device_ = 0;
};

/**
 * @brief 负载均衡调度器
 *
 * ⭐ 重点: 理解负载均衡的原理
 *
 * 负载均衡调度将任务分配给当前负载最低的设备。
 * 优点: 充分利用设备资源
 * 缺点: 需要监控设备负载
 *
 * 💡 思考: 如何准确衡量设备负载？
 */
class LoadBalancingScheduler : public Scheduler {
public:
    LoadBalancingScheduler(const SchedulerConfig& config = SchedulerConfig());
    ~LoadBalancingScheduler() override = default;

    std::shared_ptr<Device> schedule(std::shared_ptr<Task> task) override;

private:
    /**
     * @brief 计算设备负载
     * @param device 设备指针
     * @return 负载值 (0.0 - 1.0)
     */
    double calculate_load(std::shared_ptr<Device> device);
};

/**
 * @brief 优先级调度器
 *
 * ⭐ 重点: 理解优先级调度的原理
 *
 * 优先级调度按照任务优先级进行调度，高优先级任务优先执行。
 * 优点: 支持紧急任务
 * 缺点: 可能导致低优先级任务饥饿
 *
 * 💡 思考: 如何避免低优先级任务饥饿？
 */
class PriorityScheduler : public Scheduler {
public:
    PriorityScheduler(const SchedulerConfig& config = SchedulerConfig());
    ~PriorityScheduler() override = default;

    std::shared_ptr<Device> schedule(std::shared_ptr<Task> task) override;
};

/**
 * @brief 自适应调度器
 *
 * ⭐ 重点: 理解自适应调度的原理
 *
 * 自适应调度根据任务特性和历史性能数据动态选择最优设备。
 * 优点: 智能高效
 * 缺点: 实现复杂，需要学习
 *
 * 💡 思考: 如何收集和利用历史性能数据？
 */
class AdaptiveScheduler : public Scheduler {
public:
    AdaptiveScheduler(const SchedulerConfig& config = SchedulerConfig());
    ~AdaptiveScheduler() override = default;

    std::shared_ptr<Device> schedule(std::shared_ptr<Task> task) override;

    /**
     * @brief 记录任务性能
     * @param task_name 任务名称
     * @param device_id 设备 ID
     * @param execution_time 执行时间
     */
    void record_performance(const std::string& task_name,
                           const std::string& device_id,
                           std::chrono::microseconds execution_time);

private:
    /**
     * @brief 分析任务特征
     * @param task 任务指针
     * @return 任务特征值
     */
    double analyze_task(std::shared_ptr<Task> task);

    /**
     * @brief 预测执行时间
     * @param task_name 任务名称
     * @param device_id 设备 ID
     * @return 预测的执行时间
     */
    std::chrono::microseconds predict_time(const std::string& task_name,
                                           const std::string& device_id);

    // 性能历史记录
    struct PerformanceRecord {
        std::vector<std::chrono::microseconds> execution_times;
        std::chrono::microseconds avg_time{0};

        void add(std::chrono::microseconds time) {
            execution_times.push_back(time);
            // 计算平均值
            auto total = std::accumulate(execution_times.begin(),
                                        execution_times.end(),
                                        std::chrono::microseconds{0});
            avg_time = total / execution_times.size();
        }
    };

    // 任务名称 -> (设备 ID -> 性能记录)
    std::unordered_map<std::string,
                       std::unordered_map<std::string, PerformanceRecord>> performance_history_;
    mutable std::mutex history_mutex_;
};

/**
 * @brief 调度器工厂
 *
 * 💡 思考: 工厂模式如何简化调度器的创建？
 */
class SchedulerFactory {
public:
    /**
     * @brief 创建调度器
     * @param strategy 调度策略
     * @param config 调度器配置
     * @return 调度器指针
     */
    static std::unique_ptr<Scheduler> create(SchedulingStrategy strategy,
                                             const SchedulerConfig& config = SchedulerConfig());
};

} // namespace heterogeneous
