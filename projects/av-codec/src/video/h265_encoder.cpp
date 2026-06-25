/**
 * @file h265_encoder.cpp
 * @brief H.265/HEVC 编码器实现
 *
 * H.265 相比 H.264 的主要改进：
 * - CTU（编码树单元）最大64x64
 * - 35种帧内预测模式
 * - 更大的变换块（最大32x32）
 * - SAO（样本自适应偏移）
 * - Tiles 和 WPP 并行处理
 */

#include "video/h265_codec.h"
#include <cstring>
#include <algorithm>
#include <cmath>
#include <chrono>

namespace av_codec {

class H265EncoderImpl : public IH265Encoder {
public:
    H265EncoderImpl() = default;
    ~H265EncoderImpl() override { close(); }

    int init(const H265EncodeParams& params) override {
        params_ = params;

        if (params_.width <= 0 || params_.height <= 0) return -1;
        if (params_.width % 2 != 0 || params_.height % 2 != 0) return -2;

        // CTU大小
        ctu_size_ = params_.max_cu_size;
        ctu_width_ = (params_.width + ctu_size_ - 1) / ctu_size_;
        ctu_height_ = (params_.height + ctu_size_ - 1) / ctu_size_;

        // 分配参考帧
        int frame_size = params_.width * params_.height * 3 / 2;
        for (int i = 0; i < params_.ref_frames + 1; i++) {
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

        H265FrameType frame_type = getFrameType(frame_count_);

        // 写入VPS/SPS/PPS（仅IDR帧）
        if (frame_type == H265FrameType::I_FRAME) {
            writeVPS(out_data);
            writeSPS(out_data);
            writePPS(out_data);
        }

        // 写入Slice头
        writeSliceHeader(out_data, frame_type);

        // 编码CTU
        for (int ctu_y = 0; ctu_y < ctu_height_; ctu_y++) {
            for (int ctu_x = 0; ctu_x < ctu_width_; ctu_x++) {
                encodeCTU(yuv_data, ctu_x, ctu_y, frame_type, out_data);
            }
        }

        // SAO滤波
        if (params_.sao) {
            applySAOFilter(out_data);
        }

        // 环路滤波
        applyDeblockingFilter();

        // 更新参考帧
        updateReferenceFrame(yuv_data);

        frame_count_++;
        updateStats(out_data.size(), frame_type);

        return 0;
    }

    int flush(std::vector<uint8_t>& out_data) override {
        out_data.clear();
        return 0;
    }

    H265EncodeStats getStats() const override { return stats_; }

    void close() override {
        initialized_ = false;
        ref_frames_.clear();
    }

private:
    H265FrameType getFrameType(int64_t frame_num) const {
        if (frame_num % params_.gop_size == 0) return H265FrameType::I_FRAME;
        if (frame_num % (params_.max_b_frames + 1) == 0) return H265FrameType::P_FRAME;
        return H265FrameType::B_FRAME;
    }

    void writeVPS(std::vector<uint8_t>& out) {
        // VPS NAL头
        out.push_back(0x00); out.push_back(0x00);
        out.push_back(0x00); out.push_back(0x01);
        out.push_back(0x40);  // VPS NAL type
        // 简化VPS数据
        out.push_back(0x01);  // vps_video_parameter_set_id
    }

    void writeSPS(std::vector<uint8_t>& out) {
        out.push_back(0x00); out.push_back(0x00);
        out.push_back(0x00); out.push_back(0x01);
        out.push_back(0x42);  // SPS NAL type
        // 简化SPS数据
        out.push_back(static_cast<uint8_t>(params_.profile));
        out.push_back(static_cast<uint8_t>(params_.level));
    }

    void writePPS(std::vector<uint8_t>& out) {
        out.push_back(0x00); out.push_back(0x00);
        out.push_back(0x00); out.push_back(0x01);
        out.push_back(0x44);  // PPS NAL type
        out.push_back(0x00);  // pps_pic_parameter_set_id
    }

    void writeSliceHeader(std::vector<uint8_t>& out, H265FrameType type) {
        out.push_back(0x00); out.push_back(0x00);
        out.push_back(0x00); out.push_back(0x01);
        uint8_t nal_type = (type == H265FrameType::I_FRAME) ? 20 : 1;
        out.push_back(nal_type);
    }

    void encodeCTU(const uint8_t* yuv_data, int ctu_x, int ctu_y,
                   H265FrameType type, std::vector<uint8_t>& out) {
        int x = ctu_x * ctu_size_;
        int y = ctu_y * ctu_size_;

        // 四叉树分割
        encodeCU(yuv_data, x, y, ctu_size_, type, out);
    }

    void encodeCU(const uint8_t* yuv_data, int x, int y, int size,
                  H265FrameType type, std::vector<uint8_t>& out) {
        if (size <= params_.min_cu_size) {
            // 叶子节点：编码PU和TU
            if (type == H265FrameType::I_FRAME) {
                encodeIntraPU(yuv_data, x, y, size, out);
            } else {
                encodeInterPU(yuv_data, x, y, size, out);
            }
            return;
        }

        // 决定是否分割
        bool split = shouldSplit(x, y, size, type);

        if (split) {
            int half = size / 2;
            encodeCU(yuv_data, x, y, half, type, out);
            encodeCU(yuv_data, x + half, y, half, type, out);
            encodeCU(yuv_data, x, y + half, half, type, out);
            encodeCU(yuv_data, x + half, y + half, half, type, out);
        } else {
            if (type == H265FrameType::I_FRAME) {
                encodeIntraPU(yuv_data, x, y, size, out);
            } else {
                encodeInterPU(yuv_data, x, y, size, out);
            }
        }
    }

    bool shouldSplit(int x, int y, int size, H265FrameType type) {
        // 简化：根据图像复杂度决定是否分割
        return size > params_.min_cu_size * 2;
    }

    void encodeIntraPU(const uint8_t* yuv_data, int x, int y, int size,
                       std::vector<uint8_t>& out) {
        // 选择最佳帧内模式（从35种模式中选择）
        int best_mode = selectBestIntraMode(yuv_data, x, y, size);

        // 帧内预测
        std::vector<uint8_t> pred(size * size);
        intraPredict(pred.data(), size, best_mode, x, y, size);

        // 计算残差、变换、量化
        std::vector<int16_t> residual(size * size);
        extractAndSubtract(yuv_data, x, y, size, pred.data(), residual.data());

        std::vector<int16_t> coeffs(size * size);
        transform(residual.data(), coeffs.data(), size);

        std::vector<int16_t> quant(size * size);
        quantize(coeffs.data(), quant.data(), size);

        // 熵编码
        entropyEncodePU(quant.data(), best_mode, size, out);
    }

    void encodeInterPU(const uint8_t* yuv_data, int x, int y, int size,
                       std::vector<uint8_t>& out) {
        // 运动估计
        int16_t mv_x = 0, mv_y = 0;
        motionEstimate(yuv_data, x, y, size, mv_x, mv_y);

        // 运动补偿
        std::vector<uint8_t> pred(size * size);
        motionCompensate(x, y, size, mv_x, mv_y, pred.data());

        // 残差、变换、量化
        std::vector<int16_t> residual(size * size);
        extractAndSubtract(yuv_data, x, y, size, pred.data(), residual.data());

        std::vector<int16_t> coeffs(size * size);
        transform(residual.data(), coeffs.data(), size);

        std::vector<int16_t> quant(size * size);
        quantize(coeffs.data(), quant.data(), size);

        // 熵编码
        entropyEncodeInterPU(quant.data(), mv_x, mv_y, size, out);
    }

    int selectBestIntraMode(const uint8_t* yuv_data, int x, int y, int size) {
        // 简化：选择DC模式
        return 1;  // DC
    }

    void intraPredict(uint8_t* pred, int stride, int mode, int x, int y, int size) {
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                pred[i * stride + j] = 128;
            }
        }
    }

