#pragma once

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/pixfmt.h>
#include <libavutil/samplefmt.h>
}

/**
 * @brief 视频编码器配置
 */
struct VideoEncoderConfig {
    int width = 1920;                           ///< 视频宽度
    int height = 1080;                          ///< 视频高度
    int fps = 30;                               ///< 帧率
    int64_t bitrate = 2000000;                  ///< 码率 (bps)
    int gop_size = 30;                          ///< GOP大小
    int max_b_frames = 3;                       ///< 最大B帧数
    AVPixelFormat pix_fmt = AV_PIX_FMT_YUV420P; ///< 像素格式
    const char* preset = "medium";              ///< 编码预设
    const char* profile = "high";               ///< 编码档次
};

/**
 * @brief 视频解码器配置
 */
struct VideoDecoderConfig {
    AVCodecID codec_id = AV_CODEC_ID_H264;     ///< 编码ID
    int width = 0;                              ///< 视频宽度
    int height = 0;                             ///< 视频高度
    AVPixelFormat pix_fmt = AV_PIX_FMT_YUV420P; ///< 像素格式
};

/**
 * @brief 音频编码器配置
 */
struct AudioEncoderConfig {
    int sample_rate = 44100;                    ///< 采样率
    int channels = 2;                           ///< 声道数
    int64_t bitrate = 128000;                   ///< 码率 (bps)
    AVSampleFormat sample_fmt = AV_SAMPLE_FMT_FLTP; ///< 采样格式
};

/**
 * @brief 音频解码器配置
 */
struct AudioDecoderConfig {
    AVCodecID codec_id = AV_CODEC_ID_AAC;      ///< 编码ID
    int sample_rate = 44100;                    ///< 采样率
    int channels = 2;                           ///< 声道数
    AVSampleFormat sample_fmt = AV_SAMPLE_FMT_FLTP; ///< 采样格式
};

/**
 * @brief 复用器配置
 */
struct MuxerConfig {
    const char* filename = nullptr;             ///< 输出文件名
    const char* format = nullptr;               ///< 容器格式
};

/**
 * @brief 解复用器配置
 */
struct DemuxerConfig {
    const char* filename = nullptr;             ///< 输入文件名
};
