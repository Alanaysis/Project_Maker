/**
 * @file h264_encoder.cpp
 * @brief H.264 编码器实现
 *
 * 实现 H.264 编码的核心流程：
 * 1. 帧内预测（Intra Prediction）
 * 2. 帧间预测（Inter Prediction）- 运动估计/补偿
 * 3. 变换编码（DCT）
 * 4. 量化（Quantization）
 * 5. 熵编码（CABAC/CAVLC）
 * 6. 环路滤波（Deblocking Filter）
 */

#include "video/h264_codec.h"
#include <cstring>
#include <algorithm>
#include <cmath>
#include <chrono>

namespace av_codec {

/**
 * @brief H.264 编码器实现
 */
class H264EncoderImpl : public IH264Encoder {
public:
    H264EncoderImpl() = default;
    ~H264EncoderImpl() override { close(); }

    int init(const H264EncodeParams& params) override {
        params_ = params;

        // 验证参数
        if (params_.width <= 0 || params_.height <= 0) {
            return -1;
        }
        if (params_.width % 2 != 0 || params_.height % 2 != 0) {
            return -2;  // 宽高必须是偶数
        }

        // 计算宏块数量
        mb_width_ = (params_.width + 15) / 16;
        mb_height_ = (params_.height + 15) / 16;

        // 分配参考帧缓冲区
        int frame_size = params_.width * params_.height * 3 / 2;  // YUV420
        for (int i = 0; i < params_.ref_frames + 1; i++) {
            ref_frames_.push_back(std::vector<uint8_t>(frame_size, 0));
        }

        // 初始化量化参数
        initQuantTables();

        // 初始化扫描顺序
        initScanOrder();

        // 初始化帧内预测模式代价表
        initIntraPredCosts();

        initialized_ = true;
        frame_count_ = 0;
        start_time_ = std::chrono::steady_clock::now();

        return 0;
    }

    int encode(const uint8_t* yuv_data, std::vector<uint8_t>& out_data) override {
        if (!initialized_ || !yuv_data) {
            return -1;
        }

        out_data.clear();

        // 确定帧类型
        H264FrameType frame_type = getFrameType(frame_count_);

        // 写入NAL头
        writeNALHeader(out_data, frame_type);

        // 写入SPS（序列参数集）- 仅在IDR帧
        if (frame_type == H264FrameType::IDR_FRAME) {
            writeSPS(out_data);
            writePPS(out_data);
        }

        // 编码一帧
        int width = params_.width;
        int height = params_.height;
        int mb_size = 16;

        // 对每个宏块进行编码
        for (int mb_y = 0; mb_y < mb_height_; mb_y++) {
            for (int mb_x = 0; mb_x < mb_width_; mb_x++) {
                encodeMacroblock(yuv_data, width, height, mb_x, mb_y,
                               frame_type, out_data);
            }
        }

        // 环路滤波
        applyDeblockingFilter(out_data);

        // 更新参考帧
        updateReferenceFrame(yuv_data);

        // 更新统计信息
        frame_count_++;
        updateStats(out_data.size(), frame_type);

        return 0;
    }

    int flush(std::vector<uint8_t>& out_data) override {
        out_data.clear();
        // 写入结束标记
        out_data.push_back(0x00);
        out_data.push_back(0x00);
        out_data.push_back(0x00);
        out_data.push_back(0x01);
        out_data.push_back(0x0A);  // End of Sequence
        return 0;
    }

    H264EncodeStats getStats() const override {
        return stats_;
    }

    void close() override {
        initialized_ = false;
        ref_frames_.clear();
        quant_table_.clear();
    }

private:
    /**
     * @brief 确定帧类型
     */
    H264FrameType getFrameType(int64_t frame_num) const {
        if (frame_num % params_.gop_size == 0) {
            return H264FrameType::IDR_FRAME;
        }
        // 每隔一定帧数插入P帧
        if (frame_num % (params_.max_b_frames + 1) == 0) {
            return H264FrameType::P_FRAME;
        }
        return H264FrameType::B_FRAME;
    }

