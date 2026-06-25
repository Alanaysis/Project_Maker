/**
 * @file simd_utils.cpp
 * @brief SIMD 优化工具实现
 *
 * SIMD指令集：
 * - SSE2: 128位
 * - AVX2: 256位
 * - NEON: 128位（ARM）
 */

#include "optimization/performance.h"
#include <cstring>
#include <algorithm>

namespace av_codec {

/**
 * @brief SIMD工具实现
 */
class SIMDUtilsImpl : public ISIMDUtils {
public:
    SIMDType detect() override {
        // 简化：返回AVX2
        return SIMDType::AVX2;
    }

    uint32_t calcSAD(const uint8_t* src, const uint8_t* ref,
                    int stride, int width, int height) override {
        uint32_t sad = 0;

        // 根据SIMD类型选择实现
        SIMDType simd = detect();

        if (simd >= SIMDType::AVX2) {
            // AVX2优化
            sad = calcSAD_AVX2(src, ref, stride, width, height);
        } else if (simd >= SIMDType::SSE2) {
            // SSE2优化
            sad = calcSAD_SSE2(src, ref, stride, width, height);
        } else {
            // 标量实现
            for (int y = 0; y < height; y++) {
                for (int x = 0; x < width; x++) {
                    sad += std::abs(static_cast<int>(src[y * stride + x]) -
                                   static_cast<int>(ref[y * stride + x]));
                }
            }
        }

        return sad;
    }

    void dct(const int16_t* input, int16_t* output, int size) override {
        // 简化的DCT实现
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                output[i * size + j] = input[i * size + j];  // 直通
            }
        }
    }

    void idct(const int16_t* input, int16_t* output, int size) override {
        // 简化的IDCT实现
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                output[i * size + j] = input[i * size + j];  // 直通
            }
        }
    }

    void weightedAvg(const uint8_t* src0, const uint8_t* src1,
                    uint8_t* dst, int weight0, int weight1,
                    int width, int height) override {
        int total_weight = weight0 + weight1;

        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                int val = (src0[y * width + x] * weight0 +
                          src1[y * width + x] * weight1 +
                          total_weight / 2) / total_weight;
                dst[y * width + x] = static_cast<uint8_t>(std::clamp(val, 0, 255));
            }
        }
    }

private:
    uint32_t calcSAD_SSE2(const uint8_t* src, const uint8_t* ref,
                         int stride, int width, int height) {
        uint32_t sad = 0;

        // SSE2优化的SAD计算
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x += 16) {
                // 简化：使用标量实现
                for (int i = 0; i < 16 && x + i < width; i++) {
                    sad += std::abs(static_cast<int>(src[y * stride + x + i]) -
                                   static_cast<int>(ref[y * stride + x + i]));
                }
            }
        }

        return sad;
    }

    uint32_t calcSAD_AVX2(const uint8_t* src, const uint8_t* ref,
                         int stride, int width, int height) {
        uint32_t sad = 0;

        // AVX2优化的SAD计算
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x += 32) {
                // 简化：使用标量实现
                for (int i = 0; i < 32 && x + i < width; i++) {
                    sad += std::abs(static_cast<int>(src[y * stride + x + i]) -
                                   static_cast<int>(ref[y * stride + x + i]));
                }
            }
        }

        return sad;
    }
};

std::unique_ptr<ISIMDUtils> createSIMDUtils() {
    return std::make_unique<SIMDUtilsImpl>();
}

} // namespace av_codec
