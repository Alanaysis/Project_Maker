// pcm_codec.cpp - PCM 编解码演示
//
// 本文件演示 PCM 编解码的基本原理：
// 1. 整数 PCM 编码（8/16/24/32-bit）
// 2. 浮点 PCM 编码（32/64-bit）
// 3. 字节序处理
//
// 编译: g++ -std=c++17 -I../../include pcm_codec.cpp -o pcm_codec -lm

#include "audio_engine.h"
#include <iostream>
#include <vector>
#include <cmath>
#include <cstring>

using namespace audio;

// PCM 16-bit 编码
std::vector<int16_t> encode_pcm16(const std::vector<float>& samples) {
    std::vector<int16_t> encoded(samples.size());
    for (size_t i = 0; i < samples.size(); ++i) {
        float clamped = clamp(samples[i], -1.0f, 1.0f);
        encoded[i] = static_cast<int16_t>(clamped * 32767.0f);
    }
    return encoded;
}

// PCM 16-bit 解码
std::vector<float> decode_pcm16(const std::vector<int16_t>& encoded) {
    std::vector<float> samples(encoded.size());
    for (size_t i = 0; i < encoded.size(); ++i) {
        samples[i] = encoded[i] / 32768.0f;
    }
    return samples;
}

// PCM 24-bit 编码（存储为 32-bit）
std::vector<int32_t> encode_pcm24(const std::vector<float>& samples) {
    std::vector<int32_t> encoded(samples.size());
    for (size_t i = 0; i < samples.size(); ++i) {
        float clamped = clamp(samples[i], -1.0f, 1.0f);
        encoded[i] = static_cast<int32_t>(clamped * 8388607.0f);
    }
    return encoded;
}

// PCM 24-bit 解码
std::vector<float> decode_pcm24(const std::vector<int32_t>& encoded) {
    std::vector<float> samples(encoded.size());
    for (size_t i = 0; i < encoded.size(); ++i) {
        samples[i] = encoded[i] / 8388608.0f;
    }
    return samples;
}

// PCM 8-bit 编码（无符号）
std::vector<uint8_t> encode_pcm8(const std::vector<float>& samples) {
    std::vector<uint8_t> encoded(samples.size());
    for (size_t i = 0; i < samples.size(); ++i) {
        float clamped = clamp(samples[i], -1.0f, 1.0f);
        encoded[i] = static_cast<uint8_t>((clamped + 1.0f) * 127.5f);
    }
    return encoded;
}

// PCM 8-bit 解码
std::vector<float> decode_pcm8(const std::vector<uint8_t>& encoded) {
    std::vector<float> samples(encoded.size());
    for (size_t i = 0; i < encoded.size(); ++i) {
        samples[i] = (encoded[i] - 128.0f) / 128.0f;
    }
    return samples;
}

// 字节序转换
uint16_t swap_endian16(uint16_t value) {
    return (value >> 8) | (value << 8);
}

uint32_t swap_endian32(uint32_t value) {
    return ((value >> 24) & 0xFF) |
           ((value >> 8) & 0xFF00) |
           ((value << 8) & 0xFF0000) |
           ((value << 24) & 0xFF000000);
}

// 检测系统字节序
bool is_little_endian() {
    uint16_t test = 1;
    return reinterpret_cast<uint8_t*>(&test)[0] == 1;
}

// 演示 PCM 编码
void demo_pcm_encoding() {
    print_separator("PCM 编码演示");

    std::cout << "\nPCM (Pulse Code Modulation): 脉冲编码调制\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 0.01f; // 10ms
    float freq = 1000.0f;

    auto original = generate_sine(freq, sample_rate, duration);

    // 显示前 10 个采样点
    std::cout << "原始浮点采样:" << std::endl;
    for (size_t i = 0; i < 10; ++i) {
        printf("  [%2zu] %+.6f\n", i, original[i]);
    }

    // 16-bit 编码
    auto pcm16 = encode_pcm16(original);
    auto decoded16 = decode_pcm16(pcm16);

    std::cout << "\n16-bit PCM 编码:" << std::endl;
    for (size_t i = 0; i < 10; ++i) {
        printf("  [%2zu] 原始: %+.6f -> 编码: %6d -> 解码: %+.6f (误差: %+.6f)\n",
               i, original[i], pcm16[i], decoded16[i], original[i] - decoded16[i]);
    }

    // 8-bit 编码
    auto pcm8 = encode_pcm8(original);
    auto decoded8 = decode_pcm8(pcm8);

    std::cout << "\n8-bit PCM 编码:" << std::endl;
    for (size_t i = 0; i < 10; ++i) {
        printf("  [%2zu] 原始: %+.6f -> 编码: %3u -> 解码: %+.6f (误差: %+.6f)\n",
               i, original[i], pcm8[i], decoded8[i], original[i] - decoded8[i]);
    }
}

