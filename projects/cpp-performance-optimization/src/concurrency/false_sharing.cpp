/**
 * @file false_sharing.cpp
 * @brief 伪共享示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <thread>
#include <atomic>

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

constexpr size_t CACHE_LINE_SIZE = 64;

/**
 * @brief 有伪共享的结构
 */
struct SharedLine {
    std::atomic<int> counter1{0};
    std::atomic<int> counter2{0};
};

/**
 * @brief 无伪共享的结构（填充到缓存行）
 */
struct alignas(CACHE_LINE_SIZE) PaddedCounter {
    std::atomic<int> value{0};
    char padding[CACHE_LINE_SIZE - sizeof(std::atomic<int>)];
};

void demonstrateFalseSharing()
{
    std::cout << "=== 伪共享演示 ===\n\n";

    const size_t N = 100000000;

    // 有伪共享
    {
        SharedLine shared;
        Timer timer;
        std::thread t1([&shared, N]() {
            for (size_t i = 0; i < N; ++i) {
                shared.counter1.fetch_add(1, std::memory_order_relaxed);
            }
        });
        std::thread t2([&shared, N]() {
            for (size_t i = 0; i < N; ++i) {
                shared.counter2.fetch_add(1, std::memory_order_relaxed);
            }
        });
        t1.join(); t2.join();
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "有伪共享: " << time << " ms\n";
        std::cout << "  counter1=" << shared.counter1 << ", counter2=" << shared.counter2 << "\n";
    }

    // 无伪共享
    {
        PaddedCounter c1, c2;
        Timer timer;
        std::thread t1([&c1, N]() {
            for (size_t i = 0; i < N; ++i) {
                c1.value.fetch_add(1, std::memory_order_relaxed);
            }
        });
        std::thread t2([&c2, N]() {
            for (size_t i = 0; i < N; ++i) {
                c2.value.fetch_add(1, std::memory_order_relaxed);
            }
        });
        t1.join(); t2.join();
        double time = timer.elapsedMs();
        std::cout << "无伪共享: " << time << " ms\n";
        std::cout << "  counter1=" << c1.value << ", counter2=" << c2.value << "\n";
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  伪共享 (False Sharing)\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: 当不同线程访问同一缓存行的不同变量时，\n";
    std::cout << "会导致缓存行在 CPU 核心间频繁传输（伪共享）。\n";
    std::cout << "使用填充或 alignas 将变量隔离到不同缓存行。\n\n";

    demonstrateFalseSharing();

    std::cout << "\n总结: 使用 alignas(64) 或填充避免伪共享。\n";
    return 0;
}
