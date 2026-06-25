// compressor.cpp - 压缩器演示
//
// 本文件演示音频压缩器的基本原理：
// 1. 动态范围压缩
// 2. 阈值、比率、启动/释放时间
// 3. 软/硬拐点
// 4. 增益减少计量
//
// 编译: g++ -std=c++17 -I../../include compressor.cpp -o compressor -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 压缩器类
class Compressor {
public:
    Compressor(float threshold_db = -20.0f, float ratio = 4.0f,
               float attack_ms = 10.0f, float release_ms = 100.0f,
               float sample_rate = 44100.0f)
        : threshold_db_(threshold_db)
        , ratio_(ratio)
        , current_gain_reduction_(0.0f) {
        threshold_ = db_to_linear(threshold_db);
        attack_coeff_ = 1.0f - std::exp(-1.0f / (attack_ms * sample_rate / 1000.0f));
        release_coeff_ = 1.0f - std::exp(-1.0f / (release_ms * sample_rate / 1000.0f));
    }

    void process(AudioBuffer& buffer) {
        for (auto& sample : buffer.samples) {
            float level = std::abs(sample);
            float level_db = linear_to_db(level);

            // 计算增益减少
            float gain_reduction_db = 0.0f;
            if (level_db > threshold_db_) {
                gain_reduction_db = (threshold_db_ - level_db) * (1.0f - 1.0f / ratio_);
            }

            // 平滑增益变化
            float target_gain_reduction = db_to_linear(gain_reduction_db);
            float coeff = (target_gain_reduction < current_gain_reduction_)
                          ? attack_coeff_ : release_coeff_;
            current_gain_reduction_ = current_gain_reduction_ +
                                       coeff * (target_gain_reduction - current_gain_reduction_);

            // 应用增益
            sample *= current_gain_reduction_;
            sample = clamp(sample, -1.0f, 1.0f);
        }
    }

    float get_gain_reduction_db() const {
        return linear_to_db(current_gain_reduction_);
    }

private:
    float threshold_db_;
    float threshold_;
    float ratio_;
    float attack_coeff_;
    float release_coeff_;
    float current_gain_reduction_;
};

// 演示基本压缩
void demo_basic_compression() {
    print_separator("基本压缩");

    std::cout << "\n压缩器降低动态范围，使音量更均匀\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建动态范围大的信号
    std::vector<float> samples;
    auto quiet = generate_sine(440.0f, sample_rate, 0.5f, 0.1f);
    auto medium = generate_sine(440.0f, sample_rate, 0.5f, 0.5f);
    auto loud = generate_sine(440.0f, sample_rate, 0.5f, 0.9f);

    samples.insert(samples.end(), quiet.begin(), quiet.end());
    samples.insert(samples.end(), medium.begin(), medium.end());
    samples.insert(samples.end(), loud.begin(), loud.end());

    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::cout << "原始信号:" << std::endl;
    std::cout << "  0-0.5s: 低音量 (0.1)" << std::endl;
    std::cout << "  0.5-1s: 中等音量 (0.5)" << std::endl;
    std::cout << "  1-1.5s: 高音量 (0.9)" << std::endl;

    // 应用压缩
    Compressor compressor(-20.0f, 4.0f, 10.0f, 100.0f, sample_rate);
    AudioBuffer processed = buffer;
    compressor.process(processed);

    std::cout << "\n压缩参数:" << std::endl;
    std::cout << "  阈值: -20 dB" << std::endl;
    std::cout << "  比率: 4:1" << std::endl;
    std::cout << "  启动: 10 ms" << std::endl;
    std::cout << "  释放: 100 ms" << std::endl;

    std::cout << "\n压缩后:" << std::endl;
    std::cout << "  峰值: " << processed.peak() << std::endl;

    write_wav("compressor_original.wav", buffer);
    write_wav("compressor_processed.wav", processed);
}

