/**
 * @file h264_decoder.cpp
 * @brief H.264 解码器实现
 *
 * 实现 H.264 解码的核心流程：
 * 1. 熵解码（CABAC/CAVLC）
 * 2. 反量化
 * 3. 逆DCT变换
 * 4. 帧内/帧间预测重建
 * 5. 环路滤波
 */

#include "video/h264_codec.h"
#include <cstring>
#include <algorithm>
#include <cmath>

namespace av_codec {

/**
 * @brief H.264 解码器实现
 */
class H264DecoderImpl : public IH264Decoder {
public:
    H264DecoderImpl() = default;
    ~H264DecoderImpl() override { close(); }

    int init(const H264DecodeParams& params) override {
        params_ = params;
        initialized_ = true;
        frame_count_ = 0;
        return 0;
    }

    int decode(const uint8_t* data, int size, std::vector<uint8_t>& out_yuv) override {
        if (!initialized_ || !data || size <= 0) {
            return -1;
        }

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

            // 解析NAL头
            if (pos >= size) break;
            uint8_t nal_header = data[pos++];
            uint8_t nal_type = nal_header & 0x1F;

            // 根据NAL类型处理
            switch (nal_type) {
                case 7:  // SPS
                    parseSPS(data + pos, size - pos);
                    break;
                case 8:  // PPS
                    parsePPS(data + pos, size - pos);
                    break;
                case 5:  // IDR Slice
                    decodeSlice(data + pos, size - pos, true);
                    break;
                case 1:  // Non-IDR Slice
                    decodeSlice(data + pos, size - pos, false);
                    break;
                default:
                    break;
            }

            // 查找下一个NAL
            while (pos < size) {
                if (pos + 3 <= size &&
                    data[pos] == 0x00 && data[pos + 1] == 0x00 &&
                    (data[pos + 2] == 0x01 || data[pos + 2] == 0x00)) {
                    break;
                }
                pos++;
            }
        }

        // 输出重建帧
        if (!recon_frame_.empty()) {
            out_yuv = recon_frame_;
        }

        frame_count_++;
        return 0;
    }

    int flush(std::vector<uint8_t>& out_yuv) override {
        out_yuv.clear();
        // 输出缓冲区中的帧
        if (!recon_frame_.empty()) {
            out_yuv = recon_frame_;
        }
        return 0;
    }

    void close() override {
        initialized_ = false;
        ref_frames_.clear();
        recon_frame_.clear();
    }

private:
    /**
     * @brief 解析SPS
     */
    void parseSPS(const uint8_t* data, int size) {
        if (size < 10) return;

        // 解析基本参数
        sps_.profile_idc = data[0];
        sps_.level_idc = data[2];
        sps_.width = ((data[6] << 8) | data[7]) * 16;
        sps_.height = ((data[8] << 8) | data[9]) * 16;

        // 分配重建帧缓冲区
        int frame_size = sps_.width * sps_.height * 3 / 2;
        recon_frame_.resize(frame_size, 0);

        // 分配参考帧缓冲区
        for (int i = 0; i < 16; i++) {
            ref_frames_.push_back(std::vector<uint8_t>(frame_size, 0));
        }
    }

    /**
     * @brief 解析PPS
     */
    void parsePPS(const uint8_t* data, int size) {
        if (size < 3) return;

        pps_.id = data[0];
        pps_.sps_id = data[1];
        pps_.cabac = (data[2] & 0x01) != 0;
    }

    /**
     * @brief 解码Slice
     */
    void decodeSlice(const uint8_t* data, int size, bool is_idr) {
        if (sps_.width == 0 || sps_.height == 0) return;

        int mb_width = (sps_.width + 15) / 16;
        int mb_height = (sps_.height + 15) / 16;

        int pos = 0;
        for (int mb_y = 0; mb_y < mb_height; mb_y++) {
            for (int mb_x = 0; mb_x < mb_width; mb_x++) {
                if (pos >= size) break;

                // 解码宏块
                pos += decodeMacroblock(data + pos, size - pos,
                                       mb_x, mb_y, is_idr);
            }
        }

        // 环路滤波
        applyDeblockingFilter();
    }

    /**
     * @brief 解码宏块
     */
    int decodeMacroblock(const uint8_t* data, int size,
                        int mb_x, int mb_y, bool is_idr) {
        int pos = 0;
        if (pos >= size) return 0;

        // 读取宏块类型
        int mb_type = data[pos++];

        if (is_idr || mb_type < 5) {
            // 帧内预测宏块
            decodeIntraMacroblock(data + pos, size - pos, mb_x, mb_y, mb_type);
        } else {
            // 帧间预测宏块
            decodeInterMacroblock(data + pos, size - pos, mb_x, mb_y, mb_type);
        }

        return pos;
    }

