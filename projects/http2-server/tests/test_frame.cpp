/**
 * @file test_frame.cpp
 * @brief HTTP/2 帧处理测试
 */

#include "http2_frame.h"
#include <iostream>
#include <cassert>
#include <cstring>

using namespace http2;

void test_frame_header_serialize() {
    std::cout << "Testing FrameHeader serialize..." << std::endl;

    FrameHeader header;
    header.length = 100;
    header.type = FrameType::DATA;
    header.flags = 0x01;
    header.stream_id = 1;

    auto data = header.serialize();

    // 验证长度（24位）
    assert(data[0] == 0);
    assert(data[1] == 0);
    assert(data[2] == 100);

    // 验证类型
    assert(data[3] == 0x00);  // DATA

    // 验证标志
    assert(data[4] == 0x01);

    // 验证流 ID（31位）
    assert(data[5] == 0);
    assert(data[6] == 0);
    assert(data[7] == 0);
    assert(data[8] == 1);

    std::cout << "  PASSED" << std::endl;
}

void test_frame_header_deserialize() {
    std::cout << "Testing FrameHeader deserialize..." << std::endl;

    uint8_t data[] = {
        0x00, 0x00, 0x64,  // 长度: 100
        0x01,               // 类型: HEADERS
        0x04,               // 标志: END_HEADERS
        0x00, 0x00, 0x00, 0x03  // 流 ID: 3
    };

    auto header = FrameHeader::deserialize(data);

    assert(header.length == 100);
    assert(header.type == FrameType::HEADERS);
    assert(header.flags == 0x04);
    assert(header.stream_id == 3);

    std::cout << "  PASSED" << std::endl;
}

void test_settings_frame() {
    std::cout << "Testing SettingsFrame..." << std::endl;

    SettingsFrame frame;
    frame.add_setting(SettingsFrame::SettingId::HEADER_TABLE_SIZE, 4096);
    frame.add_setting(SettingsFrame::SettingId::MAX_CONCURRENT_STREAMS, 100);
    frame.add_setting(SettingsFrame::SettingId::INITIAL_WINDOW_SIZE, 65535);

    auto data = frame.serialize();

    // 验证帧头部
    assert(data[3] == 0x04);  // SETTINGS 类型
    assert(data[4] == 0x00);  // 无标志

    // 验证载荷大小（每个设置 6 字节）
    assert(frame.payload.size() == 18);

    std::cout << "  PASSED" << std::endl;
}

void test_window_update_frame() {
    std::cout << "Testing WindowUpdateFrame..." << std::endl;

    WindowUpdateFrame frame(1, 1024);

    auto data = frame.serialize();

    // 验证帧类型
    assert(data[3] == 0x08);  // WINDOW_UPDATE

    // 验证窗口增量
    uint32_t increment = (static_cast<uint32_t>(frame.payload[0] & 0x7F) << 24) |
                        (static_cast<uint32_t>(frame.payload[1]) << 16) |
                        (static_cast<uint32_t>(frame.payload[2]) << 8) |
                        static_cast<uint32_t>(frame.payload[3]);
    assert(increment == 1024);

    std::cout << "  PASSED" << std::endl;
}

void test_goaway_frame() {
    std::cout << "Testing GoAwayFrame..." << std::endl;

    GoAwayFrame frame(10, ErrorCode::NO_ERROR, "test debug data");

    auto data = frame.serialize();

    // 验证帧类型
    assert(data[3] == 0x07);  // GOAWAY

    // 验证最后流 ID
    uint32_t last_stream = (static_cast<uint32_t>(frame.payload[0] & 0x7F) << 24) |
                          (static_cast<uint32_t>(frame.payload[1]) << 16) |
                          (static_cast<uint32_t>(frame.payload[2]) << 8) |
                          static_cast<uint32_t>(frame.payload[3]);
    assert(last_stream == 10);

    // 验证错误码
    ErrorCode error_code = static_cast<ErrorCode>(
        (static_cast<uint32_t>(frame.payload[4]) << 24) |
        (static_cast<uint32_t>(frame.payload[5]) << 16) |
        (static_cast<uint32_t>(frame.payload[6]) << 8) |
        static_cast<uint32_t>(frame.payload[7])
    );
    assert(error_code == ErrorCode::NO_ERROR);

    std::cout << "  PASSED" << std::endl;
}

void test_ping_frame() {
    std::cout << "Testing PingFrame..." << std::endl;

    uint64_t ping_data = 0x1234567890ABCDEF;
    PingFrame frame(ping_data, false);

    auto data = frame.serialize();

    // 验证帧类型
    assert(data[3] == 0x06);  // PING

    // 验证 ACK 标志
    assert(data[4] == 0x00);  // 非 ACK

    // 验证数据
    uint64_t decoded_data = 0;
    for (int i = 0; i < 8; ++i) {
        decoded_data = (decoded_data << 8) | frame.payload[i];
    }
    assert(decoded_data == ping_data);

    // 测试 ACK
    PingFrame ack_frame(ping_data, true);
    assert(ack_frame.header.flags == 0x01);

    std::cout << "  PASSED" << std::endl;
}

void test_rst_stream_frame() {
    std::cout << "Testing RstStreamFrame..." << std::endl;

    RstStreamFrame frame(5, ErrorCode::CANCEL);

    auto data = frame.serialize();

    // 验证帧类型
    assert(data[3] == 0x03);  // RST_STREAM

    // 验证错误码
    ErrorCode error_code = static_cast<ErrorCode>(
        (static_cast<uint32_t>(frame.payload[0]) << 24) |
        (static_cast<uint32_t>(frame.payload[1]) << 16) |
        (static_cast<uint32_t>(frame.payload[2]) << 8) |
        static_cast<uint32_t>(frame.payload[3])
    );
    assert(error_code == ErrorCode::CANCEL);

    std::cout << "  PASSED" << std::endl;
}

void test_data_frame() {
    std::cout << "Testing DataFrame..." << std::endl;

    std::vector<uint8_t> test_data = {0x01, 0x02, 0x03, 0x04, 0x05};
    DataFrame frame(1, test_data, true);

    auto data = frame.serialize();

    // 验证帧类型
    assert(data[3] == 0x00);  // DATA

    // 验证 END_STREAM 标志
    assert(data[4] & 0x01);

    // 验证载荷
    assert(frame.payload == test_data);

    std::cout << "  PASSED" << std::endl;
}

int main() {
    std::cout << "Running HTTP/2 Frame Tests..." << std::endl;
    std::cout << std::endl;

    test_frame_header_serialize();
    test_frame_header_deserialize();
    test_settings_frame();
    test_window_update_frame();
    test_goaway_frame();
    test_ping_frame();
    test_rst_stream_frame();
    test_data_frame();

    std::cout << std::endl;
    std::cout << "All frame tests PASSED!" << std::endl;

    return 0;
}
