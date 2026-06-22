/**
 * @file scheduler.cpp
 * @brief 调度器实现
 */

#include "heterogeneous/scheduler.h"
#include <algorithm>
#include <chrono>

namespace heterogeneous {

// Scheduler 基类实现

Scheduler::Scheduler(const SchedulerConfig& config)
    : config_(config)
    , device_manager_(std::make_shared<DeviceManager>()) {}

Scheduler::~Scheduler() {
    shutdown();
}

bool Scheduler::initialize() {
    if (running_) {
        return true;
    }

    // 初始化设备管理器
    if (!device_manager_->initialize()) {
        return false;
    }

    running_ = true;
    scheduling_thread_ = std::thread(&Scheduler::scheduling_thread_func, this);

    return true;
}

void Scheduler::shutdown() {
    if (!running_) {
        return;
    }

    running_ = false;
    queue_cv_.notify_all();

    if (scheduling_thread_.joinable()) {
        scheduling_thread_.join();
    }

    // 通知所有等待的任务
    std::lock_guard<std::mutex> lock(promise_mutex_);
    for (auto& pair : task_promises_) {
        pair.second.set_exception(
            std::make_exception_ptr(
                TaskException("Scheduler shutdown", ErrorCode::TaskCancelled)
            )
        );
    }
    task_promises_.clear();
}

bool Scheduler::submit_task(std::shared_ptr<Task> task) {
    if (!task || !running_) {
        return false;
    }

    // 创建 promise
    {
        std::lock_guard<std::mutex> lock(promise_mutex_);
        task_promises_[task->id()] = std::promise<void>();
    }

    // 添加到队列
    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        TaskEntry entry;
        entry.task = task;
        entry.submit_time = std::chrono::steady_clock::now();
        task_queue_.push(entry);
    }

    queue_cv_.notify_one();

    // 更新统计
    {
        std::lock_guard<std::mutex> lock(stats_mutex_);
        stats_.total_tasks_scheduled++;
    }

    return true;
}

bool Scheduler::wait_for_task(const std::string& task_id,
                               std::chrono::milliseconds timeout) {
    std::future<void> future;
    {
        std::lock_guard<std::mutex> lock(promise_mutex_);
        auto it = task_promises_.find(task_id);
        if (it == task_promises_.end()) {
            return false;
        }
        future = it->second.get_future();
    }

    if (timeout == std::chrono::milliseconds::max()) {
        future.wait();
        return true;
    }

    auto status = future.wait_for(timeout);
    return status == std::future_status::ready;
}

void Scheduler::wait_for_all() {
    std::vector<std::future<void>> futures;
    {
        std::lock_guard<std::mutex> lock(promise_mutex_);
        for (auto& pair : task_promises_) {
            futures.push_back(pair.second.get_future());
        }
    }

    for (auto& future : futures) {
        future.wait();
    }
}

bool Scheduler::cancel_task(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(promise_mutex_);
    auto it = task_promises_.find(task_id);
    if (it == task_promises_.end()) {
        return false;
    }

    it->second.set_exception(
        std::make_exception_ptr(
            TaskException("Task cancelled", ErrorCode::TaskCancelled)
        )
    );
    task_promises_.erase(it);

    return true;
}

SchedulingStats Scheduler::get_stats() const {
    std::lock_guard<std::mutex> lock(stats_mutex_);
    return stats_;
}

void Scheduler::update_config(const SchedulerConfig& config) {
    config_ = config;
}

std::shared_ptr<Device> Scheduler::select_device(std::shared_ptr<Task> task) {
    // 默认实现: 选择首选设备
    auto devices = device_manager_->get_devices(task->preferred_device());
    if (!devices.empty()) {
        return devices[0];
    }

    // 降级到任何可用设备
    auto all_devices = device_manager_->get_all_devices();
    for (auto& device : all_devices) {
        if (device->is_available()) {
            return device;
        }
    }

    return nullptr;
}

void Scheduler::execute_task(std::shared_ptr<Task> task, std::shared_ptr<Device> device) {
    try {
        task->set_device_used(device->id());
        device->execute_task(task);

        // 更新统计
        {
            std::lock_guard<std::mutex> lock(stats_mutex_);
            if (device->type() == DeviceType::CPU) {
                stats_.tasks_on_cpu++;
            } else {
                stats_.tasks_on_gpu++;
            }
        }

        // 通知完成
        {
            std::lock_guard<std::mutex> lock(promise_mutex_);
            auto it = task_promises_.find(task->id());
            if (it != task_promises_.end()) {
                it->second.set_value();
                task_promises_.erase(it);
            }
        }
    } catch (const std::exception& e) {
        task->set_error(e.what());

        // 通知失败
        {
            std::lock_guard<std::mutex> lock(promise_mutex_);
            auto it = task_promises_.find(task->id());
            if (it != task_promises_.end()) {
                it->second.set_exception(std::current_exception());
                task_promises_.erase(it);
            }
        }
    }
}

