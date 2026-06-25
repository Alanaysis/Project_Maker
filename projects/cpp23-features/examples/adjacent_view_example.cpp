/**
 * @file adjacent_view_example.cpp
 * @brief C++23 std::views::adjacent 示例
 *
 * std::views::adjacent 是 C++23 引入的相邻元素视图。
 * 它可以同时访问范围中相邻的 N 个元素。
 *
 * 主要特点：
 * - 同时访问相邻的 N 个元素
 * - 支持结构化绑定
 * - 适用于差分、梯度计算等
 * - 支持惰性求值
 *
 * 编译命令：
 * g++ -std=c++23 -o adjacent_view_example adjacent_view_example.cpp
 */

#include <iostream>
#include <vector>
#include <ranges>
#include <algorithm>
#include <cmath>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8};

    // 获取相邻的 2 个元素
    std::cout << "Adjacent pairs:" << std::endl;
    for (auto [a, b] : data | std::views::adjacent<2>) {
        std::cout << "  (" << a << ", " << b << ")" << std::endl;
    }
}

// ========== 2. 三个相邻元素 ==========

void three_adjacent() {
    std::cout << "\n=== 三个相邻元素 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7};

    // 获取相邻的 3 个元素
    std::cout << "Adjacent triples:" << std::endl;
    for (auto [a, b, c] : data | std::views::adjacent<3>) {
        std::cout << "  (" << a << ", " << b << ", " << c << ")" << std::endl;
    }
}

// ========== 3. 实际应用：差分计算 ==========

void difference_calculation() {
    std::cout << "\n=== 实际应用：差分计算 ===" << std::endl;

    std::vector<double> values = {10.0, 12.5, 11.0, 13.5, 15.0, 14.0};

    std::cout << "Values: ";
    for (double v : values) std::cout << v << " ";
    std::cout << std::endl;

    // 计算一阶差分
    std::cout << "First differences:" << std::endl;
    for (auto [a, b] : values | std::views::adjacent<2>) {
        std::cout << "  " << b << " - " << a << " = " << (b - a) << std::endl;
    }
}

// ========== 4. 实际应用：梯度计算 ==========

void gradient_calculation() {
    std::cout << "\n=== 实际应用：梯度计算 ===" << std::endl;

    std::vector<double> positions = {0.0, 1.0, 4.0, 9.0, 16.0, 25.0};

    std::cout << "Positions: ";
    for (double p : positions) std::cout << p << " ";
    std::cout << std::endl;

    // 计算速度 (一阶导数)
    std::cout << "Velocities (first derivative):" << std::endl;
    for (auto [a, b] : positions | std::views::adjacent<2>) {
        double velocity = b - a;
        std::cout << "  " << velocity << std::endl;
    }

    // 计算加速度 (二阶导数)
    std::cout << "\nAccelerations (second derivative):" << std::endl;
    for (auto [a, b, c] : positions | std::views::adjacent<3>) {
        double acceleration = c - 2 * b + a;
        std::cout << "  " << acceleration << std::endl;
    }
}

// ========== 5. 实际应用：平滑处理 ==========

void smoothing() {
    std::cout << "\n=== 实际应用：平滑处理 ===" << std::endl;

    std::vector<double> noisy_data = {10.0, 12.5, 11.0, 13.5, 15.0, 14.0, 12.5, 11.0};

    std::cout << "Original data: ";
    for (double v : noisy_data) std::cout << v << " ";
    std::cout << std::endl;

    // 使用相邻 3 个元素进行平滑
    std::cout << "Smoothed data (3-point average):" << std::endl;
    for (auto [a, b, c] : noisy_data | std::views::adjacent<3>) {
        double smoothed = (a + b + c) / 3.0;
        std::cout << "  (" << a << " + " << b << " + " << c << ") / 3 = " << smoothed << std::endl;
    }
}

// ========== 6. 实际应用：趋势检测 ==========

