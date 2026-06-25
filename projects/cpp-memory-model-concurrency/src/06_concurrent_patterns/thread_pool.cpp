/**
 * 线程池 (Thread Pool)
 *
 * 线程池的特点：
 * 1. 复用线程，减少创建开销
 * 2. 限制并发数量
 * 3. 任务队列管理
 * 4. 支持返回值
 *
 * 编译：g++ -std=c++17 -pthread thread_pool.cpp -o thread_pool
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
#include <atomic>

class ThreadPool {
public:
    explicit ThreadPool(size_t num_threads) : stop_(false) {
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this]() {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock lock(mutex_);
                        cv_.wait(lock, [this]() {
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

    ~ThreadPool() {
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

    template<typename F, typename... Args>
    auto submit(F&& f, Args&&... args) -> std::future<std::invoke_result_t<F, Args...>> {
        using ReturnType = std::invoke_result_t<F, Args...>;

        auto task = std::make_shared<std::packaged_task<ReturnType()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );

        std::future<ReturnType> result = task->get_future();
        {
            std::lock_guard lock(mutex_);
            if (stop_) throw std::runtime_error("ThreadPool is stopped");
            tasks_.emplace([task]() { (*task)(); });
        }
        cv_.notify_one();
        return result;
    }

    size_t queue_size() const {
        std::lock_guard lock(mutex_);
        return tasks_.size();
    }

private:
    std::vector<std::thread> workers_;
    std::queue<std::function<void()>> tasks_;
    mutable std::mutex mutex_;
    std::condition_variable cv_;
    bool stop_;
};

// 基本测试
void basic_test() {
    std::cout << "=== 基本测试 ===" << std::endl;

    ThreadPool pool(4);

    // 提交任务
    std::vector<std::future<int>> results;
    for (int i = 0; i < 8; ++i) {
        results.emplace_back(pool.submit([i]() {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            return i * i;
        }));
    }

    // 获取结果
    for (auto& result : results) {
        std::cout << result.get() << " ";
    }
    std::cout << std::endl;
}

// 并发测试
void concurrent_test() {
    std::cout << "\n=== 并发测试 ===" << std::endl;

    ThreadPool pool(4);
    std::atomic<int> counter{0};

    const int num_tasks = 100;
    std::vector<std::future<void>> futures;

    for (int i = 0; i < num_tasks; ++i) {
        futures.emplace_back(pool.submit([&counter]() {
            counter.fetch_add(1);
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }));
    }

    for (auto& future : futures) {
        future.get();
    }

    std::cout << "完成任务数: " << counter.load() << std::endl;
}

// 性能测试
void performance_test() {
    std::cout << "\n=== 性能测试 ===" << std::endl;

    const int num_tasks = 1000;

    // 线程池
    {
        ThreadPool pool(4);
        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::future<int>> futures;
        for (int i = 0; i < num_tasks; ++i) {
            futures.emplace_back(pool.submit([i]() {
                return i * i;
            }));
        }

        for (auto& future : futures) {
            future.get();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "线程池: " << time.count() << " ms" << std::endl;
    }

    // 直接创建线程
    {
        auto start = std::chrono::high_resolution_clock::now();

        std::vector<std::thread> threads;
        std::vector<int> results(num_tasks);

        for (int i = 0; i < num_tasks; ++i) {
            threads.emplace_back([&results, i]() {
                results[i] = i * i;
            });
        }

        for (auto& t : threads) {
            t.join();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto time = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
        std::cout << "直接线程: " << time.count() << " ms" << std::endl;
    }
}

int main() {
    std::cout << "C++ 并发模式：线程池" << std::endl;
    std::cout << "=====================\n" << std::endl;

    basic_test();
    concurrent_test();
    performance_test();

    return 0;
}
