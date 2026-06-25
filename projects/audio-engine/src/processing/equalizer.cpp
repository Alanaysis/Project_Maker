// equalizer.cpp - 均衡器演示
//
// 本文件演示音频均衡器的基本原理：
// 1. 参数均衡器（PEQ）
// 2. 图形均衡器（GEQ）
// 3. 低通/高通/带通滤波器
// 4. 频率响应可视化
//
// 编译: g++ -std=c++17 -I../../include equalizer.cpp -o equalizer -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <complex>

using namespace audio;

// 二阶 IIR 滤波器系数
struct BiquadCoeffs {
    float b0, b1, b2, a1, a2;
};

// 计算峰值均衡器系数
BiquadCoeffs calculate_peak_eq(float freq, float gain_db, float q, float sample_rate) {
    BiquadCoeffs coeffs;
    float A = std::sqrt(db_to_linear(gain_db));
    float w0 = 2.0f * M_PI * freq / sample_rate;
    float alpha = std::sin(w0) / (2.0f * q);

    float b0 = 1.0f + alpha * A;
    float b1 = -2.0f * std::cos(w0);
    float b2 = 1.0f - alpha * A;
    float a0 = 1.0f + alpha / A;
    float a1 = -2.0f * std::cos(w0);
    float a2 = 1.0f - alpha / A;

    // 归一化
    coeffs.b0 = b0 / a0;
    coeffs.b1 = b1 / a0;
    coeffs.b2 = b2 / a0;
    coeffs.a1 = a1 / a0;
    coeffs.a2 = a2 / a0;

    return coeffs;
}

// 计算低通滤波器系数
BiquadCoeffs calculate_lowpass(float freq, float q, float sample_rate) {
    BiquadCoeffs coeffs;
    float w0 = 2.0f * M_PI * freq / sample_rate;
    float alpha = std::sin(w0) / (2.0f * q);

    float b0 = (1.0f - std::cos(w0)) / 2.0f;
    float b1 = 1.0f - std::cos(w0);
    float b2 = (1.0f - std::cos(w0)) / 2.0f;
    float a0 = 1.0f + alpha;
    float a1 = -2.0f * std::cos(w0);
    float a2 = 1.0f - alpha;

    coeffs.b0 = b0 / a0;
    coeffs.b1 = b1 / a0;
    coeffs.b2 = b2 / a0;
    coeffs.a1 = a1 / a0;
    coeffs.a2 = a2 / a0;

    return coeffs;
}

// 计算高通滤波器系数
BiquadCoeffs calculate_highpass(float freq, float q, float sample_rate) {
    BiquadCoeffs coeffs;
    float w0 = 2.0f * M_PI * freq / sample_rate;
    float alpha = std::sin(w0) / (2.0f * q);

    float b0 = (1.0f + std::cos(w0)) / 2.0f;
    float b1 = -(1.0f + std::cos(w0));
    float b2 = (1.0f + std::cos(w0)) / 2.0f;
    float a0 = 1.0f + alpha;
    float a1 = -2.0f * std::cos(w0);
    float a2 = 1.0f - alpha;

    coeffs.b0 = b0 / a0;
    coeffs.b1 = b1 / a0;
    coeffs.b2 = b2 / a0;
    coeffs.a1 = a1 / a0;
    coeffs.a2 = a2 / a0;

    return coeffs;
}

// 应用双二阶滤波器
void apply_biquad(AudioBuffer& buffer, const BiquadCoeffs& coeffs) {
    float x1 = 0, x2 = 0, y1 = 0, y2 = 0;

    for (size_t i = 0; i < buffer.samples.size(); ++i) {
        float x0 = buffer.samples[i];
        float y0 = coeffs.b0 * x0 + coeffs.b1 * x1 + coeffs.b2 * x2
                   - coeffs.a1 * y1 - coeffs.a2 * y2;

        buffer.samples[i] = y0;

        x2 = x1; x1 = x0;
        y2 = y1; y1 = y0;
    }
}

