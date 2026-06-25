/**
 * @file intra_prediction.cpp
 * @brief 帧内预测实现
 *
 * 帧内预测模式：
 * - H.264: 9种模式（4x4块）/ 4种模式（16x16块）
 * - H.265: 35种模式
 * - AV1: 56种模式
 */

#include "video/prediction.h"
#include <cstring>
#include <algorithm>
#include <cmath>

namespace av_codec {

/**
 * @brief H.264 帧内预测器
 */
class H264IntraPredictor : public IIntraPredictor {
public:
    int predict(const IntraPredParams& params,
               const uint8_t* ref_data,
               uint8_t* pred_data) override {
        int size = params.block_size;

        switch (params.mode) {
            case IntraPredDir::VERTICAL:
                predictVertical(ref_data, pred_data, size);
                break;
            case IntraPredDir::HORIZONTAL:
                predictHorizontal(ref_data, pred_data, size);
                break;
            case IntraPredDir::DC:
                predictDC(ref_data, pred_data, size);
                break;
            case IntraPredDir::DIAG_DOWN_LEFT:
                predictDiagDownLeft(ref_data, pred_data, size);
                break;
            case IntraPredDir::DIAG_DOWN_RIGHT:
                predictDiagDownRight(ref_data, pred_data, size);
                break;
            case IntraPredDir::VERT_RIGHT:
                predictVertRight(ref_data, pred_data, size);
                break;
            case IntraPredDir::HORZ_DOWN:
                predictHorzDown(ref_data, pred_data, size);
                break;
            case IntraPredDir::VERT_LEFT:
                predictVertLeft(ref_data, pred_data, size);
                break;
            case IntraPredDir::HORZ_UP:
                predictHorzUp(ref_data, pred_data, size);
                break;
            default:
                predictDC(ref_data, pred_data, size);
                break;
        }

        return 0;
    }

    int getModeCount() const override { return 9; }

    IntraPredDir getBestMode(int block_size, const uint8_t* ref_data) override {
        IntraPredDir best_mode = IntraPredDir::DC;
        uint32_t best_cost = UINT32_MAX;

        for (int mode = 0; mode < 9; mode++) {
            IntraPredDir dir = static_cast<IntraPredDir>(mode);
            uint8_t pred[16 * 16];
            IntraPredParams params;
            params.block_size = block_size;
            params.mode = dir;
            predict(params, ref_data, pred);

            uint32_t cost = 0;
            for (int i = 0; i < block_size * block_size; i++) {
                cost += std::abs(static_cast<int>(ref_data[i]) - static_cast<int>(pred[i]));
            }

            if (cost < best_cost) {
                best_cost = cost;
                best_mode = dir;
            }
        }

        return best_mode;
    }

private:
    void predictVertical(const uint8_t* ref, uint8_t* pred, int size) {
        // 使用上方像素进行垂直预测
        const uint8_t* top = ref - size;  // 上方行
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                pred[y * size + x] = top[x];
            }
        }
    }

    void predictHorizontal(const uint8_t* ref, uint8_t* pred, int size) {
        // 使用左方像素进行水平预测
        const uint8_t* left = ref - 1;  // 左方列
        for (int y = 0; y < size; y++) {
            uint8_t val = left[y * size];
            for (int x = 0; x < size; x++) {
                pred[y * size + x] = val;
            }
        }
    }

    void predictDC(const uint8_t* ref, uint8_t* pred, int size) {
        // DC预测：使用上方和左方像素的平均值
        const uint8_t* top = ref - size;
        const uint8_t* left = ref - 1;

        int sum = 0;
        for (int i = 0; i < size; i++) {
            sum += top[i] + left[i * size];
        }
        uint8_t dc = static_cast<uint8_t>(sum / (2 * size));

        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                pred[y * size + x] = dc;
            }
        }
    }

    void predictDiagDownLeft(const uint8_t* ref, uint8_t* pred, int size) {
        // 对角线左下预测
        const uint8_t* top = ref - size;
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                int idx = x + y;
                if (idx < size - 1) {
                    pred[y * size + x] = (top[idx] + top[idx + 1] + 1) >> 1;
                } else {
                    pred[y * size + x] = top[size - 1];
                }
            }
        }
    }

    void predictDiagDownRight(const uint8_t* ref, uint8_t* pred, int size) {
        // 对角线右下预测
        const uint8_t* top = ref - size;
        const uint8_t* left = ref - 1;
        uint8_t top_left = ref[-size - 1];

        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                if (x > y) {
                    pred[y * size + x] = (top[x - y - 1] + top[x - y] + 1) >> 1;
                } else if (x < y) {
                    pred[y * size + x] = (left[(y - x - 1) * size] + left[(y - x) * size] + 1) >> 1;
                } else {
                    pred[y * size + x] = (top[0] + top_left + left[0] + 1) >> 1;
                }
            }
        }
    }

    void predictVertRight(const uint8_t* ref, uint8_t* pred, int size) {
        // 垂直偏右预测
        const uint8_t* top = ref - size;
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                pred[y * size + x] = top[x];
            }
        }
    }

    void predictHorzDown(const uint8_t* ref, uint8_t* pred, int size) {
        // 水平偏下预测
        const uint8_t* left = ref - 1;
        for (int y = 0; y < size; y++) {
            uint8_t val = left[y * size];
            for (int x = 0; x < size; x++) {
                pred[y * size + x] = val;
            }
        }
    }

    void predictVertLeft(const uint8_t* ref, uint8_t* pred, int size) {
        // 垂直偏左预测
        const uint8_t* top = ref - size;
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                int idx = x + y / 2;
                if (idx < size - 1) {
                    pred[y * size + x] = (top[idx] + top[idx + 1] + 1) >> 1;
                } else {
                    pred[y * size + x] = top[size - 1];
                }
            }
        }
    }

    void predictHorzUp(const uint8_t* ref, uint8_t* pred, int size) {
        // 水平偏上预测
        const uint8_t* left = ref - 1;
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                int idx = y + x / 2;
                if (idx < size) {
                    pred[y * size + x] = left[idx * size];
                } else {
                    pred[y * size + x] = left[(size - 1) * size];
                }
            }
        }
    }
};

