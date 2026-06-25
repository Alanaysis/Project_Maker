// bit_depth.cpp - 位深度处理演示
//
// 本文件演示位深度处理的基本原理：
// 1. 位深度转换
// 2. 抖动处理
// 3. 噪声整形
// 4. 动态范围
//
// 编译: g++ -std=c++17 -I../../include bit_depth.cpp -o bit_depth -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <iomanip>

using namespace audio;

// 位深度转换
std::vector<float> convert_bit_depth(const std::vector<float>& input,
                                      int from_bits, int to_bits) {
    std::vector<float> output(input.size());

    // 模拟量化到目标位深度
    int levels = (1 << to_bits) - 1;

    for (size_t i = 0; i < input.size(); ++i) {
        // 将 [-1, 1] 映射到 [0, levels]
        float normalized = (input[i] + 1.0f) / 2.0f;
        int quantized = static_cast<int>(normalized * levels + 0.5f);
        quantized = std::max(0, std::min(levels, quantized));

        // 映射回 [-1, 1]
        output[i] = 2.0f * quantized / levels - 1.0f;
    }

    return output;
}

// 应用抖动
std::vector<float> apply_dither(const std::vector<float>& input,
                                 float amplitude) {
    std::vector<float> output(input.size());
    std::mt19937 gen(42);
    std::uniform_real_distribution<float> dist(-amplitude, amplitude);

    for (size_t i = 0; i < input.size(); ++i) {
        output[i] = input[i] + dist(gen);
    }
    return output;
}

// 计算信噪比
float calculate_snr(const std::vector<float>& original,
                    const std::vector<float>& processed) {
    float signal_power = 0.0f;
    float noise_power = 0.0f;

    for (size_t i = 0; i < original.size(); ++i) {
        signal_power += original[i] * original[i];
        float noise = original[i] - processed[i];
        noise_power += noise * noise;
    }

    if (noise_power == 0.0f) return 100.0f;
    return 10.0f * std::log10(signal_power / noise_power);
}

// 演示位深度转换
void demo_bit_depth_conversion() {
    print_separator("位深度转换");

    std::cout << "\n位深度转换：改变音频的量化精度\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;
    float freq = 1000.0f;

    auto original = generate_sine(freq, sample_rate, duration);

    // 24-bit → 16-bit
    auto converted_16 = convert_bit_depth(original, 24, 16);
    float snr_16 = calculate_snr(original, converted_16);

    // 24-bit → 8-bit
    auto converted_8 = convert_bit_depth(original, 24, 8);
    float snr_8 = calculate_snr(original, converted_8);

    std::cout << "原始信号 (24-bit 内部表示)" << std::endl;
    std::cout << "\n转换结果:" << std::endl;
    std::cout << "  16-bit: SNR = " << snr_16 << " dB" << std::endl;
    std::cout << "  8-bit:  SNR = " << snr_8 << " dB" << std::endl;

    // 保存文件
    AudioBuffer buf_16 = make_buffer(converted_16, static_cast<uint32_t>(sample_rate));
    buf_16.bit_depth = 16;

    AudioBuffer buf_8 = make_buffer(converted_8, static_cast<uint32_t>(sample_rate));
    buf_8.bit_depth = 8;

    write_wav("bit_depth_16.wav", buf_16);
    write_wav("bit_depth_8.wav", buf_8);
}

// 演示抖动技术
void demo_dithering() {
    print_separator("抖动技术 (Dithering)");

    std::cout << "\n抖动在量化前添加低电平噪声\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;
    float freq = 1000.0f;

    auto original = generate_sine(freq, sample_rate, duration);

    // 无抖动 8-bit 量化
    auto no_dither = convert_bit_depth(original, 24, 8);
    float snr_no_dither = calculate_snr(original, no_dither);

    // 有抖动 8-bit 量化
    auto dithered = apply_dither(original, 1.0f / 128.0f);
    auto with_dither = convert_bit_depth(dithered, 24, 8);
    float snr_with_dither = calculate_snr(original, with_dither);

    std::cout << "无抖动 8-bit:" << std::endl;
    std::cout << "  SNR = " << snr_no_dither << " dB" << std::endl;

    std::cout << "\n有抖动 8-bit:" << std::endl;
    std::cout << "  SNR = " << snr_with_dither << " dB" << std::endl;

    std::cout << "\n抖动的作用:" << std::endl;
    std::cout << "  1. 将量化误差随机化" << std::endl;
    std::cout << "  2. 改善低电平信号的听感" << std::endl;
    std::cout << "  3. 避免信号相关的失真" << std::endl;

    // 保存文件
    AudioBuffer no_dither_buf = make_buffer(no_dither, static_cast<uint32_t>(sample_rate));
    AudioBuffer with_dither_buf = make_buffer(with_dither, static_cast<uint32_t>(sample_rate));

    write_wav("no_dither_8bit.wav", no_dither_buf);
    write_wav("with_dither_8bit.wav", with_dither_buf);
}