    /**
     * @brief 写入NAL头
     */
    void writeNALHeader(std::vector<uint8_t>& out, H264FrameType type) {
        // 起始码
        out.push_back(0x00);
        out.push_back(0x00);
        out.push_back(0x00);
        out.push_back(0x01);

        // NAL单元类型
        uint8_t nal_type = 0;
        switch (type) {
            case H264FrameType::IDR_FRAME:
                nal_type = 5;  // IDR slice
                break;
            case H264FrameType::I_FRAME:
                nal_type = 5;  // I slice
                break;
            case H264FrameType::P_FRAME:
                nal_type = 1;  // Non-IDR slice
                break;
            case H264FrameType::B_FRAME:
                nal_type = 1;  // Non-IDR slice
                break;
            default:
                nal_type = 1;
                break;
        }

        // forbidden_zero_bit(1) | nal_ref_idc(2) | nal_unit_type(5)
        uint8_t nal_header = (0 << 7) | (3 << 5) | nal_type;
        out.push_back(nal_header);
    }

    /**
     * @brief 写入SPS
     */
    void writeSPS(std::vector<uint8_t>& out) {
        // 起始码
        out.push_back(0x00);
        out.push_back(0x00);
        out.push_back(0x00);
        out.push_back(0x01);
        out.push_back(0x67);  // SPS NAL type

        // 简化的SPS数据
        // profile_idc
        out.push_back(static_cast<uint8_t>(params_.profile));
        // constraint_set0_flag - constraint_set5_flag, reserved_zero_2bits
        out.push_back(0x00);
        // level_idc
        out.push_back(static_cast<uint8_t>(params_.level));
        // seq_parameter_set_id (exp-golomb)
        out.push_back(0x00);

        // 简化实现：写入基本参数
        // log2_max_frame_num
        out.push_back(0x08);
        // pic_order_cnt_type
        out.push_back(0x00);
        // max_num_ref_frames
        out.push_back(static_cast<uint8_t>(params_.ref_frames));
        // pic_width_in_mbs_minus1
        uint16_t width_mb = static_cast<uint16_t>(mb_width_ - 1);
        out.push_back(static_cast<uint8_t>((width_mb >> 8) & 0xFF));
        out.push_back(static_cast<uint8_t>(width_mb & 0xFF));
        // pic_height_in_map_units_minus1
        uint16_t height_mb = static_cast<uint16_t>(mb_height_ - 1);
        out.push_back(static_cast<uint8_t>((height_mb >> 8) & 0xFF));
        out.push_back(static_cast<uint8_t>(height_mb & 0xFF));
    }

    /**
     * @brief 写入PPS
     */
    void writePPS(std::vector<uint8_t>& out) {
        // 起始码
        out.push_back(0x00);
        out.push_back(0x00);
        out.push_back(0x00);
        out.push_back(0x01);
        out.push_back(0x68);  // PPS NAL type

        // pic_parameter_set_id
        out.push_back(0x00);
        // seq_parameter_set_id
        out.push_back(0x00);
        // entropy_coding_mode_flag (0=CAVLC, 1=CABAC)
        out.push_back(params_.cabac ? 0x01 : 0x00);
    }

    /**
     * @brief 编码一个宏块
     */
    void encodeMacroblock(const uint8_t* yuv_data, int width, int height,
                          int mb_x, int mb_y, H264FrameType frame_type,
                          std::vector<uint8_t>& out) {
        int x = mb_x * 16;
        int y = mb_y * 16;

        // 判断使用帧内还是帧间预测
        if (frame_type == H264FrameType::IDR_FRAME ||
            frame_type == H264FrameType::I_FRAME) {
            // 帧内预测
            encodeIntraMacroblock(yuv_data, width, height, x, y, out);
        } else {
            // 帧间预测
            encodeInterMacroblock(yuv_data, width, height, x, y, out);
        }
    }

