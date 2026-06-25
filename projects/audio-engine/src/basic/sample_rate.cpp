// sample_rate.cpp - 采样率转换演示
//
// 本文件演示采样率转换的基本原理：
// 1. 整数倍上采样（插值）
// 2. 整数倍下采样（抽取）
// 3. 非整数倍采样率转换
// 4. 抗混叠滤波
//
// 编译: g++ -std=c++17 -I../../include sample_rate.cpp -o sample_rate -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 最近邻插值上采样
std::vector<float> upsample_nearest(const std::vector<float>& input, int factor) {
    std::vector<float> output(input.size() * factor);
    for (size_t i = 0; i < input.size(); ++i) {
        for (int j = 0; j < factor; ++j) {
            output[i * factor + j] = input[i];
        }
    }
    return output;
}

// 线性插值上采样
std::vector<float> upsample_linear(const std::vector<float>& input, int factor) {
    std::vector<float> output(input.size() * factor);
    for (size_t i = 0; i < input.size() - 1; ++i) {
        for (int j = 0; j < factor; ++j) {
            float t = static_cast<float>(j) / factor;
            output[i * factor + j] = lerp(input[i], input[i + 1], t);
        }
    }
    // 最后一个采样点
    output[(input.size() - 1) * factor] = input.back();
    return output;
}

// 简单低通滤波器（用于抗混叠）
std::vector<float> lowpass_filter(const std::vector<float>& input, float cutoff_ratio) {
    std::vector<float> output(input.size());
    // 简单的一阶 IIR 低通滤波器
    float alpha = cutoff_ratio;
    output[0] = input[0];
    for (size_t i = 1; i < input.size(); ++i) {
        output[i] = alpha * input[i] + (1.0f - alpha) * output[i - 1];
    }
    return output;
}

// 整数倍下采样
std::vector<float> downsample(const std::vector<float>& input, int factor,
                               bool apply_filter = true) {
    std::vector<float> filtered = input;

    // 应用抗混叠滤波
    if (apply_filter) {
        filtered = lowpass_filter(input, 1.0f / factor);
    }

    // 抽取
    std::vector<float> output(filtered.size() / factor);
    for (size_t i = 0; i < output.size(); ++i) {
        output[i] = filtered[i * factor];
    }
    return output;
}

// 线性插值重采样（非整数倍）
std::vector<float> resample_linear(const std::vector<float>& input,
                                    float ratio) {
    size_t output_size = static_cast<size_t>(input.size() * ratio);
    std::vector<float> output(output_size);

    for (size_t i = 0; i < output_size; ++i) {
        float src_pos = i / ratio;
        size_t src_idx = static_cast<size_t>(src_pos);
        float frac = src_pos - src_idx;

        if (src_idx + 1 < input.size()) {
            output[i] = lerp(input[src_idx], input[src_idx + 1], frac);
        } else {
            output[i] = input[src_idx];
        }
    }
    return output;
}

// 演示上采样
void demo_upsampling() {
    print_separator("上采样 (Upsampling)");

    std::cout << "\n上采样：增加采样点数，提高采样率\n" << std::endl;

    float freq = 440.0f;
    float original_sr = 8000.0f;
    float duration = 0.005f; // 5ms

    auto original = generate_sine(freq, original_sr, duration);

    std::cout << "原始采样率: " << original_sr << " Hz" << std::endl;
    std::cout << "原始采样点数: " << original.size() << std::endl;

    // 2x 上采样
    auto upsampled = upsample_linear(original, 2);
    std::cout << "\n2x 上采样后:" << std::endl;
    std::cout << "  采样点数: " << upsampled.size() << std::endl;
    std::cout << "  等效采样率: " << original_sr * 2 << " Hz" << std::endl;

    // 4x 上采样
    auto upsampled4x = upsample_linear(original, 4);
    std::cout << "\n4x 上采样后:" << std::endl;
    std::cout << "  采样点数: " << upsampled4x.size() << std::endl;
    std::cout << "  等效采样率: " << original_sr * 4 << " Hz" << std::endl;

    // 保存文件
    AudioBuffer buf1 = make_buffer(original, static_cast<uint32_t>(original_sr));
    AudioBuffer buf2 = make_buffer(upsampled, static_cast<uint32_t>(original_sr * 2));

    write_wav("upsample_original.wav", buf1);
    write_wav("upsample_2x.wav", buf2);
}

