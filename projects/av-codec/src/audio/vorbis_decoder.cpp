/**
 * @file vorbis_decoder.cpp
 * @brief Vorbis 解码器实现
 */

#include "audio/vorbis_codec.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

class VorbisDecoderImpl : public IVorbisDecoder {
public:
    VorbisDecoderImpl() = default;
    ~VorbisDecoderImpl() override { close(); }

    int init(const VorbisDecodeParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int decode(const uint8_t* vorbis_data, int vorbis_size,
              std::vector<float>& out_float) override {
        if (!initialized_ || !vorbis_data || vorbis_size <= 0) return -1;

        out_float.clear();

        // 反量化
        int samples = vorbis_size / 2;
        std::vector<float> spectrum(samples);
        for (int i = 0; i < samples; i++) {
            int16_t quant = static_cast<int16_t>((vorbis_data[i * 2] << 8) | vorbis_data[i * 2 + 1]);
            spectrum[i] = quant / 4.0f;
        }

        // IMDCT变换
        for (int i = 0; i < samples; i++) {
            float sum = 0.0f;
            for (int k = 0; k < samples / 2; k++) {
                sum += spectrum[k] *
                       std::cos(M_PI / (samples / 2) * (i + 0.5 + samples / 4) * (k + 0.5));
            }
            out_float.push_back(sum * 2.0f / samples);
        }

        return 0;
    }

    void close() override {
        initialized_ = false;
    }

private:
    VorbisDecodeParams params_;
    bool initialized_ = false;
};

std::unique_ptr<IVorbisDecoder> createVorbisDecoder() {
    return std::make_unique<VorbisDecoderImpl>();
}

} // namespace av_codec
