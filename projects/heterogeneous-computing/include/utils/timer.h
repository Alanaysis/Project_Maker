#pragma once

/**
 * @file timer.h
 * @brief 性能计时器
 *
 * 本文件定义了性能计时相关的工具类。
 *
 * ⭐ 重点: 理解性能测量的重要性和方法
 * 💡 思考: 如何准确测量代码执行时间？
 */

#include <chrono>
#include <string>
#include <map>
#include <vector>
#include <mutex>
#include <iostream>
#include <iomanip>

namespace heterogeneous {
namespace utils {

/**
 * @brief 高精度计时器
 *
 * ⭐ 重点: 理解不同时间精度的区别
 *
 * 使用 std::chrono 实现高精度计时。
 * 支持微秒级别的精度。
 *
 * 💡 思考: 为什么使用 steady_clock 而不是 system_clock？
 */
class Timer {
public:
    using Clock = std::chrono::steady_clock;
    using TimePoint = std::chrono::time_point<Clock>;
    using Duration = std::chrono::microseconds;

    /**
     * @brief 构造函数
     * @param name 计时器名称
     * @param auto_start 是否自动开始
     */
    explicit Timer(const std::string& name = "", bool auto_start = false)
        : name_(name)
        , running_(false)
        , elapsed_(0) {
        if (auto_start) {
            start();
        }
    }

    /**
     * @brief 开始计时
     */
    void start() {
        if (!running_) {
            start_time_ = Clock::now();
            running_ = true;
        }
    }

    /**
     * @brief 停止计时
     * @return 经过的时间 (微秒)
     */
    Duration stop() {
        if (running_) {
            auto end_time = Clock::now();
            elapsed_ += std::chrono::duration_cast<Duration>(end_time - start_time_);
            running_ = false;
        }
        return elapsed_;
    }

    /**
     * @brief 重置计时器
     */
    void reset() {
        running_ = false;
        elapsed_ = Duration::zero();
    }

    /**
     * @brief 重新开始计时
     * @return 经过的时间 (微秒)
     */
    Duration restart() {
        auto elapsed = stop();
        reset();
        start();
        return elapsed;
    }

    /**
     * @brief 获取经过的时间
     * @return 经过的时间 (微秒)
     */
    Duration elapsed() const {
        if (running_) {
            auto now = Clock::now();
            return elapsed_ + std::chrono::duration_cast<Duration>(now - start_time_);
        }
        return elapsed_;
    }

    /**
     * @brief 获取经过的时间 (毫秒)
     */
    double elapsed_ms() const {
        return elapsed().count() / 1000.0;
    }

    /**
     * @brief 获取经过的时间 (秒)
     */
    double elapsed_sec() const {
        return elapsed().count() / 1000000.0;
    }

    /**
     * @brief 检查是否正在计时
     */
    bool is_running() const { return running_; }

    /**
     * @brief 获取计时器名称
     */
    const std::string& name() const { return name_; }

private:
    std::string name_;
    bool running_;
    TimePoint start_time_;
    Duration elapsed_;
};

/**
 * @brief 自动计时器 (RAII 模式)
 *
 * ⭐ 重点: 理解 RAII 模式在资源管理中的应用
 *
 * 自动计时器在构造时开始计时，在析构时停止计时。
 * 适合测量代码块的执行时间。
 *
 * 💡 思考: RAII 模式如何简化资源管理？
 */
class AutoTimer {
public:
    /**
     * @brief 构造函数
     * @param name 计时器名称
     * @param output 输出流 (可选)
     */
    explicit AutoTimer(const std::string& name, std::ostream* output = nullptr)
        : name_(name)
        , output_(output)
        , timer_(name, true) {}

    /**
     * @brief 析构函数
     */
    ~AutoTimer() {
        timer_.stop();
        if (output_) {
            *output_ << "[" << name_ << "] " << timer_.elapsed_ms() << " ms" << std::endl;
        }
    }

    /**
     * @brief 获取计时器
     */
    const Timer& timer() const { return timer_; }

private:
    std::string name_;
    std::ostream* output_;
    Timer timer_;
};

/**
 * @brief 性能分析器
 *
 * ⭐ 重点: 理解性能分析的方法
 *
 * 性能分析器用于收集和分析性能数据。
 *
 * 💡 思考: 如何识别性能瓶颈？
 */
class Profiler {
public:
    /**
     * @brief 获取单例实例
     */
    static Profiler& instance();

    /**
     * @brief 开始测量
     * @param name 测量名称
     */
    void start(const std::string& name);

    /**
     * @brief 停止测量
     * @param name 测量名称
     * @return 经过的时间 (微秒)
     */
    Timer::Duration stop(const std::string& name);

    /**
     * @brief 记录时间点
     * @param name 时间点名称
     */
    void record(const std::string& name);

    /**
     * @brief 获取测量结果
     * @param name 测量名称
     * @return 经过的时间 (微秒)
     */
    Timer::Duration get_duration(const std::string& name) const;

    /**
     * @brief 获取平均时间
     * @param name 测量名称
     * @return 平均时间 (微秒)
     */
    Timer::Duration get_average(const std::string& name) const;

