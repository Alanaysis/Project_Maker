// fft.cpp - FFT 分析演示
//
// 本文件演示快速傅里叶变换（FFT）的基本原理：
// 1. Cooley-Tukey FFT 算法
// 2. 窗函数应用
// 3. 频谱计算
//
// 编译: g++ -std=c++17 -I../../include fft.cpp -o fft -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <complex>
#include <algorithm>

using namespace audio;

// 位反转置换
void bit_reverse(std::vector<std::complex<double>>& x) {
    size_t n = x.size();
    size_t bits = 0;
    size_t temp = n;
    while (temp >>= 1) ++bits;

    for (size_t i = 0; i < n; ++i) {
        size_t rev = 0;
        for (size_t j = 0; j < bits; ++j) {
            rev = (rev << 1) | ((i >> j) & 1);
        }
        if (i < rev) {
            std::swap(x[i], x[rev]);
        }
    }
}

// 迭代 FFT (Cooley-Tukey)
std::vector<std::complex<double>> fft(const std::vector<double>& input) {
    size_t n = input.size();

    // 检查是否为 2 的幂
    if (n == 0 || (n & (n - 1)) != 0) {
        throw std::runtime_error("FFT size must be a power of 2");
    }

    // 转换为复数
    std::vector<std::complex<double>> x(n);
    for (size_t i = 0; i < n; ++i) {
        x[i] = std::complex<double>(input[i], 0.0);
    }

    // 位反转
    bit_reverse(x);

    // 蝶形运算
    for (size_t len = 2; len <= n; len *= 2) {
        double angle = -2.0 * M_PI / len;
        std::complex<double> wn(std::cos(angle), std::sin(angle));

        for (size_t i = 0; i < n; i += len) {
            std::complex<double> w(1.0, 0.0);
            for (size_t j = 0; j < len / 2; ++j) {
                std::complex<double> u = x[i + j];
                std::complex<double> v = x[i + j + len / 2] * w;
                x[i + j] = u + v;
                x[i + j + len / 2] = u - v;
                w *= wn;
            }
        }
    }

    return x;
}

// IFFT
std::vector<double> ifft(const std::vector<std::complex<double>>& input) {
    size_t n = input.size();
    std::vector<std::complex<double>> x = input;

    // 取共轭
    for (auto& val : x) {
        val = std::conj(val);
    }

    // FFT
    bit_reverse(x);
    for (size_t len = 2; len <= n; len *= 2) {
        double angle = -2.0 * M_PI / len;
        std::complex<double> wn(std::cos(angle), std::sin(angle));

        for (size_t i = 0; i < n; i += len) {
            std::complex<double> w(1.0, 0.0);
            for (size_t j = 0; j < len / 2; ++j) {
                std::complex<double> u = x[i + j];
                std::complex<double> v = x[i + j + len / 2] * w;
                x[i + j] = u + v;
                x[i + j + len / 2] = u - v;
                w *= wn;
            }
        }
    }

    // 取共轭并归一化
    std::vector<double> output(n);
    for (size_t i = 0; i < n; ++i) {
        output[i] = std::conj(x[i]).real() / n;
    }

    return output;
}

// 窗函数
enum class WindowType {
    Rectangular,
    Hanning,
    Hamming,
    Blackman
};

std::vector<double> create_window(size_t size, WindowType type) {
    std::vector<double> window(size);

    for (size_t i = 0; i < size; ++i) {
        switch (type) {
            case WindowType::Rectangular:
                window[i] = 1.0;
                break;
            case WindowType::Hanning:
                window[i] = 0.5 * (1.0 - std::cos(2.0 * M_PI * i / (size - 1)));
                break;
            case WindowType::Hamming:
                window[i] = 0.54 - 0.46 * std::cos(2.0 * M_PI * i / (size - 1));
                break;
            case WindowType::Blackman:
                window[i] = 0.42 - 0.5 * std::cos(2.0 * M_PI * i / (size - 1)) +
                             0.08 * std::cos(4.0 * M_PI * i / (size - 1));
                break;
        }
    }

    return window;
}

// 应用窗函数
std::vector<double> apply_window(const std::vector<double>& signal,
                                  const std::vector<double>& window) {
    std::vector<double> output(signal.size());
    for (size_t i = 0; i < signal.size(); ++i) {
        output[i] = signal[i] * window[i];
    }
    return output;
}

// 计算幅度谱
std::vector<double> magnitude_spectrum(const std::vector<std::complex<double>>& spectrum) {
    std::vector<double> mag(spectrum.size() / 2);
    for (size_t i = 0; i < mag.size(); ++i) {
        mag[i] = std::abs(spectrum[i]) / spectrum.size() * 2.0;
    }
    return mag;
}

