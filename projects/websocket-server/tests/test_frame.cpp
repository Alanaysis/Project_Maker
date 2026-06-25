/**
 * @file test_frame.cpp
 * @brief WebSocket 帧编解码测试
 *
 * 测试 WebSocket 帧的序列化和反序列化功能。
 */

#include "websocket/frame.h"
#include <iostream>
#include <cassert>
#include <cstring>

using namespace ws;

/**
 * @brief 测试工具函数
 */
void assert_eq(int expected, int actual, const std::string& msg) {
    if (expected != actual) {
        std::cerr << "FAIL: " << msg << " (expected " << expected << ", got " << actual << ")" << std::endl;
        exit(1);
    }
}

void assert_true(bool condition, const std::string& msg) {
    if (!condition) {
        std::cerr << "FAIL: " << msg << std::endl;
        exit(1);
    }
}

/**
 * @brief 测试文本帧编码
 */
void test_text_frame_encoding() {
    std::cout << "Testing text frame encoding..." << std::endl;

    std::string text = "Hello, WebSocket!";
    auto data = FrameCodec::encode_text(text);

    // 验证帧头
    assert_true(!data.empty(), "Frame data should not be empty");
    assert_true((data[0] & 0x80) != 0, "FIN bit should be set");
    assert_true((data[0] & 0x0F) == 0x01, "Opcode should be Text (0x1)");

    // 验证载荷长度
    uint8_t len = data[1] & 0x7F;
    assert_eq(text.size(), len, "Payload length should match text size");

    // 验证载荷数据
    std::string payload(data.begin() + 2, data.begin() + 2 + text.size());
    assert_true(payload == text, "Payload should match original text");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试二进制帧编码
 */
void test_binary_frame_encoding() {
    std::cout << "Testing binary frame encoding..." << std::endl;

    std::vector<uint8_t> binary = {0x01, 0x02, 0x03, 0x04, 0x05};
    auto data = FrameCodec::encode_binary(binary);

    // 验证帧头
    assert_true(!data.empty(), "Frame data should not be empty");
    assert_true((data[0] & 0x80) != 0, "FIN bit should be set");
    assert_true((data[0] & 0x0F) == 0x02, "Opcode should be Binary (0x2)");

    // 验证载荷长度
    uint8_t len = data[1] & 0x7F;
    assert_eq(binary.size(), len, "Payload length should match binary size");

    // 验证载荷数据
    std::vector<uint8_t> payload(data.begin() + 2, data.begin() + 2 + binary.size());
    assert_true(payload == binary, "Payload should match original binary");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试帧解码
 */
void test_frame_decoding() {
    std::cout << "Testing frame decoding..." << std::endl;

    // 编码一个文本帧
    std::string text = "Test message";
    auto encoded = FrameCodec::encode_text(text);

    // 解码
    size_t consumed = 0;
    auto frame = FrameCodec::decode_frame(encoded.data(), encoded.size(), consumed);

    assert_true(frame.has_value(), "Frame should be decoded");
    assert_true(frame->header.fin, "FIN bit should be set");
    assert_true(frame->header.opcode == Opcode::Text, "Opcode should be Text");
    assert_true(!frame->header.masked, "Frame should not be masked");
    assert_eq(text.size(), frame->header.payload_length, "Payload length should match");

    std::string decoded_text(frame->payload.begin(), frame->payload.end());
    assert_true(decoded_text == text, "Decoded text should match original");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试掩码处理
 */
void test_masking() {
    std::cout << "Testing masking..." << std::endl;

    // 带掩码编码
    std::string text = "Masked message";
    auto masked = FrameCodec::encode_text(text, true);

    // 验证掩码位
    assert_true((masked[1] & 0x80) != 0, "MASK bit should be set");

    // 解码（应该自动去除掩码）
    size_t consumed = 0;
    auto frame = FrameCodec::decode_frame(masked.data(), masked.size(), consumed);

    assert_true(frame.has_value(), "Frame should be decoded");
    assert_true(frame->header.masked, "Frame should be marked as masked");

    std::string decoded_text(frame->payload.begin(), frame->payload.end());
    assert_true(decoded_text == text, "Decoded text should match original after unmasking");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试控制帧
 */
void test_control_frames() {
    std::cout << "Testing control frames..." << std::endl;

    // Ping 帧
    auto ping = FrameCodec::create_ping();
    assert_true(!ping.empty(), "Ping frame should not be empty");
    assert_true((ping[0] & 0x0F) == 0x09, "Opcode should be Ping (0x9)");

    // Pong 帧
    std::vector<uint8_t> pong_payload = {0x01, 0x02, 0x03};
    auto pong = FrameCodec::create_pong(pong_payload);
    assert_true(!pong.empty(), "Pong frame should not be empty");
    assert_true((pong[0] & 0x0F) == 0x0A, "Opcode should be Pong (0xA)");

    // 关闭帧
    auto close = FrameCodec::create_close_frame(CloseCode::Normal, "Bye");
    assert_true(!close.empty(), "Close frame should not be empty");
    assert_true((close[0] & 0x0F) == 0x08, "Opcode should be Close (0x8)");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试大载荷帧
 */
void test_large_payload() {
    std::cout << "Testing large payload..." << std::endl;

    // 创建 200 字节的载荷（需要 16 位扩展长度）
    std::string large_text(200, 'A');
    auto data = FrameCodec::encode_text(large_text);

    // 验证使用了 16 位扩展长度
    assert_true((data[1] & 0x7F) == 126, "Should use 16-bit extended length");

    // 验证长度
    uint16_t len = (static_cast<uint16_t>(data[2]) << 8) | data[3];
    assert_eq(200, len, "Extended length should be 200");

    // 解码
    size_t consumed = 0;
    auto frame = FrameCodec::decode_frame(data.data(), data.size(), consumed);

    assert_true(frame.has_value(), "Frame should be decoded");
    assert_eq(200, frame->header.payload_length, "Payload length should be 200");

    std::string decoded_text(frame->payload.begin(), frame->payload.end());
    assert_true(decoded_text == large_text, "Decoded text should match original");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试关闭帧解析
 */
void test_close_frame_parsing() {
    std::cout << "Testing close frame parsing..." << std::endl;

    auto close = FrameCodec::create_close_frame(CloseCode::Normal, "Goodbye");
    size_t consumed = 0;
    auto frame = FrameCodec::decode_frame(close.data(), close.size(), consumed);

    assert_true(frame.has_value(), "Close frame should be decoded");
    assert_true(frame->header.opcode == Opcode::Close, "Opcode should be Close");

    auto [code, reason] = FrameCodec::parse_close_payload(frame->payload);
    assert_eq(1000, code, "Close code should be 1000 (Normal)");
    assert_true(reason == "Goodbye", "Close reason should match");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试 Base64 编码
 */
void test_base64() {
    std::cout << "Testing Base64 encoding..." << std::endl;

    // 测试已知值
    std::string input = "Hello";
    auto encoded = utils::base64_encode(
        reinterpret_cast<const uint8_t*>(input.data()), input.size());

    assert_true(encoded == "SGVsbG8=", "Base64 encoding should match expected output");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试 SHA-1 哈希
 */
void test_sha1() {
    std::cout << "Testing SHA-1..." << std::endl;

    // 测试已知值
    auto hash = utils::sha1("test");
    assert_true(hash.size() == 20, "SHA-1 hash should be 20 bytes");

    // 验证第一个字节（SHA-1("test") = a94a8fe5...)
    assert_true(hash[0] == 0xa9, "First byte should be 0xa9");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== WebSocket Frame Tests ===" << std::endl;

    test_text_frame_encoding();
    test_binary_frame_encoding();
    test_frame_decoding();
    test_masking();
    test_control_frames();
    test_large_payload();
    test_close_frame_parsing();
    test_base64();
    test_sha1();

    std::cout << "\nAll tests passed!" << std::endl;
    return 0;
}