void Scheduler::scheduling_thread_func() {
    while (running_) {
        std::shared_ptr<Task> task;

        // 从队列获取任务
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            queue_cv_.wait(lock, [this]() {
                return !task_queue_.empty() || !running_;
            });

            if (!running_ && task_queue_.empty()) {
                break;
            }

            if (!task_queue_.empty()) {
                task = task_queue_.top().task;
                task_queue_.pop();
            }
        }

        if (task) {
            // 调度任务
            auto device = schedule(task);
            if (device) {
                task->set_status(TaskStatus::Running);
                execute_task(task, device);
            } else {
                task->set_error("No available device");
                task->set_status(TaskStatus::Failed);

                // 通知失败
                {
                    std::lock_guard<std::mutex> lock(promise_mutex_);
                    auto it = task_promises_.find(task->id());
                    if (it != task_promises_.end()) {
                        it->second.set_exception(
                            std::make_exception_ptr(
                                TaskException("No available device",
                                            ErrorCode::NoAvailableDevice)
                            )
                        );
                        task_promises_.erase(it);
                    }
                }
            }
        }

        // 调度间隔
        std::this_thread::sleep_for(config_.scheduling_interval);
    }
}

// RoundRobinScheduler 实现

RoundRobinScheduler::RoundRobinScheduler(const SchedulerConfig& config)
    : Scheduler(config) {}

std::shared_ptr<Device> RoundRobinScheduler::schedule(std::shared_ptr<Task> task) {
    auto devices = device_manager_->get_all_devices();
    if (devices.empty()) {
        return nullptr;
    }

    // 轮询选择设备
    auto device = devices[current_device_ % devices.size()];
    current_device_++;

    return device;
}

// LoadBalancingScheduler 实现

LoadBalancingScheduler::LoadBalancingScheduler(const SchedulerConfig& config)
    : Scheduler(config) {}

std::shared_ptr<Device> LoadBalancingScheduler::schedule(std::shared_ptr<Task> task) {
    auto devices = device_manager_->get_all_devices();
    if (devices.empty()) {
        return nullptr;
    }

    // 选择负载最低的设备
    std::shared_ptr<Device> best_device = nullptr;
    double min_load = 1.0;

    for (auto& device : devices) {
        if (device->is_available()) {
            double load = calculate_load(device);
            if (load < min_load) {
                min_load = load;
                best_device = device;
            }
        }
    }

    return best_device;
}

double LoadBalancingScheduler::calculate_load(std::shared_ptr<Device> device) {
    return device->get_utilization();
}

// PriorityScheduler 实现

PriorityScheduler::PriorityScheduler(const SchedulerConfig& config)
    : Scheduler(config) {}

std::shared_ptr<Device> PriorityScheduler::schedule(std::shared_ptr<Task> task) {
    // 优先级调度: 根据任务优先级选择设备
    if (task->priority() >= TaskPriority::High) {
        // 高优先级任务优先使用 GPU
        auto gpu_devices = device_manager_->get_devices(DeviceType::GPU_CUDA);
        if (!gpu_devices.empty()) {
            return gpu_devices[0];
        }

        gpu_devices = device_manager_->get_devices(DeviceType::GPU_OPENCL);
        if (!gpu_devices.empty()) {
            return gpu_devices[0];
        }
    }

    // 默认使用任何可用设备
    return select_device(task);
}

// AdaptiveScheduler 实现

AdaptiveScheduler::AdaptiveScheduler(const SchedulerConfig& config)
    : Scheduler(config) {}

std::shared_ptr<Device> AdaptiveScheduler::schedule(std::shared_ptr<Task> task) {
    auto devices = device_manager_->get_all_devices();
    if (devices.empty()) {
        return nullptr;
    }

    // 分析任务特征
    double task_complexity = analyze_task(task);

    // 预测各设备执行时间
    std::shared_ptr<Device> best_device = nullptr;
    std::chrono::microseconds best_time = std::chrono::microseconds::max();

    for (auto& device : devices) {
        if (device->is_available()) {
            auto predicted = predict_time(task->name(), device->id());
            if (predicted < best_time) {
                best_time = predicted;
                best_device = device;
            }
        }
    }

    return best_device;
}

void AdaptiveScheduler::record_performance(const std::string& task_name,
                                            const std::string& device_id,
                                            std::chrono::microseconds execution_time) {
    std::lock_guard<std::mutex> lock(history_mutex_);
    performance_history_[task_name][device_id].add(execution_time);
}

double AdaptiveScheduler::analyze_task(std::shared_ptr<Task> task) {
    // 简单的任务复杂度分析
    // 实际实现可以根据数据大小、任务类型等因素进行更复杂的分析
    return static_cast<double>(task->data_size()) / (1024 * 1024);  // MB
}

std::chrono::microseconds AdaptiveScheduler::predict_time(
    const std::string& task_name, const std::string& device_id) {
    std::lock_guard<std::mutex> lock(history_mutex_);

    auto task_it = performance_history_.find(task_name);
    if (task_it != performance_history_.end()) {
        auto device_it = task_it->second.find(device_id);
        if (device_it != task_it->second.end()) {
            return device_it->second.avg_time;
        }
    }

    // 没有历史数据，返回默认值
    return std::chrono::microseconds{1000};  // 1ms
}

// SchedulerFactory 实现

std::unique_ptr<Scheduler> SchedulerFactory::create(
    SchedulingStrategy strategy, const SchedulerConfig& config) {
    switch (strategy) {
        case SchedulingStrategy::RoundRobin:
            return std::make_unique<RoundRobinScheduler>(config);
        case SchedulingStrategy::LoadBalancing:
            return std::make_unique<LoadBalancingScheduler>(config);
        case SchedulingStrategy::Priority:
            return std::make_unique<PriorityScheduler>(config);
        case SchedulingStrategy::Adaptive:
            return std::make_unique<AdaptiveScheduler>(config);
        default:
            return std::make_unique<RoundRobinScheduler>(config);
    }
}

} // namespace heterogeneous
