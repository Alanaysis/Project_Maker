/**
 * @file entropy_coding.cpp
 * @brief 熵编码实现
 *
 * 熵编码类型：
 * - CAVLC：基于上下文的自适应可变长编码
 * - CABAC：基于上下文的自适应二进制算术编码
 * - Exp-Golomb：指数哥伦布编码
 */

#include "video/entropy_coding.h"
#include <cstring>
#include <vector>
#include <cstdint>

namespace av_codec {

/**
 * @brief 位流写入器实现
 */
class BitStreamWriterImpl : public BitStreamWriter {
public:
    BitStreamWriterImpl() { reset(); }

    void writeBits(uint32_t value, int bits) override {
        for (int i = bits - 1; i >= 0; i--) {
            writeBit((value >> i) & 1);
        }
    }

    void writeBit(int bit) override {
        if (bit_count_ % 8 == 0) {
            data_.push_back(0);
        }
        if (bit) {
            data_.back() |= (1 << (7 - (bit_count_ % 8)));
        }
        bit_count_++;
    }

    void writeExpGolomb(uint32_t value) override {
        value++;
        int bits = 0;
        uint32_t tmp = value;
        while (tmp > 0) {
            bits++;
            tmp >>= 1;
        }

        // 写入前导零
        for (int i = 0; i < bits - 1; i++) {
            writeBit(0);
        }

        // 写入值
        writeBits(value, bits);
    }

    void writeSignedExpGolomb(int32_t value) override {
        uint32_t code;
        if (value > 0) {
            code = 2 * value - 1;
        } else {
            code = -2 * value;
        }
        writeExpGolomb(code);
    }

    void align() override {
        while (bit_count_ % 8 != 0) {
            writeBit(0);
        }
    }

    const std::vector<uint8_t>& getData() const override { return data_; }
    size_t getBitCount() const override { return bit_count_; }

    void reset() override {
        data_.clear();
        bit_count_ = 0;
    }

private:
    std::vector<uint8_t> data_;
    size_t bit_count_ = 0;
};

/**
 * @brief 位流读取器实现
 */
class BitStreamReaderImpl : public BitStreamReader {
public:
    BitStreamReaderImpl() = default;

    int init(const uint8_t* data, size_t size) override {
        data_ = data;
        size_ = size;
        bit_pos_ = 0;
        return 0;
    }

    uint32_t readBits(int bits) override {
        uint32_t value = 0;
        for (int i = 0; i < bits; i++) {
            value <<= 1;
            value |= readBit();
        }
        return value;
    }

    int readBit() override {
        if (bit_pos_ >= size_ * 8) return 0;

        int byte_idx = bit_pos_ / 8;
        int bit_idx = 7 - (bit_pos_ % 8);
        bit_pos_++;

        return (data_[byte_idx] >> bit_idx) & 1;
    }

    uint32_t readExpGolomb() override {
        int leading_zeros = 0;
        while (readBit() == 0 && leading_zeros < 32) {
            leading_zeros++;
        }

        if (leading_zeros == 0) return 0;

        uint32_t value = 1;
        for (int i = 0; i < leading_zeros; i++) {
            value <<= 1;
            value |= readBit();
        }

        return value - 1;
    }

    int32_t readSignedExpGolomb() override {
        uint32_t code = readExpGolomb();
        if (code & 1) {
            return static_cast<int32_t>((code + 1) / 2);
        } else {
            return -static_cast<int32_t>(code / 2);
        }
    }

    void align() override {
        while (bit_pos_ % 8 != 0) {
            bit_pos_++;
        }
    }

    bool eof() const override { return bit_pos_ >= size_ * 8; }
    size_t getBitPosition() const override { return bit_pos_; }

    void reset() override {
        data_ = nullptr;
        size_ = 0;
        bit_pos_ = 0;
    }

private:
    const uint8_t* data_ = nullptr;
    size_t size_ = 0;
    size_t bit_pos_ = 0;
};

/**
 * @brief CABAC 编码器实现
 */
class CABACEncoder : public IEntropyEncoder {
public:
    int init(const EntropyCodingParams& params) override {
        params_ = params;
        writer_ = std::make_unique<BitStreamWriterImpl>();
        initContexts();
        return 0;
    }

