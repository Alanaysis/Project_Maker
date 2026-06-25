// channels.cpp - 声道处理演示
//
// 本文件演示声道处理的基本原理：
// 1. 单声道与立体声
// 2. 声道转换
// 3. 声像（Pan）调节
// 4. 声道平衡
//
// 编译: g++ -std=c++17 -I../../include channels.cpp -o channels -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 声像调节（Pan）
// pan: -1.0 (左) 到 1.0 (右)，0.0 = 中间
void apply_pan(AudioBuffer& buffer, float pan) {
    if (buffer.channels != 2) return;

    pan = clamp(pan, -1.0f, 1.0f);

    // 等功率声像调节
    float left_gain = std::cos((pan + 1.0f) * M_PI / 4.0f);
    float right_gain = std::sin((pan + 1.0f) * M_PI / 4.0f);

    for (size_t i = 0; i < buffer.num_samples(); ++i) {
        float left = buffer.get_sample(i, 0);
        float right = buffer.get_sample(i, 1);

        buffer.set_sample(i, 0, left * left_gain);
        buffer.set_sample(i, 1, right * right_gain);
    }
}

// 交换声道
void swap_channels(AudioBuffer& buffer) {
    if (buffer.channels != 2) return;

    for (size_t i = 0; i < buffer.num_samples(); ++i) {
        float left = buffer.get_sample(i, 0);
        float right = buffer.get_sample(i, 1);

        buffer.set_sample(i, 0, right);
        buffer.set_sample(i, 1, left);
    }
}

// 提取单个声道
AudioBuffer extract_channel(const AudioBuffer& buffer, uint16_t channel) {
    AudioBuffer result;
    result.sample_rate = buffer.sample_rate;
    result.channels = 1;
    result.bit_depth = buffer.bit_depth;

    if (channel >= buffer.channels) return result;

    result.resize(buffer.num_samples());
    for (size_t i = 0; i < buffer.num_samples(); ++i) {
        result.samples[i] = buffer.get_sample(i, channel);
    }

    return result;
}

// 演示声道转换
void demo_channel_conversion() {
    print_separator("声道转换");

    std::cout << "\n声道转换：单声道 ↔ 立体声\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;
    float freq = 440.0f;

    // 创建单声道信号
    auto mono_samples = generate_sine(freq, sample_rate, duration);
    AudioBuffer mono = make_buffer(mono_samples, static_cast<uint32_t>(sample_rate), 1);

    std::cout << "原始单声道:" << std::endl;
    print_buffer_info(mono, "  ");

    // 转换为立体声
    AudioBuffer stereo = mono.to_stereo();

    std::cout << "\n转换为立体声:" << std::endl;
    print_buffer_info(stereo, "  ");

    // 保存文件
    write_wav("channel_mono.wav", mono);
    write_wav("channel_stereo.wav", stereo);

    // 转换回单声道
    AudioBuffer mono_again = stereo.to_mono();

    std::cout << "\n转换回单声道:" << std::endl;
    print_buffer_info(mono_again, "  ");
}

// 演示声像调节
void demo_pan() {
    print_separator("声像调节 (Pan)");

    std::cout << "\n声像调节：控制声音在左右声道的位置\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 2.0f;
    float freq = 440.0f;

    // 创建立体声信号（左右声道相同）
    auto samples = generate_sine(freq, sample_rate, duration);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate), 2);

    // 创建不同声像位置的版本
    struct PanDemo {
        float pan;
        const char* position;
        const char* filename;
    };

    std::vector<PanDemo> demos = {
        {-1.0f, "最左", "pan_left.wav"},
        {-0.5f, "偏左", "pan_left_center.wav"},
        {0.0f, "中间", "pan_center.wav"},
        {0.5f, "偏右", "pan_right_center.wav"},
        {1.0f, "最右", "pan_right.wav"}
    };

    for (const auto& demo : demos) {
        AudioBuffer pan_buffer = buffer; // 复制
        apply_pan(pan_buffer, demo.pan);

        float left_rms = 0.0f, right_rms = 0.0f;
        for (size_t i = 0; i < pan_buffer.num_samples(); ++i) {
            float l = pan_buffer.get_sample(i, 0);
            float r = pan_buffer.get_sample(i, 1);
            left_rms += l * l;
            right_rms += r * r;
        }
        left_rms = std::sqrt(left_rms / pan_buffer.num_samples());
        right_rms = std::sqrt(right_rms / pan_buffer.num_samples());

        std::cout << demo.position << " (pan=" << demo.pan << "): "
                  << "L=" << left_rms << ", R=" << right_rms << std::endl;

        write_wav(demo.filename, pan_buffer);
    }
}

