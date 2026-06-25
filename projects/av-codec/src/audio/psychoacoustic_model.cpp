/**
 * @file psychoacoustic_model.cpp
 * @brief 心理声学模型实现
 *
 * 心理声学模型原理：
 * - 绝对听阈：人耳能听到的最小声压级
 * - 掩蔽效应：强信号会掩蔽附近的弱信号
 * - 临界频带：人耳频率分辨率
 */

#include "audio/audio_processing.h"
#include <cstring>
#include <cmath>
#include <vector>

namespace av_codec {

/**
 * @brief 心理声学模型实现
 */
class PsychoacousticModelImpl : public IPsychoacousticModel {
public:
    int init(const PsychoacousticParams& params) override {
        params_ = params;
        initAbsoluteThreshold();
        initBarkBands();
        initialized_ = true;
        return 0;
    }

    int calcMaskingThreshold(const float* spectrum, float* threshold) override {
        int n = params_.frame_size / 2;

        // 计算每个频带的能量
        std::vector<float> band_energy(bark_bands_.size(), 0);
        for (int i = 0; i < n; i++) {
            int band = freqToBark(static_cast<float>(i) * params_.sample_rate / params_.frame_size);
            if (band < bark_bands_.size()) {
                band_energy[band] += spectrum[i] * spectrum[i];
            }
        }

        // 计算掩蔽阈值
        for (int i = 0; i < n; i++) {
            float freq = static_cast<float>(i) * params_.sample_rate / params_.frame_size;
            int band = freqToBark(freq);

            // 绝对听阈
            float abs_threshold = absolute_threshold_[i];

            // 掩蔽阈值（简化）
            float mask_threshold = 0;
            if (band < bark_bands_.size()) {
                mask_threshold = band_energy[band] * 0.1f;
            }

            // 取较大值
            threshold[i] = std::max(abs_threshold, mask_threshold);
        }

        return 0;
    }

    int calcSMR(const float* spectrum, const float* threshold, float* smr) override {
        int n = params_.frame_size / 2;

        for (int i = 0; i < n; i++) {
            float energy = spectrum[i] * spectrum[i];
            if (threshold[i] > 0) {
                smr[i] = 10.0f * std::log10(energy / threshold[i]);
            } else {
                smr[i] = 100.0f;  // 很大的SMR
            }
        }

        return 0;
    }

    float calcPerceptualEntropy(const float* spectrum) override {
        int n = params_.frame_size / 2;
        float pe = 0;

        for (int i = 0; i < n; i++) {
            if (spectrum[i] != 0) {
                float energy = spectrum[i] * spectrum[i];
                if (energy > 0) {
                    pe -= energy * std::log2(energy);
                }
            }
        }

        return pe;
    }

    void close() override { initialized_ = false; }

private:
    void initAbsoluteThreshold() {
        int n = params_.frame_size / 2;
        absolute_threshold_.resize(n);

        for (int i = 0; i < n; i++) {
            float freq = static_cast<float>(i) * params_.sample_rate / params_.frame_size;
            if (freq < 20.0f) {
                absolute_threshold_[i] = 100.0f;
            } else {
                // ISO 226 绝对听阈近似
                absolute_threshold_[i] = 3.64f * std::pow(freq / 1000.0f, -0.8f)
                                       - 6.5f * std::exp(-0.6f * std::pow(freq / 1000.0f - 3.3f, 2))
                                       + 1e-3f * std::pow(freq / 1000.0f, 4);
            }
        }
    }

    void initBarkBands() {
        // Bark频带边界（Hz）
        static const float bark_edges[] = {
            20, 100, 200, 300, 400, 510, 630, 770, 920, 1080,
            1270, 1480, 1720, 2000, 2320, 2700, 3150, 3700, 4400,
            5300, 6400, 7700, 9500, 12000, 15500, 20000
        };

        bark_bands_.assign(bark_edges, bark_edges + 25);
    }

    int freqToBark(float freq) {
        for (int i = 0; i < bark_bands_.size() - 1; i++) {
            if (freq < bark_bands_[i + 1]) return i;
        }
        return bark_bands_.size() - 1;
    }

private:
    PsychoacousticParams params_;
    bool initialized_ = false;
    std::vector<float> absolute_threshold_;
    std::vector<float> bark_bands_;
};

std::unique_ptr<IPsychoacousticModel> createPsychoacousticModel() {
    return std::make_unique<PsychoacousticModelImpl>();
}

} // namespace av_codec
