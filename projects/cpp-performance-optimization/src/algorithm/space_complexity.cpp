/**
 * @file space_complexity.cpp
 * @brief 空间复杂度优化示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <algorithm>

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
 * @brief 示例1: 原地算法 vs 非原地算法
 */
void demonstrateInPlace()
{
    std::cout << "=== 示例1: 原地算法 vs 非原地算法 ===\n\n";

    const size_t N = 10000000;
    std::vector<int> data(N);
    for (size_t i = 0; i < N; ++i) data[i] = static_cast<int>(N - i);

    // 非原地排序（需要额外空间）
    Timer timer;
    {
        std::vector<int> sorted_data = data;
        std::sort(sorted_data.begin(), sorted_data.end());
    }
    double copy_sort_time = timer.elapsedMs();

    // 原地排序
    timer.reset();
    {
        std::vector<int> arr = data;
        std::sort(arr.begin(), arr.end());
    }
    double inplace_time = timer.elapsedMs();

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "元素数量: " << N << "\n";
    std::cout << "非原地排序: " << copy_sort_time << " ms\n";
    std::cout << "原地排序:   " << inplace_time << " ms\n";
}

/**
 * @brief 示例2: 位图 vs 布尔数组
 */
void demonstrateBitmap()
{
    std::cout << "\n=== 示例2: 位图 vs 布尔数组 ===\n\n";

    const size_t N = 10000000;

    // bool 数组 (通常 1 byte/元素)
    std::cout << "bool 数组大小: " << N * sizeof(bool) / 1024.0 / 1024.0 << " MB\n";

    // 位图 (1 bit/元素)
    std::vector<uint8_t> bitmap(N / 8 + 1, 0);
    std::cout << "位图大小:      " << bitmap.size() / 1024.0 / 1024.0 << " MB\n";
    std::cout << "节省:          " << (N * sizeof(bool) - bitmap.size()) / 1024.0 / 1024.0 << " MB\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  空间复杂度优化\n";
    std::cout << "========================================\n\n";

    demonstrateInPlace();
    demonstrateBitmap();

    std::cout << "\n总结:\n";
    std::cout << "1. 原地算法减少内存使用\n";
    std::cout << "2. 位图节省 8x 内存\n";
    std::cout << "3. 空间-时间权衡需要根据场景选择\n";

    return 0;
}
