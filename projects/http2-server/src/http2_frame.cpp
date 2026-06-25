/**
 * @file http2_frame.cpp
 * @brief HTTP/2 帧处理实现
 */

#include "http2_frame.h"
#include <stdexcept>

namespace http2 {

std::unique_ptr<Frame> Frame::deserialize(const uint8_t* data, size_t length) {
    if (length < 9) {
        return nullptr;
    }

    auto header = FrameHeader::deserialize(data);

    if (9 + header.length > length) {
        return nullptr;
    }

    const uint8_t* payload = data + 9;

    switch (header.type) {
        case FrameType::DATA: {
            auto frame = std::make_unique<DataFrame>(header.stream_id,
                std::vector<uint8_t>(payload, payload + header.length),
                (header.flags & static_cast<uint8_t>(FrameFlag::END_STREAM)) != 0);
            frame->header = header;
            return frame;
        }

        case FrameType::HEADERS: {
            auto frame = std::make_unique<HeadersFrame>(header.stream_id,
                std::vector<uint8_t>(payload, payload + header.length),
                (header.flags & static_cast<uint8_t>(FrameFlag::END_STREAM)) != 0,
                (header.flags & static_cast<uint8_t>(FrameFlag::END_HEADERS)) != 0);
            frame->header = header;
            return frame;
        }

        case FrameType::SETTINGS: {
            auto frame = std::make_unique<SettingsFrame>();
            frame->header = header;

            if (header.length % 6 != 0) {
                return nullptr;
            }

            for (size_t i = 0; i < header.length; i += 6) {
                uint16_t id = (static_cast<uint16_t>(payload[i]) << 8) | payload[i + 1];
                uint32_t value = (static_cast<uint32_t>(payload[i + 2]) << 24) |
                                (static_cast<uint32_t>(payload[i + 3]) << 16) |
                                (static_cast<uint32_t>(payload[i + 4]) << 8) |
                                static_cast<uint32_t>(payload[i + 5]);
                frame->add_setting(static_cast<SettingsFrame::SettingId>(id), value);
            }

            return frame;
        }

        case FrameType::WINDOW_UPDATE: {
            if (header.length != 4) {
                return nullptr;
            }

            uint32_t increment = (static_cast<uint32_t>(payload[0] & 0x7F) << 24) |
                                (static_cast<uint32_t>(payload[1]) << 16) |
                                (static_cast<uint32_t>(payload[2]) << 8) |
                                static_cast<uint32_t>(payload[3]);

            auto frame = std::make_unique<WindowUpdateFrame>(header.stream_id, increment);
            frame->header = header;
            return frame;
        }

        case FrameType::PING: {
            if (header.length != 8) {
                return nullptr;
            }

            uint64_t ping_data = 0;
            for (int i = 0; i < 8; ++i) {
                ping_data = (ping_data << 8) | payload[i];
            }

            bool ack = (header.flags & 0x01) != 0;
            auto frame = std::make_unique<PingFrame>(ping_data, ack);
            frame->header = header;
            return frame;
        }

        case FrameType::GOAWAY: {
            if (header.length < 8) {
                return nullptr;
            }

            uint32_t last_stream = (static_cast<uint32_t>(payload[0] & 0x7F) << 24) |
                                  (static_cast<uint32_t>(payload[1]) << 16) |
                                  (static_cast<uint32_t>(payload[2]) << 8) |
                                  static_cast<uint32_t>(payload[3]);

            ErrorCode error_code = static_cast<ErrorCode>(
                (static_cast<uint32_t>(payload[4]) << 24) |
                (static_cast<uint32_t>(payload[5]) << 16) |
                (static_cast<uint32_t>(payload[6]) << 8) |
                static_cast<uint32_t>(payload[7])
            );

            std::string debug_data;
            if (header.length > 8) {
                debug_data = std::string(reinterpret_cast<const char*>(payload + 8), header.length - 8);
            }

            auto frame = std::make_unique<GoAwayFrame>(last_stream, error_code, debug_data);
            frame->header = header;
            return frame;
        }

        case FrameType::RST_STREAM: {
            if (header.length != 4) {
                return nullptr;
            }

            ErrorCode error_code = static_cast<ErrorCode>(
                (static_cast<uint32_t>(payload[0]) << 24) |
                (static_cast<uint32_t>(payload[1]) << 16) |
                (static_cast<uint32_t>(payload[2]) << 8) |
                static_cast<uint32_t>(payload[3])
            );

            auto frame = std::make_unique<RstStreamFrame>(header.stream_id, error_code);
            frame->header = header;
            return frame;
        }

        case FrameType::PRIORITY: {
            if (header.length != 5) {
                return nullptr;
            }
            // 简化处理，只返回空帧
            auto frame = std::make_unique<Frame>(FrameType::PRIORITY, header.stream_id);
            frame->header = header;
            frame->payload = std::vector<uint8_t>(payload, payload + header.length);
            return frame;
        }

        default:
            // 未知帧类型
            auto frame = std::make_unique<Frame>(header.type, header.stream_id);
            frame->header = header;
            frame->payload = std::vector<uint8_t>(payload, payload + header.length);
            return frame;
    }
}

} // namespace http2
