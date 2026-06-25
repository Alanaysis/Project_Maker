// noise_reduction.cpp - 降噪效果演示
//
// 本文件演示音频降噪的基本原理：
// 1. 噪声门
// 2. 频谱减法
// 3. 自适应滤波
//
// 编译: g++ -std=c++17 -I../../include noise_reduction.cpp -o noise_reduction -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 噪声门
class NoiseGate {
public:
    NoiseGate(float threshold_db = -40.0f, float attack_ms = 1.0f,
              float release_ms = 100.0f, float sample_rate = 44100.0f)
        : threshold_(db_to_linear(threshold_db))
        , current_gain_(0.0f) {
        attack_coeff_ = 1.0f - std::exp(-1.0f / (attack_ms * sample_rate / 1000.0f));
        release_coeff_ = 1.0f - std::exp(-1.0f / (release_ms * sample_rate / 1000.0f));
    }

    void process(AudioBuffer& buffer) {
        for (auto& sample : buffer.samples) {
            float level = std::abs(sample);
            float target_gain = (level > threshold_) ? 1.0f : 0.0f;

            // 平滑增益变化
            float coeff = (target_gain > current_gain_) ? attack_coeff_ : release_coeff_;
            current_gain_ = current_gain_ + coeff * (target_gain - current_gain_);

            sample *= current_gain_;
        }
    }

private:
    float threshold_;
    float attack_coeff_;
    float release_coeff_;
    float current_gain_;
};

// 简化的频谱减法降噪
class SpectralDenoiser {
public:
    SpectralDenoiser(float noise_factor = 2.0f, float spectral_floor = 0.1f)
        : noise_factor_(noise_factor)
        , spectral_floor_(spectral_floor) {}

    // 估计噪声频谱（从信号开头的静音段）
    void estimate_noise(const AudioBuffer& buffer, float noise_duration = 0.5f) {
        size_t noise_samples = static_cast<size_t>(noise_duration * buffer.sample_rate);
        noise_samples = std::min(noise_samples, buffer.num_samples());

        noise_spectrum_.resize(noise_samples);
        for (size_t i = 0; i < noise_samples; ++i) {
            noise_spectrum_[i] = buffer.samples[i];
        }
    }

    // 应用降噪
    void process(AudioBuffer& buffer) {
        if (noise_spectrum_.empty()) return;

        // 简化的频谱减法（时域实现）
        for (size_t i = 0; i < buffer.samples.size(); ++i) {
            float noise_estimate = noise_spectrum_[i % noise_spectrum_.size()];
            float signal = buffer.samples[i];

            // 计算增益
            float signal_power = signal * signal;
            float noise_power = noise_estimate * noise_estimate * noise_factor_;

            float gain = 1.0f;
            if (signal_power > noise_power) {
                gain = std::sqrt(1.0f - noise_power / signal_power);
            } else {
                gain = spectral_floor_;
            }

            buffer.samples[i] = signal * gain;
        }
    }

private:
    float noise_factor_;
    float spectral_floor_;
    std::vector<float> noise_spectrum_;
};

// 演示噪声门
void demo_noise_gate() {
    print_separator("噪声门");

    std::cout << "\n噪声门：低于阈值的信号被静音\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建带噪声的信号
    std::vector<float> samples;
    auto signal = generate_sine(440.0f, sample_rate, 1.0f, 0.5f);
    auto noise = generate_noise(sample_rate, 1.0f, 0.05f);

    for (size_t i = 0; i < signal.size(); ++i) {
        samples.push_back(signal[i] + noise[i]);
    }

    // 添加静音段（带噪声）
    auto silence_noise = generate_noise(sample_rate, 0.5f, 0.05f);
    samples.insert(samples.end(), silence_noise.begin(), silence_noise.end());

    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    // 应用噪声门
    NoiseGate gate(-40.0f, 1.0f, 100.0f, sample_rate);
    gate.process(buffer);

    std::cout << "参数:" << std::endl;
    std::cout << "  阈值: -40 dB" << std::endl;
    std::cout << "  启动: 1 ms" << std::endl;
    std::cout << "  释放: 100 ms" << std::endl;

    write_wav("noise_gate.wav", buffer);
}

// 演示频谱减法
void demo_spectral_subtraction() {
    print_separator("频谱减法");

    std::cout << "\n频谱减法：从信号中减去估计的噪声\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建带噪声的信号
    auto clean = generate_sine(440.0f, sample_rate, 2.0f, 0.5f);
    auto noise = generate_noise(sample_rate, 2.0f, 0.1f);

    std::vector<float> noisy(clean.size());
    for (size_t i = 0; i < clean.size(); ++i) {
        noisy[i] = clean[i] + noise[i];
    }

    AudioBuffer buffer = make_buffer(noisy, static_cast<uint32_t>(sample_rate));

    // 创建噪声估计（使用纯噪声）
    AudioBuffer noise_estimate = make_buffer(noise, static_cast<uint32_t>(sample_rate));

    SpectralDenoiser denoiser(2.0f, 0.1f);
    denoiser.estimate_noise(noise_estimate, 1.0f);
    denoiser.process(buffer);

    std::cout << "参数:" << std::endl;
    std::cout << "  噪声因子: 2.0" << std::endl;
    std::cout << "  频谱底限: 0.1" << std::endl;

    write_wav("spectral_denoise.wav", buffer);
}

// 演示降噪应用
void demo_noise_reduction_applications() {
    print_separator("降噪应用");

    std::cout << "\n降噪的常见应用:\n" << std::endl;

    std::cout << "1. 语音通话降噪" << std::endl;
    std::cout << "   - 去除背景噪声" << std::endl;
    std::cout << "   - 保留语音清晰度" << std::endl;

    std::cout << "\n2. 音频录制降噪" << std::endl;
    std::cout << "   - 去除录音环境噪声" << std::endl;
    std::cout << "   - 去除设备噪声" << std::endl;

    std::cout << "\n3. 音乐制作" << std::endl;
    std::cout << "   - 去除录音中的嗡嗡声" << std::endl;
    std::cout << "   - 去除接地回路噪声" << std::endl;

    std::cout << "\n4. 广播/播客" << std::endl;
    std::cout << "   - 提高语音清晰度" << std::endl;
    std::cout << "   - 标准化音频质量" << std::endl;
}

int main() {
    std::cout << "=== Noise Reduction Demo (降噪效果演示) ===" << std::endl;

    demo_noise_gate();
    demo_spectral_subtraction();
    demo_noise_reduction_applications();

    std::cout << "\n=== 降噪效果总结 ===" << std::endl;
    std::cout << "1. 噪声门静音低于阈值的信号" << std::endl;
    std::cout << "2. 频谱减法从信号中减去噪声频谱" << std::endl;
    std::cout << "3. 降噪需要在去除噪声和保留信号间平衡" << std::endl;
    std::cout << "4. 实际应用通常结合多种技术" << std::endl;

    return 0;
}
