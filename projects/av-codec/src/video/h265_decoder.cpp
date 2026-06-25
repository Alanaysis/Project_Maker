/**
 * @file h265_decoder.cpp
 * @brief H.265/HEVC 解码器实现
 */

#include "video/h265_codec.h"
#include <cstring>
#include <algorithm>
#include <cmath>

namespace av_codec {

class H265DecoderImpl : public IH265Decoder {
public:
    H265DecoderImpl() = default;
    ~H265DecoderImpl() override { close(); }

    int init(const H265DecodeParams& params) override {
        params_ = params;
        initialized_ = true;
        return 0;
    }

    int decode(const uint8_t* data, int size, std::vector<uint8_t>& out_yuv) override {
        if (!initialized_ || !data || size <= 0) return -1;

        out_yuv.clear();

        // 解析NAL单元
        int pos = 0;
        while (pos < size) {
            // 查找起始码
            if (pos + 4 <= size &&
                data[pos] == 0x00 && data[pos + 1] == 0x00 &&
                data[pos + 2] == 0x00 && data[pos + 3] == 0x01) {
                pos += 4;
            } else if (pos + 3 <= size &&
                       data[pos] == 0x00 && data[pos + 1] == 0x00 &&
                       data[pos + 2] == 0x01) {
                pos += 3;
            } else {
                pos++;
                continue;
            }

            if (pos >= size) break;

            // 解析NAL头（H.265 NAL头是2字节）
            uint8_t nal_header = data[pos++];
            uint8_t nal_type = (nal_header >> 1) & 0x3F;

            switch (nal_type) {
                case 32:  // VPS
                    parseVPS(data + pos, size - pos);
                    break;
                case 33:  // SPS
                    parseSPS(data + pos, size - pos);
                    break;
                case 34:  // PPS
                    parsePPS(data + pos, size - pos);
                    break;
                case 20:  // IDR Slice
                case 1:   // Non-IDR Slice
                    decodeSlice(data + pos, size - pos, nal_type == 20);
                    break;
                default:
                    break;
            }

            // 查找下一个NAL
            while (pos < size) {
                if (pos + 3 <= size &&
                    data[pos] == 0x00 && data[pos + 1] == 0x00 &&
                    (data[pos + 2] == 0x01 || data[pos + 2] == 0x00)) break;
                pos++;
            }
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
    void parseVPS(const uint8_t* data, int size) {
        if (size < 2) return;
        vps_.id = data[0] & 0x0F;
    }

    void parseSPS(const uint8_t* data, int size) {
        if (size < 4) return;
        sps_.profile_idc = data[0];
        sps_.level_idc = data[1];
        // 简化解析
        sps_.width = 1920;
        sps_.height = 1080;

        int frame_size = sps_.width * sps_.height * 3 / 2;
        recon_frame_.resize(frame_size, 0);
        for (int i = 0; i < 16; i++) {
            ref_frames_.push_back(std::vector<uint8_t>(frame_size, 0));
        }
    }

    void parsePPS(const uint8_t* data, int size) {
        if (size < 2) return;
        pps_.id = data[0];
        pps_.sps_id = data[1];
    }

    void decodeSlice(const uint8_t* data, int size, bool is_idr) {
        if (sps_.width == 0 || sps_.height == 0) return;

        int ctu_size = 64;
        int ctu_width = (sps_.width + ctu_size - 1) / ctu_size;
        int ctu_height = (sps_.height + ctu_size - 1) / ctu_size;

        int pos = 0;
        for (int ctu_y = 0; ctu_y < ctu_height; ctu_y++) {
            for (int ctu_x = 0; ctu_x < ctu_width; ctu_x++) {
                if (pos >= size) break;
                pos += decodeCTU(data + pos, size - pos, ctu_x, ctu_y, is_idr);
            }
        }
    }

    int decodeCTU(const uint8_t* data, int size, int ctu_x, int ctu_y, bool is_idr) {
        return decodeCU(data, size, ctu_x * 64, ctu_y * 64, 64, is_idr);
    }

    int decodeCU(const uint8_t* data, int size, int x, int y, int cu_size, bool is_idr) {
        int pos = 0;
        if (pos >= size) return 0;

        if (cu_size <= 8) {
            // 叶子节点
            if (is_idr) {
                decodeIntraPU(data + pos, size - pos, x, y, cu_size);
            } else {
                decodeInterPU(data + pos, size - pos, x, y, cu_size);
            }
            return pos;
        }

        // 解码分割信息
        bool split = data[pos++] & 0x01;
        if (split) {
            int half = cu_size / 2;
            pos += decodeCU(data + pos, size - pos, x, y, half, is_idr);
            pos += decodeCU(data + pos, size - pos, x + half, y, half, is_idr);
            pos += decodeCU(data + pos, size - pos, x, y + half, half, is_idr);
            pos += decodeCU(data + pos, size - pos, x + half, y + half, half, is_idr);
        } else {
            if (is_idr) {
                decodeIntraPU(data + pos, size - pos, x, y, cu_size);
            } else {
                decodeInterPU(data + pos, size - pos, x, y, cu_size);
            }
        }

        return pos;
    }

    void decodeIntraPU(const uint8_t* data, int size, int x, int y, int pu_size) {
        int pos = 0;
        if (pos >= size) return;

        int mode = data[pos++];
        uint8_t pred[64 * 64];
        for (int i = 0; i < pu_size * pu_size; i++) pred[i] = 128;

        int width = sps_.width;
        for (int i = 0; i < pu_size && pos < size; i++) {
            for (int j = 0; j < pu_size && pos < size; j++) {
                int16_t residual = static_cast<int16_t>(data[pos++]);
                int val = pred[i * pu_size + j] + residual;
                recon_frame_[(y + i) * width + (x + j)] = static_cast<uint8_t>(
                    std::clamp(val, 0, 255));
            }
        }
    }

    void decodeInterPU(const uint8_t* data, int size, int x, int y, int pu_size) {
        int pos = 0;
        if (pos + 2 > size) return;

        int16_t mv_x = static_cast<int16_t>(data[pos++]);
        int16_t mv_y = static_cast<int16_t>(data[pos++]);

        const uint8_t* ref = ref_frames_[0].data();
        int width = sps_.width;
        int rx = x + mv_x;
        int ry = y + mv_y;

        for (int i = 0; i < pu_size && pos < size; i++) {
            for (int j = 0; j < pu_size && pos < size; j++) {
                int16_t residual = static_cast<int16_t>(data[pos++]);
                int val = ref[(ry + i) * width + (rx + j)] + residual;
                recon_frame_[(y + i) * width + (x + j)] = static_cast<uint8_t>(
                    std::clamp(val, 0, 255));
            }
        }
    }

private:
    H265DecodeParams params_;
    bool initialized_ = false;
    int64_t frame_count_ = 0;

    struct VPS { int id = 0; } vps_;
    struct SPS { int profile_idc = 0; int level_idc = 0; int width = 0; int height = 0; } sps_;
    struct PPS { int id = 0; int sps_id = 0; } pps_;

    std::vector<uint8_t> recon_frame_;
    std::vector<std::vector<uint8_t>> ref_frames_;
};

std::unique_ptr<IH265Decoder> createH265Decoder() {
    return std::make_unique<H265DecoderImpl>();
}

} // namespace av_codec
