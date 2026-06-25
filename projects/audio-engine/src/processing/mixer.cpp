// mixer.cpp - 混音器演示
//
// 本文件演示音频混音的基本原理：
// 1. 多轨音频混合
// 2. 声像（Pan）调节
// 3. 音量自动化
//
// 编译: g++ -std=c++17 -I../../include mixer.cpp -o mixer -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 混音器类
class Mixer {
public:
    struct Track {
        AudioBuffer buffer;
        float volume = 1.0f;
        float pan = 0.0f;     // -1.0 (左) 到 1.0 (右)
        bool muted = false;
    };

    void add_track(const AudioBuffer& buffer, float volume = 1.0f, float pan = 0.0f) {
        Track track;
        track.buffer = buffer;
        track.volume = volume;
        track.pan = pan;
        tracks_.push_back(track);
    }

    // 混合所有声道
    AudioBuffer mix(uint32_t output_sample_rate = 44100, uint16_t output_channels = 2) {
        // 找到最长的轨道
        size_t max_samples = 0;
        for (const auto& track : tracks_) {
            max_samples = std::max(max_samples, track.buffer.num_samples());
        }

        AudioBuffer output;
        output.sample_rate = output_sample_rate;
        output.channels = output_channels;
        output.resize(max_samples);

        // 混合
        for (const auto& track : tracks_) {
            if (track.muted) continue;

            float left_gain = std::cos((track.pan + 1.0f) * M_PI / 4.0f) * track.volume;
            float right_gain = std::sin((track.pan + 1.0f) * M_PI / 4.0f) * track.volume;

            for (size_t i = 0; i < track.buffer.num_samples(); ++i) {
                float sample = track.buffer.get_sample(i, 0);

                if (output_channels == 2) {
                    float left = output.get_sample(i, 0) + sample * left_gain;
                    float right = output.get_sample(i, 1) + sample * right_gain;
                    output.set_sample(i, 0, clamp(left, -1.0f, 1.0f));
                    output.set_sample(i, 1, clamp(right, -1.0f, 1.0f));
                } else {
                    float mono = output.get_sample(i, 0) + sample * track.volume;
                    output.set_sample(i, 0, clamp(mono, -1.0f, 1.0f));
                }
            }
        }

        return output;
    }

    size_t num_tracks() const { return tracks_.size(); }

private:
    std::vector<Track> tracks_;
};

// 演示基本混音
void demo_basic_mixing() {
    print_separator("基本混音");

    std::cout << "\n将多个音频轨道混合在一起\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 2.0f;

    // 创建不同频率的轨道
    auto track1 = generate_sine(261.63f, sample_rate, duration);    // C4
    auto track2 = generate_sine(329.63f, sample_rate, duration);    // E4
    auto track3 = generate_sine(392.00f, sample_rate, duration);    // G4

    Mixer mixer;
    mixer.add_track(make_buffer(track1, static_cast<uint32_t>(sample_rate)), 0.8f, -0.3f);
    mixer.add_track(make_buffer(track2, static_cast<uint32_t>(sample_rate)), 0.6f, 0.0f);
    mixer.add_track(make_buffer(track3, static_cast<uint32_t>(sample_rate)), 0.5f, 0.3f);

    AudioBuffer mixed = mixer.mix(static_cast<uint32_t>(sample_rate));

    std::cout << "轨道 1: C4 (261.63 Hz) - 音量 0.8, 声像 -0.3" << std::endl;
    std::cout << "轨道 2: E4 (329.63 Hz) - 音量 0.6, 声像 0.0" << std::endl;
    std::cout << "轨道 3: G4 (392.00 Hz) - 音量 0.5, 声像 0.3" << std::endl;

    std::cout << "\n混合结果:" << std::endl;
    std::cout << "  峰值: " << mixed.peak() << std::endl;
    std::cout << "  RMS: " << mixed.rms() << std::endl;

    write_wav("mix_chord.wav", mixed);
}

