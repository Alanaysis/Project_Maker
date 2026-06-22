#include <iostream>
#include <cassert>
#include <vector>
#include "audio_encoder.h"
#include "utils.h"

/**
 * @brief 音频编解码器测试
 */

// 测试编码器初始化
bool test_audio_encoder_init() {
    std::cout << "Test: Audio Encoder Init... ";

    AudioEncoder encoder;
    AudioEncoderConfig config;
    config.sample_rate = 44100;
    config.channels = 2;
    config.bitrate = 128000;

    int ret = encoder.init(config);
    assert(ret == 0);

    const char* name = encoder.getName();
    assert(name != nullptr);

    encoder.close();
    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试编码器重复初始化
bool test_audio_encoder_double_init() {
    std::cout << "Test: Audio Encoder Double Init... ";

    AudioEncoder encoder;
    AudioEncoderConfig config;
    config.sample_rate = 44100;
    config.channels = 2;
    config.bitrate = 128000;

    int ret = encoder.init(config);
    assert(ret == 0);

    ret = encoder.init(config);
    assert(ret == -1);  // 应该失败

    encoder.close();
    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试单帧编码
bool test_audio_encode_single_frame() {
    std::cout << "Test: Audio Encode Single Frame... ";

    AudioEncoder encoder;
    AudioEncoderConfig config;
    config.sample_rate = 44100;
    config.channels = 2;
    config.bitrate = 128000;

    int ret = encoder.init(config);
    assert(ret == 0);

    AVFrame* frame = utils::createTestAudioFrame(
        config.sample_rate, config.channels, 1024, 0);
    assert(frame != nullptr);

    AVPacket* pkt = av_packet_alloc();
    assert(pkt != nullptr);

    ret = encoder.encode(frame, pkt);
    assert(ret == 0);
    assert(pkt->size > 0);

    av_frame_free(&frame);
    av_packet_free(&pkt);
    encoder.close();

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试多帧编码
bool test_audio_encode_multiple_frames() {
    std::cout << "Test: Audio Encode Multiple Frames... ";

    AudioEncoder encoder;
    AudioEncoderConfig config;
    config.sample_rate = 44100;
    config.channels = 2;
    config.bitrate = 128000;

    int ret = encoder.init(config);
    assert(ret == 0);

    for (int i = 0; i < 10; i++) {
        AVFrame* frame = utils::createTestAudioFrame(
            config.sample_rate, config.channels, 1024, i);
        assert(frame != nullptr);

        AVPacket* pkt = av_packet_alloc();
        assert(pkt != nullptr);

        ret = encoder.encode(frame, pkt);
        assert(ret == 0);

        av_frame_free(&frame);
        av_packet_free(&pkt);
    }

    encoder.close();
    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试编码器刷新
bool test_audio_encoder_flush() {
    std::cout << "Test: Audio Encoder Flush... ";

    AudioEncoder encoder;
    AudioEncoderConfig config;
    config.sample_rate = 44100;
    config.channels = 2;
    config.bitrate = 128000;

    int ret = encoder.init(config);
    assert(ret == 0);

    // 编码几帧
    for (int i = 0; i < 5; i++) {
        AVFrame* frame = utils::createTestAudioFrame(
            config.sample_rate, config.channels, 1024, i);
        AVPacket* pkt = av_packet_alloc();
        encoder.encode(frame, pkt);
        av_frame_free(&frame);
        av_packet_free(&pkt);
    }

    // 刷新
    std::vector<AVPacket*> packets;
    ret = encoder.flush(packets);
    assert(ret == 0);

    // 清理
    for (auto* pkt : packets) {
        av_packet_free(&pkt);
    }
    encoder.close();

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试不同采样率
bool test_audio_different_sample_rates() {
    std::cout << "Test: Audio Different Sample Rates... ";

    int sample_rates[] = {22050, 44100, 48000};

    for (int sr : sample_rates) {
        AudioEncoder encoder;
        AudioEncoderConfig config;
        config.sample_rate = sr;
        config.channels = 2;
        config.bitrate = 128000;

        int ret = encoder.init(config);
        assert(ret == 0);

        AVFrame* frame = utils::createTestAudioFrame(sr, 2, 1024, 0);
        AVPacket* pkt = av_packet_alloc();

        ret = encoder.encode(frame, pkt);
        assert(ret == 0);

        av_frame_free(&frame);
        av_packet_free(&pkt);
        encoder.close();
    }

    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试不同声道数
bool test_audio_different_channels() {
    std::cout << "Test: Audio Different Channels... ";

    int channels[] = {1, 2};

    for (int ch : channels) {
        AudioEncoder encoder;
        AudioEncoderConfig config;
        config.sample_rate = 44100;
        config.channels = ch;
        config.bitrate = 128000;

        int ret = encoder.init(config);
        assert(ret == 0);

        AVFrame* frame = utils::createTestAudioFrame(44100, ch, 1024, 0);
        AVPacket* pkt = av_packet_alloc();

        ret = encoder.encode(frame, pkt);
        assert(ret == 0);

        av_frame_free(&frame);
        av_packet_free(&pkt);
        encoder.close();
    }

    std::cout << "PASSED" << std::endl;
    return true;
}

int main() {
    std::cout << "=== Audio Codec Tests ===" << std::endl;

    int passed = 0;
    int failed = 0;

    if (test_audio_encoder_init()) passed++; else failed++;
    if (test_audio_encoder_double_init()) passed++; else failed++;
    if (test_audio_encode_single_frame()) passed++; else failed++;
    if (test_audio_encode_multiple_frames()) passed++; else failed++;
    if (test_audio_encoder_flush()) passed++; else failed++;
    if (test_audio_different_sample_rates()) passed++; else failed++;
    if (test_audio_different_channels()) passed++; else failed++;

    std::cout << "\n=== Test Results ===" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Total: " << passed + failed << std::endl;

    return failed > 0 ? 1 : 0;
}
