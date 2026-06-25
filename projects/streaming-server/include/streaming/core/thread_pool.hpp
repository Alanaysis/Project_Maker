#pragma once

/**
 * @file thread_pool.hpp
 * @brief 线程池实现
 *
 * 实现高效的线程池，支持：
 * - 动态线程管理
 * - 任务队列
 * - 优先级任务
 * - 任务取消
 */

#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>
#include <atomic>
#include <memory>

namespace streaming {

// 任务优先级
enum class TaskPriority {
    Low = 0,
    Normal = 1,
    High = 2,
    Critical = 3
};

/**
 * @brief 线程池
 *
 * 支持动态调整线程数量，任务优先级，以及异步任务提交。
 */
class ThreadPool {
public:
    /**
     * @brief 构造函数
     * @param min_threads 最小线程数
     * @param max_threads 最大线程数
     */
    explicit ThreadPool(uint32_t min_threads = 2, uint32_t max_threads = 8);
    ~ThreadPool();

    // 禁止拷贝
    ThreadPool(const ThreadPool&) = delete;
    ThreadPool& operator=(const ThreadPool&) = delete;

    /**
     * @brief 启动线程池
     */
    void start();

    /**
     * @brief 停止线程池
     * @param wait 是否等待所有任务完成
     */
    void stop(bool wait = true);

    /**
     * @brief 提交任务
     * @param func 任务函数
     * @param priority 任务优先级
     * @return future 对象
     */
    template<typename F, typename... Args>
    auto submit(F&& func, Args&&... args, TaskPriority priority = TaskPriority::Normal)
        -> std::future<typename std::result_of<F(Args...)>::type>;

    /**
     * @brief 提交任务（无返回值）
     * @param func 任务函数
     * @param priority 任务优先级
     */
    void submit_void(std::function<void()> func, TaskPriority priority = TaskPriority::Normal);

    /**
     * @brief 等待所有任务完成
     */
    void wait_all();

    /**
     * @brief 获取任务队列大小
     */
    size_t get_queue_size() const;

    /**
     * @brief 获取活跃线程数
     */
    uint32_t get_active_thread_count() const;

    /**
     * @brief 获取总线程数
     */
    uint32_t get_thread_count() const { return threads_.size(); }

    /**
     * @brief 动态调整线程数
     */
    void resize(uint32_t min_threads, uint32_t max_threads);

private:
    // 任务包装器
    struct TaskWrapper {
        std::function<void()> func;
        TaskPriority priority;
        uint64_t id;

        bool operator<(const TaskWrapper& other) const {
            return priority < other.priority;
        }
    };

    // 工作线程函数
    void worker_thread();

    // 线程管理
    void add_thread();
    void remove_thread();

    uint32_t min_threads_;
    uint32_t max_threads_;

    std::vector<std::thread> threads_;
    std::priority_queue<TaskWrapper> task_queue_;
    mutable std::mutex queue_mutex_;
    std::condition_variable condition_;
    std::condition_variable wait_condition_;

    std::atomic<bool> running_{false};
    std::atomic<uint32_t> active_threads_{0};
    std::atomic<uint64_t> next_task_id_{0};
    std::atomic<uint32_t> pending_tasks_{0};
};

/**
 * @brief 并行任务执行器
 *
 * 将大任务分解为多个小任务并行执行。
 */
class ParallelExecutor {
public:
    /**
     * @brief 并行执行循环
     * @param begin 起始索引
     * @param end 结束索引
     * @param func 执行函数
     */
    template<typename F>
    static void parallel_for(size_t begin, size_t end, F&& func, size_t grain_size = 1000);

    /**
     * @brief 并行执行任务
     * @param tasks 任务列表
     * @return 结果列表
     */
    template<typename T, typename F>
    static std::vector<T> parallel_map(const std::vector<T>& items, F&& func);

private:
    static ThreadPool& get_pool();
};

// ============================================================================
// 模板实现
// ============================================================================

template<typename F, typename... Args>
auto ThreadPool::submit(F&& func, Args&&... args, TaskPriority priority)
    -> std::future<typename std::result_of<F(Args...)>::type>
{
    using return_type = typename std::result_of<F(Args...)>::type;

    auto task = std::make_shared<std::packaged_task<return_type()>>(
        std::bind(std::forward<F>(func), std::forward<Args>(args)...)
    );

    std::future<return_type> result = task->get_future();

    {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        if (!running_) {
            throw std::runtime_error("ThreadPool is not running");
        }

        TaskWrapper wrapper;
        wrapper.func = [task]() { (*task)(); };
        wrapper.priority = priority;
        wrapper.id = next_task_id_++;

        task_queue_.push(wrapper);
        pending_tasks_++;
    }

    condition_.notify_one();
    return result;
}

template<typename F>
void ParallelExecutor::parallel_for(size_t begin, size_t end, F&& func, size_t grain_size) {
    if (begin >= end) return;

    size_t total = end - begin;
    size_t num_tasks = (total + grain_size - 1) / grain_size;

    std::vector<std::future<void>> futures;
    futures.reserve(num_tasks);

    for (size_t i = 0; i < num_tasks; ++i) {
        size_t task_begin = begin + i * grain_size;
        size_t task_end = std::min(task_begin + grain_size, end);

        futures.push_back(get_pool().submit([=]() {
            for (size_t j = task_begin; j < task_end; ++j) {
                func(j);
            }
        }));
    }

    for (auto& future : futures) {
        future.get();
    }
}

template<typename T, typename F>
std::vector<T> ParallelExecutor::parallel_map(const std::vector<T>& items, F&& func) {
    std::vector<T> results(items.size());

    parallel_for(0, items.size(), [&](size_t i) {
        results[i] = func(items[i]);
    });

    return results;
}

} // namespace streaming
