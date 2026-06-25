#pragma once

#include <chrono>
#include <string>
#include <iostream>
#include <functional>

namespace utils {

class Timer {
public:
    using Clock = std::chrono::high_resolution_clock;
    using Duration = std::chrono::nanoseconds;

    Timer() : start_(Clock::now()) {}

    void reset() { start_ = Clock::now(); }

    Duration elapsed() const {
        return std::chrono::duration_cast<Duration>(Clock::now() - start_);
    }

    double elapsed_ms() const {
        return std::chrono::duration<double, std::milli>(Clock::now() - start_).count();
    }

    double elapsed_us() const {
        return std::chrono::duration<double, std::micro>(Clock::now() - start_).count();
    }

    double elapsed_ns() const {
        return std::chrono::duration<double, std::nano>(Clock::now() - start_).count();
    }

    // 执行函数并计时
    template<typename F>
    static auto measure(F&& func, const std::string& name = "") {
        Timer timer;
        if constexpr (std::is_void_v<std::invoke_result_t<F>>) {
            func();
            auto elapsed = timer.elapsed();
            if (!name.empty()) {
                std::cout << name << ": " << timer.elapsed_us() << " us" << std::endl;
            }
            return elapsed;
        } else {
            auto result = func();
            auto elapsed = timer.elapsed();
            if (!name.empty()) {
                std::cout << name << ": " << timer.elapsed_us() << " us" << std::endl;
            }
            return std::make_pair(std::move(result), elapsed);
        }
    }

    // 执行函数多次并统计
    template<typename F>
    static void benchmark(F&& func, size_t iterations, const std::string& name = "") {
        std::vector<double> times;
        times.reserve(iterations);

        for (size_t i = 0; i < iterations; ++i) {
            Timer timer;
            func();
            times.push_back(timer.elapsed_ns());
        }

        // 计算统计信息
        double sum = 0;
        double min_val = times[0];
        double max_val = times[0];
        for (double t : times) {
            sum += t;
            min_val = std::min(min_val, t);
            max_val = std::max(max_val, t);
        }
        double avg = sum / iterations;

        if (!name.empty()) {
            std::cout << "=== " << name << " ===" << std::endl;
        }
        std::cout << "  Iterations: " << iterations << std::endl;
        std::cout << "  Average:    " << avg / 1000.0 << " us" << std::endl;
        std::cout << "  Min:        " << min_val / 1000.0 << " us" << std::endl;
        std::cout << "  Max:        " << max_val / 1000.0 << " us" << std::endl;
    }

private:
    Clock::time_point start_;
};

// RAII 计时器
class ScopedTimer {
public:
    explicit ScopedTimer(const std::string& name)
        : name_(name), start_(Timer::Clock::now()) {}

    ~ScopedTimer() {
        auto elapsed = std::chrono::duration<double, std::milli>(
            Timer::Clock::now() - start_).count();
        std::cout << name_ << ": " << elapsed << " ms" << std::endl;
    }

private:
    std::string name_;
    Timer::Clock::time_point start_;
};

} // namespace utils
