/**
 * @file vp9_encoder.cpp
 * @brief VP9 编码器实现
 *
 * VP9 特点：
 * - 超级块（SuperBlock）最大64x64
 * - 四叉树分割
 * - 10种帧内预测模式
 * - 3个参考帧（Last, Golden, AltRef）
 * - 自适应量化
 */

#include "video/vp9_codec.h"
#include <cstring>
#include <algorithm>
#include <cmath>
#include <chrono>

namespace av_codec {

class VP9EncoderImpl : public IVP9Encoder {
public:
    VP9EncoderImpl() = default;
    ~VP9EncoderImpl() override { close(); }

    int init(const VP9EncodeParams& params) override {
        params_ = params;
        if (params_.width <= 0 || params_.height <= 0) return -1;

        sb_width_ = (params_.width + 63) / 64;
        sb_height_ = (params_.height + 63) / 64;

        int frame_size = params_.width * params_.height * 3 / 2;
        for (int i = 0; i < 3; i++) {
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

        VP9FrameType frame_type = (frame_count_ % params_.key_frame_interval == 0)
                                  ? VP9FrameType::KEY_FRAME : VP9FrameType::INTER_FRAME;

        // 写入帧头
        writeFrameHeader(out_data, frame_type);

        // 编码超级块
        for (int sb_y = 0; sb_y < sb_height_; sb_y++) {
            for (int sb_x = 0; sb_x < sb_width_; sb_x++) {
                encodeSuperBlock(yuv_data, sb_x, sb_y, frame_type, out_data);
            }
        }

        // 更新参考帧
        updateRefFrames(yuv_data);
        frame_count_++;
        updateStats(out_data.size(), frame_type);
        return 0;
    }

    int flush(std::vector<uint8_t>& out_data) override {
        out_data.clear();
        return 0;
    }

    VP9EncodeStats getStats() const override { return stats_; }
    void close() override { initialized_ = false; ref_frames_.clear(); }

private:
    void writeFrameHeader(std::vector<uint8_t>& out, VP9FrameType type) {
        // VP9帧头
        out.push_back(0x00); out.push_back(0x00); out.push_back(0x01); // 起始码
        // frame_marker (2 bits)
        // profile_low_bit, profile_high_bit
        uint8_t header = (static_cast<uint8_t>(type) << 4) | (params_.profile & 0x03);
        out.push_back(header);
        // 简化的帧头数据
        out.push_back(static_cast<uint8_t>(params_.width & 0xFF));
        out.push_back(static_cast<uint8_t>((params_.width >> 8) & 0xFF));
        out.push_back(static_cast<uint8_t>(params_.height & 0xFF));
        out.push_back(static_cast<uint8_t>((params_.height >> 8) & 0xFF));
    }

    void encodeSuperBlock(const uint8_t* yuv_data, int sb_x, int sb_y,
                          VP9FrameType type, std::vector<uint8_t>& out) {
        int x = sb_x * 64;
        int y = sb_y * 64;
        encodeBlock(yuv_data, x, y, 64, type, out);
    }

    void encodeBlock(const uint8_t* yuv_data, int x, int y, int size,
                     VP9FrameType type, std::vector<uint8_t>& out) {
        if (size <= 4) {
            if (type == VP9FrameType::KEY_FRAME) {
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
            if (type == VP9FrameType::KEY_FRAME) {
                encodeIntraBlock(yuv_data, x, y, size, out);
            } else {
                encodeInterBlock(yuv_data, x, y, size, out);
            }
        }
    }

    bool shouldSplit(int x, int y, int size) {
        return size > 8;  // 简化判断
    }

    void encodeIntraBlock(const uint8_t* yuv_data, int x, int y, int size,
                          std::vector<uint8_t>& out) {
        int best_mode = 0;  // DC_PRED
        uint8_t pred[64 * 64];
        for (int i = 0; i < size * size; i++) pred[i] = 128;

        int width = params_.width;
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                int16_t residual = yuv_data[(y + i) * width + (x + j)] - pred[i * size + j];
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

    void motionEstimate(const uint8_t* yuv_data, int x, int y, int size,
                       int16_t& mv_x, int16_t& mv_y) {
        mv_x = 0; mv_y = 0;
        uint32_t best_sad = UINT32_MAX;
        int search_range = 16;
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

    void updateRefFrames(const uint8_t* yuv_data) {
        int frame_size = params_.width * params_.height * 3 / 2;
        ref_frames_[2] = ref_frames_[1];
        ref_frames_[1] = ref_frames_[0];
        std::memcpy(ref_frames_[0].data(), yuv_data, frame_size);
    }

    void updateStats(int64_t bytes, VP9FrameType type) {
        stats_.total_bits += bytes * 8;
        stats_.total_frames++;
        if (type == VP9FrameType::KEY_FRAME) stats_.key_frames++;
        else stats_.inter_frames++;

        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - start_time_).count();
        if (elapsed > 0) stats_.fps = static_cast<double>(stats_.total_frames) / elapsed;
    }

private:
    VP9EncodeParams params_;
    bool initialized_ = false;
    int sb_width_ = 0;
    int sb_height_ = 0;
    int64_t frame_count_ = 0;
    std::vector<std::vector<uint8_t>> ref_frames_;
    VP9EncodeStats stats_;
    std::chrono::steady_clock::time_point start_time_;
};

std::unique_ptr<IVP9Encoder> createVP9Encoder() {
    return std::make_unique<VP9EncoderImpl>();
}

} // namespace av_codec
