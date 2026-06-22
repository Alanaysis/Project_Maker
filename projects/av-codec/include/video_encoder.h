#pragma once

#include <vector>
#include "codec_types.h"

/**
 * @brief 视频编码器类
 *
 * 实现H.264视频编码功能
 */
class VideoEncoder {
public:
    VideoEncoder();
    ~VideoEncoder();

    /**
     * @brief 初始化编码器
     * @param config 编码器配置
     * @return 0成功，负数失败
     */
    int init(const VideoEncoderConfig& config);

    /**
     * @brief 编码一帧
     * @param frame 输入帧
     * @param pkt 输出数据包
     * @return 0成功，负数失败
     */
    int encode(const AVFrame* frame, AVPacket* pkt);

    /**
     * @brief 刷新编码器
     * @param packets 输出的数据包列表
     * @return 0成功，负数失败
     */
    int flush(std::vector<AVPacket*>& packets);

    /**
     * @brief 获取编码器名称
     * @return 编码器名称
     */
    const char* getName() const;

    /**
     * @brief 关闭编码器
     */
    void close();

private:
    AVCodecContext* codec_ctx_;     ///< 编解码器上下文
    const AVCodec* codec_;          ///< 编解码器
    bool initialized_;              ///< 是否已初始化
};
