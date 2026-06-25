/**
 * @file motion_estimation.cpp
 * @brief 运动估计实现
 *
 * 运动估计算法：
 * - 全搜索（Full Search）
 * - 三步搜索（Three Step Search）
 * - 菱形搜索（Diamond Search）
 * - 六边形搜索（Hexagon Search）
 * - UMHexagonS
 * - EPZS
 */

#include "video/motion_estimation.h"
#include <cstring>
#include <algorithm>
#include <cmath>
#include <limits>

namespace av_codec {

/**
 * @brief 菱形搜索运动估计器
 */
class DiamondSearchME : public IMotionEstimator {
public:
    int init(const MEParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int estimate(const uint8_t* cur_data, int cur_stride,
                const uint8_t* ref_data, int ref_stride,
                int x, int y, MEResult& result) override {
        if (!initialized_) return -1;

        int block_w = params_.block_width;
        int block_h = params_.block_height;
        int search_range = params_.search_range;

        // 从零运动向量开始
        int16_t best_mv_x = 0;
        int16_t best_mv_y = 0;
        uint32_t best_cost = UINT32_MAX;

        // 大菱形搜索
        int large_diamond[9][2] = {
            {0, 0}, {-2, 0}, {2, 0}, {0, -2}, {0, 2},
            {-1, -1}, {1, -1}, {-1, 1}, {1, 1}
        };

        // 小菱形搜索
        int small_diamond[5][2] = {
            {0, 0}, {-1, 0}, {1, 0}, {0, -1}, {0, 1}
        };

        const uint8_t* cur = cur_data + y * cur_stride + x;

        // 大菱形搜索
        bool found = false;
        while (!found) {
            found = true;
            for (int i = 0; i < 9; i++) {
                int16_t mv_x = best_mv_x + large_diamond[i][0];
                int16_t mv_y = best_mv_y + large_diamond[i][1];

                if (mv_x < -search_range || mv_x > search_range ||
                    mv_y < -search_range || mv_y > search_range) {
                    continue;
                }

                int rx = x + mv_x;
                int ry = y + mv_y;
                if (rx < 0 || ry < 0) continue;

                uint32_t cost = calcSAD(cur, cur_stride,
                                       ref_data + ry * ref_stride + rx,
                                       ref_stride, block_w, block_h);

                // 添加运动向量代价
                cost += calcMVCost(mv_x, mv_y, params_.lambda);

                if (cost < best_cost) {
                    best_cost = cost;
                    best_mv_x = mv_x;
                    best_mv_y = mv_y;
                    found = false;
                }
            }
        }

        // 小菱形搜索
        found = false;
        while (!found) {
            found = true;
            for (int i = 0; i < 5; i++) {
                int16_t mv_x = best_mv_x + small_diamond[i][0];
                int16_t mv_y = best_mv_y + small_diamond[i][1];

                int rx = x + mv_x;
                int ry = y + mv_y;
                if (rx < 0 || ry < 0) continue;

                uint32_t cost = calcSAD(cur, cur_stride,
                                       ref_data + ry * ref_stride + rx,
                                       ref_stride, block_w, block_h);
                cost += calcMVCost(mv_x, mv_y, params_.lambda);

                if (cost < best_cost) {
                    best_cost = cost;
                    best_mv_x = mv_x;
                    best_mv_y = mv_y;
                    found = false;
                }
            }
        }

        result.mv_x = best_mv_x;
        result.mv_y = best_mv_y;
        result.cost = best_cost;
        result.sad = best_cost - calcMVCost(best_mv_x, best_mv_y, params_.lambda);
        result.ref_idx = params_.ref_idx;

        return 0;
    }

    int estimateMultiRef(const uint8_t* cur_data, int cur_stride,
                        const std::vector<uint8_t*>& ref_frames,
                        const std::vector<int>& ref_strides,
                        int x, int y, MEResult& result) override {
        MEResult best_result;
        best_result.cost = UINT32_MAX;

        for (size_t i = 0; i < ref_frames.size(); i++) {
            MEParams temp_params = params_;
            temp_params.ref_idx = static_cast<int>(i);

            MEResult ref_result;
            estimate(cur_data, cur_stride, ref_frames[i], ref_strides[i],
                    x, y, ref_result);

            if (ref_result.cost < best_result.cost) {
                best_result = ref_result;
                best_result.ref_idx = static_cast<int>(i);
            }
        }

        result = best_result;
        return 0;
    }

    uint32_t calcSAD(const uint8_t* src, int src_stride,
                    const uint8_t* ref, int ref_stride,
                    int width, int height) override {
        uint32_t sad = 0;
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                sad += std::abs(static_cast<int>(src[y * src_stride + x]) -
                               static_cast<int>(ref[y * ref_stride + x]));
            }
        }
        return sad;
    }

    void close() override {
        initialized_ = false;
    }

private:
    uint32_t calcMVCost(int16_t mv_x, int16_t mv_y, int lambda) {
        // 运动向量代价 = lambda * (|mv_x| + |mv_y|)
        return static_cast<uint32_t>(lambda * (std::abs(mv_x) + std::abs(mv_y)));
    }

private:
    MEParams params_;
    bool initialized_ = false;
};

