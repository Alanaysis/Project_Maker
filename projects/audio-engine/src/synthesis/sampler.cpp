// sampler.cpp - 采样合成演示
//
// 本文件演示采样合成的基本原理：
// 1. 采样加载
// 2. 采样播放
// 3. 采样变换
//
// 编译: g++ -std=c++17 -I../../include sampler.cpp -o sampler -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 采样播放器
class SamplePlayer {
public:
    SamplePlayer(float sample_rate = 44100.0f)
        : sample_rate_(sample_rate)
        , playhead_(0.0f)
        , speed_(1.0f)
        , playing_(false)
        , loop_(false) {}

    void load(const std::vector<float>& sample) {
        sample_data_ = sample;
        playhead_ = 0.0f;
    }

    void play() {
        playing_ = true;
        playhead_ = 0.0f;
    }

    void stop() {
        playing_ = false;
        playhead_ = 0.0f;
    }

    void set_speed(float speed) { speed_ = speed; }
    void set_loop(bool loop) { loop_ = loop; }

    // 设置音高（以半音为单位）
    void set_pitch(float semitones) {
        speed_ = std::pow(2.0f, semitones / 12.0f);
    }

    float process() {
        if (!playing_ || sample_data_.empty()) return 0.0f;

        // 线性插值
        size_t index = static_cast<size_t>(playhead_);
        float frac = playhead_ - index;

        float sample = 0.0f;
        if (index + 1 < sample_data_.size()) {
            sample = sample_data_[index] * (1.0f - frac) +
                     sample_data_[index + 1] * frac;
        } else if (index < sample_data_.size()) {
            sample = sample_data_[index];
        }

        // 更新播放位置
        playhead_ += speed_;

        // 循环或停止
        if (playhead_ >= sample_data_.size()) {
            if (loop_) {
                playhead_ -= sample_data_.size();
            } else {
                playing_ = false;
            }
        }

        return sample;
    }

    std::vector<float> generate_buffer(float duration) {
        size_t num_samples = static_cast<size_t>(sample_rate_ * duration);
        std::vector<float> samples(num_samples);
        for (size_t i = 0; i < num_samples; ++i) {
            samples[i] = process();
        }
        return samples;
    }

    bool is_playing() const { return playing_; }

private:
    std::vector<float> sample_data_;
    float sample_rate_;
    float playhead_;
    float speed_;
    bool playing_;
    bool loop_;
};