    /**
     * @brief 帧内预测编码宏块
     */
    void encodeIntraMacroblock(const uint8_t* yuv_data, int width, int height,
                               int x, int y, std::vector<uint8_t>& out) {
        // 提取当前宏块
        uint8_t mb[16 * 16];
        extractBlock(yuv_data + y * width + x, width, mb, 16, 16);

        // 选择最佳帧内预测模式
        int best_mode = selectBestIntraMode(mb, x, y);

        // 帧内预测
        uint8_t pred[16 * 16];
        intraPredict(pred, 16, best_mode, x, y);

        // 计算残差
        int16_t residual[16 * 16];
        for (int i = 0; i < 16 * 16; i++) {
            residual[i] = static_cast<int16_t>(mb[i]) - static_cast<int16_t>(pred[i]);
        }

        // DCT变换
        int16_t coeffs[16 * 16];
        dct4x4(residual, coeffs);

        // 量化
        int16_t quant[16 * 16];
        quantize(coeffs, quant, params_.qp);

        // 熵编码
        entropyEncode(quant, best_mode, out);
    }

    /**
     * @brief 帧间预测编码宏块
     */
    void encodeInterMacroblock(const uint8_t* yuv_data, int width, int height,
                               int x, int y, std::vector<uint8_t>& out) {
        // 运动估计
        int16_t mv_x = 0, mv_y = 0;
        motionEstimate(yuv_data, width, height, x, y, mv_x, mv_y);

        // 运动补偿
        uint8_t pred[16 * 16];
        motionCompensate(x, y, mv_x, mv_y, pred);

        // 提取当前宏块
        uint8_t mb[16 * 16];
        extractBlock(yuv_data + y * width + x, width, mb, 16, 16);

        // 计算残差
        int16_t residual[16 * 16];
        for (int i = 0; i < 16 * 16; i++) {
            residual[i] = static_cast<int16_t>(mb[i]) - static_cast<int16_t>(pred[i]);
        }

        // DCT变换
        int16_t coeffs[16 * 16];
        dct4x4(residual, coeffs);

        // 量化
        int16_t quant[16 * 16];
        quantize(coeffs, quant, params_.qp);

        // 熵编码
        entropyEncodeInter(quant, mv_x, mv_y, out);
    }

    /**
     * @brief 提取块
     */
    void extractBlock(const uint8_t* src, int src_stride,
                      uint8_t* dst, int width, int height) {
        for (int y = 0; y < height; y++) {
            std::memcpy(dst + y * width, src + y * src_stride, width);
        }
    }

    /**
     * @brief 选择最佳帧内预测模式
     */
    int selectBestIntraMode(const uint8_t* mb, int x, int y) {
        int best_mode = 0;
        uint32_t best_cost = UINT32_MAX;

        // 简化实现：比较所有模式
        for (int mode = 0; mode < 9; mode++) {
            uint8_t pred[16 * 16];
            intraPredict(pred, 16, mode, x, y);

            // 计算SAD
            uint32_t cost = 0;
            for (int i = 0; i < 16 * 16; i++) {
                cost += std::abs(static_cast<int>(mb[i]) - static_cast<int>(pred[i]));
            }

            if (cost < best_cost) {
                best_cost = cost;
                best_mode = mode;
            }
        }

        return best_mode;
    }

