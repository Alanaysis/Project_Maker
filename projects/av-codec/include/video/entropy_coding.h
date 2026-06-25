#pragma once

/**
 * @file entropy_coding.h
 * @brief 熵编码接口定义
 *
 * 熵编码是无损压缩的最后一步。
 * 主要方法：
 * - CAVLC（基于上下文的自适应可变长编码）：H.264 Baseline
 * - CABAC（基于上下文的自适应二进制算术编码）：H.264 Main/High
 * - Exp-Golomb：指数哥伦布编码
 * - 算术编码：通用算术编码
 * - Range Coding：范围编码
 * - Rans：非对称数字系统
 */

#include <cstdint>
#include <vector>
#include <cstddef>

namespace av_codec {

/**
 * @brief 熵编码类型
 */
enum class EntropyCodingType : uint8_t {
    CAVLC = 0,      ///< CAVLC
    CABAC = 1,      ///< CABAC
    EXP_GOLOMB = 2, ///< 指数哥伦布
    ARITHMETIC = 3, ///< 算术编码
    RANGE_CODING = 4, ///< 范围编码
    RANS = 5        ///< ANS
};

/**
 * @brief CABAC 上下文模型
 */
struct CABACContext {
    uint8_t state = 0;      ///< 状态 (0-63)
    uint8_t mps = 0;        ///< 最可能符号 (0或1)
};

/**
 * @brief 熵编码参数
 */
struct EntropyCodingParams {
    EntropyCodingType type = EntropyCodingType::CABAC; ///< 编码类型
    int bit_depth = 8;          ///< 位深度
    bool cabac_init_idc = 0;    ///< CABAC初始化表索引
};

/**
 * @brief 位流写入器
 */
class BitStreamWriter {
public:
    BitStreamWriter() = default;
    virtual ~BitStreamWriter() = default;

    /**
     * @brief 写入比特
     * @param value 值
     * @param bits 比特数
     */
    virtual void writeBits(uint32_t value, int bits) = 0;

    /**
     * @brief 写入1比特
     * @param bit 比特值
     */
    virtual void writeBit(int bit) = 0;

    /**
     * @brief 写入指数哥伦布编码
     * @param value 值
     */
    virtual void writeExpGolomb(uint32_t value) = 0;

    /**
     * @brief 写入有符号指数哥伦布编码
     * @param value 值
     */
    virtual void writeSignedExpGolomb(int32_t value) = 0;

    /**
     * @brief 字节对齐
     */
    virtual void align() = 0;

    /**
     * @brief 获取输出数据
     * @return 输出数据
     */
    virtual const std::vector<uint8_t>& getData() const = 0;

    /**
     * @brief 获取已写入的比特数
     * @return 比特数
     */
    virtual size_t getBitCount() const = 0;

    /**
     * @brief 重置
     */
    virtual void reset() = 0;
};

/**
 * @brief 位流读取器
 */
class BitStreamReader {
public:
    BitStreamReader() = default;
    virtual ~BitStreamReader() = default;

    /**
     * @brief 初始化
     * @param data 输入数据
     * @param size 数据大小
     * @return 0成功，负数失败
     */
    virtual int init(const uint8_t* data, size_t size) = 0;

    /**
     * @brief 读取比特
     * @param bits 比特数
     * @return 读取的值
     */
    virtual uint32_t readBits(int bits) = 0;

    /**
     * @brief 读取1比特
     * @return 比特值
     */
    virtual int readBit() = 0;

    /**
     * @brief 读取指数哥伦布编码
     * @return 读取的值
     */
    virtual uint32_t readExpGolomb() = 0;

    /**
     * @brief 读取有符号指数哥伦布编码
     * @return 读取的值
     */
    virtual int32_t readSignedExpGolomb() = 0;

    /**
     * @brief 字节对齐
     */
    virtual void align() = 0;

    /**
     * @brief 是否到达末尾
     * @return true/false
     */
    virtual bool eof() const = 0;

    /**
     * @brief 获取当前位置（比特）
     * @return 位置
     */
    virtual size_t getBitPosition() const = 0;

    /**
     * @brief 重置
     */
    virtual void reset() = 0;
};

/**
 * @brief 熵编码器接口
 */
class IEntropyEncoder {
public:
    virtual ~IEntropyEncoder() = default;

    /**
     * @brief 初始化编码器
     * @param params 熵编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const EntropyCodingParams& params) = 0;

    /**
     * @brief 编码一个符号
     * @param symbol 符号值
     * @param ctx 上下文模型
     * @return 0成功，负数失败
     */
    virtual int encodeSymbol(int symbol, CABACContext& ctx) = 0;

    /**
     * @brief 编码二进制符号
     * @param bin 二进制值
     * @param ctx 上下文模型
     * @return 0成功，负数失败
     */
    virtual int encodeBin(int bin, CABACContext& ctx) = 0;

    /**
     * @brief 编码终止符号
     * @param bin 终止符号
     * @return 0成功，负数失败
     */
    virtual int encodeTerminate(int bin) = 0;

    /**
     * @brief 刷新编码器
     * @return 0成功，负数失败
     */
    virtual int flush() = 0;

    /**
     * @brief 获取输出数据
     * @return 输出数据
     */
    virtual const std::vector<uint8_t>& getOutput() const = 0;

    /**
     * @brief 关闭编码器
     */
    virtual void close() = 0;
};

/**
 * @brief 熵解码器接口
 */
class IEntropyDecoder {
public:
    virtual ~IEntropyDecoder() = default;

    /**
     * @brief 初始化解码器
     * @param params 熵编码参数
     * @return 0成功，负数失败
     */
    virtual int init(const EntropyCodingParams& params) = 0;

    /**
     * @brief 解码一个符号
     * @param ctx 上下文模型
     * @return 符号值
     */
    virtual int decodeSymbol(CABACContext& ctx) = 0;

    /**
     * @brief 解码二进制符号
     * @param ctx 上下文模型
     * @return 二进制值
     */
    virtual int decodeBin(CABACContext& ctx) = 0;

    /**
     * @brief 解码终止符号
     * @return 终止符号
     */
    virtual int decodeTerminate() = 0;

    /**
     * @brief 设置输入数据
     * @param data 输入数据
     * @param size 数据大小
     * @return 0成功，负数失败
     */
    virtual int setInput(const uint8_t* data, size_t size) = 0;

    /**
     * @brief 关闭解码器
     */
    virtual void close() = 0;
};

} // namespace av_codec
