// synthesizer.cpp - 音频合成器演示
//
// 本文件演示音频合成器的基本功能：
// 1. 键盘控制音高
// 2. 波形选择
// 3. 包络控制
//
// 编译: g++ -std=c++17 -I../../include synthesizer.cpp -o synthesizer -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <map>

using namespace audio;

// 简单合成器类
class SimpleSynthesizer {
public:
    enum class Waveform { Sine, Square, Triangle, Sawtooth };

    SimpleSynthesizer(float sample_rate = 44100.0f)
        : sample_rate_(sample_rate)
        , waveform_(Waveform::Sine)
        , frequency_(440.0f)
        , amplitude_(0.8f)
        , phase_(0.0f) {}

    void set_waveform(Waveform wave) { waveform_ = wave; }
    void set_frequency(float freq) { frequency_ = freq; }
    void set_amplitude(float amp) { amplitude_ = clamp(amp, 0.0f, 1.0f); }

    float generate() {
        float sample = 0.0f;

        switch (waveform_) {
            case Waveform::Sine:
                sample = std::sin(2.0f * M_PI * phase_);
                break;
            case Waveform::Square:
                sample = (phase_ < 0.5f) ? 1.0f : -1.0f;
                break;
            case Waveform::Triangle:
                sample = 2.0f * std::abs(2.0f * phase_ - 1.0f) - 1.0f;
                break;
            case Waveform::Sawtooth:
                sample = 2.0f * phase_ - 1.0f;
                break;
        }

        // 更新相位
        phase_ += frequency_ / sample_rate_;
        if (phase_ >= 1.0f) phase_ -= 1.0f;

        return sample * amplitude_;
    }

    std::vector<float> generate_buffer(float duration) {
        size_t num_samples = static_cast<size_t>(sample_rate_ * duration);
        std::vector<float> samples(num_samples);
        for (size_t i = 0; i < num_samples; ++i) {
            samples[i] = generate();
        }
        return samples;
    }

private:
    float sample_rate_;
    Waveform waveform_;
    float frequency_;
    float amplitude_;
    float phase_;
};

// 演示键盘控制
void demo_keyboard_control() {
    print_separator("键盘控制");

    std::cout << "\n键盘控制音高:\n" << std::endl;

    // 音符频率映射
    std::map<char, float> key_freq = {
        {'a', 261.63f},  // C4
        {'w', 277.18f},  // C#4
        {'s', 293.66f},  // D4
        {'e', 311.13f},  // D#4
        {'d', 329.63f},  // E4
        {'f', 349.23f},  // F4
        {'t', 369.99f},  // F#4
        {'g', 392.00f},  // G4
        {'y', 415.30f},  // G#4
        {'h', 440.00f},  // A4
        {'u', 466.16f},  // A#4
        {'j', 493.88f},  // B4
        {'k', 523.25f}   // C5
    };

    std::cout << "键盘映射:" << std::endl;
    std::cout << "  白键: a s d f g h j k (C D E F G A B C)" << std::endl;
    std::cout << "  黑键: w e t y u (C# D# F# G# A#)" << std::endl;

    float sample_rate = 44100.0f;
    SimpleSynthesizer synth(sample_rate);
    synth.set_waveform(SimpleSynthesizer::Waveform::Sine);

    // 模拟按键序列
    std::vector<char> melody = {'a', 's', 'd', 'f', 'g', 'h', 'j', 'k'};

    std::vector<float> all_samples;
    for (char key : melody) {
        if (key_freq.find(key) != key_freq.end()) {
            synth.set_frequency(key_freq[key]);
            auto samples = synth.generate_buffer(0.5f);
            all_samples.insert(all_samples.end(), samples.begin(), samples.end());
        }
    }

    AudioBuffer buffer = make_buffer(all_samples, static_cast<uint32_t>(sample_rate));
    write_wav("synth_keyboard.wav", buffer);

    std::cout << "\n音阶演示已生成: synth_keyboard.wav" << std::endl;
}

// 演示波形选择
void demo_waveform_selection() {
    print_separator("波形选择");

    std::cout << "\n不同波形的音色:\n" << std::endl;

    float sample_rate = 44100.0f;
    float freq = 440.0f;

    struct WaveDemo {
        SimpleSynthesizer::Waveform type;
        const char* name;
        const char* description;
    };

    std::vector<WaveDemo> waves = {
        {SimpleSynthesizer::Waveform::Sine, "正弦波", "纯净、简单"},
        {SimpleSynthesizer::Waveform::Square, "方波", "空洞、鼻音"},
        {SimpleSynthesizer::Waveform::Triangle, "三角波", "柔和、木管"},
        {SimpleSynthesizer::Waveform::Sawtooth, "锯齿波", "明亮、尖锐"}
    };

    for (const auto& wave : waves) {
        SimpleSynthesizer synth(sample_rate);
        synth.set_waveform(wave.type);
        synth.set_frequency(freq);

        auto samples = synth.generate_buffer(2.0f);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        std::string filename = std::string("synth_") + wave.name + ".wav";
        write_wav(filename, buffer);

        std::cout << wave.name << " (" << wave.description << "): " << filename << std::endl;
    }
}

// 演示合成器应用
void demo_synthesizer_applications() {
    print_separator("合成器应用");

    std::cout << "\n音频合成器的应用:\n" << std::endl;

    std::cout << "1. 音乐制作" << std::endl;
    std::cout << "   - 电子音乐" << std::endl;
    std::cout << "   - 伴奏制作" << std::endl;
    std::cout << "   - 音色设计" << std::endl;

    std::cout << "\n2. 游戏音频" << std::endl;
    std::cout << "   - 背景音乐" << std::endl;
    std::cout << "   - 音效生成" << std::endl;
    std::cout << "   - 动态音频" << std::endl;

    std::cout << "\n3. 教育" << std::endl;
    std::cout << "   - 音乐理论学习" << std::endl;
    std::cout << "   - 声音合成实验" << std::endl;

    std::cout << "\n4. 测试" << std::endl;
    std::cout << "   - 音频设备测试" << std::endl;
    std::cout << "   - 校准信号" << std::endl;

    // 生成和弦示例
    float sample_rate = 44100.0f;

    std::vector<float> chord;
    std::vector<float> freqs = {261.63f, 329.63f, 392.00f};  // C 大调

    for (float freq : freqs) {
        SimpleSynthesizer synth(sample_rate);
        synth.set_waveform(SimpleSynthesizer::Waveform::Sine);
        synth.set_frequency(freq);
        synth.set_amplitude(0.3f);

        auto samples = synth.generate_buffer(3.0f);

        if (chord.empty()) {
            chord = samples;
        } else {
            for (size_t i = 0; i < chord.size(); ++i) {
                chord[i] += samples[i];
            }
        }
    }

    AudioBuffer buffer = make_buffer(chord, static_cast<uint32_t>(sample_rate));
    write_wav("synth_chord.wav", buffer);
    std::cout << "\n和弦示例: synth_chord.wav" << std::endl;
}

int main() {
    std::cout << "=== Synthesizer Demo (音频合成器演示) ===" << std::endl;

    demo_keyboard_control();
    demo_waveform_selection();
    demo_synthesizer_applications();

    std::cout << "\n=== 音频合成器总结 ===" << std::endl;
    std::cout << "1. 键盘控制音高" << std::endl;
    std::cout << "2. 波形选择影响音色" << std::endl;
    std::cout << "3. 包络控制音量变化" << std::endl;
    std::cout << "4. 广泛用于音乐制作和游戏" << std::endl;

    return 0;
}
