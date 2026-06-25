#pragma once

// Audio Processing Engine - 统一头文件
// 包含所有音频处理相关的数据结构和工具函数

#include <vector>
#include <complex>
#include <cstdint>
#include <string>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>
#include <functional>
#include <memory>
#include <array>
#include <iostream>
#include <fstream>
#include <cstring>
#include <sstream>
#include <random>
#include <cassert>
#include <map>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace audio {

// ============================================================================
// 基础数据结构
// ============================================================================

// 音频缓冲区 - 所有音频数据的容器
struct AudioBuffer {
    std::vector<float> samples;      // 采样数据，范围 [-1.0, 1.0]
    uint32_t sample_rate = 44100;    // 采样率 (Hz)
    uint16_t channels = 1;           // 声道数
    uint16_t bit_depth = 16;         // 位深度

    // 获取每声道采样数
    size_t num_samples() const {
        return channels > 0 ? samples.size() / channels : 0;
    }

    // 获取时长（秒）
    double duration() const {
        return sample_rate > 0 ? static_cast<double>(num_samples()) / sample_rate : 0.0;
    }

    // 获取指定位置和声道的采样值
    float get_sample(size_t index, uint16_t channel = 0) const {
        return samples[index * channels + channel];
    }

    // 设置指定位置和声道的采样值
    void set_sample(size_t index, uint16_t channel, float value) {
        samples[index * channels + channel] = value;
    }

    // 调整大小
    void resize(size_t num_samples_per_channel) {
        samples.resize(num_samples_per_channel * channels, 0.0f);
    }

    // 清空
    void clear() {
        samples.clear();
    }

    // 获取峰值
    float peak() const {
        if (samples.empty()) return 0.0f;
        float max_val = 0.0f;
        for (float s : samples) {
            max_val = std::max(max_val, std::abs(s));
        }
        return max_val;
    }

    // 获取 RMS 电平
    float rms() const {
        if (samples.empty()) return 0.0f;
        float sum = 0.0f;
        for (float s : samples) {
            sum += s * s;
        }
        return std::sqrt(sum / samples.size());
    }

    // 转换为单声道
    AudioBuffer to_mono() const {
        AudioBuffer mono;
        mono.sample_rate = sample_rate;
        mono.channels = 1;
        mono.bit_depth = bit_depth;

        if (channels == 1) {
            mono.samples = samples;
        } else {
            size_t n = num_samples();
            mono.samples.resize(n);
            for (size_t i = 0; i < n; ++i) {
                float sum = 0.0f;
                for (uint16_t ch = 0; ch < channels; ++ch) {
                    sum += get_sample(i, ch);
                }
                mono.samples[i] = sum / channels;
            }
        }
        return mono;
    }

    // 转换为立体声
    AudioBuffer to_stereo() const {
        if (channels == 2) return *this;

        AudioBuffer stereo;
        stereo.sample_rate = sample_rate;
        stereo.channels = 2;
        stereo.bit_depth = bit_depth;
        stereo.samples.resize(num_samples() * 2);

        for (size_t i = 0; i < num_samples(); ++i) {
            stereo.samples[i * 2] = samples[i];
            stereo.samples[i * 2 + 1] = samples[i];
        }
        return stereo;
    }
};

// WAV 文件头
struct WavHeader {
    // RIFF 块
    char riff_id[4] = {'R', 'I', 'F', 'F'};
    uint32_t file_size = 0;
    char wave_id[4] = {'W', 'A', 'V', 'E'};

    // fmt 子块
    char fmt_id[4] = {'f', 'm', 't', ' '};
    uint32_t fmt_size = 16;
    uint16_t audio_format = 1;     // 1=PCM, 3=IEEE Float
    uint16_t num_channels = 1;
    uint32_t sample_rate = 44100;
    uint32_t byte_rate = 0;
    uint16_t block_align = 0;
    uint16_t bits_per_sample = 16;