// 演示声道交换
void demo_channel_swap() {
    print_separator("声道交换");

    std::cout << "\n声道交换：左右声道互换\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;

    // 创建不同内容的左右声道
    std::vector<float> stereo_samples;
    auto left_samples = generate_sine(440.0f, sample_rate, duration);
    auto right_samples = generate_sine(880.0f, sample_rate, duration);

    for (size_t i = 0; i < left_samples.size(); ++i) {
        stereo_samples.push_back(left_samples[i]);   // 左声道 440 Hz
        stereo_samples.push_back(right_samples[i]);  // 右声道 880 Hz
    }

    AudioBuffer buffer = make_buffer(stereo_samples, static_cast<uint32_t>(sample_rate), 2);

    std::cout << "原始立体声:" << std::endl;
    std::cout << "  左声道: 440 Hz" << std::endl;
    std::cout << "  右声道: 880 Hz" << std::endl;

    // 保存原始
    write_wav("channel_original.wav", buffer);

    // 交换声道
    swap_channels(buffer);

    std::cout << "\n交换后:" << std::endl;
    std::cout << "  左声道: 880 Hz" << std::endl;
    std::cout << "  右声道: 440 Hz" << std::endl;

    // 保存交换后
    write_wav("channel_swapped.wav", buffer);
}

// 演示声道平衡
void demo_channel_balance() {
    print_separator("声道平衡");

    std::cout << "\n声道平衡：调整左右声道的相对音量\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 2.0f;

    // 创建立体声正弦波
    auto samples = generate_sine(440.0f, sample_rate, duration);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate), 2);

    // 调整平衡（左声道 +3dB，右声道 -3dB）
    float left_gain = db_to_linear(3.0f);
    float right_gain = db_to_linear(-3.0f);

    for (size_t i = 0; i < buffer.num_samples(); ++i) {
        float left = buffer.get_sample(i, 0) * left_gain;
        float right = buffer.get_sample(i, 1) * right_gain;
        buffer.set_sample(i, 0, left);
        buffer.set_sample(i, 1, right);
    }

    std::cout << "左声道增益: +3 dB (" << left_gain << ")" << std::endl;
    std::cout << "右声道增益: -3 dB (" << right_gain << ")" << std::endl;

    write_wav("channel_balance.wav", buffer);
}

// 演示提取单声道
void demo_extract_channel() {
    print_separator("提取单声道");

    std::cout << "\n从立体声中提取单个声道\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;

    // 创建不同内容的立体声
    std::vector<float> stereo_samples;
    auto left_samples = generate_sine(440.0f, sample_rate, duration);
    auto right_samples = generate_sine(880.0f, sample_rate, duration);

    for (size_t i = 0; i < left_samples.size(); ++i) {
        stereo_samples.push_back(left_samples[i]);
        stereo_samples.push_back(right_samples[i]);
    }

    AudioBuffer stereo = make_buffer(stereo_samples, static_cast<uint32_t>(sample_rate), 2);

    // 提取左声道
    AudioBuffer left_channel = extract_channel(stereo, 0);
    write_wav("channel_left.wav", left_channel);

    // 提取右声道
    AudioBuffer right_channel = extract_channel(stereo, 1);
    write_wav("channel_right.wav", right_channel);

    std::cout << "左声道已保存: channel_left.wav" << std::endl;
    std::cout << "右声道已保存: channel_right.wav" << std::endl;
}

int main() {
    std::cout << "=== Channel Processing Demo (声道处理演示) ===" << std::endl;

    demo_channel_conversion();
    demo_pan();
    demo_channel_swap();
    demo_channel_balance();
    demo_extract_channel();

    std::cout << "\n=== 声道处理总结 ===" << std::endl;
    std::cout << "1. 单声道转立体声：复制到两个声道" << std::endl;
    std::cout << "2. 立体声转单声道：取两个声道的平均" << std::endl;
    std::cout << "3. 声像调节：使用等功率定律" << std::endl;
    std::cout << "4. 声道交换：左右互换" << std::endl;
    std::cout << "5. 声道平衡：独立调整各声道增益" << std::endl;

    return 0;
}