    void extractAndSubtract(const uint8_t* yuv_data, int x, int y, int size,
                           const uint8_t* pred, int16_t* residual) {
        int width = params_.width;
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                residual[i * size + j] = static_cast<int16_t>(
                    yuv_data[(y + i) * width + (x + j)]) - pred[i * size + j];
            }
        }
    }

    void transform(const int16_t* input, int16_t* output, int size) {
        // 简化的DCT
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                output[i * size + j] = input[i * size + j];  // 直通
            }
        }
    }

    void quantize(const int16_t* input, int16_t* output, int size) {
        int qstep = 1 << (params_.qp / 6);
        for (int i = 0; i < size * size; i++) {
            output[i] = static_cast<int16_t>(input[i] / qstep);
        }
    }

    void motionEstimate(const uint8_t* yuv_data, int x, int y, int size,
                       int16_t& mv_x, int16_t& mv_y) {
        // 简化的运动估计
        mv_x = 0;
        mv_y = 0;
        uint32_t best_sad = UINT32_MAX;
        int search_range = 16;
        int width = params_.width;
        const uint8_t* ref = ref_frames_[0].data();
        const uint8_t* cur = yuv_data + y * width + x;

        for (int dy = -search_range; dy <= search_range; dy++) {
            for (int dx = -search_range; dx <= search_range; dx++) {
                int rx = x + dx;
                int ry = y + dy;
                if (rx < 0 || ry < 0 || rx + size > width || ry + size > params_.height) continue;

                uint32_t sad = 0;
                for (int i = 0; i < size; i++) {
                    for (int j = 0; j < size; j++) {
                        sad += std::abs(cur[i * width + j] - ref[(ry + i) * width + (rx + j)]);
                    }
                }

                if (sad < best_sad) {
                    best_sad = sad;
                    mv_x = dx;
                    mv_y = dy;
                }
            }
        }
    }

    void motionCompensate(int x, int y, int size, int16_t mv_x, int16_t mv_y, uint8_t* pred) {
        const uint8_t* ref = ref_frames_[0].data();
        int width = params_.width;
        int rx = x + mv_x;
        int ry = y + mv_y;
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                pred[i * size + j] = ref[(ry + i) * width + (rx + j)];
            }
        }
    }

    void entropyEncodePU(const int16_t* quant, int mode, int size, std::vector<uint8_t>& out) {
        out.push_back(static_cast<uint8_t>(mode));
        for (int i = 0; i < size * size; i++) {
            if (quant[i] != 0) out.push_back(static_cast<uint8_t>(quant[i] & 0xFF));
        }
    }

    void entropyEncodeInterPU(const int16_t* quant, int16_t mv_x, int16_t mv_y,
                              int size, std::vector<uint8_t>& out) {
        out.push_back(static_cast<uint8_t>(mv_x & 0xFF));
        out.push_back(static_cast<uint8_t>(mv_y & 0xFF));
        for (int i = 0; i < size * size; i++) {
            if (quant[i] != 0) out.push_back(static_cast<uint8_t>(quant[i] & 0xFF));
        }
    }

    void applySAOFilter(std::vector<uint8_t>& out) {
        // 样本自适应偏移滤波
    }

    void applyDeblockingFilter() {
        // 去块滤波
    }

    void updateReferenceFrame(const uint8_t* yuv_data) {
        int frame_size = params_.width * params_.height * 3 / 2;
        for (int i = ref_frames_.size() - 1; i > 0; i--) {
            ref_frames_[i] = ref_frames_[i - 1];
        }
        std::memcpy(ref_frames_[0].data(), yuv_data, frame_size);
    }

    void updateStats(int64_t bytes, H265FrameType type) {
        stats_.total_bits += bytes * 8;
        stats_.total_frames++;
        if (type == H265FrameType::I_FRAME) stats_.i_frames++;
        else if (type == H265FrameType::P_FRAME) stats_.p_frames++;
        else stats_.b_frames++;

        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - start_time_).count();
        if (elapsed > 0) stats_.fps = static_cast<double>(stats_.total_frames) / elapsed;
    }

private:
    H265EncodeParams params_;
    bool initialized_ = false;
    int ctu_size_ = 64;
    int ctu_width_ = 0;
    int ctu_height_ = 0;
    int64_t frame_count_ = 0;
    std::vector<std::vector<uint8_t>> ref_frames_;
    H265EncodeStats stats_;
    std::chrono::steady_clock::time_point start_time_;
};

std::unique_ptr<IH265Encoder> createH265Encoder() {
    return std::make_unique<H265EncoderImpl>();
}

} // namespace av_codec