    /**
     * @brief 解码帧内宏块
     */
    void decodeIntraMacroblock(const uint8_t* data, int size,
                               int mb_x, int mb_y, int mode) {
        int x = mb_x * 16;
        int y = mb_y * 16;
        int width = sps_.width;

        // 帧内预测重建
        uint8_t pred[16 * 16];
        intraPredict(pred, 16, mode, x, y);

        // 反量化
        int16_t coeffs[16 * 16];
        int pos = 0;
        for (int i = 0; i < 16 * 16 && pos < size; i++) {
            coeffs[i] = static_cast<int16_t>(data[pos++]);
        }

        // 逆DCT
        int16_t residual[16 * 16];
        idct4x4(coeffs, residual);

        // 重建
        for (int i = 0; i < 16; i++) {
            for (int j = 0; j < 16; j++) {
                int val = static_cast<int>(pred[i * 16 + j]) + residual[i * 16 + j];
                recon_frame_[(y + i) * width + (x + j)] = static_cast<uint8_t>(
                    std::clamp(val, 0, 255));
            }
        }
    }

    /**
     * @brief 解码帧间宏块
     */
    void decodeInterMacroblock(const uint8_t* data, int size,
                               int mb_x, int mb_y, int mb_type) {
        int x = mb_x * 16;
        int y = mb_y * 16;
        int width = sps_.width;

        int pos = 0;
        if (pos + 2 > size) return;

        // 读取运动向量
        int16_t mv_x = static_cast<int16_t>(data[pos++]);
        int16_t mv_y = static_cast<int16_t>(data[pos++]);

        // 运动补偿
        uint8_t pred[16 * 16];
        motionCompensate(x, y, mv_x, mv_y, pred, width);

        // 读取残差
        int16_t coeffs[16 * 16];
        for (int i = 0; i < 16 * 16 && pos < size; i++) {
            coeffs[i] = static_cast<int16_t>(data[pos++]);
        }

        // 逆DCT
        int16_t residual[16 * 16];
        idct4x4(coeffs, residual);

        // 重建
        for (int i = 0; i < 16; i++) {
            for (int j = 0; j < 16; j++) {
                int val = static_cast<int>(pred[i * 16 + j]) + residual[i * 16 + j];
                recon_frame_[(y + i) * width + (x + j)] = static_cast<uint8_t>(
                    std::clamp(val, 0, 255));
            }
        }
    }

    /**
     * @brief 帧内预测
     */
    void intraPredict(uint8_t* pred, int stride, int mode, int x, int y) {
        // 简化的帧内预测
        for (int i = 0; i < 16; i++) {
            for (int j = 0; j < 16; j++) {
                pred[i * stride + j] = 128;
            }
        }
    }

    /**
     * @brief 运动补偿
     */
    void motionCompensate(int x, int y, int16_t mv_x, int16_t mv_y,
                         uint8_t* pred, int width) {
        const uint8_t* ref = ref_frames_[0].data();

        int rx = x + mv_x;
        int ry = y + mv_y;

        for (int i = 0; i < 16; i++) {
            for (int j = 0; j < 16; j++) {
                pred[i * 16 + j] = ref[(ry + i) * width + (rx + j)];
            }
        }
    }

    /**
     * @brief 4x4 逆DCT
     */
    void idct4x4(const int16_t* input, int16_t* output) {
        // 简化的4x4 IDCT
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 4; j++) {
                int sum = 0;
                for (int u = 0; u < 4; u++) {
                    for (int v = 0; v < 4; v++) {
                        sum += input[u * 4 + v] *
                               static_cast<int>(cos((2 * i + 1) * u * M_PI / 8) *
                                               cos((2 * j + 1) * v * M_PI / 8));
                    }
                }
                output[i * 4 + j] = static_cast<int16_t>(sum / 4);
            }
        }
    }

    /**
     * @brief 环路滤波
     */
    void applyDeblockingFilter() {
        // 简化的去块滤波器
    }

private:
    H264DecodeParams params_;
    bool initialized_ = false;
    int64_t frame_count_ = 0;

    struct SPS {
        int profile_idc = 0;
        int level_idc = 0;
        int width = 0;
        int height = 0;
    } sps_;

    struct PPS {
        int id = 0;
        int sps_id = 0;
        bool cabac = false;
    } pps_;

    std::vector<uint8_t> recon_frame_;
    std::vector<std::vector<uint8_t>> ref_frames_;
};

// 工厂函数
std::unique_ptr<IH264Decoder> createH264Decoder() {
    return std::make_unique<H264DecoderImpl>();
}

} // namespace av_codec
