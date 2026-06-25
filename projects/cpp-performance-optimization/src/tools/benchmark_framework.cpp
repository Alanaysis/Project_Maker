/**
 * @file benchmark_framework.cpp
 * @brief 基准测试框架示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <algorithm>
#include <numeric>
#include <cmath>
#include <functional>
#include <string>

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
 * @brief 基准测试结果
 */
struct BenchResult {
    std::string name;
    double mean_ns;
    double median_ns;
    double stddev_ns;
    double min_ns;
    double max_ns;
    size_t iterations;
};

/**
 * @brief 运行基准测试
 */
template<typename F>
BenchResult benchmark(const std::string& name, F&& func,
                      size_t iterations = 1000, size_t warmup = 100)
{
    // 预热
    for (size_t i = 0; i < warmup; ++i) func();

    // 收集样本
    std::vector<double> samples;
    samples.reserve(iterations);
    for (size_t i = 0; i < iterations; ++i) {
        Timer t;
        func();
        samples.push_back(t.elapsedNs());
    }

    // 计算统计
    std::sort(samples.begin(), samples.end());
    double sum = std::accumulate(samples.begin(), samples.end(), 0.0);
    double mean = sum / samples.size();
    double median = samples[samples.size() / 2];

    double variance = 0.0;
    for (double s : samples) variance += (s - mean) * (s - mean);
    double stddev = std::sqrt(variance / samples.size());

    return {name, mean, median, stddev, samples.front(), samples.back(), iterations};
}

void printResult(const BenchResult& r)
{
    std::cout << std::fixed << std::setprecision(2);
    std::cout << "=== " << r.name << " ===\n";
    std::cout << "  迭代:   " << r.iterations << "\n";
    std::cout << "  均值:   " << r.mean_ns << " ns\n";
    std::cout << "  中位数: " << r.median_ns << " ns\n";
    std::cout << "  标准差: " << r.stddev_ns << " ns\n";
    std::cout << "  最小:   " << r.min_ns << " ns\n";
    std::cout << "  最大:   " << r.max_ns << " ns\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  基准测试框架\n";
    std::cout << "========================================\n\n";

    // 测试 vector push_back
    auto result1 = benchmark("vector::push_back", []() {
        std::vector<int> v;
        for (int i = 0; i < 1000; ++i) v.push_back(i);
    });

    // 测试 vector reserve + push_back
    auto result2 = benchmark("vector::reserve+push_back", []() {
        std::vector<int> v;
        v.reserve(1000);
        for (int i = 0; i < 1000; ++i) v.push_back(i);
    });

    printResult(result1);
    std::cout << "\n";
    printResult(result2);

    std::cout << "\n";
    std::cout << "reserve 比不 reserve 快: "
              << result1.mean_ns / result2.mean_ns << "x\n";

    return 0;
}
