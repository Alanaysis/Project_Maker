/**
 * @file mp3_decoder.cpp
 * @brief MP3 解码器实现
 */

#include "audio/mp3_codec.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

class MP3DecoderImpl : public IMP3Decoder {
public:
    MP3DecoderImpl() = default;
    ~MP3DecoderImpl() override { close(); }

    int init(const MP3DecodeParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int decode(const uint8_t* mp3_data, int mp3_size,
              std::vector<int16_t>& out_pcm) override {
        if (!initialized_ || !mp3_data || mp3_size <= 0) return -1;

        out_pcm.clear();

        int pos = 0;
        while (pos < mp3_size) {
            // 查找帧同步字
            if (pos + 4 <= mp3_size && mp3_data[pos] == 0xFF && (mp3_data[pos + 1] & 0xE0) == 0xE0) {
                // 解析帧头
                int bitrate_idx = (mp3_data[pos + 2] >> 4) & 0x0F;
                int samplerate_idx = (mp3_data[pos + 2] >> 2) & 0x03;
                int channel_mode = (mp3_data[pos + 3] >> 6) & 0x03;

                // 计算帧大小
                int bitrate = bitrate_idx * 8000;  // 简化
                int frame_size = 144 * bitrate / 44100;

                // 解码帧数据
                std::vector<float> float_pcm;
                decodeFrame(mp3_data + pos + 4, frame_size - 4, float_pcm,
                           channel_mode == 3 ? 1 : 2);

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

    int decodeFloat(const uint8_t* mp3_data, int mp3_size,
                   std::vector<float>& out_float) override {
        if (!initialized_ || !mp3_data || mp3_size <= 0) return -1;

        out_float.clear();

        int pos = 0;
        while (pos < mp3_size) {
            if (pos + 4 <= mp3_size && mp3_data[pos] == 0xFF && (mp3_data[pos + 1] & 0xE0) == 0xE0) {
                int bitrate_idx = (mp3_data[pos + 2] >> 4) & 0x0F;
                int channel_mode = (mp3_data[pos + 3] >> 6) & 0x03;

                int bitrate = bitrate_idx * 8000;
                int frame_size = 144 * bitrate / 44100;

                decodeFrame(mp3_data + pos + 4, frame_size - 4, out_float,
                           channel_mode == 3 ? 1 : 2);

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
    void decodeFrame(const uint8_t* data, int size, std::vector<float>& output,
                    int channels) {
        // 简化的MP3解码
        int samples = 1152;

        // 读取量化数据
        std::vector<int16_t> quant(size / 2);
        for (int i = 0; i < size / 2; i++) {
            quant[i] = static_cast<int16_t>((data[i * 2] << 8) | data[i * 2 + 1]);
        }

        // 反量化
        std::vector<float> spectrum(size / 2);
        for (int i = 0; i < size / 2; i++) {
            spectrum[i] = quant[i] * 1.0f;
        }

        // IMDCT变换
        std::vector<float> pcm(samples);
        imdctTransform(spectrum.data(), pcm.data(), samples);

        // 输出
        for (int i = 0; i < samples; i++) {
            output.push_back(pcm[i]);
            if (channels == 2) {
                output.push_back(pcm[i]);  // 简化：复制到右声道
            }
        }
    }

    void imdctTransform(const float* input, float* output, int n) {
        for (int i = 0; i < n; i++) {
            float sum = 0.0f;
            for (int k = 0; k < n / 2; k++) {
                sum += input[k] * std::cos(M_PI / (n / 2) * (i + 0.5 + n / 4) * (k + 0.5));
            }
            output[i] = sum * 2.0f / n;
        }
    }

private:
    MP3DecodeParams params_;
    bool initialized_ = false;
};

std::unique_ptr<IMP3Decoder> createMP3Decoder() {
    return std::make_unique<MP3DecoderImpl>();
}

} // namespace av_codec
