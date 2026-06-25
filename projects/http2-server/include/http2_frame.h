#pragma once
/**
 * @file http2_frame.h
 * @brief HTTP/2 帧格式定义
 *
 * HTTP/2 协议的核心是二进制帧格式。每个帧包含：
 * - 9 字节头部（长度、类型、标志、流标识符）
 * - 帧载荷
 *
 * 帧类型包括：
 * - DATA: 传输数据
 * - HEADERS: 传输头部
 * - PRIORITY: 设置流优先级
 * - RST_STREAM: 终止流
 * - SETTINGS: 配置连接参数
 * - PUSH_PROMISE: 服务器推送
 * - PING: 心跳检测
 * - GOAWAY: 优雅关闭连接
 * - WINDOW_UPDATE: 流量控制
 * - CONTINUATION: 续传头部
 */

#include <cstdint>
#include <vector>
#include <string>
#include <memory>
#include <cstring>

namespace http2 {

// 帧类型定义
enum class FrameType : uint8_t {
    DATA          = 0x00,  // 数据帧
    HEADERS       = 0x01,  // 头部帧
    PRIORITY      = 0x02,  // 优先级帧
    RST_STREAM    = 0x03,  // 重置流帧
    SETTINGS      = 0x04,  // 设置帧
    PUSH_PROMISE  = 0x05,  // 推送承诺帧
    PING          = 0x06,  // 心跳帧
    GOAWAY        = 0x07,  // 关闭帧
    WINDOW_UPDATE = 0x08,  // 窗口更新帧
    CONTINUATION  = 0x09   // 续传帧
};

// 帧标志定义
enum class FrameFlag : uint8_t {
    NONE          = 0x00,
    END_STREAM    = 0x01,  // 结束流标志
    END_HEADERS   = 0x04,  // 结束头部标志
    PADDED        = 0x08,  // 填充标志
    PRIORITY      = 0x20   // 优先级标志
};

// 错误码定义
enum class ErrorCode : uint32_t {
    NO_ERROR           = 0x00,  // 无错误
    PROTOCOL_ERROR     = 0x01,  // 协议错误
    INTERNAL_ERROR     = 0x02,  // 内部错误
    FLOW_CONTROL_ERROR = 0x03,  // 流量控制错误
    SETTINGS_TIMEOUT   = 0x04,  // 设置超时
    STREAM_CLOSED      = 0x05,  // 流已关闭
    FRAME_SIZE_ERROR   = 0x06,  // 帧大小错误
    REFUSED_STREAM     = 0x07,  // 拒绝流
    CANCEL             = 0x08,  // 取消
    COMPRESSION_ERROR  = 0x09,  // 压缩错误
    CONNECT_ERROR      = 0x0a,  // 连接错误
    ENHANCE_YOUR_CALM = 0x0b,  // 增强冷静
    INADEQUATE_SECURITY = 0x0c, // 安全不足
    HTTP_1_1_REQUIRED  = 0x0d   // 需要 HTTP/1.1
};

// 帧头部结构（9字节）
struct FrameHeader {
    uint32_t length;      // 载荷长度（24位）
    FrameType type;       // 帧类型（8位）
    uint8_t flags;        // 帧标志（8位）
    uint32_t stream_id;   // 流标识符（31位，最高位保留）

    // 序列化帧头部
    std::vector<uint8_t> serialize() const {
        std::vector<uint8_t> header(9);
        // 长度（24位，大端序）
        header[0] = (length >> 16) & 0xFF;
        header[1] = (length >> 8) & 0xFF;
        header[2] = length & 0xFF;
        // 类型
        header[3] = static_cast<uint8_t>(type);
        // 标志
        header[4] = flags;
        // 流标识符（31位，大端序）
        header[5] = (stream_id >> 24) & 0x7F;  // 最高位保留
        header[6] = (stream_id >> 16) & 0xFF;
        header[7] = (stream_id >> 8) & 0xFF;
        header[8] = stream_id & 0xFF;
        return header;
    }

    // 反序列化帧头部
    static FrameHeader deserialize(const uint8_t* data) {
        FrameHeader header;
        header.length = (static_cast<uint32_t>(data[0]) << 16) |
                       (static_cast<uint32_t>(data[1]) << 8) |
                       static_cast<uint32_t>(data[2]);
        header.type = static_cast<FrameType>(data[3]);
        header.flags = data[4];
        header.stream_id = (static_cast<uint32_t>(data[5] & 0x7F) << 24) |
                          (static_cast<uint32_t>(data[6]) << 16) |
                          (static_cast<uint32_t>(data[7]) << 8) |
                          static_cast<uint32_t>(data[8]);
        return header;
    }
};

// 帧基类
class Frame {
public:
    FrameHeader header;
    std::vector<uint8_t> payload;

    Frame() = default;
    Frame(FrameType type, uint32_t stream_id, uint8_t flags = 0)
        : header{0, type, flags, stream_id} {}

    virtual ~Frame() = default;

    // 序列化完整帧
    virtual std::vector<uint8_t> serialize() {
        header.length = static_cast<uint32_t>(payload.size());
        auto result = header.serialize();
        result.insert(result.end(), payload.begin(), payload.end());
        return result;
    }

