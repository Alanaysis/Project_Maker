/**
 * @file av1_decoder.cpp
 * @brief AV1 解码器实现
 */

#include "video/av1_codec.h"
#include <cstring>
#include <algorithm>
#include <cmath>

namespace av_codec {

class AV1DecoderImpl : public IAV1Decoder {
public:
    AV1DecoderImpl() = default;
    ~AV1DecoderImpl() override { close(); }

    int init(const AV1DecodeParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int decode(const uint8_t* data, int size, std::vector<uint8_t>& out_yuv) override {
        if (!initialized_ || !data || size <= 0) return -1;
        out_yuv.clear();

        int pos = 0;
        while (pos < size) {
            // 解析OBU头
            if (pos >= size) break;
            uint8_t obu_header = data[pos++];
            uint8_t obu_type = (obu_header >> 4) & 0x0F;

            // 读取OBU大小（LEB128编码）
            int obu_size = 0;
            int shift = 0;
            while (pos < size) {
                uint8_t byte = data[pos++];
                obu_size |= (byte & 0x7F) << shift;
                shift += 7;
                if (!(byte & 0x80)) break;
            }

            // 处理OBU
            switch (obu_type) {
                case 1:  // OBU_SEQUENCE_HEADER
                    parseSequenceHeader(data + pos, obu_size);
                    break;
                case 6:  // OBU_FRAME
                case 7:  // OBU_FRAME_HEADER
                    parseFrameHeader(data + pos, obu_size);
                    break;
                case 8:  // OBU_TILE_GROUP
                    decodeTileGroup(data + pos, obu_size);
                    break;
                default:
                    break;
            }

            pos += obu_size;
        }

        if (!recon_frame_.empty()) out_yuv = recon_frame_;
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
    void parseSequenceHeader(const uint8_t* data, int size) {
        if (size < 6) return;
        int profile = data[0] & 0x07;
        int width = (data[2] | (data[3] << 8)) + 1;
        int height = (data[4] | (data[5] << 8)) + 1;

        if (width > 0 && height > 0) {
            width_ = width;
            height_ = height;
            int frame_size = width * height * 3 / 2;
            recon_frame_.resize(frame_size, 0);
            for (int i = 0; i < 7; i++) {
                ref_frames_.push_back(std::vector<uint8_t>(frame_size, 0));
            }
        }
    }

    void parseFrameHeader(const uint8_t* data, int size) {
        if (size < 1) return;
        frame_type_ = static_cast<AV1FrameType>(data[0] & 0x03);
    }

    void decodeTileGroup(const uint8_t* data, int size) {
        if (width_ == 0 || height_ == 0) return;

        int sb_width = (width_ + 127) / 128;
        int sb_height = (height_ + 127) / 128;

        int pos = 0;
        for (int sb_y = 0; sb_y < sb_height; sb_y++) {
            for (int sb_x = 0; sb_x < sb_width; sb_x++) {
                pos += decodeSuperBlock(data + pos, size - pos, sb_x * 128, sb_y * 128, 128);
            }
        }

        updateRefFrames();
    }

    int decodeSuperBlock(const uint8_t* data, int size, int x, int y, int sb_size) {
        return decodeBlock(data, size, x, y, sb_size);
    }

    int decodeBlock(const uint8_t* data, int size, int x, int y, int block_size) {
        int pos = 0;
        if (pos >= size) return 0;

        if (block_size <= 4) {
            return decodeLeafBlock(data, size, x, y, block_size);
        }

        bool split = data[pos++] & 0x01;
        if (split) {
            int half = block_size / 2;
            pos += decodeBlock(data + pos, size - pos, x, y, half);
            pos += decodeBlock(data + pos, size - pos, x + half, y, half);
            pos += decodeBlock(data + pos, size - pos, x, y + half, half);
            pos += decodeBlock(data + pos, size - pos, x + half, y + half, half);
        } else {
            pos += decodeLeafBlock(data + pos, size - pos, x, y, block_size);
        }
        return pos;
    }

    int decodeLeafBlock(const uint8_t* data, int size, int x, int y, int block_size) {
        int pos = 0;
        if (pos >= size) return 0;

        int mode = data[pos++];

        const uint8_t* ref = ref_frames_[0].data();
        for (int i = 0; i < block_size && pos < size; i++) {
            for (int j = 0; j < block_size && pos < size; j++) {
                int16_t residual = static_cast<int16_t>(data[pos++]);
                int val;
                if (frame_type_ == AV1FrameType::KEY_FRAME || frame_type_ == AV1FrameType::INTRA_ONLY_FRAME) {
                    val = 128 + residual;
                } else {
                    int rx = x + j, ry = y + i;
                    if (rx >= 0 && ry >= 0 && rx < width_ && ry < height_) {
                        val = ref[ry * width_ + rx] + residual;
                    } else {
                        val = 128 + residual;
                    }
                }
                recon_frame_[y * width_ + x + i * width_ + j] = static_cast<uint8_t>(
                    std::clamp(val, 0, 255));
            }
        }
        return pos;
    }

    void updateRefFrames() {
        for (int i = ref_frames_.size() - 1; i > 0; i--) {
            ref_frames_[i] = ref_frames_[i - 1];
        }
        ref_frames_[0] = recon_frame_;
    }

private:
    AV1DecodeParams params_;
    bool initialized_ = false;
    int64_t frame_count_ = 0;
    int width_ = 0;
    int height_ = 0;
    AV1FrameType frame_type_ = AV1FrameType::KEY_FRAME;
    std::vector<uint8_t> recon_frame_;
    std::vector<std::vector<uint8_t>> ref_frames_;
};

std::unique_ptr<IAV1Decoder> createAV1Decoder() {
    return std::make_unique<AV1DecoderImpl>();
}

} // namespace av_codec