// 演示 PCM 数据大小
void demo_pcm_sizes() {
    print_separator("PCM 数据大小");

    std::cout << "\n不同位深度的 PCM 数据大小:\n" << std::endl;

    float duration = 60.0f; // 1 分钟
    float sample_rate = 44100.0f;
    int channels = 2;

    struct PCMFormat {
        int bits;
        const char* name;
    };

    std::vector<PCMFormat> formats = {
        {8, "PCM-8"},
        {16, "PCM-16"},
        {24, "PCM-24"},
        {32, "PCM-32"}
    };

    std::cout << "格式    | 每采样字节 | 每秒字节   | 1分钟立体声" << std::endl;
    std::cout << "--------|-----------|-----------|------------" << std::endl;

    for (const auto& fmt : formats) {
        float bytes_per_sample = fmt.bits / 8.0f;
        float bytes_per_sec = sample_rate * channels * bytes_per_sample;
        float total_bytes = bytes_per_sec * duration;
        float total_mb = total_bytes / (1024 * 1024);

        printf("%-7s | %7.1f   | %9.0f | %6.1f MB\n",
               fmt.name, bytes_per_sample, bytes_per_sec, total_mb);
    }
}

// 演示字节序
void demo_endianness() {
    print_separator("字节序 (Endianness)");

    std::cout << "\n字节序：多字节数据的存储顺序\n" << std::endl;

    bool le = is_little_endian();
    std::cout << "当前系统: " << (le ? "Little Endian" : "Big Endian") << std::endl;

    std::cout << "\n16-bit 值 0x1234 的存储:" << std::endl;
    std::cout << "  Little Endian: 34 12 (低字节在前)" << std::endl;
    std::cout << "  Big Endian:    12 34 (高字节在前)" << std::endl;

    uint16_t value = 0x1234;
    uint16_t swapped = swap_endian16(value);

    std::cout << "\n转换示例:" << std::endl;
    printf("  原始: 0x%04X\n", value);
    printf("  转换: 0x%04X\n", swapped);

    std::cout << "\nWAV 文件使用 Little Endian" << std::endl;
    std::cout << "AIFF 文件使用 Big Endian" << std::endl;
}

// 演示 PCM 数据的内存布局
void demo_memory_layout() {
    print_separator("PCM 内存布局");

    std::cout << "\nPCM 数据在内存中的存储:\n" << std::endl;

    float sample = 0.7071f;

    // 16-bit PCM
    int16_t pcm16 = static_cast<int16_t>(sample * 32767);
    uint8_t* bytes = reinterpret_cast<uint8_t*>(&pcm16);

    std::cout << "采样值 0.7071 的 16-bit PCM 表示:" << std::endl;
    printf("  十进制: %d\n", pcm16);
    printf("  十六进制: 0x%04X\n", static_cast<uint16_t>(pcm16));
    printf("  字节 (Little Endian): %02X %02X\n", bytes[0], bytes[1]);

    // 浮点 PCM
    float* float_ptr = &sample;
    uint8_t* float_bytes = reinterpret_cast<uint8_t*>(float_ptr);

    std::cout << "\n采样值 0.7071 的 32-bit float 表示:" << std::endl;
    printf("  十六进制: 0x%08X\n", *reinterpret_cast<uint32_t*>(&sample));
    printf("  字节 (Little Endian): %02X %02X %02X %02X\n",
           float_bytes[0], float_bytes[1], float_bytes[2], float_bytes[3]);
}

// 生成 PCM 文件
void generate_pcm_files() {
    print_separator("生成 PCM 文件");

    std::cout << "\n生成不同格式的 PCM 文件:\n" << std::endl;

    float sample_rate = 44100.0f;
    float duration = 1.0f;
    float freq = 440.0f;

    auto samples = generate_sine(freq, sample_rate, duration);

    // 作为 WAV 文件保存（使用不同的位深度）
    AudioBuffer buffer = make_buffer(samples, static_cast<uint32_t>(sample_rate));

    // 32-bit float WAV
    buffer.bit_depth = 32;
    write_wav("pcm_32bit_float.wav", buffer);
    std::cout << "  pcm_32bit_float.wav (32-bit float)" << std::endl;

    // 保存原始 PCM 数据（16-bit）
    auto pcm16 = encode_pcm16(samples);
    std::ofstream file("pcm_16bit_raw.pcm", std::ios::binary);
    file.write(reinterpret_cast<const char*>(pcm16.data()),
               pcm16.size() * sizeof(int16_t));
    file.close();
    std::cout << "  pcm_16bit_raw.pcm (原始 16-bit PCM 数据)" << std::endl;

    std::cout << "\n注意：原始 PCM 文件没有头部信息，播放时需要指定采样率和格式" << std::endl;
}

int main() {
    std::cout << "=== PCM Codec Demo (PCM 编解码演示) ===" << std::endl;

    demo_pcm_encoding();
    demo_pcm_sizes();
    demo_endianness();
    demo_memory_layout();
    generate_pcm_files();

    std::cout << "\n=== PCM 编解码总结 ===" << std::endl;
    std::cout << "1. PCM 是最基本的数字音频编码方式" << std::endl;
    std::cout << "2. 位深度决定精度：8/16/24/32-bit" << std::endl;
    std::cout << "3. 浮点 PCM 提供更大的动态范围" << std::endl;
    std::cout << "4. 字节序影响多字节数据的存储顺序" << std::endl;

    return 0;
}
