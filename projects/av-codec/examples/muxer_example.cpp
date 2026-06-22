#include <iostream>
#include <vector>
#include "video_encoder.h"
#include "audio_encoder.h"
#include "muxer.h"
#include "utils.h"

/**
 * @brief 复用器示例
 *
 * 演示如何将音视频流封装到MP4文件
 */
int main(int argc, char* argv[]) {
    std::cout << "=== Muxer Example ===" << std::endl;

    const char* output_file = "output.mp4";
    if (argc > 1) {
        output_file = argv[1];
    }

    // 初始化视频编码器
    VideoEncoderConfig video_config;
    video_config.width = 320;
    video_config.height = 240;
    video_config.fps = 30;
    video_config.bitrate = 500000;
    video_config.gop_size = 30;
    video_config.max_b_frames = 0;
    video_config.preset = "ultrafast";

    VideoEncoder video_encoder;
    int ret = video_encoder.init(video_config);
    if (ret < 0) {
        std::cerr << "Failed to initialize video encoder" << std::endl;
        return -1;
    }

    // 初始化音频编码器
    AudioEncoderConfig audio_config;
    audio_config.sample_rate = 44100;
    audio_config.channels = 2;
    audio_config.bitrate = 128000;

    AudioEncoder audio_encoder;
    ret = audio_encoder.init(audio_config);
    if (ret < 0) {
        std::cerr << "Failed to initialize audio encoder" << std::endl;
        return -1;
    }

    // 初始化复用器
    MuxerConfig muxer_config;
    muxer_config.filename = output_file;
    muxer_config.format = "mp4";

    Muxer muxer;
    ret = muxer.init(muxer_config);
    if (ret < 0) {
        std::cerr << "Failed to initialize muxer" << std::endl;
        return -1;
    }

    // 添加流
    // 注意：这里需要获取编码器上下文，简化处理
    // 实际应用中需要通过编码器获取上下文

    std::cout << "Video encoder: " << video_encoder.getName() << std::endl;
    std::cout << "Audio encoder: " << audio_encoder.getName() << std::endl;
    std::cout << "Output file: " << output_file << std::endl;

    // 模拟编码和封装过程
    const int num_frames = 30;
    std::cout << "\nEncoding and muxing " << num_frames << " frames..." << std::endl;

    for (int i = 0; i < num_frames; i++) {
        // 创建视频帧
        AVFrame* video_frame = utils::createTestFrame(
            video_config.width, video_config.height, i);

        // 创建音频帧
        AVFrame* audio_frame = utils::createTestAudioFrame(
            audio_config.sample_rate, audio_config.channels, 1024, i);

        // 编码视频
        AVPacket* video_pkt = av_packet_alloc();
        ret = video_encoder.encode(video_frame, video_pkt);
        if (ret == 0) {
            std::cout << "Video frame " << i << ": size=" << video_pkt->size << std::endl;
        }
        av_packet_free(&video_pkt);

        // 编码音频
        AVPacket* audio_pkt = av_packet_alloc();
        ret = audio_encoder.encode(audio_frame, audio_pkt);
        if (ret == 0) {
            std::cout << "Audio frame " << i << ": size=" << audio_pkt->size << std::endl;
        }
        av_packet_free(&audio_pkt);

        av_frame_free(&video_frame);
        av_frame_free(&audio_frame);
    }

    // 清理
    video_encoder.close();
    audio_encoder.close();
    muxer.close();

    std::cout << "\n=== Example completed ===" << std::endl;
    std::cout << "Note: This is a simplified example." << std::endl;
    std::cout << "In a real application, you would:" << std::endl;
    std::cout << "1. Get codec contexts from encoders" << std::endl;
    std::cout << "2. Add streams to muxer" << std::endl;
    std::cout << "3. Write header" << std::endl;
    std::cout << "4. Write packets with proper timestamps" << std::endl;
    std::cout << "5. Write trailer" << std::endl;

    return 0;
}
