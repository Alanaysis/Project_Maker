#pragma once

#include "codec_types.h"

/**
 * @brief 解复用器类
 *
 * 实现音视频解封装功能
 */
class Demuxer {
public:
    Demuxer();
    ~Demuxer();

    /**
     * @brief 初始化解复用器
     * @param config 解复用器配置
     * @return 0成功，负数失败
     */
    int init(const DemuxerConfig& config);

    /**
     * @brief 打开输入文件
     * @param filename 文件名
     * @return 0成功，负数失败
     */
    int openInput(const char* filename);

    /**
     * @brief 查找流信息
     * @return 0成功，负数失败
     */
    int findStreamInfo();

    /**
     * @brief 获取流数量
     * @return 流数量
     */
    int getStreamCount() const;

    /**
     * @brief 获取流信息
     * @param index 流索引
     * @return 流信息指针
     */
    const AVStream* getStream(int index) const;

    /**
     * @brief 读取数据包
     * @param pkt 输出数据包
     * @return 0成功，负数失败
     */
    int readPacket(AVPacket* pkt);

    /**
     * @brief 关闭解复用器
     */
    void close();

private:
    AVFormatContext* fmt_ctx_;      ///< 格式上下文
    bool initialized_;              ///< 是否已初始化
};
