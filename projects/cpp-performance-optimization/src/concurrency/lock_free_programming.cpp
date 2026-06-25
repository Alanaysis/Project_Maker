/**
 * @file lock_free_programming.cpp
 * @brief 无锁编程示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <atomic>
#include <thread>
#include <mutex>

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

void demonstrateAtomicVsMutex()
{
    std::cout << "=== 原子操作 vs 互斥锁 ===\n\n";

    const size_t N = 10000000;
    const size_t num_threads = 4;

    // 互斥锁计数器
    {
        int counter = 0;
        std::mutex mutex;
        Timer timer;
        std::vector<std::thread> threads;
        for (size_t t = 0; t < num_threads; ++t) {
            threads.emplace_back([&counter, &mutex, N, num_threads]() {
                for (size_t i = 0; i < N / num_threads; ++i) {
                    std::lock_guard<std::mutex> lock(mutex);
                    ++counter;
                }
            });
        }
        for (auto& t : threads) t.join();
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "互斥锁: " << time << " ms (counter=" << counter << ")\n";
    }

    // 原子计数器
    {
        std::atomic<int> counter{0};
        Timer timer;
        std::vector<std::thread> threads;
        for (size_t t = 0; t < num_threads; ++t) {
            threads.emplace_back([&counter, N, num_threads]() {
                for (size_t i = 0; i < N / num_threads; ++i) {
                    counter.fetch_add(1, std::memory_order_relaxed);
                }
            });
        }
        for (auto& t : threads) t.join();
        double time = timer.elapsedMs();
        std::cout << "原子操作: " << time << " ms (counter=" << counter << ")\n";
    }
}

void demonstrateMemoryOrder()
{
    std::cout << "\n=== 内存序选项 ===\n\n";
    std::cout << "memory_order_relaxed: 最弱，只保证原子性\n";
    std::cout << "memory_order_acquire: 读屏障\n";
    std::cout << "memory_order_release: 写屏障\n";
    std::cout << "memory_order_acq_rel: 读写屏障\n";
    std::cout << "memory_order_seq_cst: 最强，顺序一致性\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  无锁编程\n";
    std::cout << "========================================\n\n";
    demonstrateAtomicVsMutex();
    demonstrateMemoryOrder();
    std::cout << "\n总结: 原子操作比互斥锁更轻量，适合简单计数器。\n";
    return 0;
}
