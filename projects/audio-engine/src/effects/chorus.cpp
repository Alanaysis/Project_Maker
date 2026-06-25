// chorus.cpp - 合唱效果演示
//
// 本文件演示音频合唱效果的基本原理：
// 1. LFO 调制延迟
// 2. 多声部合唱
// 3. 参数控制
//
// 编译: g++ -std=c++17 -I../../include chorus.cpp -o chorus -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 合唱效果器
class Chorus {
public:
    Chorus(float rate = 1.5f, float depth = 0.002f, float mix = 0.5f,
           int voices = 2, float sample_rate = 44100.0f)
        : rate_(rate)
        , depth_(depth)
        , mix_(mix)
        , voices_(voices)
        , sample_rate_(sample_rate)
        , phase_(0.0f) {
        max_delay_ = static_cast<size_t>(depth * sample_rate * 2) + 10;
        delay_buffer_.resize(max_delay_, 0.0f);
        write_pos_ = 0;

        // 初始化各声部相位
        for (int i = 0; i < voices; ++i) {
            voice_phases_.push_back(2.0f * M_PI * i / voices);
        }
    }

    float process(float input) {
        float output = input * (1.0f - mix_);

        // 写入延迟线
        delay_buffer_[write_pos_] = input;

        // 计算各声部
        for (int i = 0; i < voices_; ++i) {
            // LFO 调制延迟时间
            float lfo = std::sin(phase_ + voice_phases_[i]);
            float delay_sec = depth_ * (1.0f + lfo);
            size_t delay_samples = static_cast<size_t>(delay_sec * sample_rate_);

            // 读取延迟采样（线性插值）
            size_t read_pos = (write_pos_ + max_delay_ - delay_samples) % max_delay_;
            float delayed = delay_buffer_[read_pos];

            output += delayed * mix_ / voices_;
        }

        write_pos_ = (write_pos_ + 1) % max_delay_;
        phase_ += 2.0f * M_PI * rate_ / sample_rate_;

        return output;
    }

    void process_buffer(AudioBuffer& buffer) {
        for (auto& sample : buffer.samples) {
            sample = process(sample);
        }
    }

private:
    float rate_;
    float depth_;
    float mix_;
    int voices_;
    float sample_rate_;
    float phase_;
    std::vector<float> delay_buffer_;
    size_t max_delay_;
    size_t write_pos_;
    std::vector<float> voice_phases_;
};

// 演示基本合唱
void demo_basic_chorus() {
    print_separator("基本合唱");

    std::cout << "\n合唱效果：通过调制延迟创造多个声部\n" << std::endl;

    float sample_rate = 44100.0f;
    auto dry = generate_sine(440.0f, sample_rate, 2.0f, 0.7f);

    AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));

    Chorus chorus(1.5f, 0.002f, 0.5f, 2, sample_rate);
    chorus.process_buffer(buffer);

    std::cout << "参数:" << std::endl;
    std::cout << "  LFO 频率: 1.5 Hz" << std::endl;
    std::cout << "  深度: 2 ms" << std::endl;
    std::cout << "  混合: 0.5" << std::endl;
    std::cout << "  声部: 2" << std::endl;

    write_wav("chorus_basic.wav", buffer);
}

// 演示不同声部数
void demo_voices() {
    print_separator("不同声部数");

    std::cout << "\n声部越多，效果越丰富\n" << std::endl;

    float sample_rate = 44100.0f;
    auto dry = generate_sine(440.0f, sample_rate, 2.0f, 0.7f);

    std::vector<int> voice_counts = {1, 2, 4};

    for (int voices : voice_counts) {
        AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));
        Chorus chorus(1.5f, 0.002f, 0.5f, voices, sample_rate);
        chorus.process_buffer(buffer);

        std::string filename = "chorus_" + std::to_string(voices) + "voices.wav";
        write_wav(filename, buffer);

        std::cout << voices << " 声部: " << filename << std::endl;
    }
}

// 演示不同深度
void demo_depths() {
    print_separator("不同深度");

    std::cout << "\n深度影响调制范围\n" << std::endl;

    float sample_rate = 44100.0f;
    auto dry = generate_sine(440.0f, sample_rate, 2.0f, 0.7f);

    std::vector<float> depths = {0.001f, 0.002f, 0.005f};

    for (float depth : depths) {
        AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));
        Chorus chorus(1.5f, depth, 0.5f, 2, sample_rate);
        chorus.process_buffer(buffer);

        std::string filename = "chorus_depth_" +
                               std::to_string(static_cast<int>(depth * 1000)) + "ms.wav";
        write_wav(filename, buffer);

        std::cout << "深度 " << depth * 1000 << " ms: " << filename << std::endl;
    }
}

// 演示合唱应用
void demo_chorus_applications() {
    print_separator("合唱应用");

    std::cout << "\n合唱效果的常见应用:\n" << std::endl;

    std::cout << "1. 吉他合唱" << std::endl;
    std::cout << "   - 增加厚度和宽度" << std::endl;
    std::cout << "   - 速率: 0.5-2 Hz" << std::endl;
    std::cout << "   - 深度: 1-3 ms" << std::endl;

    std::cout << "\n2. 人声合唱" << std::endl;
    std::cout << "   - 模拟多人合唱" << std::endl;
    std::cout << "   - 速率: 1-3 Hz" << std::endl;
    std::cout << "   - 深度: 2-5 ms" << std::endl;

    std::cout << "\n3. 键盘/合成器" << std::endl;
    std::cout << "   - 增加运动感" << std::endl;
    std::cout << "   - 速率: 0.3-1 Hz" << std::endl;
    std::cout << "   - 深度: 3-10 ms" << std::endl;

    // 生成吉他合唱示例
    float sample_rate = 44100.0f;
    auto guitar = generate_sine(330.0f, sample_rate, 3.0f, 0.6f);
    AudioBuffer buffer = make_buffer(guitar, static_cast<uint32_t>(sample_rate));

    Chorus chorus(0.8f, 0.003f, 0.4f, 2, sample_rate);
    chorus.process_buffer(buffer);

    write_wav("chorus_guitar.wav", buffer);
}

int main() {
    std::cout << "=== Chorus Effect Demo (合唱效果演示) ===" << std::endl;

    demo_basic_chorus();
    demo_voices();
    demo_depths();
    demo_chorus_applications();

    std::cout << "\n=== 合唱效果总结 ===" << std::endl;
    std::cout << "1. 合唱通过 LFO 调制延迟时间" << std::endl;
    std::cout << "2. 多声部增加丰富度" << std::endl;
    std::cout << "3. 深度和速率控制效果强度" << std::endl;
    std::cout << "4. 常用于吉他、人声、键盘" << std::endl;

    return 0;
}
