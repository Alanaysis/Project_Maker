#pragma once

#include "codec_types.h"

/**
 * @brief 复用器类
 *
 * 实现音视频封装功能
 */
class Muxer {
public:
    Muxer();
    ~Muxer();

    /**
     * @brief 初始化复用器
     * @param config 复用器配置
     * @return 0成功，负数失败
     */
    int init(const MuxerConfig& config);

    /**
     * @brief 添加流
     * @param codec_ctx 编解码器上下文
     * @return 流索引，负数失败
     */
    int addStream(const AVCodecContext* codec_ctx);

    /**
     * @brief 写入文件头
     * @return 0成功，负数失败
     */
    int writeHeader();

    /**
     * @brief 写入数据包
     * @param pkt 数据包
     * @return 0成功，负数失败
     */
    int writePacket(AVPacket* pkt);

    /**
     * @brief 写入文件尾
     * @return 0成功，负数失败
     */
    int writeTrailer();

    /**
     * @brief 关闭复用器
     */
    void close();

private:
    AVFormatContext* fmt_ctx_;      ///< 格式上下文
    bool initialized_;              ///< 是否已初始化
    bool header_written_;           ///< 是否已写入文件头
};
