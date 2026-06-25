#pragma once

/**
 * @file audio_processing.h
 * @brief 音频处理接口定义
 *
 * 包含：
 * - 频域编码（MDCT, FFT）
 * - 时域编码（线性预测, CELP）
 * - 心理声学模型
 * - 音频滤波器
 */

#include <cstdint>
#include <vector>
#include <complex>

namespace av_codec {

/**
 * @brief 频域变换类型
 */
enum class FreqTransformType : uint8_t {
    FFT = 0,        ///< 快速傅里叶变换
    MDCT = 1,       ///< 改进离散余弦变换
    DCT = 2,        ///< 离散余弦变换
    DFT = 3         ///< 离散傅里叶变换
};

/**
 * @brief 窗函数类型
 */
enum class WindowType : uint8_t {
    RECTANGULAR = 0,    ///< 矩形窗
    HANNING = 1,        ///< 汉宁窗
    HAMMING = 2,        ///< 汉明窗
    BLACKMAN = 3,       ///< 布莱克曼窗
    KAISER = 4,         ///< 凯泽窗
    SINE = 5            ///< 正弦窗
};

/**
 * @brief 频域编码参数
 */
struct FreqCodingParams {
    FreqTransformType transform = FreqTransformType::MDCT; ///< 变换类型
    int frame_size = 1024;      ///< 帧大小
    int overlap = 512;          ///< 重叠大小
    WindowType window = WindowType::SINE; ///< 窗函数
    int bit_depth = 16;         ///< 位深度
};

/**
 * @brief 时域编码参数
 */
struct TemporalCodingParams {
    int frame_size = 320;       ///< 帧大小
    int sample_rate = 8000;     ///< 采样率
    int lpc_order = 10;         ///< LPC阶数
    int subframes = 4;          ///< 子帧数
    bool open_loop = false;     ///< 开环预测
};

/**
 * @brief 心理声学模型参数
 */
struct PsychoacousticParams {
    int frame_size = 1024;      ///< 帧大小
    int sample_rate = 44100;    ///< 采样率
    float spread_width = 0.5f;  ///< 扩展宽度
    float absolute_threshold = 0.0f; ///< 绝对阈值
    int bark_bands = 25;        ///< Bark频带数
};

/**
 * @brief 频域编码器接口
 */
class IFreqEncoder {
public:
    virtual ~IFreqEncoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const FreqCodingParams& params) = 0;

    /**
     * @brief 执行频域变换
     * @param input 输入时域数据
     * @param output 输出频域系数
     * @return 0成功，负数失败
     */
    virtual int transform(const float* input, std::complex<float>* output) = 0;

    /**
     * @brief 执行逆变换
     * @param input 输入频域系数
     * @param output 输出时域数据
     * @return 0成功，负数失败
     */
    virtual int inverseTransform(const std::complex<float>* input, float* output) = 0;

    /**
     * @brief 应用窗函数
     * @param data 数据
     * @param size 大小
     * @param window 窗函数类型
     * @return 0成功，负数失败
     */
    virtual int applyWindow(float* data, int size, WindowType window) = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief 时域编码器接口
 */
class ITemporalEncoder {
public:
    virtual ~ITemporalEncoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const TemporalCodingParams& params) = 0;

    /**
     * @brief 线性预测分析
     * @param input 输入信号
     * @param lpc LPC系数
     * @param order LPC阶数
     * @return 0成功，负数失败
     */
    virtual int lpcAnalysis(const float* input, float* lpc, int order) = 0;

    /**
     * @brief 编码一帧
     * @param input 输入PCM数据
     * @param output 输出编码数据
     * @return 0成功，负数失败
     */
    virtual int encode(const float* input, std::vector<uint8_t>& output) = 0;

    /**
     * @brief 解码一帧
     * @param input 输入编码数据
     * @param output 输出PCM数据
     * @return 0成功，负数失败
     */
    virtual int decode(const uint8_t* input, int size, float* output) = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief 心理声学模型接口
 */
class IPsychoacousticModel {
public:
    virtual ~IPsychoacousticModel() = default;

    /**
     * @brief 初始化模型
     * @param params 模型参数
     * @return 0成功，负数失败
     */
    virtual int init(const PsychoacousticParams& params) = 0;

    /**
     * @brief 计算掩蔽阈值
     * @param spectrum 频谱数据
     * @param threshold 输出掩蔽阈值
     * @return 0成功，负数失败
     */
    virtual int calcMaskingThreshold(const float* spectrum, float* threshold) = 0;

    /**
     * @brief 计算信掩比
     * @param spectrum 频谱数据
     * @param threshold 掩蔽阈值
     * @param smr 输出信掩比
     * @return 0成功，负数失败
     */
    virtual int calcSMR(const float* spectrum, const float* threshold, float* smr) = 0;

    /**
     * @brief 计算感知熵
     * @param spectrum 频谱数据
     * @return 感知熵
     */
    virtual float calcPerceptualEntropy(const float* spectrum) = 0;

    /**
     * @brief 关闭模型
     */
    virtual void close() = 0;
};

} // namespace av_codec
