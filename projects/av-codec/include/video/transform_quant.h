#pragma once

/**
 * @file transform_quant.h
 * @brief 变换编码和量化接口定义
 *
 * 变换编码：将空间域信号转换为频率域
 * - DCT（离散余弦变换）：最常用
 * - DST（离散正弦变换）：H.265帧内小块
 * - Hadamard变换：快速近似
 * - KLT（Karhunen-Loève变换）：最优但计算复杂
 *
 * 量化：有损压缩的关键步骤
 * - 标量量化
 * - 矢量量化
 * - 死区量化
 * - 自适应量化
 */

#include <cstdint>
#include <vector>

namespace av_codec {

/**
 * @brief 变换类型
 */
enum class TransformType : uint8_t {
    DCT_II = 0,     ///< DCT-II（最常用）
    DCT_III = 1,    ///< DCT-III（IDCT）
    DCT_I = 2,      ///< DCT-I
    DST_I = 3,      ///< DST-I
    DST_VII = 4,    ///< DST-VII（H.265帧内）
    HADAMARD = 5,   ///< Hadamard变换
    KLT = 6         ///< KLT变换
};

/**
 * @brief 变换块大小
 */
enum class TransformSize : uint8_t {
    SIZE_4x4 = 0,   ///< 4x4
    SIZE_8x8 = 1,   ///< 8x8
    SIZE_16x16 = 2, ///< 16x16
    SIZE_32x32 = 3  ///< 32x32
};

/**
 * @brief 量化模式
 */
enum class QuantMode : uint8_t {
    SCALAR = 0,     ///< 标量量化
    VECTOR = 1,     ///< 矢量量化
    DEADZONE = 2,   ///< 死区量化
    ADAPTIVE = 3    ///< 自适应量化
};

/**
 * @brief 变换参数
 */
struct TransformParams {
    TransformType type = TransformType::DCT_II; ///< 变换类型
    TransformSize size = TransformSize::SIZE_4x4; ///< 块大小
    int width = 4;              ///< 块宽度
    int height = 4;             ///< 块高度
    bool transpose = false;     ///< 是否转置
};

/**
 * @brief 量化参数
 */
struct QuantParams {
    QuantMode mode = QuantMode::SCALAR; ///< 量化模式
    int qp = 26;                ///< 量化参数
    int bit_depth = 8;          ///< 位深度
    bool perceptual = false;    ///< 感知量化
    int lambda = 0;             ///< 拉格朗日乘子
};

/**
 * @brief 变换器接口
 */
class ITransformer {
public:
    virtual ~ITransformer() = default;

    /**
     * @brief 执行正变换
     * @param params 变换参数
     * @param input 输入数据
     * @param input_stride 输入行跨度
     * @param output 输出系数
     * @param output_stride 输出行跨度
     * @return 0成功，负数失败
     */
    virtual int forward(const TransformParams& params,
                       const int16_t* input, int input_stride,
                       int16_t* output, int output_stride) = 0;

    /**
     * @brief 执行逆变换
     * @param params 变换参数
     * @param input 输入系数
     * @param input_stride 输入行跨度
     * @param output 输出数据
     * @param output_stride 输出行跨度
     * @return 0成功，负数失败
     */
    virtual int inverse(const TransformParams& params,
                       const int16_t* input, int input_stride,
                       int16_t* output, int output_stride) = 0;

    /**
     * @brief 执行2D变换
     * @param params 变换参数
     * @param input 输入数据
     * @param output 输出数据
     * @return 0成功，负数失败
     */
    virtual int transform2D(const TransformParams& params,
                           const int16_t* input, int16_t* output) = 0;

    /**
     * @brief 执行2D逆变换
     * @param params 变换参数
     * @param input 输入系数
     * @param output 输出数据
     * @return 0成功，负数失败
     */
    virtual int inverseTransform2D(const TransformParams& params,
                                  const int16_t* input, int16_t* output) = 0;
};

/**
 * @brief 量化器接口
 */
class IQuantizer {
public:
    virtual ~IQuantizer() = default;

    /**
     * @brief 执行量化
     * @param params 量化参数
     * @param input 输入系数
     * @param output 输出量化系数
     * @param width 宽度
     * @param height 高度
     * @return 0成功，负数失败
     */
    virtual int quantize(const QuantParams& params,
                        const int16_t* input, int16_t* output,
                        int width, int height) = 0;

    /**
     * @brief 执行反量化
     * @param params 量化参数
     * @param input 输入量化系数
     * @param output 输出系数
     * @param width 宽度
     * @param height 高度
     * @return 0成功，负数失败
     */
    virtual int dequantize(const QuantParams& params,
                          const int16_t* input, int16_t* output,
                          int width, int height) = 0;

    /**
     * @brief 计算量化步长
     * @param qp 量化参数
     * @return 量化步长
     */
    virtual double getQuantStep(int qp) const = 0;

    /**
     * @brief 计算RDO代价
     * @param coeffs 变换系数
     * @param width 宽度
     * @param height 高度
     * @param qp 量化参数
     * @param lambda 拉格朗日乘子
     * @return 代价
     */
    virtual double calcRDCost(const int16_t* coeffs, int width, int height,
                             int qp, double lambda) = 0;
};

} // namespace av_codec
