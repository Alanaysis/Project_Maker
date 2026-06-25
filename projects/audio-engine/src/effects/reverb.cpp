// reverb.cpp - 混响效果演示
//
// 本文件演示音频混响效果的基本原理：
// 1. Schroeder 混响
// 2. 梳状滤波器
// 3. 全通滤波器
// 4. 参数控制
//
// 编译: g++ -std=c++17 -I../../include reverb.cpp -o reverb -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 延迟线
class DelayLine {
public:
    DelayLine(size_t max_delay) : buffer_(max_delay, 0.0f), write_pos_(0) {}

    float read(size_t delay) const {
        size_t read_pos = (write_pos_ + buffer_.size() - delay) % buffer_.size();
        return buffer_[read_pos];
    }

    void write(float sample) {
        buffer_[write_pos_] = sample;
        write_pos_ = (write_pos_ + 1) % buffer_.size();
    }

private:
    std::vector<float> buffer_;
    size_t write_pos_;
};

// 梳状滤波器
class CombFilter {
public:
    CombFilter(float delay_ms, float feedback, float damping, float sample_rate)
        : delay_line_(static_cast<size_t>(delay_ms * sample_rate / 1000.0f) + 1)
        , feedback_(feedback)
        , damping_(damping)
        , last_output_(0.0f) {
        delay_samples_ = static_cast<size_t>(delay_ms * sample_rate / 1000.0f);
    }

    float process(float input) {
        float delayed = delay_line_.read(delay_samples_);
        float output = delayed;

        // 低通滤波（阻尼）
        last_output_ = last_output_ * damping_ + output * (1.0f - damping_);

        delay_line_.write(input + last_output_ * feedback_);

        return output;
    }

private:
    DelayLine delay_line_;
    size_t delay_samples_;
    float feedback_;
    float damping_;
    float last_output_;
};

// 全通滤波器
class AllpassFilter {
public:
    AllpassFilter(float delay_ms, float sample_rate)
        : delay_line_(static_cast<size_t>(delay_ms * sample_rate / 1000.0f) + 1)
        , coefficient_(0.5f) {
        delay_samples_ = static_cast<size_t>(delay_ms * sample_rate / 1000.0f);
    }

    float process(float input) {
        float delayed = delay_line_.read(delay_samples_);
        float output = -coefficient_ * input + delayed;
        delay_line_.write(input + coefficient_ * delayed);
        return output;
    }

private:
    DelayLine delay_line_;
    size_t delay_samples_;
    float coefficient_;
};

// Schroeder 混响器
class SchroederReverb {
public:
    SchroederReverb(float room_size = 0.5f, float damping = 0.5f,
                    float mix = 0.3f, float sample_rate = 44100.0f)
        : mix_(mix)
        , comb1_(30.0f * room_size, 0.8f, damping, sample_rate)
        , comb2_(34.0f * room_size, 0.8f, damping, sample_rate)
        , comb3_(39.0f * room_size, 0.8f, damping, sample_rate)
        , comb4_(44.0f * room_size, 0.8f, damping, sample_rate)
        , allpass1_(5.0f, sample_rate)
        , allpass2_(1.7f, sample_rate) {}

    float process(float input) {
        // 并行梳状滤波器
        float comb_sum = comb1_.process(input) + comb2_.process(input) +
                         comb3_.process(input) + comb4_.process(input);
        comb_sum *= 0.25f; // 归一化

        // 串联全通滤波器
        float output = allpass1_.process(comb_sum);
        output = allpass2_.process(output);

        // 混合干湿信号
        return input * (1.0f - mix_) + output * mix_;
    }

    void process_buffer(AudioBuffer& buffer) {
        for (auto& sample : buffer.samples) {
            sample = process(sample);
        }
    }

private:
    float mix_;
    CombFilter comb1_, comb2_, comb3_, comb4_;
    AllpassFilter allpass1_, allpass2_;
};