    // data 子块
    char data_id[4] = {'d', 'a', 't', 'a'};
    uint32_t data_size = 0;

    // 计算派生字段
    void calculate() {
        block_align = num_channels * bits_per_sample / 8;
        byte_rate = sample_rate * block_align;
        file_size = 36 + data_size;
    }
};

// FFT 结果
struct FFTResult {
    std::vector<std::complex<double>> spectrum;
    size_t fft_size = 0;

    // 获取幅度谱
    std::vector<double> magnitude() const {
        std::vector<double> mag(spectrum.size());
        for (size_t i = 0; i < spectrum.size(); ++i) {
            mag[i] = std::abs(spectrum[i]);
        }
        return mag;
    }

    // 获取相位谱
    std::vector<double> phase() const {
        std::vector<double> ph(spectrum.size());
        for (size_t i = 0; i < spectrum.size(); ++i) {
            ph[i] = std::arg(spectrum[i]);
        }
        return ph;
    }

    // 获取功率谱
    std::vector<double> power() const {
        std::vector<double> pow(spectrum.size());
        for (size_t i = 0; i < spectrum.size(); ++i) {
            double mag = std::abs(spectrum[i]);
            pow[i] = mag * mag;
        }
        return pow;
    }
};

// ============================================================================
// 工具函数
// ============================================================================

// 线性插值
inline float lerp(float a, float b, float t) {
    return a + t * (b - a);
}

// 限制范围
inline float clamp(float value, float min_val, float max_val) {
    return std::max(min_val, std::min(max_val, value));
}

// dB 转线性
inline float db_to_linear(float db) {
    return std::pow(10.0f, db / 20.0f);
}

// 线性转 dB
inline float linear_to_db(float linear) {
    if (linear <= 0.0f) return -100.0f;
    return 20.0f * std::log10(linear);
}

// 生成正弦波
inline std::vector<float> generate_sine(float freq, float sample_rate,
                                         float duration, float amplitude = 1.0f) {
    size_t num_samples = static_cast<size_t>(sample_rate * duration);
    std::vector<float> samples(num_samples);
    for (size_t i = 0; i < num_samples; ++i) {
        samples[i] = amplitude * std::sin(2.0 * M_PI * freq * i / sample_rate);
    }
    return samples;
}

// 生成方波
inline std::vector<float> generate_square(float freq, float sample_rate,
                                           float duration, float amplitude = 1.0f) {
    size_t num_samples = static_cast<size_t>(sample_rate * duration);
    std::vector<float> samples(num_samples);
    for (size_t i = 0; i < num_samples; ++i) {
        double phase = std::fmod(freq * i / sample_rate, 1.0);
        samples[i] = amplitude * (phase < 0.5 ? 1.0f : -1.0f);
    }
    return samples;
}

// 生成三角波
inline std::vector<float> generate_triangle(float freq, float sample_rate,
                                             float duration, float amplitude = 1.0f) {
    size_t num_samples = static_cast<size_t>(sample_rate * duration);
    std::vector<float> samples(num_samples);
    for (size_t i = 0; i < num_samples; ++i) {
        double phase = std::fmod(freq * i / sample_rate, 1.0);
        samples[i] = amplitude * static_cast<float>(2.0 * std::abs(2.0 * phase - 1.0) - 1.0);
    }
    return samples;
}

// 生成锯齿波
inline std::vector<float> generate_sawtooth(float freq, float sample_rate,
                                             float duration, float amplitude = 1.0f) {
    size_t num_samples = static_cast<size_t>(sample_rate * duration);
    std::vector<float> samples(num_samples);
    for (size_t i = 0; i < num_samples; ++i) {
        double phase = std::fmod(freq * i / sample_rate, 1.0);
        samples[i] = amplitude * static_cast<float>(2.0 * phase - 1.0);
    }
    return samples;
}

