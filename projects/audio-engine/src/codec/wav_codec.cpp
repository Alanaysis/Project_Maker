// wav_codec.cpp - WAV 文件编解码演示
//
// 本文件演示 WAV 文件的读写操作：
// 1. WAV 文件格式解析
// 2. WAV 文件读取
// 3. WAV 文件写入
// 4. 不同格式支持
//
// 编译: g++ -std=c++17 -I../../include wav_codec.cpp -o wav_codec -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <fstream>

using namespace audio;

// 演示 WAV 文件格式
void demo_wav_format() {
    print_separator("WAV 文件格式");

    std::cout << "\nWAV 文件结构:\n" << std::endl;

    std::cout << "┌─────────────────────────────────┐" << std::endl;
    std::cout << "│ RIFF Header (12 bytes)          │" << std::endl;
    std::cout << "│   - 'RIFF' (4 bytes)            │" << std::endl;
    std::cout << "│   - File Size (4 bytes)         │" << std::endl;
    std::cout << "│   - 'WAVE' (4 bytes)            │" << std::endl;
    std::cout << "├─────────────────────────────────┤" << std::endl;
    std::cout << "│ fmt Subchunk (24 bytes)         │" << std::endl;
    std::cout << "│   - 'fmt ' (4 bytes)            │" << std::endl;
    std::cout << "│   - Subchunk Size (4 bytes)     │" << std::endl;
    std::cout << "│   - Audio Format (2 bytes)      │" << std::endl;
    std::cout << "│   - Num Channels (2 bytes)      │" << std::endl;
    std::cout << "│   - Sample Rate (4 bytes)       │" << std::endl;
    std::cout << "│   - Byte Rate (4 bytes)         │" << std::endl;
    std::cout << "│   - Block Align (2 bytes)       │" << std::endl;
    std::cout << "│   - Bits Per Sample (2 bytes)   │" << std::endl;
    std::cout << "├─────────────────────────────────┤" << std::endl;
    std::cout << "│ data Subchunk (8+ bytes)        │" << std::endl;
    std::cout << "│   - 'data' (4 bytes)            │" << std::endl;
    std::cout << "│   - Data Size (4 bytes)         │" << std::endl;
    std::cout << "│   - Audio Data (variable)       │" << std::endl;
    std::cout << "└─────────────────────────────────┘" << std::endl;

    std::cout << "\nAudio Format 值:" << std::endl;
    std::cout << "  1  = PCM (整数)" << std::endl;
    std::cout << "  3  = IEEE Float" << std::endl;
    std::cout << "  6  = A-law" << std::endl;
    std::cout << "  7  = μ-law" << std::endl;
}

// 演示创建 WAV 文件
void demo_create_wav() {
    print_separator("创建 WAV 文件");

    std::cout << "\n创建不同参数的 WAV 文件:\n" << std::endl;

    float duration = 2.0f;

    struct WavConfig {
        uint32_t sample_rate;
        uint16_t channels;
        uint16_t bit_depth;
        const char* description;
        const char* filename;
    };

    std::vector<WavConfig> configs = {
        {44100, 1, 16, "CD质量单声道", "wav_cd_mono.wav"},
        {44100, 2, 16, "CD质量立体声", "wav_cd_stereo.wav"},
        {48000, 2, 24, "专业音频立体声", "wav_pro_stereo.wav"},
        {96000, 2, 32, "高清音频立体声", "wav_hd_stereo.wav"},
        {8000, 1, 16, "电话质量单声道", "wav_phone.wav"}
    };

    for (const auto& config : configs) {
        auto samples = generate_sine(440.0f, config.sample_rate, duration);
        AudioBuffer buffer = make_buffer(samples, config.sample_rate, config.channels);
        buffer.bit_depth = config.bit_depth;

        if (write_wav(config.filename, buffer)) {
            float file_size = config.sample_rate * config.channels *
                             (config.bit_depth / 8.0f) * duration;

            std::cout << config.description << ":" << std::endl;
            std::cout << "  文件: " << config.filename << std::endl;
            std::cout << "  采样率: " << config.sample_rate << " Hz" << std::endl;
            std::cout << "  声道: " << config.channels << std::endl;
            std::cout << "  位深: " << config.bit_depth << "-bit" << std::endl;
            std::cout << "  大小: " << file_size / 1024 << " KB" << std::endl;
            std::cout << std::endl;
        }
    }
}

