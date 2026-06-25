/**
 * @file aac_decoder.cpp
 * @brief AAC 解码器实现
 */

#include "audio/aac_codec.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

class AACDecoderImpl : public IAACDecoder {
public:
    AACDecoderImpl() = default;
    ~AACDecoderImpl() override { close(); }

    int init(const AACDecodeParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int decode(const uint8_t* aac_data, int aac_size,
              std::vector<int16_t>& out_pcm) override {
        if (!initialized_ || !aac_data || aac_size <= 0) return -1;

        out_pcm.clear();

        int pos = 0;
        while (pos < aac_size) {
            // 检查ADTS同步字
            if (pos + 7 <= aac_size && aac_data[pos] == 0xFF && (aac_data[pos + 1] & 0xF0) == 0xF0) {
                // 解析ADTS头
                int frame_size = ((aac_data[pos + 3] & 0x03) << 11) |
                                (aac_data[pos + 4] << 3) |
                                ((aac_data[pos + 5] >> 5) & 0x07);
                int profile = (aac_data[pos + 2] >> 6) & 0x03;
                int sample_rate_idx = (aac_data[pos + 2] >> 2) & 0x0F;
                int channels = ((aac_data[pos + 2] & 0x01) << 2) |
                              ((aac_data[pos + 3] >> 6) & 0x03);

                // 解码帧数据
                std::vector<float> float_pcm;
                decodeFrame(aac_data + pos + 7, frame_size - 7, float_pcm);

                // 转换为int16
                for (float sample : float_pcm) {
                    int16_t pcm_sample = static_cast<int16_t>(
                        std::clamp(sample * 32768.0f, -32768.0f, 32767.0f));
                    out_pcm.push_back(pcm_sample);
                }

                pos += frame_size;
            } else {
                pos++;
            }
        }

        return 0;
    }

    int decodeFloat(const uint8_t* aac_data, int aac_size,
                   std::vector<float>& out_float) override {
        if (!initialized_ || !aac_data || aac_size <= 0) return -1;

        out_float.clear();

        int pos = 0;
        while (pos < aac_size) {
            if (pos + 7 <= aac_size && aac_data[pos] == 0xFF && (aac_data[pos + 1] & 0xF0) == 0xF0) {
                int frame_size = ((aac_data[pos + 3] & 0x03) << 11) |
                                (aac_data[pos + 4] << 3) |
                                ((aac_data[pos + 5] >> 5) & 0x07);

                decodeFrame(aac_data + pos + 7, frame_size - 7, out_float);
                pos += frame_size;
            } else {
                pos++;
            }
        }

        return 0;
    }

    int flush(std::vector<int16_t>& out_pcm) override {
        out_pcm.clear();
        return 0;
    }

    void close() override {
        initialized_ = false;
    }

private:
    void decodeFrame(const uint8_t* data, int size, std::vector<float>& output) {
        // 简化的AAC解码
        // 1. 熵解码
        std::vector<int16_t> quant(size / 2);
        for (int i = 0; i < size / 2; i++) {
            quant[i] = static_cast<int16_t>((data[i * 2] << 8) | data[i * 2 + 1]);
        }

        // 2. 反量化
        std::vector<float> spectrum(size / 2);
        for (int i = 0; i < size / 2; i++) {
            spectrum[i] = quant[i] * 1.0f;
        }

        // 3. IMDCT变换
        std::vector<float> pcm(1024);
        imdctTransform(spectrum.data(), pcm.data(), 1024);

        output.insert(output.end(), pcm.begin(), pcm.end());
    }

    void imdctTransform(const float* input, float* output, int n) {
        // 简化的IMDCT实现
        for (int i = 0; i < n; i++) {
            float sum = 0.0f;
            for (int k = 0; k < n / 2; k++) {
                sum += input[k] * std::cos(M_PI / (n / 2) * (i + 0.5 + n / 4) * (k + 0.5));
            }
            output[i] = sum * 2.0f / n;
        }
    }

private:
    AACDecodeParams params_;
    bool initialized_ = false;
};

std::unique_ptr<IAACDecoder> createAACDecoder() {
    return std::make_unique<AACDecoderImpl>();
}

} // namespace av_codec