// 演示基本 FFT
void demo_basic_fft() {
    print_separator("基本 FFT");

    std::cout << "\nFFT 将时域信号转换为频域表示\n" << std::endl;

    // 创建测试信号：440 Hz + 880 Hz
    size_t fft_size = 1024;
    float sample_rate = 44100.0f;

    std::vector<double> signal(fft_size);
    for (size_t i = 0; i < fft_size; ++i) {
        double t = static_cast<double>(i) / sample_rate;
        signal[i] = 0.5 * std::sin(2.0 * M_PI * 440.0 * t) +
                     0.3 * std::sin(2.0 * M_PI * 880.0 * t);
    }

    // 执行 FFT
    auto spectrum = fft(signal);
    auto mag = magnitude_spectrum(spectrum);

    std::cout << "输入信号: 440 Hz (0.5) + 880 Hz (0.3)" << std::endl;
    std::cout << "FFT 大小: " << fft_size << std::endl;
    std::cout << "频率分辨率: " << sample_rate / fft_size << " Hz" << std::endl;

    // 显示频谱
    std::cout << "\n频谱 (前 10 个频率 bin):" << std::endl;
    for (size_t i = 0; i < 10; ++i) {
        double freq = i * sample_rate / fft_size;
        printf("  %6.1f Hz: %.4f\n", freq, mag[i]);
    }
}

// 演示窗函数
void demo_windowing() {
    print_separator("窗函数");

    std::cout << "\n窗函数减少频谱泄漏\n" << std::endl;

    size_t fft_size = 1024;
    float sample_rate = 44100.0f;

    // 创建信号
    std::vector<double> signal(fft_size);
    for (size_t i = 0; i < fft_size; ++i) {
        double t = static_cast<double>(i) / sample_rate;
        signal[i] = std::sin(2.0 * M_PI * 1000.0 * t);
    }

    // 不同窗函数
    std::vector<WindowType> types = {
        WindowType::Rectangular,
        WindowType::Hanning,
        WindowType::Hamming,
        WindowType::Blackman
    };

    std::vector<std::string> names = {"矩形窗", "汉宁窗", "汉明窗", "布莱克曼窗"};

    for (size_t i = 0; i < types.size(); ++i) {
        auto window = create_window(fft_size, types[i]);
        auto windowed = apply_window(signal, window);
        auto spectrum = fft(windowed);
        auto mag = magnitude_spectrum(spectrum);

        std::cout << names[i] << ":" << std::endl;
        std::cout << "  主瓣宽度: 窄 -> 宽" << std::endl;
        std::cout << "  旁瓣衰减: 低 -> 高" << std::endl;
    }

    std::cout << "\n窗函数选择:" << std::endl;
    std::cout << "  矩形窗: 频率分辨率最好，旁瓣最高" << std::endl;
    std::cout << "  汉宁窗: 平衡的选择" << std::endl;
    std::cout << "  汉明窗: 旁瓣更低" << std::endl;
    std::cout << "  布莱克曼窗: 旁瓣最低，主瓣最宽" << std::endl;
}

// 演示 FFT 应用
void demo_fft_applications() {
    print_separator("FFT 应用");

    std::cout << "\nFFT 的常见应用:\n" << std::endl;

    std::cout << "1. 频谱分析" << std::endl;
    std::cout << "   - 可视化音频频率成分" << std::endl;
    std::cout << "   - 识别频率峰值" << std::endl;

    std::cout << "\n2. 频域滤波" << std::endl;
    std::cout << "   - FFT -> 频域处理 -> IFFT" << std::endl;
    std::cout << "   - 高效实现卷积" << std::endl;

    std::cout << "\n3. 音高检测" << std::endl;
    std::cout << "   - 识别基频" << std::endl;
    std::cout << "   - 音乐信息检索" << std::endl;

    std::cout << "\n4. 音频压缩" << std::endl;
    std::cout << "   - MP3/AAC 使用 MDCT" << std::endl;
    std::cout << "   - 去除人耳不敏感的频率" << std::endl;

    // 生成频谱分析文件
    size_t fft_size = 4096;
    float sample_rate = 44100.0f;

    std::vector<double> signal(fft_size);
    for (size_t i = 0; i < fft_size; ++i) {
        double t = static_cast<double>(i) / sample_rate;
        signal[i] = 0.5 * std::sin(2.0 * M_PI * 440.0 * t) +
                     0.3 * std::sin(2.0 * M_PI * 880.0 * t) +
                     0.2 * std::sin(2.0 * M_PI * 1320.0 * t);
    }

    auto window = create_window(fft_size, WindowType::Hanning);
    auto windowed = apply_window(signal, window);
    auto spectrum = fft(windowed);
    auto mag = magnitude_spectrum(spectrum);

    std::cout << "\n频谱峰值:" << std::endl;
    for (size_t i = 1; i < mag.size() - 1; ++i) {
        if (mag[i] > mag[i-1] && mag[i] > mag[i+1] && mag[i] > 0.1) {
            double freq = i * sample_rate / fft_size;
            printf("  %.1f Hz: %.4f\n", freq, mag[i]);
        }
    }
}

int main() {
    std::cout << "=== FFT Analysis Demo (FFT 分析演示) ===" << std::endl;

    demo_basic_fft();
    demo_windowing();
    demo_fft_applications();

    std::cout << "\n=== FFT 总结 ===" << std::endl;
    std::cout << "1. FFT 将时域信号转换为频域表示" << std::endl;
    std::cout << "2. Cooley-Tukey 算法复杂度 O(N log N)" << std::endl;
    std::cout << "3. 窗函数减少频谱泄漏" << std::endl;
    std::cout << "4. 广泛用于频谱分析、滤波、压缩" << std::endl;

    return 0;
}
