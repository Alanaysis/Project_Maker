#pragma once

/**
 * @file opus_codec.h
 * @brief Opus 编解码器接口定义
 *
 * Opus 是一个开放的、免版税的音频编码格式。
 * 主要特点：
 * - 从低比特率语音到高质量音乐
 * - 低延迟（最小 2.5ms）
 * - 动态比特率调整
 * - 广泛用于 WebRTC、VoIP、流媒体
 */

#include <cstdint>
#include <vector>

namespace av_codec {

// Opus 常量定义
constexpr int OPUS_MAX_CHANNELS = 2;       ///< 最大通道数
constexpr int OPUS_MAX_SAMPLE_RATE = 48000; ///< 最大采样率
constexpr int OPUS_FRAME_SIZE_MIN = 120;   ///< 最小帧大小
constexpr int OPUS_FRAME_SIZE_MAX = 5760;  ///< 最大帧大小

/**
 * @brief Opus 应用类型
 */
enum class OpusApplication : uint8_t {
    VOIP = 0,           ///< VoIP语音
    AUDIO = 1,          ///< 音频
    RESTRICTED_LOWDELAY = 2 ///< 限制低延迟
};

/**
 * @brief Opus 信号类型
 */
enum class OpusSignal : uint8_t {
    AUTO = -1,          ///< 自动
    VOICE = 0,          ///< 语音
    MUSIC = 1           ///< 音乐
};

/**
 * @brief Opus 带宽
 */
enum class OpusBandwidth : uint8_t {
    NARROWBAND = 0,     ///< 窄带 (4kHz)
    MEDIUMBAND = 1,     ///< 中带 (6kHz)
    WIDEBAND = 2,       ///< 宽带 (8kHz)
    SUPERWIDEBAND = 3,  ///< 超宽带 (12kHz)
    FULLBAND = 4        ///< 全带 (20kHz)
};

/**
 * @brief Opus 编码参数
 */
struct OpusEncodeParams {
    int sample_rate = 48000;        ///< 采样率
    int channels = 2;               ///< 通道数
    int bitrate = 64000;            ///< 目标码率 (bps)
    OpusApplication application = OpusApplication::AUDIO; ///< 应用类型
    OpusSignal signal = OpusSignal::AUTO; ///< 信号类型
    OpusBandwidth bandwidth = OpusBandwidth::AUTO; ///< 带宽
    int complexity = 10;            ///< 复杂度 (0-10)
    bool dtx = false;               ///< 不连续传输
    bool inband_fec = false;        ///< 带内FEC
    int packet_loss_perc = 0;       ///< 丢包率百分比
    int lsb_depth = 24;             ///< LSB深度
    int prediction_disabled = 0;    ///< 禁用预测
};

/**
 * @brief Opus 解码参数
 */
struct OpusDecodeParams {
    bool decode_fec = false;        ///< 使用FEC解码
    int gain = 0;                   ///< 增益 (dB)
    int plc = 0;                    ///< 丢包隐藏
};

/**
 * @brief Opus 编码统计信息
 */
struct OpusEncodeStats {
    int64_t total_bytes = 0;        ///< 总编码字节数
    int64_t total_frames = 0;       ///< 总编码帧数
    double avg_bitrate = 0.0;       ///< 平均码率
    double encoding_speed = 0.0;    ///< 编码速度
};

/**
 * @brief Opus 编码器接口
 */
class IOpusEncoder {
public:
    virtual ~IOpusEncoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const OpusEncodeParams& params) = 0;

    /**
     * @brief 编码一帧
     * @param pcm_data PCM数据
     * @param frame_size 帧大小
     * @param out_data 输出Opus数据
     * @return 0成功，负数失败
     */
    virtual int encode(const int16_t* pcm_data, int frame_size,
                      std::vector<uint8_t>& out_data) = 0;

    /**
     * @brief 浮点编码
     * @param float_data 浮点PCM数据
     * @param frame_size 帧大小
     * @param out_data 输出Opus数据
     * @return 0成功，负数失败
     */
    virtual int encodeFloat(const float* float_data, int frame_size,
                           std::vector<uint8_t>& out_data) = 0;

    /**
     * @brief 获取编码统计信息
     * @return 统计信息
     */
    virtual OpusEncodeStats getStats() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief Opus 解码器接口
 */
class IOpusDecoder {
public:
    virtual ~IOpusDecoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 解码参数
     * @return 0成功，负数失败
     */
    virtual int init(const OpusDecodeParams& params) = 0;

    /**
     * @brief 解码一帧
     * @param opus_data Opus数据
     * @param opus_size Opus数据大小
     * @param out_pcm 输出PCM数据
     * @param frame_size 请求的帧大小
     * @return 0成功，负数失败
     */
    virtual int decode(const uint8_t* opus_data, int opus_size,
                      std::vector<int16_t>& out_pcm, int frame_size) = 0;

    /**
     * @brief 浮点解码
     * @param opus_data Opus数据
     * @param opus_size Opus数据大小
     * @param out_float 输出浮点PCM数据
     * @param frame_size 请求的帧大小
     * @return 0成功，负数失败
     */
    virtual int decodeFloat(const uint8_t* opus_data, int opus_size,
                           std::vector<float>& out_float, int frame_size) = 0;

    /**
     * @brief 关闭解码器
     */
    virtual void close() = 0;
};

} // namespace av_codec
