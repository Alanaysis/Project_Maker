/**
 * @file aac_encoder.cpp
 * @brief AAC 编码器实现
 *
 * AAC编码流程：
 * 1. 时域到频域变换（MDCT）
 * 2. 心理声学模型分析
 * 3. 量化和编码
 * 4. 无噪声编码（Huffman）
 * 5. ADTS/RAW封装
 */

#include "audio/aac_codec.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

class AACEncoderImpl : public IAACEncoder {
public:
    AACEncoderImpl() = default;
    ~AACEncoderImpl() override { close(); }

    int init(const AACEncodeParams& params) override {
        params_ = params;

        // 验证参数
        if (params_.sample_rate <= 0 || params_.channels <= 0) return -1;
        if (params_.channels > AAC_MAX_CHANNELS) return -2;

        // 初始化MDCT
        frame_size_ = AAC_FRAME_SIZE;
        mdct_buffer_.resize(frame_size_ * 2, 0);

        // 初始化心理声学模型
        initPsychoacousticModel();

        // 初始化量化表
        initQuantTables();

        initialized_ = true;
        total_bytes_ = 0;
        total_frames_ = 0;

        return 0;
    }

    int encode(const int16_t* pcm_data, int pcm_size,
              std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !pcm_data) return -1;

        out_data.clear();

        // 处理每一帧
        int samples_per_channel = frame_size_;
        int total_samples = pcm_size / params_.channels;

        for (int offset = 0; offset < total_samples; offset += samples_per_channel) {
            // 提取一帧数据
            std::vector<float> frame(samples_per_channel * params_.channels);
            for (int i = 0; i < samples_per_channel && (offset + i) < total_samples; i++) {
                for (int ch = 0; ch < params_.channels; ch++) {
                    int idx = (offset + i) * params_.channels + ch;
                    if (idx < pcm_size) {
                        frame[i * params_.channels + ch] = pcm_data[idx] / 32768.0f;
                    }
                }
            }

            // 编码一帧
            std::vector<uint8_t> frame_data;
            encodeFrame(frame.data(), samples_per_channel, frame_data);

            // 添加ADTS头
            if (params_.format == AACOutputFormat::ADTS) {
                writeADTSHeader(frame_data.size(), out_data);
            }

            out_data.insert(out_data.end(), frame_data.begin(), frame_data.end());
        }

        total_bytes_ += out_data.size();
        total_frames_++;

        return 0;
    }

    int encodeFloat(const float* float_data, int samples,
                   std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !float_data) return -1;

        out_data.clear();

        int samples_per_channel = frame_size_;
        int total_samples = samples / params_.channels;

        for (int offset = 0; offset < total_samples; offset += samples_per_channel) {
            std::vector<uint8_t> frame_data;
            encodeFrame(float_data + offset * params_.channels,
                       samples_per_channel, frame_data);

            if (params_.format == AACOutputFormat::ADTS) {
                writeADTSHeader(frame_data.size(), out_data);
            }

            out_data.insert(out_data.end(), frame_data.begin(), frame_data.end());
        }

        total_bytes_ += out_data.size();
        total_frames_++;

        return 0;
    }

    int flush(std::vector<uint8_t>& out_data) override {
        out_data.clear();
        return 0;
    }

    AACEncodeStats getStats() const override {
        AACEncodeStats stats;
        stats.total_bytes = total_bytes_;
        stats.total_frames = total_frames_;
        if (total_frames_ > 0) {
            stats.avg_bitrate = static_cast<double>(total_bytes_ * 8) / total_frames_;
        }
        return stats;
    }

    void close() override {
        initialized_ = false;
        mdct_buffer_.clear();
    }