    /**
     * @brief 帧内预测
     */
    void intraPredict(uint8_t* pred, int stride, int mode, int x, int y) {
        // 简化的帧内预测实现
        switch (mode) {
            case 0:  // 垂直预测
                for (int i = 0; i < 16; i++) {
                    for (int j = 0; j < 16; j++) {
                        pred[i * stride + j] = 128;  // 简化：使用DC值
                    }
                }
                break;
            case 1:  // 水平预测
                for (int i = 0; i < 16; i++) {
                    for (int j = 0; j < 16; j++) {
                        pred[i * stride + j] = 128;
                    }
                }
                break;
            case 2:  // DC预测
                for (int i = 0; i < 16; i++) {
                    for (int j = 0; j < 16; j++) {
                        pred[i * stride + j] = 128;
                    }
                }
                break;
            default:
                for (int i = 0; i < 16; i++) {
                    for (int j = 0; j < 16; j++) {
                        pred[i * stride + j] = 128;
                    }
                }
                break;
        }
    }

    /**
     * @brief 运动估计
     */
    void motionEstimate(const uint8_t* cur_data, int width, int height,
                       int x, int y, int16_t& mv_x, int16_t& mv_y) {
        // 简化的运动估计：在搜索范围内找到最佳匹配
        int search_range = 16;
        uint32_t best_sad = UINT32_MAX;
        mv_x = 0;
        mv_y = 0;

        const uint8_t* ref = ref_frames_[0].data();
        const uint8_t* cur = cur_data + y * width + x;

        for (int dy = -search_range; dy <= search_range; dy++) {
            for (int dx = -search_range; dx <= search_range; dx++) {
                int rx = x + dx;
                int ry = y + dy;

                if (rx < 0 || ry < 0 || rx + 16 > width || ry + 16 > height) {
                    continue;
                }

                uint32_t sad = calcSAD(cur, width, ref + ry * width + rx, width, 16, 16);
                if (sad < best_sad) {
                    best_sad = sad;
                    mv_x = dx;
                    mv_y = dy;
                }
            }
        }
    }

    /**
     * @brief 运动补偿
     */
    void motionCompensate(int x, int y, int16_t mv_x, int16_t mv_y, uint8_t* pred) {
        const uint8_t* ref = ref_frames_[0].data();
        int width = params_.width;

        int rx = x + mv_x;
        int ry = y + mv_y;

        for (int i = 0; i < 16; i++) {
            for (int j = 0; j < 16; j++) {
                pred[i * 16 + j] = ref[(ry + i) * width + (rx + j)];
            }
        }
    }

