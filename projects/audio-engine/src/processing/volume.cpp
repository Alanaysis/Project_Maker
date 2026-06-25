// volume.cpp - 音量调节演示
//
// 本文件演示音频音量调节的基本原理：
// 1. 线性音量调节
// 2. 分贝音量调节
// 3. 自动增益控制（AGC）
//
// 编译: g++ -std=c++17 -I../../include volume.cpp -o volume -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 线性音量调节
void apply_linear_gain(AudioBuffer& buffer, float gain) {
    for (auto& sample : buffer.samples) {
        sample *= gain;
        sample = clamp(sample, -1.0f, 1.0f);
    }
}

// 分贝音量调节
void apply_db_gain(AudioBuffer& buffer, float db) {
    float gain = db_to_linear(db);
    apply_linear_gain(buffer, gain);
}

// 自动增益控制 (AGC)
class AutoGainControl {
public:
    AutoGainControl(float target_level_db = -20.0f, float attack_ms = 10.0f,
                    float release_ms = 100.0f, float sample_rate = 44100.0f)
        : target_level_(db_to_linear(target_level_db))
        , current_gain_(1.0f) {
        attack_coeff_ = 1.0f - std::exp(-1.0f / (attack_ms * sample_rate / 1000.0f));
        release_coeff_ = 1.0f - std::exp(-1.0f / (release_ms * sample_rate / 1000.0f));
    }

    void process(AudioBuffer& buffer) {
        for (auto& sample : buffer.samples) {
            float level = std::abs(sample);
            float target_gain = (level > 0.001f) ? target_level_ / level : 1.0f;

            // 平滑增益变化
            float coeff = (target_gain < current_gain_) ? attack_coeff_ : release_coeff_;
            current_gain_ = current_gain_ + coeff * (target_gain - current_gain_);

            // 限制增益范围
            current_gain_ = clamp(current_gain_, 0.1f, 10.0f);

            sample *= current_gain_;
            sample = clamp(sample, -1.0f, 1.0f);
        }
    }

private:
    float target_level_;
    float current_gain_;
    float attack_coeff_;
    float release_coeff_;
};

// 演示线性音量调节
void demo_linear_volume() {
    print_separator("线性音量调节");

    std::cout << "\n线性音量调节：直接乘以增益系数\n" << std::endl;

    auto samples = generate_sine(440.0f, 44100.0f, 1.0f);
    AudioBuffer buffer = make_buffer(samples, 44100);

    std::cout << "原始信号:" << std::endl;
    std::cout << "  峰值: " << buffer.peak() << std::endl;
    std::cout << "  RMS: " << buffer.rms() << std::endl;

    // 不同增益
    std::vector<float> gains = {0.25f, 0.5f, 0.75f, 1.0f, 1.5f, 2.0f};

    for (float gain : gains) {
        AudioBuffer processed = buffer;
        apply_linear_gain(processed, gain);

        std::cout << "\n增益 " << gain << ":" << std::endl;
        std::cout << "  峰值: " << processed.peak() << std::endl;
        std::cout << "  RMS: " << processed.rms() << std::endl;
    }
}

// 演示分贝音量调节
void demo_db_volume() {
    print_separator("分贝音量调节");

    std::cout << "\n分贝音量调节：使用 dB 值控制音量\n" << std::endl;

    auto samples = generate_sine(440.0f, 44100.0f, 1.0f);
    AudioBuffer buffer = make_buffer(samples, 44100);

    std::cout << "原始信号 (0 dB):" << std::endl;
    std::cout << "  峰值: " << buffer.peak() << std::endl;

    // 不同 dB 值
    std::vector<float> db_values = {-12.0f, -6.0f, -3.0f, 0.0f, 3.0f, 6.0f};

    for (float db : db_values) {
        AudioBuffer processed = buffer;
        apply_db_gain(processed, db);

        std::cout << "\n" << db << " dB (增益 = " << db_to_linear(db) << "):" << std::endl;
        std::cout << "  峰值: " << processed.peak() << std::endl;
    }

    std::cout << "\n常用 dB 值:" << std::endl;
    std::cout << "  -6 dB: 音量减半" << std::endl;
    std::cout << "  -12 dB: 音量减至 1/4" << std::endl;
    std::cout << "  +6 dB: 音量加倍" << std::endl;
}

