/**
 * @file timer.hpp
 * @brief 计时工具集
 *
 * 提供各种计时和测量工具
 */

#pragma once

#include <chrono>
#include <string>
#include <iostream>
#include <functional>
#include <vector>
#include <numeric>
#include <algorithm>
#include <cmath>

namespace perf {

/**
 * @brief 自动选择合适单位的时间格式化
 */
inline std::string formatDuration(double ns)
{
    if (ns < 1000.0) {
        return std::to_string(ns) + " ns";
    } else if (ns < 1000000.0) {
        return std::to_string(ns / 1000.0) + " us";
    } else if (ns < 1000000000.0) {
        return std::to_string(ns / 1000000.0) + " ms";
    } else {
        return std::to_string(ns / 1000000000.0) + " s";
    }
}

/**
 * @brief 带自动输出的计时器
 */
class AutoTimer
{
public:
    explicit AutoTimer(const std::string& label = "")
        : label_(label), start_(std::chrono::high_resolution_clock::now()) {}

    ~AutoTimer()
    {
        auto end = std::chrono::high_resolution_clock::now();
        auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start_).count();
        if (!label_.empty()) {
            std::cout << label_ << ": " << formatDuration(static_cast<double>(ns)) << "\n";
        }
    }

    double elapsed() const
    {
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration_cast<std::chrono::nanoseconds>(end - start_).count();
    }

private:
    std::string label_;
    std::chrono::high_resolution_clock::time_point start_;
};

/**
 * @brief 多次测量计时器
 */
class MultiTimer
{
public:
    void start()
    {
        current_ = std::chrono::high_resolution_clock::now();
    }

    void stop()
    {
        auto end = std::chrono::high_resolution_clock::now();
        auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - current_).count();
        samples_.push_back(static_cast<double>(ns));
    }

    void reset()
    {
        samples_.clear();
    }

    size_t count() const { return samples_.size(); }

    double mean() const
    {
        if (samples_.empty()) return 0.0;
        return std::accumulate(samples_.begin(), samples_.end(), 0.0) / samples_.size();
    }

    double median() const
    {
        if (samples_.empty()) return 0.0;
        auto sorted = samples_;
        std::sort(sorted.begin(), sorted.end());
        if (sorted.size() % 2 == 0) {
            return (sorted[sorted.size() / 2 - 1] + sorted[sorted.size() / 2]) / 2.0;
        }
        return sorted[sorted.size() / 2];
    }

    double stddev() const
    {
        if (samples_.size() < 2) return 0.0;
        double m = mean();
        double variance = 0.0;
        for (double s : samples_) {
            variance += (s - m) * (s - m);
        }
        return std::sqrt(variance / (samples_.size() - 1));
    }

    double min() const
    {
        return *std::min_element(samples_.begin(), samples_.end());
    }

    double max() const
    {
        return *std::max_element(samples_.begin(), samples_.end());
    }

    void print(const std::string& label = "") const
    {
        if (!label.empty()) {
            std::cout << label << ":\n";
        }
        std::cout << "  Mean:   " << formatDuration(mean()) << "\n";
        std::cout << "  Median: " << formatDuration(median()) << "\n";
        std::cout << "  StdDev: " << formatDuration(stddev()) << "\n";
        std::cout << "  Min:    " << formatDuration(min()) << "\n";
        std::cout << "  Max:    " << formatDuration(max()) << "\n";
    }

private:
    std::vector<double> samples_;
    std::chrono::high_resolution_clock::time_point current_;
};

/**
 * @brief CPU 周期计数器（x86）
 */
inline uint64_t rdtsc()
{
#if defined(__x86_64__) || defined(_M_X64)
    unsigned int lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return ((uint64_t)hi << 32) | lo;
#elif defined(__i386__) || defined(_M_IX86)
    unsigned int lo, hi;
    __asm__ __volatile__ ("rdtsc" : "=a" (lo), "=d" (hi));
    return ((uint64_t)hi << 32) | lo;
#else
    return 0; // 不支持
#endif
}

/**
 * @brief 使用 rdtsc 的高精度计时
 */
class CycleTimer
{
public:
    CycleTimer() : start_(rdtsc()) {}

    uint64_t elapsed() const
    {
        return rdtsc() - start_;
    }

    void reset()
    {
        start_ = rdtsc();
    }

private:
    uint64_t start_;
};

/**
 * @brief 吞吐量测量器
 */
class ThroughputMeter
{
public:
    void start()
    {
        start_ = std::chrono::high_resolution_clock::now();
        operations_ = 0;
    }

    void addOperations(size_t count)
    {
        operations_ += count;
    }

    double stop()
    {
        auto end = std::chrono::high_resolution_clock::now();
        auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start_).count();
        duration_ns_ = static_cast<double>(ns);
        return operationsPerSecond();
    }

    double operationsPerSecond() const
    {
        if (duration_ns_ <= 0) return 0.0;
        return operations_ * 1e9 / duration_ns_;
    }

    double nsPerOperation() const
    {
        if (operations_ == 0) return 0.0;
        return duration_ns_ / operations_;
    }

private:
    std::chrono::high_resolution_clock::time_point start_;
    size_t operations_ = 0;
    double duration_ns_ = 0.0;
};

} // namespace perf