// 演示下采样
void demo_downsampling() {
    print_separator("下采样 (Downsampling)");

    std::cout << "\n下采样：减少采样点数，降低采样率\n" << std::endl;

    float freq = 1000.0f;
    float original_sr = 48000.0f;
    float duration = 0.01f;

    auto original = generate_sine(freq, original_sr, duration);

    std::cout << "原始采样率: " << original_sr << " Hz" << std::endl;
    std::cout << "原始采样点数: " << original.size() << std::endl;

    // 2x 下采样（带抗混叠）
    auto downsampled = downsample(original, 2, true);
    std::cout << "\n2x 下采样后（带抗混叠滤波）:" << std::endl;
    std::cout << "  采样点数: " << downsampled.size() << std::endl;
    std::cout << "  等效采样率: " << original_sr / 2 << " Hz" << std::endl;

    // 6x 下采样
    auto downsampled6x = downsample(original, 6, true);
    std::cout << "\n6x 下采样后:" << std::endl;
    std::cout << "  采样点数: " << downsampled6x.size() << std::endl;
    std::cout << "  等效采样率: " << original_sr / 6 << " Hz" << std::endl;
}

// 演示非整数倍重采样
void demo_resampling() {
    print_separator("非整数倍重采样");

    std::cout << "\n重采样：改变采样率到任意目标值\n" << std::endl;

    float freq = 440.0f;
    float source_sr = 44100.0f;
    float duration = 1.0f;

    auto original = generate_sine(freq, source_sr, duration);

    std::cout << "源采样率: " << source_sr << " Hz" << std::endl;
    std::cout << "源采样点数: " << original.size() << std::endl;

    // 转换到 48000 Hz
    float target_sr = 48000.0f;
    float ratio = target_sr / source_sr;
    auto resampled = resample_linear(original, ratio);

    std::cout << "\n目标采样率: " << target_sr << " Hz" << std::endl;
    std::cout << "重采样比率: " << ratio << std::endl;
    std::cout << "目标采样点数: " << resampled.size() << std::endl;

    // 保存文件
    AudioBuffer source_buf = make_buffer(original, static_cast<uint32_t>(source_sr));
    AudioBuffer target_buf = make_buffer(resampled, static_cast<uint32_t>(target_sr));

    write_wav("resample_44100hz.wav", source_buf);
    write_wav("resample_48000hz.wav", target_buf);
}

// 演示采样率转换的实际应用
void demo_practical_conversion() {
    print_separator("实际应用场景");

    std::cout << "\n常见采样率转换场景:\n" << std::endl;

    struct Conversion {
        uint32_t source;
        uint32_t target;
        const char* scenario;
    };

    std::vector<Conversion> conversions = {
        {44100, 48000, "CD → 专业音频/视频"},
        {48000, 44100, "专业音频 → CD"},
        {96000, 44100, "高清音频 → CD"},
        {44100, 22050, "CD → 网络流媒体"},
        {16000, 8000, "宽带语音 → 电话"},
        {44100, 16000, "CD → 语音识别"}
    };

    std::cout << "源采样率 → 目标采样率 | 应用场景" << std::endl;
    std::cout << "----------------------|----------" << std::endl;

    for (const auto& conv : conversions) {
        printf("%6d → %6d Hz   | %s\n",
               conv.source, conv.target, conv.scenario);
    }

    std::cout << "\n注意事项:" << std::endl;
    std::cout << "1. 下采样前必须进行抗混叠滤波" << std::endl;
    std::cout << "2. 上采样后需要进行镜像抑制滤波" << std::endl;
    std::cout << "3. 高质量重采样需要更复杂的滤波器" << std::endl;
}

int main() {
    std::cout << "=== Sample Rate Conversion Demo (采样率转换演示) ===" << std::endl;

    demo_upsampling();
    demo_downsampling();
    demo_resampling();
    demo_practical_conversion();

    std::cout << "\n=== 采样率转换总结 ===" << std::endl;
    std::cout << "1. 上采样：插值增加采样点" << std::endl;
    std::cout << "2. 下采样：抗混叠滤波 + 抽取" << std::endl;
    std::cout << "3. 非整数倍：线性插值或其他插值方法" << std::endl;
    std::cout << "4. 高质量转换需要复杂的滤波器设计" << std::endl;

    return 0;
}
