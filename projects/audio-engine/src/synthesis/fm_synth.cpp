// fm_synth.cpp - FM 合成演示
//
// 本文件演示 FM 合成的基本原理：
// 1. 基本 FM 合成
// 2. 调制指数和比率
// 3. FM 算子链
//
// 编译: g++ -std=c++17 -I../../include fm_synth.cpp -o fm_synth -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// FM 合成器
class FMSynthesizer {
public:
    FMSynthesizer(float carrier_freq = 440.0f, float mod_freq = 440.0f,
                  float mod_index = 1.0f, float sample_rate = 44100.0f)
        : carrier_freq_(carrier_freq)
        , mod_freq_(mod_freq)
        , mod_index_(mod_index)
        , sample_rate_(sample_rate)
        , carrier_phase_(0.0f)
        , mod_phase_(0.0f) {}

    void set_carrier_freq(float freq) { carrier_freq_ = freq; }
    void set_mod_freq(float freq) { mod_freq_ = freq; }
    void set_mod_index(float index) { mod_index_ = index; }

    // 设置调制比率（调制频率 = 载波频率 * 比率）
    void set_mod_ratio(float ratio) {
        mod_freq_ = carrier_freq_ * ratio;
    }

    float generate() {
        // 调制器
        float mod_output = std::sin(2.0f * M_PI * mod_phase_) * mod_index_;

        // 载波器（被调制）
        float output = std::sin(2.0f * M_PI * carrier_phase_ + mod_output);

        // 更新相位
        carrier_phase_ += carrier_freq_ / sample_rate_;
        mod_phase_ += mod_freq_ / sample_rate_;

        // 保持相位在 [0, 1) 范围
        if (carrier_phase_ >= 1.0f) carrier_phase_ -= 1.0f;
        if (mod_phase_ >= 1.0f) mod_phase_ -= 1.0f;

        return output;
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
    float carrier_freq_;
    float mod_freq_;
    float mod_index_;
    float sample_rate_;
    float carrier_phase_;
    float mod_phase_;
};

// 演示基本 FM 合成
void demo_basic_fm() {
    print_separator("基本 FM 合成");

    std::cout << "\nFM 合成：用调制器调制载波器的频率\n" << std::endl;

    std::cout << "FM 合成公式:" << std::endl;
    std::cout << "  y(t) = sin(2π * fc * t + I * sin(2π * fm * t))" << std::endl;
    std::cout << "  fc = 载波频率" << std::endl;
    std::cout << "  fm = 调制频率" << std::endl;
    std::cout << "  I = 调制指数" << std::endl;

    float sample_rate = 44100.0f;

    // 基本 FM
    FMSynthesizer fm(440.0f, 440.0f, 1.0f, sample_rate);
    auto samples = fm.generate_buffer(2.0f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::cout << "\n参数:" << std::endl;
    std::cout << "  载波频率: 440 Hz" << std::endl;
    std::cout << "  调制频率: 440 Hz" << std::endl;
    std::cout << "  调制指数: 1.0" << std::endl;

    write_wav("fm_basic.wav", buffer);
}

// 演示调制指数
void demo_modulation_index() {
    print_separator("调制指数");

    std::cout << "\n调制指数控制频谱的丰富程度\n" << std::endl;

    float sample_rate = 44100.0f;
    std::vector<float> indices = {0.5f, 1.0f, 2.0f, 5.0f, 10.0f};

    for (float index : indices) {
        FMSynthesizer fm(440.0f, 440.0f, index, sample_rate);
        auto samples = fm.generate_buffer(1.0f);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        std::string filename = "fm_index_" +
                               std::to_string(static_cast<int>(index * 10)) + ".wav";
        write_wav(filename, buffer);

        std::cout << "调制指数 " << index << ": " << filename << std::endl;
    }

    std::cout << "\n调制指数越大，频谱越丰富" << std::endl;
}

// 演示调制比率
void demo_modulation_ratio() {
    print_separator("调制比率");

    std::cout << "\n调制比率决定谐波结构\n" << std::endl;

    float sample_rate = 44100.0f;
    std::vector<float> ratios = {0.5f, 1.0f, 1.5f, 2.0f, 3.0f};

    for (float ratio : ratios) {
        FMSynthesizer fm(440.0f, 440.0f * ratio, 2.0f, sample_rate);
        auto samples = fm.generate_buffer(1.0f);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        std::string filename = "fm_ratio_" +
                               std::to_string(static_cast<int>(ratio * 10)) + ".wav";
        write_wav(filename, buffer);

        std::cout << "比率 " << ratio << " (调制频率 "
                  << 440.0f * ratio << " Hz): " << filename << std::endl;
    }
}

// 演示经典 FM 音色
void demo_classic_fm_sounds() {
    print_separator("经典 FM 音色");

    std::cout << "\nFM 合成的经典音色:\n" << std::endl;

    float sample_rate = 44100.0f;

    struct FMPatch {
        const char* name;
        float carrier;
        float mod;
        float index;
        const char* description;
    };

    std::vector<FMPatch> patches = {
        {"Bell", 440.0f, 880.0f, 3.0f, "钟声"},
        {"Bass", 110.0f, 110.0f, 1.5f, "低音"},
        {"Brass", 220.0f, 220.0f, 2.0f, "铜管"},
        {"Strings", 330.0f, 660.0f, 0.5f, "弦乐"}
    };

    for (const auto& patch : patches) {
        FMSynthesizer fm(patch.carrier, patch.mod, patch.index, sample_rate);
        auto samples = fm.generate_buffer(2.0f);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        std::string filename = std::string("fm_") + patch.name + ".wav";
        write_wav(filename, buffer);

        std::cout << patch.name << " (" << patch.description << "):" << std::endl;
        std::cout << "  载波: " << patch.carrier << " Hz" << std::endl;
        std::cout << "  调制: " << patch.mod << " Hz" << std::endl;
        std::cout << "  指数: " << patch.index << std::endl;
    }
}

// 演示 FM 合成应用
void demo_fm_applications() {
    print_separator("FM 合成应用");

    std::cout << "\nFM 合成的应用:\n" << std::endl;

    std::cout << "1. 经典合成器" << std::endl;
    std::cout << "   - Yamaha DX7 (1983)" << std::endl;
    std::cout << "   - 6 个算子" << std::endl;
    std::cout << "   - 32 种算法" << std::endl;

    std::cout << "\n2. 游戏音效" << std::endl;
    std::cout << "   - Sega Genesis/Mega Drive" << std::endl;
    std::cout << "   - FM 芯片音源" << std::endl;

    std::cout << "\n3. 电子音乐" << std::endl;
    std::cout << "   - 独特的音色" << std::endl;
    std::cout << "   - 动态变化" << std::endl;

    std::cout << "\n4. 音效设计" << std::endl;
    std::cout << "   - 金属音效" << std::endl;
    std::cout << "   - 铃声/钟声" << std::endl;
}

int main() {
    std::cout << "=== FM Synthesis Demo (FM 合成演示) ===" << std::endl;

    demo_basic_fm();
    demo_modulation_index();
    demo_modulation_ratio();
    demo_classic_fm_sounds();
    demo_fm_applications();

    std::cout << "\n=== FM 合成总结 ===" << std::endl;
    std::cout << "1. FM 合成用调制器调制载波器频率" << std::endl;
    std::cout << "2. 调制指数控制频谱丰富度" << std::endl;
    std::cout << "3. 调制比率决定谐波结构" << std::endl;
    std::cout << "4. 产生丰富的音色，如钟声、贝斯等" << std::endl;

    return 0;
}
