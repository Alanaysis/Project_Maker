// limiter.cpp - 限幅器演示
//
// 本文件演示音频限幅器的基本原理：
// 1. 峰值限幅
// 2. 真峰值限幅
// 3. 释放时间控制
//
// 编译: g++ -std=c++17 -I../../include limiter.cpp -o limiter -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 限幅器类
class Limiter {
public:
    Limiter(float threshold_db = -0.1f, float release_ms = 50.0f,
            float sample_rate = 44100.0f)
        : threshold_db_(threshold_db)
        , current_gain_(1.0f) {
        threshold_ = db_to_linear(threshold_db);
        release_coeff_ = 1.0f - std::exp(-1.0f / (release_ms * sample_rate / 1000.0f));
    }

    void process(AudioBuffer& buffer) {
        for (auto& sample : buffer.samples) {
            float level = std::abs(sample);

            // 计算需要的增益
            float target_gain = 1.0f;
            if (level > threshold_) {
                target_gain = threshold_ / level;
            }

            // 平滑增益变化
            if (target_gain < current_gain_) {
                // 立即限制
                current_gain_ = target_gain;
            } else {
                // 释放
                current_gain_ = current_gain_ +
                                release_coeff_ * (target_gain - current_gain_);
            }

            // 应用增益
            sample *= current_gain_;
            sample = clamp(sample, -threshold_, threshold_);
        }
    }

private:
    float threshold_db_;
    float threshold_;
    float release_coeff_;
    float current_gain_;
};

// 演示基本限幅
void demo_basic_limiting() {
    print_separator("基本限幅");

    std::cout << "\n限幅器防止信号超过阈值\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建可能削波的信号
    auto samples = generate_sine(440.0f, sample_rate, 1.0f, 1.2f); // 超过 1.0
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::cout << "原始信号:" << std::endl;
    std::cout << "  峰值: " << buffer.peak() << " (超过 1.0，会削波)" << std::endl;

    // 应用限幅
    Limiter limiter(-0.1f, 50.0f, sample_rate);
    AudioBuffer processed = buffer;
    limiter.process(processed);

    std::cout << "\n限幅后:" << std::endl;
    std::cout << "  阈值: -0.1 dBFS" << std::endl;
    std::cout << "  峰值: " << processed.peak() << " (限制在阈值以下)" << std::endl;

    write_wav("limiter_original.wav", buffer);
    write_wav("limiter_processed.wav", processed);
}

// 演示不同阈值
void demo_thresholds() {
    print_separator("不同阈值");

    std::cout << "\n不同阈值的限幅效果:\n" << std::endl;

    float sample_rate = 44100.0f;
    auto samples = generate_sine(440.0f, sample_rate, 1.0f, 0.9f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::vector<float> thresholds = {-6.0f, -3.0f, -1.0f, -0.1f};

    for (float thresh : thresholds) {
        Limiter limiter(thresh, 50.0f, sample_rate);
        AudioBuffer processed = buffer;
        limiter.process(processed);

        std::cout << "阈值 " << thresh << " dB: 峰值 = " << processed.peak() << std::endl;

        std::string filename = "limiter_thresh_" +
                               std::to_string(static_cast<int>(thresh)) + "db.wav";
        write_wav(filename, processed);
    }
}

// 演示释放时间
void demo_release_time() {
    print_separator("释放时间");

    std::cout << "\n释放时间影响限幅器的恢复速度\n" << std::endl;

    float sample_rate = 44100.0f;

    std::cout << "释放时间短 (10 ms):" << std::endl;
    std::cout << "  - 快速恢复" << std::endl;
    std::cout << "  - 可能产生失真" << std::endl;

    std::cout << "\n释放时间长 (200 ms):" << std::endl;
    std::cout << "  - 平滑恢复" << std::endl;
    std::cout << "  - 更自然的声音" << std::endl;

    auto samples = generate_sine(440.0f, sample_rate, 1.0f, 1.1f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    // 短释放
    Limiter short_release(-0.1f, 10.0f, sample_rate);
    AudioBuffer short_processed = buffer;
    short_release.process(short_processed);
    write_wav("limiter_release_short.wav", short_processed);

    // 长释放
    Limiter long_release(-0.1f, 200.0f, sample_rate);
    AudioBuffer long_processed = buffer;
    long_release.process(long_processed);
    write_wav("limiter_release_long.wav", long_processed);
}

// 演示限幅器与压缩器的区别
void demo_limiter_vs_compressor() {
    print_separator("限幅器 vs 压缩器");

    std::cout << "\n限幅器和压缩器的区别:\n" << std::endl;

    std::cout << "特性       | 压缩器          | 限幅器" << std::endl;
    std::cout << "-----------|-----------------|----------------" << std::endl;
    std::cout << "目的       | 减小动态范围     | 防止削波" << std::endl;
    std::cout << "比率       | 2:1 到 10:1    | 10:1 到 inf:1" << std::endl;
    std::cout << "阈值       | 较低 (-20 dB)   | 接近 0 dB" << std::endl;
    std::cout << "应用       | 音乐制作        | 母带处理" << std::endl;

    std::cout << "\n简单来说:" << std::endl;
    std::cout << "  - 压缩器: 降低动态范围，使音量更均匀" << std::endl;
    std::cout << "  - 限幅器: 硬性限制最大电平，防止削波" << std::endl;

    std::cout << "\n实际应用中，限幅器通常用在母带处理的最后一步" << std::endl;
}

// 演示真峰值限幅概念
void demo_true_peak() {
    print_separator("真峰值限幅");

    std::cout << "\n真峰值限幅考虑采样间的峰值:\n" << std::endl;

    std::cout << "问题：采样值可能不到 1.0，但采样间的峰值可能超过" << std::endl;
    std::cout << "解决方案：使用过采样检测真峰值" << std::endl;

    std::cout << "\n真峰值 (True Peak) vs 峰值 (Sample Peak):" << std::endl;
    std::cout << "  - 峰值: 采样点的最大绝对值" << std::endl;
    std::cout << "  - 真峰值: 考虑采样间插值后的最大值" << std::endl;

    std::cout << "\n广播标准通常要求真峰值不超过 -1 dBTP" << std::endl;
    std::cout << "dBTP = dB True Peak" << std::endl;

    float sample_rate = 44100.0f;
    auto samples = generate_sine(440.0f, sample_rate, 1.0f, 0.95f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    Limiter limiter(-1.0f, 50.0f, sample_rate);
    AudioBuffer processed = buffer;
    limiter.process(processed);

    write_wav("limiter_true_peak.wav", processed);
}

int main() {
    std::cout << "=== Limiter Demo (限幅器演示) ===" << std::endl;

    demo_basic_limiting();
    demo_thresholds();
    demo_release_time();
    demo_limiter_vs_compressor();
    demo_true_peak();

    std::cout << "\n=== 限幅器总结 ===" << std::endl;
    std::cout << "1. 限幅器防止信号超过阈值" << std::endl;
    std::cout << "2. 阈值通常设置在 -0.1 到 -1 dB" << std::endl;
    std::cout << "3. 释放时间影响恢复速度和音质" << std::endl;
    std::cout << "4. 用于母带处理和广播标准化" << std::endl;

    return 0;
}
