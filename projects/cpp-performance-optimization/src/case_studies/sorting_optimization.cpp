/**
 * @file sorting_optimization.cpp
 * @brief 排序算法优化案例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <algorithm>
#include <random>
#include <numeric>
#include <thread>

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
 * @brief 基数排序（仅适用于整数）
 */
void radixSort(std::vector<int>& arr)
{
    if (arr.empty()) return;
    int max_val = *std::max_element(arr.begin(), arr.end());
    std::vector<int> output(arr.size());

    for (int exp = 1; max_val / exp > 0; exp *= 10) {
        std::vector<int> count(10, 0);
        for (auto v : arr) count[(v / exp) % 10]++;
        for (int i = 1; i < 10; ++i) count[i] += count[i - 1];
        for (int i = arr.size() - 1; i >= 0; --i) {
            output[count[(arr[i] / exp) % 10] - 1] = arr[i];
            count[(arr[i] / exp) % 10]--;
        }
        arr = output;
    }
}

void demonstrateSorting()
{
    std::cout << "=== 排序算法对比 ===\n\n";

    std::vector<size_t> sizes = {100000, 1000000};

    for (size_t N : sizes) {
        std::cout << "N = " << N << ":\n";

        std::vector<int> data(N);
        std::mt19937 rng(42);
        std::uniform_int_distribution<int> dist(0, 10000000);
        for (auto& v : data) v = dist(rng);

        // std::sort
        {
            std::vector<int> arr = data;
            Timer timer;
            std::sort(arr.begin(), arr.end());
            double time = timer.elapsedMs();
            std::cout << std::fixed << std::setprecision(2);
            std::cout << "  std::sort:    " << time << " ms\n";
        }

        // 基数排序
        {
            std::vector<int> arr = data;
            Timer timer;
            radixSort(arr);
            double time = timer.elapsedMs();
            std::cout << "  基数排序:     " << time << " ms\n";
        }

        // std::stable_sort
        {
            std::vector<int> arr = data;
            Timer timer;
            std::stable_sort(arr.begin(), arr.end());
            double time = timer.elapsedMs();
            std::cout << "  stable_sort:  " << time << " ms\n";
        }
        std::cout << "\n";
    }
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  排序算法优化\n";
    std::cout << "========================================\n\n";
    demonstrateSorting();
    std::cout << "总结: 基数排序对整数是 O(n)，比比较排序 O(n log n) 更快。\n";
    return 0;
}