// 演示声像调节
void demo_pan_mixing() {
    print_separator("声像调节混音");

    std::cout << "\n使用声像调节将不同轨道放在不同位置\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 2.0f;

    auto bass = generate_sine(110.0f, sample_rate, duration, 0.8f);
    auto mid = generate_sine(440.0f, sample_rate, duration, 0.6f);
    auto high = generate_sine(1760.0f, sample_rate, duration, 0.4f);

    Mixer mixer;
    mixer.add_track(make_buffer(bass, static_cast<uint32_t>(sample_rate)), 1.0f, -0.5f);
    mixer.add_track(make_buffer(mid, static_cast<uint32_t>(sample_rate)), 1.0f, 0.0f);
    mixer.add_track(make_buffer(high, static_cast<uint32_t>(sample_rate)), 1.0f, 0.5f);

    AudioBuffer mixed = mixer.mix(static_cast<uint32_t>(sample_rate));

    std::cout << "低频 (110 Hz): 声像 -0.5 (偏左)" << std::endl;
    std::cout << "中频 (440 Hz): 声像 0.0 (中间)" << std::endl;
    std::cout << "高频 (1760 Hz): 声像 0.5 (偏右)" << std::endl;

    write_wav("mix_pan.wav", mixed);
}

// 演示音量平衡
void demo_volume_balance() {
    print_separator("音量平衡");

    std::cout << "\n调整各轨道音量以达到平衡\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 2.0f;

    auto vocal = generate_sine(440.0f, sample_rate, duration, 0.9f);
    auto drums = generate_sine(100.0f, sample_rate, duration, 0.7f);
    auto bass = generate_sine(55.0f, sample_rate, duration, 0.8f);

    Mixer mixer;

    // 不平衡的混音
    mixer.add_track(make_buffer(vocal, static_cast<uint32_t>(sample_rate)), 1.0f, 0.0f);
    mixer.add_track(make_buffer(drums, static_cast<uint32_t>(sample_rate)), 1.0f, 0.0f);
    mixer.add_track(make_buffer(bass, static_cast<uint32_t>(sample_rate)), 1.0f, 0.0f);

    AudioBuffer unbalanced = mixer.mix(static_cast<uint32_t>(sample_rate));
    write_wav("mix_unbalanced.wav", unbalanced);

    std::cout << "不平衡混音:" << std::endl;
    std::cout << "  峰值: " << unbalanced.peak() << " (可能削波)" << std::endl;

    // 平衡的混音
    Mixer balanced_mixer;
    balanced_mixer.add_track(make_buffer(vocal, static_cast<uint32_t>(sample_rate)), 0.6f, 0.0f);
    balanced_mixer.add_track(make_buffer(drums, static_cast<uint32_t>(sample_rate)), 0.4f, -0.2f);
    balanced_mixer.add_track(make_buffer(bass, static_cast<uint32_t>(sample_rate)), 0.5f, 0.2f);

    AudioBuffer balanced = balanced_mixer.mix(static_cast<uint32_t>(sample_rate));
    write_wav("mix_balanced.wav", balanced);

    std::cout << "\n平衡混音:" << std::endl;
    std::cout << "  峰值: " << balanced.peak() << std::endl;
}

