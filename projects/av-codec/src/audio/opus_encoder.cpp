/**
 * @file opus_encoder.cpp
 * @brief Opus 编码器实现
 *
 * Opus 特点：
 * - 混合编码器（SILK + CELT）
 * - 低延迟
 * - 动态比特率
 * - 支持语音和音乐
 */

#include "audio/opus_codec.h"
#include <cstring>
#include <cmath>
#include <algorithm>

namespace av_codec {

class OpusEncoderImpl : public IOpusEncoder {
public:
    OpusEncoderImpl() = default;
    ~OpusEncoderImpl() override { close(); }

    int init(const OpusEncodeParams& params) override {
        params_ = params;

        if (params_.sample_rate <= 0 || params_.channels <= 0) return -1;
        if (params_.channels > OPUS_MAX_CHANNELS) return -2;

        initialized_ = true;
        total_bytes_ = 0;
        total_frames_ = 0;

        return 0;
    }

    int encode(const int16_t* pcm_data, int frame_size,
              std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !pcm_data) return -1;

        out_data.clear();

        // 确定编码模式
        if (params_.application == OpusApplication::VOIP) {
            // SILK模式（语音）
            encodeSILK(pcm_data, frame_size, out_data);
        } else if (params_.application == OpusApplication::RESTRICTED_LOWDELAY) {
            // CELT模式（音乐/低延迟）
            encodeCELT(pcm_data, frame_size, out_data);
        } else {
            // 混合模式
            encodeHybrid(pcm_data, frame_size, out_data);
        }

        total_bytes_ += out_data.size();
        total_frames_++;

        return 0;
    }

    int encodeFloat(const float* float_data, int frame_size,
                   std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !float_data) return -1;

        // 转换为int16
        std::vector<int16_t> pcm(frame_size * params_.channels);
        for (int i = 0; i < frame_size * params_.channels; i++) {
            pcm[i] = static_cast<int16_t>(
                std::clamp(float_data[i] * 32768.0f, -32768.0f, 32767.0f));
        }

        return encode(pcm.data(), frame_size, out_data);
    }

    OpusEncodeStats getStats() const override {
        OpusEncodeStats stats;
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
    void encodeSILK(const int16_t* pcm, int frame_size, std::vector<uint8_t>& output) {
        // SILK编码（线性预测编码）
        // 1. 预处理
        std::vector<float> signal(frame_size * params_.channels);
        for (int i = 0; i < frame_size * params_.channels; i++) {
            signal[i] = pcm[i] / 32768.0f;
        }

        // 2. LPC分析
        std::vector<float> lpc(10);
        lpcAnalysis(signal.data(), frame_size, lpc.data(), 10);

        // 3. 残差编码
        std::vector<float> residual(frame_size);
        for (int i = 0; i < frame_size; i++) {
            float pred = 0;
            for (int j = 0; j < 10 && i - j - 1 >= 0; j++) {
                pred += lpc[j] * signal[i - j - 1];
            }
            residual[i] = signal[i] - pred;
        }

        // 4. 量化残差
        for (int i = 0; i < frame_size; i++) {
            int16_t quant = static_cast<int16_t>(residual[i] * 128);
            output.push_back(static_cast<uint8_t>((quant >> 8) & 0xFF));
            output.push_back(static_cast<uint8_t>(quant & 0xFF));
        }
    }

    void encodeCELT(const int16_t* pcm, int frame_size, std::vector<uint8_t>& output) {
        // CELT编码（MDCT）
        // 1. MDCT变换
        std::vector<float> spectrum(frame_size);
        for (int k = 0; k < frame_size; k++) {
            float sum = 0.0f;
            for (int i = 0; i < frame_size * 2; i++) {
                sum += pcm[i] * std::cos(M_PI / frame_size * (i + 0.5 + frame_size / 2) * (k + 0.5));
            }
            spectrum[k] = sum;
        }

        // 2. 量化
        for (int i = 0; i < frame_size; i++) {
            int16_t quant = static_cast<int16_t>(spectrum[i] / 256);
            output.push_back(static_cast<uint8_t>((quant >> 8) & 0xFF));
            output.push_back(static_cast<uint8_t>(quant & 0xFF));
        }
    }

    void encodeHybrid(const int16_t* pcm, int frame_size, std::vector<uint8_t>& output) {
        // 混合编码：低频用SILK，高频用CELT
        int silk_size = frame_size / 2;
        int celt_size = frame_size - silk_size;

        encodeSILK(pcm, silk_size, output);
        encodeCELT(pcm + silk_size * params_.channels, celt_size, output);
    }

    void lpcAnalysis(const float* signal, int samples, float* lpc, int order) {
        // 简化的LPC分析（自相关法）
        std::vector<float> autocorr(order + 1, 0);
        for (int i = 0; i <= order; i++) {
            for (int j = 0; j < samples - i; j++) {
                autocorr[i] += signal[j] * signal[j + i];
            }
        }

        // Levinson-Durbin算法
        std::vector<float> a(order + 1), a_prev(order + 1);
        float error = autocorr[0];

        for (int i = 1; i <= order; i++) {
            float lambda = 0;
            for (int j = 1; j < i; j++) {
                lambda += a_prev[j] * autocorr[i - j];
            }
            lambda = (autocorr[i] - lambda) / error;

            a[i] = lambda;
            for (int j = 1; j < i; j++) {
                a[j] = a_prev[j] - lambda * a_prev[i - j];
            }

            error *= (1 - lambda * lambda);
            a_prev = a;
        }

        for (int i = 0; i < order; i++) {
            lpc[i] = a[i + 1];
        }
    }

private:
    OpusEncodeParams params_;
    bool initialized_ = false;
    int64_t total_bytes_ = 0;
    int64_t total_frames_ = 0;
};

std::unique_ptr<IOpusEncoder> createOpusEncoder() {
    return std::make_unique<OpusEncoderImpl>();
}

} // namespace av_codec