    // 反序列化帧
    static std::unique_ptr<Frame> deserialize(const uint8_t* data, size_t length);
};

// DATA 帧
class DataFrame : public Frame {
public:
    DataFrame(uint32_t stream_id, const std::vector<uint8_t>& data, bool end_stream = true)
        : Frame(FrameType::DATA, stream_id, end_stream ? static_cast<uint8_t>(FrameFlag::END_STREAM) : 0) {
        payload = data;
    }

    // 获取数据
    const std::vector<uint8_t>& get_data() const { return payload; }
};

// HEADERS 帧
class HeadersFrame : public Frame {
public:
    HeadersFrame(uint32_t stream_id, const std::vector<uint8_t>& header_block, bool end_stream = true, bool end_headers = true)
        : Frame(FrameType::HEADERS, stream_id) {
        uint8_t flags = 0;
        if (end_stream) flags |= static_cast<uint8_t>(FrameFlag::END_STREAM);
        if (end_headers) flags |= static_cast<uint8_t>(FrameFlag::END_HEADERS);
        header.flags = flags;
        payload = header_block;
    }
};

// SETTINGS 帧
class SettingsFrame : public Frame {
public:
    // 设置标识符
    enum class SettingId : uint16_t {
        HEADER_TABLE_SIZE      = 0x0001,  // HPACK 动态表大小
        ENABLE_PUSH            = 0x0002,  // 启用服务器推送
        MAX_CONCURRENT_STREAMS = 0x0003,  // 最大并发流
        INITIAL_WINDOW_SIZE    = 0x0004,  // 初始窗口大小
        MAX_FRAME_SIZE         = 0x0005,  // 最大帧大小
        MAX_HEADER_LIST_SIZE   = 0x0006   // 最大头部列表大小
    };

    struct Setting {
        SettingId id;
        uint32_t value;
    };

    std::vector<Setting> settings;

    SettingsFrame() : Frame(FrameType::SETTINGS, 0) {}

    // 添加设置
    void add_setting(SettingId id, uint32_t value) {
        settings.push_back({id, value});
    }

    // 序列化设置帧
    std::vector<uint8_t> serialize() override {
        payload.clear();
        for (const auto& setting : settings) {
            uint16_t id = static_cast<uint16_t>(setting.id);
            payload.push_back((id >> 8) & 0xFF);
            payload.push_back(id & 0xFF);
            payload.push_back((setting.value >> 24) & 0xFF);
            payload.push_back((setting.value >> 16) & 0xFF);
            payload.push_back((setting.value >> 8) & 0xFF);
            payload.push_back(setting.value & 0xFF);
        }
        return Frame::serialize();
    }
};

// WINDOW_UPDATE 帧
class WindowUpdateFrame : public Frame {
public:
    uint32_t window_size_increment;

    WindowUpdateFrame(uint32_t stream_id, uint32_t increment)
        : Frame(FrameType::WINDOW_UPDATE, stream_id), window_size_increment(increment) {
        payload.resize(4);
        payload[0] = (increment >> 24) & 0x7F;  // 最高位保留
        payload[1] = (increment >> 16) & 0xFF;
        payload[2] = (increment >> 8) & 0xFF;
        payload[3] = increment & 0xFF;
    }
};

// GOAWAY 帧
class GoAwayFrame : public Frame {
public:
    uint32_t last_stream_id;
    ErrorCode error_code;
    std::string debug_data;

    GoAwayFrame(uint32_t last_stream, ErrorCode code, const std::string& debug = "")
        : Frame(FrameType::GOAWAY, 0), last_stream_id(last_stream), error_code(code), debug_data(debug) {
        // 序列化载荷
        payload.resize(8 + debug_data.size());
        payload[0] = (last_stream_id >> 24) & 0x7F;
        payload[1] = (last_stream_id >> 16) & 0xFF;
        payload[2] = (last_stream_id >> 8) & 0xFF;
        payload[3] = last_stream_id & 0xFF;
        payload[4] = (static_cast<uint32_t>(error_code) >> 24) & 0xFF;
        payload[5] = (static_cast<uint32_t>(error_code) >> 16) & 0xFF;
        payload[6] = (static_cast<uint32_t>(error_code) >> 8) & 0xFF;
        payload[7] = static_cast<uint32_t>(error_code) & 0xFF;
        std::memcpy(payload.data() + 8, debug_data.data(), debug_data.size());
    }
};

// RST_STREAM 帧
class RstStreamFrame : public Frame {
public:
    ErrorCode error_code;

    RstStreamFrame(uint32_t stream_id, ErrorCode code)
        : Frame(FrameType::RST_STREAM, stream_id), error_code(code) {
        payload.resize(4);
        payload[0] = (static_cast<uint32_t>(code) >> 24) & 0xFF;
        payload[1] = (static_cast<uint32_t>(code) >> 16) & 0xFF;
        payload[2] = (static_cast<uint32_t>(code) >> 8) & 0xFF;
        payload[3] = static_cast<uint32_t>(code) & 0xFF;
    }
};

// PING 帧
class PingFrame : public Frame {
public:
    uint64_t data;

    PingFrame(uint64_t ping_data, bool ack = false)
        : Frame(FrameType::PING, 0, ack ? 0x01 : 0x00), data(ping_data) {
        payload.resize(8);
        for (int i = 7; i >= 0; --i) {
            payload[7 - i] = (data >> (i * 8)) & 0xFF;
        }
    }
};

} // namespace http2
