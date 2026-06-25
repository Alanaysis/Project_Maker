#pragma once

/**
 * @file prediction.h
 * @brief 帧内预测和帧间预测接口定义
 *
 * 预测是视频编码的核心技术之一：
 * - 帧内预测：利用图像空间相关性
 * - 帧间预测：利用图像时间相关性（运动估计/补偿）
 */

#include <cstdint>
#include <vector>

namespace av_codec {

/**
 * @brief 预测模式
 */
enum class PredMode : uint8_t {
    INTRA = 0,  ///< 帧内预测
    INTER = 1,  ///< 帧间预测
    SKIP = 2    ///< 跳过模式
};

/**
 * @brief 帧内预测方向
 */
enum class IntraPredDir : uint8_t {
    DC = 0,         ///< DC预测
    VERTICAL = 1,   ///< 垂直预测
    HORIZONTAL = 2, ///< 水平预测
    DIAG_DOWN_LEFT = 3,  ///< 对角左下
    DIAG_DOWN_RIGHT = 4, ///< 对角右下
    VERT_RIGHT = 5,      ///< 垂直右
    HORZ_DOWN = 6,       ///< 水平下
    VERT_LEFT = 7,       ///< 垂直左
    HORZ_UP = 8,         ///< 水平上
    PLANAR = 9           ///< 平面预测（H.265/AV1）
};

/**
 * @brief 运动向量预测模式
 */
enum class MVPredMode : uint8_t {
    NONE = 0,       ///< 无预测
    MEDIAN = 1,     ///< 中值预测
    LEFT = 2,       ///< 左邻预测
    TOP = 3,        ///< 上邻预测
    TOPRIGHT = 4,   ///< 右上邻预测
    COLLOCATED = 5  ///< 协同定位预测
};

/**
 * @brief 帧内预测参数
 */
struct IntraPredParams {
    int block_size = 0;         ///< 块大小
    IntraPredDir mode = IntraPredDir::DC; ///< 预测模式
    bool chroma_from_luma = false;  ///< 色度从亮度预测
    int chroma_mode = 0;        ///< 色度预测模式
};

/**
 * @brief 帧间预测参数
 */
struct InterPredParams {
    int block_width = 0;        ///< 块宽度
    int block_height = 0;       ///< 块高度
    int16_t mv_x = 0;           ///< 运动向量X
    int16_t mv_y = 0;           ///< 运动向量Y
    int ref_idx = 0;            ///< 参考帧索引
    int ref_list = 0;           ///< 参考列表 (0=L0, 1=L1)
    bool bidir = false;         ///< 双向预测
    int16_t mv_x2 = 0;          ///< 第二运动向量X
    int16_t mv_y2 = 0;          ///< 第二运动向量Y
    int ref_idx2 = 0;           ///< 第二参考帧索引
    MVPredMode mv_pred = MVPredMode::NONE; ///< MV预测模式
};

/**
 * @brief 帧内预测器接口
 */
class IIntraPredictor {
public:
    virtual ~IIntraPredictor() = default;

    /**
     * @brief 执行帧内预测
     * @param params 预测参数
     * @param ref_data 参考数据（已解码的相邻像素）
     * @param pred_data 输出预测数据
     * @return 0成功，负数失败
     */
    virtual int predict(const IntraPredParams& params,
                       const uint8_t* ref_data,
                       uint8_t* pred_data) = 0;

    /**
     * @brief 获取支持的预测模式数
     * @return 模式数
     */
    virtual int getModeCount() const = 0;

    /**
     * @brief 获取最优预测模式
     * @param block_size 块大小
     * @param ref_data 参考数据
     * @return 最优模式
     */
    virtual IntraPredDir getBestMode(int block_size, const uint8_t* ref_data) = 0;
};

/**
 * @brief 帧间预测器接口
 */
class IInterPredictor {
public:
    virtual ~IInterPredictor() = default;

    /**
     * @brief 执行帧间预测（运动补偿）
     * @param params 预测参数
     * @param ref_frame 参考帧数据
     * @param ref_stride 参考帧行跨度
     * @param pred_data 输出预测数据
     * @return 0成功，负数失败
     */
    virtual int predict(const InterPredParams& params,
                       const uint8_t* ref_frame, int ref_stride,
                       uint8_t* pred_data) = 0;

    /**
     * @brief 执行双向预测
     * @param params 预测参数
     * @param ref_frame0 参考帧0数据
     * @param ref_stride0 参考帧0行跨度
     * @param ref_frame1 参考帧1数据
     * @param ref_stride1 参考帧1行跨度
     * @param pred_data 输出预测数据
     * @return 0成功，负数失败
     */
    virtual int predictBidir(const InterPredParams& params,
                            const uint8_t* ref_frame0, int ref_stride0,
                            const uint8_t* ref_frame1, int ref_stride1,
                            uint8_t* pred_data) = 0;

    /**
     * @brief 分像素插值
     * @param ref_data 参考数据
     * @param ref_stride 参考数据行跨度
     * @param width 宽度
     * @param height 高度
     * @param mv_x 运动向量X（1/4像素精度）
     * @param mv_y 运动向量Y（1/4像素精度）
     * @param out_data 输出数据
     * @return 0成功，负数失败
     */
    virtual int interpolate(const uint8_t* ref_data, int ref_stride,
                           int width, int height,
                           int16_t mv_x, int16_t mv_y,
                           uint8_t* out_data) = 0;
};

} // namespace av_codec
