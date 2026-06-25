/**
 * @file common.cpp
 * @brief 公共工具函数实现
 *
 * 实现 Base64 编码、SHA-1 哈希等工具函数。
 * SHA-1 用于 WebSocket 握手中的密钥验证。
 */

#include "websocket/common.h"
#include <cstring>

namespace ws {
namespace utils {

// ============================================================================
// Base64 编码
// ============================================================================

static const char BASE64_CHARS[] =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

std::string base64_encode(const uint8_t* data, size_t length) {
    std::string result;
    result.reserve(((length + 2) / 3) * 4);

    for (size_t i = 0; i < length; i += 3) {
        uint32_t octet_a = i < length ? data[i] : 0;
        uint32_t octet_b = (i + 1) < length ? data[i + 1] : 0;
        uint32_t octet_c = (i + 2) < length ? data[i + 2] : 0;

        uint32_t triple = (octet_a << 16) | (octet_b << 8) | octet_c;

        result += BASE64_CHARS[(triple >> 18) & 0x3F];
        result += BASE64_CHARS[(triple >> 12) & 0x3F];

        if ((i + 1) < length) {
            result += BASE64_CHARS[(triple >> 6) & 0x3F];
        } else {
            result += '=';
        }

        if ((i + 2) < length) {
            result += BASE64_CHARS[triple & 0x3F];
        } else {
            result += '=';
        }
    }

    return result;
}

// ============================================================================
// SHA-1 实现
// ============================================================================

/**
 * @brief SHA-1 辅助函数
 */
static inline uint32_t sha1_rotate_left(uint32_t value, int bits) {
    return (value << bits) | (value >> (32 - bits));
}

static inline uint32_t sha1_ft(size_t t, uint32_t b, uint32_t c, uint32_t d) {
    if (t < 20) return (b & c) | ((~b) & d);
    if (t < 40) return b ^ c ^ d;
    if (t < 60) return (b & c) | (b & d) | (c & d);
    return b ^ c ^ d;
}

static inline uint32_t sha1_kt(size_t t) {
    if (t < 20) return 0x5A827999;
    if (t < 40) return 0x6ED9EBA1;
    if (t < 60) return 0x8F1BBCDC;
    return 0xCA62C1D6;
}

std::vector<uint8_t> sha1(const std::string& input) {
    // 初始哈希值
    uint32_t h0 = 0x67452301;
    uint32_t h1 = 0xEFCDAB89;
    uint32_t h2 = 0x98BADCFE;
    uint32_t h3 = 0x10325476;
    uint32_t h4 = 0xC3D2E1F0;

    // 预处理: 添加填充
    size_t original_length = input.size();
    size_t bit_length = original_length * 8;

    // 计算填充后的长度
    size_t padded_length = original_length + 1;  // +1 for 0x80
    while ((padded_length % 64) != 56) {
        padded_length++;
    }
    padded_length += 8;  // +8 for length

    // 创建填充后的消息
    std::vector<uint8_t> padded(padded_length, 0);
    std::memcpy(padded.data(), input.data(), original_length);
    padded[original_length] = 0x80;

    // 添加长度（大端序）
    for (int i = 0; i < 8; ++i) {
        padded[padded_length - 1 - i] = (bit_length >> (i * 8)) & 0xFF;
    }

    // 处理每个 512 位块
    for (size_t chunk = 0; chunk < padded_length; chunk += 64) {
        uint32_t w[80];

        // 将块分解为 16 个 32 位字
        for (int i = 0; i < 16; ++i) {
            w[i] = (static_cast<uint32_t>(padded[chunk + i * 4]) << 24) |
                   (static_cast<uint32_t>(padded[chunk + i * 4 + 1]) << 16) |
                   (static_cast<uint32_t>(padded[chunk + i * 4 + 2]) << 8) |
                   static_cast<uint32_t>(padded[chunk + i * 4 + 3]);
        }

        // 扩展
        for (int i = 16; i < 80; ++i) {
            w[i] = sha1_rotate_left(w[i-3] ^ w[i-8] ^ w[i-14] ^ w[i-16], 1);
        }

        uint32_t a = h0, b = h1, c = h2, d = h3, e = h4;

        for (int i = 0; i < 80; ++i) {
            uint32_t temp = sha1_rotate_left(a, 5) + sha1_ft(i, b, c, d) + e + w[i] + sha1_kt(i);
            e = d;
            d = c;
            c = sha1_rotate_left(b, 30);
            b = a;
            a = temp;
        }

        h0 += a;
        h1 += b;
        h2 += c;
        h3 += d;
        h4 += e;
    }

    // 输出 160 位哈希
    std::vector<uint8_t> hash(20);
    for (int i = 0; i < 4; ++i) {
        hash[i]      = (h0 >> (24 - i * 8)) & 0xFF;
        hash[i + 4]  = (h1 >> (24 - i * 8)) & 0xFF;
        hash[i + 8]  = (h2 >> (24 - i * 8)) & 0xFF;
        hash[i + 12] = (h3 >> (24 - i * 8)) & 0xFF;
        hash[i + 16] = (h4 >> (24 - i * 8)) & 0xFF;
    }

    return hash;
}

} // namespace utils

// ============================================================================
// WebSocket URI 解析
// ============================================================================

std::optional<WebSocketURI> WebSocketURI::parse(const std::string& uri) {
    WebSocketURI result;

    // 检查协议
    if (uri.substr(0, 6) == "wss://") {
        result.secure = true;
        result.port = 443;
    } else if (uri.substr(0, 5) == "ws://") {
        result.secure = false;
        result.port = 80;
    } else {
        return std::nullopt;
    }

    // 解析主机和端口
    size_t host_start = result.secure ? 6 : 5;
    size_t path_start = uri.find('/', host_start);

    std::string host_port;
    if (path_start != std::string::npos) {
        host_port = uri.substr(host_start, path_start - host_start);
        result.path = uri.substr(path_start);
    } else {
        host_port = uri.substr(host_start);
        result.path = "/";
    }

    // 检查查询参数
    size_t query_start = result.path.find('?');
    if (query_start != std::string::npos) {
        result.query = result.path.substr(query_start + 1);
        result.path = result.path.substr(0, query_start);
    }

    // 解析主机和端口
    size_t colon_pos = host_port.find(':');
    if (colon_pos != std::string::npos) {
        result.host = host_port.substr(0, colon_pos);
        try {
            result.port = static_cast<uint16_t>(std::stoi(host_port.substr(colon_pos + 1)));
        } catch (...) {
            return std::nullopt;
        }
    } else {
        result.host = host_port;
    }

    if (result.host.empty()) {
        return std::nullopt;
    }

    return result;
}

} // namespace ws