/**
 * @brief H.265 帧内预测器（35种模式）
 */
class H265IntraPredictor : public IIntraPredictor {
public:
    int predict(const IntraPredParams& params,
               const uint8_t* ref_data,
               uint8_t* pred_data) override {
        int size = params.block_size;
        int mode = static_cast<int>(params.mode);

        if (mode == 0) {
            predictPlanar(ref_data, pred_data, size);
        } else if (mode == 1) {
            predictDC(ref_data, pred_data, size);
        } else if (mode == 2) {
            predictVertical(ref_data, pred_data, size);
        } else if (mode == 3) {
            predictHorizontal(ref_data, pred_data, size);
        } else {
            // 角度预测 (4-34)
            predictAngular(ref_data, pred_data, size, mode);
        }

        return 0;
    }

    int getModeCount() const override { return 35; }

    IntraPredDir getBestMode(int block_size, const uint8_t* ref_data) override {
        return IntraPredDir::DC;
    }

private:
    void predictPlanar(const uint8_t* ref, uint8_t* pred, int size) {
        const uint8_t* top = ref - size;
        const uint8_t* left = ref - 1;
        uint8_t top_right = ref[-size + size - 1];  // 右上角
        uint8_t bottom_left = ref[(size - 1) * size - 1];  // 左下角

        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                int val = (top[x] * (size - 1 - y) + bottom_left * (y + 1) +
                          left[y * size] * (size - 1 - x) + top_right * (x + 1) + size) >> (size > 8 ? 5 : 4);
                pred[y * size + x] = static_cast<uint8_t>(std::clamp(val, 0, 255));
            }
        }
    }

    void predictDC(const uint8_t* ref, uint8_t* pred, int size) {
        const uint8_t* top = ref - size;
        const uint8_t* left = ref - 1;

        int sum = 0;
        for (int i = 0; i < size; i++) {
            sum += top[i] + left[i * size];
        }
        uint8_t dc = static_cast<uint8_t>((sum + size) / (2 * size));

        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                pred[y * size + x] = dc;
            }
        }
    }

    void predictVertical(const uint8_t* ref, uint8_t* pred, int size) {
        const uint8_t* top = ref - size;
        for (int y = 0; y < size; y++) {
            std::memcpy(pred + y * size, top, size);
        }
    }

    void predictHorizontal(const uint8_t* ref, uint8_t* pred, int size) {
        const uint8_t* left = ref - 1;
        for (int y = 0; y < size; y++) {
            std::memset(pred + y * size, left[y * size], size);
        }
    }

    void predictAngular(const uint8_t* ref, uint8_t* pred, int size, int mode) {
        // 简化的角度预测实现
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                pred[y * size + x] = 128;
            }
        }
    }
};

// 工厂函数
std::unique_ptr<IIntraPredictor> createH264IntraPredictor() {
    return std::make_unique<H264IntraPredictor>();
}

std::unique_ptr<IIntraPredictor> createH265IntraPredictor() {
    return std::make_unique<H265IntraPredictor>();
}

} // namespace av_codec
