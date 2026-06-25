/**
 * @file benchmark.hpp
 * @brief 简单的基准测试框架
 *
 * 提供计时、统计和基准测试功能
 */

#pragma once

#include <chrono>
#include <vector>
#include <algorithm>
#include <numeric>
#include <cmath>
#include <iostream>
#include <string>
#include <functional>
#include <iomanip>

namespace perf {

/**
 * @brief 高精度计时器
 */
class Timer
{
public:
    using Clock = std::chrono::high_resolution_clock;
    using Duration = std::chrono::nanoseconds;

    Timer() : start_(Clock::now()) {}

    void reset()
    {
        start_ = Clock::now();
    }

    /**
     * @brief 获取经过的时间（纳秒）
     */
    int64_t elapsedNs() const
    {
        return std::chrono::duration_cast<Duration>(Clock::now() - start_).count();
    }

    /**
     * @brief 获取经过的时间（微秒）
     */
    double elapsedUs() const
    {
        return elapsedNs() / 1000.0;
    }

    /**
     * @brief 获取经过的时间（毫秒）
     */
    double elapsedMs() const
    {
        return elapsedNs() / 1000000.0;
    }

    /**
     * @brief 获取经过的时间（秒）
     */
    double elapsedS() const
    {
        return elapsedNs() / 1000000000.0;
    }

private:
    Clock::time_point start_;
};

/**
 * @brief RAII 风格的作用域计时器
 */
class ScopedTimer
{
public:
    explicit ScopedTimer(const std::string& name)
        : name_(name), timer_() {}

    ~ScopedTimer()
    {
        std::cout << name_ << ": " << timer_.elapsedUs() << " us\n";
    }

private:
    std::string name_;
    Timer timer_;
};

/**
 * @brief 基准测试结果
 */
struct BenchmarkResult
{
    std::string name;
    size_t iterations;
    double mean_ns;
    double median_ns;
    double stddev_ns;
    double min_ns;
    double max_ns;
    double total_ns;

    void print() const
    {
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "=== " << name << " ===\n";
        std::cout << "  Iterations: " << iterations << "\n";
        std::cout << "  Mean:       " << mean_ns << " ns\n";
        std::cout << "  Median:     " << median_ns << " ns\n";
        std::cout << "  StdDev:     " << stddev_ns << " ns\n";
        std::cout << "  Min:        " << min_ns << " ns\n";
        std::cout << "  Max:        " << max_ns << " ns\n";
        std::cout << "  Total:      " << total_ns / 1e6 << " ms\n";
    }
};

/**
 * @brief 基准测试运行器
 */
class BenchmarkRunner
{
public:
    /**
     * @brief 运行基准测试
     * @param name 测试名称
     * @param func 要测试的函数
     * @param iterations 迭代次数
     * @param warmup 预热次数
     */
    template<typename F>
    BenchmarkResult run(const std::string& name, F&& func,
                       size_t iterations = 1000, size_t warmup = 100)
    {
        // 预热
        for (size_t i = 0; i < warmup; ++i) {
            func();
        }

        // 收集样本
        std::vector<double> samples;
        samples.reserve(iterations);

        for (size_t i = 0; i < iterations; ++i) {
            Timer timer;
            func();
            samples.push_back(static_cast<double>(timer.elapsedNs()));
        }

        // 计算统计信息
        return calculateStats(name, samples);
    }

    /**
     * @brief 运行基准测试（带迭代控制）
     * @param name 测试名称
     * @param func 要测试的函数（接受迭代次数参数）
     * @param iterations 迭代次数
     * @param warmup 预热次数
     */
    template<typename F>
    BenchmarkResult runWithIteration(const std::string& name, F&& func,
                                    size_t iterations = 1000, size_t warmup = 100)
    {
        // 预热
        for (size_t i = 0; i < warmup; ++i) {
            func(i);
        }

        // 收集样本
        std::vector<double> samples;
        samples.reserve(iterations);

        for (size_t i = 0; i < iterations; ++i) {
            Timer timer;
            func(i);
            samples.push_back(static_cast<double>(timer.elapsedNs()));
        }

        return calculateStats(name, samples);
    }

    /**
     * @brief 比较两个基准测试结果
     */
    static void compare(const BenchmarkResult& baseline,
                       const BenchmarkResult& optimized)
    {
        double speedup = baseline.mean_ns / optimized.mean_ns;
        double improvement = (1.0 - optimized.mean_ns / baseline.mean_ns) * 100.0;

        std::cout << std::fixed << std::setprecision(2);
        std::cout << "\n=== 性能对比: " << baseline.name << " vs " << optimized.name << " ===\n";
        std::cout << "  基准 (" << baseline.name << "):  " << baseline.mean_ns << " ns\n";
        std::cout << "  优化 (" << optimized.name << "): " << optimized.mean_ns << " ns\n";
        std::cout << "  加速比: " << speedup << "x\n";
        std::cout << "  提升:   " << improvement << "%\n";
    }

private:
    BenchmarkResult calculateStats(const std::string& name,
                                   std::vector<double>& samples)
    {
        BenchmarkResult result;
        result.name = name;
        result.iterations = samples.size();

        // 排序计算中位数
        std::sort(samples.begin(), samples.end());

        result.min_ns = samples.front();
        result.max_ns = samples.back();

        // 计算均值
        result.total_ns = std::accumulate(samples.begin(), samples.end(), 0.0);
        result.mean_ns = result.total_ns / samples.size();

        // 计算中位数
        if (samples.size() % 2 == 0) {
            result.median_ns = (samples[samples.size() / 2 - 1] +
                               samples[samples.size() / 2]) / 2.0;
        } else {
            result.median_ns = samples[samples.size() / 2];
        }

        // 计算标准差
        double variance = 0.0;
        for (double s : samples) {
            variance += (s - result.mean_ns) * (s - result.mean_ns);
        }
        result.stddev_ns = std::sqrt(variance / samples.size());

        return result;
    }
};

/**
 * @brief 一次性基准测试（简化接口）
 */
template<typename F>
BenchmarkResult benchmark(const std::string& name, F&& func,
                         size_t iterations = 1000, size_t warmup = 100)
{
    BenchmarkRunner runner;
    return runner.run(name, std::forward<F>(func), iterations, warmup);
}

/**
 * @brief 比较两个函数的性能
 */
template<typename F1, typename F2>
void compare(const std::string& name,
            const std::string& name1, F1&& func1,
            const std::string& name2, F2&& func2,
            size_t iterations = 1000)
{
    auto result1 = benchmark(name1, std::forward<F1>(func1), iterations);
    auto result2 = benchmark(name2, std::forward<F2>(func2), iterations);

    result1.print();
    std::cout << "\n";
    result2.print();

    BenchmarkRunner::compare(result1, result2);
}

} // namespace perf

// 便利宏
#define PERF_SCOPED_TIMER(name) perf::ScopedTimer _timer_##__LINE__(name)

#define PERF_BENCHMARK(name, func, ...) \
    perf::benchmark(name, func, ##__VA_ARGS__)

#define PERF_COMPARE(name, name1, func1, name2, func2, ...) \
    perf::compare(name, name1, func1, name2, func2, ##__VA_ARGS__)