    int encodeSymbol(int symbol, CABACContext& ctx) override {
        return encodeBin(symbol, ctx);
    }

    int encodeBin(int bin, CABACContext& ctx) override {
        // CABAC编码
        int state = ctx.state;
        int mps = ctx.mps;

        if (bin == mps) {
            // 大概率符号
            writer_->writeBit(0);
            // 更新状态
            ctx.state = next_state_mps_[state];
        } else {
            // 小概率符号
            writer_->writeBit(1);
            // 更新状态
            ctx.state = next_state_lps_[state];
            if (state == 0) {
                ctx.mps = 1 - mps;
            }
        }

        return 0;
    }

    int encodeTerminate(int bin) override {
        if (bin) {
            writer_->writeBit(1);
        } else {
            writer_->writeBit(0);
        }
        return 0;
    }

    int flush() override {
        writer_->align();
        return 0;
    }

    const std::vector<uint8_t>& getOutput() const override {
        return writer_->getData();
    }

    void close() override {
        writer_.reset();
    }

private:
    void initContexts() {
        // 初始化CABAC状态转移表
        for (int i = 0; i < 64; i++) {
            next_state_mps_[i] = std::min(i + 1, 63);
            next_state_lps_[i] = std::max(0, i - 1);
        }
    }

private:
    EntropyCodingParams params_;
    std::unique_ptr<BitStreamWriterImpl> writer_;
    int next_state_mps_[64];
    int next_state_lps_[64];
};

/**
 * @brief CABAC 解码器实现
 */
class CABACDecoder : public IEntropyDecoder {
public:
    int init(const EntropyCodingParams& params) override {
        params_ = params;
        reader_ = std::make_unique<BitStreamReaderImpl>();
        initContexts();
        return 0;
    }

    int decodeSymbol(CABACContext& ctx) override {
        return decodeBin(ctx);
    }

    int decodeBin(CABACContext& ctx) override {
        int state = ctx.state;
        int mps = ctx.mps;

        int bin = reader_->readBit();

        if (bin == 0) {
            // 大概率符号
            ctx.state = next_state_mps_[state];
            return mps;
        } else {
            // 小概率符号
            ctx.state = next_state_lps_[state];
            if (state == 0) {
                ctx.mps = 1 - mps;
            }
            return 1 - mps;
        }
    }

    int decodeTerminate() override {
        return reader_->readBit();
    }

    int setInput(const uint8_t* data, size_t size) override {
        return reader_->init(data, size);
    }

    void close() override {
        reader_.reset();
    }

private:
    void initContexts() {
        for (int i = 0; i < 64; i++) {
            next_state_mps_[i] = std::min(i + 1, 63);
            next_state_lps_[i] = std::max(0, i - 1);
        }
    }

private:
    EntropyCodingParams params_;
    std::unique_ptr<BitStreamReaderImpl> reader_;
    int next_state_mps_[64];
    int next_state_lps_[64];
};

// 工厂函数
std::unique_ptr<IEntropyEncoder> createEntropyEncoder(EntropyCodingType type) {
    EntropyCodingParams params;
    params.type = type;
    auto encoder = std::make_unique<CABACEncoder>();
    encoder->init(params);
    return encoder;
}

std::unique_ptr<IEntropyDecoder> createEntropyDecoder(EntropyCodingType type) {
    EntropyCodingParams params;
    params.type = type;
    auto decoder = std::make_unique<CABACDecoder>();
    decoder->init(params);
    return decoder;
}

std::unique_ptr<BitStreamWriter> createBitStreamWriter() {
    return std::make_unique<BitStreamWriterImpl>();
}

std::unique_ptr<BitStreamReader> createBitStreamReader() {
    return std::make_unique<BitStreamReaderImpl>();
}

} // namespace av_codec
