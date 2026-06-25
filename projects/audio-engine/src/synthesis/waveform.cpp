// waveform.cpp - 波形合成演示
//
// 本文件演示波形合成的基本原理：
// 1. 正弦波生成
// 2. 方波、三角波、锯齿波
// 3. 脉冲宽度调制
//
// 编译: g++ -std=c++17 -I../../include waveform.cpp -o waveform -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 振荡器类
class Oscillator {
public:
    enum class WaveType {
        Sine,
        Square,
        Triangle,
        Sawtooth,
        Pulse
    };

    Oscillator(float freq = 440.0f, float sample_rate = 44100.0f)
        : freq_(freq)
        , sample_rate_(sample_rate)
        , phase_(0.0f)
        , pulse_width_(0.5f) {
        phase_increment_ = freq / sample_rate;
    }

    void set_frequency(float freq) {
        freq_ = freq;
        phase_increment_ = freq / sample_rate_;
    }

    void set_pulse_width(float width) {
        pulse_width_ = clamp(width, 0.01f, 0.99f);
    }

    float generate(WaveType type) {
        float sample = 0.0f;

        switch (type) {
            case WaveType::Sine:
                sample = std::sin(2.0f * M_PI * phase_);
                break;
            case WaveType::Square:
                sample = (phase_ < 0.5f) ? 1.0f : -1.0f;
                break;
            case WaveType::Triangle:
                sample = 2.0f * std::abs(2.0f * phase_ - 1.0f) - 1.0f;
                break;
            case WaveType::Sawtooth:
                sample = 2.0f * phase_ - 1.0f;
                break;
            case WaveType::Pulse:
                sample = (phase_ < pulse_width_) ? 1.0f : -1.0f;
                break;
        }

        // 更新相位
        phase_ += phase_increment_;
        if (phase_ >= 1.0f) phase_ -= 1.0f;

        return sample;
    }

    std::vector<float> generate_buffer(WaveType type, float duration) {
        size_t num_samples = static_cast<size_t>(sample_rate_ * duration);
        std::vector<float> samples(num_samples);
        for (size_t i = 0; i < num_samples; ++i) {
            samples[i] = generate(type);
        }
        return samples;
    }

private:
    float freq_;
    float sample_rate_;
    float phase_;
    float phase_increment_;
    float pulse_width_;
};

// 演示基本波形
void demo_basic_waveforms() {
    print_separator("基本波形");

    std::cout << "\n基本波形合成:\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 0.01f; // 10ms 便于可视化
    float freq = 440.0f;

    Oscillator osc(freq, sample_rate);

    std::cout << "频率: " << freq << " Hz" << std::endl;
    std::cout << "时长: " << duration * 1000 << " ms" << std::endl;

    struct WaveInfo {
        Oscillator::WaveType type;
        const char* name;
        const char* description;
    };

    std::vector<WaveInfo> waves = {
        {Oscillator::WaveType::Sine, "正弦波", "纯音，无谐波"},
        {Oscillator::WaveType::Square, "方波", "奇次谐波"},
        {Oscillator::WaveType::Triangle, "三角波", "奇次谐波，衰减快"},
        {Oscillator::WaveType::Sawtooth, "锯齿波", "所有谐波"}
    };

    for (const auto& wave : waves) {
        auto samples = osc.generate_buffer(wave.type, duration);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        std::cout << "\n" << wave.name << " (" << wave.description << "):" << std::endl;
        std::cout << "  峰值: " << buffer.peak() << std::endl;

        std::string filename = std::string("wave_") + wave.name + ".wav";
        // 生成更长的文件用于听觉测试
        auto long_samples = osc.generate_buffer(wave.type, 1.0f);
        AudioBuffer long_buffer = make_buffer(long_samples, static_cast<uint32_t>(sample_rate));
        write_wav(filename, long_buffer);
    }
}

