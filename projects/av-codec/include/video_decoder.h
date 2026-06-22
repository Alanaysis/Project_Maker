#pragma once

#include "codec_types.h"

/**
 * @brief 视频解码器类
 *
 * 实现H.264视频解码功能
 */
class VideoDecoder {
public:
    VideoDecoder();
    ~VideoDecoder();

    /**
     * @brief 初始化解码器
     * @param config 解码器配置
     * @return 0成功，负数失败
     */
    int init(const VideoDecoderConfig& config);

    /**
     * @brief 解码一个数据包
     * @param pkt 输入数据包
     * @param frame 输出帧
     * @return 0成功，负数失败
     */
    int decode(const AVPacket* pkt, AVFrame* frame);

    /**
     * @brief 刷新解码器
     * @param frame 输出帧
     * @return 0成功，负数失败
     */
    int flush(AVFrame* frame);

    /**
     * @brief 获取解码器名称
     * @return 解码器名称
     */
    const char* getName() const;

    /**
     * @brief 关闭解码器
     */
    void close();

private:
    AVCodecContext* codec_ctx_;     ///< 编解码器上下文
    const AVCodec* codec_;          ///< 编解码器
    bool initialized_;              ///< 是否已初始化
};
