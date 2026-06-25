/**
 * @file time_complexity.cpp
 * @brief 时间复杂度优化示例
 *
 * 本文件演示算法时间复杂度对性能的影响：
 * 1. O(n^2) vs O(n log n) vs O(n)
 * 2. 哈希表 vs 线性搜索
 * 3. 算法选择的重要性
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <algorithm>
#include <unordered_set>
#include <set>
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
 * @brief 示例1: 排序算法复杂度对比
 */
void demonstrateSortingComplexity()
{
    std::cout << "=== 示例1: 排序算法复杂度对比 ===\n\n";

    std::vector<size_t> sizes = {1000, 10000, 100000};

    for (size_t N : sizes) {
        std::vector<int> data(N);
        std::mt19937 rng(42);
        std::uniform_int_distribution<int> dist(0, 1000000);
        for (auto& v : data) v = dist(rng);

        std::cout << "N = " << N << ":\n";

        // O(n^2) - 冒泡排序
        {
            std::vector<int> arr = data;
            Timer timer;
            for (size_t i = 0; i < N - 1; ++i) {
                for (size_t j = 0; j < N - i - 1; ++j) {
                    if (arr[j] > arr[j + 1]) {
                        std::swap(arr[j], arr[j + 1]);
                    }
                }
            }
            double time = timer.elapsedMs();
            std::cout << "  冒泡排序 O(n^2):    " << std::fixed << std::setprecision(2)
                      << time << " ms\n";
        }

        // O(n log n) - std::sort
        {
            std::vector<int> arr = data;
            Timer timer;
            std::sort(arr.begin(), arr.end());
            double time = timer.elapsedMs();
            std::cout << "  std::sort O(n log n): " << time << " ms\n";
        }
        std::cout << "\n";
    }
}

/**
 * @brief 示例2: 查找算法复杂度对比
 */
void demonstrateSearchComplexity()
{
    std::cout << "=== 示例2: 查找算法复杂度对比 ===\n\n";

    const size_t N = 100000;
    const size_t QUERIES = 10000;

    std::vector<int> data(N);
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(0, 1000000);
    for (auto& v : data) v = dist(rng);

    std::vector<int> queries(QUERIES);
    for (auto& q : queries) q = dist(rng);

    // O(n) - 线性搜索
    {
        Timer timer;
        volatile size_t found = 0;
        for (auto q : queries) {
            for (size_t i = 0; i < N; ++i) {
                if (data[i] == q) { ++found; break; }
            }
        }
        double time = timer.elapsedMs();
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "线性搜索 O(n):     " << time << " ms\n";
        (void)found;
    }

    // O(log n) - 二分搜索
    {
        std::vector<int> sorted_data = data;
        std::sort(sorted_data.begin(), sorted_data.end());
        Timer timer;
        volatile size_t found = 0;
        for (auto q : queries) {
            if (std::binary_search(sorted_data.begin(), sorted_data.end(), q)) {
                ++found;
            }
        }
        double time = timer.elapsedMs();
        std::cout << "二分搜索 O(log n): " << time << " ms\n";
        (void)found;
    }

    // O(1) - 哈希表
    {
        std::unordered_set<int> hash_set(data.begin(), data.end());
        Timer timer;
        volatile size_t found = 0;
        for (auto q : queries) {
            if (hash_set.count(q)) ++found;
        }
        double time = timer.elapsedMs();
        std::cout << "哈希表 O(1):       " << time << " ms\n";
        (void)found;
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  时间复杂度优化\n";
    std::cout << "========================================\n\n";

    std::cout << "说明: 算法选择对性能影响最大。\n";
    std::cout << "选择正确的算法复杂度比微优化重要得多。\n\n";

    demonstrateSortingComplexity();
    demonstrateSearchComplexity();

    std::cout << "========================================\n";
    std::cout << "  总结\n";
    std::cout << "========================================\n";
    std::cout << "1. 算法选择影响数量级性能\n";
    std::cout << "2. O(n log n) 优于 O(n^2)\n";
    std::cout << "3. 哈希表 O(1) 查找最快\n";
    std::cout << "4. 先选择正确算法，再微优化\n";

    return 0;
}
