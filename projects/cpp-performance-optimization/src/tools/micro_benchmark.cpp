/**
 * @file micro_benchmark.cpp
 * @brief 微基准测试技巧示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <algorithm>
#include <numeric>
#include <cmath>
#include <functional>

class Timer
{
public:
    using Clock = std::chrono::high_resolution_clock;
    Timer() : start_(Clock::now()) {}
    void reset() { start_ = Clock::now(); }
    double elapsedNs() const {
        return static_cast<double>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                Clock::now() - start_).count());
    }
private:
    Clock::time_point start_;
};

/**
 * @brief 防止编译器优化掉结果
 */
template<typename T>
void doNotOptimize(T const& val)
{
#if defined(__GNUC__) || defined(__clang__)
    asm volatile("" : : "r,m"(val) : "memory");
#else
    volatile void* p = &val;
    (void)p;
#endif
}

void demonstrateBenchmarkPitfalls()
{
    std::cout << "=== 微基准测试技巧 ===\n\n";

    std::cout << "1. 防止编译器优化:\n";
    std::cout << "   - 使用 doNotOptimize() 保留结果\n";
    std::cout << "   - 使用 volatile 防止消除\n\n";

    std::cout << "2. 预热运行:\n";
    std::cout << "   - CPU 缓存需要预热\n";
    std::cout << "   - 分支预测器需要训练\n\n";

    std::cout << "3. 多次运行取平均:\n";
    std::cout << "   - 消除随机误差\n";
    std::cout << "   - 使用中位数减少异常值影响\n\n";

    std::cout << "4. 统计分析:\n";
    std::cout << "   - 计算标准差\n";
    std::cout << "   - 识别异常值\n\n";

    // 示例: 正确的基准测试
    std::cout << "--- 示例基准测试 ---\n";

    const size_t N = 1000000;
    std::vector<int> data(N);
    for (size_t i = 0; i < N; ++i) data[i] = static_cast<int>(i);

    const size_t ITERS = 100;
    std::vector<double> samples;

    for (size_t run = 0; run < ITERS; ++run) {
        Timer t;
        volatile long long sum = 0;
        for (size_t i = 0; i < N; ++i) {
            sum += data[i];
        }
        doNotOptimize(sum);
        samples.push_back(t.elapsedNs());
    }

    std::sort(samples.begin(), samples.end());
    double mean = std::accumulate(samples.begin(), samples.end(), 0.0) / samples.size();
    double median = samples[samples.size() / 2];

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "均值:   " << mean / 1e6 << " ms\n";
    std::cout << "中位数: " << median / 1e6 << " ms\n";
    std::cout << "最小:   " << samples.front() / 1e6 << " ms\n";
    std::cout << "最大:   " << samples.back() / 1e6 << " ms\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  微基准测试技巧\n";
    std::cout << "========================================\n\n";
    demonstrateBenchmarkPitfalls();
    return 0;
}
