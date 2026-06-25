/**
 * @file constant_factor.cpp
 * @brief 常数因子优化示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <cmath>

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

/**
 * @brief 示例1: 乘法 vs 移位
 */
void demonstrateStrengthReduction()
{
    std::cout << "=== 示例1: 强度削减 ===\n\n";

    const size_t N = 100000000;
    std::vector<int> data(N);
    for (size_t i = 0; i < N; ++i) data[i] = static_cast<int>(i);

    constexpr size_t ITERS = 10;

    // 乘法
    Timer timer;
    volatile long long sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            sum1 += data[i] * 8;
        }
    }
    double mul_time = timer.elapsedMs();

    // 移位
    timer.reset();
    volatile long long sum2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            sum2 += data[i] << 3;
        }
    }
    double shift_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "乘法: " << mul_time << " ms\n";
    std::cout << "移位: " << shift_time << " ms\n";
    (void)sum1; (void)sum2;
}

/**
 * @brief 示例2: 查找表 vs 计算
 */
void demonstrateLookupTable()
{
    std::cout << "\n=== 示例2: 查找表 vs 计算 ===\n\n";

    const size_t N = 10000000;

    // 预计算查找表
    std::vector<float> sin_table(3600);
    for (size_t i = 0; i < 3600; ++i) {
        sin_table[i] = std::sin(i * 3.14159f / 1800.0f);
    }

    constexpr size_t ITERS = 10;

    // 直接计算
    Timer timer;
    volatile float sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            sum1 += std::sin(static_cast<float>(i % 3600) * 3.14159f / 1800.0f);
        }
    }
    double compute_time = timer.elapsedMs();

    // 查找表
    timer.reset();
    volatile float sum2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            sum2 += sin_table[i % 3600];
        }
    }
    double lookup_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "直接计算: " << compute_time << " ms\n";
    std::cout << "查找表:   " << lookup_time << " ms\n";
    std::cout << "查找表快: " << compute_time / lookup_time << "x\n";
    (void)sum1; (void)sum2;
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  常数因子优化\n";
    std::cout << "========================================\n\n";

    demonstrateStrengthReduction();
    demonstrateLookupTable();

    std::cout << "\n总结:\n";
    std::cout << "1. 强度削减: 用移位替代乘法\n";
    std::cout << "2. 查找表: 用空间换时间\n";
    std::cout << "3. 避免重复计算\n";

    return 0;
}
