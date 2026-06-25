#pragma once

/**
 * @file vorbis_codec.h
 * @brief Vorbis 编解码器接口定义
 *
 * Vorbis 是一个开源的音频编码格式。
 * 主要特点：
 * - 完全开源免费
 * - 高质量音频编码
 * - 支持多声道
 * - 用于 Ogg 容器格式
 */

#include <cstdint>
#include <vector>

namespace av_codec {

// Vorbis 常量定义
constexpr int VORBIS_MAX_CHANNELS = 255;   ///< 最大通道数
constexpr int VORBIS_BLOCK_SIZE_MIN = 64;  ///< 最小块大小
constexpr int VORBIS_BLOCK_SIZE_MAX = 8192; ///< 最大块大小

/**
 * @brief Vorbis 编码参数
 */
struct VorbisEncodeParams {
    int sample_rate = 44100;        ///< 采样率
    int channels = 2;               ///< 通道数
    float quality = 0.4f;           ///< 质量 (-0.1 到 1.0)
    int bitrate_min = 0;            ///< 最小比特率
    int bitrate_nominal = 128000;   ///< 标称比特率
    int bitrate_max = 0;            ///< 最大比特率
    int block_size_min = 512;       ///< 最小块大小
    int block_size_max = 4096;      ///< 最大块大小
};

/**
 * @brief Vorbis 解码参数
 */
struct VorbisDecodeParams {
    // Vorbis 解码参数较少
};

/**
 * @brief Vorbis 编码统计信息
 */
struct VorbisEncodeStats {
    int64_t total_bytes = 0;        ///< 总编码字节数
    int64_t total_frames = 0;       ///< 总编码帧数
    double avg_bitrate = 0.0;       ///< 平均比特率
};

/**
 * @brief Vorbis 编码器接口
 */
class IVorbisEncoder {
public:
    virtual ~IVorbisEncoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const VorbisEncodeParams& params) = 0;

    /**
     * @brief 编码一帧
     * @param float_data 浮点PCM数据
     * @param samples 采样数
     * @param out_data 输出Vorbis数据
     * @return 0成功，负数失败
     */
    virtual int encode(const float* float_data, int samples,
                      std::vector<uint8_t>& out_data) = 0;

    /**
     * @brief 刷新编码器
     * @param out_data 输出剩余数据
     * @return 0成功，负数失败
     */
    virtual int flush(std::vector<uint8_t>& out_data) = 0;

    /**
     * @brief 获取编码统计信息
     * @return 统计信息
     */
    virtual VorbisEncodeStats getStats() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief Vorbis 解码器接口
 */
class IVorbisDecoder {
public:
    virtual ~IVorbisDecoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 解码参数
     * @return 0成功，负数失败
     */
    virtual int init(const VorbisDecodeParams& params) = 0;

    /**
     * @brief 解码一帧
     * @param vorbis_data Vorbis数据
     * @param vorbis_size Vorbis数据大小
     * @param out_float 输出浮点PCM数据
     * @return 0成功，负数失败
     */
    virtual int decode(const uint8_t* vorbis_data, int vorbis_size,
                      std::vector<float>& out_float) = 0;

    /**
     * @brief 关闭解码器
     */
    virtual void close() = 0;
};

} // namespace av_codec
