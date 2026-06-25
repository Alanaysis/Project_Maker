/**
 * 任务调度器
 *
 * 任务调度器的特点：
 * 1. 优先级队列
 * 2. 定时任务
 * 3. 周期性任务
 * 4. 任务取消
 *
 * 编译：g++ -std=c++17 -pthread task_scheduler.cpp -o task_scheduler
 */

#include <iostream>
#include <queue>
#include <vector>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <chrono>
#include <atomic>
#include <future>

// 任务优先级
enum class Priority {
    LOW = 0,
    NORMAL = 1,
    HIGH = 2
};

// 任务结构
struct Task {
    std::function<void()> func;
    Priority priority;
    std::chrono::steady_clock::time_point execute_at;

    bool operator<(const Task& other) const {
        if (priority != other.priority) {
            return priority < other.priority;
        }
        return execute_at > other.execute_at;
    }
};

// 任务调度器
class TaskScheduler {
public:
    explicit TaskScheduler(size_t num_threads = 4) : stop_(false) {
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this]() {
                while (true) {
                    Task task;
                    {
                        std::unique_lock lock(mutex_);
                        cv_.wait(lock, [this]() {
                            return stop_ || !tasks_.empty();
                        });
                        if (stop_ && tasks_.empty()) return;

                        // 等待任务执行时间
                        auto now = std::chrono::steady_clock::now();
                        if (tasks_.top().execute_at > now) {
                            cv_.wait_until(lock, tasks_.top().execute_at);
                            if (stop_) return;
                        }

                        task = tasks_.top();
                        tasks_.pop();
                    }
                    task.func();
                }
            });
        }
    }

    ~TaskScheduler() {
        {
            std::lock_guard lock(mutex_);
            stop_ = true;
        }
        cv_.notify_all();
        for (auto& worker : workers_) {
            if (worker.joinable()) {
                worker.join();
            }
        }
    }

    // 立即执行任务
    template<typename F>
    void submit(F&& func, Priority priority = Priority::NORMAL) {
        {
            std::lock_guard lock(mutex_);
            tasks_.push({
                std::forward<F>(func),
                priority,
                std::chrono::steady_clock::now()
            });
        }
        cv_.notify_one();
    }

    // 延迟执行任务
    template<typename F>
    void submit_after(F&& func, std::chrono::milliseconds delay,
                      Priority priority = Priority::NORMAL) {
        {
            std::lock_guard lock(mutex_);
            tasks_.push({
                std::forward<F>(func),
                priority,
                std::chrono::steady_clock::now() + delay
            });
        }
        cv_.notify_one();
    }

    // 周期性任务
    template<typename F>
    void submit_periodic(F&& func, std::chrono::milliseconds interval,
                         Priority priority = Priority::NORMAL) {
        auto task_func = std::make_shared<std::function<void()>>();
        *task_func = [this, func = std::forward<F>(func), interval, priority, task_func]() {
            func();
            {
                std::lock_guard lock(mutex_);
                tasks_.push({
                    *task_func,
                    priority,
                    std::chrono::steady_clock::now() + interval
                });
            }
            cv_.notify_one();
        };

        {
            std::lock_guard lock(mutex_);
            tasks_.push({
                *task_func,
                priority,
                std::chrono::steady_clock::now()
            });
        }
        cv_.notify_one();
    }

    size_t queue_size() const {
        std::lock_guard lock(mutex_);
        return tasks_.size();
    }

private:
    std::vector<std::thread> workers_;
    std::priority_queue<Task> tasks_;
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    bool stop_;
};

// 示例1：基本用法
void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    TaskScheduler scheduler(2);

    scheduler.submit([]() {
        std::cout << "普通任务" << std::endl;
    });

    scheduler.submit([]() {
        std::cout << "高优先级任务" << std::endl;
    }, Priority::HIGH);

    scheduler.submit([]() {
        std::cout << "低优先级任务" << std::endl;
    }, Priority::LOW);

    std::this_thread::sleep_for(std::chrono::milliseconds(100));
}

// 示例2：延迟任务
void delayed_tasks() {
    std::cout << "\n=== 延迟任务 ===" << std::endl;

    TaskScheduler scheduler(2);

    scheduler.submit_after([]() {
        std::cout << "延迟 100ms 的任务" << std::endl;
    }, std::chrono::milliseconds(100));

    scheduler.submit_after([]() {
        std::cout << "延迟 200ms 的任务" << std::endl;
    }, std::chrono::milliseconds(200));

    scheduler.submit_after([]() {
        std::cout << "延迟 50ms 的任务" << std::endl;
    }, std::chrono::milliseconds(50));

    std::this_thread::sleep_for(std::chrono::milliseconds(300));
}

// 示例3：周期性任务
void periodic_tasks() {
    std::cout << "\n=== 周期性任务 ===" << std::endl;

    TaskScheduler scheduler(2);
    std::atomic<int> count{0};

    scheduler.submit_periodic([&count]() {
        int c = count.fetch_add(1) + 1;
        std::cout << "周期性任务执行: " << c << std::endl;
    }, std::chrono::milliseconds(100));

    std::this_thread::sleep_for(std::chrono::milliseconds(550));
    std::cout << "总执行次数: " << count.load() << std::endl;
}

int main() {
    std::cout << "C++ 并发模式：任务调度器" << std::endl;
    std::cout << "=========================\n" << std::endl;

    basic_usage();
    delayed_tasks();
    periodic_tasks();

    return 0;
}
