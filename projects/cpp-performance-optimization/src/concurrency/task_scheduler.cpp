/**
 * @file task_scheduler.cpp
 * @brief 任务调度器示例
 */

#include <iostream>
#include <vector>
#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>
#include <chrono>
#include <iomanip>

class Timer
{
public:
    using Clock = std::chrono::high_resolution_clock;
    Timer() : start_(Clock::now()) {}
    void reset() { start_ = Clock::now(); }
    double elapsedMs() const {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            Clock::now() - start_).count() / 1e6;
    }
private:
    Clock::time_point start_;
};

/**
 * @brief 简单的优先级任务调度器
 */
class PriorityScheduler
{
public:
    explicit PriorityScheduler(size_t num_threads) : stop_(false)
    {
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this]() {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock<std::mutex> lock(mutex_);
                        condition_.wait(lock, [this]() {
                            return stop_ || !tasks_.empty();
                        });
                        if (stop_ && tasks_.empty()) return;
                        task = std::move(const_cast<std::function<void()>&>(tasks_.top().task));
                        tasks_.pop();
                    }
                    task();
                }
            });
        }
    }

    ~PriorityScheduler()
    {
        {
            std::unique_lock<std::mutex> lock(mutex_);
            stop_ = true;
        }
        condition_.notify_all();
        for (auto& w : workers_) w.join();
    }

    void enqueue(std::function<void()> task, int priority = 0)
    {
        {
            std::unique_lock<std::mutex> lock(mutex_);
            tasks_.push({priority, std::move(task)});
        }
        condition_.notify_one();
    }

private:
    struct PriorityTask {
        int priority;
        std::function<void()> task;
        bool operator<(const PriorityTask& other) const {
            return priority < other.priority;
        }
    };

    std::vector<std::thread> workers_;
    std::priority_queue<PriorityTask> tasks_;
    std::mutex mutex_;
    std::condition_variable condition_;
    bool stop_;
};

void demonstratePriorityScheduler()
{
    std::cout << "=== 优先级任务调度 ===\n\n";

    PriorityScheduler scheduler(2);
    std::mutex print_mutex;

    for (int i = 0; i < 10; ++i) {
        int priority = i % 3;
        scheduler.enqueue([i, priority, &print_mutex]() {
            std::lock_guard<std::mutex> lock(print_mutex);
            std::cout << "任务 " << i << " (优先级=" << priority << ")\n";
        }, priority);
    }

    std::this_thread::sleep_for(std::chrono::milliseconds(100));
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  任务调度器\n";
    std::cout << "========================================\n\n";
    demonstratePriorityScheduler();
    std::cout << "\n总结: 优先级调度器可以保证重要任务优先执行。\n";
    return 0;
}
