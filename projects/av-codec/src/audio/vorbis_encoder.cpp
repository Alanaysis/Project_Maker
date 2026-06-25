/**
 * @file vorbis_encoder.cpp
 * @brief Vorbis 编码器实现
 */

#include "audio/vorbis_codec.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

class VorbisEncoderImpl : public IVorbisEncoder {
public:
    VorbisEncoderImpl() = default;
    ~VorbisEncoderImpl() override { close(); }

    int init(const VorbisEncodeParams& params) override {
        params_ = params;
        if (params_.sample_rate <= 0 || params_.channels <= 0) return -1;

        block_size_ = params_.block_size_max;
        initialized_ = true;
        total_bytes_ = 0;
        total_frames_ = 0;

        return 0;
    }

    int encode(const float* float_data, int samples,
              std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !float_data) return -1;

        out_data.clear();

        for (int offset = 0; offset < samples; offset += block_size_) {
            int block_samples = std::min(block_size_, samples - offset);

            // MDCT变换
            std::vector<float> spectrum(block_samples);
            for (int k = 0; k < block_samples; k++) {
                float sum = 0.0f;
                for (int i = 0; i < block_samples * 2; i++) {
                    sum += float_data[offset + i] *
                           std::cos(M_PI / block_samples * (i + 0.5 + block_samples / 2) * (k + 0.5));
                }
                spectrum[k] = sum;
            }

            // 量化
            float quality = params_.quality;
            for (int i = 0; i < block_samples; i++) {
                int16_t quant = static_cast<int16_t>(spectrum[i] * quality);
                out_data.push_back(static_cast<uint8_t>((quant >> 8) & 0xFF));
                out_data.push_back(static_cast<uint8_t>(quant & 0xFF));
            }
        }

        total_bytes_ += out_data.size();
        total_frames_++;

        return 0;
    }

    int flush(std::vector<uint8_t>& out_data) override {
        out_data.clear();
        return 0;
    }

    VorbisEncodeStats getStats() const override {
        VorbisEncodeStats stats;
        stats.total_bytes = total_bytes_;
        stats.total_frames = total_frames_;
        if (total_frames_ > 0) {
            stats.avg_bitrate = static_cast<double>(total_bytes_ * 8) / total_frames_;
        }
        return stats;
    }

    void close() override {
        initialized_ = false;
    }

private:
    VorbisEncodeParams params_;
    bool initialized_ = false;
    int block_size_ = 4096;
    int64_t total_bytes_ = 0;
    int64_t total_frames_ = 0;
};

std::unique_ptr<IVorbisEncoder> createVorbisEncoder() {
    return std::make_unique<VorbisEncoderImpl>();
}

} // namespace av_codec
