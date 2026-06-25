// spectrum.cpp - 频谱分析演示
//
// 本文件演示频谱分析的基本原理：
// 1. 功率谱密度
// 2. 频谱图（Spectrogram）
// 3. 频谱可视化
//
// 编译: g++ -std=c++17 -I../../include spectrum.cpp -o spectrum -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <complex>

using namespace audio;

// 简化的 FFT
std::vector<std::complex<double>> simple_fft(const std::vector<double>& input) {
    size_t n = input.size();
    if (n == 1) {
        return {std::complex<double>(input[0], 0.0)};
    }

    std::vector<double> even, odd;
    for (size_t i = 0; i < n; i += 2) {
        even.push_back(input[i]);
        if (i + 1 < n) odd.push_back(input[i + 1]);
    }

    auto fft_even = simple_fft(even);
    auto fft_odd = simple_fft(odd);

    std::vector<std::complex<double>> result(n);
    for (size_t k = 0; k < n / 2; ++k) {
        double angle = -2.0 * M_PI * k / n;
        std::complex<double> twiddle(std::cos(angle), std::sin(angle));
        result[k] = fft_even[k] + twiddle * fft_odd[k];
        result[k + n / 2] = fft_even[k] - twiddle * fft_odd[k];
    }

    return result;
}

// 计算功率谱
std::vector<double> power_spectrum(const std::vector<std::complex<double>>& spectrum) {
    std::vector<double> power(spectrum.size());
    for (size_t i = 0; i < spectrum.size(); ++i) {
        double mag = std::abs(spectrum[i]);
        power[i] = mag * mag / spectrum.size();
    }
    return power;
}

// 计算功率谱密度 (dB)
std::vector<double> power_spectrum_db(const std::vector<double>& power) {
    std::vector<double> psd(power.size());
    for (size_t i = 0; i < power.size(); ++i) {
        psd[i] = 10.0 * std::log10(power[i] + 1e-10);
    }
    return psd;
}

// 文本频谱可视化
void print_spectrum(const std::vector<double>& magnitudes, float sample_rate,
                    size_t max_bins = 50) {
    size_t num_bins = std::min(magnitudes.size(), max_bins);

    // 找到最大值用于归一化
    double max_mag = 0;
    for (size_t i = 0; i < num_bins; ++i) {
        max_mag = std::max(max_mag, magnitudes[i]);
    }

    std::cout << "\n频谱可视化:" << std::endl;
    std::cout << "频率 (Hz)  | 幅度" << std::endl;
    std::cout << "-----------|-----" << std::endl;

    for (size_t i = 0; i < num_bins; ++i) {
        double freq = i * sample_rate / (magnitudes.size() * 2);
        int bar_len = static_cast<int>(40 * magnitudes[i] / max_mag);

        printf("%8.0f   | ", freq);
        for (int j = 0; j < bar_len; ++j) {
            std::cout << "#";
        }
        std::cout << std::endl;
    }
}

// 演示功率谱
void demo_power_spectrum() {
    print_separator("功率谱密度");

    std::cout << "\n功率谱显示信号在各频率的能量分布\n" << std::endl;

    float sample_rate = 44100.0f;
    size_t fft_size = 1024;

    // 创建混合信号
    std::vector<double> signal(fft_size);
    for (size_t i = 0; i < fft_size; ++i) {
        double t = static_cast<double>(i) / sample_rate;
        signal[i] = 0.5 * std::sin(2.0 * M_PI * 440.0 * t) +
                     0.3 * std::sin(2.0 * M_PI * 880.0 * t);
    }

    auto spectrum = simple_fft(signal);
    auto power = power_spectrum(spectrum);
    auto psd = power_spectrum_db(power);

    std::cout << "信号: 440 Hz (0.5) + 880 Hz (0.3)" << std::endl;

    // 显示部分频谱
    print_spectrum(power, sample_rate, 20);
}

// 演示频谱分析应用
void demo_spectrum_analysis() {
    print_separator("频谱分析应用");

    std::cout << "\n频谱分析的常见应用:\n" << std::endl;

    std::cout << "1. 音频可视化" << std::endl;
    std::cout << "   - 频谱图显示频率随时间变化" << std::endl;
    std::cout << "   - 实时频谱分析器" << std::endl;

    std::cout << "\n2. 噪声分析" << std::endl;
    std::cout << "   - 识别噪声频率成分" << std::endl;
    std::cout << "   - 设计针对性滤波器" << std::endl;

    std::cout << "\n3. 音乐分析" << std::endl;
    std::cout << "   - 识别乐器频率范围" << std::endl;
    std::cout << "   - 分析和弦成分" << std::endl;

    std::cout << "\n4. 语音分析" << std::endl;
    std::cout << "   - 语音识别特征提取" << std::endl;
    std::cout << "   - 说话人识别" << std::endl;

    // 生成测试频谱
    float sample_rate = 44100.0f;
    size_t fft_size = 2048;

    std::vector<double> signal(fft_size);
    for (size_t i = 0; i < fft_size; ++i) {
        double t = static_cast<double>(i) / sample_rate;
        // 多个频率成分
        signal[i] = 0.4 * std::sin(2.0 * M_PI * 261.63 * t) +  // C4
                     0.3 * std::sin(2.0 * M_PI * 329.63 * t) +  // E4
                     0.2 * std::sin(2.0 * M_PI * 392.00 * t);   // G4
    }

    auto spectrum = simple_fft(signal);
    auto power = power_spectrum(spectrum);

    std::cout << "\nC 大调和弦频谱:" << std::endl;
    print_spectrum(power, sample_rate, 30);
}

int main() {
    std::cout << "=== Spectrum Analysis Demo (频谱分析演示) ===" << std::endl;

    demo_power_spectrum();
    demo_spectrum_analysis();

    std::cout << "\n=== 频谱分析总结 ===" << std::endl;
    std::cout << "1. 功率谱显示信号能量分布" << std::endl;
    std::cout << "2. 频谱图显示频率随时间变化" << std::endl;
    std::cout << "3. 广泛用于音频分析和可视化" << std::endl;

    return 0;
}
