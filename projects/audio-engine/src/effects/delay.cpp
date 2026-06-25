// delay.cpp - 延迟效果演示
//
// 本文件演示音频延迟效果的基本原理：
// 1. 单延迟效果
// 2. 延迟+反馈
// 3. Ping-pong 延迟
//
// 编译: g++ -std=c++17 -I../../include delay.cpp -o delay -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 延迟线
class SimpleDelay {
public:
    SimpleDelay(float delay_ms, float feedback, float mix, float sample_rate)
        : feedback_(feedback)
        , mix_(mix)
        , write_pos_(0) {
        delay_samples_ = static_cast<size_t>(delay_ms * sample_rate / 1000.0f);
        buffer_.resize(delay_samples_ + 1, 0.0f);
    }

    float process(float input) {
        float delayed = buffer_[write_pos_];
        float output = input * (1.0f - mix_) + delayed * mix_;

        buffer_[write_pos_] = input + delayed * feedback_;
        write_pos_ = (write_pos_ + 1) % buffer_.size();

        return output;
    }

    void process_buffer(AudioBuffer& buffer) {
        for (auto& sample : buffer.samples) {
            sample = process(sample);
        }
    }

private:
    std::vector<float> buffer_;
    size_t delay_samples_;
    size_t write_pos_;
    float feedback_;
    float mix_;
};

// 演示基本延迟
void demo_basic_delay() {
    print_separator("基本延迟");

    std::cout << "\n延迟效果：复制信号并在稍后播放\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建短脉冲
    std::vector<float> samples(44100, 0.0f);
    for (int i = 0; i < 5; ++i) {
        samples[i * 1000] = 0.8f;
    }

    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    // 应用延迟
    SimpleDelay delay(500.0f, 0.0f, 0.5f, sample_rate);
    delay.process_buffer(buffer);

    std::cout << "参数:" << std::endl;
    std::cout << "  延迟时间: 500 ms" << std::endl;
    std::cout << "  反馈: 0 (无重复)" << std::endl;
    std::cout << "  混合: 0.5" << std::endl;

    write_wav("delay_basic.wav", buffer);
}

// 演示反馈延迟
void demo_feedback_delay() {
    print_separator("反馈延迟");

    std::cout << "\n反馈延迟：延迟信号再次进入延迟线\n" << std::endl;

    float sample_rate = 44100.0f;

    std::vector<float> samples(88200, 0.0f);
    samples[0] = 0.8f;

    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    SimpleDelay delay(300.0f, 0.6f, 0.5f, sample_rate);
    delay.process_buffer(buffer);

    std::cout << "参数:" << std::endl;
    std::cout << "  延迟时间: 300 ms" << std::endl;
    std::cout << "  反馈: 0.6 (逐渐衰减)" << std::endl;
    std::cout << "  混合: 0.5" << std::endl;

    write_wav("delay_feedback.wav", buffer);
}

// 演示不同延迟时间
void demo_delay_times() {
    print_separator("不同延迟时间");

    std::cout << "\n不同延迟时间产生不同效果:\n" << std::endl;

    float sample_rate = 44100.0f;

    struct DelayInfo {
        float time_ms;
        const char* effect;
    };

    std::vector<DelayInfo> delays = {
        {20.0f, "梳状滤波"},
        {80.0f, "拍打回声"},
        {200.0f, "回声"},
        {500.0f, "长回声"}
    };

    for (const auto& info : delays) {
        std::vector<float> samples(88200, 0.0f);
        samples[0] = 0.8f;

        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));
        SimpleDelay delay(info.time_ms, 0.5f, 0.5f, sample_rate);
        delay.process_buffer(buffer);

        std::string filename = "delay_" +
                               std::to_string(static_cast<int>(info.time_ms)) + "ms.wav";
        write_wav(filename, buffer);

        std::cout << info.time_ms << " ms: " << info.effect << std::endl;
    }
}

// 演示延迟应用
void demo_delay_applications() {
    print_separator("延迟应用");

    std::cout << "\n延迟效果的常见应用:\n" << std::endl;

    std::cout << "1. 回声效果" << std::endl;
    std::cout << "   - 延迟: 200-500 ms" << std::endl;
    std::cout << "   - 反馈: 0.3-0.6" << std::endl;
    std::cout << "   - 混合: 0.3-0.5" << std::endl;

    std::cout << "\n2. 拍打回声" << std::endl;
    std::cout << "   - 延迟: 80-150 ms" << std::endl;
    std::cout << "   - 反馈: 0.4-0.7" << std::endl;
    std::cout << "   - 混合: 0.4-0.6" << std::endl;

    std::cout << "\n3. 合唱效果" << std::endl;
    std::cout << "   - 延迟: 20-30 ms" << std::endl;
    std::cout << "   - 反馈: 0.0-0.3" << std::endl;
    std::cout << "   - 混合: 0.5" << std::endl;

    std::cout << "\n4. 梳状滤波" << std::endl;
    std::cout << "   - 延迟: 1-20 ms" << std::endl;
    std::cout << "   - 反馈: 0.5-0.9" << std::endl;
    std::cout << "   - 混合: 0.5" << std::endl;

    // 生成回声效果
    float sample_rate = 44100.0f;
    auto vocal = generate_sine(300.0f, sample_rate, 2.0f, 0.6f);
    AudioBuffer buffer = make_buffer(vocal, static_cast<uint32_t>(sample_rate));

    SimpleDelay delay(350.0f, 0.4f, 0.4f, sample_rate);
    delay.process_buffer(buffer);

    write_wav("delay_echo.wav", buffer);
}

int main() {
    std::cout << "=== Delay Effect Demo (延迟效果演示) ===" << std::endl;

    demo_basic_delay();
    demo_feedback_delay();
    demo_delay_times();
    demo_delay_applications();

    std::cout << "\n=== 延迟效果总结 ===" << std::endl;
    std::cout << "1. 延迟效果复制信号并在稍后播放" << std::endl;
    std::cout << "2. 反馈产生重复的回声" << std::endl;
    std::cout << "3. 延迟时间决定回声间隔" << std::endl;
    std::cout << "4. 反馈量决定回声衰减速度" << std::endl;

    return 0;
}
