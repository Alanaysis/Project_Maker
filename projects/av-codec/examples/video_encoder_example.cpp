#include <iostream>
#include <vector>
#include "video_encoder.h"
#include "video_decoder.h"
#include "utils.h"

/**
 * @brief 视频编码示例
 *
 * 演示如何使用VideoEncoder进行H.264编码
 */
int main(int argc, char* argv[]) {
    std::cout << "=== Video Encoder Example ===" << std::endl;

    // 配置编码器
    VideoEncoderConfig config;
    config.width = 320;
    config.height = 240;
    config.fps = 30;
    config.bitrate = 500000;
    config.gop_size = 30;
    config.max_b_frames = 0;
    config.preset = "ultrafast";

    // 创建编码器
    VideoEncoder encoder;
    int ret = encoder.init(config);
    if (ret < 0) {
        std::cerr << "Failed to initialize encoder" << std::endl;
        return -1;
    }

    std::cout << "Encoder: " << encoder.getName() << std::endl;
    std::cout << "Resolution: " << config.width << "x" << config.height << std::endl;
    std::cout << "FPS: " << config.fps << std::endl;
    std::cout << "Bitrate: " << config.bitrate << " bps" << std::endl;

    // 编码循环
    const int num_frames = 30;
    std::vector<AVPacket*> packets;

    std::cout << "\nEncoding " << num_frames << " frames..." << std::endl;

    for (int i = 0; i < num_frames; i++) {
        // 创建测试帧
        AVFrame* frame = utils::createTestFrame(config.width, config.height, i);
        if (!frame) {
            std::cerr << "Failed to create frame " << i << std::endl;
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
                  << " key=" << (pkt->flags & AV_PKT_FLAG_KEY ? "Yes" : "No")
                  << std::endl;

        av_frame_free(&frame);
    }

    // 刷新编码器
    std::vector<AVPacket*> flush_packets;
    encoder.flush(flush_packets);
    packets.insert(packets.end(), flush_packets.begin(), flush_packets.end());

    std::cout << "\nTotal packets: " << packets.size() << std::endl;

    // 计算统计信息
    int total_size = 0;
    int key_frames = 0;
    for (const auto* pkt : packets) {
        total_size += pkt->size;
        if (pkt->flags & AV_PKT_FLAG_KEY) {
            key_frames++;
        }
    }

    std::cout << "Total size: " << total_size << " bytes" << std::endl;
    std::cout << "Key frames: " << key_frames << std::endl;
    std::cout << "Average packet size: " << total_size / packets.size() << " bytes" << std::endl;

    // 清理
    for (auto* pkt : packets) {
        av_packet_free(&pkt);
    }
    encoder.close();

    std::cout << "\n=== Example completed ===" << std::endl;
    return 0;
}