// 演示动态范围
void demo_dynamic_range() {
    print_separator("动态范围");

    std::cout << "\n动态范围 = 最大信号 / 最小可表示信号\n" << std::endl;

    std::vector<int> bit_depths = {8, 12, 16, 20, 24, 32};

    std::cout << "位深度 | 动态范围 | 最小信号" << std::endl;
    std::cout << "-------|----------|----------" << std::endl;

    for (int bits : bit_depths) {
        float dynamic_range = 6.02 * bits + 1.76;
        float min_signal = db_to_linear(-dynamic_range);

        printf("%6d | %6.1f dB | %.2e\n",
               bits, dynamic_range, min_signal);
    }

    std::cout << "\n实际应用:" << std::endl;
    std::cout << "  16-bit (96 dB): CD 质量，足够大多数应用" << std::endl;
    std::cout << "  24-bit (144 dB): 专业录音，保留余量" << std::endl;
    std::cout << "  32-bit float: 内部处理，避免累积误差" << std::endl;
}

// 演示噪声整形（概念）
void demo_noise_shaping() {
    print_separator("噪声整形 (Noise Shaping) - 概念");

    std::cout << "\n噪声整形：将量化噪声移到人耳不敏感的频率范围\n" << std::endl;

    std::cout << "原理:" << std::endl;
    std::cout << "  1. 在量化前，从信号中减去之前的量化误差" << std::endl;
    std::cout << "  2. 量化后，将新的量化误差反馈" << std::endl;
    std::cout << "  3. 结果：噪声被推到高频" << std::endl;

    std::cout << "\n噪声整形滤波器 (1阶):" << std::endl;
    std::cout << "  H(z) = 1 - z^(-1)" << std::endl;
    std::cout << "  效果: +6 dB/oct 高频噪声提升" << std::endl;

    std::cout << "\n应用场景:" << std::endl;
    std::cout << "  - 1-bit DSD 编码" << std::endl;
    std::cout << "  - 高质量采样率转换" << std::endl;
    std::cout << "  - DAC 内部处理" << std::endl;
}

// 演示实际文件大小对比
void demo_file_sizes() {
    print_separator("文件大小对比");

    std::cout << "\n不同位深度的文件大小:\n" << std::endl;

    float duration = 60.0f; // 1 分钟
    float sample_rate = 44100.0f;
    int channels = 2; // 立体声

    struct BitDepthInfo {
        int bits;
        const char* format;
    };

    std::vector<BitDepthInfo> formats = {
        {8, "8-bit PCM"},
        {16, "16-bit PCM (CD)"},
        {24, "24-bit PCM (专业)"},
        {32, "32-bit float"}
    };

    std::cout << "格式            | 每采样字节 | 文件大小 (1分钟立体声)" << std::endl;
    std::cout << "----------------|-----------|----------------------" << std::endl;

    for (const auto& fmt : formats) {
        float bytes_per_sample = fmt.bits / 8.0f;
        float file_size = sample_rate * channels * bytes_per_sample * duration;
        float file_size_mb = file_size / (1024 * 1024);

        printf("%-15s | %7.1f   | %6.1f MB\n",
               fmt.format, bytes_per_sample, file_size_mb);
    }
}

int main() {
    std::cout << "=== Bit Depth Processing Demo (位深度处理演示) ===" << std::endl;

    demo_bit_depth_conversion();
    demo_dithering();
    demo_dynamic_range();
    demo_noise_shaping();
    demo_file_sizes();

    std::cout << "\n=== 位深度处理总结 ===" << std::endl;
    std::cout << "1. 位深度决定动态范围：DR = 6.02*N + 1.76 dB" << std::endl;
    std::cout << "2. 抖动技术改善量化特性" << std::endl;
    std::cout << "3. 噪声整形将噪声移到高频" << std::endl;
    std::cout << "4. 专业音频使用 24-bit，内部处理用 32-bit float" << std::endl;

    return 0;
}
