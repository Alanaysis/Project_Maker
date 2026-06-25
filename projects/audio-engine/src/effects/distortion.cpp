// distortion.cpp - 失真效果演示
//
// 本文件演示音频失真效果的基本原理：
// 1. 软削波
// 2. 硬削波
// 3. 过载模拟
//
// 编译: g++ -std=c++17 -I../../include distortion.cpp -o distortion -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 软削波函数
float soft_clip(float input, float threshold = 0.5f) {
    if (input > threshold) {
        return threshold + (1.0f - threshold) * std::tanh((input - threshold) / (1.0f - threshold));
    } else if (input < -threshold) {
        return -threshold - (1.0f - threshold) * std::tanh((-input - threshold) / (1.0f - threshold));
    }
    return input;
}

// 硬削波函数
float hard_clip(float input, float threshold = 0.5f) {
    return clamp(input, -threshold, threshold);
}

// 过载模拟
float overdrive(float input, float drive = 2.0f) {
    float driven = input * drive;
    return std::tanh(driven);
}

// 演示软削波
void demo_soft_clipping() {
    print_separator("软削波");

    std::cout << "\n软削波：平滑地限制信号幅度\n" << std::endl;

    float sample_rate = 44100.0f;
    auto dry = generate_sine(440.0f, sample_rate, 1.0f, 0.8f);

    AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));

    // 应用软削波
    for (auto& sample : buffer.samples) {
        sample = soft_clip(sample, 0.5f);
    }

    std::cout << "原始信号峰值: 0.8" << std::endl;
    std::cout << "软削波阈值: 0.5" << std::endl;
    std::cout << "处理后峰值: " << buffer.peak() << std::endl;

    write_wav("distortion_soft_clip.wav", buffer);
}

// 演示硬削波
void demo_hard_clipping() {
    print_separator("硬削波");

    std::cout << "\n硬削波：直接截断超过阈值的信号\n" << std::endl;

    float sample_rate = 44100.0f;
    auto dry = generate_sine(440.0f, sample_rate, 1.0f, 0.8f);

    AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));

    // 应用硬削波
    for (auto& sample : buffer.samples) {
        sample = hard_clip(sample, 0.5f);
    }

    std::cout << "原始信号峰值: 0.8" << std::endl;
    std::cout << "硬削波阈值: 0.5" << std::endl;
    std::cout << "处理后峰值: " << buffer.peak() << std::endl;

    write_wav("distortion_hard_clip.wav", buffer);
}

// 演示过载模拟
void demo_overdrive() {
    print_separator("过载模拟");

    std::cout << "\n过载模拟：模拟电子管放大器的失真\n" << std::endl;

    float sample_rate = 44100.0f;
    auto dry = generate_sine(440.0f, sample_rate, 1.0f, 0.5f);

    std::vector<float> drives = {1.0f, 2.0f, 5.0f, 10.0f};

    for (float drive : drives) {
        AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));

        for (auto& sample : buffer.samples) {
            sample = overdrive(sample, drive);
        }

        std::string filename = "distortion_drive_" +
                               std::to_string(static_cast<int>(drive)) + ".wav";
        write_wav(filename, buffer);

        std::cout << "驱动 " << drive << ": 峰值 = " << buffer.peak() << std::endl;
    }
}

// 演示失真应用
void demo_distortion_applications() {
    print_separator("失真应用");

    std::cout << "\n失真效果的常见应用:\n" << std::endl;

    std::cout << "1. 电吉他失真" << std::endl;
    std::cout << "   - 软削波: 温暖的过载" << std::endl;
    std::cout << "   - 硬削波: 激进的失真" << std::endl;
    std::cout << "   - 过载: 模拟电子管" << std::endl;

    std::cout << "\n2. 贝斯过载" << std::endl;
    std::cout << "   - 轻度过载增加谐波" << std::endl;
    std::cout << "   - 保持低频清晰" << std::endl;

    std::cout << "\n3. 人声失真" << std::endl;
    std::cout << "   - 轻度饱和增加温暖感" << std::endl;
    std::cout << "   - 特殊效果使用激进失真" << std::endl;

    // 生成吉他失真示例
    float sample_rate = 44100.0f;
    auto guitar = generate_sawtooth(330.0f, sample_rate, 2.0f, 0.4f);
    AudioBuffer buffer = make_buffer(guitar, static_cast<uint32_t>(sample_rate));

    for (auto& sample : buffer.samples) {
        sample = overdrive(sample, 3.0f);
    }

    write_wav("distortion_guitar.wav", buffer);
}

int main() {
    std::cout << "=== Distortion Effect Demo (失真效果演示) ===" << std::endl;

    demo_soft_clipping();
    demo_hard_clipping();
    demo_overdrive();
    demo_distortion_applications();

    std::cout << "\n=== 失真效果总结 ===" << std::endl;
    std::cout << "1. 软削波平滑限制，声音温暖" << std::endl;
    std::cout << "2. 硬削波直接截断，声音激进" << std::endl;
    std::cout << "3. 过载模拟电子管放大器" << std::endl;
    std::cout << "4. 常用于吉他、贝斯等乐器" << std::endl;

    return 0;
}
