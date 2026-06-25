#pragma once

/**
 * @file h265_codec.h
 * @brief H.265/HEVC 编解码器接口定义
 *
 * H.265 (High Efficiency Video Coding) 是 H.264 的继任者。
 * 主要特点：
 * - 比 H.264 提高 50% 压缩效率
 * - 支持 4K/8K 超高清视频
 * - 灵活的块划分（CTU 从 64x64 到 4x4）
 * - 更多的帧内预测模式（35种）
 * - 更大的变换块（最大 32x32）
 * - 并行处理工具（Tiles, WPP）
 */

#include <cstdint>
#include <vector>
#include <memory>

namespace av_codec {

// H.265 常量定义
constexpr int H265_MAX_CU_SIZE = 64;      ///< 最大编码单元
constexpr int H265_MIN_CU_SIZE = 8;       ///< 最小编码单元
constexpr int H265_MAX_PU_SIZE = 64;      ///< 最大预测单元
constexpr int H265_MAX_TU_SIZE = 32;      ///< 最大变换单元
constexpr int H265_MIN_TU_SIZE = 4;       ///< 最小变换单元
constexpr int H265_MAX_QP = 51;           ///< 最大量化参数
constexpr int H265_MAX_REF_FRAMES = 16;   ///< 最大参考帧数
constexpr int H265_INTRA_MODES = 35;      ///< 帧内预测模式数
constexpr int H265_INTER_MODES = 8;       ///< 帧间预测模式数

/**
 * @brief H.265 帧类型
 */
enum class H265FrameType : uint8_t {
    I_FRAME = 0,    ///< I帧
    P_FRAME = 1,    ///< P帧
    B_FRAME = 2     ///< B帧
};

/**
 * @brief H.265 CU 分割模式
 */
enum class H265CUSplitMode : uint8_t {
    NO_SPLIT = 0,   ///< 不分割
    QUAD_SPLIT = 1, ///< 四叉树分割
    BI_SPLIT_H = 2, ///< 水平二分
    BI_SPLIT_V = 3, ///< 垂直二分
    TRI_SPLIT_A = 4,///< 三叉树A
    TRI_SPLIT_B = 5 ///< 三叉树B
};

/**
 * @brief H.265 PU 预测模式
 */
enum class H265PUPredMode : uint8_t {
    INTRA = 0,      ///< 帧内预测
    INTER = 1,      ///< 帧间预测
    SKIP = 2        ///< 跳过模式
};

/**
 * @brief H.265 PU 分割模式
 */
enum class H265PUSplitMode : uint8_t {
    PART_2Nx2N = 0, ///< 2Nx2N
    PART_2NxN = 1,  ///< 2NxN
    PART_Nx2N = 2,  ///< Nx2N
    PART_NxN = 3,   ///< NxN
    PART_2NxnU = 4, ///< 2NxnU
    PART_2NxnD = 5, ///< 2NxnD
    PART_nLx2N = 6, ///< nLx2N
    PART_nRx2N = 7  ///< nRx2N
};

/**
 * @brief H.265 帧内预测模式
 */
enum class H265IntraPredMode : uint8_t {
    PLANAR = 0,     ///< 平面预测
    DC = 1,         ///< DC预测
    VERT = 2,       ///< 垂直预测
    HORZ = 3,       ///< 水平预测
    // 角度预测模式 (4-34)
    ANGULAR_2 = 4,
    ANGULAR_3 = 5,
    ANGULAR_4 = 6,
    ANGULAR_5 = 7,
    ANGULAR_6 = 8,
    ANGULAR_7 = 9,
    ANGULAR_8 = 10,
    ANGULAR_9 = 11,
    ANGULAR_10 = 12,
    ANGULAR_11 = 13,
    ANGULAR_12 = 14,
    ANGULAR_13 = 15,
    ANGULAR_14 = 16,
    ANGULAR_15 = 17,
    ANGULAR_16 = 18,
    ANGULAR_17 = 19,
    ANGULAR_18 = 20,
    ANGULAR_19 = 21,
    ANGULAR_20 = 22,
    ANGULAR_21 = 23,
    ANGULAR_22 = 24,
    ANGULAR_23 = 25,
    ANGULAR_24 = 26,
    ANGULAR_25 = 27,
    ANGULAR_26 = 28,
    ANGULAR_27 = 29,
    ANGULAR_28 = 30,
    ANGULAR_29 = 31,
    ANGULAR_30 = 32,
    ANGULAR_31 = 33,
    ANGULAR_32 = 34
};

/**
 * @brief H.265 编码参数
 */
struct H265EncodeParams {
    int width = 1920;               ///< 视频宽度
    int height = 1080;              ///< 视频高度
    int fps = 30;                   ///< 帧率
    int bitrate = 2000000;          ///< 目标码率 (bps)
    int qp = 26;                    ///< 量化参数
    int gop_size = 30;              ///< GOP大小
    int max_b_frames = 3;           ///< 最大B帧数
    int ref_frames = 4;             ///< 参考帧数
    int profile = 2;                ///< Profile (0=Main, 1=Main10, 2=MainStillPicture)
    int level = 120;                ///< Level (120=4.0)
    int max_cu_size = 64;           ///< 最大CU大小
    int min_cu_size = 8;            ///< 最小CU大小
    int max_tu_size = 32;           ///< 最大TU大小
    int min_tu_size = 4;            ///< 最小TU大小
    int max_tu_depth = 3;           ///< 最大TU深度
    bool amp = true;                ///< 非对称运动分区
    bool sao = true;                ///< 样本自适应偏移
    bool wpp = true;                ///< 波前并行处理
    int tiles_cols = 1;             ///< Tile列数
    int tiles_rows = 1;             ///< Tile行数
    int threads = 4;                ///< 编码线程数
};

/**
 * @brief H.265 解码参数
 */
struct H265DecodeParams {
    int threads = 4;                ///< 解码线程数
    bool error_resilient = true;    ///< 错误恢复
};

/**
 * @brief H.265 编码统计信息
 */
struct H265EncodeStats {
    int64_t total_bits = 0;         ///< 总编码比特数
    int64_t total_frames = 0;       ///< 总编码帧数
    int i_frames = 0;               ///< I帧数量
    int p_frames = 0;               ///< P帧数量
    int b_frames = 0;               ///< B帧数量
    double avg_qp = 0.0;            ///< 平均量化参数
    double avg_psnr = 0.0;          ///< 平均PSNR
    double fps = 0.0;               ///< 编码帧率
    int64_t total_ctu = 0;          ///< CTU总数
    int64_t intra_ctu = 0;          ///< 帧内CTU数
    int64_t inter_ctu = 0;          ///< 帧间CTU数
};

/**
 * @brief H.265 编码器接口
 */
class IH265Encoder {
public:
    virtual ~IH265Encoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const H265EncodeParams& params) = 0;

    /**
     * @brief 编码一帧
     * @param yuv_data YUV420P数据
     * @param out_data 输出H.265码流
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
    virtual H265EncodeStats getStats() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief H.265 解码器接口
 */
class IH265Decoder {
public:
    virtual ~IH265Decoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 解码参数
     * @return 0成功，负数失败
     */
    virtual int init(const H265DecodeParams& params) = 0;

    /**
     * @brief 解码一帧
     * @param data H.265码流数据
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
