// rhythm.cpp - 节奏检测演示
//
// 本文件演示节奏检测的基本原理：
// 1. 能量检测
// 2. 自相关分析
// 3. BPM 估计
//
// 编译: g++ -std=c++17 -I../../include rhythm.cpp -o rhythm -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 计算短时能量
std::vector<float> short_time_energy(const AudioBuffer& buffer, size_t frame_size,
                                       size_t hop_size) {
    size_t num_frames = (buffer.num_samples() - frame_size) / hop_size + 1;
    std::vector<float> energy(num_frames);

    for (size_t i = 0; i < num_frames; ++i) {
        float sum = 0.0f;
        size_t start = i * hop_size;
        for (size_t j = 0; j < frame_size; ++j) {
            float sample = buffer.samples[start + j];
            sum += sample * sample;
        }
        energy[i] = sum / frame_size;
    }

    return energy;
}

// 检测峰值（节拍位置）
std::vector<size_t> detect_peaks(const std::vector<float>& energy,
                                   float threshold_factor = 1.5f) {
    std::vector<size_t> peaks;

    // 计算平均能量
    float mean_energy = 0.0f;
    for (float e : energy) {
        mean_energy += e;
    }
    mean_energy /= energy.size();

    float threshold = mean_energy * threshold_factor;

    // 寻找峰值
    for (size_t i = 1; i < energy.size() - 1; ++i) {
        if (energy[i] > threshold &&
            energy[i] > energy[i - 1] &&
            energy[i] > energy[i + 1]) {
            // 确保峰值之间有最小间隔
            if (peaks.empty() || i - peaks.back() > 5) {
                peaks.push_back(i);
            }
        }
    }

    return peaks;
}

// 从峰值间隔估计 BPM
float estimate_bpm(const std::vector<size_t>& peaks, float frame_rate) {
    if (peaks.size() < 2) return 0.0f;

    // 计算平均间隔
    float total_interval = 0.0f;
    for (size_t i = 1; i < peaks.size(); ++i) {
        total_interval += peaks[i] - peaks[i - 1];
    }
    float avg_interval = total_interval / (peaks.size() - 1);

    // 转换为 BPM
    float bpm = 60.0f * frame_rate / avg_interval;

    // 调整到合理范围 (60-200 BPM)
    while (bpm < 60.0f) bpm *= 2.0f;
    while (bpm > 200.0f) bpm /= 2.0f;

    return bpm;
}

// 演示能量检测
void demo_energy_detection() {
    print_separator("能量检测");

    std::cout << "\n能量检测：识别信号中的节拍位置\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 4.0f;

    // 创建模拟节拍的信号
    std::vector<float> samples;
    float bpm = 120.0f;
    float beat_interval = 60.0f / bpm;
    size_t beat_samples = static_cast<size_t>(beat_interval * sample_rate);

    for (size_t i = 0; i < static_cast<size_t>(duration * sample_rate); ++i) {
        float t = static_cast<float>(i) / sample_rate;
        float beat_phase = std::fmod(t, beat_interval) / beat_interval;

        // 在每个节拍位置创建脉冲
        float sample = 0.0f;
        if (beat_phase < 0.1f) {
            sample = 0.8f * std::sin(2.0f * M_PI * 100.0f * t);
        }
        samples.push_back(sample);
    }

    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    // 计算短时能量
    size_t frame_size = 1024;
    size_t hop_size = 512;
    auto energy = short_time_energy(buffer, frame_size, hop_size);

    std::cout << "参数:" << std::endl;
    std::cout << "  帧大小: " << frame_size << std::endl;
    std::cout << "  跳步大小: " << hop_size << std::endl;
    std::cout << "  能量帧数: " << energy.size() << std::endl;

    // 检测峰值
    auto peaks = detect_peaks(energy);
    float frame_rate = sample_rate / hop_size;

    std::cout << "\n检测到 " << peaks.size() << " 个节拍" << std::endl;

    // 估计 BPM
    float estimated_bpm = estimate_bpm(peaks, frame_rate);
    std::cout << "估计 BPM: " << estimated_bpm << std::endl;
    std::cout << "实际 BPM: " << bpm << std::endl;
}

// 演示 BPM 估计
void demo_bpm_estimation() {
    print_separator("BPM 估计");

    std::cout << "\nBPM 估计：从节拍间隔计算每分钟节拍数\n" << std::endl;

    float sample_rate = 44100.0f;

    std::vector<float> target_bpms = {90.0f, 120.0f, 140.0f};

    for (float target_bpm : target_bpms) {
        // 创建指定 BPM 的信号
        std::vector<float> samples;
        float beat_interval = 60.0f / target_bpm;

        for (size_t i = 0; i < static_cast<size_t>(4.0f * sample_rate); ++i) {
            float t = static_cast<float>(i) / sample_rate;
            float beat_phase = std::fmod(t, beat_interval) / beat_interval;

            float sample = 0.0f;
            if (beat_phase < 0.05f) {
                sample = 0.9f;
            }
            samples.push_back(sample);
        }

        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        auto energy = short_time_energy(buffer, 1024, 512);
        auto peaks = detect_peaks(energy);
        float estimated_bpm = estimate_bpm(peaks, sample_rate / 512);

        std::cout << "目标 BPM: " << target_bpm
                  << " -> 估计 BPM: " << estimated_bpm << std::endl;
    }
}

// 演示节奏检测应用
void demo_rhythm_applications() {
    print_separator("节奏检测应用");

    std::cout << "\n节奏检测的常见应用:\n" << std::endl;

    std::cout << "1. 音乐信息检索" << std::endl;
    std::cout << "   - 自动识别歌曲 BPM" << std::endl;
    std::cout << "   - 音乐分类和推荐" << std::endl;

    std::cout << "\n2. DJ 软件" << std::endl;
    std::cout << "   - 节拍同步" << std::endl;
    std::cout << "   - 自动混音" << std::endl;

    std::cout << "\n3. 音乐制作" << std::endl;
    std::cout << "   - 量化音符" << std::endl;
    std::cout << "   - 节奏分析" << std::endl;

    std::cout << "\n4. 舞蹈游戏" << std::endl;
    std::cout << "   - 节拍检测" << std::endl;
    std::cout << "   - 同步游戏元素" << std::endl;
}

int main() {
    std::cout << "=== Rhythm Detection Demo (节奏检测演示) ===" << std::endl;

    demo_energy_detection();
    demo_bpm_estimation();
    demo_rhythm_applications();

    std::cout << "\n=== 节奏检测总结 ===" << std::endl;
    std::cout << "1. 能量检测识别节拍位置" << std::endl;
    std::cout << "2. 自相关分析找到周期性" << std::endl;
    std::cout << "3. BPM 从节拍间隔计算" << std::endl;
    std::cout << "4. 广泛用于音乐信息检索和 DJ 软件" << std::endl;

    return 0;
}
