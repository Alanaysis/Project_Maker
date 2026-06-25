// fade.cpp - 淡入淡出演示
//
// 本文件演示音频淡入淡出的基本原理：
// 1. 线性淡入淡出
// 2. S 曲线淡入淡出
// 3. 指数淡入淡出
//
// 编译: g++ -std=c++17 -I../../include fade.cpp -o fade -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 线性淡入
void fade_in_linear(AudioBuffer& buffer, float duration_sec) {
    size_t num_samples = static_cast<size_t>(duration_sec * buffer.sample_rate);
    num_samples = std::min(num_samples, buffer.num_samples());

    for (size_t i = 0; i < num_samples; ++i) {
        float gain = static_cast<float>(i) / num_samples;
        for (uint16_t ch = 0; ch < buffer.channels; ++ch) {
            buffer.set_sample(i, ch, buffer.get_sample(i, ch) * gain);
        }
    }
}

// 线性淡出
void fade_out_linear(AudioBuffer& buffer, float duration_sec) {
    size_t num_samples = static_cast<size_t>(duration_sec * buffer.sample_rate);
    num_samples = std::min(num_samples, buffer.num_samples());

    size_t start = buffer.num_samples() - num_samples;
    for (size_t i = 0; i < num_samples; ++i) {
        float gain = 1.0f - static_cast<float>(i) / num_samples;
        for (uint16_t ch = 0; ch < buffer.channels; ++ch) {
            buffer.set_sample(start + i, ch, buffer.get_sample(start + i, ch) * gain);
        }
    }
}

// S 曲线淡入
void fade_in_scurve(AudioBuffer& buffer, float duration_sec) {
    size_t num_samples = static_cast<size_t>(duration_sec * buffer.sample_rate);
    num_samples = std::min(num_samples, buffer.num_samples());

    for (size_t i = 0; i < num_samples; ++i) {
        float t = static_cast<float>(i) / num_samples;
        // S 曲线：3t^2 - 2t^3
        float gain = t * t * (3.0f - 2.0f * t);
        for (uint16_t ch = 0; ch < buffer.channels; ++ch) {
            buffer.set_sample(i, ch, buffer.get_sample(i, ch) * gain);
        }
    }
}

// S 曲线淡出
void fade_out_scurve(AudioBuffer& buffer, float duration_sec) {
    size_t num_samples = static_cast<size_t>(duration_sec * buffer.sample_rate);
    num_samples = std::min(num_samples, buffer.num_samples());

    size_t start = buffer.num_samples() - num_samples;
    for (size_t i = 0; i < num_samples; ++i) {
        float t = 1.0f - static_cast<float>(i) / num_samples;
        float gain = t * t * (3.0f - 2.0f * t);
        for (uint16_t ch = 0; ch < buffer.channels; ++ch) {
            buffer.set_sample(start + i, ch, buffer.get_sample(start + i, ch) * gain);
        }
    }
}

// 指数淡入
void fade_in_exponential(AudioBuffer& buffer, float duration_sec) {
    size_t num_samples = static_cast<size_t>(duration_sec * buffer.sample_rate);
    num_samples = std::min(num_samples, buffer.num_samples());

    for (size_t i = 0; i < num_samples; ++i) {
        float t = static_cast<float>(i) / num_samples;
        // 指数曲线
        float gain = (std::exp(t * 5.0f) - 1.0f) / (std::exp(5.0f) - 1.0f);
        for (uint16_t ch = 0; ch < buffer.channels; ++ch) {
            buffer.set_sample(i, ch, buffer.get_sample(i, ch) * gain);
        }
    }
}

// 指数淡出
void fade_out_exponential(AudioBuffer& buffer, float duration_sec) {
    size_t num_samples = static_cast<size_t>(duration_sec * buffer.sample_rate);
    num_samples = std::min(num_samples, buffer.num_samples());

    size_t start = buffer.num_samples() - num_samples;
    for (size_t i = 0; i < num_samples; ++i) {
        float t = 1.0f - static_cast<float>(i) / num_samples;
        float gain = (std::exp(t * 5.0f) - 1.0f) / (std::exp(5.0f) - 1.0f);
        for (uint16_t ch = 0; ch < buffer.channels; ++ch) {
            buffer.set_sample(start + i, ch, buffer.get_sample(start + i, ch) * gain);
        }
    }
}

// 演示线性淡入淡出
void demo_linear_fade() {
    print_separator("线性淡入淡出");

    std::cout << "\n线性淡入淡出：最简单的淡入淡出曲线\n" << std::endl;

    auto samples = generate_sine(440.0f, 44100.0f, 2.0f);
    AudioBuffer buffer = make_buffer(samples, 44100);

    std::cout << "原始信号:" << std::endl;
    std::cout << "  峰值: " << buffer.peak() << std::endl;

    // 应用淡入淡出
    AudioBuffer processed = buffer;
    fade_in_linear(processed, 0.5f);
    fade_out_linear(processed, 0.5f);

    std::cout << "\n应用 0.5 秒线性淡入淡出后:" << std::endl;
    std::cout << "  峰值: " << processed.peak() << std::endl;

    write_wav("fade_linear.wav", processed);
}

