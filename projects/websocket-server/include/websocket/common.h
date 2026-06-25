#pragma once
/**
 * @file common.h
 * @brief WebSocket 服务器公共类型定义
 *
 * 定义 WebSocket 协议中使用的枚举、常量和基础类型。
 * 参考 RFC 6455: The WebSocket Protocol
 */

#include <cstdint>
#include <string>
#include <vector>
#include <functional>
#include <memory>
#include <chrono>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <queue>
#include <optional>
#include <sstream>
#include <cstring>
#include <algorithm>
#include <random>

namespace ws {

// ============================================================================
// WebSocket 帧操作码 (RFC 6455 Section 11.8)
// ============================================================================
enum class Opcode : uint8_t {
    Continuation = 0x0,  // 继续帧
    Text         = 0x1,  // 文本帧
    Binary       = 0x2,  // 二进制帧
    Close        = 0x8,  // 关闭帧
    Ping         = 0x9,  // Ping 帧
    Pong         = 0xA,  // Pong 帧
};

// ============================================================================
// WebSocket 连接状态
// ============================================================================
enum class ConnectionState {
    Connecting,    // 正在连接（等待握手）
    Open,          // 连接已建立
    Closing,       // 正在关闭
    Closed,        // 已关闭
};

// ============================================================================
// WebSocket 关闭状态码 (RFC 6455 Section 7.4)
// ============================================================================
enum class CloseCode : uint16_t {
    Normal            = 1000,  // 正常关闭
    GoingAway         = 1001,  // 端点正在离开（如服务器关闭或浏览器导航离开）
    ProtocolError     = 1002,  // 协议错误
    UnsupportedData   = 1003,  // 接收到不可接受的数据类型
    // 1004 保留
    NoStatusReceived  = 1005,  // 预期的状态码（非实际传输）
    AbnormalClosure   = 1006,  // 异常关闭（非实际传输）
    InvalidPayload    = 1007,  // 消息内容与类型不一致
    PolicyViolation   = 1008,  // 策略违规
    MessageTooBig     = 1009,  // 消息过大
    MandatoryExt      = 1010,  // 客户端期望服务器协商一个或多个扩展
    InternalError     = 1011,  // 服务器遇到意外情况
    // 1015 保留 (TLS 握手失败)
};

// ============================================================================
// 帧头结构
// ============================================================================
struct FrameHeader {
    bool     fin;        // 是否是消息的最后一帧
    bool     rsv1;       // 保留位 1 (用于压缩)
    bool     rsv2;       // 保留位 2
    bool     rsv3;       // 保留位 3
    Opcode   opcode;     // 操作码
    bool     masked;     // 是否使用掩码
    uint64_t payload_length;  // 载荷长度
    uint8_t  mask_key[4];     // 掩码密钥 (如果 masked)
};

// ============================================================================
// WebSocket 帧
// ============================================================================
struct Frame {
    FrameHeader header;
    std::vector<uint8_t> payload;  // 载荷数据

    /**
     * @brief 序列化帧为字节流
     * @return 序列化后的字节数据
     */
    std::vector<uint8_t> serialize() const;

    /**
     * @brief 从字节流反序列化帧
     * @param data 输入字节流
     * @param offset 偏移量（输入/输出）
     * @return 解析的帧，如果数据不足返回 nullopt
     */
    static std::optional<Frame> deserialize(const uint8_t* data, size_t length, size_t& offset);
};

// ============================================================================
// WebSocket 消息（由一个或多个帧组成）
// ============================================================================
struct Message {
    Opcode type;                     // 消息类型
    std::vector<uint8_t> data;       // 消息数据

    /**
     * @brief 获取文本内容（仅对文本消息有效）
     */
    std::string text() const {
        return std::string(data.begin(), data.end());
    }

    /**
     * @brief 创建文本消息
     */
    static Message text_message(const std::string& text) {
        Message msg;
        msg.type = Opcode::Text;
        msg.data.assign(text.begin(), text.end());
        return msg;
    }

    /**
     * @brief 创建二进制消息
     */
    static Message binary_message(const std::vector<uint8_t>& bin) {
        Message msg;
        msg.type = Opcode::Binary;
        msg.data = bin;
        return msg;
    }
};

// ============================================================================
// WebSocket URI 解析
// ============================================================================
struct WebSocketURI {
    bool        secure;   // wss://
    std::string host;
    uint16_t    port;
    std::string path;
    std::string query;

    /**
     * @brief 解析 WebSocket URI
     * @param uri ws://host:port/path?query 或 wss://host:port/path
     */
    static std::optional<WebSocketURI> parse(const std::string& uri);
};

// ============================================================================
// 工具函数
// ============================================================================
namespace utils {

/**
 * @brief 生成指定长度的随机字节
 */
inline std::vector<uint8_t> random_bytes(size_t length) {
    std::vector<uint8_t> bytes(length);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 255);
    for (auto& b : bytes) {
        b = static_cast<uint8_t>(dis(gen));
    }
    return bytes;
}

/**
 * @brief Base64 编码
 */
std::string base64_encode(const uint8_t* data, size_t length);

/**
 * @brief SHA-1 哈希（用于握手）
 */
std::vector<uint8_t> sha1(const std::string& input);

/**
 * @brief 应用 WebSocket 掩码
 */
inline void apply_mask(uint8_t* data, size_t length, const uint8_t mask[4]) {
    for (size_t i = 0; i < length; ++i) {
        data[i] ^= mask[i % 4];
    }
}

/**
 * @brief 获取当前时间戳（毫秒）
 */
inline int64_t timestamp_ms() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()
    ).count();
}

} // namespace utils
} // namespace ws