private:
    void initPsychoacousticModel() {
        // 初始化心理声学模型参数
        // 计算绝对听阈
        absolute_threshold_.resize(frame_size_ / 2);
        for (int i = 0; i < frame_size_ / 2; i++) {
            double freq = static_cast<double>(i) * params_.sample_rate / frame_size_;
            // 简化的绝对听阈曲线
            absolute_threshold_[i] = 3.64 * std::pow(freq / 1000.0, -0.8)
                                   - 6.5 * std::exp(-0.6 * std::pow(freq / 1000.0 - 3.3, 2))
                                   + 1e-3 * std::pow(freq / 1000.0, 4);
        }
    }

    void initQuantTables() {
        // 初始化量化表
        quant_table_.resize(256);
        for (int i = 0; i < 256; i++) {
            quant_table_[i] = std::pow(2.0, (i - 100) / 4.0);
        }
    }

    void encodeFrame(const float* input, int samples, std::vector<uint8_t>& output) {
        // 1. MDCT变换
        std::vector<float> spectrum(samples);
        mdctTransform(input, spectrum.data(), samples);

        // 2. 心理声学模型
        std::vector<float> threshold(samples / 2);
        calcMaskingThreshold(spectrum.data(), threshold.data(), samples / 2);

        // 3. 量化
        std::vector<int16_t> quant(samples / 2);
        quantize(spectrum.data(), threshold.data(), quant.data(), samples / 2);

        // 4. 熵编码
        entropyEncode(quant.data(), samples / 2, output);
    }

    void mdctTransform(const float* input, float* output, int n) {
        // 简化的MDCT实现
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
            // 简化：使用绝对听阈
            threshold[i] = absolute_threshold_[i];
        }
    }

    void quantize(const float* spectrum, const float* threshold,
                 int16_t* output, int n) {
        for (int i = 0; i < n; i++) {
            // 根据阈值进行量化
            float step = threshold[i] > 0 ? threshold[i] : 1.0f;
            output[i] = static_cast<int16_t>(std::round(spectrum[i] / step));
        }
    }

    void entropyEncode(const int16_t* quant, int n, std::vector<uint8_t>& output) {
        // 简化的Huffman编码
        for (int i = 0; i < n; i++) {
            int16_t val = quant[i];
            // 写入符号
            output.push_back(static_cast<uint8_t>((val >> 8) & 0xFF));
            output.push_back(static_cast<uint8_t>(val & 0xFF));
        }
    }

    void writeADTSHeader(int frame_size, std::vector<uint8_t>& output) {
        int adts_size = 7 + frame_size;

        // ADTS头
        output.push_back(0xFF);  // syncword high
        output.push_back(0xF1);  // syncword low, MPEG-4, Layer 0, no CRC

        // profile (2 bits) | sampling_frequency_index (4 bits) | private_bit (1 bit) | channel_configuration (1 bit)
        int sampling_freq_index = getSampleRateIndex(params_.sample_rate);
        uint8_t byte = ((params_.profile & 0x03) << 6) |
                       ((sampling_freq_index & 0x0F) << 2) |
                       (0 << 1) | ((params_.channels >> 2) & 0x01);
        output.push_back(byte);

        // channel_configuration (2 bits) | original_copy (1 bit) | home (1 bit) | copyright_id_bit (1 bit) | copyright_id_start (1 bit) | frame_length (2 bits)
        byte = ((params_.channels & 0x03) << 6) |
               (0 << 5) | (0 << 4) | (0 << 3) | (0 << 2) |
               ((adts_size >> 11) & 0x03);
        output.push_back(byte);

        // frame_length (8 bits)
        output.push_back(static_cast<uint8_t>((adts_size >> 3) & 0xFF));

        // frame_length (3 bits) | buffer_fullness (5 bits)
        byte = ((adts_size & 0x07) << 5) | (0x1F & 0x1F);
        output.push_back(byte);

        // buffer_fullness (6 bits) | number_of_raw_data_blocks (2 bits)
        output.push_back(0xFC);
    }

    int getSampleRateIndex(int sample_rate) {
        static const int rates[] = {96000, 88200, 64000, 48000, 44100, 32000,
                                    24000, 22050, 16000, 12000, 11025, 8000, 7350};
        for (int i = 0; i < 13; i++) {
            if (rates[i] == sample_rate) return i;
        }
        return 4;  // 默认44100
    }

private:
    AACEncodeParams params_;
    bool initialized_ = false;
    int frame_size_ = 1024;
    std::vector<float> mdct_buffer_;
    std::vector<float> absolute_threshold_;
    std::vector<double> quant_table_;
    int64_t total_bytes_ = 0;
    int64_t total_frames_ = 0;
};

std::unique_ptr<IAACEncoder> createAACEncoder() {
    return std::make_unique<AACEncoderImpl>();
}

} // namespace av_codec
