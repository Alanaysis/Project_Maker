/**
 * @file timestamp.h
 * @brief 高精度时间戳
 *
 * 提供纳秒级时间戳，用于延迟测量和时间记录。
 * 使用 std::chrono::high_resolution_clock 实现。
 */

#pragma once

#include <chrono>
#include <cstdint>
#include <string>
#include <ctime>

namespace hft {

/**
 * @class Timestamp
 * @brief 高精度时间戳类
 *
 * 使用纳秒精度存储时间戳，支持时间比较和格式化输出。
 */
class Timestamp {
public:
    /**
     * @brief 默认构造函数
     */
    Timestamp() : nanoseconds_(0) {}

    /**
     * @brief 从纳秒构造
     * @param ns 纳秒数
     */
    explicit Timestamp(int64_t ns) : nanoseconds_(ns) {}

    /**
     * @brief 获取当前时间戳
     * @return 当前时间戳
     */
    static Timestamp now() {
        auto now = std::chrono::high_resolution_clock::now();
        return Timestamp(
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                now.time_since_epoch()
            ).count()
        );
    }

    /**
     * @brief 获取系统时间戳
     * @return 系统时间戳（微秒精度）
     */
    static Timestamp system_now() {
        auto now = std::chrono::system_clock::now();
        return Timestamp(
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                now.time_since_epoch()
            ).count()
        );
    }

    /**
     * @brief 获取纳秒数
     * @return 纳秒数
     */
    int64_t nanoseconds() const { return nanoseconds_; }

    /**
     * @brief 获取微秒数
     * @return 微秒数
     */
    int64_t microseconds() const { return nanoseconds_ / 1000; }

    /**
     * @brief 获取毫秒数
     * @return 毫秒数
     */
    int64_t milliseconds() const { return nanoseconds_ / 1000000; }

    /**
     * @brief 获取秒数
     * @return 秒数
     */
    int64_t seconds() const { return nanoseconds_ / 1000000000; }

    /**
     * @brief 计算与另一个时间戳的差值
     * @param other 另一个时间戳
     * @return 差值（纳秒）
     */
    int64_t diff(const Timestamp& other) const {
        return nanoseconds_ - other.nanoseconds_;
    }

    /**
     * @brief 格式化为字符串
     * @return 格式化的时间字符串
     */
    std::string to_string() const {
        auto ns = nanoseconds_ % 1000000000;
        auto us = (nanoseconds_ / 1000) % 1000000;
        auto ms = (nanoseconds_ / 1000000) % 1000;
        auto s = nanoseconds_ / 1000000000;

        char buffer[64];
        std::snprintf(buffer, sizeof(buffer), "%lld.%03lld%03lld%03lld",
                     static_cast<long long>(s),
                     static_cast<long long>(ms),
                     static_cast<long long>(us),
                     static_cast<long long>(ns));
        return std::string(buffer);
    }

    /**
     * @brief 格式化为日期时间字符串
     * @return 日期时间字符串
     */
    std::string to_datetime_string() const {
        auto time_t_val = static_cast<std::time_t>(nanoseconds_ / 1000000000);
        auto* tm = std::localtime(&time_t_val);

        char buffer[64];
        std::strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", tm);

        auto ns = nanoseconds_ % 1000000000;
        char result[80];
        std::snprintf(result, sizeof(result), "%s.%09lld", buffer,
                     static_cast<long long>(ns));
        return std::string(result);
    }

    // 比较操作符
    bool operator==(const Timestamp& other) const {
        return nanoseconds_ == other.nanoseconds_;
    }

    bool operator!=(const Timestamp& other) const {
        return nanoseconds_ != other.nanoseconds_;
    }

    bool operator<(const Timestamp& other) const {
        return nanoseconds_ < other.nanoseconds_;
    }

    bool operator<=(const Timestamp& other) const {
        return nanoseconds_ <= other.nanoseconds_;
    }

    bool operator>(const Timestamp& other) const {
        return nanoseconds_ > other.nanoseconds_;
    }

    bool operator>=(const Timestamp& other) const {
        return nanoseconds_ >= other.nanoseconds_;
    }

    // 算术操作符
    Timestamp operator+(int64_t ns) const {
        return Timestamp(nanoseconds_ + ns);
    }

    Timestamp operator-(int64_t ns) const {
        return Timestamp(nanoseconds_ - ns);
    }

    int64_t operator-(const Timestamp& other) const {
        return nanoseconds_ - other.nanoseconds_;
    }

    Timestamp& operator+=(int64_t ns) {
        nanoseconds_ += ns;
        return *this;
    }

    Timestamp& operator-=(int64_t ns) {
        nanoseconds_ -= ns;
        return *this;
    }

private:
    int64_t nanoseconds_;  ///< 纳秒时间戳
};

/**
 * @class ScopedTimer
 * @brief 作用域计时器
 *
 * RAII 风格的计时器，在析构时输出耗时。
 */
class ScopedTimer {
public:
    /**
     * @brief 构造函数，开始计时
     * @param name 计时器名称
     */
    explicit ScopedTimer(const std::string& name)
        : name_(name), start_(Timestamp::now()) {}

    /**
     * @brief 析构函数，输出耗时
     */
    ~ScopedTimer() {
        auto end = Timestamp::now();
        auto duration = end - start_;
        // 可以输出到日志系统
        (void)duration;
    }

    /**
     * @brief 获取已经过的时间
     * @return 经过的时间（纳秒）
     */
    int64_t elapsed() const {
        return Timestamp::now() - start_;
    }

private:
    std::string name_;
    Timestamp start_;
};

} // namespace hft