// 演示脉冲宽度调制
void demo_pulse_width() {
    print_separator("脉冲宽度调制 (PWM)");

    std::cout << "\n脉冲宽度调制：改变方波的占空比\n" << std::endl;

    float sample_rate = 44100.0f;
    float freq = 440.0f;

    std::vector<float> widths = {0.1f, 0.25f, 0.5f, 0.75f, 0.9f};

    for (float width : widths) {
        Oscillator osc(freq, sample_rate);
        osc.set_pulse_width(width);

        auto samples = osc.generate_buffer(Oscillator::WaveType::Pulse, 1.0f);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        std::string filename = "wave_pwm_" +
                               std::to_string(static_cast<int>(width * 100)) + ".wav";
        write_wav(filename, buffer);

        std::cout << "占空比 " << width << ": " << filename << std::endl;
    }

    std::cout << "\n注意：不同占空比产生不同的音色" << std::endl;
}

// 演示波形特性
void demo_waveform_characteristics() {
    print_separator("波形特性");

    std::cout << "\n波形特性对比:\n" << std::endl;

    std::cout << "波形   | 谐波成分     | 音色特点" << std::endl;
    std::cout << "-------|-------------|----------" << std::endl;
    std::cout << "正弦波 | 无谐波       | 纯净、简单" << std::endl;
    std::cout << "方波   | 奇次谐波     | 空洞、鼻音" << std::endl;
    std::cout << "三角波 | 奇次谐波(快) | 柔和、木管" << std::endl;
    std::cout << "锯齿波 | 所有谐波     | 明亮、尖锐" << std::endl;

    std::cout << "\n谐波衰减规律:" << std::endl;
    std::cout << "  正弦波: 无谐波" << std::endl;
    std::cout << "  方波: 1/n (n 为奇数)" << std::endl;
    std::cout << "  三角波: 1/n^2 (n 为奇数)" << std::endl;
    std::cout << "  锯齿波: 1/n" << std::endl;
}

// 演示波形应用
void demo_waveform_applications() {
    print_separator("波形应用");

    std::cout << "\n波形合成的应用:\n" << std::endl;

    std::cout << "1. 音乐合成" << std::endl;
    std::cout << "   - 合成器音色" << std::endl;
    std::cout << "   - 电子音乐" << std::endl;

    std::cout << "\n2. 测试信号" << std::endl;
    std::cout << "   - 设备测试" << std::endl;
    std::cout << "   - 校准" << std::endl;

    std::cout << "\n3. 警报/提示音" << std::endl;
    std::cout << "   - 简单的音调" << std::endl;
    std::cout << "   - 通知声音" << std::endl;

    std::cout << "\n4. 效果处理" << std::endl;
    std::cout << "   - LFO 调制" << std::endl;
    std::cout << "   - 颤音效果" << std::endl;

    // 生成测试音阶
    float sample_rate = 44100.0f;
    std::vector<float> scale = {261.63f, 293.66f, 329.63f, 349.23f,
                                 392.00f, 440.00f, 493.88f, 523.25f};

    std::vector<float> all_samples;
    for (float freq : scale) {
        Oscillator osc(freq, sample_rate);
        auto samples = osc.generate_buffer(Oscillator::WaveType::Sine, 0.5f);
        all_samples.insert(all_samples.end(), samples.begin(), samples.end());
    }

    AudioBuffer buffer = make_buffer(all_samples, static_cast<uint32_t>(sample_rate));
    write_wav("wave_scale.wav", buffer);
    std::cout << "\n音阶文件已生成: wave_scale.wav" << std::endl;
}

int main() {
    std::cout << "=== Waveform Synthesis Demo (波形合成演示) ===" << std::endl;

    demo_basic_waveforms();
    demo_pulse_width();
    demo_waveform_characteristics();
    demo_waveform_applications();

    std::cout << "\n=== 波形合成总结 ===" << std::endl;
    std::cout << "1. 基本波形：正弦、方波、三角、锯齿" << std::endl;
    std::cout << "2. 不同波形有不同的谐波成分" << std::endl;
    std::cout << "3. 脉冲宽度调制改变音色" << std::endl;
    std::cout << "4. 广泛用于音乐合成和测试" << std::endl;

    return 0;
}
