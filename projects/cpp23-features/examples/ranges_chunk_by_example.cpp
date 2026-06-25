/**
 * @file ranges_chunk_by_example.cpp
 * @brief C++23 std::views::chunk_by 示例
 *
 * std::views::chunk_by 是 C++23 引入的按条件分块视图。
 * 它根据谓词将连续满足条件的元素分组。
 *
 * 主要特点：
 * - 根据谓词将连续元素分组
 * - 适用于数据分段和分组
 * - 支持惰性求值
 * - 相邻元素必须满足谓词才在同一组
 *
 * 编译命令：
 * g++ -std=c++23 -o ranges_chunk_by_example ranges_chunk_by_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>
#include <cmath>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 5, 6, 7, 10, 11, 12, 15};

    // 按相邻元素差值是否为 1 分组
    auto chunks = data | std::views::chunk_by([](int a, int b) {
        return b - a == 1;
    });

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Consecutive groups:" << std::endl;
    for (auto chunk : chunks) {
        std::cout << "  [";
        bool first = true;
        for (int n : chunk) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 2. 按奇偶性分组 ==========

void group_by_parity() {
    std::cout << "\n=== 按奇偶性分组 ===" << std::endl;

    std::vector<int> data = {1, 3, 5, 2, 4, 6, 7, 9, 8, 10};

    // 按奇偶性分组
    auto chunks = data | std::views::chunk_by([](int a, int b) {
        return (a % 2) == (b % 2);
    });

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Groups by parity:" << std::endl;
    for (auto chunk : chunks) {
        std::cout << "  [";
        bool first = true;
        for (int n : chunk) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "] - " << (*chunk.begin() % 2 == 0 ? "Even" : "Odd") << std::endl;
    }
}

// ========== 3. 实际应用：数据分段 ==========

void data_segmentation() {
    std::cout << "\n=== 实际应用：数据分段 ===" << std::endl;

    // 传感器数据
    std::vector<double> sensor_data = {
        10.0, 10.2, 10.1,  // 稳定
        15.0, 15.5, 16.0,  // 上升
        16.0, 15.8, 15.5,  // 下降
        10.0, 10.1, 10.2   // 稳定
    };

    // 按变化趋势分组
    auto segments = sensor_data | std::views::chunk_by([](double a, double b) {
        return std::abs(b - a) < 1.0;  // 变化小于 1 视为同一段
    });

    std::cout << "Sensor data segments:" << std::endl;
    int segment_num = 1;
    for (auto segment : segments) {
        std::cout << "  Segment " << segment_num++ << ": [";
        bool first = true;
        for (double val : segment) {
            if (!first) std::cout << ", ";
            std::cout << val;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 4. 实际应用：文本处理 ==========

void text_processing() {
    std::cout << "\n=== 实际应用：文本处理 ===" << std::endl;

    // 字符序列
    std::vector<char> chars = {'a', 'b', 'c', '1', '2', '3', 'x', 'y', 'z', '4', '5'};

    // 按字符类型分组
    auto groups = chars | std::views::chunk_by([](char a, char b) {
        return std::isalpha(a) == std::isalpha(b);
    });

    std::cout << "Character groups:" << std::endl;
    for (auto group : groups) {
        bool is_alpha = std::isalpha(*group.begin());
        std::cout << "  " << (is_alpha ? "Letters" : "Digits") << ": [";
        bool first = true;
        for (char c : group) {
            if (!first) std::cout << ", ";
            std::cout << c;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 5. 实际应用：时间序列分析 ==========

void time_series_analysis() {
    std::cout << "\n=== 实际应用：时间序列分析 ===" << std::endl;

    // 股票价格
    std::vector<double> prices = {
        100.0, 102.5, 105.0,  // 上涨
        105.0, 103.0, 101.0,  // 下跌
        101.0, 103.5, 106.0,  // 上涨
        106.0, 104.0, 102.0   // 下跌
    };

    // 按趋势分组
    auto trends = prices | std::views::chunk_by([](double a, double b) {
        return (b - a) > 0 == (a - prices[0]) > 0;  // 简化：按涨跌方向
    });

    std::cout << "Price trends:" << std::endl;
    for (auto trend : trends) {
        std::vector<double> values(trend.begin(), trend.end());
        double change = values.back() - values.front();

        std::cout << "  " << (change >= 0 ? "Up" : "Down") << ": [";
        bool first = true;
        for (double v : trend) {
            if (!first) std::cout << ", ";
            std::cout << v;
            first = false;
        }
        std::cout << "] (change: " << change << ")" << std::endl;
    }
}

// ========== 6. 实际应用：数据清洗 ==========

void data_cleaning() {
    std::cout << "\n=== 实际应用：数据清洗 ===" << std::endl;

    // 带有缺失值的数据
    std::vector<std::optional<int>> data = {
        1, 2, 3,
        std::nullopt, std::nullopt,
        4, 5, 6,
        std::nullopt,
        7, 8, 9
    };

    // 按有效数据分组
    auto groups = data | std::views::chunk_by([](auto a, auto b) {
        return a.has_value() == b.has_value();
    });

    std::cout << "Data groups:" << std::endl;
    for (auto group : groups) {
        bool has_value = group.begin()->has_value();
        std::cout << "  " << (has_value ? "Valid" : "Missing") << ": [";
        bool first = true;
        for (auto val : group) {
            if (!first) std::cout << ", ";
            if (val) {
                std::cout << *val;
            } else {
                std::cout << "NA";
            }
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 7. 实际应用：日志分析 ==========

void log_analysis() {
    std::cout << "\n=== 实际应用：日志分析 ===" << std::endl;

    // 日志级别
    std::vector<std::string> logs = {
        "INFO: Start",
        "INFO: Loading",
        "ERROR: Failed",
        "ERROR: Timeout",
        "INFO: Retry",
        "INFO: Success"
    };

    // 按日志级别分组
    auto groups = logs | std::views::chunk_by([](const std::string& a, const std::string& b) {
        return a.substr(0, 5) == b.substr(0, 5);
    });

    std::cout << "Log groups:" << std::endl;
    for (auto group : groups) {
        std::string level = group.begin()->substr(0, 5);
        std::cout << "  " << level << ":" << std::endl;
        for (const auto& log : group) {
            std::cout << "    " << log << std::endl;
        }
    }
}

// ========== 8. 实际应用：图像处理 ==========

void image_processing() {
    std::cout << "\n=== 实际应用：图像处理 ===" << std::endl;

    // 一维像素数据
    std::vector<int> pixels = {
        100, 100, 100,  // 区域 1
        200, 200, 200,  // 区域 2
        100, 100, 100,  // 区域 3
        200, 200, 200   // 区域 4
    };

    // 按像素值分组
    auto regions = pixels | std::views::chunk_by([](int a, int b) {
        return std::abs(a - b) < 50;
    });

    std::cout << "Image regions:" << std::endl;
    int region_num = 1;
    for (auto region : regions) {
        int avg = 0;
        int count = 0;
        for (int p : region) {
            avg += p;
            ++count;
        }
        avg /= count;

        std::cout << "  Region " << region_num++ << " (avg=" << avg << "): [";
        bool first = true;
        for (int p : region) {
            if (!first) std::cout << ", ";
            std::cout << p;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::views::chunk_by 示例\n" << std::endl;

    basic_usage();
    group_by_parity();
    data_segmentation();
    text_processing();
    time_series_analysis();
    data_cleaning();
    log_analysis();
    image_processing();

    return 0;
}