// 演示 S 曲线淡入淡出
void demo_scurve_fade() {
    print_separator("S 曲线淡入淡出");

    std::cout << "\nS 曲线：更平滑的过渡，听感更自然\n" << std::endl;

    auto samples = generate_sine(440.0f, 44100.0f, 2.0f);
    AudioBuffer buffer = make_buffer(samples, 44100);

    AudioBuffer processed = buffer;
    fade_in_scurve(processed, 0.5f);
    fade_out_scurve(processed, 0.5f);

    std::cout << "S 曲线公式: gain = 3t^2 - 2t^3" << std::endl;
    std::cout << "特点: 开始和结束时变化慢，中间变化快" << std::endl;

    write_wav("fade_scurve.wav", processed);
}

// 演示指数淡入淡出
void demo_exponential_fade() {
    print_separator("指数淡入淡出");

    std::cout << "\n指数淡入淡出：快速达到目标值\n" << std::endl;

    auto samples = generate_sine(440.0f, 44100.0f, 2.0f);
    AudioBuffer buffer = make_buffer(samples, 44100);

    AudioBuffer processed = buffer;
    fade_in_exponential(processed, 0.5f);
    fade_out_exponential(processed, 0.5f);

    std::cout << "指数曲线公式: gain = (e^(5t) - 1) / (e^5 - 1)" << std::endl;
    std::cout << "特点: 快速上升/下降" << std::endl;

    write_wav("fade_exponential.wav", processed);
}

// 演示不同淡入淡出时间
void demo_fade_durations() {
    print_separator("不同淡入淡出时间");

    std::cout << "\n淡入淡出时间的选择:\n" << std::endl;

    struct FadeInfo {
        float duration;
        const char* application;
    };

    std::vector<FadeInfo> fades = {
        {0.005f, "极短：消除咔嗒声"},
        {0.01f, "短：快速过渡"},
        {0.05f, "中短：平滑过渡"},
        {0.1f, "中等：标准淡入淡出"},
        {0.5f, "长：音乐段落过渡"},
        {2.0f, "很长：电影音频"}
    };

    for (const auto& fade : fades) {
        std::cout << "  " << fade.duration << " 秒: " << fade.application << std::endl;
    }

    // 生成不同时间的淡入淡出
    auto samples = generate_sine(440.0f, 44100.0f, 3.0f);
    AudioBuffer buffer = make_buffer(samples, 44100);

    std::vector<float> durations = {0.01f, 0.1f, 0.5f, 1.0f};
    for (float dur : durations) {
        AudioBuffer processed = buffer;
        fade_in_linear(processed, dur);
        fade_out_linear(processed, dur);

        std::string filename = "fade_dur_" + std::to_string(static_cast<int>(dur * 1000)) + "ms.wav";
        write_wav(filename, processed);
    }
}

// 演示实际应用
void demo_fade_applications() {
    print_separator("淡入淡出应用");

    std::cout << "\n淡入淡出的实际应用:\n" << std::endl;

    std::cout << "1. 音乐制作" << std::endl;
    std::cout << "   - 歌曲开头淡入" << std::endl;
    std::cout << "   - 歌曲结尾淡出" << std::endl;
    std::cout << "   - 段落过渡" << std::endl;

    std::cout << "\n2. 播客/广播" << std::endl;
    std::cout << "   - 开场白淡入" << std::endl;
    std::cout << "   - 背景音乐淡入淡出" << std::endl;

    std::cout << "\n3. 电影/视频" << std::endl;
    std::cout << "   - 场景转换" << std::endl;
    std::cout << "   - 对话与背景音的平衡" << std::endl;

    std::cout << "\n4. 游戏音频" << std::endl;
    std::cout << "   - 音乐切换" << std::endl;
    std::cout << "   - 环境音过渡" << std::endl;

    // 生成演示
    auto samples = generate_sine(440.0f, 44100.0f, 3.0f);
    AudioBuffer buffer = make_buffer(samples, 44100);

    // 模拟音乐淡出
    AudioBuffer music_fade = buffer;
    fade_out_scurve(music_fade, 2.0f);
    write_wav("fade_music_out.wav", music_fade);

    // 模拟短淡入淡出消除咔嗒声
    AudioBuffer click_free = make_buffer(generate_sine(440.0f, 44100.0f, 0.1f), 44100);
    fade_in_linear(click_free, 0.005f);
    fade_out_linear(click_free, 0.005f);
    write_wav("fade_click_free.wav", click_free);
}

int main() {
    std::cout << "=== Fade In/Out Demo (淡入淡出演示) ===" << std::endl;

    demo_linear_fade();
    demo_scurve_fade();
    demo_exponential_fade();
    demo_fade_durations();
    demo_fade_applications();

    std::cout << "\n=== 淡入淡出总结 ===" << std::endl;
    std::cout << "1. 线性：简单直接，但听感不够自然" << std::endl;
    std::cout << "2. S 曲线：平滑自然，推荐使用" << std::endl;
    std::cout << "3. 指数：快速响应，适合短过渡" << std::endl;
    std::cout << "4. 时间选择取决于应用场景" << std::endl;

    return 0;
}
