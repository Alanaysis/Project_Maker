#include "utils.h"
#include <iostream>
#include <fstream>
#include <cmath>

extern "C" {
#include <libavutil/imgutils.h>
}

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace utils {

int readYUVFile(const char* filename, std::vector<uint8_t>& buffer,
                int width, int height) {
    // 计算YUV420P大小
    int y_size = width * height;
    int uv_size = (width / 2) * (height / 2);
    int total_size = y_size + uv_size * 2;

    // 读取文件
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Could not open file: " << filename << std::endl;
        return -1;
    }

    buffer.resize(total_size);
    file.read(reinterpret_cast<char*>(buffer.data()), total_size);

    return file.gcount();
}

int writeYUVFile(const char* filename, const AVFrame* frame) {
    std::ofstream file(filename, std::ios::binary | std::ios::app);
    if (!file.is_open()) {
        std::cerr << "Could not open file: " << filename << std::endl;
        return -1;
    }

    // 写入Y分量
    for (int y = 0; y < frame->height; y++) {
        file.write(reinterpret_cast<const char*>(frame->data[0] + y * frame->linesize[0]),
                   frame->width);
    }

    // 写入U分量
    for (int y = 0; y < frame->height / 2; y++) {
        file.write(reinterpret_cast<const char*>(frame->data[1] + y * frame->linesize[1]),
                   frame->width / 2);
    }

    // 写入V分量
    for (int y = 0; y < frame->height / 2; y++) {
        file.write(reinterpret_cast<const char*>(frame->data[2] + y * frame->linesize[2]),
                   frame->width / 2);
    }

    return 0;
}

AVFrame* createTestFrame(int width, int height, int frame_number) {
    AVFrame* frame = av_frame_alloc();
    if (!frame) {
        return nullptr;
    }

    frame->format = AV_PIX_FMT_YUV420P;
    frame->width = width;
    frame->height = height;

    int ret = av_frame_get_buffer(frame, 0);
    if (ret < 0) {
        av_frame_free(&frame);
        return nullptr;
    }

    // 填充Y分量 (灰度渐变 + 运动)
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            // 创建移动的渐变效果
            int value = ((x + frame_number * 5) % 256 + (y + frame_number * 3) % 256) / 2;
            frame->data[0][y * frame->linesize[0] + x] = value;
        }
    }

    // 填充U分量
    for (int y = 0; y < height / 2; y++) {
        for (int x = 0; x < width / 2; x++) {
            frame->data[1][y * frame->linesize[1] + x] = 128;
        }
    }

    // 填充V分量
    for (int y = 0; y < height / 2; y++) {
        for (int x = 0; x < width / 2; x++) {
            frame->data[2][y * frame->linesize[2] + x] = 128;
        }
    }

    frame->pts = frame_number;

    return frame;
}

AVFrame* createTestAudioFrame(int sample_rate, int channels,
                               int nb_samples, int frame_number) {
    AVFrame* frame = av_frame_alloc();
    if (!frame) {
        return nullptr;
    }

    frame->format = AV_SAMPLE_FMT_FLTP;
    frame->channels = channels;
    frame->channel_layout = av_get_default_channel_layout(channels);
    frame->sample_rate = sample_rate;
    frame->nb_samples = nb_samples;

    int ret = av_frame_get_buffer(frame, 0);
    if (ret < 0) {
        av_frame_free(&frame);
        return nullptr;
    }

    // 填充正弦波数据
    double time_offset = (double)frame_number * nb_samples / sample_rate;
    for (int ch = 0; ch < channels; ch++) {
        float* data = (float*)frame->data[ch];
        for (int i = 0; i < nb_samples; i++) {
            double t = time_offset + (double)i / sample_rate;
            // 440Hz正弦波，不同声道略有相位差
            data[i] = (float)(sin(2 * M_PI * 440 * t + ch * 0.1) * 0.5);
        }
    }

    frame->pts = frame_number * nb_samples;

    return frame;
}

int savePPM(const char* filename, const AVFrame* frame) {
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        return -1;
    }

    // PPM头
    file << "P6\n" << frame->width << " " << frame->height << "\n255\n";

    // YUV转RGB并写入
    for (int y = 0; y < frame->height; y++) {
        for (int x = 0; x < frame->width; x++) {
            int Y = frame->data[0][y * frame->linesize[0] + x];
            int U = frame->data[1][(y/2) * frame->linesize[1] + (x/2)] - 128;
            int V = frame->data[2][(y/2) * frame->linesize[2] + (x/2)] - 128;

            int R = (int)(Y + 1.402 * V);
            int G = (int)(Y - 0.344 * U - 0.714 * V);
            int B = (int)(Y + 1.772 * U);

            R = std::max(0, std::min(255, R));
            G = std::max(0, std::min(255, G));
            B = std::max(0, std::min(255, B));

            file.put((char)R);
            file.put((char)G);
            file.put((char)B);
        }
    }

    return 0;
}

void printFrameInfo(const AVFrame* frame) {
    std::cout << "Frame Info:" << std::endl;
    std::cout << "  Format: " << frame->format << std::endl;
    std::cout << "  Width: " << frame->width << std::endl;
    std::cout << "  Height: " << frame->height << std::endl;
    std::cout << "  PTS: " << frame->pts << std::endl;
    std::cout << "  Key Frame: " << (frame->key_frame ? "Yes" : "No") << std::endl;
}

void printPacketInfo(const AVPacket* pkt) {
    std::cout << "Packet Info:" << std::endl;
    std::cout << "  Size: " << pkt->size << std::endl;
    std::cout << "  PTS: " << pkt->pts << std::endl;
    std::cout << "  DTS: " << pkt->dts << std::endl;
    std::cout << "  Duration: " << pkt->duration << std::endl;
    std::cout << "  Key Packet: " << (pkt->flags & AV_PKT_FLAG_KEY ? "Yes" : "No") << std::endl;
}

} // namespace utils