// 计算滤波器频率响应
std::vector<float> calculate_frequency_response(const BiquadCoeffs& coeffs,
                                                  float sample_rate,
                                                  int num_points = 512) {
    std::vector<float> response(num_points);

    for (int i = 0; i < num_points; ++i) {
        float freq = (sample_rate / 2.0f) * i / num_points;
        float w = 2.0f * M_PI * freq / sample_rate;

        std::complex<float> z = std::exp(std::complex<float>(0, -w));
        std::complex<float> z2 = z * z;

        std::complex<float> num = coeffs.b0 + coeffs.b1 * z + coeffs.b2 * z2;
        std::complex<float> den = 1.0f + coeffs.a1 * z + coeffs.a2 * z2;

        response[i] = linear_to_db(std::abs(num / den));
    }

    return response;
}

// 演示峰值均衡器
void demo_peak_eq() {
    print_separator("峰值均衡器 (Peak EQ)");

    std::cout << "\n峰值均衡器：在特定频率提升或衰减\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建测试信号（白噪声）
    auto noise = generate_noise(sample_rate, 1.0f);
    AudioBuffer buffer = make_buffer(noise, static_cast<uint32_t>(sample_rate));

    // 在 1000 Hz 提升 6 dB
    BiquadCoeffs coeffs = calculate_peak_eq(1000.0f, 6.0f, 2.0f, sample_rate);

    AudioBuffer processed = buffer;
    apply_biquad(processed, coeffs);

    std::cout << "参数:" << std::endl;
    std::cout << "  频率: 1000 Hz" << std::endl;
    std::cout << "  增益: +6 dB" << std::endl;
    std::cout << "  Q: 2.0" << std::endl;

    // 显示频率响应
    auto response = calculate_frequency_response(coeffs, sample_rate);
    std::cout << "\n频率响应 (部分):" << std::endl;
    for (int i = 0; i < 10; ++i) {
        float freq = (sample_rate / 2.0f) * i / 10;
        printf("  %6.0f Hz: %+.1f dB\n", freq, response[i]);
    }

    write_wav("eq_peak.wav", processed);
}

// 演示低通滤波器
void demo_lowpass() {
    print_separator("低通滤波器 (Low Pass)");

    std::cout << "\n低通滤波器：允许低频通过，衰减高频\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建混合信号
    auto low = generate_sine(500.0f, sample_rate, 1.0f, 0.5f);
    auto high = generate_sine(5000.0f, sample_rate, 1.0f, 0.5f);

    std::vector<float> mixed(low.size());
    for (size_t i = 0; i < low.size(); ++i) {
        mixed[i] = low[i] + high[i];
    }

    AudioBuffer buffer = make_buffer(mixed, static_cast<uint32_t>(sample_rate));

    // 应用低通滤波器 (截止频率 1000 Hz)
    BiquadCoeffs coeffs = calculate_lowpass(1000.0f, 0.707f, sample_rate);

    AudioBuffer processed = buffer;
    apply_biquad(processed, coeffs);

    std::cout << "原始信号: 500 Hz + 5000 Hz" << std::endl;
    std::cout << "截止频率: 1000 Hz" << std::endl;

    std::cout << "\n处理后:" << std::endl;
    std::cout << "  峰值: " << processed.peak() << std::endl;
    std::cout << "  (高频被衰减)" << std::endl;

    write_wav("eq_lowpass.wav", processed);
}

// 演示高通滤波器
void demo_highpass() {
    print_separator("高通滤波器 (High Pass)");

    std::cout << "\n高通滤波器：允许高频通过，衰减低频\n" << std::endl;

    float sample_rate = 44100.0f;

    auto low = generate_sine(200.0f, sample_rate, 1.0f, 0.5f);
    auto high = generate_sine(2000.0f, sample_rate, 1.0f, 0.5f);

    std::vector<float> mixed(low.size());
    for (size_t i = 0; i < low.size(); ++i) {
        mixed[i] = low[i] + high[i];
    }

    AudioBuffer buffer = make_buffer(mixed, static_cast<uint32_t>(sample_rate));

    BiquadCoeffs coeffs = calculate_highpass(1000.0f, 0.707f, sample_rate);

    AudioBuffer processed = buffer;
    apply_biquad(processed, coeffs);

    std::cout << "原始信号: 200 Hz + 2000 Hz" << std::endl;
    std::cout << "截止频率: 1000 Hz" << std::endl;

    write_wav("eq_highpass.wav", processed);
}

