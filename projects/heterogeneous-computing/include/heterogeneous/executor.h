#pragma once

/**
 * @file executor.h
 * @brief 任务执行器
 *
 * 本文件定义了任务执行相关的类和接口。
 *
 * ⭐ 重点: 理解任务执行的流程和优化策略
 * 💡 思考: 如何实现计算与传输的重叠？
 */

#include "core.h"
#include "task.h"
#include "device.h"
#include "memory.h"
#include <string>
#include <vector>
#include <memory>
#include <future>
#include <thread>
#include <atomic>
#include <mutex>
#include <functional>

namespace heterogeneous {

/**
 * @brief 执行器基类
 *
 * ⭐ 重点: 理解执行器的设计
 *
 * 执行器负责在设备上执行任务，包括:
 * - 数据准备
 * - 任务执行
 * - 结果收集
 *
 * 💡 思考: 执行器如何处理执行失败？
 */
class Executor {
public:
    /**
     * @brief 构造函数
     * @param device 设备指针
     */
    explicit Executor(std::shared_ptr<Device> device);

    /**
     * @brief 虚析构函数
     */
    virtual ~Executor();

    /**
     * @brief 执行任务
     * @param task 任务指针
     * @return 任务结果
     */
    virtual TaskResult execute(std::shared_ptr<Task> task);

    /**
     * @brief 批量执行任务
     * @param tasks 任务列表
     * @return 结果列表
     */
    virtual std::vector<TaskResult> execute_batch(
        const std::vector<std::shared_ptr<Task>>& tasks);

    /**
     * @brief 异步执行任务
     * @param task 任务指针
     * @return future 对象
     */
    virtual std::future<TaskResult> execute_async(std::shared_ptr<Task> task);

    /**
     * @brief 获取设备
     */
    std::shared_ptr<Device> device() const { return device_; }

    /**
     * @brief 获取执行统计
     */
    ExecutionStats get_stats() const { return stats_; }

protected:
    /**
     * @brief 准备数据
     * @param task 任务指针
     */
    virtual void prepare_data(std::shared_ptr<Task> task);

    /**
     * @brief 执行计算
     * @param task 任务指针
     */
    virtual void compute(std::shared_ptr<Task> task);

    /**
     * @brief 收集结果
     * @param task 任务指针
     */
    virtual void collect_result(std::shared_ptr<Task> task);

    std::shared_ptr<Device> device_;
    ExecutionStats stats_;
    mutable std::mutex stats_mutex_;
};

/**
 * @brief CPU 执行器
 *
 * ⭐ 重点: 理解 CPU 并行执行的方式
 *
 * CPU 执行器使用线程池实现并行执行。
 * 适合:
 * - 串行任务
 * - 复杂控制逻辑
 * - 小规模并行任务
 *
 * 💡 思考: CPU 执行器如何利用多核？
 */
class CPUExecutor : public Executor {
public:
    CPUExecutor(std::shared_ptr<Device> device);
    ~CPUExecutor() override;

    TaskResult execute(std::shared_ptr<Task> task) override;

private:
    /**
     * @brief 线程池大小
     */
    size_t thread_pool_size_;
};

/**
 * @brief GPU 执行器
 *
 * ⭐ 重点: 理解 GPU 执行的流程
 *
 * GPU 执行器的执行流程:
 * 1. 准备数据 (从主机复制到设备)
 * 2. 启动内核
 * 3. 等待执行完成
 * 4. 收集结果 (从设备复制回主机)
 *
 * 💡 思考: 如何实现计算与传输的重叠？
 */
class GPUExecutor : public Executor {
public:
    GPUExecutor(std::shared_ptr<Device> device);
    ~GPUExecutor() override;

    TaskResult execute(std::shared_ptr<Task> task) override;

protected:
    /**
     * @brief 传输数据到设备
     * @param task 任务指针
     */
    virtual void transfer_to_device(std::shared_ptr<Task> task);

    /**
     * @brief 在设备上执行计算
     * @param task 任务指针
     */
    virtual void compute_on_device(std::shared_ptr<Task> task);

