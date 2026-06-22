#include <iostream>
#include <cassert>
#include <vector>
#include "video_encoder.h"
#include "video_decoder.h"
#include "utils.h"

/**
 * @brief 视频编解码器测试
 */

// 测试编码器初始化
bool test_encoder_init() {
    std::cout << "Test: Encoder Init... ";

    VideoEncoder encoder;
    VideoEncoderConfig config;
    config.width = 320;
    config.height = 240;
    config.fps = 30;
    config.bitrate = 500000;
    config.preset = "ultrafast";

    int ret = encoder.init(config);
    assert(ret == 0);

    const char* name = encoder.getName();
    assert(name != nullptr);
    assert(std::string(name) == "libx264");

    encoder.close();
    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试编码器重复初始化
bool test_encoder_double_init() {
    std::cout << "Test: Encoder Double Init... ";

    VideoEncoder encoder;
    VideoEncoderConfig config;
    config.width = 320;
    config.height = 240;
    config.preset = "ultrafast";

    int ret = encoder.init(config);
    assert(ret == 0);

    ret = encoder.init(config);
    assert(ret == -1);  // 应该失败

    encoder.close();
    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试单帧编码
bool test_encode_single_frame() {
    std::cout << "Test: Encode Single Frame... ";

    VideoEncoder encoder;
    VideoEncoderConfig config;
    config.width = 320;
    config.height = 240;
    config.fps = 30;
    config.bitrate = 500000;
    config.preset = "ultrafast";

    int ret = encoder.init(config);
    assert(ret == 0);

    AVFrame* frame = utils::createTestFrame(config.width, config.height, 0);
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
bool test_encode_multiple_frames() {
    std::cout << "Test: Encode Multiple Frames... ";

    VideoEncoder encoder;
    VideoEncoderConfig config;
    config.width = 320;
    config.height = 240;
    config.fps = 30;
    config.bitrate = 500000;
    config.preset = "ultrafast";

    int ret = encoder.init(config);
    assert(ret == 0);

    for (int i = 0; i < 10; i++) {
        AVFrame* frame = utils::createTestFrame(config.width, config.height, i);
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
bool test_encoder_flush() {
    std::cout << "Test: Encoder Flush... ";

    VideoEncoder encoder;
    VideoEncoderConfig config;
    config.width = 320;
    config.height = 240;
    config.fps = 30;
    config.bitrate = 500000;
    config.preset = "ultrafast";

    int ret = encoder.init(config);
    assert(ret == 0);

    // 编码几帧
    for (int i = 0; i < 5; i++) {
        AVFrame* frame = utils::createTestFrame(config.width, config.height, i);
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

// 测试解码器初始化
bool test_decoder_init() {
    std::cout << "Test: Decoder Init... ";

    VideoDecoder decoder;
    VideoDecoderConfig config;
    config.codec_id = AV_CODEC_ID_H264;

    int ret = decoder.init(config);
    assert(ret == 0);

    const char* name = decoder.getName();
    assert(name != nullptr);
    assert(std::string(name) == "h264");

    decoder.close();
    std::cout << "PASSED" << std::endl;
    return true;
}

// 测试编解码往返
bool test_encode_decode_roundtrip() {
    std::cout << "Test: Encode-Decode Round Trip... ";

    // 编码
    VideoEncoder encoder;
    VideoEncoderConfig enc_config;
    enc_config.width = 320;
    enc_config.height = 240;
    enc_config.fps = 30;
    enc_config.bitrate = 500000;
    enc_config.preset = "ultrafast";
    enc_config.max_b_frames = 0;

    int ret = encoder.init(enc_config);
    assert(ret == 0);

    AVFrame* original = utils::createTestFrame(enc_config.width, enc_config.height, 0);
    assert(original != nullptr);

    AVPacket* pkt = av_packet_alloc();
    ret = encoder.encode(original, pkt);
    assert(ret == 0);

    // 解码
    VideoDecoder decoder;
    VideoDecoderConfig dec_config;
    dec_config.codec_id = AV_CODEC_ID_H264;

    ret = decoder.init(dec_config);
    assert(ret == 0);

    AVFrame* decoded = av_frame_alloc();
    ret = decoder.decode(pkt, decoded);
    assert(ret == 0);

    // 验证尺寸
    assert(decoded->width == original->width);
    assert(decoded->height == original->height);

    av_frame_free(&original);
    av_frame_free(&decoded);
    av_packet_free(&pkt);
    encoder.close();
    decoder.close();

    std::cout << "PASSED" << std::endl;
    return true;
}

int main() {
    std::cout << "=== Video Codec Tests ===" << std::endl;

    int passed = 0;
    int failed = 0;

    if (test_encoder_init()) passed++; else failed++;
    if (test_encoder_double_init()) passed++; else failed++;
    if (test_encode_single_frame()) passed++; else failed++;
    if (test_encode_multiple_frames()) passed++; else failed++;
    if (test_encoder_flush()) passed++; else failed++;
    if (test_decoder_init()) passed++; else failed++;
    if (test_encode_decode_roundtrip()) passed++; else failed++;

    std::cout << "\n=== Test Results ===" << std::endl;
    std::cout << "Passed: " << passed << std::endl;
    std::cout << "Failed: " << failed << std::endl;
    std::cout << "Total: " << passed + failed << std::endl;

    return failed > 0 ? 1 : 0;
}