// 生成白噪声
inline std::vector<float> generate_noise(float sample_rate, float duration,
                                          float amplitude = 1.0f) {
    size_t num_samples = static_cast<size_t>(sample_rate * duration);
    std::vector<float> samples(num_samples);
    std::mt19937 gen(42);
    std::uniform_real_distribution<float> dist(-amplitude, amplitude);
    for (size_t i = 0; i < num_samples; ++i) {
        samples[i] = dist(gen);
    }
    return samples;
}

// 创建 AudioBuffer 的便捷函数
inline AudioBuffer make_buffer(const std::vector<float>& samples,
                                uint32_t sample_rate = 44100,
                                uint16_t channels = 1) {
    AudioBuffer buffer;
    buffer.samples = samples;
    buffer.sample_rate = sample_rate;
    buffer.channels = channels;
    return buffer;
}

// 写入 WAV 文件
inline bool write_wav(const std::string& filename, const AudioBuffer& buffer) {
    WavHeader header;
    header.num_channels = buffer.channels;
    header.sample_rate = buffer.sample_rate;
    header.bits_per_sample = buffer.bit_depth;
    header.data_size = static_cast<uint32_t>(buffer.samples.size() * sizeof(float));
    header.audio_format = 3; // IEEE Float
    header.calculate();

    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) return false;

    file.write(reinterpret_cast<const char*>(&header), sizeof(header));

    // 写入 float 数据
    file.write(reinterpret_cast<const char*>(buffer.samples.data()),
               buffer.samples.size() * sizeof(float));

    file.close();
    return true;
}

// 读取 WAV 文件（简化版，支持 PCM 和 Float）
inline AudioBuffer read_wav(const std::string& filename) {
    AudioBuffer buffer;

    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file: " + filename);
    }

    WavHeader header;
    file.read(reinterpret_cast<char*>(&header), sizeof(header));

    if (std::string(header.riff_id, 4) != "RIFF" ||
        std::string(header.wave_id, 4) != "WAVE") {
        throw std::runtime_error("Invalid WAV file");
    }

    buffer.sample_rate = header.sample_rate;
    buffer.channels = header.num_channels;
    buffer.bit_depth = header.bits_per_sample;

    size_t num_samples = header.data_size / (header.bits_per_sample / 8);
    buffer.samples.resize(num_samples);

    if (header.audio_format == 3 && header.bits_per_sample == 32) {
        // IEEE Float
        file.read(reinterpret_cast<char*>(buffer.samples.data()),
                  num_samples * sizeof(float));
    } else if (header.audio_format == 1 && header.bits_per_sample == 16) {
        // PCM 16-bit
        std::vector<int16_t> raw(num_samples);
        file.read(reinterpret_cast<char*>(raw.data()), num_samples * sizeof(int16_t));
        for (size_t i = 0; i < num_samples; ++i) {
            buffer.samples[i] = raw[i] / 32768.0f;
        }
    } else {
        throw std::runtime_error("Unsupported WAV format");
    }

    file.close();
    return buffer;
}

// 打印分隔线
inline void print_separator(const std::string& title = "") {
    std::cout << "\n========================================" << std::endl;
    if (!title.empty()) {
        std::cout << "  " << title << std::endl;
        std::cout << "========================================" << std::endl;
    }
}

// 打印音频信息
inline void print_buffer_info(const AudioBuffer& buffer, const std::string& label = "") {
    if (!label.empty()) {
        std::cout << label << ":" << std::endl;
    }
    std::cout << "  Sample Rate: " << buffer.sample_rate << " Hz" << std::endl;
    std::cout << "  Channels: " << buffer.channels << std::endl;
    std::cout << "  Bit Depth: " << buffer.bit_depth << std::endl;
    std::cout << "  Duration: " << buffer.duration() << " s" << std::endl;
    std::cout << "  Samples: " << buffer.num_samples() << std::endl;
    std::cout << "  Peak: " << buffer.peak() << std::endl;
    std::cout << "  RMS: " << buffer.rms() << std::endl;
}

} // namespace audio
