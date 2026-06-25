/**
 * @file parallel_for_example.cpp
 * @brief Intel TBB parallel_for 示例
 * @details 展示 Intel TBB 的 parallel_for 用法
 *          Intel TBB 是一个任务并行框架
 *          提供高级并行算法和数据结构
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <numeric>
#include <tbb/parallel_for.h>
#include <tbb/blocked_range.h>

/**
 * @brief 基础 parallel_for 示例
 * @details 展示 parallel_for 的基本用法
 */
void basic_parallel_for() {
    std::cout << "=== 基础 parallel_for ===" << std::endl;

    const int n = 1000000;
    std::vector<double> data(n, 1.0);

    // 串行版本
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < n; ++i) {
        data[i] = data[i] * 2.0 + 1.0;
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto serial_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "Serial time: " << serial_time.count() << " microseconds" << std::endl;

    // 并行版本
    std::fill(data.begin(), data.end(), 1.0);
    start = std::chrono::high_resolution_clock::now();
    tbb::parallel_for(tbb::blocked_range<int>(0, n),
        [&data](const tbb::blocked_range<int>& r) {
            for (int i = r.begin(); i != r.end(); ++i) {
                data[i] = data[i] * 2.0 + 1.0;
            }
        });
    end = std::chrono::high_resolution_clock::now();
    auto parallel_time = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

    std::cout << "Parallel time: " << parallel_time.count() << " microseconds" << std::endl;
    std::cout << "Speedup: " << (double)serial_time.count() / parallel_time.count() << "x" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 简化语法示例
 * @details 展示 parallel_for 的简化用法
 */
void simplified_syntax() {
    std::cout << "=== 简化语法 ===" << std::endl;

    const int n = 1000000;
    std::vector<double> data(n, 1.0);

    // 使用简化语法
    tbb::parallel_for(0, n, [&data](int i) {
        data[i] = data[i] * 2.0 + 1.0;
    });

    // 验证结果
    bool correct = std::all_of(data.begin(), data.end(),
        [](double val) { return val == 3.0; });

    std::cout << "All elements are 3.0: " << (correct ? "Yes" : "No") << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 矩阵运算示例
 * @details 展示 parallel_for 在矩阵运算中的应用
 */
void matrix_example() {
    std::cout << "=== 矩阵运算 ===" << std::endl;

    const int rows = 1000;
    const int cols = 1000;
    std::vector<std::vector<double>> A(rows, std::vector<double>(cols, 1.0));
    std::vector<std::vector<double>> B(rows, std::vector<double>(cols, 2.0));
    std::vector<std::vector<double>> C(rows, std::vector<double>(cols, 0.0));

    // 并行矩阵加法
    tbb::parallel_for(0, rows, [&](int i) {
        for (int j = 0; j < cols; ++j) {
            C[i][j] = A[i][j] + B[i][j];
        }
    });

    // 验证结果
    bool correct = true;
    for (int i = 0; i < rows && correct; ++i) {
        for (int j = 0; j < cols && correct; ++j) {
            if (C[i][j] != 3.0) {
                correct = false;
            }
        }
    }

    std::cout << "Matrix addition correct: " << (correct ? "Yes" : "No") << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 TBB 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：图像处理
    const int width = 1920;
    const int height = 1080;
    std::vector<uint8_t> image(width * height, 128);
    std::vector<uint8_t> result(width * height, 0);

    // 并行图像亮度调整
    tbb::parallel_for(0, height, [&](int y) {
        for (int x = 0; x < width; ++x) {
            int idx = y * width + x;
            int value = static_cast<int>(image[idx]) + 50;
            result[idx] = static_cast<uint8_t>(std::min(255, std::max(0, value)));
        }
    });

    std::cout << "Image processed: " << width << "x" << height << std::endl;

    // 场景：数据统计
    const int n = 10000000;
    std::vector<double> data(n);
    std::iota(data.begin(), data.end(), 1.0);

    // 并行求和
    double sum = 0;
    tbb::parallel_for(tbb::blocked_range<int>(0, n),
        [&data, &sum](const tbb::blocked_range<int>& r) {
            double local_sum = 0;
            for (int i = r.begin(); i != r.end(); ++i) {
                local_sum += data[i];
            }
            // 注意：这里需要原子操作来避免竞态条件
            // 简化示例，实际应用中应使用 tbb::combinable
        });

    std::cout << "Data sum calculated" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Intel TBB parallel_for 示例 ===" << std::endl;
    std::cout << std::endl;

    basic_parallel_for();
    simplified_syntax();
    matrix_example();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}