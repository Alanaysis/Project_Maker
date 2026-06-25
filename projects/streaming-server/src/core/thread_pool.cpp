/**
 * @file thread_pool.cpp
 * @brief 线程池实现
 */

#include "streaming/core/thread_pool.hpp"
#include "streaming/monitor/logger.hpp"

#include <algorithm>

namespace streaming {

// ============================================================================
// ThreadPool 实现
// ============================================================================

ThreadPool::ThreadPool(uint32_t min_threads, uint32_t max_threads)
    : min_threads_(min_threads), max_threads_(max_threads) {
    if (max_threads_ < min_threads_) {
        max_threads_ = min_threads_;
    }
}

ThreadPool::~ThreadPool() {
    stop(true);
}

void ThreadPool::start() {
    if (running_) return;

    running_ = true;

    // 创建最小线程数
    for (uint32_t i = 0; i < min_threads_; ++i) {
        add_thread();
    }

    LOG_INFO("ThreadPool started with " + std::to_string(min_threads_) + " threads");
}

void ThreadPool::stop(bool wait) {
    if (!running_) return;

    running_ = false;
    condition_.notify_all();

    if (wait) {
        // 等待所有任务完成
        std::unique_lock<std::mutex> lock(queue_mutex_);
        wait_condition_.wait(lock, [this]() {
            return pending_tasks_ == 0 && task_queue_.empty();
        });
    }

    // 等待所有线程结束
    for (auto& thread : threads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    threads_.clear();

    LOG_INFO("ThreadPool stopped");
}

void ThreadPool::submit_void(std::function<void()> func, TaskPriority priority) {
    if (!running_) {
        throw std::runtime_error("ThreadPool is not running");
    }

    {
        std::unique_lock<std::mutex> lock(queue_mutex_);

        TaskWrapper wrapper;
        wrapper.func = std::move(func);
        wrapper.priority = priority;
        wrapper.id = next_task_id_++;

        task_queue_.push(wrapper);
        pending_tasks_++;
    }

    condition_.notify_one();
}

void ThreadPool::wait_all() {
    std::unique_lock<std::mutex> lock(queue_mutex_);
    wait_condition_.wait(lock, [this]() {
        return pending_tasks_ == 0 && task_queue_.empty();
    });
}

size_t ThreadPool::get_queue_size() const {
    std::lock_guard<std::mutex> lock(queue_mutex_);
    return task_queue_.size();
}

uint32_t ThreadPool::get_active_thread_count() const {
    return active_threads_;
}

void ThreadPool::resize(uint32_t min_threads, uint32_t max_threads) {
    min_threads_ = min_threads;
    max_threads_ = std::max(max_threads, min_threads);

    // 添加线程
    while (threads_.size() < min_threads_ && running_) {
        add_thread();
    }

    LOG_INFO("ThreadPool resized: min=" + std::to_string(min_threads_) +
             ", max=" + std::to_string(max_threads_));
}

void ThreadPool::worker_thread() {
    while (running_) {
        TaskWrapper task;
        bool has_task = false;

        {
            std::unique_lock<std::mutex> lock(queue_mutex_);

            // 等待任务或停止信号
            condition_.wait(lock, [this]() {
                return !running_ || !task_queue_.empty();
            });

            if (!running_ && task_queue_.empty()) {
                break;
            }

            if (!task_queue_.empty()) {
                task = std::move(const_cast<TaskWrapper&>(task_queue_.top()));
                task_queue_.pop();
                has_task = true;
            }
        }

        if (has_task) {
            active_threads_++;

            try {
                task.func();
            } catch (const std::exception& e) {
                LOG_ERROR("Task exception: " + std::string(e.what()));
            } catch (...) {
                LOG_ERROR("Unknown task exception");
            }

            active_threads_--;
            pending_tasks_--;

            // 通知等待者
            if (pending_tasks_ == 0) {
                wait_condition_.notify_all();
            }
        }
    }
}

void ThreadPool::add_thread() {
    threads_.emplace_back(&ThreadPool::worker_thread, this);
}

void ThreadPool::remove_thread() {
    // 实现线程移除逻辑
    // 这里简化处理，实际可以通过设置标志让线程退出
}

// ============================================================================
// ParallelExecutor 实现
// ============================================================================

ThreadPool& ParallelExecutor::get_pool() {
    static ThreadPool pool(2, std::thread::hardware_concurrency());
    static bool initialized = false;

    if (!initialized) {
        pool.start();
        initialized = true;
    }

    return pool;
}

} // namespace streaming