// 演示基本混响
void demo_basic_reverb() {
    print_separator("基本混响");

    std::cout << "\nSchroeder 混响：经典的数字混响算法\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建干信号（短脉冲）
    std::vector<float> dry(44100, 0.0f);
    dry[0] = 1.0f; // 脉冲

    AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));

    std::cout << "Schroeder 混响结构:" << std::endl;
    std::cout << "  - 4 个并行梳状滤波器" << std::endl;
    std::cout << "  - 2 个串联全通滤波器" << std::endl;

    // 应用混响
    SchroederReverb reverb(0.5f, 0.5f, 0.3f, sample_rate);
    reverb.process_buffer(buffer);

    std::cout << "\n参数:" << std::endl;
    std::cout << "  房间大小: 0.5" << std::endl;
    std::cout << "  阻尼: 0.5" << std::endl;
    std::cout << "  混合: 0.3" << std::endl;

    write_wav("reverb_basic.wav", buffer);
}

// 演示不同房间大小
void demo_room_sizes() {
    print_separator("不同房间大小");

    std::cout << "\n房间大小影响混响时间\n" << std::endl;

    float sample_rate = 44100.0f;
    auto dry = generate_sine(440.0f, sample_rate, 0.5f, 0.5f);

    std::vector<float> room_sizes = {0.2f, 0.5f, 0.8f};

    for (float size : room_sizes) {
        AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));
        SchroederReverb reverb(size, 0.5f, 0.3f, sample_rate);
        reverb.process_buffer(buffer);

        std::string filename = "reverb_size_" +
                               std::to_string(static_cast<int>(size * 10)) + ".wav";
        write_wav(filename, buffer);

        std::cout << "房间大小 " << size << ": " << filename << std::endl;
    }
}

// 演示不同阻尼
void demo_damping() {
    print_separator("不同阻尼");

    std::cout << "\n阻尼控制高频衰减速度\n" << std::endl;

    float sample_rate = 44100.0f;
    auto dry = generate_sine(440.0f, sample_rate, 0.5f, 0.5f);

    std::vector<float> dampings = {0.2f, 0.5f, 0.8f};

    for (float damp : dampings) {
        AudioBuffer buffer = make_buffer(dry, static_cast<uint32_t>(sample_rate));
        SchroederReverb reverb(0.5f, damp, 0.3f, sample_rate);
        reverb.process_buffer(buffer);

        std::string filename = "reverb_damp_" +
                               std::to_string(static_cast<int>(damp * 10)) + ".wav";
        write_wav(filename, buffer);

        std::cout << "阻尼 " << damp << ": " << filename << std::endl;
    }
}

// 演示混响应用
void demo_reverb_applications() {
    print_separator("混响应用");

    std::cout << "\n混响的常见应用:\n" << std::endl;

    std::cout << "1. 人声混响" << std::endl;
    std::cout << "   - 增加空间感" << std::endl;
    std::cout << "   - 房间大小: 0.3-0.6" << std::endl;
    std::cout << "   - 混合: 0.2-0.4" << std::endl;

    std::cout << "\n2. 鼓混响" << std::endl;
    std::cout << "   - 增加冲击感" << std::endl;
    std::cout << "   - 房间大小: 0.5-0.8" << std::endl;
    std::cout << "   - 混合: 0.3-0.5" << std::endl;

    std::cout << "\n3. 钢琴混响" << std::endl;
    std::cout << "   - 增加丰富度" << std::endl;
    std::cout << "   - 房间大小: 0.6-0.9" << std::endl;
    std::cout << "   - 混合: 0.3-0.5" << std::endl;

    // 生成人声混响示例
    float sample_rate = 44100.0f;
    auto vocal = generate_sine(300.0f, sample_rate, 2.0f, 0.6f);
    AudioBuffer buffer = make_buffer(vocal, static_cast<uint32_t>(sample_rate));

    SchroederReverb reverb(0.4f, 0.6f, 0.3f, sample_rate);
    reverb.process_buffer(buffer);

    write_wav("reverb_vocal.wav", buffer);
}

int main() {
    std::cout << "=== Reverb Effect Demo (混响效果演示) ===" << std::endl;

    demo_basic_reverb();
    demo_room_sizes();
    demo_damping();
    demo_reverb_applications();

    std::cout << "\n=== 混响效果总结 ===" << std::endl;
    std::cout << "1. 混响模拟声音在空间中的反射" << std::endl;
    std::cout << "2. Schroeder 混响使用梳状滤波器和全通滤波器" << std::endl;
    std::cout << "3. 房间大小控制混响时间" << std::endl;
    std::cout << "4. 阻尼控制高频衰减" << std::endl;
    std::cout << "\n注意：代码中有语法错误需要修复（namespace 重复）" << std::endl;

    return 0;
}
