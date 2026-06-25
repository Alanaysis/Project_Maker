#pragma once

/**
 * @file av1_codec.h
 * @brief AV1 编解码器接口定义
 *
 * AV1 是 AOM (Alliance for Open Media) 开发的下一代开源视频编码标准。
 * 主要特点：
 * - 完全开源免费，无专利费用
 * - 比 VP9/H.265 提高 30% 压缩效率
 * - 支持 8K、HDR、宽色域
 * - 专为互联网流媒体设计
 * - 被 Netflix、YouTube、Facebook 等采用
 */

#include <cstdint>
#include <vector>
#include <memory>

namespace av_codec {

// AV1 常量定义
constexpr int AV1_MAX_BLOCK_SIZE = 128;  ///< 最大块大小
constexpr int AV1_MIN_BLOCK_SIZE = 4;    ///< 最小块大小
constexpr int AV1_MAX_REF_FRAMES = 7;    ///< 最大参考帧数
constexpr int AV1_MAX_QP = 255;          ///< 最大量化参数
constexpr int AV1_MAX_SEGMENTS = 8;      ///< 最大分割数
constexpr int AV1_NUM_PLANES = 3;        ///< 平面数

/**
 * @brief AV1 帧类型
 */
enum class AV1FrameType : uint8_t {
    KEY_FRAME = 0,          ///< 关键帧
    INTER_FRAME = 1,        ///< 帧间帧
    INTRA_ONLY_FRAME = 2,   ///< 纯帧内帧
    SWITCH_FRAME = 3,       ///< 切换帧
    FRAME_TYPE_MAX = 4
};

/**
 * @brief AV1 块大小
 */
enum class AV1BlockSize : uint8_t {
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
    BLOCK_64x128 = 13,
    BLOCK_128x64 = 14,
    BLOCK_128x128 = 15,
    BLOCK_INVALID = 16
};

/**
 * @brief AV1 帧内预测模式
 */
enum class AV1IntraPredMode : uint8_t {
    DC_PRED = 0,            ///< DC预测
    V_PRED = 1,             ///< 垂直预测
    H_PRED = 2,             ///< 水平预测
    D45_PRED = 3,           ///< 45度对角线
    D135_PRED = 4,          ///< 135度对角线
    D117_PRED = 5,          ///< 117度对角线
    D153_PRED = 6,          ///< 153度对角线
    D207_PRED = 7,          ///< 207度对角线
    D63_PRED = 8,           ///< 63度对角线
    SMOOTH_PRED = 9,        ///< 平滑预测
    SMOOTH_V_PRED = 10,     ///< 垂直平滑预测
    SMOOTH_H_PRED = 11,     ///< 水平平滑预测
    PAETH_PRED = 12,        ///< Paeth预测
    NEARESTMV = 13,         ///< 最近运动向量
    NEARMV = 14,            ///< 近邻运动向量
    GLOBALMV = 15,          ///< 全局运动向量
    NEWMV = 16              ///< 新运动向量
};

/**
 * @brief AV1 参考帧类型
 */
enum class AV1RefFrame : uint8_t {
    NONE = -1,
    INTRA_FRAME = 0,
    LAST_FRAME = 1,
    LAST2_FRAME = 2,
    LAST3_FRAME = 3,
    GOLDEN_FRAME = 4,
    BWDREF_FRAME = 5,
    ALTREF2_FRAME = 6,
    ALTREF_FRAME = 7
};

/**
 * @brief AV1 编码参数
 */
struct AV1EncodeParams {
    int width = 1920;               ///< 视频宽度
    int height = 1080;              ///< 视频高度
    int fps = 30;                   ///< 帧率
    int bitrate = 2000000;          ///< 目标码率 (bps)
    int cq_level = 31;              ///< 约束质量模式
    int key_frame_interval = 3000;  ///< 关键帧间隔
    int ref_frames = 7;             ///< 参考帧数
    int tile_columns = 0;           ///< Tile列数（log2）
    int tile_rows = 0;              ///< Tile行数（log2）
    bool error_resilient = false;   ///< 错误恢复模式
    bool cdef = true;               ///< 约束方向增强滤波器
    bool restoration = true;        ///< 环路恢复滤波器
    bool film_grain = false;        ///< 胶片颗粒合成
    int threads = 4;                ///< 编码线程数
    int profile = 0;                ///< Profile (0=Main, 1=High, 2=Professional)
    int level = 0;                  ///< Level
};

/**
 * @brief AV1 解码参数
 */
struct AV1DecodeParams {
    int threads = 4;                ///< 解码线程数
    bool error_resilient = false;   ///< 错误恢复模式
};

/**
 * @brief AV1 编码统计信息
 */
struct AV1EncodeStats {
    int64_t total_bits = 0;         ///< 总编码比特数
    int64_t total_frames = 0;       ///< 总编码帧数
    int key_frames = 0;             ///< 关键帧数
    int inter_frames = 0;           ///< 帧间帧数
    int intra_only_frames = 0;      ///< 纯帧内帧数
    double avg_qp = 0.0;            ///< 平均量化参数
    double avg_psnr = 0.0;          ///< 平均PSNR
    double fps = 0.0;               ///< 编码帧率
};

/**
 * @brief AV1 编码器接口
 */
class IAV1Encoder {
public:
    virtual ~IAV1Encoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const AV1EncodeParams& params) = 0;

    /**
     * @brief 编码一帧
     * @param yuv_data YUV420P数据
     * @param out_data 输出AV1码流
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
    virtual AV1EncodeStats getStats() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief AV1 解码器接口
 */
class IAV1Decoder {
public:
    virtual ~IAV1Decoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 解码参数
     * @return 0成功，负数失败
     */
    virtual int init(const AV1DecodeParams& params) = 0;

    /**
     * @brief 解码一帧
     * @param data AV1码流数据
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