    /**
     * @brief 获取最小时间
     * @param name 测量名称
     * @return 最小时间 (微秒)
     */
    Timer::Duration get_min(const std::string& name) const;

    /**
     * @brief 获取最大时间
     * @param name 测量名称
     * @return 最大时间 (微秒)
     */
    Timer::Duration get_max(const std::string& name) const;

    /**
     * @brief 生成报告
     * @param output 输出流
     */
    void report(std::ostream& output = std::cout) const;

    /**
     * @brief 生成报告到文件
     * @param filename 文件名
     */
    void report_to_file(const std::string& filename) const;

    /**
     * @brief 清除所有数据
     */
    void clear();

private:
    Profiler() = default;
    ~Profiler() = default;

    struct Measurement {
        std::vector<Timer::Duration> durations;
        Timer::Duration total{0};
        Timer::Duration min{Timer::Duration::max()};
        Timer::Duration max{Timer::Duration::zero()};
        size_t count = 0;

        void add(Timer::Duration duration) {
            durations.push_back(duration);
            total += duration;
            count++;
            if (duration < min) min = duration;
            if (duration > max) max = duration;
        }
    };

    std::map<std::string, Timer> timers_;
    std::map<std::string, Measurement> measurements_;
    mutable std::mutex mutex_;
};

/**
 * @brief 吞吐量测量器
 *
 * ⭐ 重点: 理解吞吐量的概念
 *
 * 吞吐量 = 处理的任务数 / 时间
 *
 * 💡 思考: 吞吐量和延迟有什么关系？
 */
class ThroughputMeter {
public:
    /**
     * @brief 构造函数
     * @param window_size 窗口大小 (用于计算平均值)
     */
    explicit ThroughputMeter(size_t window_size = 100)
        : window_size_(window_size) {}

    /**
     * @brief 记录任务完成
     * @param count 任务数量
     */
    void record(size_t count = 1) {
        std::lock_guard<std::mutex> lock(mutex_);
        auto now = std::chrono::steady_clock::now();

        timestamps_.push_back(now);
        counts_.push_back(count);

        // 保持窗口大小
        if (timestamps_.size() > window_size_) {
            timestamps_.erase(timestamps_.begin());
            counts_.erase(counts_.begin());
        }
    }

    /**
     * @brief 获取当前吞吐量 (任务/秒)
     */
    double get_throughput() const {
        std::lock_guard<std::mutex> lock(mutex_);
        if (timestamps_.size() < 2) return 0.0;

        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
            timestamps_.back() - timestamps_.front()
        );

        size_t total_count = 0;
        for (auto count : counts_) {
            total_count += count;
        }

        return total_count / (duration.count() / 1000000.0);
    }

    /**
     * @brief 重置
     */
    void reset() {
        std::lock_guard<std::mutex> lock(mutex_);
        timestamps_.clear();
        counts_.clear();
    }

private:
    size_t window_size_;
    std::vector<std::chrono::steady_clock::time_point> timestamps_;
    std::vector<size_t> counts_;
    mutable std::mutex mutex_;
};

/**
 * @brief 带宽测量器
 *
 * ⭐ 重点: 理解带宽的概念
 *
 * 带宽 = 数据量 / 时间
 *
 * 💡 思考: 如何测量实际带宽？
 */
class BandwidthMeter {
public:
    /**
     * @brief 构造函数
     * @param name 测量名称
     */
    explicit BandwidthMeter(const std::string& name = "")
        : name_(name) {}

    /**
     * @brief 开始测量
     * @param data_size 数据大小 (字节)
     */
    void start(size_t data_size) {
        data_size_ = data_size;
        timer_.start();
    }

    /**
     * @brief 停止测量
     * @return 带宽 (字节/秒)
     */
    double stop() {
        timer_.stop();
        return get_bandwidth();
    }

    /**
     * @brief 获取带宽 (字节/秒)
     */
    double get_bandwidth() const {
        auto elapsed = timer_.elapsed_sec();
        if (elapsed <= 0) return 0.0;
        return data_size_ / elapsed;
    }

    /**
     * @brief 获取带宽 (MB/秒)
     */
    double get_bandwidth_mbps() const {
        return get_bandwidth() / (1024 * 1024);
    }

    /**
     * @brief 获取带宽 (GB/秒)
     */
    double get_bandwidth_gbps() const {
        return get_bandwidth() / (1024 * 1024 * 1024);
    }

private:
    std::string name_;
    size_t data_size_ = 0;
    Timer timer_;
};

} // namespace utils
} // namespace heterogeneous

// 便捷宏

/**
 * @brief 计时宏
 */
#define HETERO_TIMER(name) \
    heterogeneous::utils::AutoTimer timer_##__LINE__(name)

/**
 * @brief 性能分析宏
 */
#define HETERO_PROFILER_START(name) \
    heterogeneous::utils::Profiler::instance().start(name)

#define HETERO_PROFILER_STOP(name) \
    heterogeneous::utils::Profiler::instance().stop(name)