// 演示图形均衡器
void demo_graphic_eq() {
    print_separator("图形均衡器 (Graphic EQ)");

    std::cout << "\n图形均衡器：多个固定频段的均衡器\n" << std::endl;

    float sample_rate = 44100.0f;

    // 定义频段
    struct EqBand {
        float freq;
        float gain_db;
    };

    std::vector<EqBand> bands = {
        {60.0f, -3.0f},    // 低频衰减
        {250.0f, 0.0f},    // 中低频
        {1000.0f, 3.0f},   // 中频提升
        {4000.0f, 6.0f},   // 中高频提升
        {16000.0f, -6.0f}  // 高频衰减
    };

    std::cout << "图形均衡器设置:" << std::endl;
    std::cout << "频段 (Hz) | 增益 (dB)" << std::endl;
    std::cout << "----------|----------" << std::endl;
    for (const auto& band : bands) {
        printf("%8.0f  | %+.1f\n", band.freq, band.gain_db);
    }

    // 应用多个均衡器
    auto noise = generate_noise(sample_rate, 1.0f);
    AudioBuffer buffer = make_buffer(noise, static_cast<uint32_t>(sample_rate));
    AudioBuffer processed = buffer;

    for (const auto& band : bands) {
        if (band.gain_db != 0.0f) {
            BiquadCoeffs coeffs = calculate_peak_eq(band.freq, band.gain_db, 2.0f, sample_rate);
            apply_biquad(processed, coeffs);
        }
    }

    write_wav("eq_graphic.wav", processed);
}

// 演示参数均衡器应用
void demo_parametric_eq() {
    print_separator("参数均衡器应用");

    std::cout << "\n参数均衡器的常见应用:\n" << std::endl;

    std::cout << "1. 人声增强" << std::endl;
    std::cout << "   - 提升 2-5 kHz (清晰度)" << std::endl;
    std::cout << "   - 衰减 200-400 Hz (减少浑浊)" << std::endl;

    std::cout << "\n2. 低音增强" << std::endl;
    std::cout << "   - 提升 60-100 Hz (低音)" << std::endl;
    std::cout << "   - 衰减 200-300 Hz (减少浑浊)" << std::endl;

    std::cout << "\n3. 高音增强" << std::endl;
    std::cout << "   - 提升 8-12 kHz (亮度)" << std::endl;
    std::cout << "   - 衰减 3-5 kHz (减少刺耳)" << std::endl;

    // 演示人声增强
    float sample_rate = 44100.0f;
    auto vocal = generate_sine(300.0f, sample_rate, 1.0f, 0.5f);
    AudioBuffer buffer = make_buffer(vocal, static_cast<uint32_t>(sample_rate));

    // 提升 3 kHz
    BiquadCoeffs coeffs = calculate_peak_eq(3000.0f, 6.0f, 2.0f, sample_rate);
    AudioBuffer processed = buffer;
    apply_biquad(processed, coeffs);

    write_wav("eq_vocal_enhance.wav", processed);
}

int main() {
    std::cout << "=== Equalizer Demo (均衡器演示) ===" << std::endl;

    demo_peak_eq();
    demo_lowpass();
    demo_highpass();
    demo_graphic_eq();
    demo_parametric_eq();

    std::cout << "\n=== 均衡器总结 ===" << std::endl;
    std::cout << "1. 均衡器用于调整音频的频率响应" << std::endl;
    std::cout << "2. 峰值 EQ 在特定频率提升或衰减" << std::endl;
    std::cout << "3. 低通/高通滤波器用于去除特定频率范围" << std::endl;
    std::cout << "4. 图形 EQ 有多个固定频段" << std::endl;

    return 0;
}
