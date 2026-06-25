#pragma once

/**
 * @file h264_codec.h
 * @brief H.264/AVC 编解码器接口定义
 *
 * H.264 是目前应用最广泛的视频编码标准，由 ITU-T 和 ISO/IEC 联合开发。
 * 主要特点：
 * - 高效的压缩比（比 H.263 提高 50%）
 * - 支持多种分辨率和帧率
 * - 灵活的宏块划分（16x16, 8x8, 4x4）
 * - 多参考帧运动补偿
 * - CAVLC/CABAC 熵编码
 */

#include <cstdint>
#include <vector>
#include <memory>
#include <functional>

namespace av_codec {

// H.264 常量定义
constexpr int H264_MAX_REF_FRAMES = 16;
constexpr int H264_MB_SIZE = 16;
constexpr int H264_SUB_MB_SIZE = 4;
constexpr int H264_MAX_QP = 51;
constexpr int H264_MIN_QP = 0;

/**
 * @brief H.264 帧类型
 */
enum class H264FrameType : uint8_t {
    I_FRAME = 0,    ///< I帧 - 关键帧，仅帧内编码
    P_FRAME = 1,    ///< P帧 - 预测帧，前向预测
    B_FRAME = 2,    ///< B帧 - 双向预测帧
    IDR_FRAME = 3,  ///< IDR帧 - 即时解码刷新帧
    S_FRAME = 4,    ///< S帧 - 切换帧
    SI_FRAME = 5,   ///< SI帧 - 切换I帧
    SP_FRAME = 6    ///< SP帧 - 切换P帧
};

/**
 * @brief H.264 宏块类型
 */
enum class H264MBType : uint8_t {
    I_4x4 = 0,      ///< I帧 4x4块
    I_8x8 = 1,      ///< I帧 8x8块
    I_16x16 = 2,    ///< I帧 16x16块
    I_PCM = 3,      ///< I帧 PCM模式
    P_L0_16x16 = 4, ///< P帧 16x16预测
    P_L0_16x8 = 5,  ///< P帧 16x8分割
    P_L0_8x16 = 6,  ///< P帧 8x16分割
    P_L0_8x8 = 7,   ///< P帧 8x8分割
    P_SKIP = 8,     ///< P帧 跳过模式
    B_DIRECT = 9,   ///< B帧 直接模式
    B_L0_16x16 = 10,///< B帧 前向16x16
    B_L1_16x16 = 11,///< B帧 后向16x16
    B_BI_16x16 = 12 ///< B帧 双向16x16
};

/**
 * @brief H.264 帧内预测模式（亮度）
 */
enum class H264IntraPredMode : uint8_t {
    VERT = 0,           ///< 垂直预测
    HORZ = 1,           ///< 水平预测
    DC = 2,             ///< DC预测
    DIAG_DOWN_LEFT = 3, ///< 对角线左下
    DIAG_DOWN_RIGHT = 4,///< 对角线右下
    VERT_RIGHT = 5,     ///< 垂直偏右
    HORZ_DOWN = 6,      ///< 水平偏下
    VERT_LEFT = 7,      ///< 垂直偏左
    HORZ_UP = 8         ///< 水平偏上
};

/**
 * @brief 运动向量
 */
struct MotionVector {
    int16_t x = 0;  ///< 水平分量（以1/4像素为单位）
    int16_t y = 0;  ///< 垂直分量（以1/4像素为单位）
    int16_t ref_idx = -1; ///< 参考帧索引
};

/**
 * @brief H.264 编码参数
 */
struct H264EncodeParams {
    int width = 1920;               ///< 视频宽度
    int height = 1080;              ///< 视频高度
    int fps = 30;                   ///< 帧率
    int bitrate = 2000000;          ///< 目标码率 (bps)
    int qp = 26;                    ///< 量化参数 (0-51)
    int gop_size = 30;              ///< GOP大小
    int max_b_frames = 3;           ///< 最大B帧数
    int ref_frames = 4;             ///< 参考帧数
    int profile = 100;              ///< Profile (66=Baseline, 77=Main, 100=High)
    int level = 40;                 ///< Level
    bool cabac = true;              ///< 使用CABAC熵编码
    bool interlaced = false;        ///< 隔行扫描
    int threads = 4;                ///< 编码线程数
};

/**
 * @brief H.264 解码参数
 */
struct H264DecodeParams {
    int threads = 4;                ///< 解码线程数
    bool error_resilient = true;    ///< 错误恢复
    int max_ref_frames = 16;        ///< 最大参考帧数
};

/**
 * @brief H.264 编码统计信息
 */
struct H264EncodeStats {
    int64_t total_bits = 0;         ///< 总编码比特数
    int64_t total_frames = 0;       ///< 总编码帧数
    int i_frames = 0;               ///< I帧数量
    int p_frames = 0;               ///< P帧数量
    int b_frames = 0;               ///< B帧数量
    double avg_qp = 0.0;            ///< 平均量化参数
    double avg_psnr = 0.0;          ///< 平均PSNR
    double fps = 0.0;               ///< 编码帧率
};

/**
 * @brief H.264 编码器接口
 */
class IH264Encoder {
public:
    virtual ~IH264Encoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const H264EncodeParams& params) = 0;

    /**
     * @brief 编码一帧
     * @param yuv_data YUV420P数据
     * @param out_data 输出H.264码流
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
    virtual H264EncodeStats getStats() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief H.264 解码器接口
 */
class IH264Decoder {
public:
    virtual ~IH264Decoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 解码参数
     * @return 0成功，负数失败
     */
    virtual int init(const H264DecodeParams& params) = 0;

    /**
     * @brief 解码一帧
     * @param data H.264码流数据
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
