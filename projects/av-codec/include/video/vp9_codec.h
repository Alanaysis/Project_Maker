#pragma once

/**
 * @file vp9_codec.h
 * @brief VP8/VP9 编解码器接口定义
 *
 * VP9 是 Google 开发的开源视频编码格式。
 * 主要特点：
 * - 完全开源免费
 * - 支持 4K/8K 视频
 * - 高效的压缩性能（接近 H.265）
 * - WebM 容器格式支持
 * - 广泛用于 YouTube、Chrome 等
 */

#include <cstdint>
#include <vector>
#include <memory>

namespace av_codec {

// VP9 常量定义
constexpr int VP9_MAX_BLOCK_SIZE = 64;   ///< 最大块大小
constexpr int VP9_MIN_BLOCK_SIZE = 4;    ///< 最小块大小
constexpr int VP9_MAX_REF_FRAMES = 3;    ///< 最大参考帧数
constexpr int VP9_MAX_QP = 255;          ///< 最大量化参数
constexpr int VP9_NUM_FRAMES = 8;        ///< 帧上下文数

/**
 * @brief VP9 帧类型
 */
enum class VP9FrameType : uint8_t {
    KEY_FRAME = 0,      ///< 关键帧
    INTER_FRAME = 1,    ///< 帧间帧
    FRAME_TYPE_MAX = 2
};

/**
 * @brief VP9 帧内预测模式
 */
enum class VP9IntraPredMode : uint8_t {
    DC_PRED = 0,        ///< DC预测
    V_PRED = 1,         ///< 垂直预测
    H_PRED = 2,         ///< 水平预测
    D45_PRED = 3,       ///< 45度对角线
    D135_PRED = 4,      ///< 135度对角线
    D117_PRED = 5,      ///< 117度对角线
    D153_PRED = 6,      ///< 153度对角线
    D207_PRED = 7,      ///< 207度对角线
    D63_PRED = 8,       ///< 63度对角线
    TM_PRED = 9,        ///< True-Motion预测
    NEARESTMV = 10,     ///< 最近运动向量
    NEARMV = 11,        ///< 近邻运动向量
    ZEROMV = 12,        ///< 零运动向量
    NEWMV = 13          ///< 新运动向量
};

/**
 * @brief VP9 块大小
 */
enum class VP9BlockSize : uint8_t {
    BLOCK_4x4 = 0,
    BLOCK_4x8 = 1,
    BLOCK_8x4 = 2,
    BLOCK_8x8 = 3,
    BLOCK_8x16 = 4,
    BLOCK_16x8 = 5,
    BLOCK_16x16 = 6,
    BLOCK_16x32 = 7,
    BLOCK_32x16 = 8,
    BLOCK_32x32 = 9,
    BLOCK_32x64 = 10,
    BLOCK_64x32 = 11,
    BLOCK_64x64 = 12,
    BLOCK_INVALID = 13
};

/**
 * @brief VP9 参考帧类型
 */
enum class VP9RefFrame : uint8_t {
    NONE = -1,
    INTRA_FRAME = 0,
    LAST_FRAME = 1,
    GOLDEN_FRAME = 2,
    ALTREF_FRAME = 3
};

/**
 * @brief VP9 编码参数
 */
struct VP9EncodeParams {
    int width = 1920;               ///< 视频宽度
    int height = 1080;              ///< 视频高度
    int fps = 30;                   ///< 帧率
    int bitrate = 2000000;          ///< 目标码率 (bps)
    int cq_level = 31;              ///< 约束质量模式
    int key_frame_interval = 3000;  ///< 关键帧间隔
    int ref_frames = 3;             ///< 参考帧数
    int tile_columns = 0;           ///< Tile列数（log2）
    int tile_rows = 0;              ///< Tile行数（log2）
    bool error_resilient = false;   ///< 错误恢复模式
    bool arnr = true;               ///< 自适应参考帧噪声减少
    int arnr_strength = 3;          ///< ARNR强度
    int arnr_max_frames = 7;        ///< ARNR最大帧数
    int threads = 4;                ///< 编码线程数
    int profile = 0;                ///< Profile (0=0, 1=1, 2=2, 3=3)
};

/**
 * @brief VP9 解码参数
 */
struct VP9DecodeParams {
    int threads = 4;                ///< 解码线程数
    bool error_resilient = false;   ///< 错误恢复模式
};

/**
 * @brief VP9 编码统计信息
 */
struct VP9EncodeStats {
    int64_t total_bits = 0;         ///< 总编码比特数
    int64_t total_frames = 0;       ///< 总编码帧数
    int key_frames = 0;             ///< 关键帧数
    int inter_frames = 0;           ///< 帧间帧数
    double avg_qp = 0.0;            ///< 平均量化参数
    double avg_psnr = 0.0;          ///< 平均PSNR
    double fps = 0.0;               ///< 编码帧率
};

/**
 * @brief VP9 编码器接口
 */
class IVP9Encoder {
public:
    virtual ~IVP9Encoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const VP9EncodeParams& params) = 0;

    /**
     * @brief 编码一帧
     * @param yuv_data YUV420P数据
     * @param out_data 输出VP9码流
     * @return 0成功，负数失败
     */
    virtual int encode(const uint8_t* yuv_data, std::vector<uint8_t>& out_data) = 0;

    /**
     * @brief 刷新编码器
     * @param out_data 输出剩余码流
     * @return 0成功，负数失败
     */
    virtual int flush(std::vector<uint8_t>& out_data) = 0;

    /**
     * @brief 获取编码统计信息
     * @return 统计信息
     */
    virtual VP9EncodeStats getStats() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief VP9 解码器接口
 */
class IVP9Decoder {
public:
    virtual ~IVP9Decoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 解码参数
     * @return 0成功，负数失败
     */
    virtual int init(const VP9DecodeParams& params) = 0;

    /**
     * @brief 解码一帧
     * @param data VP9码流数据
     * @param size 数据大小
     * @param out_yuv 输出YUV420P数据
     * @return 0成功，负数失败
     */
    virtual int decode(const uint8_t* data, int size, std::vector<uint8_t>& out_yuv) = 0;

    /**
     * @brief 刷新解码器
     * @param out_yuv 输出剩余帧
     * @return 0成功，负数失败
     */
    virtual int flush(std::vector<uint8_t>& out_yuv) = 0;

    /**
     * @brief 关闭解码器
     */
    virtual void close() = 0;
};

} // namespace av_codec
