/**
 * @file string_processing.cpp
 * @brief 字符串处理优化案例
 */

#include <iostream>
#include <string>
#include <vector>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <numeric>

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

void demonstrateStringConcat()
{
    std::cout << "=== 字符串拼接优化 ===\n\n";

    const size_t N = 100000;

    // 逐个拼接
    {
        Timer timer;
        std::string result;
        for (size_t i = 0; i < N; ++i) {
            result += std::to_string(i) + ",";
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "逐个拼接:     " << time << " ms\n";
    }

    // 预留空间
    {
        Timer timer;
        std::string result;
        result.reserve(N * 6);
        for (size_t i = 0; i < N; ++i) {
            result += std::to_string(i) + ",";
        }
        double time = timer.elapsedMs();
        std::cout << "预留空间:     " << time << " ms\n";
    }

    // ostringstream
    {
        Timer timer;
        std::ostringstream oss;
        for (size_t i = 0; i < N; ++i) {
            oss << i << ",";
        }
        std::string result = oss.str();
        double time = timer.elapsedMs();
        std::cout << "ostringstream: " << time << " ms\n";
    }
}

void demonstrateStringView()
{
    std::cout << "\n=== string_view 优化 ===\n\n";

    const size_t N = 1000000;
    std::string source = "Hello, World! This is a test string for benchmarking.";

    // string 拷贝
    {
        Timer timer;
        volatile size_t total_len = 0;
        for (size_t i = 0; i < N; ++i) {
            std::string s = source;
            total_len += s.length();
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "string 拷贝:    " << time << " ms\n";
        (void)total_len;
    }

    // string_view
    {
        Timer timer;
        volatile size_t total_len = 0;
        for (size_t i = 0; i < N; ++i) {
            std::string_view sv = source;
            total_len += sv.length();
        }
        double time = timer.elapsedMs();
        std::cout << "string_view:    " << time << " ms\n";
        (void)total_len;
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  字符串处理优化\n";
    std::cout << "========================================\n\n";
    demonstrateStringConcat();
    demonstrateStringView();
    std::cout << "\n总结: 预留空间和 string_view 可以显著提升字符串操作性能。\n";
    return 0;
}