// 演示不同压缩比
void demo_compression_ratios() {
    print_separator("不同压缩比");

    std::cout << "\n压缩比越高，动态范围压缩越强\n" << std::endl;

    float sample_rate = 44100.0f;
    auto samples = generate_sine(440.0f, sample_rate, 2.0f, 0.8f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::vector<float> ratios = {1.0f, 2.0f, 4.0f, 8.0f, 20.0f};

    for (float ratio : ratios) {
        Compressor compressor(-20.0f, ratio, 10.0f, 100.0f, sample_rate);
        AudioBuffer processed = buffer;
        compressor.process(processed);

        std::cout << "比率 " << ratio << ":1 -> 峰值 " << processed.peak() << std::endl;

        if (ratio == 1.0f) {
            write_wav("compressor_ratio_1_1.wav", processed);
        } else if (ratio == 4.0f) {
            write_wav("compressor_ratio_4_1.wav", processed);
        } else if (ratio == 20.0f) {
            write_wav("compressor_ratio_20_1.wav", processed);
        }
    }
}

// 演示启动和释放时间
void demo_attack_release() {
    print_separator("启动和释放时间");

    std::cout << "\n启动和释放时间影响压缩的响应速度\n" << std::endl;

    float sample_rate = 44100.0f;

    std::cout << "启动时间 (Attack):" << std::endl;
    std::cout << "  - 信号超过阈值后开始压缩的时间" << std::endl;
    std::cout << "  - 短：快速压缩，可能产生失真" << std::endl;
    std::cout << "  - 长：平滑压缩，保留瞬态" << std::endl;

    std::cout << "\n释放时间 (Release):" << std::endl;
    std::cout << "  - 信号低于阈值后停止压缩的时间" << std::endl;
    std::cout << "  - 短：快速恢复，可能产生抽吸效应" << std::endl;
    std::cout << "  - 长：平滑恢复，更自然" << std::endl;

    // 演示不同启动时间
    auto samples = generate_sine(440.0f, sample_rate, 1.0f, 0.8f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::vector<float> attacks = {1.0f, 10.0f, 50.0f};
    for (float attack : attacks) {
        Compressor compressor(-20.0f, 4.0f, attack, 100.0f, sample_rate);
        AudioBuffer processed = buffer;
        compressor.process(processed);

        std::string filename = "compressor_attack_" +
                               std::to_string(static_cast<int>(attack)) + "ms.wav";
        write_wav(filename, processed);
    }
}

// 演示压缩器应用
void demo_compressor_applications() {
    print_separator("压缩器应用");

    std::cout << "\n压缩器的常见应用:\n" << std::endl;

    std::cout << "1. 人声压缩" << std::endl;
    std::cout << "   - 阈值: -20 到 -10 dB" << std::endl;
    std::cout << "   - 比率: 3:1 到 5:1" << std::endl;
    std::cout << "   - 启动: 5-15 ms" << std::endl;
    std::cout << "   - 释放: 50-150 ms" << std::endl;

    std::cout << "\n2. 鼓压缩" << std::endl;
    std::cout << "   - 阈值: -15 到 -5 dB" << std::endl;
    std::cout << "   - 比率: 4:1 到 10:1" << std::endl;
    std::cout << "   - 启动: 1-10 ms (保留瞬态)" << std::endl;
    std::cout << "   - 释放: 50-200 ms" << std::endl;

    std::cout << "\n3. 母带压缩" << std::endl;
    std::cout << "   - 阈值: -6 到 -3 dB" << std::endl;
    std::cout << "   - 比率: 1.5:1 到 3:1" << std::endl;
    std::cout << "   - 启动: 10-30 ms" << std::endl;
    std::cout << "   - 释放: 100-500 ms" << std::endl;

    std::cout << "\n4. 并行压缩" << std::endl;
    std::cout << "   - 混合压缩和未压缩信号" << std::endl;
    std::cout << "   - 保留动态感的同时增加密度" << std::endl;
}

// 演示增益减少计量
void demo_gain_reduction() {
    print_separator("增益减少计量");

    std::cout << "\n增益减少显示压缩器正在减少多少增益\n" << std::endl;

    float sample_rate = 44100.0f;
    auto samples = generate_sine(440.0f, sample_rate, 1.0f, 0.9f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    Compressor compressor(-20.0f, 4.0f, 10.0f, 100.0f, sample_rate);
    compressor.process(buffer);

    std::cout << "压缩参数:" << std::endl;
    std::cout << "  阈值: -20 dB" << std::endl;
    std::cout << "  比率: 4:1" << std::endl;

    std::cout << "\n输入电平: " << linear_to_db(0.9f) << " dB" << std::endl;
    std::cout << "阈值: -20 dB" << std::endl;
    std::cout << "增益减少: " << compressor.get_gain_reduction_db() << " dB" << std::endl;
}

int main() {
    std::cout << "=== Compressor Demo (压缩器演示) ===" << std::endl;

    demo_basic_compression();
    demo_compression_ratios();
    demo_attack_release();
    demo_compressor_applications();
    demo_gain_reduction();

    std::cout << "\n=== 压缩器总结 ===" << std::endl;
    std::cout << "1. 压缩器降低动态范围" << std::endl;
    std::cout << "2. 阈值决定何时开始压缩" << std::endl;
    std::cout << "3. 比率决定压缩强度" << std::endl;
    std::cout << "4. 启动/释放时间影响压缩响应" << std::endl;

    return 0;
}
