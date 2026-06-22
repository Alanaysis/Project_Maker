/**
 * @file task.cpp
 * @brief 任务实现
 */

#include "heterogeneous/task.h"
#include <sstream>
#include <random>
#include <algorithm>

namespace heterogeneous {

// Task 实现

Task::Task(const std::string& name, TaskFunc func)
    : id_(generate_id())
    , name_(name)
    , func_(std::move(func))
    , status_(TaskStatus::Created)
    , priority_(TaskPriority::Normal)
    , preferred_device_(DeviceType::CPU) {}

std::string Task::generate_id() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<> dis(0, 15);

    std::stringstream ss;
    ss << "task_";
    for (int i = 0; i < 8; i++) {
        ss << std::hex << dis(gen);
    }
    return ss.str();
}

Task& Task::set_input(const void* data, size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    input_data_ = data;
    data_size_ = size;
    return *this;
}

Task& Task::set_output(void* data, size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);
    output_data_ = data;
    return *this;
}

Task& Task::prefer_device(DeviceType type) {
    std::lock_guard<std::mutex> lock(mutex_);
    preferred_device_ = type;
    return *this;
}

Task& Task::set_priority(TaskPriority priority) {
    std::lock_guard<std::mutex> lock(mutex_);
    priority_ = priority;
    return *this;
}

Task& Task::add_dependency(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    dependencies_.push_back(task_id);
    return *this;
}

Task& Task::on_complete(std::function<void(const Task&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    on_complete_ = std::move(callback);
    return *this;
}

Task& Task::on_error(std::function<void(const Task&, const std::exception&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    on_error_ = std::move(callback);
    return *this;
}

void Task::set_status(TaskStatus status) {
    std::lock_guard<std::mutex> lock(mutex_);
    status_ = status;
}

void Task::set_execution_time(std::chrono::microseconds time) {
    std::lock_guard<std::mutex> lock(mutex_);
    execution_time_ = time;
}

void Task::set_device_used(const std::string& device_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    device_used_ = device_id;
}

void Task::set_error(const std::string& message) {
    std::lock_guard<std::mutex> lock(mutex_);
    error_message_ = message;
    status_ = TaskStatus::Failed;
}

void Task::notify_complete() {
    std::function<void(const Task&)> callback;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        callback = on_complete_;
    }
    if (callback) {
        callback(*this);
    }
}

void Task::notify_error(const std::exception& e) {
    std::function<void(const Task&, const std::exception&)> callback;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        callback = on_error_;
    }
    if (callback) {
        callback(*this, e);
    }
}

bool Task::is_ready() const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (status_ != TaskStatus::Created && status_ != TaskStatus::Ready) {
        return false;
    }

    // 检查所有依赖是否完成
    for (const auto& dep : dependencies_) {
        if (std::find(completed_deps_.begin(), completed_deps_.end(), dep) ==
            completed_deps_.end()) {
            return false;
        }
    }

    return true;
}

void Task::execute(const DeviceInfo* device_info) {
    if (!func_) {
        throw TaskException("Task function is not set", ErrorCode::TaskExecutionFailed);
    }

    auto start_time = std::chrono::steady_clock::now();
    {
        std::lock_guard<std::mutex> lock(mutex_);
        status_ = TaskStatus::Running;
    }

    try {
        func_(input_data_, output_data_, data_size_, device_info);
        {
            std::lock_guard<std::mutex> lock(mutex_);
            status_ = TaskStatus::Completed;
        }
    } catch (const std::exception& e) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            status_ = TaskStatus::Failed;
            error_message_ = e.what();
        }
        notify_error(e);
        throw;
    }

    auto end_time = std::chrono::steady_clock::now();
    {
        std::lock_guard<std::mutex> lock(mutex_);
        execution_time_ = std::chrono::duration_cast<std::chrono::microseconds>(
            end_time - start_time
        );
    }

    notify_complete();
}

void Task::reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    status_ = TaskStatus::Created;
    execution_time_ = std::chrono::microseconds{0};
    device_used_.clear();
    error_message_.clear();
    completed_deps_.clear();
}

// TaskManager 实现

TaskManager& TaskManager::instance() {
    static TaskManager instance;
    return instance;
}

std::shared_ptr<Task> TaskManager::create_task(const std::string& name, TaskFunc func) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto task = std::make_shared<Task>(name, std::move(func));
    tasks_[task->id()] = task;
    return task;
}

bool TaskManager::submit_task(std::shared_ptr<Task> task) {
    if (!task) {
        return false;
    }

    std::lock_guard<std::mutex> lock(mutex_);
    if (tasks_.find(task->id()) == tasks_.end()) {
        tasks_[task->id()] = task;
    }

    task->set_status(TaskStatus::Ready);
    return true;
}

bool TaskManager::wait_for_task(const std::string& task_id,
                                 std::chrono::milliseconds timeout) {
    std::shared_ptr<Task> task;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = tasks_.find(task_id);
        if (it == tasks_.end()) {
            return false;
        }
        task = it->second;
    }

    auto start = std::chrono::steady_clock::now();
    while (task->status() != TaskStatus::Completed &&
           task->status() != TaskStatus::Failed &&
           task->status() != TaskStatus::Cancelled) {
        if (timeout != std::chrono::milliseconds::max()) {
            auto now = std::chrono::steady_clock::now();
            auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(now - start);
            if (elapsed >= timeout) {
                return false;
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }

    return task->status() == TaskStatus::Completed;
}

void TaskManager::wait_for_all() {
    std::vector<std::shared_ptr<Task>> tasks;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        for (auto& pair : tasks_) {
            tasks.push_back(pair.second);
        }
    }

    for (auto& task : tasks) {
        wait_for_task(task->id());
    }
}

bool TaskManager::cancel_task(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = tasks_.find(task_id);
    if (it == tasks_.end()) {
        return false;
    }

    auto& task = it->second;
    if (task->status() == TaskStatus::Running) {
        task->set_status(TaskStatus::Cancelled);
        return true;
    }

    return false;
}

std::shared_ptr<Task> TaskManager::get_task(const std::string& task_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = tasks_.find(task_id);
    if (it == tasks_.end()) {
        return nullptr;
    }
    return it->second;
}

TaskStatus TaskManager::get_task_status(const std::string& task_id) {
    auto task = get_task(task_id);
    if (!task) {
        throw TaskException("Task not found: " + task_id, ErrorCode::TaskCreationFailed);
    }
    return task->status();
}

std::vector<std::shared_ptr<Task>> TaskManager::get_tasks(TaskStatus status) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::shared_ptr<Task>> result;

    for (auto& pair : tasks_) {
        if (pair.second->status() == status) {
            result.push_back(pair.second);
        }
    }

    return result;
}

ExecutionStats TaskManager::get_stats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return stats_;
}

void TaskManager::clear_completed() {
    std::lock_guard<std::mutex> lock(mutex_);
    for (auto it = tasks_.begin(); it != tasks_.end();) {
        if (it->second->status() == TaskStatus::Completed ||
            it->second->status() == TaskStatus::Failed ||
            it->second->status() == TaskStatus::Cancelled) {
            it = tasks_.erase(it);
        } else {
            ++it;
        }
    }
}

} // namespace heterogeneous
