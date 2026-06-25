#pragma once

/**
 * @file performance.h
 * @brief 性能优化接口定义
 *
 * 包含：
 * - SIMD优化（SSE, AVX, NEON）
 * - 多线程编码
 * - GPU加速（CUDA, OpenCL, Vulkan）
 * - 硬件编解码（VAAPI, NVENC, QSV, DXVA）
 */

#include <cstdint>
#include <vector>
#include <functional>
#include <thread>

namespace av_codec {

/**
 * @brief SIMD 指令集
 */
enum class SIMDType : uint8_t {
    NONE = 0,       ///< 无SIMD
    SSE2 = 1,       ///< SSE2
    SSE4 = 2,       ///< SSE4.1/4.2
    AVX = 3,        ///< AVX
    AVX2 = 4,       ///< AVX2
    AVX512 = 5,     ///< AVX-512
    NEON = 6        ///< ARM NEON
};

/**
 * @brief GPU 类型
 */
enum class GPUType : uint8_t {
    NONE = 0,       ///< 无GPU
    CUDA = 1,       ///< NVIDIA CUDA
    OPENCL = 2,     ///< OpenCL
    VULKAN = 3,     ///< Vulkan
    METAL = 4,      ///< Apple Metal
    DX11 = 5,       ///< DirectX 11
    DX12 = 6        ///< DirectX 12
};

/**
 * @brief 硬件编解码器类型
 */
enum class HWCodecType : uint8_t {
    NONE = 0,       ///< 软件编解码
    NVENC = 1,      ///< NVIDIA NVENC
    NVDEC = 2,      ///< NVIDIA NVDEC
    QSV = 3,        ///< Intel Quick Sync Video
    VAAPI = 4,      ///< VA-API (Linux)
    VDPAU = 5,      ///< VDPAU (Linux)
    DXVA = 6,       ///< DXVA (Windows)
    VTB = 7,        ///< VideoToolbox (macOS)
    MEDIACODEC = 8  ///< MediaCodec (Android)
};

/**
 * @brief SIMD 优化参数
 */
struct SIMDParams {
    SIMDType type = SIMDType::AUTO; ///< SIMD类型
    bool auto_detect = true;    ///< 自动检测
    int alignment = 32;         ///< 内存对齐
};

/**
 * @brief 多线程参数
 */
struct ThreadParams {
    int thread_count = 0;       ///< 线程数 (0=自动)
    int frame_threads = 0;      ///< 帧级并行线程数
    int slice_threads = 0;      ///< 切片级并行线程数
    bool thread_type_frame = true;  ///< 帧级并行
    bool thread_type_slice = true;  ///< 切片级并行
};

/**
 * @brief GPU 加速参数
 */
struct GPUParams {
    GPUType type = GPUType::NONE;   ///< GPU类型
    int device_id = 0;          ///< 设备ID
    bool async_transfer = true; ///< 异步传输
    int max_threads = 32;       ///< 最大线程数
    size_t memory_limit = 0;    ///< 显存限制 (0=自动)
};

/**
 * @brief 硬件编解码参数
 */
struct HWCodecParams {
    HWCodecType type = HWCodecType::NONE; ///< 硬件类型
    int device_id = 0;          ///< 设备ID
    bool low_latency = false;   ///< 低延迟模式
    int quality = 0;            ///< 质量预设
    bool async_depth = 1;       ///< 异步深度
};

/**
 * @brief 性能统计信息
 */
struct PerformanceStats {
    double cpu_usage = 0.0;     ///< CPU使用率
    double gpu_usage = 0.0;     ///< GPU使用率
    size_t memory_used = 0;     ///< 内存使用
    size_t gpu_memory_used = 0; ///< GPU显存使用
    double encoding_fps = 0.0;  ///< 编码帧率
    double decoding_fps = 0.0;  ///< 解码帧率
    int64_t avg_encode_time_ms = 0; ///< 平均编码时间
    int64_t avg_decode_time_ms = 0; ///< 平均解码时间
};

/**
 * @brief SIMD 工具接口
 */
class ISIMDUtils {
public:
    virtual ~ISIMDUtils() = default;

    /**
     * @brief 检测SIMD支持
     * @return 支持的SIMD类型
     */
    virtual SIMDType detect() = 0;

    /**
     * @brief SIMD优化的SAD计算
     * @param src 源数据
     * @param ref 参考数据
     * @param stride 行跨度
     * @param width 宽度
     * @param height 高度
     * @return SAD值
     */
    virtual uint32_t calcSAD(const uint8_t* src, const uint8_t* ref,
                            int stride, int width, int height) = 0;

    /**
     * @brief SIMD优化的DCT
     * @param input 输入数据
     * @param output 输出系数
     * @param size 块大小
     */
    virtual void dct(const int16_t* input, int16_t* output, int size) = 0;

