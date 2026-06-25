#pragma once

/**
 * @file container.h
 * @brief 容器格式接口定义
 *
 * 支持的容器格式：
 * - MP4：最流行的容器格式，支持 H.264/H.265/AAC
 * - MKV：开源容器格式，支持几乎所有编码
 * - AVI：经典容器格式，兼容性好
 * - FLV：Flash视频格式，流媒体常用
 * - TS：传输流格式，广播/流媒体专用
 */

#include <cstdint>
#include <vector>
#include <string>
#include <memory>

namespace av_codec {

/**
 * @brief 容器格式类型
 */
enum class ContainerFormat : uint8_t {
    MP4 = 0,    ///< MP4格式
    MKV = 1,    ///< MKV格式
    AVI = 2,    ///< AVI格式
    FLV = 3,    ///< FLV格式
    TS = 4,     ///< TS格式
    WEBM = 5,   ///< WebM格式
    OGG = 6,    ///< Ogg格式
    MOV = 7     ///< MOV格式
};

/**
 * @brief 流类型
 */
enum class StreamType : uint8_t {
    VIDEO = 0,  ///< 视频流
    AUDIO = 1,  ///< 音频流
    SUBTITLE = 2, ///< 字幕流
    DATA = 3    ///< 数据流
};

/**
 * @brief 视频流信息
 */
struct VideoStreamInfo {
    int codec_id = 0;           ///< 编码ID
    int width = 0;              ///< 视频宽度
    int height = 0;             ///< 视频高度
    int fps_num = 30;           ///< 帧率分子
    int fps_den = 1;            ///< 帧率分母
    int64_t bitrate = 0;        ///< 比特率
    int profile = 0;            ///< 编码Profile
    int level = 0;              ///< 编码Level
    int bits_per_sample = 8;    ///< 每样本比特数
    std::vector<uint8_t> extra_data; ///< 额外数据
};

/**
 * @brief 音频流信息
 */
struct AudioStreamInfo {
    int codec_id = 0;           ///< 编码ID
    int sample_rate = 0;        ///< 采样率
    int channels = 0;           ///< 通道数
    int bits_per_sample = 16;   ///< 每样本比特数
    int64_t bitrate = 0;        ///< 比特率
    int block_align = 0;        ///< 块对齐
    std::vector<uint8_t> extra_data; ///< 额外数据
};

/**
 * @brief 字幕流信息
 */
struct SubtitleStreamInfo {
    int codec_id = 0;           ///< 编码ID
    std::string language;       ///< 语言
};

/**
 * @brief 流信息
 */
struct StreamInfo {
    int index = 0;              ///< 流索引
    StreamType type = StreamType::VIDEO; ///< 流类型
    int64_t duration = 0;       ///< 持续时间（微秒）
    int64_t start_time = 0;     ///< 开始时间
    std::string language;       ///< 语言
    std::string title;          ///< 标题

    union {
        VideoStreamInfo video;  ///< 视频流信息
        AudioStreamInfo audio;  ///< 音频流信息
        SubtitleStreamInfo subtitle; ///< 字幕流信息
    };
};

/**
 * @brief 数据包
 */
struct AVPacketData {
    int stream_index = 0;       ///< 流索引
    int64_t pts = 0;            ///< 显示时间戳
    int64_t dts = 0;            ///< 解码时间戳
    int64_t duration = 0;       ///< 持续时间
    int64_t pos = 0;            ///< 位置
    std::vector<uint8_t> data;  ///< 数据
    bool keyframe = false;      ///< 是否关键帧
};

/**
 * @brief 复用器接口
 */
class IMuxer {
public:
    virtual ~IMuxer() = default;

    /**
     * @brief 初始化复用器
     * @param filename 输出文件名
     * @param format 容器格式
     * @return 0成功，负数失败
     */
    virtual int init(const char* filename, ContainerFormat format) = 0;

    /**
     * @brief 添加视频流
     * @param info 视频流信息
     * @return 流索引，负数失败
     */
    virtual int addVideoStream(const VideoStreamInfo& info) = 0;

    /**
     * @brief 添加音频流
     * @param info 音频流信息
     * @return 流索引，负数失败
     */
    virtual int addAudioStream(const AudioStreamInfo& info) = 0;

    /**
     * @brief 写入文件头
     * @return 0成功，负数失败
     */
    virtual int writeHeader() = 0;

    /**
     * @brief 写入数据包
     * @param pkt 数据包
     * @return 0成功，负数失败
     */
    virtual int writePacket(const AVPacketData& pkt) = 0;

    /**
     * @brief 写入文件尾
     * @return 0成功，负数失败
     */
    virtual int writeTrailer() = 0;

    /**
     * @brief 关闭复用器
     */
    virtual void close() = 0;
};

/**
 * @brief 解复用器接口
 */
class IDemuxer {
public:
    virtual ~IDemuxer() = default;

    /**
     * @brief 初始化解复用器
     * @param filename 输入文件名
     * @return 0成功，负数失败
     */
    virtual int init(const char* filename) = 0;

    /**
     * @brief 获取流数量
     * @return 流数量
     */
    virtual int getStreamCount() const = 0;

    /**
     * @brief 获取流信息
     * @param index 流索引
     * @return 流信息
     */
    virtual const StreamInfo* getStreamInfo(int index) const = 0;

    /**
     * @brief 读取数据包
     * @param pkt 输出数据包
     * @return 0成功，负数失败
     */
    virtual int readPacket(AVPacketData& pkt) = 0;

    /**
     * @brief 定位到指定时间
     * @param timestamp 时间戳（微秒）
     * @param stream_index 流索引
     * @return 0成功，负数失败
     */
    virtual int seek(int64_t timestamp, int stream_index = -1) = 0;

    /**
     * @brief 关闭解复用器
     */
    virtual void close() = 0;
};

} // namespace av_codec
