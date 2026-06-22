#pragma once

/**
 * @file task.h
 * @brief 任务抽象和管理
 *
 * 本文件定义了任务相关的类和接口。
 *
 * ⭐ 重点: 理解任务的生命周期和状态转换
 * 💡 思考: 如何设计一个灵活且高效的任务系统？
 */

#include "core.h"
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <atomic>
#include <mutex>

namespace heterogeneous {

// 前向声明
class Device;

/**
 * @brief 任务计算函数类型
 *
 * @param input 输入数据指针
 * @param output 输出数据指针
 * @param size 数据大小 (字节)
 * @param device_info 设备信息 (可选，用于设备特定优化)
 */
using TaskFunc = std::function<void(const void* input, void* output, size_t size,
                                     const DeviceInfo* device_info)>;

/**
 * @brief 任务类
 *
 * ⭐ 重点: 理解任务的设计和使用方式
 *
 * 任务是异构计算的基本单位，包含:
 * - 计算函数
 * - 输入/输出数据
 * - 执行配置
 * - 状态信息
 *
 * 💡 思考: 为什么使用 Builder 模式来配置任务？
 */
class Task {
public:
    /**
     * @brief 构造函数
     * @param name 任务名称
     * @param func 计算函数
     */
    Task(const std::string& name, TaskFunc func);

    /**
     * @brief 析构函数
     */
    ~Task() = default;

    // 禁止拷贝
    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;

    // 允许移动
    Task(Task&&) = default;
    Task& operator=(Task&&) = default;

    // Builder 模式接口

    /**
     * @brief 设置输入数据
     * @param data 数据指针
     * @param size 数据大小 (字节)
     * @return Task& 引用，支持链式调用
     */
    Task& set_input(const void* data, size_t size);

    /**
     * @brief 设置输出数据
     * @param data 数据指针
     * @param size 数据大小 (字节)
     * @return Task& 引用，支持链式调用
     */
    Task& set_output(void* data, size_t size);

    /**
     * @brief 设置首选设备类型
     * @param type 设备类型
     * @return Task& 引用，支持链式调用
     */
    Task& prefer_device(DeviceType type);

    /**
     * @brief 设置任务优先级
     * @param priority 优先级
     * @return Task& 引用，支持链式调用
     */
    Task& set_priority(TaskPriority priority);

    /**
     * @brief 添加依赖任务
     * @param task_id 依赖任务的 ID
     * @return Task& 引用，支持链式调用
     */
    Task& add_dependency(const std::string& task_id);

    /**
     * @brief 设置完成回调
     * @param callback 回调函数
     * @return Task& 引用，支持链式调用
     */
    Task& on_complete(std::function<void(const Task&)> callback);

    /**
     * @brief 设置错误回调
     * @param callback 回调函数
     * @return Task& 引用，支持链式调用
     */
    Task& on_error(std::function<void(const Task&, const std::exception&)> callback);

    // 状态查询

    /**
     * @brief 获取任务 ID
     */
    const std::string& id() const { return id_; }

    /**
     * @brief 获取任务名称
     */
    const std::string& name() const { return name_; }

    /**
     * @brief 获取任务状态
     */
    TaskStatus status() const { return status_; }

    /**
     * @brief 获取任务优先级
     */
    TaskPriority priority() const { return priority_; }

    /**
     * @brief 获取首选设备类型
     */
    DeviceType preferred_device() const { return preferred_device_; }

    /**
     * @brief 获取输入数据
     */
    const void* input_data() const { return input_data_; }

    /**
     * @brief 获取输出数据
     */
    void* output_data() const { return output_data_; }

    /**
     * @brief 获取数据大小
     */
    size_t data_size() const { return data_size_; }

    /**
     * @brief 获取依赖任务列表
     */
    const std::vector<std::string>& dependencies() const { return dependencies_; }

    /**
     * @brief 获取执行时间
     */
    std::chrono::microseconds execution_time() const { return execution_time_; }

