/**
 * @file executor.cpp
 * @brief 执行器实现
 */

#include "heterogeneous/executor.h"
#include <chrono>

namespace heterogeneous {

// Executor 基类实现

Executor::Executor(std::shared_ptr<Device> device)
    : device_(device) {}

Executor::~Executor() = default;

TaskResult Executor::execute(std::shared_ptr<Task> task) {
    TaskResult result;
    auto start_time = std::chrono::steady_clock::now();

    try {
        // 准备数据
        prepare_data(task);

        // 执行计算
        compute(task);

        // 收集结果
        collect_result(task);

        result.success = true;
        result.error_code = ErrorCode::Success;
    } catch (const std::exception& e) {
        result.success = false;
        result.error_code = ErrorCode::TaskExecutionFailed;
        result.error_message = e.what();
    }

    auto end_time = std::chrono::steady_clock::now();
    result.execution_time = std::chrono::duration_cast<std::chrono::microseconds>(
        end_time - start_time
    );
    result.device_used = device_->id();

    // 更新统计
    {
        std::lock_guard<std::mutex> lock(stats_mutex_);
        stats_.total_tasks_executed++;
        if (result.success) {
            stats_.successful_tasks++;
        } else {
            stats_.failed_tasks++;
        }
        stats_.total_execution_time += result.execution_time;
        if (stats_.total_tasks_executed > 0) {
            stats_.avg_execution_time = stats_.total_execution_time / stats_.total_tasks_executed;
        }
    }

    return result;
}

std::vector<TaskResult> Executor::execute_batch(
    const std::vector<std::shared_ptr<Task>>& tasks) {
    std::vector<TaskResult> results;
    results.reserve(tasks.size());

    for (auto& task : tasks) {
        results.push_back(execute(task));
    }

    return results;
}

std::future<TaskResult> Executor::execute_async(std::shared_ptr<Task> task) {
    return std::async(std::launch::async, [this, task]() {
        return execute(task);
    });
}

void Executor::prepare_data(std::shared_ptr<Task> task) {
    // 默认实现: 不需要特殊准备
}

void Executor::compute(std::shared_ptr<Task> task) {
    // 默认实现: 调用设备执行
    device_->execute_task(task);
}

void Executor::collect_result(std::shared_ptr<Task> task) {
    // 默认实现: 不需要特殊收集
}

// CPUExecutor 实现

CPUExecutor::CPUExecutor(std::shared_ptr<Device> device)
    : Executor(device)
    , thread_pool_size_(std::thread::hardware_concurrency()) {}

CPUExecutor::~CPUExecutor() = default;

TaskResult CPUExecutor::execute(std::shared_ptr<Task> task) {
    // CPU 执行器直接使用基类实现
    return Executor::execute(task);
}

// GPUExecutor 实现

GPUExecutor::GPUExecutor(std::shared_ptr<Device> device)
    : Executor(device) {}

GPUExecutor::~GPUExecutor() {
    // 释放设备内存缓冲区
    if (input_buffer_) {
        device_->deallocate(input_buffer_);
    }
    if (output_buffer_) {
        device_->deallocate(output_buffer_);
    }
}

TaskResult GPUExecutor::execute(std::shared_ptr<Task> task) {
    TaskResult result;
    auto start_time = std::chrono::steady_clock::now();

    try {
        // 1. 传输数据到设备
        transfer_to_device(task);

        // 2. 在设备上执行计算
        compute_on_device(task);

        // 3. 从设备传输结果
        transfer_from_device(task);

        result.success = true;
        result.error_code = ErrorCode::Success;
    } catch (const std::exception& e) {
        result.success = false;
        result.error_code = ErrorCode::TaskExecutionFailed;
        result.error_message = e.what();
    }

    auto end_time = std::chrono::steady_clock::now();
    result.execution_time = std::chrono::duration_cast<std::chrono::microseconds>(
        end_time - start_time
    );
    result.device_used = device_->id();

    // 更新统计
    {
        std::lock_guard<std::mutex> lock(stats_mutex_);
        stats_.total_tasks_executed++;
        if (result.success) {
            stats_.successful_tasks++;
        } else {
            stats_.failed_tasks++;
        }
        stats_.total_execution_time += result.execution_time;
        if (stats_.total_tasks_executed > 0) {
            stats_.avg_execution_time = stats_.total_execution_time / stats_.total_tasks_executed;
        }
    }

    return result;
}

void GPUExecutor::transfer_to_device(std::shared_ptr<Task> task) {
    if (!task->input_data() || task->data_size() == 0) {
        return;
    }

    // 确保设备缓冲区足够大
    if (buffer_size_ < task->data_size()) {
        if (input_buffer_) {
            device_->deallocate(input_buffer_);
        }
        if (output_buffer_) {
            device_->deallocate(output_buffer_);
        }

        input_buffer_ = device_->allocate(task->data_size());
        output_buffer_ = device_->allocate(task->data_size());
        buffer_size_ = task->data_size();
    }

    // 传输输入数据到设备
    device_->copy_to_device(input_buffer_, task->input_data(), task->data_size());
}

void GPUExecutor::compute_on_device(std::shared_ptr<Task> task) {
    // 创建设备特定的任务副本
    // 注意: 这里简化处理，实际实现需要更复杂的设备特定逻辑
    device_->execute_task(task);
}

void GPUExecutor::transfer_from_device(std::shared_ptr<Task> task) {
    if (!task->output_data() || task->data_size() == 0) {
        return;
    }

    // 传输结果回主机
    device_->copy_from_device(task->output_data(), output_buffer_, task->data_size());
}

#ifdef HETEROGENEOUS_ENABLE_CUDA

// CUDAExecutor 实现

CUDAExecutor::CUDAExecutor(std::shared_ptr<Device> device)
    : GPUExecutor(device)
    , stream_(nullptr) {
    // 实际实现需要: cudaStreamCreate(&stream_);
}

CUDAExecutor::~CUDAExecutor() {
    // 实际实现需要: cudaStreamDestroy(stream_);
}

TaskResult CUDAExecutor::execute(std::shared_ptr<Task> task) {
    // 使用 CUDA 流实现异步执行
    return GPUExecutor::execute(task);
}

void CUDAExecutor::transfer_to_device(std::shared_ptr<Task> task) {
    // 使用 CUDA 异步传输
    GPUExecutor::transfer_to_device(task);
}

void CUDAExecutor::compute_on_device(std::shared_ptr<Task> task) {
    // 启动 CUDA 内核
    GPUExecutor::compute_on_device(task);
}

void CUDAExecutor::transfer_from_device(std::shared_ptr<Task> task) {
    // 使用 CUDA 异步传输
    GPUExecutor::transfer_from_device(task);
}

#endif // HETEROGENEOUS_ENABLE_CUDA

#ifdef HETEROGENEOUS_ENABLE_OPENCL

// OpenCLExecutor 实现

OpenCLExecutor::OpenCLExecutor(std::shared_ptr<Device> device)
    : GPUExecutor(device) {}

OpenCLExecutor::~OpenCLExecutor() = default;

TaskResult OpenCLExecutor::execute(std::shared_ptr<Task> task) {
    // 使用 OpenCL 命令队列实现异步执行
    return GPUExecutor::execute(task);
}

void OpenCLExecutor::transfer_to_device(std::shared_ptr<Task> task) {
    GPUExecutor::transfer_to_device(task);
}

void OpenCLExecutor::compute_on_device(std::shared_ptr<Task> task) {
    // 启动 OpenCL 内核
    GPUExecutor::compute_on_device(task);
}

void OpenCLExecutor::transfer_from_device(std::shared_ptr<Task> task) {
    GPUExecutor::transfer_from_device(task);
}

#endif // HETEROGENEOUS_ENABLE_OPENCL

// ExecutorFactory 实现

std::unique_ptr<Executor> ExecutorFactory::create(std::shared_ptr<Device> device) {
    if (!device) {
        return nullptr;
    }

    switch (device->type()) {
        case DeviceType::CPU:
            return std::make_unique<CPUExecutor>(device);

#ifdef HETEROGENEOUS_ENABLE_CUDA
        case DeviceType::GPU_CUDA:
            return std::make_unique<CUDAExecutor>(device);
#endif

#ifdef HETEROGENEOUS_ENABLE_OPENCL
        case DeviceType::GPU_OPENCL:
            return std::make_unique<OpenCLExecutor>(device);
#endif

        default:
            return std::make_unique<CPUExecutor>(device);
    }
}

// Pipeline 实现

Pipeline::Pipeline() = default;
Pipeline::~Pipeline() = default;

Pipeline& Pipeline::add_stage(const std::string& name, std::unique_ptr<Executor> executor) {
    stages_.push_back({name, std::move(executor)});
    return *this;
}

std::vector<TaskResult> Pipeline::execute(const std::vector<std::shared_ptr<Task>>& tasks) {
    std::vector<TaskResult> results;
    results.reserve(tasks.size());

    for (auto& task : tasks) {
        TaskResult final_result;

        // 依次通过各个阶段
        for (auto& stage : stages_) {
            auto result = stage.executor->execute(task);
            if (!result.success) {
                final_result = result;
                break;
            }
            final_result = result;
        }

        results.push_back(final_result);
    }

    return results;
}

// ParallelExecutor 实现

ParallelExecutor::ParallelExecutor(std::vector<std::unique_ptr<Executor>> executors)
    : executors_(std::move(executors)) {}

ParallelExecutor::~ParallelExecutor() = default;

std::vector<TaskResult> ParallelExecutor::execute(
    const std::vector<std::shared_ptr<Task>>& tasks) {
    std::vector<TaskResult> results(tasks.size());

    // 使用线程池并行执行
    std::vector<std::future<void>> futures;
    futures.reserve(tasks.size());

    for (size_t i = 0; i < tasks.size(); i++) {
        futures.push_back(std::async(std::launch::async, [this, i, &tasks, &results]() {
            // 轮询选择执行器
            size_t executor_idx = current_executor_++ % executors_.size();
            results[i] = executors_[executor_idx]->execute(tasks[i]);
        }));
    }

    // 等待所有任务完成
    for (auto& future : futures) {
        future.wait();
    }

    return results;
}

} // namespace heterogeneous
