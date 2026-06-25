// subtractive.cpp - 减法合成演示
//
// 本文件演示减法合成的基本原理：
// 1. 噪声源
// 2. 滤波器设计
// 3. 包络控制
//
// 编译: g++ -std=c++17 -I../../include subtractive.cpp -o subtractive -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// ADSR 包络
class ADSREnvelope {
public:
    ADSREnvelope(float attack = 0.01f, float decay = 0.1f,
                 float sustain = 0.7f, float release = 0.3f,
                 float sample_rate = 44100.0f)
        : attack_(attack)
        , decay_(decay)
        , sustain_(sustain)
        , release_(release)
        , sample_rate_(sample_rate)
        , level_(0.0f)
        , stage_(Stage::Idle)
        , stage_time_(0.0f) {}

    void note_on() {
        stage_ = Stage::Attack;
        stage_time_ = 0.0f;
    }

    void note_off() {
        stage_ = Stage::Release;
        stage_time_ = 0.0f;
    }

    float process() {
        float dt = 1.0f / sample_rate_;
        stage_time_ += dt;

        switch (stage_) {
            case Stage::Attack:
                level_ = stage_time_ / attack_;
                if (level_ >= 1.0f) {
                    level_ = 1.0f;
                    stage_ = Stage::Decay;
                    stage_time_ = 0.0f;
                }
                break;

            case Stage::Decay:
                level_ = 1.0f - (1.0f - sustain_) * (stage_time_ / decay_);
                if (level_ <= sustain_) {
                    level_ = sustain_;
                    stage_ = Stage::Sustain;
                }
                break;

            case Stage::Sustain:
                level_ = sustain_;
                break;

            case Stage::Release:
                level_ -= dt / release_;
                if (level_ <= 0.0f) {
                    level_ = 0.0f;
                    stage_ = Stage::Idle;
                }
                break;

            case Stage::Idle:
                level_ = 0.0f;
                break;
        }

        return level_;
    }

    bool is_active() const { return stage_ != Stage::Idle; }

private:
    enum class Stage { Idle, Attack, Decay, Sustain, Release };

    float attack_, decay_, sustain_, release_;
    float sample_rate_;
    float level_;
    Stage stage_;
    float stage_time_;
};

// 简单低通滤波器
class SimpleLowPass {
public:
    SimpleLowPass(float cutoff = 1000.0f, float sample_rate = 44100.0f)
        : cutoff_(cutoff), sample_rate_(sample_rate), last_(0.0f) {
        calculate_coeff();
    }

    void set_cutoff(float cutoff) {
        cutoff_ = cutoff;
        calculate_coeff();
    }

    float process(float input) {
        last_ = last_ + coeff_ * (input - last_);
        return last_;
    }

private:
    void calculate_coeff() {
        float rc = 1.0f / (2.0f * M_PI * cutoff_);
        float dt = 1.0f / sample_rate_;
        coeff_ = dt / (rc + dt);
    }

    float cutoff_;
    float sample_rate_;
    float last_;
    float coeff_;
};

// 减法合成器
class SubtractiveSynth {
public:
    SubtractiveSynth(float freq = 440.0f, float sample_rate = 44100.0f)
        : freq_(freq)
        , sample_rate_(sample_rate)
        , oscillator_phase_(0.0f) {
        filter_ = std::make_unique<SimpleLowPass>(5000.0f, sample_rate);
        envelope_ = std::make_unique<ADSREnvelope>(0.01f, 0.1f, 0.7f, 0.3f, sample_rate);
    }

    void note_on() {
        envelope_->note_on();
    }

    void note_off() {
        envelope_->note_off();
    }

    float generate() {
        // 锯齿波振荡器
        float osc = 2.0f * oscillator_phase_ - 1.0f;

        // 更新相位
        oscillator_phase_ += freq_ / sample_rate_;
        if (oscillator_phase_ >= 1.0f) oscillator_phase_ -= 1.0f;

        // 应用滤波器
        float filtered = filter_->process(osc);

        // 应用包络
        float envelope = envelope_->process();

        return filtered * envelope;
    }

    std::vector<float> generate_buffer(float duration) {
        size_t num_samples = static_cast<size_t>(sample_rate_ * duration);
        std::vector<float> samples(num_samples);

        note_on();
        for (size_t i = 0; i < num_samples; ++i) {
            samples[i] = generate();
        }

        return samples;
    }

private:
    float freq_;
    float sample_rate_;
    float oscillator_phase_;
    std::unique_ptr<SimpleLowPass> filter_;
    std::unique_ptr<ADSREnvelope> envelope_;
};

