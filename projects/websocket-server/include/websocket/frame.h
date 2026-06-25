#pragma once
/**
 * @file frame.h
 * @brief WebSocket 帧编解码器
 *
 * 实现 WebSocket 帧的序列化和反序列化。
 * 参考 RFC 6455 Section 5: Wire Format
 *
 * 帧格式：
 *   0                   1                   2                   3
 *   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 *  +-+-+-+-+-------+-+-------------+-------------------------------+
 *  |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
 *  |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
 *  |N|V|V|V|       |S|             |   (if payload len==126/127)   |
 *  | |1|2|3|       |K|             |                               |
 *  +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
 *  |     Extended payload length continued, if payload len == 127  |
 *  + - - - - - - - - - - - - - - - +-------------------------------+
 *  |                               |Masking-key, if MASK set to 1  |
 *  +-------------------------------+-------------------------------+
 *  | Masking-key (continued)       |          Payload Data         |
 *  +-------------------------------- - - - - - - - - - - - - - - - +
 */

#include "common.h"

namespace ws {

/**
 * @brief 帧编码器/解码器
 *
 * 负责将 WebSocket 帧序列化为字节流，
 * 以及从字节流中解析 WebSocket 帧。
 */
class FrameCodec {
public:
    /**
     * @brief 创建控制帧
     * @param opcode 操作码 (Close, Ping, Pong)
     * @param payload 载荷数据
     * @return 序列化后的帧数据
     */
    static std::vector<uint8_t> create_control_frame(Opcode opcode,
                                                       const std::vector<uint8_t>& payload = {});

    /**
     * @brief 创建数据帧
     * @param opcode 操作码 (Text, Binary)
     * @param payload 载荷数据
     * @param fin 是否是最后一帧
     * @param masked 是否使用掩码（客户端发送的帧需要掩码）
     * @return 序列化后的帧数据
     */
    static std::vector<uint8_t> create_data_frame(Opcode opcode,
                                                    const std::vector<uint8_t>& payload,
                                                    bool fin = true,
                                                    bool masked = false);

    /**
     * @brief 创建 Ping 帧
     * @param payload 可选的载荷数据
     */
    static std::vector<uint8_t> create_ping(const std::vector<uint8_t>& payload = {});

    /**
     * @brief 创建 Pong 帧
     * @param payload 载荷数据（通常与 Ping 帧相同）
     */
    static std::vector<uint8_t> create_pong(const std::vector<uint8_t>& payload = {});

    /**
     * @brief 创建关闭帧
     * @param code 关闭状态码
     * @param reason 关闭原因
     */
    static std::vector<uint8_t> create_close_frame(CloseCode code,
                                                     const std::string& reason = "");

    /**
     * @brief 创建关闭帧（原始数据）
     * @param payload 载荷数据（状态码 + 原因）
     */
    static std::vector<uint8_t> create_close_frame(const std::vector<uint8_t>& payload);

    /**
     * @brief 将文本消息编码为帧
     */
    static std::vector<uint8_t> encode_text(const std::string& text, bool masked = false);

    /**
     * @brief 将二进制消息编码为帧
     */
    static std::vector<uint8_t> encode_binary(const std::vector<uint8_t>& data, bool masked = false);

    /**
     * @brief 解析单个帧
     * @param data 输入缓冲区
     * @param length 缓冲区长度
     * @param bytes_consumed 消耗的字节数（输出）
     * @return 解析的帧，数据不足时返回 nullopt
     */
    static std::optional<Frame> decode_frame(const uint8_t* data, size_t length,
                                              size_t& bytes_consumed);

    /**
     * @brief 解析关闭帧的关闭码和原因
     * @param payload 关闭帧的载荷
     * @return 关闭码和原因
     */
    static std::pair<uint16_t, std::string> parse_close_payload(
        const std::vector<uint8_t>& payload);

private:
    /**
     * @brief 序列化帧头
     * @param header 帧头结构
     * @param payload_length 载荷长度
     * @return 序列化后的帧头字节
     */
    static std::vector<uint8_t> serialize_header(const FrameHeader& header,
                                                  uint64_t payload_length);
};

} // namespace ws
