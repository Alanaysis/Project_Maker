/**
 * @file temporal_coding.cpp
 * @brief 时域编码实现（线性预测, CELP）
 */

#include "audio/audio_processing.h"
#include <cstring>
#include <cmath>
#include <vector>

namespace av_codec {

/**
 * @brief 时域编码器实现
 */
class TemporalEncoderImpl : public ITemporalEncoder {
public:
    int init(const TemporalCodingParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int lpcAnalysis(const float* input, float* lpc, int order) override {
        int n = params_.frame_size;

        // 自相关法
        std::vector<float> autocorr(order + 1, 0);
        for (int i = 0; i <= order; i++) {
            for (int j = 0; j < n - i; j++) {
                autocorr[i] += input[j] * input[j + i];
            }
        }

        // Levinson-Durbin算法
        std::vector<float> a(order + 1), a_prev(order + 1);
        float error = autocorr[0];

        if (error < 1e-10) {
            for (int i = 0; i < order; i++) lpc[i] = 0;
            return 0;
        }

        for (int i = 1; i <= order; i++) {
            float lambda = 0;
            for (int j = 1; j < i; j++) {
                lambda += a_prev[j] * autocorr[i - j];
            }
            lambda = (autocorr[i] - lambda) / error;

            a[i] = lambda;
            for (int j = 1; j < i; j++) {
                a[j] = a_prev[j] - lambda * a_prev[i - j];
            }

            error *= (1 - lambda * lambda);
            if (error < 1e-10) error = 1e-10;
            a_prev = a;
        }

        for (int i = 0; i < order; i++) {
            lpc[i] = a[i + 1];
        }

        return 0;
    }

    int encode(const float* input, std::vector<uint8_t>& output) override {
        int n = params_.frame_size;
        int order = params_.lpc_order;

        // LPC分析
        std::vector<float> lpc(order);
        lpcAnalysis(input, lpc.data(), order);

        // 计算残差
        std::vector<float> residual(n);
        for (int i = 0; i < n; i++) {
            float pred = 0;
            for (int j = 0; j < order && i - j - 1 >= 0; j++) {
                pred += lpc[j] * input[i - j - 1];
            }
            residual[i] = input[i] - pred;
        }

        // 量化LPC系数
        for (int i = 0; i < order; i++) {
            int16_t quant = static_cast<int16_t>(lpc[i] * 4096);
            output.push_back(static_cast<uint8_t>((quant >> 8) & 0xFF));
            output.push_back(static_cast<uint8_t>(quant & 0xFF));
        }

        // 量化残差
        for (int i = 0; i < n; i++) {
            int16_t quant = static_cast<int16_t>(residual[i] * 256);
            output.push_back(static_cast<uint8_t>((quant >> 8) & 0xFF));
            output.push_back(static_cast<uint8_t>(quant & 0xFF));
        }

        return 0;
    }

    int decode(const uint8_t* input, int size, float* output) override {
        int order = params_.lpc_order;
        int pos = 0;

        // 读取LPC系数
        std::vector<float> lpc(order);
        for (int i = 0; i < order && pos + 2 <= size; i++) {
            int16_t quant = static_cast<int16_t>((input[pos] << 8) | input[pos + 1]);
            lpc[i] = quant / 4096.0f;
            pos += 2;
        }

        // 读取残差
        int n = params_.frame_size;
        std::vector<float> residual(n);
        for (int i = 0; i < n && pos + 2 <= size; i++) {
            int16_t quant = static_cast<int16_t>((input[pos] << 8) | input[pos + 1]);
            residual[i] = quant / 256.0f;
            pos += 2;
        }

        // 重建信号
        for (int i = 0; i < n; i++) {
            float pred = 0;
            for (int j = 0; j < order && i - j - 1 >= 0; j++) {
                pred += lpc[j] * output[i - j - 1];
            }
            output[i] = residual[i] + pred;
        }

        return 0;
    }

    void close() override { initialized_ = false; }

private:
    TemporalCodingParams params_;
    bool initialized_ = false;
};

std::unique_ptr<ITemporalEncoder> createTemporalEncoder() {
    return std::make_unique<TemporalEncoderImpl>();
}

} // namespace av_codec
