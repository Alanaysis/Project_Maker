/**
 * @file av1_encoder.cpp
 * @brief AV1 编码器实现
 *
 * AV1 特点：
 * - 超级块最大128x128
 * - 56种帧内预测模式
 * - 7个参考帧
 * - CDEF（约束方向增强滤波器）
 * - 环路恢复滤波器
 * - 胶片颗粒合成
 */

#include "video/av1_codec.h"
#include <cstring>
#include <algorithm>
#include <cmath>
#include <chrono>

namespace av_codec {

class AV1EncoderImpl : public IAV1Encoder {
public:
    AV1EncoderImpl() = default;
    ~AV1EncoderImpl() override { close(); }

    int init(const AV1EncodeParams& params) override {
        params_ = params;
        if (params_.width <= 0 || params_.height <= 0) return -1;

        sb_width_ = (params_.width + 127) / 128;
        sb_height_ = (params_.height + 127) / 128;

        int frame_size = params_.width * params_.height * 3 / 2;
        for (int i = 0; i < 7; i++) {
            ref_frames_.push_back(std::vector<uint8_t>(frame_size, 0));
        }

        initialized_ = true;
        frame_count_ = 0;
        start_time_ = std::chrono::steady_clock::now();
        return 0;
    }

    int encode(const uint8_t* yuv_data, std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !yuv_data) return -1;
        out_data.clear();

        AV1FrameType frame_type = getFrameType(frame_count_);

        // 写入OBU（开放位流单元）
        writeOBUHeader(out_data, frame_type);

        // 写入序列头（仅关键帧）
        if (frame_type == AV1FrameType::KEY_FRAME) {
            writeSequenceHeader(out_data);
        }

        // 写入帧头
        writeFrameHeader(out_data, frame_type);

        // 编码超级块
        for (int sb_y = 0; sb_y < sb_height_; sb_y++) {
            for (int sb_x = 0; sb_x < sb_width_; sb_x++) {
                encodeSuperBlock(yuv_data, sb_x, sb_y, frame_type, out_data);
            }
        }

        // CDEF滤波
        if (params_.cdef) applyCDEF(out_data);

        // 恢复滤波
        if (params_.restoration) applyRestoration(out_data);

        updateRefFrames(yuv_data);
        frame_count_++;
        updateStats(out_data.size(), frame_type);
        return 0;
    }

    int flush(std::vector<uint8_t>& out_data) override {
        out_data.clear();
        return 0;
    }

    AV1EncodeStats getStats() const override { return stats_; }
    void close() override { initialized_ = false; ref_frames_.clear(); }

private:
    AV1FrameType getFrameType(int64_t frame_num) const {
        if (frame_num % params_.key_frame_interval == 0) return AV1FrameType::KEY_FRAME;
        return AV1FrameType::INTER_FRAME;
    }

    void writeOBUHeader(std::vector<uint8_t>& out, AV1FrameType type) {
        // OBU header: obu_type(4) | obu_extension_flag(1) | reserved(3)
        uint8_t obu_type = (type == AV1FrameType::KEY_FRAME) ? 1 : 6;  // FRAME vs FRAME_HEADER
        out.push_back((obu_type << 4) | 0x00);
    }

    void writeSequenceHeader(std::vector<uint8_t>& out) {
        // seq_profile (3 bits)
        out.push_back(static_cast<uint8_t>(params_.profile & 0x07));
        // still_picture (1 bit) | reduced_still_picture_header (1 bit)
        out.push_back(0x00);
        // max frame width/height
        out.push_back(static_cast<uint8_t>((params_.width - 1) & 0xFF));
        out.push_back(static_cast<uint8_t>(((params_.width - 1) >> 8) & 0xFF));
        out.push_back(static_cast<uint8_t>((params_.height - 1) & 0xFF));
        out.push_back(static_cast<uint8_t>(((params_.height - 1) >> 8) & 0xFF));
    }

    void writeFrameHeader(std::vector<uint8_t>& out, AV1FrameType type) {
        // frame_type (2 bits)
        out.push_back(static_cast<uint8_t>(type) & 0x03);
    }

    void encodeSuperBlock(const uint8_t* yuv_data, int sb_x, int sb_y,
                          AV1FrameType type, std::vector<uint8_t>& out) {
        int x = sb_x * 128;
        int y = sb_y * 128;
        encodeBlock(yuv_data, x, y, 128, type, out);
    }