// 演示自动增益控制
void demo_agc() {
    print_separator("自动增益控制 (AGC)");

    std::cout << "\nAGC 自动调整音量到目标电平\n" << std::endl;

    // 创建音量变化的信号
    std::vector<float> samples;
    float sample_rate = 44100.0f;

    // 前 0.5 秒：低音量
    auto quiet = generate_sine(440.0f, sample_rate, 0.5f, 0.1f);
    samples.insert(samples.end(), quiet.begin(), quiet.end());

    // 中间 0.5 秒：中等音量
    auto medium = generate_sine(440.0f, sample_rate, 0.5f, 0.5f);
    samples.insert(samples.end(), medium.begin(), medium.end());

    // 后 0.5 秒：高音量
    auto loud = generate_sine(440.0f, sample_rate, 0.5f, 0.9f);
    samples.insert(samples.end(), loud.begin(), loud.end());

    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::cout << "原始信号 (音量变化):" << std::endl;
    std::cout << "  0-0.5s: 低音量 (0.1)" << std::endl;
    std::cout << "  0.5-1s: 中等音量 (0.5)" << std::endl;
    std::cout << "  1-1.5s: 高音量 (0.9)" << std::endl;

    // 应用 AGC
    AutoGainControl agc(-20.0f, 10.0f, 100.0f, sample_rate);
    AudioBuffer processed = buffer;
    agc.process(processed);

    std::cout << "\nAGC 处理后:" << std::endl;
    std::cout << "  目标电平: -20 dB" << std::endl;
    std::cout << "  峰值: " << processed.peak() << std::endl;
    std::cout << "  RMS: " << processed.rms() << std::endl;

    // 保存文件
    write_wav("volume_original.wav", buffer);
    write_wav("volume_agc.wav", processed);
}

// 演示音量单位
void demo_volume_units() {
    print_separator("音量单位");

    std::cout << "\n音频中常用的音量单位:\n" << std::endl;

    std::cout << "1. dBFS (dB Full Scale)" << std::endl;
    std::cout << "   - 数字音频的标准单位" << std::endl;
    std::cout << "   - 0 dBFS = 最大可表示值" << std::endl;
    std::cout << "   - 所有值都是负数" << std::endl;

    std::cout << "\n2. dBu" << std::endl;
    std::cout << "   - 模拟音频的标准单位" << std::endl;
    std::cout << "   - 0 dBu = 0.775V" << std::endl;

    std::cout << "\n3. dBV" << std::endl;
    std::cout << "   - 0 dBV = 1V" << std::endl;

    std::cout << "\n常用电平参考:" << std::endl;
    std::cout << "  0 dBFS: 最大电平（削波）" << std::endl;
    std::cout << "  -6 dBFS: 专业音频最大工作电平" << std::endl;
    std::cout << "  -18 dBFS: 0 VU (模拟标准)" << std::endl;
    std::cout << "  -20 dBFS: 广播标准" << std::endl;
    std::cout << "  -60 dBFS: 噪声底限" << std::endl;

    // 演示转换
    std::cout << "\n线性值与 dB 转换:" << std::endl;
    std::vector<float> linear_values = {0.001f, 0.01f, 0.1f, 0.5f, 1.0f};

    for (float v : linear_values) {
        printf("  %.3f -> %.1f dBFS\n", v, linear_to_db(v));
    }
}

// 生成音量测试文件
void generate_volume_demos() {
    print_separator("生成音量测试文件");

    std::cout << "\n生成不同音量的测试文件:\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 2.0f;

    struct VolumeDemo {
        float db;
        const char* label;
        const char* filename;
    };

    std::vector<VolumeDemo> demos = {
        {-6.0f, "-6 dB", "volume_neg6db.wav"},
        {-12.0f, "-12 dB", "volume_neg12db.wav"},
        {-20.0f, "-20 dB", "volume_neg20db.wav"},
        {-40.0f, "-40 dB", "volume_neg40db.wav"}
    };

    for (const auto& demo : demos) {
        auto samples = generate_sine(1000.0f, sample_rate, duration);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));
        apply_db_gain(buffer, demo.db);

        write_wav(demo.filename, buffer);
        std::cout << "  " << demo.label << ": " << demo.filename
                  << " (峰值: " << buffer.peak() << ")" << std::endl;
    }
}

int main() {
    std::cout << "=== Volume Control Demo (音量调节演示) ===" << std::endl;

    demo_linear_volume();
    demo_db_volume();
    demo_agc();
    demo_volume_units();
    generate_volume_demos();

    std::cout << "\n=== 音量调节总结 ===" << std::endl;
    std::cout << "1. 线性增益：直接乘以系数" << std::endl;
    std::cout << "2. dB 增益：使用对数刻度，更符合人耳感知" << std::endl;
    std::cout << "3. AGC：自动调整到目标电平" << std::endl;
    std::cout << "4. 0 dBFS 是数字音频的最大电平" << std::endl;

    return 0;
}
