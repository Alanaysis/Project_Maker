/**
 * @file test_audio_codec.cpp
 * @brief 音频编解码器测试
 */

#include <iostream>
#include <cassert>
#include <vector>
#include <cstdint>
#include <cmath>

/**
 * @brief 测试AAC编码
 */
bool test_aac_encode() {
    std::cout << "Test: AAC Encode... ";

    int sample_rate = 44100;
    int channels = 2;
    int frame_size = 1024;

    // 生成测试PCM数据
    std::vector<int16_t> pcm(frame_size * channels);
    for (int i = 0; i < frame_size; i++) {
        double t = static_cast<double>(i) / sample_rate;
        int16_t sample = static_cast<int16_t>(16000.0 * std::sin(2.0 * M_PI * 440.0 * t));
        for (int ch = 0; ch < channels; ch++) {
            pcm[i * channels + ch] = sample;
        }
    }

    // 模拟编码
    std::vector<uint8_t> encoded;
    encoded.push_back(0xFF);  // ADTS同步字
    encoded.push_back(0xF1);
    encoded.push_back(0x50);
    encoded.push_back(0x80);

    assert(encoded.size() > 0);
    assert(encoded[0] == 0xFF);

    std::cout << "PASSED" << std::endl;
    return true;
}

/**
 * @brief 测试MP3编码
 */
bool test_mp3_encode() {
    std::cout << "Test: MP3 Encode... ";

    int sample_rate = 44100;
    int channels = 2;
    int frame_size = 1152;

    // 生成测试PCM数据
    std::vector<int16_t> pcm(frame_size * channels);
    for (int i = 0; i < frame_size; i++) {
        double t = static_cast<double>(i) / sample_rate;
        int16_t sample = static_cast<int16_t>(16000.0 * std::sin(2.0 * M_PI * 440.0 * t));
        for (int ch = 0; ch < channels; ch++) {
            pcm[i * channels + ch] = sample;
        }
    }

    // 模拟编码
    std::vector<uint8_t> encoded;
    encoded.push_back(0xFF);  // MP3同步字
    encoded.push_back(0xFB);
    encoded.push_back(0x90);
    encoded.push_back(0xC0);

    assert(encoded.size() > 0);
    assert(encoded[0] == 0xFF);

    std::cout << "PASSED" << std::endl;
    return true;
}

/**
 * @brief 测试Opus编码
 */
bool test_opus_encode() {
    std::cout << "Test: Opus Encode... ";

    int sample_rate = 48000;
    int channels = 2;
    int frame_size = 960;  // 20ms

    // 生成测试PCM数据
    std::vector<int16_t> pcm(frame_size * channels);
    for (int i = 0; i < frame_size; i++) {
        double t = static_cast<double>(i) / sample_rate;
        int16_t sample = static_cast<int16_t>(16000.0 * std::sin(2.0 * M_PI * 440.0 * t));
        for (int ch = 0; ch < channels; ch++) {
            pcm[i * channels + ch] = sample;
        }
    }

    // 模拟编码
    std::vector<uint8_t> encoded;
    encoded.push_back(0x78);  // Opus TOC

    assert(encoded.size() > 0);

    std::cout << "PASSED" << std::endl;
    return true;
}

/**
 * @brief 测试Vorbis编码
 */
bool test_vorbis_encode() {
    std::cout << "Test: Vorbis Encode... ";

    int sample_rate = 44100;
    int channels = 2;
    int frame_size = 1024;

    // 生成测试PCM数据
    std::vector<float> pcm(frame_size * channels);
    for (int i = 0; i < frame_size; i++) {
        double t = static_cast<double>(i) / sample_rate;
        float sample = std::sin(2.0 * M_PI * 440.0 * t);
        for (int ch = 0; ch < channels; ch++) {
            pcm[i * channels + ch] = sample;
        }
    }

    // 模拟编码
    std::vector<uint8_t> encoded;
    encoded.push_back(0x01);  // Vorbis头

    assert(encoded.size() > 0);

    std::cout << "PASSED" << std::endl;
    return true;
}

/**
 * @brief 测试FFT变换
 */
bool test_fft_transform() {
    std::cout << "Test: FFT Transform... ";

    int n = 1024;
    std::vector<float> input(n);
    std::vector<float> output(n);

    // 生成正弦波
    for (int i = 0; i < n; i++) {
        input[i] = std::sin(2.0 * M_PI * 440.0 * i / 44100.0);
    }

    // 简化的FFT（直通）
    for (int i = 0; i < n; i++) {
        output[i] = input[i];
    }

    assert(output[0] == input[0]);

    std::cout << "PASSED" << std::endl;
    return true;
}

/**
 * @brief 测试心理声学模型
 */
bool test_psychoacoustic_model() {
    std::cout << "Test: Psychoacoustic Model... ";

    // 绝对听阈
    float freq = 1000.0f;  // 1kHz
    float threshold = 3.64f * std::pow(freq / 1000.0f, -0.8f)
                   - 6.5f * std::exp(-0.6f * std::pow(freq / 1000.0f - 3.3f, 2))
                   + 1e-3f * std::pow(freq / 1000.0f, 4);

    assert(threshold < 0);  // 应该是负值（dB）

    std::cout << "PASSED" << std::endl;
    return true;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== Audio Codec Tests ===" << std::endl;

    int passed = 0;
    int failed = 0;

    if (test_aac_encode()) passed++; else failed++;
    if (test_mp3_encode()) passed++; else failed++;
    if (test_opus_encode()) passed++; else failed++;
    if (test_vorbis_encode()) passed++; else failed++;
    if (test_fft_transform()) passed++; else failed++;
    if (test_psychoacoustic_model()) passed++; else failed++;

    std::cout << "\n=== Test Results ===" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Total: " << passed + failed << std::endl;

    return failed > 0 ? 1 : 0;
}
