#pragma once

/**
 * @file core.h
 * @brief 异构计算框架核心定义
 *
 * 本文件定义了框架的核心类型、枚举和常量。
 *
 * ⭐ 重点: 理解这些核心概念是使用框架的基础
 * 💡 思考: 为什么需要这些抽象？它们如何帮助简化异构计算？
 */

#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <chrono>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <future>
#include <stdexcept>
#include <map>
#include <unordered_map>
#include <queue>
#include <thread>
#include <iostream>
#include <algorithm>
#include <numeric>

namespace heterogeneous {

/**
 * @brief 框架版本信息
 */
struct Version {
    static constexpr int MAJOR = 0;
    static constexpr int MINOR = 1;
    static constexpr int PATCH = 0;

    static std::string to_string() {
        return std::to_string(MAJOR) + "." +
               std::to_string(MINOR) + "." +
               std::to_string(PATCH);
    }
};

/**
 * @brief 设备类型枚举
 *
 * ⭐ 重点: 理解不同设备类型的特点和适用场景
 *
 * - CPU: 适合串行任务，复杂控制逻辑
 * - GPU_CUDA: 适合大规模并行计算，需要 NVIDIA GPU
 * - GPU_OPENCL: 适合跨平台 GPU 计算
 * - FPGA: 适合特定硬件加速
 */
enum class DeviceType {
    CPU,           // 中央处理器
    GPU_CUDA,      // NVIDIA GPU (CUDA)
    GPU_OPENCL,    // GPU (OpenCL)
    FPGA,          // 现场可编程门阵列
    Unknown        // 未知设备
};

/**
 * @brief 设备状态枚举
 */
enum class DeviceStatus {
    Available,     // 可用
    Busy,          // 忙碌
    Error,         // 错误
    Offline        // 离线
};

/**
 * @brief 任务状态枚举
 *
 * 💡 思考: 任务状态机是如何转换的？每个状态代表什么含义？
 */
enum class TaskStatus {
    Created,       // 已创建
    Ready,         // 就绪
    Queued,        // 已排队
    Running,       // 运行中
    Completed,     // 完成
    Failed,        // 失败
    Cancelled      // 已取消
};

/**
 * @brief 任务优先级枚举
 */
enum class TaskPriority {
    Low = 0,       // 低优先级
    Normal = 1,    // 普通优先级
    High = 2,      // 高优先级
    Critical = 3   // 关键优先级
};

/**
 * @brief 内存位置枚举
 *
 * ⭐ 重点: 理解主机内存和设备内存的区别
 *
 * - Host: CPU 可直接访问的内存
 * - Device: GPU 设备内存，需要显式传输
 * - Unified: 统一内存，自动在 CPU/GPU 间迁移
 */
enum class MemoryLocation {
    Host,          // 主机内存 (CPU)
    Device,        // 设备内存 (GPU)
    Unified        // 统一内存
};

/**
 * @brief 调度策略枚举
 *
 * ⭐ 重点: 不同调度策略的适用场景
 *
 * - RoundRobin: 简单公平，适合任务均匀的场景
 * - LoadBalancing: 负载均衡，适合任务不均匀的场景
 * - Affinity: 亲和性，适合有数据局部性的场景
 * - Priority: 优先级，适合有紧急任务的场景
 * - Adaptive: 自适应，适合复杂多变的场景
 */
enum class SchedulingStrategy {
    RoundRobin,    // 轮询调度
    LoadBalancing, // 负载均衡
    Affinity,      // 亲和性调度
    Priority,      // 优先级调度
    Adaptive       // 自适应调度
};

/**
 * @brief 框架状态枚举
 */
enum class FrameworkStatus {
    Uninitialized, // 未初始化
    Initializing,  // 初始化中
    Ready,         // 就绪
    Running,       // 运行中
    ShuttingDown,  // 关闭中
    Error          // 错误
};

/**
 * @brief 错误码枚举
 */
enum class ErrorCode {
    Success = 0,

    // 设备错误 (100-199)
    DeviceNotFound = 100,
    DeviceNotAvailable = 101,
    DeviceInitFailed = 102,