void trend_detection() {
    std::cout << "\n=== 实际应用：趋势检测 ===" << std::endl;

    std::vector<double> prices = {100.0, 102.5, 105.0, 103.0, 101.0, 104.0, 107.0};

    std::cout << "Prices: ";
    for (double p : prices) std::cout << p << " ";
    std::cout << std::endl;

    // 检测趋势变化
    std::cout << "Trend analysis:" << std::endl;
    for (auto [a, b, c] : prices | std::views::adjacent<3>) {
        bool increasing = (b > a) && (c > b);
        bool decreasing = (b < a) && (c < b);

        std::cout << "  [" << a << ", " << b << ", " << c << "] -> ";
        if (increasing) {
            std::cout << "Uptrend";
        } else if (decreasing) {
            std::cout << "Downtrend";
        } else {
            std::cout << "Mixed";
        }
        std::cout << std::endl;
    }
}

// ========== 7. 实际应用：异常检测 ==========

void anomaly_detection() {
    std::cout << "\n=== 实际应用：异常检测 ===" << std::endl;

    std::vector<double> sensor_data = {10.0, 10.2, 10.1, 15.0, 10.3, 10.2, 10.1};

    std::cout << "Sensor data: ";
    for (double v : sensor_data) std::cout << v << " ";
    std::cout << std::endl;

    // 检测异常值
    std::cout << "Anomaly detection:" << std::endl;
    for (auto [a, b, c] : sensor_data | std::views::adjacent<3>) {
        double mean = (a + c) / 2.0;
        double deviation = std::abs(b - mean);

        if (deviation > 2.0) {
            std::cout << "  [" << a << ", " << b << ", " << c << "] - ANOMALY DETECTED!" << std::endl;
        }
    }
}

// ========== 8. 实际应用：图像边缘检测 ==========

void edge_detection() {
    std::cout << "\n=== 实际应用：图像边缘检测 ===" << std::endl;

    // 一维像素数据
    std::vector<int> pixels = {100, 100, 100, 200, 200, 200, 100, 100, 100};

    std::cout << "Pixels: ";
    for (int p : pixels) std::cout << p << " ";
    std::cout << std::endl;

    // 使用 Sobel 算子检测边缘
    std::cout << "Edge detection (Sobel):" << std::endl;
    for (auto [a, b, c] : pixels | std::views::adjacent<3>) {
        int edge = std::abs(c - a);
        std::cout << "  [" << a << ", " << b << ", " << c << "] -> edge=" << edge << std::endl;
    }
}

// ========== 9. 实际应用：数据压缩 ==========

void data_compression() {
    std::cout << "\n=== 实际应用：数据压缩 ===" << std::endl;

    std::vector<int> data = {100, 102, 104, 106, 108, 110};

    std::cout << "Original data: ";
    for (int d : data) std::cout << d << " ";
    std::cout << std::endl;

    // 差分编码
    std::cout << "Differential encoding:" << std::endl;
    std::cout << "  First value: " << data[0] << std::endl;
    for (auto [a, b] : data | std::views::adjacent<2>) {
        std::cout << "  Difference: " << (b - a) << std::endl;
    }
}

// ========== 10. 实际应用：统计分析 ==========

void statistical_analysis() {
    std::cout << "\n=== 实际应用：统计分析 ===" << std::endl;

    std::vector<double> data = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0};

    // 计算移动相关系数
    std::cout << "Moving correlation (window=3):" << std::endl;
    for (auto [a, b, c] : data | std::views::adjacent<3>) {
        // 简化的相关性计算
        double mean = (a + b + c) / 3.0;
        double variance = ((a - mean) * (a - mean) + (b - mean) * (b - mean) + (c - mean) * (c - mean)) / 3.0;
        double stddev = std::sqrt(variance);

        std::cout << "  [" << a << ", " << b << ", " << c << "] -> mean=" << mean
                  << ", stddev=" << stddev << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::views::adjacent 示例\n" << std::endl;

    basic_usage();
    three_adjacent();
    difference_calculation();
    gradient_calculation();
    smoothing();
    trend_detection();
    anomaly_detection();
    edge_detection();
    data_compression();
    statistical_analysis();

    return 0;
}
