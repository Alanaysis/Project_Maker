/**
 * @file quantization.cpp
 * @brief 量化实现
 *
 * 量化类型：
 * - 标量量化
 * - 死区量化
 * - 自适应量化
 */

#include "video/transform_quant.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

/**
 * @brief 标量量化器
 */
class ScalarQuantizer : public IQuantizer {
public:
    int quantize(const QuantParams& params,
                const int16_t* input, int16_t* output,
                int width, int height) override {
        int qp = params.qp;
        int qstep = getQuantStep(qp);

        for (int i = 0; i < width * height; i++) {
            output[i] = static_cast<int16_t>((input[i] + qstep / 2) / qstep);
        }

        return 0;
    }

    int dequantize(const QuantParams& params,
                  const int16_t* input, int16_t* output,
                  int width, int height) override {
        int qp = params.qp;
        int qstep = getQuantStep(qp);

        for (int i = 0; i < width * height; i++) {
            output[i] = static_cast<int16_t>(input[i] * qstep);
        }

        return 0;
    }

    double getQuantStep(int qp) const override {
        // H.264量化步长表
        static const int qpc[6] = {10, 11, 13, 14, 16, 18};
        return qpc[qp % 6] * (1 << (qp / 6));
    }

    double calcRDCost(const int16_t* coeffs, int width, int height,
                     int qp, double lambda) override {
        double distortion = 0.0;
        int bits = 0;

        for (int i = 0; i < width * height; i++) {
            if (coeffs[i] != 0) {
                distortion += coeffs[i] * coeffs[i];
                bits += 1 + static_cast<int>(std::log2(std::abs(coeffs[i]) + 1));
            }
        }

        return distortion + lambda * bits;
    }
};

/**
 * @brief 死区量化器
 */
class DeadzoneQuantizer : public IQuantizer {
public:
    int quantize(const QuantParams& params,
                const int16_t* input, int16_t* output,
                int width, int height) override {
        int qp = params.qp;
        int qstep = getQuantStep(qp);
        int deadzone = qstep / 3;  // 死区大小

        for (int i = 0; i < width * height; i++) {
            int val = input[i];
            if (std::abs(val) < deadzone) {
                output[i] = 0;
            } else {
                output[i] = static_cast<int16_t>(val / qstep);
            }
        }

        return 0;
    }

    int dequantize(const QuantParams& params,
                  const int16_t* input, int16_t* output,
                  int width, int height) override {
        int qp = params.qp;
        int qstep = getQuantStep(qp);

        for (int i = 0; i < width * height; i++) {
            output[i] = static_cast<int16_t>(input[i] * qstep);
        }

        return 0;
    }

    double getQuantStep(int qp) const override {
        static const int qpc[6] = {10, 11, 13, 14, 16, 18};
        return qpc[qp % 6] * (1 << (qp / 6));
    }

    double calcRDCost(const int16_t* coeffs, int width, int height,
                     int qp, double lambda) override {
        double distortion = 0.0;
        int bits = 0;

        for (int i = 0; i < width * height; i++) {
            if (coeffs[i] != 0) {
                distortion += coeffs[i] * coeffs[i];
                bits += 1 + static_cast<int>(std::log2(std::abs(coeffs[i]) + 1));
            }
        }

        return distortion + lambda * bits;
    }
};

// 工厂函数
std::unique_ptr<IQuantizer> createQuantizer(QuantMode mode) {
    switch (mode) {
        case QuantMode::DEADZONE:
            return std::make_unique<DeadzoneQuantizer>();
        default:
            return std::make_unique<ScalarQuantizer>();
    }
}

} // namespace av_codec
