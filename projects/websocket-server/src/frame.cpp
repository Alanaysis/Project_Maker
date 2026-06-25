/**
 * @file frame.cpp
 * @brief WebSocket 帧编解码器实现
 *
 * 实现 WebSocket 帧的序列化和反序列化。
 * 参考 RFC 6455 Section 5: Wire Format
 */

#include "websocket/frame.h"
#include <cstring>

namespace ws {

// ============================================================================
// FrameCodec 实现
// ============================================================================

std::vector<uint8_t> FrameCodec::serialize_header(const FrameHeader& header,
                                                   uint64_t payload_length) {
    std::vector<uint8_t> header_bytes;

    // 第一个字节: FIN + RSV + Opcode
    uint8_t byte1 = 0;
    if (header.fin)  byte1 |= 0x80;
    if (header.rsv1) byte1 |= 0x40;
    if (header.rsv2) byte1 |= 0x20;
    if (header.rsv3) byte1 |= 0x10;
    byte1 |= static_cast<uint8_t>(header.opcode) & 0x0F;
    header_bytes.push_back(byte1);

    // 第二个字节: MASK + Payload Length
    uint8_t byte2 = 0;
    if (header.masked) byte2 |= 0x80;

    if (payload_length <= 125) {
        // 7 位长度
        byte2 |= static_cast<uint8_t>(payload_length);
        header_bytes.push_back(byte2);
    } else if (payload_length <= 65535) {
        // 7 位 = 126, 后跟 16 位长度
        byte2 |= 126;
        header_bytes.push_back(byte2);
        header_bytes.push_back((payload_length >> 8) & 0xFF);
        header_bytes.push_back(payload_length & 0xFF);
    } else {
        // 7 位 = 127, 后跟 64 位长度
        byte2 |= 127;
        header_bytes.push_back(byte2);
        for (int i = 7; i >= 0; --i) {
            header_bytes.push_back((payload_length >> (i * 8)) & 0xFF);
        }
    }

    // 掩码密钥
    if (header.masked) {
        header_bytes.push_back(header.mask_key[0]);
        header_bytes.push_back(header.mask_key[1]);
        header_bytes.push_back(header.mask_key[2]);
        header_bytes.push_back(header.mask_key[3]);
    }

    return header_bytes;
}

std::vector<uint8_t> FrameCodec::create_control_frame(Opcode opcode,
                                                        const std::vector<uint8_t>& payload) {
    // 控制帧载荷不能超过 125 字节 (RFC 6455 Section 5.5)
    if (payload.size() > 125) {
        return {};
    }

    FrameHeader header{};
    header.fin = true;
    header.rsv1 = false;
    header.rsv2 = false;
    header.rsv3 = false;
    header.opcode = opcode;
    header.masked = false;

    auto result = serialize_header(header, payload.size());
    result.insert(result.end(), payload.begin(), payload.end());
    return result;
}

std::vector<uint8_t> FrameCodec::create_data_frame(Opcode opcode,
                                                     const std::vector<uint8_t>& payload,
                                                     bool fin,
                                                     bool masked) {
    FrameHeader header{};
    header.fin = fin;
    header.rsv1 = false;
    header.rsv2 = false;
    header.rsv3 = false;
    header.opcode = opcode;
    header.masked = masked;

    // 生成掩码密钥
    if (masked) {
        auto mask = utils::random_bytes(4);
        std::memcpy(header.mask_key, mask.data(), 4);
    }

    auto result = serialize_header(header, payload.size());

    // 添加载荷
    if (masked) {
        std::vector<uint8_t> masked_payload = payload;
        utils::apply_mask(masked_payload.data(), masked_payload.size(), header.mask_key);
        result.insert(result.end(), masked_payload.begin(), masked_payload.end());
    } else {
        result.insert(result.end(), payload.begin(), payload.end());
    }

    return result;
}

std::vector<uint8_t> FrameCodec::create_ping(const std::vector<uint8_t>& payload) {
    return create_control_frame(Opcode::Ping, payload);
}

std::vector<uint8_t> FrameCodec::create_pong(const std::vector<uint8_t>& payload) {
    return create_control_frame(Opcode::Pong, payload);
}

std::vector<uint8_t> FrameCodec::create_close_frame(CloseCode code,
                                                      const std::string& reason) {
    std::vector<uint8_t> payload;

    // 状态码 (2 字节, 网络字节序)
    uint16_t code_val = static_cast<uint16_t>(code);
    payload.push_back((code_val >> 8) & 0xFF);
    payload.push_back(code_val & 0xFF);

    // 原因
    payload.insert(payload.end(), reason.begin(), reason.end());

    return create_close_frame(payload);
}

std::vector<uint8_t> FrameCodec::create_close_frame(const std::vector<uint8_t>& payload) {
    return create_control_frame(Opcode::Close, payload);
}

std::vector<uint8_t> FrameCodec::encode_text(const std::string& text, bool masked) {
    std::vector<uint8_t> payload(text.begin(), text.end());
    return create_data_frame(Opcode::Text, payload, true, masked);
}

std::vector<uint8_t> FrameCodec::encode_binary(const std::vector<uint8_t>& data, bool masked) {
    return create_data_frame(Opcode::Binary, data, true, masked);
}

std::optional<Frame> FrameCodec::decode_frame(const uint8_t* data, size_t length,
                                               size_t& bytes_consumed) {
    bytes_consumed = 0;

    if (length < 2) {
        return std::nullopt;  // 数据不足
    }

    Frame frame;
    size_t pos = 0;

    // 第一个字节: FIN + RSV + Opcode
    uint8_t byte1 = data[pos++];
    frame.header.fin  = (byte1 & 0x80) != 0;
    frame.header.rsv1 = (byte1 & 0x40) != 0;
    frame.header.rsv2 = (byte1 & 0x20) != 0;
    frame.header.rsv3 = (byte1 & 0x10) != 0;
    frame.header.opcode = static_cast<Opcode>(byte1 & 0x0F);

    // 第二个字节: MASK + Payload Length
    uint8_t byte2 = data[pos++];
    frame.header.masked = (byte2 & 0x80) != 0;
    uint64_t payload_length = byte2 & 0x7F;

    // 扩展长度
    if (payload_length == 126) {
        if (length < pos + 2) return std::nullopt;
        payload_length = (static_cast<uint64_t>(data[pos]) << 8) | data[pos + 1];
        pos += 2;
    } else if (payload_length == 127) {
        if (length < pos + 8) return std::nullopt;
        payload_length = 0;
        for (int i = 0; i < 8; ++i) {
            payload_length = (payload_length << 8) | data[pos + i];
        }
        pos += 8;
    }

    frame.header.payload_length = payload_length;

    // 掩码密钥
    if (frame.header.masked) {
        if (length < pos + 4) return std::nullopt;
        std::memcpy(frame.header.mask_key, data + pos, 4);
        pos += 4;
    }

    // 载荷数据
    if (length < pos + payload_length) return std::nullopt;

    frame.payload.assign(data + pos, data + pos + payload_length);
    pos += payload_length;

    // 如果有掩码，解码载荷
    if (frame.header.masked) {
        utils::apply_mask(frame.payload.data(), frame.payload.size(), frame.header.mask_key);
    }

    bytes_consumed = pos;
    return frame;
}

std::pair<uint16_t, std::string> FrameCodec::parse_close_payload(
    const std::vector<uint8_t>& payload) {
    if (payload.size() < 2) {
        return {1005, ""};
    }

    uint16_t code = (static_cast<uint16_t>(payload[0]) << 8) | payload[1];
    std::string reason;

    if (payload.size() > 2) {
        reason.assign(payload.begin() + 2, payload.end());
    }

    return {code, reason};
}

// ============================================================================
// Frame 序列化/反序列化
// ============================================================================

std::vector<uint8_t> Frame::serialize() const {
    FrameCodec codec;
    return FrameCodec::create_data_frame(
        header.opcode, payload, header.fin, header.masked);
}

std::optional<Frame> Frame::deserialize(const uint8_t* data, size_t length, size_t& offset) {
    return FrameCodec::decode_frame(data + offset, length - offset, offset);
}

} // namespace ws
