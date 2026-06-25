/**
 * @file branch_prediction.cpp
 * @brief 分支预测优化示例
 *
 * 本文件演示分支预测的影响和优化：
 * 1. 分支预测失败惩罚
 * 2. 无分支编程
 * 3. [[likely]]/[[unlikely]] 提示
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <algorithm>
#include <random>

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
 * @brief 示例1: 排序数据 vs 未排序数据
 *
 * 分支预测器对有序数据预测准确率高，
 * 对无序数据预测准确率低。
 */
void demonstrateSortedVsUnsorted()
{
    std::cout << "=== 示例1: 排序数据 vs 未排序数据 ===\n\n";

    const size_t N = 10000000;
    std::vector<int> data(N);

    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(0, 255);
    for (auto& v : data) v = dist(rng);

    constexpr size_t ITERS = 10;

    // 未排序数据
    Timer timer;
    volatile long long sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            if (data[i] >= 128) {
                sum1 += data[i];
            }
        }
    }
    double unsorted_time = timer.elapsedMs();

    // 排序数据
    std::vector<int> sorted_data = data;
    std::sort(sorted_data.begin(), sorted_data.end());

    timer.reset();
    volatile long long sum2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            if (sorted_data[i] >= 128) {
                sum2 += sorted_data[i];
            }
        }
    }
    double sorted_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "未排序: " << unsorted_time << " ms\n";
    std::cout << "已排序: " << sorted_time << " ms\n";
    std::cout << "排序快: " << unsorted_time / sorted_time << "x\n";
    (void)sum1; (void)sum2;
}

/**
 * @brief 示例2: 无分支编程
 *
 * 用条件移动或位运算替代分支。
 */
void demonstrateBranchless()
{
    std::cout << "\n=== 示例2: 无分支编程 ===\n\n";

    const size_t N = 10000000;
    std::vector<int> data(N);
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(0, 255);
    for (auto& v : data) v = dist(rng);

    constexpr size_t ITERS = 10;

    // 有分支版本
    Timer timer;
    volatile long long sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            if (data[i] >= 128) {
                sum1 += data[i];
            }
        }
    }
    double branch_time = timer.elapsedMs();

    // 无分支版本（使用条件表达式，编译器可能用 cmov）
    timer.reset();
    volatile long long sum2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            sum2 += (data[i] >= 128) ? data[i] : 0;
        }
    }
    double branchless_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "有分支:   " << branch_time << " ms\n";
    std::cout << "无分支:   " << branchless_time << " ms\n";
    (void)sum1; (void)sum2;
}

/**
 * @brief 示例3: [[likely]] 和 [[unlikely]] 提示
 */
void demonstrateLikelyUnlikely()
{
    std::cout << "\n=== 示例3: [[likely]]/[[unlikely]] 提示 ===\n\n";

    const size_t N = 10000000;
    std::vector<int> data(N);
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(0, 99);
    for (auto& v : data) v = dist(rng);

    constexpr size_t ITERS = 10;

    // 无提示版本
    Timer timer;
    volatile long long sum1 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            if (data[i] < 90) {
                sum1 += data[i];
            } else {
                sum1 -= data[i];
            }
        }
    }
    double no_hint_time = timer.elapsedMs();

    // 有提示版本（90% 的情况走 likely 分支）
    timer.reset();
    volatile long long sum2 = 0;
    for (size_t iter = 0; iter < ITERS; ++iter) {
        for (size_t i = 0; i < N; ++i) {
            if (data[i] < 90) [[likely]] {
                sum2 += data[i];
            } else [[unlikely]] {
                sum2 -= data[i];
            }
        }
    }
    double hint_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "无提示: " << no_hint_time << " ms\n";
    std::cout << "有提示: " << hint_time << " ms\n";
    (void)sum1; (void)sum2;
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  分支预测优化 (Branch Prediction)\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: 分支预测失败会导致 CPU 流水线清空，\n";
    std::cout << "代价约 10-20 个时钟周期。\n";

    demonstrateSortedVsUnsorted();
    demonstrateBranchless();
    demonstrateLikelyUnlikely();

    std::cout << "\n========================================\n";
    std::cout << "  总结\n";
    std::cout << "========================================\n";
    std::cout << "1. 排序数据提高分支预测准确率\n";
    std::cout << "2. 无分支编程避免预测失败\n";
    std::cout << "3. 使用 [[likely]]/[[unlikely]] 提示\n";
    std::cout << "4. 保持分支条件简单\n";

    return 0;
}
