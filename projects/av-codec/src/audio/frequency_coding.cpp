/**
 * @file frequency_coding.cpp
 * @brief 频域编码实现（FFT, MDCT）
 */

#include "audio/audio_processing.h"
#include <cstring>
#include <cmath>
#include <complex>
#include <vector>

namespace av_codec {

/**
 * @brief FFT 频域编码器
 */
class FFTEncoder : public IFreqEncoder {
public:
    int init(const FreqCodingParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int transform(const float* input, std::complex<float>* output) override {
        int n = params_.frame_size;

        // FFT实现（Cooley-Tukey算法）
        std::vector<std::complex<float>> x(n);
        for (int i = 0; i < n; i++) {
            x[i] = std::complex<float>(input[i], 0);
        }

        // 位反转置换
        int bits = 0;
        int temp = n;
        while (temp > 1) { bits++; temp >>= 1; }

        for (int i = 0; i < n; i++) {
            int j = 0;
            for (int b = 0; b < bits; b++) {
                j = (j << 1) | ((i >> b) & 1);
            }
            if (i < j) std::swap(x[i], x[j]);
        }

        // FFT蝶形运算
        for (int stage = 1; stage <= bits; stage++) {
            int m = 1 << stage;
            int half_m = m / 2;
            std::complex<float> wn = std::exp(std::complex<float>(0, -2.0f * M_PI / m));

            for (int k = 0; k < n; k += m) {
                std::complex<float> w = 1;
                for (int j = 0; j < half_m; j++) {
                    std::complex<float> t = w * x[k + j + half_m];
                    std::complex<float> u = x[k + j];
                    x[k + j] = u + t;
                    x[k + j + half_m] = u - t;
                    w *= wn;
                }
            }
        }

        for (int i = 0; i < n; i++) {
            output[i] = x[i];
        }

        return 0;
    }

    int inverseTransform(const std::complex<float>* input, float* output) override {
        int n = params_.frame_size;

        // IFFT
        std::vector<std::complex<float>> x(n);
        for (int i = 0; i < n; i++) {
            x[i] = std::conj(input[i]);
        }

        // FFT
        std::vector<std::complex<float>> fft_result(n);
        // 简化：直接计算
        for (int i = 0; i < n; i++) {
            std::complex<float> sum = 0;
            for (int k = 0; k < n; k++) {
                float angle = 2.0f * M_PI * i * k / n;
                sum += x[k] * std::exp(std::complex<float>(0, angle));
            }
            fft_result[i] = sum;
        }

        for (int i = 0; i < n; i++) {
            output[i] = std::real(fft_result[i]) / n;
        }

        return 0;
    }

    int applyWindow(float* data, int size, WindowType window) override {
        for (int i = 0; i < size; i++) {
            float w = 1.0f;
            switch (window) {
                case WindowType::HANNING:
                    w = 0.5f * (1.0f - std::cos(2.0f * M_PI * i / (size - 1)));
                    break;
                case WindowType::HAMMING:
                    w = 0.54f - 0.46f * std::cos(2.0f * M_PI * i / (size - 1));
                    break;
                case WindowType::BLACKMAN:
                    w = 0.42f - 0.5f * std::cos(2.0f * M_PI * i / (size - 1))
                       + 0.08f * std::cos(4.0f * M_PI * i / (size - 1));
                    break;
                case WindowType::SINE:
                    w = std::sin(M_PI * i / (size - 1));
                    break;
                default:
                    break;
            }
            data[i] *= w;
        }
        return 0;
    }

    void close() override { initialized_ = false; }

private:
    FreqCodingParams params_;
    bool initialized_ = false;
};

std::unique_ptr<IFreqEncoder> createFreqEncoder() {
    return std::make_unique<FFTEncoder>();
}

} // namespace av_codec
