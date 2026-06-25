/**
 * @file vp9_decoder.cpp
 * @brief VP9 解码器实现
 */

#include "video/vp9_codec.h"
#include <cstring>
#include <algorithm>
#include <cmath>

namespace av_codec {

class VP9DecoderImpl : public IVP9Decoder {
public:
    VP9DecoderImpl() = default;
    ~VP9DecoderImpl() override { close(); }

    int init(const VP9DecodeParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int decode(const uint8_t* data, int size, std::vector<uint8_t>& out_yuv) override {
        if (!initialized_ || !data || size <= 0) return -1;
        out_yuv.clear();

        int pos = 0;
        // 查找起始码
        if (pos + 3 <= size && data[pos] == 0x00 && data[pos + 1] == 0x00 && data[pos + 2] == 0x01) {
            pos += 3;
        }

        // 解析帧头
        if (pos >= size) return -1;
        uint8_t header = data[pos++];
        VP9FrameType type = static_cast<VP9FrameType>((header >> 4) & 0x01);

        // 读取宽高
        if (pos + 4 > size) return -1;
        int width = data[pos] | (data[pos + 1] << 8);
        int height = data[pos + 2] | (data[pos + 3] << 8);
        pos += 4;

        if (width <= 0 || height <= 0) return -1;

        int frame_size = width * height * 3 / 2;
        recon_frame_.resize(frame_size, 0);

        // 解码块
        int sb_width = (width + 63) / 64;
        int sb_height = (height + 63) / 64;

        for (int sb_y = 0; sb_y < sb_height; sb_y++) {
            for (int sb_x = 0; sb_x < sb_width; sb_x++) {
                pos += decodeSuperBlock(data + pos, size - pos,
                                       sb_x * 64, sb_y * 64, 64, type, width);
            }
        }

        // 更新参考帧
        updateRefFrames();

        out_yuv = recon_frame_;
        frame_count_++;
        return 0;
    }

    int flush(std::vector<uint8_t>& out_yuv) override {
        out_yuv = recon_frame_;
        return 0;
    }

    void close() override {
        initialized_ = false;
        ref_frames_.clear();
        recon_frame_.clear();
    }

private:
    int decodeSuperBlock(const uint8_t* data, int size, int x, int y,
                        int sb_size, VP9FrameType type, int width) {
        return decodeBlock(data, size, x, y, sb_size, type, width);
    }

    int decodeBlock(const uint8_t* data, int size, int x, int y,
                   int block_size, VP9FrameType type, int width) {
        int pos = 0;
        if (pos >= size) return 0;

        if (block_size <= 4) {
            if (type == VP9FrameType::KEY_FRAME) {
                return decodeIntraBlock(data, size, x, y, block_size, width);
            } else {
                return decodeInterBlock(data, size, x, y, block_size, width);
            }
        }

        bool split = data[pos++] & 0x01;
        if (split) {
            int half = block_size / 2;
            pos += decodeBlock(data + pos, size - pos, x, y, half, type, width);
            pos += decodeBlock(data + pos, size - pos, x + half, y, half, type, width);
            pos += decodeBlock(data + pos, size - pos, x, y + half, half, type, width);
            pos += decodeBlock(data + pos, size - pos, x + half, y + half, half, type, width);
        } else {
            if (type == VP9FrameType::KEY_FRAME) {
                pos += decodeIntraBlock(data + pos, size - pos, x, y, block_size, width);
            } else {
                pos += decodeInterBlock(data + pos, size - pos, x, y, block_size, width);
            }
        }
        return pos;
    }

    int decodeIntraBlock(const uint8_t* data, int size, int x, int y,
                        int block_size, int width) {
        int pos = 0;
        if (pos >= size) return 0;

        int mode = data[pos++];
        for (int i = 0; i < block_size && pos < size; i++) {
            for (int j = 0; j < block_size && pos < size; j++) {
                int16_t residual = static_cast<int16_t>(data[pos++]);
                int val = 128 + residual;
                recon_frame_[(y + i) * width + (x + j)] = static_cast<uint8_t>(
                    std::clamp(val, 0, 255));
            }
        }
        return pos;
    }

    int decodeInterBlock(const uint8_t* data, int size, int x, int y,
                        int block_size, int width) {
        int pos = 0;
        if (pos + 2 > size) return 0;

        int16_t mv_x = static_cast<int16_t>(data[pos++]);
        int16_t mv_y = static_cast<int16_t>(data[pos++]);

        const uint8_t* ref = ref_frames_[0].data();
        int rx = x + mv_x;
        int ry = y + mv_y;

        for (int i = 0; i < block_size && pos < size; i++) {
            for (int j = 0; j < block_size && pos < size; j++) {
                int16_t residual = static_cast<int16_t>(data[pos++]);
                int val = ref[(ry + i) * width + (rx + j)] + residual;
                recon_frame_[(y + i) * width + (x + j)] = static_cast<uint8_t>(
                    std::clamp(val, 0, 255));
            }
        }
        return pos;
    }

    void updateRefFrames() {
        if (ref_frames_.size() < 3) {
            ref_frames_.push_back(recon_frame_);
        } else {
            ref_frames_[2] = ref_frames_[1];
            ref_frames_[1] = ref_frames_[0];
            ref_frames_[0] = recon_frame_;
        }
    }

private:
    VP9DecodeParams params_;
    bool initialized_ = false;
    int64_t frame_count_ = 0;
    std::vector<uint8_t> recon_frame_;
    std::vector<std::vector<uint8_t>> ref_frames_;
};

std::unique_ptr<IVP9Decoder> createVP9Decoder() {
    return std::make_unique<VP9DecoderImpl>();
}

} // namespace av_codec
