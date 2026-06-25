/**
 * @file thread_pool.cpp
 * @brief 线程池实现示例
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
 * @brief 简单线程池实现
 */
class ThreadPool
{
public:
    explicit ThreadPool(size_t num_threads) : stop_(false)
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
                        task = std::move(tasks_.front());
                        tasks_.pop();
                    }
                    task();
                }
            });
        }
    }

    ~ThreadPool()
    {
        {
            std::unique_lock<std::mutex> lock(mutex_);
            stop_ = true;
        }
        condition_.notify_all();
        for (auto& w : workers_) w.join();
    }

    template<typename F, typename... Args>
    auto enqueue(F&& f, Args&&... args)
        -> std::future<typename std::invoke_result<F, Args...>::type>
    {
        using return_type = typename std::invoke_result<F, Args...>::type;
        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );
        std::future<return_type> result = task->get_future();
        {
            std::unique_lock<std::mutex> lock(mutex_);
            tasks_.emplace([task]() { (*task)(); });
        }
        condition_.notify_one();
        return result;
    }

private:
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    std::mutex mutex_;
    std::condition_variable condition_;
    bool stop_;
};

void demonstrateThreadPool()
{
    std::cout << "=== 线程池 vs 创建线程 ===\n\n";

    const size_t N = 1000;
    const size_t num_threads = 4;

    // 创建新线程
    {
        Timer timer;
        for (size_t i = 0; i < N; ++i) {
            std::thread t([]() {
                volatile int sum = 0;
                for (int j = 0; j < 10000; ++j) sum += j;
                (void)sum;
            });
            t.join();
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "创建线程 " << N << " 次: " << time << " ms\n";
    }

    // 使用线程池
    {
        ThreadPool pool(num_threads);
        Timer timer;
        std::vector<std::future<void>> futures;
        for (size_t i = 0; i < N; ++i) {
            futures.push_back(pool.enqueue([]() {
                volatile int sum = 0;
                for (int j = 0; j < 10000; ++j) sum += j;
                (void)sum;
            }));
        }
        for (auto& f : futures) f.get();
        double time = timer.elapsedMs();
        std::cout << "线程池 " << N << " 次:   " << time << " ms\n";
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  线程池\n";
    std::cout << "========================================\n\n";
    demonstrateThreadPool();
    std::cout << "\n总结: 线程池复用线程，避免频繁创建销毁的开销。\n";
    return 0;
}
