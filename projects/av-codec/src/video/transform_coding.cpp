/**
 * @file transform_coding.cpp
 * @brief 变换编码实现
 *
 * 变换编码类型：
 * - DCT-II：最常用的变换
 * - DST-I：用于H.265帧内小块
 * - Hadamard：快速近似变换
 * - KLT：最优变换
 */

#include "video/transform_quant.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

/**
 * @brief DCT变换器实现
 */
class DCTTransformer : public ITransformer {
public:
    int forward(const TransformParams& params,
               const int16_t* input, int input_stride,
               int16_t* output, int output_stride) override {
        int width = params.width;
        int height = params.height;

        // 1D DCT行变换
        for (int y = 0; y < height; y++) {
            dct1D(input + y * input_stride, output + y * output_stride, width);
        }

        // 1D DCT列变换
        std::vector<int16_t> temp(width * height);
        for (int x = 0; x < width; x++) {
            std::vector<int16_t> col(height);
            for (int y = 0; y < height; y++) {
                col[y] = output[y * output_stride + x];
            }
            std::vector<int16_t> dct_col(height);
            dct1D(col.data(), dct_col.data(), height);
            for (int y = 0; y < height; y++) {
                temp[y * width + x] = dct_col[y];
            }
        }

        // 复制到输出
        for (int y = 0; y < height; y++) {
            std::memcpy(output + y * output_stride, temp.data() + y * width,
                       width * sizeof(int16_t));
        }

        return 0;
    }

    int inverse(const TransformParams& params,
               const int16_t* input, int input_stride,
               int16_t* output, int output_stride) override {
        int width = params.width;
        int height = params.height;

        // 1D IDCT列变换
        std::vector<int16_t> temp(width * height);
        for (int x = 0; x < width; x++) {
            std::vector<int16_t> col(height);
            for (int y = 0; y < height; y++) {
                col[y] = input[y * input_stride + x];
            }
            std::vector<int16_t> idct_col(height);
            idct1D(col.data(), idct_col.data(), height);
            for (int y = 0; y < height; y++) {
                temp[y * width + x] = idct_col[y];
            }
        }

        // 1D IDCT行变换
        for (int y = 0; y < height; y++) {
            idct1D(temp.data() + y * width, output + y * output_stride, width);
        }

        return 0;
    }

    int transform2D(const TransformParams& params,
                   const int16_t* input, int16_t* output) override {
        return forward(params, input, params.width, output, params.width);
    }

    int inverseTransform2D(const TransformParams& params,
                          const int16_t* input, int16_t* output) override {
        return inverse(params, input, params.width, output, params.width);
    }

private:
    /**
     * @brief 1D DCT-II
     */
    void dct1D(const int16_t* input, int16_t* output, int n) {
        for (int k = 0; k < n; k++) {
            double sum = 0.0;
            for (int i = 0; i < n; i++) {
                sum += input[i] * cos(M_PI * k * (2 * i + 1) / (2 * n));
            }
            if (k == 0) {
                output[k] = static_cast<int16_t>(sum / sqrt(n));
            } else {
                output[k] = static_cast<int16_t>(sum * sqrt(2.0 / n));
            }
        }
    }

    /**
     * @brief 1D IDCT
     */
    void idct1D(const int16_t* input, int16_t* output, int n) {
        for (int i = 0; i < n; i++) {
            double sum = 0.0;
            for (int k = 0; k < n; k++) {
                double coeff = (k == 0) ? 1.0 / sqrt(n) : sqrt(2.0 / n);
                sum += coeff * input[k] * cos(M_PI * k * (2 * i + 1) / (2 * n));
            }
            output[i] = static_cast<int16_t>(std::clamp(sum, -32768.0, 32767.0));
        }
    }
};

/**
 * @brief Hadamard变换器实现
 */
class HadamardTransformer : public ITransformer {
public:
    int forward(const TransformParams& params,
               const int16_t* input, int input_stride,
               int16_t* output, int output_stride) override {
        int size = params.width;

        // Hadamard变换
        hadamard2D(input, input_stride, output, output_stride, size);

        return 0;
    }

    int inverse(const TransformParams& params,
               const int16_t* input, int input_stride,
               int16_t* output, int output_stride) override {
        int size = params.width;

        // Hadamard逆变换（与正变换相同，需除以N）
        hadamard2D(input, input_stride, output, output_stride, size);

        // 归一化
        int n = size * size;
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                output[y * output_stride + x] /= n;
            }
        }

        return 0;
    }

    int transform2D(const TransformParams& params,
                   const int16_t* input, int16_t* output) override {
        return forward(params, input, params.width, output, params.width);
    }

    int inverseTransform2D(const TransformParams& params,
                          const int16_t* input, int16_t* output) override {
        return inverse(params, input, params.width, output, params.width);
    }

private:
    void hadamard2D(const int16_t* input, int input_stride,
                   int16_t* output, int output_stride, int size) {
        // 行变换
        for (int y = 0; y < size; y++) {
            hadamard1D(input + y * input_stride, output + y * output_stride, size);
        }

        // 列变换
        std::vector<int16_t> temp(size * size);
        for (int x = 0; x < size; x++) {
            std::vector<int16_t> col(size);
            for (int y = 0; y < size; y++) {
                col[y] = output[y * output_stride + x];
            }
            std::vector<int16_t> had_col(size);
            hadamard1D(col.data(), had_col.data(), size);
            for (int y = 0; y < size; y++) {
                temp[y * size + x] = had_col[y];
            }
        }

        for (int y = 0; y < size; y++) {
            std::memcpy(output + y * output_stride, temp.data() + y * size,
                       size * sizeof(int16_t));
        }
    }

    void hadamard1D(const int16_t* input, int16_t* output, int n) {
        if (n == 1) {
            output[0] = input[0];
            return;
        }

        int half = n / 2;
        std::vector<int16_t> even(half), odd(half);
        std::vector<int16_t> even_out(half), odd_out(half);

        for (int i = 0; i < half; i++) {
            even[i] = input[i] + input[i + half];
            odd[i] = input[i] - input[i + half];
        }

        hadamard1D(even.data(), even_out.data(), half);
        hadamard1D(odd.data(), odd_out.data(), half);

        for (int i = 0; i < half; i++) {
            output[i] = even_out[i];
            output[i + half] = odd_out[i];
        }
    }
};

// 工厂函数
std::unique_ptr<ITransformer> createTransformer(TransformType type) {
    switch (type) {
        case TransformType::DCT_II:
        case TransformType::DCT_III:
        case TransformType::DCT_I:
            return std::make_unique<DCTTransformer>();
        case TransformType::HADAMARD:
            return std::make_unique<HadamardTransformer>();
        default:
            return std::make_unique<DCTTransformer>();
    }
}

} // namespace av_codec
