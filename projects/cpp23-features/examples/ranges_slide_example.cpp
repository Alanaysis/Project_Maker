/**
 * @file ranges_slide_example.cpp
 * @brief C++23 std::views::slide 示例
 *
 * std::views::slide 是 C++23 引入的滑动窗口视图。
 * 它创建一个滑动窗口，每次移动一个元素。
 *
 * 主要特点：
 * - 创建固定大小的滑动窗口
 * - 每次移动一个元素
 * - 适用于移动平均、模式匹配等
 * - 支持惰性求值
 *
 * 编译命令：
 * g++ -std=c++23 -o ranges_slide_example ranges_slide_example.cpp
 */

#include <iostream>
#include <vector>
#include <ranges>
#include <algorithm>
#include <numeric>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8};

    // 创建大小为 3 的滑动窗口
    auto windows = data | std::views::slide(3);

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Sliding windows of size 3:" << std::endl;
    for (auto window : windows) {
        std::cout << "  [";
        bool first = true;
        for (int n : window) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 2. 不同窗口大小 ==========

void different_window_sizes() {
    std::cout << "\n=== 不同窗口大小 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6};

    // 窗口大小为 2
    std::cout << "Windows of size 2:" << std::endl;
    for (auto window : data | std::views::slide(2)) {
        std::cout << "  [";
        bool first = true;
        for (int n : window) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }

    // 窗口大小为 4
    std::cout << "\nWindows of size 4:" << std::endl;
    for (auto window : data | std::views::slide(4)) {
        std::cout << "  [";
        bool first = true;
        for (int n : window) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 3. 实际应用：移动平均 ==========

void moving_average() {
    std::cout << "\n=== 实际应用：移动平均 ===" << std::endl;

    // 模拟温度数据
    std::vector<double> temperatures = {
        20.5, 21.0, 19.8, 22.3, 23.1, 21.5, 20.8, 22.0, 23.5, 24.0
    };

    const size_t window_size = 3;

    std::cout << "Temperature data: ";
    for (double t : temperatures) std::cout << t << " ";
    std::cout << std::endl;

    // 计算移动平均
    std::cout << "Moving average (window=" << window_size << "):" << std::endl;
    for (auto window : temperatures | std::views::slide(window_size)) {
        double sum = 0;
        for (double t : window) sum += t;
        double avg = sum / window_size;

        std::cout << "  [";
        bool first = true;
        for (double t : window) {
            if (!first) std::cout << ", ";
            std::cout << t;
            first = false;
        }
        std::cout << "] -> " << avg << std::endl;
    }
}

// ========== 4. 实际应用：趋势检测 ==========

void trend_detection() {
    std::cout << "\n=== 实际应用：趋势检测 ===" << std::endl;

    // 股票价格数据
    std::vector<double> prices = {
        100.0, 102.5, 101.0, 103.5, 105.0, 104.0, 106.5, 108.0, 107.5, 109.0
    };

    std::cout << "Stock prices: ";
    for (double p : prices) std::cout << p << " ";
    std::cout << std::endl;

    // 使用滑动窗口检测趋势
    const size_t window_size = 3;
    std::cout << "Trend analysis (window=" << window_size << "):" << std::endl;

    for (auto window : prices | std::views::slide(window_size)) {
        std::vector<double> values(window.begin(), window.end());

        // 检查是否上涨
        bool increasing = true;
        for (size_t i = 1; i < values.size(); ++i) {
            if (values[i] <= values[i-1]) {
                increasing = false;
                break;
            }
        }

        // 检查是否下跌
        bool decreasing = true;
        for (size_t i = 1; i < values.size(); ++i) {
            if (values[i] >= values[i-1]) {
                decreasing = false;
                break;
            }
        }

        std::cout << "  [";
        bool first = true;
        for (double p : window) {
            if (!first) std::cout << ", ";
            std::cout << p;
            first = false;
        }
        std::cout << "] -> ";

        if (increasing) {
            std::cout << "Uptrend";
        } else if (decreasing) {
            std::cout << "Downtrend";
        } else {
            std::cout << "Sideways";
        }
        std::cout << std::endl;
    }
}

// ========== 5. 实际应用：模式匹配 ==========

void pattern_matching() {
    std::cout << "\n=== 实际应用：模式匹配 ===" << std::endl;

    // 二进制序列
    std::vector<int> binary = {1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0};

    std::cout << "Binary sequence: ";
    for (int b : binary) std::cout << b << " ";
    std::cout << std::endl;

    // 查找连续的 1
    const size_t pattern_size = 3;
    std::cout << "Looking for " << pattern_size << " consecutive 1s:" << std::endl;

    size_t position = 0;
    for (auto window : binary | std::views::slide(pattern_size)) {
        bool all_ones = true;
        for (int b : window) {
            if (b != 1) {
                all_ones = false;
                break;
            }
        }

        if (all_ones) {
            std::cout << "  Found at position " << position << ": [";
            bool first = true;
            for (int b : window) {
                if (!first) std::cout << ", ";
                std::cout << b;
                first = false;
            }
            std::cout << "]" << std::endl;
        }
        ++position;
    }
}

// ========== 6. 实际应用：异常检测 ==========

void anomaly_detection() {
    std::cout << "\n=== 实际应用：异常检测 ===" << std::endl;

    // 传感器数据
    std::vector<double> sensor_data = {
        10.0, 10.2, 10.1, 10.3, 15.0, 10.2, 10.1, 10.0, 10.3, 10.2
    };

    std::cout << "Sensor data: ";
    for (double d : sensor_data) std::cout << d << " ";
    std::cout << std::endl;

    // 使用滑动窗口检测异常
    const size_t window_size = 3;
    const double threshold = 2.0;

    std::cout << "Anomaly detection (window=" << window_size << ", threshold=" << threshold << "):" << std::endl;

    size_t position = 0;
    for (auto window : sensor_data | std::views::slide(window_size)) {
        std::vector<double> values(window.begin(), window.end());

        // 计算均值
        double mean = std::accumulate(values.begin(), values.end(), 0.0) / values.size();

        // 计算标准差
        double variance = 0;
        for (double v : values) {
            variance += (v - mean) * (v - mean);
        }
        variance /= values.size();
        double stddev = std::sqrt(variance);

        // 检测异常
        bool anomaly = false;
        for (double v : values) {
            if (std::abs(v - mean) > threshold * stddev) {
                anomaly = true;
                break;
            }
        }

        if (anomaly) {
            std::cout << "  Position " << position << ": [";
            bool first = true;
            for (double v : window) {
                if (!first) std::cout << ", ";
                std::cout << v;
                first = false;
            }
            std::cout << "] - ANOMALY DETECTED!" << std::endl;
        }
        ++position;
    }
}

// ========== 7. 实际应用：图像处理 ==========

void image_processing() {
    std::cout << "\n=== 实际应用：图像处理 ===" << std::endl;

    // 一维图像数据 (灰度)
    std::vector<int> pixels = {100, 120, 110, 130, 140, 120, 110, 100, 130, 140, 120, 110};

    std::cout << "Original pixels: ";
    for (int p : pixels) std::cout << p << " ";
    std::cout << std::endl;

    // 使用滑动窗口进行平滑
    const size_t window_size = 3;
    std::cout << "Smoothed pixels (window=" << window_size << "):" << std::endl;

    for (auto window : pixels | std::views::slide(window_size)) {
        int sum = 0;
        for (int p : window) sum += p;
        int avg = sum / window_size;

        std::cout << "  [";
        bool first = true;
        for (int p : window) {
            if (!first) std::cout << ", ";
            std::cout << p;
            first = false;
        }
        std::cout << "] -> " << avg << std::endl;
    }
}

// ========== 8. 实际应用：数据分析 ==========

void data_analysis() {
    std::cout << "\n=== 实际应用：数据分析 ===" << std::endl;

    // 销售数据
    std::vector<int> sales = {100, 150, 120, 180, 200, 170, 190, 160, 210, 230};

    std::cout << "Sales data: ";
    for (int s : sales) std::cout << s << " ";
    std::cout << std::endl;

    // 计算滚动最大值
    const size_t window_size = 3;
    std::cout << "Rolling maximum (window=" << window_size << "):" << std::endl;

    for (auto window : sales | std::views::slide(window_size)) {
        int max_val = *std::ranges::max_element(window);

        std::cout << "  [";
        bool first = true;
        for (int s : window) {
            if (!first) std::cout << ", ";
            std::cout << s;
            first = false;
        }
        std::cout << "] -> max=" << max_val << std::endl;
    }

    // 计算滚动最小值
    std::cout << "\nRolling minimum (window=" << window_size << "):" << std::endl;

    for (auto window : sales | std::views::slide(window_size)) {
        int min_val = *std::ranges::min_element(window);

        std::cout << "  [";
        bool first = true;
        for (int s : window) {
            if (!first) std::cout << ", ";
            std::cout << s;
            first = false;
        }
        std::cout << "] -> min=" << min_val << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::views::slide 示例\n" << std::endl;

    basic_usage();
    different_window_sizes();
    moving_average();
    trend_detection();
    pattern_matching();
    anomaly_detection();
    image_processing();
    data_analysis();

    return 0;
}