// 演示读取 WAV 文件信息
void demo_read_wav_info() {
    print_separator("读取 WAV 文件信息");

    std::cout << "\n先创建一个测试文件，然后读取其信息:\n" << std::endl;

    // 创建测试文件
    float duration = 1.0f;
    auto samples = generate_sine(1000.0f, 44100.0f, duration);
    AudioBuffer buffer = make_buffer(samples, 44100, 2);
    buffer.bit_depth = 16;

    std::string filename = "wav_test_info.wav";
    write_wav(filename, buffer);

    // 读取并显示信息
    try {
        AudioBuffer loaded = read_wav(filename);
        std::cout << "文件: " << filename << std::endl;
        print_buffer_info(loaded, "  ");
    } catch (const std::exception& e) {
        std::cout << "读取错误: " << e.what() << std::endl;
    }
}

// 演示 WAV 文件处理
void demo_wav_processing() {
    print_separator("WAV 文件处理");

    std::cout << "\n读取 WAV 文件，处理后保存:\n" << std::endl;

    // 创建原始文件
    float duration = 2.0f;
    auto samples = generate_sine(440.0f, 44100.0f, duration);
    AudioBuffer original = make_buffer(samples, 44100, 1);

    std::string input_file = "wav_process_input.wav";
    std::string output_file = "wav_process_output.wav";

    write_wav(input_file, original);
    std::cout << "输入文件: " << input_file << std::endl;
    print_buffer_info(original, "  原始");

    // 读取并处理
    AudioBuffer loaded = read_wav(input_file);

    // 音量减半
    for (auto& sample : loaded.samples) {
        sample *= 0.5f;
    }

    write_wav(output_file, loaded);
    std::cout << "\n输出文件: " << output_file << std::endl;
    print_buffer_info(loaded, "  处理后");

    std::cout << "\n处理: 音量减半 (-6 dB)" << std::endl;
}

// 演示 WAV 格式对比
void demo_wav_formats() {
    print_separator("WAV 格式对比");

    std::cout << "\n不同 WAV 格式的比较:\n" << std::endl;

    std::cout << "格式类型    | 位深度 | 动态范围 | 文件大小 | 应用场景" << std::endl;
    std::cout << "------------|--------|----------|----------|----------" << std::endl;
    std::cout << "PCM-8       | 8-bit  | 48 dB    | 最小     | 低质量语音" << std::endl;
    std::cout << "PCM-16      | 16-bit | 96 dB    | 中等     | CD质量" << std::endl;
    std::cout << "PCM-24      | 24-bit | 144 dB   | 较大     | 专业录音" << std::endl;
    std::cout << "IEEE Float  | 32-bit | 1528 dB  | 最大     | 内部处理" << std::endl;

    std::cout << "\n推荐:" << std::endl;
    std::cout << "  - 分发: PCM-16 (兼容性最好)" << std::endl;
    std::cout << "  - 录音: PCM-24 (保留余量)" << std::endl;
    std::cout << "  - 处理: IEEE Float (避免裁剪)" << std::endl;
}

int main() {
    std::cout << "=== WAV Codec Demo (WAV 编解码演示) ===" << std::endl;

    demo_wav_format();
    demo_create_wav();
    demo_read_wav_info();
    demo_wav_processing();
    demo_wav_formats();

    std::cout << "\n=== WAV 编解码总结 ===" << std::endl;
    std::cout << "1. WAV 是最简单的音频容器格式" << std::endl;
    std::cout << "2. 支持 PCM 和 IEEE Float 编码" << std::endl;
    std::cout << "3. 文件由 RIFF 头 + fmt 块 + data 块组成" << std::endl;
    std::cout << "4. 广泛支持，适合开发和测试" << std::endl;

    return 0;
}
