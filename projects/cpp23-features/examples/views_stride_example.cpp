/**
 * @file views_stride_example.cpp
 * @brief C++23 std::views::stride 示例
 *
 * std::views::stride 是 C++23 引入的步长视图。
 * 它可以按指定步长跳过元素。
 *
 * 主要特点：
 * - 按指定步长跳过元素
 * - 支持采样和降采样
 * - 适用于数据采样和索引操作
 * - 支持惰性求值
 *
 * 编译命令：
 * g++ -std=c++23 -o views_stride_example views_stride_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 步长为 2
    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Stride 2: ";
    for (int n : data | std::views::stride(2)) std::cout << n << " ";
    std::cout << std::endl;

    // 步长为 3
    std::cout << "Stride 3: ";
    for (int n : data | std::views::stride(3)) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 2. 不同步长 ==========

void different_strides() {
    std::cout << "\n=== 不同步长 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};

    for (int s = 1; s <= 4; ++s) {
        std::cout << "Stride " << s << ": ";
        for (int n : data | std::views::stride(s)) std::cout << n << " ";
        std::cout << std::endl;
    }
}

// ========== 3. 实际应用：数据采样 ==========

void data_sampling() {
    std::cout << "\n=== 实际应用：数据采样 ===" << std::endl;

    // 模拟高频数据
    std::vector<double> high_freq_data;
    for (int i = 0; i < 20; ++i) {
        high_freq_data.push_back(i * 0.5);
    }

    std::cout << "High frequency data (20 samples): ";
    for (double v : high_freq_data) std::cout << v << " ";
    std::cout << std::endl;

    // 降采样 (每 4 个取 1 个)
    std::cout << "Downsampled (stride=4): ";
    for (double v : high_freq_data | std::views::stride(4)) std::cout << v << " ";
    std::cout << std::endl;

    // 降采样 (每 5 个取 1 个)
    std::cout << "Downsampled (stride=5): ";
    for (double v : high_freq_data | std::views::stride(5)) std::cout << v << " ";
    std::cout << std::endl;
}

// ========== 4. 实际应用：图像处理 ==========

void image_processing() {
    std::cout << "\n=== 实际应用：图像处理 ===" << std::endl;

    // 模拟图像数据 (4x4)
    std::vector<int> pixels = {
        100, 110, 120, 130,
        140, 150, 160, 170,
        180, 190, 200, 210,
        220, 230, 240, 250
    };

    std::cout << "Original image (4x4):" << std::endl;
    for (size_t i = 0; i < 4; ++i) {
        for (size_t j = 0; j < 4; ++j) {
            std::cout << pixels[i * 4 + j] << "\t";
        }
        std::cout << std::endl;
    }

    // 降采样 (每隔一个像素取一个)
    std::cout << "\nDownsampled (stride=2):" << std::endl;
    auto downsampled = pixels | std::views::stride(2);
    for (size_t i = 0; i < 2; ++i) {
        for (size_t j = 0; j < 2; ++j) {
            std::cout << *(downsampled.begin() + i * 2 + j) << "\t";
        }
        std::cout << std::endl;
    }
}

// ========== 5. 实际应用：时间序列 ==========

void time_series() {
    std::cout << "\n=== 实际应用：时间序列 ===" << std::endl;

    // 每小时数据
    std::vector<double> hourly_data = {
        10.0, 10.5, 11.0, 11.5, 12.0, 12.5,
        13.0, 13.5, 14.0, 14.5, 15.0, 15.5,
        16.0, 16.5, 17.0, 17.5, 18.0, 18.5,
        19.0, 19.5, 20.0, 20.5, 21.0, 21.5
    };

    std::cout << "Hourly data (24 hours): ";
    for (double v : hourly_data) std::cout << v << " ";
    std::cout << std::endl;

    // 每 6 小时采样
    std::cout << "Every 6 hours: ";
    for (double v : hourly_data | std::views::stride(6)) std::cout << v << " ";
    std::cout << std::endl;

    // 每 12 小时采样
    std::cout << "Every 12 hours: ";
    for (double v : hourly_data | std::views::stride(12)) std::cout << v << " ";
    std::cout << std::endl;
}

// ========== 6. 实际应用：音频处理 ==========

void audio_processing() {
    std::cout << "\n=== 实际应用：音频处理 ===" << std::endl;

    // 模拟音频样本
    std::vector<int> audio_samples;
    for (int i = 0; i < 20; ++i) {
        audio_samples.push_back(static_cast<int>(128 + 50 * std::sin(i * 0.5)));
    }

    std::cout << "Original audio (20 samples): ";
    for (int s : audio_samples) std::cout << s << " ";
    std::cout << std::endl;

    // 降采样
    std::cout << "Downsampled (stride=2): ";
    for (int s : audio_samples | std::views::stride(2)) std::cout << s << " ";
    std::cout << std::endl;
}

// ========== 7. 实际应用：数据压缩 ==========

void data_compression() {
    std::cout << "\n=== 实际应用：数据压缩 ===" << std::endl;

    // 原始数据
    std::vector<int> data = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100};

    std::cout << "Original data: ";
    for (int d : data) std::cout << d << " ";
    std::cout << std::endl;

    // 奇数索引
    std::cout << "Odd indices (stride=2, offset=0): ";
    for (int d : data | std::views::stride(2)) std::cout << d << " ";
    std::cout << std::endl;

    // 偶数索引
    std::cout << "Even indices (stride=2, offset=1): ";
    auto even_indices = data | std::views::drop(1) | std::views::stride(2);
    for (int d : even_indices) std::cout << d << " ";
    std::cout << std::endl;
}

// ========== 8. 实际应用：性能测试 ==========

void performance_testing() {
    std::cout << "\n=== 实际应用：性能测试 ===" << std::endl;

    // 大数据集
    std::vector<int> large_data(100);
    std::iota(large_data.begin(), large_data.end(), 1);

    // 测试不同步长
    for (int stride = 1; stride <= 5; ++stride) {
        int count = 0;
        for (int n : large_data | std::views::stride(stride)) {
            ++count;
        }
        std::cout << "Stride " << stride << ": " << count << " elements" << std::endl;
    }
}

// ========== 9. 实际应用：数据可视化 ==========

void data_visualization() {
    std::cout << "\n=== 实际应用：数据可视化 ===" << std::endl;

    // 数据点
    std::vector<double> data = {1.0, 2.5, 4.0, 5.5, 7.0, 8.5, 10.0, 11.5, 13.0, 14.5};

    std::cout << "Data points: ";
    for (double v : data) std::cout << v << " ";
    std::cout << std::endl;

    // 简化显示
    std::cout << "Simplified (stride=2): ";
    for (double v : data | std::views::stride(2)) std::cout << v << " ";
    std::cout << std::endl;
}

// ========== 10. 实际应用：索引生成 ==========

void index_generation() {
    std::cout << "\n=== 实际应用：索引生成 ===" << std::endl;

    // 生成偶数索引
    std::cout << "Even indices: ";
    for (int i : std::views::iota(0, 10) | std::views::stride(2)) {
        std::cout << i << " ";
    }
    std::cout << std::endl;

    // 生成奇数索引
    std::cout << "Odd indices: ";
    for (int i : std::views::iota(1, 10) | std::views::stride(2)) {
        std::cout << i << " ";
    }
    std::cout << std::endl;
}

int main() {
    std::cout << "C++23 std::views::stride 示例\n" << std::endl;

    basic_usage();
    different_strides();
    data_sampling();
    image_processing();
    time_series();
    audio_processing();
    data_compression();
    performance_testing();
    data_visualization();
    index_generation();

    return 0;
}
