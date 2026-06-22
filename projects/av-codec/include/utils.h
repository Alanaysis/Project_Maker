#pragma once

#include <string>
#include <vector>
#include "codec_types.h"

extern "C" {
#include <libavutil/frame.h>
}

/**
 * @brief 工具函数命名空间
 */
namespace utils {

    /**
     * @brief 读取YUV文件
     * @param filename 文件名
     * @param buffer 输出缓冲区
     * @param width 视频宽度
     * @param height 视频高度
     * @return 读取的字节数，负数失败
     */
    int readYUVFile(const char* filename, std::vector<uint8_t>& buffer,
                    int width, int height);

    /**
     * @brief 写入YUV文件
     * @param filename 文件名
     * @param frame 帧数据
     * @return 0成功，负数失败
     */
    int writeYUVFile(const char* filename, const AVFrame* frame);

    /**
     * @brief 创建测试帧
     * @param width 视频宽度
     * @param height 视频高度
     * @param frame_number 帧序号
     * @return 帧指针，nullptr失败
     */
    AVFrame* createTestFrame(int width, int height, int frame_number);

    /**
     * @brief 创建测试音频帧
     * @param sample_rate 采样率
     * @param channels 声道数
     * @param nb_samples 采样数
     * @param frame_number 帧序号
     * @return 帧指针，nullptr失败
     */
    AVFrame* createTestAudioFrame(int sample_rate, int channels,
                                   int nb_samples, int frame_number);

    /**
     * @brief 保存PPM图像
     * @param filename 文件名
     * @param frame 帧数据
     * @return 0成功，负数失败
     */
    int savePPM(const char* filename, const AVFrame* frame);

    /**
     * @brief 打印帧信息
     * @param frame 帧数据
     */
    void printFrameInfo(const AVFrame* frame);

    /**
     * @brief 打印数据包信息
     * @param pkt 数据包
     */
    void printPacketInfo(const AVPacket* pkt);

} // namespace utils