    void encodeBlock(const uint8_t* yuv_data, int x, int y, int size,
                     AV1FrameType type, std::vector<uint8_t>& out) {
        if (size <= 4) {
            if (type == AV1FrameType::KEY_FRAME || type == AV1FrameType::INTRA_ONLY_FRAME) {
                encodeIntraBlock(yuv_data, x, y, size, out);
            } else {
                encodeInterBlock(yuv_data, x, y, size, out);
            }
            return;
        }

        bool split = shouldSplit(x, y, size);
        if (split) {
            int half = size / 2;
            encodeBlock(yuv_data, x, y, half, type, out);
            encodeBlock(yuv_data, x + half, y, half, type, out);
            encodeBlock(yuv_data, x, y + half, half, type, out);
            encodeBlock(yuv_data, x + half, y + half, half, type, out);
        } else {
            if (type == AV1FrameType::KEY_FRAME || type == AV1FrameType::INTRA_ONLY_FRAME) {
                encodeIntraBlock(yuv_data, x, y, size, out);
            } else {
                encodeInterBlock(yuv_data, x, y, size, out);
            }
        }
    }

    bool shouldSplit(int x, int y, int size) {
        return size > 16;
    }

    void encodeIntraBlock(const uint8_t* yuv_data, int x, int y, int size,
                          std::vector<uint8_t>& out) {
        // AV1支持56种帧内预测模式
        int best_mode = selectBestIntraMode(yuv_data, x, y, size);
        out.push_back(static_cast<uint8_t>(best_mode));

        int width = params_.width;
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                int16_t residual = yuv_data[(y + i) * width + (x + j)] - 128;
                out.push_back(static_cast<uint8_t>(residual & 0xFF));
            }
        }
    }

    void encodeInterBlock(const uint8_t* yuv_data, int x, int y, int size,
                          std::vector<uint8_t>& out) {
        int16_t mv_x = 0, mv_y = 0;
        motionEstimate(yuv_data, x, y, size, mv_x, mv_y);

        out.push_back(static_cast<uint8_t>(mv_x & 0xFF));
        out.push_back(static_cast<uint8_t>(mv_y & 0xFF));

        const uint8_t* ref = ref_frames_[0].data();
        int width = params_.width;
        int rx = x + mv_x;
        int ry = y + mv_y;

        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                int16_t residual = yuv_data[(y + i) * width + (x + j)]
                                 - ref[(ry + i) * width + (rx + j)];
                out.push_back(static_cast<uint8_t>(residual & 0xFF));
            }
        }
    }

    int selectBestIntraMode(const uint8_t* yuv_data, int x, int y, int size) {
        return 0;  // DC_PRED
    }

    void motionEstimate(const uint8_t* yuv_data, int x, int y, int size,
                       int16_t& mv_x, int16_t& mv_y) {
        mv_x = 0; mv_y = 0;
        uint32_t best_sad = UINT32_MAX;
        int search_range = 32;
        int width = params_.width;
        const uint8_t* ref = ref_frames_[0].data();
        const uint8_t* cur = yuv_data + y * width + x;

        for (int dy = -search_range; dy <= search_range; dy++) {
            for (int dx = -search_range; dx <= search_range; dx++) {
                int rx = x + dx, ry = y + dy;
                if (rx < 0 || ry < 0 || rx + size > width || ry + size > params_.height) continue;

                uint32_t sad = 0;
                for (int i = 0; i < size; i++) {
                    for (int j = 0; j < size; j++) {
                        sad += std::abs(cur[i * width + j] - ref[(ry + i) * width + (rx + j)]);
                    }
                }
                if (sad < best_sad) { best_sad = sad; mv_x = dx; mv_y = dy; }
            }
        }
    }

    void applyCDEF(std::vector<uint8_t>& out) {
        // CDEF滤波器实现
    }

    void applyRestoration(std::vector<uint8_t>& out) {
        // 恢复滤波器实现
    }

    void updateRefFrames(const uint8_t* yuv_data) {
        int frame_size = params_.width * params_.height * 3 / 2;
        for (int i = ref_frames_.size() - 1; i > 0; i--) {
            ref_frames_[i] = ref_frames_[i - 1];
        }
        std::memcpy(ref_frames_[0].data(), yuv_data, frame_size);
    }

    void updateStats(int64_t bytes, AV1FrameType type) {
        stats_.total_bits += bytes * 8;
        stats_.total_frames++;
        if (type == AV1FrameType::KEY_FRAME) stats_.key_frames++;
        else if (type == AV1FrameType::INTRA_ONLY_FRAME) stats_.intra_only_frames++;
        else stats_.inter_frames++;

        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - start_time_).count();
        if (elapsed > 0) stats_.fps = static_cast<double>(stats_.total_frames) / elapsed;
    }

private:
    AV1EncodeParams params_;
    bool initialized_ = false;
    int sb_width_ = 0;
    int sb_height_ = 0;
    int64_t frame_count_ = 0;
    std::vector<std::vector<uint8_t>> ref_frames_;
    AV1EncodeStats stats_;
    std::chrono::steady_clock::time_point start_time_;
};

std::unique_ptr<IAV1Encoder> createAV1Encoder() {
    return std::make_unique<AV1EncoderImpl>();
}

} // namespace av_codec
