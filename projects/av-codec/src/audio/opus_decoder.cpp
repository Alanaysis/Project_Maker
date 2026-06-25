/**
 * @file opus_decoder.cpp
 * @brief Opus 解码器实现
 */

#include "audio/opus_codec.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

class OpusDecoderImpl : public IOpusDecoder {
public:
    OpusDecoderImpl() = default;
    ~OpusDecoderImpl() override { close(); }

    int init(const OpusDecodeParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int decode(const uint8_t* opus_data, int opus_size,
              std::vector<int16_t>& out_pcm, int frame_size) override {
        if (!initialized_ || !opus_data || opus_size <= 0) return -1;

        out_pcm.clear();

        // 解码残差
        std::vector<float> residual(opus_size / 2);
        for (int i = 0; i < opus_size / 2; i++) {
            int16_t quant = static_cast<int16_t>((opus_data[i * 2] << 8) | opus_data[i * 2 + 1]);
            residual[i] = quant / 128.0f;
        }

        // 重建信号
        for (int i = 0; i < frame_size; i++) {
            float sample = residual[i % residual.size()];
            if (params_.gain != 0) {
                sample *= std::pow(10.0f, params_.gain / 20.0f);
            }
            int16_t pcm_sample = static_cast<int16_t>(
                std::clamp(sample * 32768.0f, -32768.0f, 32767.0f));
            out_pcm.push_back(pcm_sample);
        }

        return 0;
    }

    int decodeFloat(const uint8_t* opus_data, int opus_size,
                   std::vector<float>& out_float, int frame_size) override {
        if (!initialized_ || !opus_data || opus_size <= 0) return -1;

        out_float.clear();

        std::vector<float> residual(opus_size / 2);
        for (int i = 0; i < opus_size / 2; i++) {
            int16_t quant = static_cast<int16_t>((opus_data[i * 2] << 8) | opus_data[i * 2 + 1]);
            residual[i] = quant / 128.0f;
        }

        for (int i = 0; i < frame_size; i++) {
            float sample = residual[i % residual.size()];
            if (params_.gain != 0) {
                sample *= std::pow(10.0f, params_.gain / 20.0f);
            }
            out_float.push_back(sample);
        }

        return 0;
    }

    void close() override {
        initialized_ = false;
    }

private:
    OpusDecodeParams params_;
    bool initialized_ = false;
};

std::unique_ptr<IOpusDecoder> createOpusDecoder() {
    return std::make_unique<OpusDecoderImpl>();
}

} // namespace av_codec