    /**
     * @brief SIMD优化的IDCT
     * @param input 输入系数
     * @param output 输出数据
     * @param size 块大小
     */
    virtual void idct(const int16_t* input, int16_t* output, int size) = 0;

    /**
     * @brief SIMD优化的像素加权平均
     * @param src0 源0
     * @param src1 源1
     * @param dst 目标
     * @param weight0 权重0
     * @param weight1 权重1
     * @param width 宽度
     * @param height 高度
     */
    virtual void weightedAvg(const uint8_t* src0, const uint8_t* src1,
                            uint8_t* dst, int weight0, int weight1,
                            int width, int height) = 0;
};

/**
 * @brief 多线程编码器接口
 */
class IThreadedEncoder {
public:
    virtual ~IThreadedEncoder() = default;

    /**
     * @brief 初始化多线程编码器
     * @param params 线程参数
     * @return 0成功，负数失败
     */
    virtual int init(const ThreadParams& params) = 0;

    /**
     * @brief 并行编码多个块
     * @param blocks 块数据列表
     * @param results 输出结果列表
     * @return 0成功，负数失败
     */
    virtual int encodeParallel(const std::vector<const uint8_t*>& blocks,
                              std::vector<std::vector<uint8_t>>& results) = 0;

    /**
     * @brief 并行编码多个帧
     * @param frames 帧数据列表
     * @param results 输出结果列表
     * @return 0成功，负数失败
     */
    virtual int encodeFramesParallel(const std::vector<const uint8_t*>& frames,
                                    std::vector<std::vector<uint8_t>>& results) = 0;

    /**
     * @brief 获取线程数
     * @return 线程数
     */
    virtual int getThreadCount() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief GPU 加速器接口
 */
class IGPUAccelerator {
public:
    virtual ~IGPUAccelerator() = default;

    /**
     * @brief 初始化GPU加速器
     * @param params GPU参数
     * @return 0成功，负数失败
     */
    virtual int init(const GPUParams& params) = 0;

    /**
     * @brief 上传数据到GPU
     * @param host_data 主机数据
     * @param size 数据大小
     * @return GPU指针
     */
    virtual void* uploadToGPU(const void* host_data, size_t size) = 0;

    /**
     * @brief 从GPU下载数据
     * @param gpu_data GPU数据指针
     * @param host_data 主机数据
     * @param size 数据大小
     * @return 0成功，负数失败
     */
    virtual int downloadFromGPU(const void* gpu_data, void* host_data, size_t size) = 0;

    /**
     * @brief GPU上的DCT变换
     * @param input 输入数据
     * @param output 输出系数
     * @param size 块大小
     * @return 0成功，负数失败
     */
    virtual int gpuDCT(const void* input, void* output, int size) = 0;

    /**
     * @brief GPU上的运动估计
     * @param current 当前帧
     * @param reference 参考帧
     * @param mv_x 输出MV X
     * @param mv_y 输出MV Y
     * @return 0成功，负数失败
     */
    virtual int gpuMotionEstimation(const void* current, const void* reference,
                                   int16_t* mv_x, int16_t* mv_y) = 0;

    /**
     * @brief 获取GPU信息
     * @param name 设备名称
     * @param memory 显存大小
     * @return 0成功，负数失败
     */
    virtual int getGPUInfo(std::string& name, size_t& memory) = 0;

    /**
     * @brief 关闭GPU加速器
     */
    virtual void close() = 0;
};

/**
 * @brief 硬件编解码器接口
 */
class IHWCodec {
public:
    virtual ~IHWCodec() = default;

    /**
     * @brief 初始化硬件编解码器
     * @param params 硬件参数
     * @return 0成功，负数失败
     */
    virtual int init(const HWCodecParams& params) = 0;

    /**
     * @brief 检测硬件支持
     * @param type 硬件类型
     * @return true/false
     */
    virtual bool isSupported(HWCodecType type) = 0;

    /**
     * @brief 创建硬件编码器
     * @param codec_id 编码ID
     * @return 0成功，负数失败
     */
    virtual int createEncoder(int codec_id) = 0;

    /**
     * @brief 创建硬件解码器
     * @param codec_id 编码ID
     * @return 0成功，负数失败
     */
    virtual int createDecoder(int codec_id) = 0;

    /**
     * @brief 硬件编码
     * @param input 输入数据
     * @param output 输出数据
     * @return 0成功，负数失败
     */
    virtual int encode(const void* input, std::vector<uint8_t>& output) = 0;

    /**
     * @brief 硬件解码
     * @param input 输入数据
     * @param output 输出数据
     * @return 0成功，负数失败
     */
    virtual int decode(const uint8_t* input, int size, void* output) = 0;

    /**
     * @brief 关闭硬件编解码器
     */
    virtual void close() = 0;
};

} // namespace av_codec