/**
 * @brief 六边形搜索运动估计器
 */
class HexagonSearchME : public IMotionEstimator {
public:
    int init(const MEParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int estimate(const uint8_t* cur_data, int cur_stride,
                const uint8_t* ref_data, int ref_stride,
                int x, int y, MEResult& result) override {
        if (!initialized_) return -1;

        int block_w = params_.block_width;
        int block_h = params_.block_height;
        int search_range = params_.search_range;

        int16_t best_mv_x = 0;
        int16_t best_mv_y = 0;
        uint32_t best_cost = UINT32_MAX;

        const uint8_t* cur = cur_data + y * cur_stride + x;

        // 六边形搜索点
        int hexagon[7][2] = {
            {0, 0}, {-2, 0}, {2, 0}, {-1, -2}, {1, -2}, {-1, 2}, {1, 2}
        };

        // 六边形搜索
        bool found = false;
        while (!found) {
            found = true;
            for (int i = 0; i < 7; i++) {
                int16_t mv_x = best_mv_x + hexagon[i][0];
                int16_t mv_y = best_mv_y + hexagon[i][1];

                if (mv_x < -search_range || mv_x > search_range ||
                    mv_y < -search_range || mv_y > search_range) {
                    continue;
                }

                int rx = x + mv_x;
                int ry = y + mv_y;
                if (rx < 0 || ry < 0) continue;

                uint32_t cost = calcSAD(cur, cur_stride,
                                       ref_data + ry * ref_stride + rx,
                                       ref_stride, block_w, block_h);
                cost += calcMVCost(mv_x, mv_y, params_.lambda);

                if (cost < best_cost) {
                    best_cost = cost;
                    best_mv_x = mv_x;
                    best_mv_y = mv_y;
                    found = false;
                }
            }
        }

        // 小菱形搜索
        int small_diamond[5][2] = {
            {0, 0}, {-1, 0}, {1, 0}, {0, -1}, {0, 1}
        };

        found = false;
        while (!found) {
            found = true;
            for (int i = 0; i < 5; i++) {
                int16_t mv_x = best_mv_x + small_diamond[i][0];
                int16_t mv_y = best_mv_y + small_diamond[i][1];

                int rx = x + mv_x;
                int ry = y + mv_y;
                if (rx < 0 || ry < 0) continue;

                uint32_t cost = calcSAD(cur, cur_stride,
                                       ref_data + ry * ref_stride + rx,
                                       ref_stride, block_w, block_h);
                cost += calcMVCost(mv_x, mv_y, params_.lambda);

                if (cost < best_cost) {
                    best_cost = cost;
                    best_mv_x = mv_x;
                    best_mv_y = mv_y;
                    found = false;
                }
            }
        }

        result.mv_x = best_mv_x;
        result.mv_y = best_mv_y;
        result.cost = best_cost;
        result.sad = best_cost - calcMVCost(best_mv_x, best_mv_y, params_.lambda);
        result.ref_idx = params_.ref_idx;

        return 0;
    }

    int estimateMultiRef(const uint8_t* cur_data, int cur_stride,
                        const std::vector<uint8_t*>& ref_frames,
                        const std::vector<int>& ref_strides,
                        int x, int y, MEResult& result) override {
        MEResult best_result;
        best_result.cost = UINT32_MAX;

        for (size_t i = 0; i < ref_frames.size(); i++) {
            MEResult ref_result;
            estimate(cur_data, cur_stride, ref_frames[i], ref_strides[i],
                    x, y, ref_result);

            if (ref_result.cost < best_result.cost) {
                best_result = ref_result;
                best_result.ref_idx = static_cast<int>(i);
            }
        }

        result = best_result;
        return 0;
    }

    uint32_t calcSAD(const uint8_t* src, int src_stride,
                    const uint8_t* ref, int ref_stride,
                    int width, int height) override {
        uint32_t sad = 0;
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                sad += std::abs(static_cast<int>(src[y * src_stride + x]) -
                               static_cast<int>(ref[y * ref_stride + x]));
            }
        }
        return sad;
    }

    void close() override { initialized_ = false; }

private:
    uint32_t calcMVCost(int16_t mv_x, int16_t mv_y, int lambda) {
        return static_cast<uint32_t>(lambda * (std::abs(mv_x) + std::abs(mv_y)));
    }

private:
    MEParams params_;
    bool initialized_ = false;
};

// 工厂函数
std::unique_ptr<IMotionEstimator> createMotionEstimator(MESearchAlgo algo) {
    switch (algo) {
        case MESearchAlgo::DIAMOND:
        case MESearchAlgo::FAST_DIAMOND:
            return std::make_unique<DiamondSearchME>();
        case MESearchAlgo::HEXAGON:
            return std::make_unique<HexagonSearchME>();
        default:
            return std::make_unique<DiamondSearchME>();
    }
}

} // namespace av_codec
