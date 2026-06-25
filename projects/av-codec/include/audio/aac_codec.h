#pragma once

/**
 * @file aac_codec.h
 * @brief AAC 编解码器接口定义
 *
 * AAC (Advanced Audio Coding) 是 MPEG-2/MPEG-4 音频标准。
 * 主要特点：
 * - 比 MP3 更好的音质（相同比特率）
 * - 支持多声道（最多 48 声道）
 * - 支持多种采样率（8kHz - 96kHz）
 * - 低延迟模式（AAC-LD）
 * - 高效模式（HE-AAC, HE-AAC v2）
 */

#include <cstdint>
#include <vector>

namespace av_codec {

// AAC 常量定义
constexpr int AAC_MAX_CHANNELS = 48;       ///< 最大通道数
constexpr int AAC_MAX_SAMPLE_RATE = 96000; ///< 最大采样率
constexpr int AAC_FRAME_SIZE = 1024;       ///< 帧大小
constexpr int AAC_LD_FRAME_SIZE = 512;     ///< LD帧大小
constexpr int AAC_ELD_FRAME_SIZE = 480;    ///< ELD帧大小

/**
 * @brief AAC Profile
 */
enum class AACProfile : uint8_t {
    MAIN = 0,           ///< Main Profile
    LC = 1,             ///< Low Complexity
    SSR = 2,            ///< Scalable Sample Rate
    LTP = 3,            ///< Long Term Prediction
    HE_AAC = 4,         ///< HE-AAC (SBR)
    HE_AAC_v2 = 5,      ///< HE-AAC v2 (SBR+PS)
    LD = 6,             ///< Low Delay
    ELD = 7,            ///< Enhanced Low Delay
    XHE_AAC = 8         ///< Extended HE-AAC
};

/**
 * @brief AAC 输出格式
 */
enum class AACOutputFormat : uint8_t {
    RAW = 0,            ///< 原始AAC帧
    ADTS = 1,           ///< ADTS封装
    ADIF = 2,           ///< ADIF封装
    LATM = 3,           ///< LATM封装
    LOAS = 4            ///< LOAS封装
};

/**
 * @brief AAC 编码参数
 */
struct AACEncodeParams {
    int sample_rate = 44100;        ///< 采样率
    int channels = 2;               ///< 通道数
    int bitrate = 128000;           ///< 目标码率 (bps)
    AACProfile profile = AACProfile::LC; ///< Profile
    AACOutputFormat format = AACOutputFormat::ADTS; ///< 输出格式
    int afterburner = 1;            ///< 质量优化 (0=off, 1=on)
    int vbr = 0;                    ///< VBR模式 (0=CBR, 1-5=VBR)
    int cutoff = 0;                 ///< 频率截止 (0=auto)
    int transmux = 0;               ///< 传输复用
};

/**
 * @brief AAC 解码参数
 */
struct AACDecodeParams {
    int output_sample_rate = 0;     ///< 输出采样率 (0=原始)
    int output_channels = 0;        ///< 输出通道数 (0=原始)
    bool downmix = false;           ///< 下混到立体声
};

/**
 * @brief AAC 编码统计信息
 */
struct AACEncodeStats {
    int64_t total_bytes = 0;        ///< 总编码字节数
    int64_t total_frames = 0;       ///< 总编码帧数
    double avg_bitrate = 0.0;       ///< 平均码率
    double encoding_speed = 0.0;    ///< 编码速度（倍速）
};

/**
 * @brief AAC 编码器接口
 */
class IAACEncoder {
public:
    virtual ~IAACEncoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const AACEncodeParams& params) = 0;

    /**
     * @brief 编码一帧
     * @param pcm_data PCM数据
     * @param pcm_size PCM数据大小
     * @param out_data 输出AAC数据
     * @return 0成功，负数失败
     */
    virtual int encode(const int16_t* pcm_data, int pcm_size,
                      std::vector<uint8_t>& out_data) = 0;

    /**
     * @brief 浮点编码
     * @param float_data 浮点PCM数据
     * @param samples 采样数
     * @param out_data 输出AAC数据
     * @return 0成功，负数失败
     */
    virtual int encodeFloat(const float* float_data, int samples,
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
    virtual AACEncodeStats getStats() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief AAC 解码器接口
 */
class IAACDecoder {
public:
    virtual ~IAACDecoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 解码参数
     * @return 0成功，负数失败
     */
    virtual int init(const AACDecodeParams& params) = 0;

    /**
     * @brief 解码一帧
     * @param aac_data AAC数据
     * @param aac_size AAC数据大小
     * @param out_pcm 输出PCM数据
     * @return 0成功，负数失败
     */
    virtual int decode(const uint8_t* aac_data, int aac_size,
                      std::vector<int16_t>& out_pcm) = 0;

    /**
     * @brief 浮点解码
     * @param aac_data AAC数据
     * @param aac_size AAC数据大小
     * @param out_float 输出浮点PCM数据
     * @return 0成功，负数失败
     */
    virtual int decodeFloat(const uint8_t* aac_data, int aac_size,
                           std::vector<float>& out_float) = 0;

    /**
     * @brief 刷新解码器
     * @param out_pcm 输出剩余PCM数据
     * @return 0成功，负数失败
     */
    virtual int flush(std::vector<int16_t>& out_pcm) = 0;

    /**
     * @brief 关闭解码器
     */
    virtual void close() = 0;
};

} // namespace av_codec