    /**
     * @brief 获取使用的设备 ID
     */
    const std::string& device_used() const { return device_used_; }

    /**
     * @brief 获取错误信息
     */
    const std::string& error_message() const { return error_message_; }

    // 状态修改

    /**
     * @brief 设置任务状态
     * @param status 新状态
     */
    void set_status(TaskStatus status);

    /**
     * @brief 设置执行时间
     * @param time 执行时间
     */
    void set_execution_time(std::chrono::microseconds time);

    /**
     * @brief 设置使用的设备
     * @param device_id 设备 ID
     */
    void set_device_used(const std::string& device_id);

    /**
     * @brief 设置错误信息
     * @param message 错误信息
     */
    void set_error(const std::string& message);

    /**
     * @brief 执行完成回调
     */
    void notify_complete();

    /**
     * @brief 执行错误回调
     * @param e 异常
     */
    void notify_error(const std::exception& e);

    /**
     * @brief 检查是否可以执行
     * @return true 如果所有依赖都已完成
     */
    bool is_ready() const;

    /**
     * @brief 执行任务
     * @param device_info 设备信息
     */
    void execute(const DeviceInfo* device_info = nullptr);

    /**
     * @brief 重置任务状态
     */
    void reset();

private:
    /**
     * @brief 生成唯一 ID
     */
    static std::string generate_id();

    std::string id_;                              // 任务 ID
    std::string name_;                            // 任务名称
    TaskFunc func_;                               // 计算函数

    const void* input_data_ = nullptr;            // 输入数据
    void* output_data_ = nullptr;                 // 输出数据
    size_t data_size_ = 0;                        // 数据大小

    DeviceType preferred_device_ = DeviceType::CPU;  // 首选设备
    TaskPriority priority_ = TaskPriority::Normal;   // 优先级

    std::vector<std::string> dependencies_;       // 依赖任务
    std::vector<std::string> completed_deps_;     // 已完成的依赖

    TaskStatus status_ = TaskStatus::Created;     // 任务状态
    std::chrono::microseconds execution_time_{0}; // 执行时间
    std::string device_used_;                     // 使用的设备
    std::string error_message_;                   // 错误信息

    std::function<void(const Task&)> on_complete_;                    // 完成回调
    std::function<void(const Task&, const std::exception&)> on_error_; // 错误回调

    mutable std::mutex mutex_;                    // 线程安全
};

/**
 * @brief 任务管理器
 *
 * ⭐ 重点: 理解任务生命周期管理
 *
 * 💡 思考: 为什么使用单例模式？有什么优缺点？
 */
class TaskManager {
public:
    /**
     * @brief 获取单例实例
     */
    static TaskManager& instance();

    /**
     * @brief 创建任务
     * @param name 任务名称
     * @param func 计算函数
     * @return 任务指针
     */
    std::shared_ptr<Task> create_task(const std::string& name, TaskFunc func);

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
     * @brief 获取任务
     * @param task_id 任务 ID
     * @return 任务指针
     */
    std::shared_ptr<Task> get_task(const std::string& task_id);

    /**
     * @brief 获取任务状态
     * @param task_id 任务 ID
     * @return 任务状态
     */
    TaskStatus get_task_status(const std::string& task_id);

    /**
     * @brief 获取任务列表
     * @param status 任务状态过滤
     * @return 任务列表
     */
    std::vector<std::shared_ptr<Task>> get_tasks(TaskStatus status = TaskStatus::Created);

    /**
     * @brief 获取任务统计
     */
    ExecutionStats get_stats() const;

    /**
     * @brief 清除已完成的任务
     */
    void clear_completed();

private:
    TaskManager() = default;
    ~TaskManager() = default;

    // 禁止拷贝和移动
    TaskManager(const TaskManager&) = delete;
    TaskManager& operator=(const TaskManager&) = delete;

    std::unordered_map<std::string, std::shared_ptr<Task>> tasks_;
    mutable std::mutex mutex_;
    ExecutionStats stats_;
};

} // namespace heterogeneous