// 演示静音和独奏
void demo_mute_solo() {
    print_separator("静音和独奏");

    std::cout << "\n静音和独奏功能:\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 2.0f;

    auto track1 = generate_sine(261.63f, sample_rate, duration);  // C4
    auto track2 = generate_sine(329.63f, sample_rate, duration);  // E4
    auto track3 = generate_sine(392.00f, sample_rate, duration);  // G4

    Mixer mixer;
    mixer.add_track(make_buffer(track1, static_cast<uint32_t>(sample_rate)), 0.7f, -0.3f);
    mixer.add_track(make_buffer(track2, static_cast<uint32_t>(sample_rate)), 0.6f, 0.0f);
    mixer.add_track(make_buffer(track3, static_cast<uint32_t>(sample_rate)), 0.5f, 0.3f);

    // 全部混合
    AudioBuffer all = mixer.mix(static_cast<uint32_t>(sample_rate));
    write_wav("mix_all.wav", all);
    std::cout << "全部轨道混合: mix_all.wav" << std::endl;

    // 模拟静音轨道 2
    Mixer mute_mixer;
    mute_mixer.add_track(make_buffer(track1, static_cast<uint32_t>(sample_rate)), 0.7f, -0.3f);
    mute_mixer.add_track(make_buffer(track2, static_cast<uint32_t>(sample_rate)), 0.0f, 0.0f); // 静音
    mute_mixer.add_track(make_buffer(track3, static_cast<uint32_t>(sample_rate)), 0.5f, 0.3f);

    AudioBuffer muted = mute_mixer.mix(static_cast<uint32_t>(sample_rate));
    write_wav("mix_muted.wav", muted);
    std::cout << "轨道 2 静音: mix_muted.wav" << std::endl;

    // 模拟独奏轨道 1
    Mixer solo_mixer;
    solo_mixer.add_track(make_buffer(track1, static_cast<uint32_t>(sample_rate)), 0.7f, -0.3f);
    solo_mixer.add_track(make_buffer(track2, static_cast<uint32_t>(sample_rate)), 0.0f, 0.0f); // 静音
    solo_mixer.add_track(make_buffer(track3, static_cast<uint32_t>(sample_rate)), 0.0f, 0.3f); // 静音

    AudioBuffer solo = solo_mixer.mix(static_cast<uint32_t>(sample_rate));
    write_wav("mix_solo.wav", solo);
    std::cout << "轨道 1 独奏: mix_solo.wav" << std::endl;
}

// 演示实际混音场景
void demo_practical_mixing() {
    print_separator("实际混音场景");

    std::cout << "\n模拟一个简单的乐队混音:\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 3.0f;

    // 模拟不同乐器
    auto bass_guitar = generate_sine(82.41f, sample_rate, duration, 0.7f);   // E2
    auto guitar = generate_sine(329.63f, sample_rate, duration, 0.5f);       // E4
    auto synth = generate_sine(440.0f, sample_rate, duration, 0.4f);         // A4
    auto hihat = generate_noise(sample_rate, duration, 0.2f);                // 噪声模拟

    Mixer mixer;
    mixer.add_track(make_buffer(bass_guitar, static_cast<uint32_t>(sample_rate)), 0.7f, 0.0f);
    mixer.add_track(make_buffer(guitar, static_cast<uint32_t>(sample_rate)), 0.5f, -0.4f);
    mixer.add_track(make_buffer(synth, static_cast<uint32_t>(sample_rate)), 0.4f, 0.3f);
    mixer.add_track(make_buffer(hihat, static_cast<uint32_t>(sample_rate)), 0.2f, 0.5f);

    AudioBuffer mix = mixer.mix(static_cast<uint32_t>(sample_rate));

    std::cout << "乐器配置:" << std::endl;
    std::cout << "  贝斯 (E2): 音量 0.7, 声像 0.0" << std::endl;
    std::cout << "  吉他 (E4): 音量 0.5, 声像 -0.4" << std::endl;
    std::cout << "  合成器 (A4): 音量 0.4, 声像 0.3" << std::endl;
    std::cout << "  嗦音: 音量 0.2, 声像 0.5" << std::endl;

    std::cout << "\n混音结果:" << std::endl;
    std::cout << "  峰值: " << mix.peak() << std::endl;
    std::cout << "  RMS: " << mix.rms() << std::endl;

    write_wav("mix_band.wav", mix);
}

int main() {
    std::cout << "=== Mixer Demo (混音器演示) ===" << std::endl;

    demo_basic_mixing();
    demo_pan_mixing();
    demo_volume_balance();
    demo_mute_solo();
    demo_practical_mixing();

    std::cout << "\n=== 混音器总结 ===" << std::endl;
    std::cout << "1. 混音是将多个音频轨道合并的过程" << std::endl;
    std::cout << "2. 声像调节控制声音在立体声场中的位置" << std::endl;
    std::cout << "3. 音量平衡确保各轨道清晰可闻" << std::endl;
    std::cout << "4. 静音/独奏便于单独调整轨道" << std::endl;

    return 0;
}