    // 内存错误 (200-299)
    MemoryAllocationFailed = 200,
    MemoryTransferFailed = 201,
    MemoryNotEnough = 202,

    // 任务错误 (300-399)
    TaskCreationFailed = 300,
    TaskExecutionFailed = 301,
    TaskTimeout = 302,
    TaskCancelled = 303,

    // 调度错误 (400-499)
    SchedulingFailed = 400,
    NoAvailableDevice = 401,

    // 未知错误 (999)
    Unknown = 999
};

/**
 * @brief 设备信息结构体
 */
struct DeviceInfo {
    std::string id;                    // 设备 ID
    std::string name;                  // 设备名称
    DeviceType type;                   // 设备类型
    DeviceStatus status;               // 设备状态

    // 硬件信息
    size_t memory_size;                // 内存大小 (字节)
    size_t compute_units;              // 计算单元数
    size_t max_work_group_size;        // 最大工作组大小

    // 能力信息
    bool supports_double_precision;    // 是否支持双精度
    bool supports_unified_memory;      // 是否支持统一内存
    int compute_capability_major;      // 计算能力主版本
    int compute_capability_minor;      // 计算能力次版本

    // 性能信息
    size_t memory_bandwidth;           // 内存带宽 (字节/秒)
    size_t compute_throughput;         // 计算吞吐量 (浮点操作/秒)

    DeviceInfo()
        : type(DeviceType::Unknown)
        , status(DeviceStatus::Offline)
        , memory_size(0)
        , compute_units(0)
        , max_work_group_size(0)
        , supports_double_precision(false)
        , supports_unified_memory(false)
        , compute_capability_major(0)
        , compute_capability_minor(0)
        , memory_bandwidth(0)
        , compute_throughput(0) {}
};

/**
 * @brief 任务结果结构体
 */
struct TaskResult {
    bool success;                      // 是否成功
    ErrorCode error_code;              // 错误码
    std::string error_message;         // 错误信息

    // 性能统计
    std::chrono::microseconds execution_time;   // 执行时间
    size_t memory_used;                // 使用的内存
    std::string device_used;           // 使用的设备

    TaskResult()
        : success(false)
        , error_code(ErrorCode::Unknown)
        , execution_time(0)
        , memory_used(0) {}
};

/**
 * @brief 调度统计信息
 */
struct SchedulingStats {
    size_t total_tasks_scheduled;      // 总调度任务数
    size_t tasks_on_cpu;               // CPU 上的任务数
    size_t tasks_on_gpu;               // GPU 上的任务数
    double avg_scheduling_time;        // 平均调度时间
    double load_balance_factor;        // 负载均衡因子

    SchedulingStats()
        : total_tasks_scheduled(0)
        , tasks_on_cpu(0)
        , tasks_on_gpu(0)
        , avg_scheduling_time(0.0)
        , load_balance_factor(1.0) {}
};

/**
 * @brief 执行统计信息
 */
struct ExecutionStats {
    size_t total_tasks_executed;       // 总执行任务数
    size_t successful_tasks;           // 成功任务数
    size_t failed_tasks;               // 失败任务数
    std::chrono::microseconds total_execution_time;  // 总执行时间
    std::chrono::microseconds avg_execution_time;    // 平均执行时间

    ExecutionStats()
        : total_tasks_executed(0)
        , successful_tasks(0)
        , failed_tasks(0)
        , total_execution_time(0)
        , avg_execution_time(0) {}
};

/**
 * @brief 调度器配置
 */
struct SchedulerConfig {
    SchedulingStrategy strategy;       // 调度策略
    size_t max_concurrent_tasks;       // 最大并发任务数
    size_t task_queue_size;            // 任务队列大小
    bool enable_task_reordering;       // 是否启用任务重排序
    bool enable_data_prefetch;         // 是否启用数据预取

    // 负载均衡参数
    double cpu_load_threshold;         // CPU 负载阈值
    double gpu_load_threshold;         // GPU 负载阈值

    // 超时设置
    std::chrono::milliseconds task_timeout;          // 任务超时
    std::chrono::milliseconds scheduling_interval;   // 调度间隔

