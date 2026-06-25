// analyzer.cpp - 音频分析工具演示
//
// 本文件演示音频分析工具的基本功能：
// 1. 文件信息显示
// 2. 频谱分析
// 3. 峰值/RMS 电平
//
// 编译: g++ -std=c++17 -I../../include analyzer.cpp -o analyzer -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>

using namespace audio;

// 音频分析器类
class AudioAnalyzer {
public:
    AudioAnalyzer() {}

    bool load(const std::string& filename) {
        try {
            buffer_ = read_wav(filename);
            filename_ = filename;
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << std::endl;
            return false;
        }
    }

    void print_info() const {
        std::cout << "\n文件信息:" << std::endl;
        std::cout << "  文件名: " << filename_ << std::endl;
        std::cout << "  采样率: " << buffer_.sample_rate << " Hz" << std::endl;
        std::cout << "  声道数: " << buffer_.channels << std::endl;
        std::cout << "  位深度: " << buffer_.bit_depth << " bit" << std::endl;
        std::cout << "  时长: " << buffer_.duration() << " 秒" << std::endl;
        std::cout << "  采样点数: " << buffer_.num_samples() << std::endl;
    }

    void print_levels() const {
        std::cout << "\n电平信息:" << std::endl;
        std::cout << "  峰值: " << buffer_.peak()
                  << " (" << linear_to_db(buffer_.peak()) << " dBFS)" << std::endl;
        std::cout << "  RMS: " << buffer_.rms()
                  << " (" << linear_to_db(buffer_.rms()) << " dBFS)" << std::endl;

        // 计算动态范围
        float min_level = 1.0f;
        for (float s : buffer_.samples) {
            float abs_s = std::abs(s);
            if (abs_s > 0.0001f) {  // 忽略接近零的值
                min_level = std::min(min_level, abs_s);
            }
        }
        float dynamic_range = linear_to_db(buffer_.peak()) - linear_to_db(min_level);
        std::cout << "  动态范围: " << dynamic_range << " dB" << std::endl;
    }

    void print_statistics() const {
        std::cout << "\n统计信息:" << std::endl;

        // 计算过零率
        size_t zero_crossings = 0;
        for (size_t i = 1; i < buffer_.samples.size(); ++i) {
            if ((buffer_.samples[i - 1] >= 0 && buffer_.samples[i] < 0) ||
                (buffer_.samples[i - 1] < 0 && buffer_.samples[i] >= 0)) {
                ++zero_crossings;
            }
        }
        float zcr = static_cast<float>(zero_crossings) / buffer_.samples.size();
        std::cout << "  过零率: " << zcr << std::endl;

        // 计算频谱质心（简化）
        float spectral_centroid = zcr * buffer_.sample_rate / 2.0f;
        std::cout << "  频谱质心: " << spectral_centroid << " Hz" << std::endl;
    }

    void analyze_spectrum() const {
        std::cout << "\n频谱分析:" << std::endl;

        // 使用部分数据进行分析
        size_t fft_size = 4096;
        size_t start = buffer_.samples.size() / 4;  // 从 1/4 处开始

        std::vector<double> signal(fft_size);
        for (size_t i = 0; i < fft_size && start + i < buffer_.samples.size(); ++i) {
            signal[i] = buffer_.samples[start + i];
        }

        // 简化的频率分析
        std::cout << "  频率成分分析:" << std::endl;

        // 检测主要频率（简化方法）
        size_t zero_crossings = 0;
        for (size_t i = 1; i < fft_size; ++i) {
            if ((signal[i - 1] >= 0 && signal[i] < 0) ||
                (signal[i - 1] < 0 && signal[i] >= 0)) {
                ++zero_crossings;
            }
        }

        float estimated_freq = zero_crossings * buffer_.sample_rate / (2.0f * fft_size);
        std::cout << "    估计基频: " << estimated_freq << " Hz" << std::endl;
    }

    void generate_report() const {
        print_separator("音频分析报告");
        print_info();
        print_levels();
        print_statistics();
        analyze_spectrum();
    }

private:
    std::string filename_;
    AudioBuffer buffer_;
};

