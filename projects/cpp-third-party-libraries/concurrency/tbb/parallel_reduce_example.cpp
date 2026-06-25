/**
 * @file parallel_reduce_example.cpp
 * @brief Intel TBB parallel_reduce 示例
 * @details 展示 Intel TBB 的 parallel_reduce 用法
 */

#include <iostream>
#include <vector>
#include <numeric>
#include <tbb/parallel_reduce.h>
#include <tbb/blocked_range.h>

/**
 * @brief 基础 parallel_reduce 示例
 * @details 展示 parallel_reduce 的基本用法
 */
void basic_reduce() {
    std::cout << "=== 基础 parallel_reduce ===" << std::endl;

    const int n = 1000000;
    std::vector<double> data(n);
    std::iota(data.begin(), data.end(), 1.0);

    // 串行求和
    auto start = std::chrono::high_resolution_clock::now();
    double serial_sum = std::accumulate(data.begin(), data.end(), 0.0);
    auto end = std::chrono::high_resolution_clock::now();
    auto serial_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "Serial sum: " << serial_sum << std::endl;
    std::cout << "Serial time: " << serial_time.count() << " microseconds" << std::endl;

    // 并行求和
    start = std::chrono::high_resolution_clock::now();
    double parallel_sum = tbb::parallel_reduce(
        tbb::blocked_range<int>(0, n),
        0.0,
        [&data](const tbb::blocked_range<int>& r, double init) -> double {
            for (int i = r.begin(); i != r.end(); ++i) {
                init += data[i];
            }
            return init;
        },
        [](double a, double b) -> double {
            return a + b;
        }
    );
    end = std::chrono::high_resolution_clock::now();
    auto parallel_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "Parallel sum: " << parallel_sum << std::endl;
    std::cout << "Parallel time: " << parallel_time.count() << " microseconds" << std::endl;
    std::cout << "Speedup: " << (double)serial_time.count() / parallel_time.count() << "x" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 简化语法示例
 * @details 展示 parallel_reduce 的简化用法
 */
void simplified_reduce() {
    std::cout << "=== 简化语法 ===" << std::endl;

    const int n = 1000000;
    std::vector<double> data(n);
    std::iota(data.begin(), data.end(), 1.0);

    // 使用简化语法
    double sum = tbb::parallel_reduce(
        tbb::blocked_range<int>(0, n),
        0.0,
        [&data](const tbb::blocked_range<int>& r, double init) -> double {
            for (int i = r.begin(); i != r.end(); ++i) {
                init += data[i];
            }
            return init;
        },
        [](double a, double b) -> double {
            return a + b;
        }
    );

    std::cout << "Sum: " << sum << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 查找最小值示例
 * @details 展示如何使用 parallel_reduce 查找最小值
 */
void find_minimum() {
    std::cout << "=== 查找最小值 ===" << std::endl;

    const int n = 1000000;
    std::vector<double> data(n);
    std::iota(data.begin(), data.end(), 1.0);
    data[500000] = -100.0;  // 设置一个最小值

    // 串行查找
    double serial_min = *std::min_element(data.begin(), data.end());
    std::cout << "Serial min: " << serial_min << std::endl;

    // 并行查找
    double parallel_min = tbb::parallel_reduce(
        tbb::blocked_range<int>(0, n),
        std::numeric_limits<double>::max(),
        [&data](const tbb::blocked_range<int>& r, double init) -> double {
            for (int i = r.begin(); i != r.end(); ++i) {
                if (data[i] < init) {
                    init = data[i];
                }
            }
            return init;
        },
        [](double a, double b) -> double {
            return std::min(a, b);
        }
    );

    std::cout << "Parallel min: " << parallel_min << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 parallel_reduce 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：计算向量范数
    const int n = 1000000;
    std::vector<double> data(n);
    std::iota(data.begin(), data.end(), 1.0);

    // 并行计算平方和
    double sum_of_squares = tbb::parallel_reduce(
        tbb::blocked_range<int>(0, n),
        0.0,
        [&data](const tbb::blocked_range<int>& r, double init) -> double {
            for (int i = r.begin(); i != r.end(); ++i) {
                init += data[i] * data[i];
            }
            return init;
        },
        [](double a, double b) -> double {
            return a + b;
        }
    );

    double norm = std::sqrt(sum_of_squares);
    std::cout << "Vector norm: " << norm << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Intel TBB parallel_reduce 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_reduce();
    simplified_reduce();
    find_minimum();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}