// quantization.cpp - 量化处理演示
//
// 本文件演示音频量化的基本原理：
// 1. 量化过程（连续值→离散值）
// 2. 不同位深度的效果
// 3. 量化噪声与信噪比（SNR）
// 4. 抖动（Dither）技术
//
// 编译: g++ -std=c++17 -I../../include quantization.cpp -o quantization -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <iomanip>

using namespace audio;

// 将浮点值量化到指定位深度
float quantize(float sample, int bits) {
    int levels = (1 << bits) - 1;  // 量化级数
    float min_val = -1.0f;
    float max_val = 1.0f;

    // 将 [-1, 1] 映射到 [0, levels]
    float normalized = (sample - min_val) / (max_val - min_val);
    int quantized = static_cast<int>(normalized * levels + 0.5f);
    quantized = std::max(0, std::min(levels, quantized));

    // 映射回 [-1, 1]
    return min_val + (max_val - min_val) * quantized / levels;
}

// 计算信噪比（SNR）
float calculate_snr(const std::vector<float>& original,
                    const std::vector<float>& quantized) {
    float signal_power = 0.0f;
    float noise_power = 0.0f;

    for (size_t i = 0; i < original.size(); ++i) {
        signal_power += original[i] * original[i];
        float noise = original[i] - quantized[i];
        noise_power += noise * noise;
    }

    if (noise_power == 0.0f) return 100.0f; // 无噪声
    return 10.0f * std::log10(signal_power / noise_power);
}

// 添加抖动
float add_dither(float sample, float amplitude) {
    static std::mt19937 gen(42);
    std::uniform_real_distribution<float> dist(-amplitude, amplitude);
    return sample + dist(gen);
}

// 演示量化过程
void demo_quantization_process() {
    print_separator("量化过程演示");

    std::cout << "\n量化：将连续采样值映射到有限的离散级别\n" << std::endl;

    float sample = 0.7071f; // sqrt(2)/2
    std::cout << "原始采样值: " << sample << std::endl;

    std::vector<int> bit_depths = {8, 12, 16, 24};

    for (int bits : bit_depths) {
        int levels = (1 << bits) - 1;
        float quantized = quantize(sample, bits);
        float error = sample - quantized;

        std::cout << "\n" << bits << "-bit 量化:" << std::endl;
        std::cout << "  量化级数: " << levels << std::endl;
        std::cout << "  量化值: " << quantized << std::endl;
        std::cout << "  量化误差: " << error << std::endl;
        std::cout << "  理论 SNR: " << (6.02 * bits + 1.76) << " dB" << std::endl;
    }
}

// 演示不同位深度的效果
void demo_bit_depth_effect() {
    print_separator("位深度效果对比");

    std::cout << "\n位深度越高，动态范围越大，量化噪声越小\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;
    float freq = 1000.0f;

    // 生成原始信号
    auto original = generate_sine(freq, sample_rate, duration);

    std::vector<int> bit_depths = {8, 12, 16, 24};

    std::cout << "位深度 | 量化级数 | 动态范围 | SNR" << std::endl;
    std::cout << "-------|---------|----------|-----" << std::endl;

    for (int bits : bit_depths) {
        // 量化
        std::vector<float> quantized(original.size());
        for (size_t i = 0; i < original.size(); ++i) {
            quantized[i] = quantize(original[i], bits);
        }

        int levels = (1 << bits) - 1;
        float dynamic_range = 6.02 * bits + 1.76;
        float snr = calculate_snr(original, quantized);

        printf("%6d | %7d | %6.1f dB | %.1f dB\n",
               bits, levels, dynamic_range, snr);

        // 保存文件
        AudioBuffer buffer = make_buffer(quantized, static_cast<uint32_t>(sample_rate));
        buffer.bit_depth = bits;
        std::string filename = "quantized_" + std::to_string(bits) + "bit.wav";
        write_wav(filename, buffer);
    }
}

