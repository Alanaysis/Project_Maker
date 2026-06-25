// features.cpp - 特征提取演示
//
// 本文件演示音频特征提取的基本原理：
// 1. MFCC 特征
// 2. 色度特征
// 3. 频谱特征
//
// 编译: g++ -std=c++17 -I../../include features.cpp -o features -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 计算过零率
float zero_crossing_rate(const std::vector<float>& signal) {
    size_t crossings = 0;
    for (size_t i = 1; i < signal.size(); ++i) {
        if ((signal[i - 1] >= 0 && signal[i] < 0) ||
            (signal[i - 1] < 0 && signal[i] >= 0)) {
            ++crossings;
        }
    }
    return static_cast<float>(crossings) / (signal.size() - 1);
}

// 计算频谱质心
float spectral_centroid(const std::vector<float>& signal, float sample_rate) {
    // 简化实现：使用过零率近似
    float zcr = zero_crossing_rate(signal);
    return zcr * sample_rate / 2.0f;
}

// 计算频谱带宽
float spectral_bandwidth(const std::vector<float>& signal, float sample_rate) {
    // 简化实现
    float centroid = spectral_centroid(signal, sample_rate);
    float sum = 0.0f;
    float weight_sum = 0.0f;

    for (size_t i = 0; i < signal.size(); ++i) {
        float freq = i * sample_rate / signal.size();
        float weight = std::abs(signal[i]);
        sum += weight * (freq - centroid) * (freq - centroid);
        weight_sum += weight;
    }

    return weight_sum > 0 ? std::sqrt(sum / weight_sum) : 0.0f;
}

// 计算 RMS 能量
float rms_energy(const std::vector<float>& signal) {
    float sum = 0.0f;
    for (float s : signal) {
        sum += s * s;
    }
    return std::sqrt(sum / signal.size());
}

// 计算频谱滚降点
float spectral_rolloff(const std::vector<float>& signal, float sample_rate,
                        float rolloff_percent = 0.85f) {
    // 简化实现
    float total_energy = 0.0f;
    for (float s : signal) {
        total_energy += s * s;
    }

    float threshold = total_energy * rolloff_percent;
    float cumulative = 0.0f;

    for (size_t i = 0; i < signal.size(); ++i) {
        cumulative += signal[i] * signal[i];
        if (cumulative >= threshold) {
            return i * sample_rate / signal.size();
        }
    }

    return sample_rate / 2.0f;
}

// 演示基本特征
void demo_basic_features() {
    print_separator("基本音频特征");

    std::cout << "\n基本音频特征提取:\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;

    // 不同类型的信号
    auto sine = generate_sine(440.0f, sample_rate, duration);
    auto noise = generate_noise(sample_rate, duration, 0.5f);

    std::cout << "正弦波 (440 Hz):" << std::endl;
    std::cout << "  过零率: " << zero_crossing_rate(sine) << std::endl;
    std::cout << "  RMS 能量: " << rms_energy(sine) << std::endl;
    std::cout << "  频谱质心: " << spectral_centroid(sine, sample_rate) << " Hz" << std::endl;

    std::cout << "\n白噪声:" << std::endl;
    std::cout << "  过零率: " << zero_crossing_rate(noise) << std::endl;
    std::cout << "  RMS 能量: " << rms_energy(noise) << std::endl;
    std::cout << "  频谱质心: " << spectral_centroid(noise, sample_rate) << " Hz" << std::endl;
}

// 演示特征应用
void demo_feature_applications() {
    print_separator("特征应用");

    std::cout << "\n音频特征的常见应用:\n" << std::endl;

    std::cout << "1. 音频分类" << std::endl;
    std::cout << "   - 音乐/语音/噪声分类" << std::endl;
    std::cout << "   - 乐器识别" << std::endl;

    std::cout << "\n2. 语音识别" << std::endl;
    std::cout << "   - MFCC 特征" << std::endl;
    std::cout << "   - 说话人识别" << std::endl;

    std::cout << "\n3. 音乐信息检索" << std::endl;
    std::cout << "   - 相似度计算" << std::endl;
    std::cout << "   - 推荐系统" << std::endl;

    std::cout << "\n4. 音频监控" << std::endl;
    std::cout << "   - 异常声音检测" << std::endl;
    std::cout << "   - 环境音识别" << std::endl;

    // 比较不同信号的特征
    float sample_rate = 44100.0f;
    float duration = 1.0f;

    struct SignalInfo {
        std::string name;
        std::vector<float> signal;
    };

    std::vector<SignalInfo> signals = {
        {"正弦波", generate_sine(440.0f, sample_rate, duration)},
        {"方波", generate_square(440.0f, sample_rate, duration)},
        {"锯齿波", generate_sawtooth(440.0f, sample_rate, duration)},
        {"白噪声", generate_noise(sample_rate, duration)}
    };

    std::cout << "\n特征对比:" << std::endl;
    std::cout << "信号   | 过零率  | RMS能量 | 频谱质心" << std::endl;
    std::cout << "-------|--------|---------|----------" << std::endl;

    for (const auto& sig : signals) {
        printf("%-6s | %.4f | %.4f | %.0f Hz\n",
               sig.name.c_str(),
               zero_crossing_rate(sig.signal),
               rms_energy(sig.signal),
               spectral_centroid(sig.signal, sample_rate));
    }
}

int main() {
    std::cout << "=== Feature Extraction Demo (特征提取演示) ===" << std::endl;

    demo_basic_features();
    demo_feature_applications();

    std::cout << "\n=== 特征提取总结 ===" << std::endl;
    std::cout << "1. 过零率：信号过零的频率" << std::endl;
    std::cout << "2. 频谱质心：频谱的重心" << std::endl;
    std::cout << "3. RMS 能量：信号的均方根能量" << std::endl;
    std::cout << "4. 广泛用于音频分类和识别" << std::endl;

    return 0;
}
