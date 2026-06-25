/**
 * @file mp3_encoder.cpp
 * @brief MP3 编码器实现
 *
 * MP3编码流程：
 * 1. 分帧和加窗
 * 2. MDCT变换
 * 3. 心理声学模型
 * 4. 比特分配
 * 5. 量化和编码
 * 6. 帧封装
 */

#include "audio/mp3_codec.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

class MP3EncoderImpl : public IMP3Encoder {
public:
    MP3EncoderImpl() = default;
    ~MP3EncoderImpl() override { close(); }

    int init(const MP3EncodeParams& params) override {
        params_ = params;

        if (params_.sample_rate <= 0 || params_.channels <= 0) return -1;
        if (params_.channels > MP3_MAX_CHANNELS) return -2;

        frame_size_ = MP3_FRAME_SIZE;
        mdct_buffer_.resize(frame_size_ * 2, 0);

        initPsychoacousticModel();
        initBitrateTable();

        initialized_ = true;
        total_bytes_ = 0;
        total_frames_ = 0;

        return 0;
    }

    int encode(const int16_t* pcm_left, const int16_t* pcm_right,
              int samples, std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !pcm_left) return -1;

        out_data.clear();

        for (int offset = 0; offset < samples; offset += frame_size_) {
            int frame_samples = std::min(frame_size_, samples - offset);

            // 编码一帧
            std::vector<uint8_t> frame_data;
            encodeFrame(pcm_left + offset, pcm_right ? pcm_right + offset : nullptr,
                       frame_samples, frame_data);

            out_data.insert(out_data.end(), frame_data.begin(), frame_data.end());
        }

        total_bytes_ += out_data.size();
        total_frames_++;

        return 0;
    }

    int encodeInterleaved(const int16_t* pcm_data, int samples,
                         std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !pcm_data) return -1;

        out_data.clear();

        // 分离左右声道
        std::vector<int16_t> left(samples), right(samples);
        for (int i = 0; i < samples; i++) {
            left[i] = pcm_data[i * 2];
            right[i] = pcm_data[i * 2 + 1];
        }

        return encode(left.data(), right.data(), samples, out_data);
    }

    int flush(std::vector<uint8_t>& out_data) override {
        out_data.clear();
        return 0;
    }

    MP3EncodeStats getStats() const override {
        MP3EncodeStats stats;
        stats.total_bytes = total_bytes_;
        stats.total_frames = total_frames_;
        if (total_frames_ > 0) {
            stats.avg_bitrate = static_cast<double>(total_bytes_ * 8) / total_frames_ / 1000;
        }
        return stats;
    }

    void close() override {
        initialized_ = false;
        mdct_buffer_.clear();
    }

private:
    void initPsychoacousticModel() {
        // 初始化心理声学模型
        absolute_threshold_.resize(frame_size_ / 2);
        for (int i = 0; i < frame_size_ / 2; i++) {
            double freq = static_cast<double>(i) * params_.sample_rate / frame_size_;
            absolute_threshold_[i] = 3.64 * std::pow(freq / 1000.0, -0.8)
                                   - 6.5 * std::exp(-0.6 * std::pow(freq / 1000.0 - 3.3, 2))
                                   + 1e-3 * std::pow(freq / 1000.0, 4);
        }
    }

    void initBitrateTable() {
        // MP3比特率表 (kbps)
        static const int bitrate_table[2][3][15] = {
            // MPEG-1
            {
                {0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320},  // Layer I
                {0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384},  // Layer II
                {0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320}   // Layer III
            },
            // MPEG-2
            {
                {0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256},
                {0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160},
                {0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160}
            }
        };
    }

    void encodeFrame(const int16_t* pcm_left, const int16_t* pcm_right,
                    int samples, std::vector<uint8_t>& output) {
        // 1. MDCT变换
        std::vector<float> spectrum_left(frame_size_), spectrum_right(frame_size_);
        mdctTransform(pcm_left, spectrum_left.data(), samples);
        if (pcm_right) {
            mdctTransform(pcm_right, spectrum_right.data(), samples);
        }

        // 2. 心理声学分析
        std::vector<float> threshold(frame_size_ / 2);
        calcMaskingThreshold(spectrum_left.data(), threshold.data(), frame_size_ / 2);

        // 3. 量化
        std::vector<int16_t> quant_left(frame_size_ / 2), quant_right(frame_size_ / 2);
        quantize(spectrum_left.data(), threshold.data(), quant_left.data(), frame_size_ / 2);
        if (pcm_right) {
            quantize(spectrum_right.data(), threshold.data(), quant_right.data(), frame_size_ / 2);
        }

        // 4. 写入帧头
        writeFrameHeader(output);

        // 5. 写入量化数据
        for (int i = 0; i < frame_size_ / 2; i++) {
            output.push_back(static_cast<uint8_t>((quant_left[i] >> 8) & 0xFF));
            output.push_back(static_cast<uint8_t>(quant_left[i] & 0xFF));
        }
        if (pcm_right) {
            for (int i = 0; i < frame_size_ / 2; i++) {
                output.push_back(static_cast<uint8_t>((quant_right[i] >> 8) & 0xFF));
                output.push_back(static_cast<uint8_t>(quant_right[i] & 0xFF));
            }
        }
    }

    void mdctTransform(const int16_t* input, float* output, int n) {
        for (int k = 0; k < n; k++) {
            float sum = 0.0f;
            for (int i = 0; i < n * 2; i++) {
                sum += input[i] * std::cos(M_PI / n * (i + 0.5 + n / 2) * (k + 0.5));
            }
            output[k] = sum;
        }
    }

    void calcMaskingThreshold(const float* spectrum, float* threshold, int n) {
        for (int i = 0; i < n; i++) {
            threshold[i] = absolute_threshold_[i];
        }
    }

    void quantize(const float* spectrum, const float* threshold,
                 int16_t* output, int n) {
        for (int i = 0; i < n; i++) {
            float step = threshold[i] > 0 ? threshold[i] : 1.0f;
            output[i] = static_cast<int16_t>(std::round(spectrum[i] / step));
        }
    }

    void writeFrameHeader(std::vector<uint8_t>& output) {
        // MP3帧头
        output.push_back(0xFF);  // 同步字
        output.push_back(0xFB);  // MPEG-1, Layer III, 无CRC

        // 比特率和采样率
        int bitrate_idx = getBitrateIndex(params_.bitrate);
        int samplerate_idx = getSampleRateIndex(params_.sample_rate);
        output.push_back(static_cast<uint8_t>((bitrate_idx << 4) | (samplerate_idx << 2)));

        // 声道模式
        int channel_mode = (params_.channels == 1) ? 3 : 0;
        output.push_back(static_cast<uint8_t>((channel_mode << 6) | 0x00));
    }

    int getBitrateIndex(int bitrate) {
        // 简化：返回默认索引
        return 9;  // 128kbps
    }

    int getSampleRateIndex(int sample_rate) {
        if (sample_rate == 44100) return 0;
        if (sample_rate == 48000) return 1;
        if (sample_rate == 32000) return 2;
        return 0;
    }

private:
    MP3EncodeParams params_;
    bool initialized_ = false;
    int frame_size_ = 1152;
    std::vector<float> mdct_buffer_;
    std::vector<float> absolute_threshold_;
    int64_t total_bytes_ = 0;
    int64_t total_frames_ = 0;
};

std::unique_ptr<IMP3Encoder> createMP3Encoder() {
    return std::make_unique<MP3EncoderImpl>();
}

} // namespace av_codec
