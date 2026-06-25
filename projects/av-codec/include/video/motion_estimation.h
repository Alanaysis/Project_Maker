#pragma once

/**
 * @file motion_estimation.h
 * @brief 运动估计接口定义
 *
 * 运动估计是视频编码中计算量最大的模块之一。
 * 主要算法：
 * - 全搜索（Full Search）：精度最高，计算量最大
 * - 三步搜索（Three Step Search）
 * - 菱形搜索（Diamond Search）
 * - 六边形搜索（Hexagon Search）
 * - 非对称十字多层次六边形搜索（UMHexagonS）
 */

#include <cstdint>
#include <vector>

namespace av_codec {

/**
 * @brief 运动估计搜索算法
 */
enum class MESearchAlgo : uint8_t {
    FULL_SEARCH = 0,        ///< 全搜索
    THREE_STEP = 1,         ///< 三步搜索
    DIAMOND = 2,            ///< 菱形搜索
    HEXAGON = 3,            ///< 六边形搜索
    UMHexagonS = 4,         ///< UMHexagonS
    EPZS = 5,               ///< EPZS
    FAST_DIAMOND = 6        ///< 快速菱形搜索
};

/**
 * @brief 运动估计匹配准则
 */
enum class MEMatchCriteria : uint8_t {
    SAD = 0,    ///< 绝对误差和
    SSD = 1,    ///< 平方误差和
    SATD = 2,   ///< Hadamard变换后绝对误差和
    SSIM = 3    ///< 结构相似性
};

/**
 * @brief 运动估计参数
 */
struct MEParams {
    int block_width = 16;       ///< 块宽度
    int block_height = 16;      ///< 块高度
    int search_range = 64;      ///< 搜索范围
    MESearchAlgo algorithm = MESearchAlgo::DIAMOND; ///< 搜索算法
    MEMatchCriteria criteria = MEMatchCriteria::SAD; ///< 匹配准则
    int subpel_precision = 2;   ///< 亚像素精度 (0=整像素, 1=半像素, 2=1/4像素)
    int ref_idx = 0;            ///< 参考帧索引
    bool use_me_cache = true;   ///< 使用运动估计缓存
    int lambda = 0;             ///< 拉格朗日乘子
};

/**
 * @brief 运动向量候选
 */
struct MVCandidate {
    int16_t x = 0;              ///< 运动向量X
    int16_t y = 0;              ///< 运动向量Y
    uint32_t cost = 0;          ///< 代价值
    int ref_idx = 0;            ///< 参考帧索引
};

/**
 * @brief 运动估计结果
 */
struct MEResult {
    int16_t mv_x = 0;           ///< 最优运动向量X
    int16_t mv_y = 0;           ///< 最优运动向量Y
    uint32_t sad = 0;           ///< SAD值
    uint32_t cost = 0;          ///< 代价值
    int ref_idx = 0;            ///< 参考帧索引
    int search_points = 0;      ///< 搜索点数
};

/**
 * @brief 运动估计器接口
 */
class IMotionEstimator {
public:
    virtual ~IMotionEstimator() = default;

    /**
     * @brief 初始化运动估计器
     * @param params 运动估计参数
     * @return 0成功，负数失败
     */
    virtual int init(const MEParams& params) = 0;

    /**
     * @brief 执行运动估计
     * @param cur_data 当前块数据
     * @param cur_stride 当前行跨度
     * @param ref_data 参考帧数据
     * @param ref_stride 参考帧行跨度
     * @param x 块X坐标
     * @param y 块Y坐标
     * @param result 输出结果
     * @return 0成功，负数失败
     */
    virtual int estimate(const uint8_t* cur_data, int cur_stride,
                        const uint8_t* ref_data, int ref_stride,
                        int x, int y, MEResult& result) = 0;

    /**
     * @brief 执行多参考帧运动估计
     * @param cur_data 当前块数据
     * @param cur_stride 当前行跨度
     * @param ref_frames 参考帧列表
     * @param ref_strides 参考帧行跨度列表
     * @param x 块X坐标
     * @param y 块Y坐标
     * @param result 输出结果
     * @return 0成功，负数失败
     */
    virtual int estimateMultiRef(const uint8_t* cur_data, int cur_stride,
                                const std::vector<uint8_t*>& ref_frames,
                                const std::vector<int>& ref_strides,
                                int x, int y, MEResult& result) = 0;

    /**
     * @brief 计算SAD
     * @param src 源数据
     * @param src_stride 源行跨度
     * @param ref 参考数据
     * @param ref_stride 参考行跨度
     * @param width 宽度
     * @param height 高度
     * @return SAD值
     */
    virtual uint32_t calcSAD(const uint8_t* src, int src_stride,
                            const uint8_t* ref, int ref_stride,
                            int width, int height) = 0;

    /**
     * @brief 关闭运动估计器
     */
    virtual void close() = 0;
};

} // namespace av_codec
