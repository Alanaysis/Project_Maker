#include <iostream>
#include <vector>
#include "audio_encoder.h"
#include "utils.h"

/**
 * @brief 音频编码示例
 *
 * 演示如何使用AudioEncoder进行AAC编码
 */
int main(int argc, char* argv[]) {
    std::cout << "=== Audio Encoder Example ===" << std::endl;

    // 配置编码器
    AudioEncoderConfig config;
    config.sample_rate = 44100;
    config.channels = 2;
    config.bitrate = 128000;
    config.sample_fmt = AV_SAMPLE_FMT_FLTP;

    // 创建编码器
    AudioEncoder encoder;
    int ret = encoder.init(config);
    if (ret < 0) {
        std::cerr << "Failed to initialize encoder" << std::endl;
        return -1;
    }

    std::cout << "Encoder: " << encoder.getName() << std::endl;
    std::cout << "Sample Rate: " << config.sample_rate << " Hz" << std::endl;
    std::cout << "Channels: " << config.channels << std::endl;
    std::cout << "Bitrate: " << config.bitrate << " bps" << std::endl;

    // 编码循环
    const int num_frames = 50;
    const int nb_samples = 1024;  // AAC帧大小
    std::vector<AVPacket*> packets;

    std::cout << "\nEncoding " << num_frames << " frames..." << std::endl;

    for (int i = 0; i < num_frames; i++) {
        // 创建测试音频帧
        AVFrame* frame = utils::createTestAudioFrame(
            config.sample_rate, config.channels, nb_samples, i);
        if (!frame) {
            std::cerr << "Failed to create audio frame " << i << std::endl;
            continue;
        }

        // 编码
        AVPacket* pkt = av_packet_alloc();
        ret = encoder.encode(frame, pkt);
        if (ret < 0) {
            if (ret == AVERROR(EAGAIN)) {
                av_packet_free(&pkt);
                av_frame_free(&frame);
                continue;
            }
            std::cerr << "Failed to encode frame " << i << std::endl;
            av_packet_free(&pkt);
            av_frame_free(&frame);
            continue;
        }

        packets.push_back(pkt);
        std::cout << "Encoded frame " << i << ": size=" << pkt->size
                  << " pts=" << pkt->pts << std::endl;

        av_frame_free(&frame);
    }

    // 刷新编码器
    std::vector<AVPacket*> flush_packets;
    encoder.flush(flush_packets);
    packets.insert(packets.end(), flush_packets.begin(), flush_packets.end());

    std::cout << "\nTotal packets: " << packets.size() << std::endl;

    // 计算统计信息
    int total_size = 0;
    for (const auto* pkt : packets) {
        total_size += pkt->size;
    }

    std::cout << "Total size: " << total_size << " bytes" << std::endl;
    std::cout << "Average packet size: " << total_size / packets.size() << " bytes" << std::endl;

    // 计算音频时长
    double duration = (double)(num_frames * nb_samples) / config.sample_rate;
    std::cout << "Audio duration: " << duration << " seconds" << std::endl;
    std::cout << "Compression ratio: "
              << (double)(num_frames * nb_samples * config.channels * 2) / total_size
              << ":1" << std::endl;

    // 清理
    for (auto* pkt : packets) {
        av_packet_free(&pkt);
    }
    encoder.close();

    std::cout << "\n=== Example completed ===" << std::endl;
    return 0;
}