    /**
     * @brief 从设备传输结果
     * @param task 任务指针
     */
    virtual void transfer_from_device(std::shared_ptr<Task> task);

private:
    // 设备内存缓冲区
    void* input_buffer_ = nullptr;
    void* output_buffer_ = nullptr;
    size_t buffer_size_ = 0;
};

#ifdef HETEROGENEOUS_ENABLE_CUDA
/**
 * @brief CUDA 执行器
 *
 * ⭐ 重点: 理解 CUDA 执行的细节
 *
 * CUDA 执行器使用 CUDA 流实现异步执行。
 *
 * 💡 思考: CUDA 流如何实现计算与传输的重叠？
 */
class CUDAExecutor : public GPUExecutor {
public:
    CUDAExecutor(std::shared_ptr<Device> device);
    ~CUDAExecutor() override;

    TaskResult execute(std::shared_ptr<Task> task) override;

protected:
    void transfer_to_device(std::shared_ptr<Task> task) override;
    void compute_on_device(std::shared_ptr<Task> task) override;
    void transfer_from_device(std::shared_ptr<Task> task) override;

private:
    void* stream_;  // cudaStream_t
};
#endif // HETEROGENEOUS_ENABLE_CUDA

#ifdef HETEROGENEOUS_ENABLE_OPENCL
/**
 * @brief OpenCL 执行器
 *
 * ⭐ 重点: 理解 OpenCL 执行的细节
 *
 * OpenCL 执行器使用命令队列实现异步执行。
 *
 * 💡 思考: OpenCL 和 CUDA 的执行模型有什么区别？
 */
class OpenCLExecutor : public GPUExecutor {
public:
    OpenCLExecutor(std::shared_ptr<Device> device);
    ~OpenCLExecutor() override;

    TaskResult execute(std::shared_ptr<Task> task) override;

protected:
    void transfer_to_device(std::shared_ptr<Task> task) override;
    void compute_on_device(std::shared_ptr<Task> task) override;
    void transfer_from_device(std::shared_ptr<Task> task) override;
};
#endif // HETEROGENEOUS_ENABLE_OPENCL

/**
 * @brief 执行器工厂
 *
 * 💡 思考: 工厂模式如何简化执行器的创建？
 */
class ExecutorFactory {
public:
    /**
     * @brief 创建执行器
     * @param device 设备指针
     * @return 执行器指针
     */
    static std::unique_ptr<Executor> create(std::shared_ptr<Device> device);
};

/**
 * @brief 任务流水线
 *
 * ⭐ 重点: 理解流水线的概念
 *
 * 任务流水线将多个任务组织成流水线，实现任务并行。
 *
 * 💡 思考: 流水线如何提高吞吐量？
 */
class Pipeline {
public:
    /**
     * @brief 构造函数
     */
    Pipeline();

    /**
     * @brief 析构函数
     */
    ~Pipeline();

    /**
     * @brief 添加阶段
     * @param name 阶段名称
     * @param executor 执行器
     * @return 流水线引用
     */
    Pipeline& add_stage(const std::string& name, std::unique_ptr<Executor> executor);

    /**
     * @brief 执行流水线
     * @param tasks 任务列表
     * @return 结果列表
     */
    std::vector<TaskResult> execute(const std::vector<std::shared_ptr<Task>>& tasks);

    /**
     * @brief 获取阶段数量
     */
    size_t stage_count() const { return stages_.size(); }

private:
    struct Stage {
        std::string name;
        std::unique_ptr<Executor> executor;
    };
    std::vector<Stage> stages_;
};

/**
 * @brief 并行执行器
 *
 * ⭐ 重点: 理解并行执行的实现
 *
 * 并行执行器将任务分配给多个设备并行执行。
 *
 * 💡 思考: 如何处理并行执行中的同步问题？
 */
class ParallelExecutor {
public:
    /**
     * @brief 构造函数
     * @param executors 执行器列表
     */
    ParallelExecutor(std::vector<std::unique_ptr<Executor>> executors);

    /**
     * @brief 析构函数
     */
    ~ParallelExecutor();

    /**
     * @brief 并行执行任务
     * @param tasks 任务列表
     * @return 结果列表
     */
    std::vector<TaskResult> execute(const std::vector<std::shared_ptr<Task>>& tasks);

    /**
     * @brief 获取执行器数量
     */
    size_t executor_count() const { return executors_.size(); }

private:
    std::vector<std::unique_ptr<Executor>> executors_;
    std::atomic<size_t> current_executor_{0};
};

} // namespace heterogeneous