// 演示基本采样播放
void demo_basic_sampling() {
    print_separator("基本采样播放");

    std::cout << "\n采样合成：播放录制的音频样本\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建一个"采样"（合成的钢琴音色）
    size_t sample_length = static_cast<size_t>(sample_rate * 0.5f);
    std::vector<float> piano_sample(sample_length);

    for (size_t i = 0; i < sample_length; ++i) {
        float t = static_cast<float>(i) / sample_rate;
        // 简单的钢琴模拟：多个谐波 + 衰减
        float envelope = std::exp(-t * 3.0f);
        piano_sample[i] = envelope * (
            0.5f * std::sin(2.0f * M_PI * 261.63f * t) +  // C4
            0.3f * std::sin(2.0f * M_PI * 523.25f * t) +  // C5
            0.15f * std::sin(2.0f * M_PI * 784.88f * t)   // G5
        );
    }

    SamplePlayer player(sample_rate);
    player.load(piano_sample);
    player.play();

    auto samples = player.generate_buffer(2.0f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::cout << "采样长度: " << sample_length << " 采样点" << std::endl;
    std::cout << "播放时长: 2.0 秒" << std::endl;

    write_wav("sampler_basic.wav", buffer);
}

// 演示音高变换
void demo_pitch_shifting() {
    print_separator("音高变换");

    std::cout << "\n通过改变播放速度改变音高\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建采样
    auto sample = generate_sine(440.0f, sample_rate, 0.5f);

    SamplePlayer player(sample_rate);
    player.load(sample);

    // 不同音高
    std::vector<float> semitones = {-12.0f, -7.0f, 0.0f, 7.0f, 12.0f};

    for (float st : semitones) {
        player.play();
        player.set_pitch(st);
        auto samples = player.generate_buffer(1.0f);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        std::string filename = "sampler_pitch_" +
                               std::to_string(static_cast<int>(st)) + "st.wav";
        write_wav(filename, buffer);

        float freq = 440.0f * std::pow(2.0f, st / 12.0f);
        std::cout << st << " 半音 (" << freq << " Hz): " << filename << std::endl;
    }
}

// 演示循环播放
void demo_looping() {
    print_separator("循环播放");

    std::cout << "\n循环播放：重复播放采样\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建短采样
    auto sample = generate_sine(440.0f, sample_rate, 0.2f);

    SamplePlayer player(sample_rate);
    player.load(sample);
    player.set_loop(true);
    player.play();

    auto samples = player.generate_buffer(2.0f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::cout << "采样长度: 0.2 秒" << std::endl;
    std::cout << "循环播放: 2.0 秒" << std::endl;

    write_wav("sampler_loop.wav", buffer);
}

// 演示采样合成应用
void demo_sampler_applications() {
    print_separator("采样合成应用");

    std::cout << "\n采样合成的应用:\n" << std::endl;

    std::cout << "1. 钢琴采样" << std::endl;
    std::cout << "   - 录制每个音符" << std::endl;
    std::cout << "   - 多力度层" << std::endl;
    std::cout << "   - 真实的钢琴音色" << std::endl;

    std::cout << "\n2. 鼓机" << std::endl;
    std::cout << "   - 录制鼓声" << std::endl;
    std::cout << "   - 触发播放" << std::endl;
    std::cout << "   - 节奏编程" << std::endl;

    std::cout << "\n3. 乐器采样" << std::endl;
    std::cout << "   - 管弦乐采样库" << std::endl;
    std::cout << "   - 虚拟乐器" << std::endl;

    std::cout << "\n4. 音效设计" << std::endl;
    std::cout << "   - 环境音" << std::endl;
    std::cout << "   - 特效音" << std::endl;

    // 生成鼓机示例
    float sample_rate = 44100.0f;

    // 创建不同"鼓声"
    auto kick = generate_sine(60.0f, sample_rate, 0.1f, 0.9f);
    auto snare = generate_noise(sample_rate, 0.05f, 0.7f);
    auto hihat = generate_noise(sample_rate, 0.02f, 0.3f);

    // 简单的节奏模式
    std::vector<float> drum_pattern;
    float bpm = 120.0f;
    float beat_duration = 60.0f / bpm;

    for (int beat = 0; beat < 8; ++beat) {
        size_t beat_samples = static_cast<size_t>(beat_duration * sample_rate);

        // Kick on beats 1, 5
        if (beat == 0 || beat == 4) {
            drum_pattern.insert(drum_pattern.end(), kick.begin(), kick.end());
            drum_pattern.resize((beat + 1) * beat_samples, 0.0f);
        }
        // Snare on beats 3, 7
        else if (beat == 2 || beat == 6) {
            drum_pattern.insert(drum_pattern.end(), snare.begin(), snare.end());
            drum_pattern.resize((beat + 1) * beat_samples, 0.0f);
        }
        // Hihat on all beats
        else {
            drum_pattern.insert(drum_pattern.end(), hihat.begin(), hihat.end());
            drum_pattern.resize((beat + 1) * beat_samples, 0.0f);
        }
    }

    AudioBuffer buffer = make_buffer(drum_pattern, static_cast<uint32_t>(sample_rate));
    write_wav("sampler_drums.wav", buffer);
    std::cout << "\n鼓机示例: sampler_drums.wav" << std::endl;
}

int main() {
    std::cout << "=== Sampler Synthesis Demo (采样合成演示) ===" << std::endl;

    demo_basic_sampling();
    demo_pitch_shifting();
    demo_looping();
    demo_sampler_applications();

    std::cout << "\n=== 采样合成总结 ===" << std::endl;
    std::cout << "1. 采样合成播放录制的音频样本" << std::endl;
    std::cout << "2. 改变播放速度改变音高" << std::endl;
    std::cout << "3. 循环播放延长音符" << std::endl;
    std::cout << "4. 广泛用于钢琴、鼓机、管弦乐" << std::endl;

    return 0;
}
