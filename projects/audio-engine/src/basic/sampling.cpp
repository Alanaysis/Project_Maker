// sampling.cpp - 音频采样原理演示
//
// 本文件演示数字音频采样的基本原理：
// 1. 采样定理（奈奎斯特定理）
// 2. 混叠现象（Aliasing）
// 3. 不同采样率的效果对比
//
// 编译: g++ -std=c++17 -I../../include sampling.cpp -o sampling -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 演示采样定理
void demo_sampling_theorem() {
    print_separator("采样定理 (Nyquist-Shannon Sampling Theorem)");

    std::cout << "\n采样定理：采样率必须 >= 2 * 最高频率\n" << std::endl;

    // 生成一个 1000 Hz 的正弦波
    float freq = 1000.0f;
    float duration = 0.01f; // 10ms，便于可视化

    // 使用不同采样率采样
    std::vector<uint32_t> sample_rates = {8000, 16000, 44100, 48000, 96000};

    for (uint32_t sr : sample_rates) {
        auto samples = generate_sine(freq, sr, duration);
        float max_val = 0.0f;
        for (float s : samples) max_val = std::max(max_val, std::abs(s));

        std::cout << "采样率 " << sr << " Hz: "
                  << samples.size() << " 采样点, "
                  << "峰值 = " << max_val
                  << " (Nyquist = " << sr / 2 << " Hz)" << std::endl;
    }
}

// 演示混叠现象
void demo_aliasing() {
    print_separator("混叠现象 (Aliasing)");

    std::cout << "\n当采样率 < 2 * 信号频率时，发生混叠\n" << std::endl;

    // 原始信号：5000 Hz
    float freq = 5000.0f;

    // 低采样率：8000 Hz（Nyquist = 4000 Hz < 5000 Hz）
    uint32_t low_sr = 8000;
    auto low_samples = generate_sine(freq, low_sr, 0.002f);

    // 高采样率：48000 Hz（Nyquist = 24000 Hz > 5000 Hz）
    uint32_t high_sr = 48000;
    auto high_samples = generate_sine(freq, high_sr, 0.002f);

    std::cout << "原始信号频率: " << freq << " Hz" << std::endl;
    std::cout << "\n低采样率 (" << low_sr << " Hz) 采样:" << std::endl;
    std::cout << "  Nyquist 频率: " << low_sr / 2 << " Hz" << std::endl;
    std::cout << "  混叠频率: " << freq - low_sr << " Hz (会出现负频率的绝对值)" << std::endl;

    // 计算实际混叠频率
    float alias_freq = std::abs(static_cast<float>(freq) - low_sr);
    std::cout << "  实际混叠: " << alias_freq << " Hz" << std::endl;

    std::cout << "\n高采样率 (" << high_sr << " Hz) 采样:" << std::endl;
    std::cout << "  Nyquist 频率: " << high_sr / 2 << " Hz" << std::endl;
    std::cout << "  无混叠（信号频率 < Nyquist）" << std::endl;
}

// 演示不同采样率的频率分辨率
void demo_frequency_resolution() {
    print_separator("采样率与频率分辨率");

    std::cout << "\n采样率越高，能表示的频率范围越广\n" << std::endl;

    struct SampleRateInfo {
        uint32_t rate;
        const char* application;
    };

    std::vector<SampleRateInfo> rates = {
        {8000, "电话语音"},
        {16000, "宽带语音"},
        {22050, "AM广播"},
        {44100, "CD质量"},
        {48000, "专业音频/视频"},
        {96000, "高清音频"},
        {192000, "超高分辨率"}
    };

    std::cout << "采样率 (Hz) | 最高频率 (Hz) | 应用场景" << std::endl;
    std::cout << "------------|---------------|----------" << std::endl;

    for (const auto& info : rates) {
        printf("%11d | %13d | %s\n",
               info.rate, info.rate / 2, info.application);
    }
}

// 生成采样演示文件
void generate_sampling_demos() {
    print_separator("生成采样演示文件");

    float freq = 440.0f; // A4 音符
    float duration = 1.0f;

    std::cout << "\n生成 440 Hz 正弦波，不同采样率..." << std::endl;

    std::vector<uint32_t> rates = {8000, 22050, 44100, 48000};

    for (uint32_t sr : rates) {
        auto samples = generate_sine(freq, sr, duration);
        AudioBuffer buffer = make_buffer(samples, sr);
        std::string filename = "sampling_" + std::to_string(sr) + "hz.wav";

        if (write_wav(filename, buffer)) {
            std::cout << "  生成: " << filename
                      << " (" << samples.size() << " 采样点)" << std::endl;
        }
    }

    std::cout << "\n注意：使用高采样率播放低采样率文件，音高会变高（需要重采样）" << std::endl;
}

// 演示采样点数与时间的关系
void demo_sample_count() {
    print_separator("采样点数与时间");

    std::cout << "\n采样点数 = 采样率 × 时间(秒)\n" << std::endl;

    float duration = 1.0f;

    std::cout << "时长 " << duration << " 秒:" << std::endl;
    std::cout << "  8000 Hz: " << static_cast<size_t>(8000 * duration) << " 采样点" << std::endl;
    std::cout << "  44100 Hz: " << static_cast<size_t>(44100 * duration) << " 采样点" << std::endl;
    std::cout << "  96000 Hz: " << static_cast<size_t>(96000 * duration) << " 采样点" << std::endl;

    std::cout << "\n每采样点间隔:" << std::endl;
    std::cout << "  8000 Hz: " << 1000000.0 / 8000 << " 微秒" << std::endl;
    std::cout << "  44100 Hz: " << 1000000.0 / 44100 << " 微秒" << std::endl;
    std::cout << "  96000 Hz: " << 1000000.0 / 96000 << " 微秒" << std::endl;
}

int main() {
    std::cout << "=== Audio Sampling Demo (音频采样原理演示) ===" << std::endl;

    demo_sampling_theorem();
    demo_aliasing();
    demo_frequency_resolution();
    demo_sample_count();
    generate_sampling_demos();

    std::cout << "\n=== 采样原理总结 ===" << std::endl;
    std::cout << "1. 采样率决定了可表示的最高频率（Nyquist频率 = 采样率/2）" << std::endl;
    std::cout << "2. 采样率不足会导致混叠（Aliasing）" << std::endl;
    std::cout << "3. 常用采样率：8kHz(电话), 44.1kHz(CD), 48kHz(专业)" << std::endl;
    std::cout << "4. 采样点数 = 采样率 × 时长" << std::endl;

    return 0;
}