    /**
     * @brief 计算SAD
     */
    uint32_t calcSAD(const uint8_t* src, int src_stride,
                    const uint8_t* ref, int ref_stride,
                    int width, int height) {
        uint32_t sad = 0;
        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                sad += std::abs(static_cast<int>(src[y * src_stride + x]) -
                               static_cast<int>(ref[y * ref_stride + x]));
            }
        }
        return sad;
    }

    /**
     * @brief 4x4 DCT变换
     */
    void dct4x4(const int16_t* input, int16_t* output) {
        // 简化的4x4 DCT
        for (int i = 0; i < 4; i++) {
            for (int j = 0; j < 4; j++) {
                int sum = 0;
                for (int x = 0; x < 4; x++) {
                    for (int y = 0; y < 4; y++) {
                        sum += input[x * 4 + y] *
                               static_cast<int>(cos((2 * x + 1) * i * M_PI / 8) *
                                               cos((2 * y + 1) * j * M_PI / 8));
                    }
                }
                output[i * 4 + j] = static_cast<int16_t>(sum / 4);
            }
        }
    }

    /**
     * @brief 量化
     */
    void quantize(const int16_t* input, int16_t* output, int qp) {
        int qstep = quant_table_[qp % 6] >> (qp / 6);
        for (int i = 0; i < 16 * 16; i++) {
            output[i] = static_cast<int16_t>(input[i] / qstep);
        }
    }

    /**
     * @brief 熵编码（帧内）
     */
    void entropyEncode(const int16_t* quant, int mode, std::vector<uint8_t>& out) {
        // 简化的CAVLC编码
        // 写入预测模式
        out.push_back(static_cast<uint8_t>(mode));

        // 写入量化系数
        for (int i = 0; i < 16 * 16; i++) {
            if (quant[i] != 0) {
                out.push_back(static_cast<uint8_t>(quant[i] & 0xFF));
            }
        }
    }

    /**
     * @brief 熵编码（帧间）
     */
    void entropyEncodeInter(const int16_t* quant, int16_t mv_x, int16_t mv_y,
                           std::vector<uint8_t>& out) {
        // 写入运动向量
        out.push_back(static_cast<uint8_t>(mv_x & 0xFF));
        out.push_back(static_cast<uint8_t>(mv_y & 0xFF));

        // 写入量化系数
        for (int i = 0; i < 16 * 16; i++) {
            if (quant[i] != 0) {
                out.push_back(static_cast<uint8_t>(quant[i] & 0xFF));
            }
        }
    }

    /**
     * @brief 环路滤波
     */
    void applyDeblockingFilter(std::vector<uint8_t>& frame) {
        // 简化的去块滤波器实现
        // 实际应用中需要根据边界强度和阈值进行滤波
    }

    /**
     * @brief 更新参考帧
     */
    void updateReferenceFrame(const uint8_t* yuv_data) {
        int frame_size = params_.width * params_.height * 3 / 2;
        // 将当前帧移至参考帧列表
        for (int i = ref_frames_.size() - 1; i > 0; i--) {
            ref_frames_[i] = ref_frames_[i - 1];
        }
        std::memcpy(ref_frames_[0].data(), yuv_data, frame_size);
    }

    /**
     * @brief 初始化量化表
     */
    void initQuantTables() {
        // H.264 量化步长表
        quant_table_ = {
            10, 11, 13, 14, 16, 18, 20, 22,
            23, 25, 28, 30, 33, 35, 38, 41
        };
    }

    /**
     * @brief 初始化扫描顺序
     */
    void initScanOrder() {
        // Zigzag扫描顺序
        zigzag_order_ = {
            0,  1,  8, 16,  9,  2,  3, 10,
            17, 24, 32, 25, 18, 11,  4,  5,
            12, 19, 26, 33, 40, 48, 41, 34,
            27, 20, 13,  6,  7, 14, 21, 28,
            35, 42, 49, 56, 57, 50, 43, 36,
            29, 22, 15, 23, 30, 37, 44, 51,
            58, 59, 52, 45, 38, 31, 39, 46,
            53, 60, 61, 54, 47, 55, 62, 63
        };
    }

    /**
     * @brief 初始化帧内预测代价表
     */
    void initIntraPredCosts() {
        // 初始化代价表
    }

    /**
     * @brief 更新统计信息
     */
    void updateStats(int64_t bits, H264FrameType type) {
        stats_.total_bits += bits * 8;
        stats_.total_frames++;

        switch (type) {
            case H264FrameType::IDR_FRAME:
            case H264FrameType::I_FRAME:
                stats_.i_frames++;
                break;
            case H264FrameType::P_FRAME:
                stats_.p_frames++;
                break;
            case H264FrameType::B_FRAME:
                stats_.b_frames++;
                break;
            default:
                break;
        }

        // 计算帧率
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - start_time_).count();
        if (elapsed > 0) {
            stats_.fps = static_cast<double>(stats_.total_frames) / elapsed;
        }
    }

private:
    H264EncodeParams params_;
    bool initialized_ = false;
    int mb_width_ = 0;
    int mb_height_ = 0;
    int64_t frame_count_ = 0;

    std::vector<std::vector<uint8_t>> ref_frames_;
    std::vector<int> quant_table_;
    std::vector<int> zigzag_order_;

    H264EncodeStats stats_;
    std::chrono::steady_clock::time_point start_time_;
};

// 工厂函数
std::unique_ptr<IH264Encoder> createH264Encoder() {
    return std::make_unique<H264EncoderImpl>();
}

} // namespace av_codec