    SchedulerConfig()
        : strategy(SchedulingStrategy::Adaptive)
        , max_concurrent_tasks(16)
        , task_queue_size(1000)
        , enable_task_reordering(true)
        , enable_data_prefetch(true)
        , cpu_load_threshold(0.8)
        , gpu_load_threshold(0.9)
        , task_timeout(std::chrono::milliseconds(30000))
        , scheduling_interval(std::chrono::milliseconds(10)) {}
};

/**
 * @brief 框架配置
 */
struct FrameworkConfig {
    SchedulerConfig scheduler_config;
    bool enable_logging;
    bool enable_profiling;
    std::string log_file;

    FrameworkConfig()
        : enable_logging(true)
        , enable_profiling(false) {}
};

// 异常类定义

/**
 * @brief 异构计算框架异常基类
 */
class HeterogeneousException : public std::exception {
public:
    HeterogeneousException(const std::string& message, ErrorCode code = ErrorCode::Unknown)
        : message_(message), error_code_(code) {}

    const char* what() const noexcept override {
        return message_.c_str();
    }

    ErrorCode error_code() const {
        return error_code_;
    }

private:
    std::string message_;
    ErrorCode error_code_;
};

/**
 * @brief 设备相关异常
 */
class DeviceException : public HeterogeneousException {
public:
    DeviceException(const std::string& message, ErrorCode code = ErrorCode::DeviceNotFound)
        : HeterogeneousException(message, code) {}
};

/**
 * @brief 内存相关异常
 */
class MemoryException : public HeterogeneousException {
public:
    MemoryException(const std::string& message, ErrorCode code = MemoryAllocationFailed)
        : HeterogeneousException(message, code) {}
};

/**
 * @brief 任务相关异常
 */
class TaskException : public HeterogeneousException {
public:
    TaskException(const std::string& message, ErrorCode code = TaskCreationFailed)
        : HeterogeneousException(message, code) {}
};

// 便捷函数

/**
 * @brief 获取设备类型名称
 */
inline std::string device_type_name(DeviceType type) {
    switch (type) {
        case DeviceType::CPU: return "CPU";
        case DeviceType::GPU_CUDA: return "GPU_CUDA";
        case DeviceType::GPU_OPENCL: return "GPU_OPENCL";
        case DeviceType::FPGA: return "FPGA";
        default: return "Unknown";
    }
}

/**
 * @brief 获取任务状态名称
 */
inline std::string task_status_name(TaskStatus status) {
    switch (status) {
        case TaskStatus::Created: return "Created";
        case TaskStatus::Ready: return "Ready";
        case TaskStatus::Queued: return "Queued";
        case TaskStatus::Running: return "Running";
        case TaskStatus::Completed: return "Completed";
        case TaskStatus::Failed: return "Failed";
        case TaskStatus::Cancelled: return "Cancelled";
        default: return "Unknown";
    }
}

/**
 * @brief 获取错误码名称
 */
inline std::string error_code_name(ErrorCode code) {
    switch (code) {
        case ErrorCode::Success: return "Success";
        case ErrorCode::DeviceNotFound: return "DeviceNotFound";
        case ErrorCode::DeviceNotAvailable: return "DeviceNotAvailable";
        case ErrorCode::DeviceInitFailed: return "DeviceInitFailed";
        case ErrorCode::MemoryAllocationFailed: return "MemoryAllocationFailed";
        case ErrorCode::MemoryTransferFailed: return "MemoryTransferFailed";
        case ErrorCode::MemoryNotEnough: return "MemoryNotEnough";
        case ErrorCode::TaskCreationFailed: return "TaskCreationFailed";
        case ErrorCode::TaskExecutionFailed: return "TaskExecutionFailed";
        case ErrorCode::TaskTimeout: return "TaskTimeout";
        case ErrorCode::TaskCancelled: return "TaskCancelled";
        case ErrorCode::SchedulingFailed: return "SchedulingFailed";
        case ErrorCode::NoAvailableDevice: return "NoAvailableDevice";
        default: return "Unknown";
    }
}

} // namespace heterogeneous