// 演示量化噪声
void demo_quantization_noise() {
    print_separator("量化噪声");

    std::cout << "\n量化噪声 = 原始信号 - 量化信号\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 0.01f; // 10ms
    float freq = 1000.0f;

    auto original = generate_sine(freq, sample_rate, duration);

    // 8-bit 量化
    std::vector<float> quantized(original.size());
    std::vector<float> noise(original.size());

    for (size_t i = 0; i < original.size(); ++i) {
        quantized[i] = quantize(original[i], 8);
        noise[i] = original[i] - quantized[i];
    }

    // 显示前 20 个采样点
    std::cout << "采样点 | 原始值  | 量化值  | 噪声" << std::endl;
    std::cout << "-------|---------|---------|--------" << std::endl;

    for (size_t i = 0; i < 20; ++i) {
        printf("%6zu | %+.4f | %+.4f | %+.4f\n",
               i, original[i], quantized[i], noise[i]);
    }

    // 保存噪声信号
    AudioBuffer noise_buffer = make_buffer(noise, static_cast<uint32_t>(sample_rate));
    write_wav("quantization_noise.wav", noise_buffer);
    std::cout << "\n量化噪声已保存到 quantization_noise.wav" << std::endl;
}

// 演示抖动技术
void demo_dithering() {
    print_separator("抖动技术 (Dithering)");

    std::cout << "\n抖动：在量化前添加低电平噪声，改善量化特性\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;
    float freq = 1000.0f;

    auto original = generate_sine(freq, sample_rate, duration);

    // 不使用抖动的 8-bit 量化
    std::vector<float> no_dither(original.size());
    for (size_t i = 0; i < original.size(); ++i) {
        no_dither[i] = quantize(original[i], 8);
    }

    // 使用抖动的 8-bit 量化
    std::vector<float> with_dither(original.size());
    float dither_amplitude = 1.0f / 128.0f; // 1 LSB
    for (size_t i = 0; i < original.size(); ++i) {
        float dithered = add_dither(original[i], dither_amplitude);
        with_dither[i] = quantize(dithered, 8);
    }

    float snr_no_dither = calculate_snr(original, no_dither);
    float snr_with_dither = calculate_snr(original, with_dither);

    std::cout << "无抖动 SNR: " << snr_no_dither << " dB" << std::endl;
    std::cout << "有抖动 SNR: " << snr_with_dither << " dB" << std::endl;
    std::cout << "\n注意：抖动不会降低总噪声，但使噪声更均匀分布" << std::endl;
    std::cout << "这改善了低电平信号的听感" << std::endl;

    // 保存文件
    AudioBuffer no_dither_buf = make_buffer(no_dither, static_cast<uint32_t>(sample_rate));
    AudioBuffer with_dither_buf = make_buffer(with_dither, static_cast<uint32_t>(sample_rate));

    write_wav("quantized_no_dither.wav", no_dither_buf);
    write_wav("quantized_with_dither.wav", with_dither_buf);
}

// 演示不同信号的量化
void demo_signal_quantization() {
    print_separator("不同信号的量化");

    std::cout << "\n静音信号的量化问题：\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;

    // 生成低电平正弦波（-60dB）
    float amplitude = db_to_linear(-60.0f);
    auto quiet_signal = generate_sine(1000.0f, sample_rate, duration, amplitude);

    // 8-bit 量化
    std::vector<float> quantized(quiet_signal.size());
    for (size_t i = 0; i < quiet_signal.size(); ++i) {
        quantized[i] = quantize(quiet_signal[i], 8);
    }

    // 检查是否全为零
    bool all_zero = true;
    for (float s : quantized) {
        if (s != 0.0f) {
            all_zero = false;
            break;
        }
    }

    std::cout << "信号幅度: " << amplitude << " (" << -60 << " dB)" << std::endl;
    std::cout << "量化后全为零: " << (all_zero ? "是" : "否") << std::endl;

    if (all_zero) {
        std::cout << "\n问题：低电平信号在低位深度下会丢失！" << std::endl;
        std::cout << "解决方案：使用抖动或更高位深度" << std::endl;
    }
}

int main() {
    std::cout << "=== Quantization Demo (量化处理演示) ===" << std::endl;

    demo_quantization_process();
    demo_bit_depth_effect();
    demo_quantization_noise();
    demo_dithering();
    demo_signal_quantization();

    std::cout << "\n=== 量化处理总结 ===" << std::endl;
    std::cout << "1. 量化将连续值映射到离散级别" << std::endl;
    std::cout << "2. 位深度决定动态范围：DR = 6.02*N + 1.76 dB" << std::endl;
    std::cout << "3. 量化噪声是不可避免的" << std::endl;
    std::cout << "4. 抖动技术可以改善低电平信号的表现" << std::endl;
    std::cout << "5. 专业音频使用 24-bit，内部处理使用 32-bit float" << std::endl;

    return 0;
}
