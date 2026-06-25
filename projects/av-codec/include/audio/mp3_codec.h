#pragma once

/**
 * @file mp3_codec.h
 * @brief MP3 编解码器接口定义
 *
 * MP3 (MPEG-1 Audio Layer III) 是最广泛使用的音频编码格式。
 * 主要特点：
 * - 广泛的兼容性
 * - 比特率范围：8-320 kbps
 * - 支持 CBR/VBR/ABR 模式
 * - 心理声学模型优化
 */

#include <cstdint>
#include <vector>

namespace av_codec {

// MP3 常量定义
constexpr int MP3_MAX_CHANNELS = 2;        ///< 最大通道数
constexpr int MP3_FRAME_SIZE = 1152;       ///< 帧大小
constexpr int MP3_SAMPLE_RATE_COUNT = 3;   ///< 采样率版本数
constexpr int MP3_BITRATE_COUNT = 15;      ///< 比特率数

/**
 * @brief MP3 版本
 */
enum class MP3Version : uint8_t {
    MPEG1 = 0,      ///< MPEG-1
    MPEG2 = 1,      ///< MPEG-2
    MPEG25 = 2      ///< MPEG-2.5
};

/**
 * @brief MP3 Layer
 */
enum class MP3Layer : uint8_t {
    LAYER_I = 0,    ///< Layer I
    LAYER_II = 1,   ///< Layer II
    LAYER_III = 2   ///< Layer III
};

/**
 * @brief MP3 比特率模式
 */
enum class MP3BitrateMode : uint8_t {
    CBR = 0,        ///< 恒定比特率
    VBR = 1,        ///< 可变比特率
    ABR = 2         ///< 平均比特率
};

/**
 * @brief MP3 编码参数
 */
struct MP3EncodeParams {
    int sample_rate = 44100;        ///< 采样率
    int channels = 2;               ///< 通道数
    int bitrate = 128;              ///< 比特率 (kbps)
    MP3Version version = MP3Version::MPEG1; ///< MPEG版本
    MP3Layer layer = MP3Layer::LAYER_III;   ///< Layer
    MP3BitrateMode bitrate_mode = MP3BitrateMode::CBR; ///< 比特率模式
    int quality = 2;                ///< 质量 (0=最高, 9=最低)
    bool vbr_quality = 4;           ///< VBR质量 (0=最高, 9=最低)
    bool joint_stereo = true;       ///< 联合立体声
    bool copyright = false;         ///< 版权标志
    bool original = false;          ///< 原始标志
};

/**
 * @brief MP3 解码参数
 */
struct MP3DecodeParams {
    bool downsample = false;        ///< 下采样
    bool downmix = false;           ///< 下混到单声道
    bool gapless = true;            ///< 无缝播放
};

/**
 * @brief MP3 编码统计信息
 */
struct MP3EncodeStats {
    int64_t total_bytes = 0;        ///< 总编码字节数
    int64_t total_frames = 0;       ///< 总编码帧数
    double avg_bitrate = 0.0;       ///< 平均比特率
    double encoding_speed = 0.0;    ///< 编码速度
};

/**
 * @brief MP3 编码器接口
 */
class IMP3Encoder {
public:
    virtual ~IMP3Encoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const MP3EncodeParams& params) = 0;

    /**
     * @brief 编码一帧
     * @param pcm_left 左声道PCM数据
     * @param pcm_right 右声道PCM数据
     * @param samples 采样数
     * @param out_data 输出MP3数据
     * @return 0成功，负数失败
     */
    virtual int encode(const int16_t* pcm_left, const int16_t* pcm_right,
                      int samples, std::vector<uint8_t>& out_data) = 0;

    /**
     * @brief 交错编码
     * @param pcm_data 交错PCM数据
     * @param samples 采样数
     * @param out_data 输出MP3数据
     * @return 0成功，负数失败
     */
    virtual int encodeInterleaved(const int16_t* pcm_data, int samples,
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
    virtual MP3EncodeStats getStats() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief MP3 解码器接口
 */
class IMP3Decoder {
public:
    virtual ~IMP3Decoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 解码参数
     * @return 0成功，负数失败
     */
    virtual int init(const MP3DecodeParams& params) = 0;

    /**
     * @brief 解码一帧
     * @param mp3_data MP3数据
     * @param mp3_size MP3数据大小
     * @param out_pcm 输出PCM数据
     * @return 0成功，负数失败
     */
    virtual int decode(const uint8_t* mp3_data, int mp3_size,
                      std::vector<int16_t>& out_pcm) = 0;

    /**
     * @brief 浮点解码
     * @param mp3_data MP3数据
     * @param mp3_size MP3数据大小
     * @param out_float 输出浮点PCM数据
     * @return 0成功，负数失败
     */
    virtual int decodeFloat(const uint8_t* mp3_data, int mp3_size,
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
