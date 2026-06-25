/**
 * @file atomic_optimization.cpp
 * @brief 原子操作优化示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <atomic>
#include <thread>

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

void demonstrateMemoryOrderPerformance()
{
    std::cout << "=== 内存序性能对比 ===\n\n";

    const size_t N = 10000000;

    // seq_cst (最强)
    {
        std::atomic<int> counter{0};
        Timer timer;
        for (size_t i = 0; i < N; ++i) {
            counter.fetch_add(1, std::memory_order_seq_cst);
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "seq_cst:  " << time << " ms\n";
    }

    // relaxed (最弱)
    {
        std::atomic<int> counter{0};
        Timer timer;
        for (size_t i = 0; i < N; ++i) {
            counter.fetch_add(1, std::memory_order_relaxed);
        }
        double time = timer.elapsedMs();
        std::cout << "relaxed:  " << time << " ms\n";
    }

    // 非原子版本（对照）
    {
        int counter = 0;
        Timer timer;
        for (size_t i = 0; i < N; ++i) {
            ++counter;
        }
        double time = timer.elapsedMs();
        std::cout << "非原子:   " << time << " ms\n";
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  原子操作优化\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: 不同内存序有不同性能开销。\n";
    std::cout << "relaxed 最快，seq_cst 最慢但最安全。\n\n";

    demonstrateMemoryOrderPerformance();

    std::cout << "\n总结: 在不需要顺序保证时使用 relaxed 内存序。\n";
    return 0;
}
