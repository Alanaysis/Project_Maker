// pitch.cpp - 音高检测演示
//
// 本文件演示音高检测的基本原理：
// 1. 自相关法
// 2. 频谱峰值法
// 3. 音高频率转换
//
// 编译: g++ -std=c++17 -I../../include pitch.cpp -o pitch -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 自相关音高检测
float detect_pitch_autocorrelation(const std::vector<float>& signal,
                                     float sample_rate,
                                     float min_freq = 50.0f,
                                     float max_freq = 2000.0f) {
    size_t min_lag = static_cast<size_t>(sample_rate / max_freq);
    size_t max_lag = static_cast<size_t>(sample_rate / min_freq);
    max_lag = std::min(max_lag, signal.size() / 2);

    // 计算自相关
    std::vector<float> autocorr(max_lag + 1, 0.0f);
    for (size_t lag = min_lag; lag <= max_lag; ++lag) {
        float sum = 0.0f;
        for (size_t i = 0; i < signal.size() - lag; ++i) {
            sum += signal[i] * signal[i + lag];
        }
        autocorr[lag] = sum;
    }

    // 寻找最大自相关值
    size_t best_lag = min_lag;
    float best_corr = autocorr[min_lag];

    for (size_t lag = min_lag + 1; lag <= max_lag; ++lag) {
        if (autocorr[lag] > best_corr) {
            best_corr = autocorr[lag];
            best_lag = lag;
        }
    }

    return sample_rate / best_lag;
}

// 频谱峰值音高检测
float detect_pitch_spectrum(const std::vector<float>& signal,
                              float sample_rate) {
    // 简化：直接在时域寻找过零点
    size_t zero_crossings = 0;
    for (size_t i = 1; i < signal.size(); ++i) {
        if ((signal[i - 1] >= 0 && signal[i] < 0) ||
            (signal[i - 1] < 0 && signal[i] >= 0)) {
            ++zero_crossings;
        }
    }

    float duration = static_cast<float>(signal.size()) / sample_rate;
    float freq = zero_crossings / (2.0f * duration);

    return freq;
}

// 音符名称转换
std::string freq_to_note(float freq) {
    if (freq <= 0) return "N/A";

    // A4 = 440 Hz
    float semitones = 12.0f * std::log2(freq / 440.0f);
    int note_index = static_cast<int>(std::round(semitones)) % 12;
    if (note_index < 0) note_index += 12;

    const char* notes[] = {"A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"};
    int octave = static_cast<int>(std::floor(std::log2(freq / 440.0f) + 4.99f));

    return std::string(notes[note_index]) + std::to_string(octave);
}

// 演示自相关音高检测
void demo_autocorrelation_pitch() {
    print_separator("自相关音高检测");

    std::cout << "\n自相关法：通过信号的周期性检测音高\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 0.1f;

    std::vector<float> test_freqs = {261.63f, 440.0f, 880.0f}; // C4, A4, A5

    for (float freq : test_freqs) {
        auto signal = generate_sine(freq, sample_rate, duration);
        float detected = detect_pitch_autocorrelation(signal, sample_rate);

        std::cout << "实际: " << freq << " Hz (" << freq_to_note(freq)
                  << ") -> 检测: " << detected << " Hz ("
                  << freq_to_note(detected) << ")" << std::endl;
    }
}

// 演示频谱音高检测
void demo_spectrum_pitch() {
    print_separator("频谱音高检测");

    std::cout << "\n频谱法：通过频率分析检测音高\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 0.1f;

    std::vector<float> test_freqs = {261.63f, 440.0f, 880.0f};

    for (float freq : test_freqs) {
        auto signal = generate_sine(freq, sample_rate, duration);
        float detected = detect_pitch_spectrum(signal, sample_rate);

        std::cout << "实际: " << freq << " Hz (" << freq_to_note(freq)
                  << ") -> 检测: " << detected << " Hz ("
                  << freq_to_note(detected) << ")" << std::endl;
    }
}

// 演示音符频率表
void demo_note_frequencies() {
    print_separator("音符频率表");

    std::cout << "\n标准音符频率 (A4 = 440 Hz):\n" << std::endl;

    std::cout << "音符 | 频率 (Hz)" << std::endl;
    std::cout << "-----|----------" << std::endl;

    std::vector<std::string> notes = {"C", "C#", "D", "D#", "E", "F",
                                       "F#", "G", "G#", "A", "A#", "B"};

    for (int octave = 2; octave <= 6; ++octave) {
        for (int i = 0; i < 12; ++i) {
            int midi = (octave + 1) * 12 + i;
            float freq = 440.0f * std::pow(2.0f, (midi - 69) / 12.0f);

            if (octave >= 3 && octave <= 5) {
                printf("%s%d  | %8.2f\n", notes[i].c_str(), octave, freq);
            }
        }
    }
}

// 演示音高检测应用
void demo_pitch_applications() {
    print_separator("音高检测应用");

    std::cout << "\n音高检测的常见应用:\n" << std::endl;

    std::cout << "1. 音乐教育" << std::endl;
    std::cout << "   - 乐器调音器" << std::endl;
    std::cout << "   - 声乐练习" << std::endl;

    std::cout << "\n2. 音乐信息检索" << std::endl;
    std::cout << "   - 旋律提取" << std::endl;
    std::cout << "   - 和弦识别" << std::endl;

    std::cout << "\n3. 语音处理" << std::endl;
    std::cout << "   - 基频检测" << std::endl;
    std::cout << "   - 语音合成" << std::endl;

    std::cout << "\n4. 音乐制作" << std::endl;
    std::cout << "   - 自动修音" << std::endl;
    std::cout << "   - 音高跟踪" << std::endl;
}

int main() {
    std::cout << "=== Pitch Detection Demo (音高检测演示) ===" << std::endl;

    demo_autocorrelation_pitch();
    demo_spectrum_pitch();
    demo_note_frequencies();
    demo_pitch_applications();

    std::cout << "\n=== 音高检测总结 ===" << std::endl;
    std::cout << "1. 自相关法通过信号周期性检测音高" << std::endl;
    std::cout << "2. 频谱法通过频率分析检测音高" << std::endl;
    std::cout << "3. A4 = 440 Hz 是标准音高参考" << std::endl;
    std::cout << "4. 广泛用于调音器和音乐分析" << std::endl;

    return 0;
}