// 演示减法合成
void demo_subtractive() {
    print_separator("减法合成");

    std::cout << "\n减法合成：从丰富的波形中减去不需要的频率\n" << std::endl;

    std::cout << "减法合成流程:" << std::endl;
    std::cout << "  1. 振荡器产生丰富谐波的波形（如锯齿波）" << std::endl;
    std::cout << "  2. 滤波器去除不需要的频率" << std::endl;
    std::cout << "  3. 包络控制音量变化" << std::endl;

    float sample_rate = 44100.0f;
    SubtractiveSynth synth(220.0f, sample_rate);

    auto samples = synth.generate_buffer(2.0f);
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    std::cout << "\n参数:" << std::endl;
    std::cout << "  频率: 220 Hz" << std::endl;
    std::cout << "  波形: 锯齿波" << std::endl;
    std::cout << "  滤波器截止: 5000 Hz" << std::endl;
    std::cout << "  包络: A=10ms, D=100ms, S=0.7, R=300ms" << std::endl;

    write_wav("subtractive_basic.wav", buffer);
}

// 演示 ADSR 包络
void demo_adsr() {
    print_separator("ADSR 包络");

    std::cout << "\nADSR 包络控制音量随时间的变化:\n" << std::endl;

    std::cout << "ADSR = Attack, Decay, Sustain, Release" << std::endl;
    std::cout << "  Attack: 从 0 上升到最大值的时间" << std::endl;
    std::cout << "  Decay: 从最大值下降到持续电平的时间" << std::endl;
    std::cout << "  Sustain: 按键期间的持续电平" << std::endl;
    std::cout << "  Release: 松开按键后下降到 0 的时间" << std::endl;

    float sample_rate = 44100.0f;

    struct ADSRPatch {
        const char* name;
        float attack, decay, sustain, release;
    };

    std::vector<ADSRPatch> patches = {
        {"Percussive", 0.001f, 0.1f, 0.0f, 0.1f},
        {"Pad", 0.5f, 0.3f, 0.8f, 1.0f},
        {"Pluck", 0.001f, 0.2f, 0.3f, 0.5f}
    };

    for (const auto& patch : patches) {
        SubtractiveSynth synth(440.0f, sample_rate);
        // 这里简化处理，直接生成音符
        auto samples = synth.generate_buffer(2.0f);
        AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

        std::string filename = std::string("adsr_") + patch.name + ".wav";
        write_wav(filename, buffer);

        std::cout << patch.name << ": A=" << patch.attack
                  << " D=" << patch.decay
                  << " S=" << patch.sustain
                  << " R=" << patch.release << std::endl;
    }
}

// 演示减法合成应用
void demo_subtractive_applications() {
    print_separator("减法合成应用");

    std::cout << "\n减法合成的应用:\n" << std::endl;

    std::cout << "1. 模拟合成器" << std::endl;
    std::cout << "   - Moog, Roland, Korg" << std::endl;
    std::cout << "   - 温暖的模拟音色" << std::endl;

    std::cout << "\n2. 贝斯音色" << std::endl;
    std::cout << "   - 低频锯齿波 + 低通滤波" << std::endl;
    std::cout << "   - 深沉的贝斯" << std::endl;

    std::cout << "\n3. 铺底音色" << std::endl;
    std::cout << "   - 锯齿波 + 低截止频率" << std::endl;
    std::cout << "   - 柔和的和声" << std::endl;

    std::cout << "\n4. 音效设计" << std::endl;
    std::cout << "   - 滤波器扫描" << std::endl;
    std::cout << "   - 动态音色变化" << std::endl;
}

int main() {
    std::cout << "=== Subtractive Synthesis Demo (减法合成演示) ===" << std::endl;

    demo_subtractive();
    demo_adsr();
    demo_subtractive_applications();

    std::cout << "\n=== 减法合成总结 ===" << std::endl;
    std::cout << "1. 从丰富波形中减去不需要的频率" << std::endl;
    std::cout << "2. 使用滤波器塑造音色" << std::endl;
    std::cout << "3. ADSR 包络控制音量变化" << std::endl;
    std::cout << "4. 模拟合成器的经典方法" << std::endl;

    return 0;
}