// 演示文件分析
void demo_file_analysis() {
    print_separator("文件分析");

    std::cout << "\n分析音频文件的详细信息:\n" << std::endl;

    float sample_rate = 44100.0f;

    // 创建不同类型的测试文件
    auto sine = generate_sine(440.0f, sample_rate, 2.0f, 0.7f);
    AudioBuffer sine_buf = make_buffer(sine, static_cast<uint32_t>(sample_rate));
    write_wav("analyze_sine.wav", sine_buf);

    auto noise = generate_noise(sample_rate, 2.0f, 0.3f);
    AudioBuffer noise_buf = make_buffer(noise, static_cast<uint32_t>(sample_rate));
    write_wav("analyze_noise.wav", noise_buf);

    // 分析
    AudioAnalyzer analyzer;

    std::cout << "分析正弦波文件:" << std::endl;
    analyzer.load("analyze_sine.wav");
    analyzer.generate_report();

    std::cout << "\n分析噪声文件:" << std::endl;
    analyzer.load("analyze_noise.wav");
    analyzer.generate_report();
}

// 演示电平分析
void demo_level_analysis() {
    print_separator("电平分析");

    std::cout << "\n分析音频的电平特征:\n" << std::endl;

    float sample_rate = 44100.0f;

    struct TestSignal {
        const char* name;
        std::vector<float> samples;
    };

    std::vector<TestSignal> signals = {
        {"低音量", generate_sine(440.0f, sample_rate, 1.0f, 0.1f)},
        {"中等音量", generate_sine(440.0f, sample_rate, 1.0f, 0.5f)},
        {"高音量", generate_sine(440.0f, sample_rate, 1.0f, 0.9f)}
    };

    for (const auto& sig : signals) {
        AudioBuffer buffer = make_buffer(sig.samples, static_cast<uint32_t>(sample_rate));

        std::cout << sig.name << ":" << std::endl;
        std::cout << "  峰值: " << buffer.peak()
                  << " (" << linear_to_db(buffer.peak()) << " dBFS)" << std::endl;
        std::cout << "  RMS: " << buffer.rms()
                  << " (" << linear_to_db(buffer.rms()) << " dBFS)" << std::endl;
    }
}

// 演示分析工具应用
void demo_analyzer_applications() {
    print_separator("分析工具应用");

    std::cout << "\n音频分析工具的应用:\n" << std::endl;

    std::cout << "1. 质量控制" << std::endl;
    std::cout << "   - 检查电平是否符合标准" << std::endl;
    std::cout << "   - 检测削波" << std::endl;
    std::cout << "   - 验证格式" << std::endl;

    std::cout << "\n2. 音频修复" << std::endl;
    std::cout << "   - 识别问题区域" << std::endl;
    std::cout << "   - 分析噪声特征" << std::endl;
    std::cout << "   - 确定修复参数" << std::endl;

    std::cout << "\n3. 音乐分析" << std::endl;
    std::cout << "   - 频谱分析" << std::endl;
    std::cout << "   - 特征提取" << std::endl;
    std::cout << "   - 相似度比较" << std::endl;

    std::cout << "\n4. 广播标准" << std::endl;
    std::cout << "   - 响度标准化" << std::endl;
    std::cout << "   - 真峰值检测" << std::endl;
}

int main() {
    std::cout << "=== Audio Analyzer Demo (音频分析工具演示) ===" << std::endl;

    demo_file_analysis();
    demo_level_analysis();
    demo_analyzer_applications();

    std::cout << "\n=== 音频分析工具总结 ===" << std::endl;
    std::cout << "1. 文件信息：采样率、声道、时长等" << std::endl;
    std::cout << "2. 电平分析：峰值、RMS、动态范围" << std::endl;
    std::cout << "3. 频谱分析：频率成分、频谱特征" << std::endl;
    std::cout << "4. 广泛用于质量控制和音频修复" << std::endl;

    return 0;
}
