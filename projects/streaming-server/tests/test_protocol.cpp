/**
 * @file test_protocol.cpp
 * @brief 协议测试
 */

#include "streaming/protocol/rtmp_server.hpp"
#include "streaming/protocol/hls_server.hpp"
#include "streaming/monitor/logger.hpp"

#include <iostream>
#include <cassert>

using namespace streaming;

// 测试 AMF 编解码
void test_amf_codec() {
    std::cout << "Testing AMF codec..." << std::endl;

    // 测试编码
    auto number = AmfCodec::encodeNumber(3.14);
    assert(number[0] == static_cast<uint8_t>(AmfType::Number));

    auto boolean = AmfCodec::encodeBoolean(true);
    assert(boolean[0] == static_cast<uint8_t>(AmfType::Boolean));
    assert(boolean[1] == 1);

    auto string = AmfCodec::encodeString("hello");
    assert(string[0] == static_cast<uint8_t>(AmfType::String));

    auto null = AmfCodec::encodeNull();
    assert(null[0] == static_cast<uint8_t>(AmfType::Null));

    std::cout << "  AMF codec tests passed!" << std::endl;
}

// 测试 M3U8 生成
void test_m3u8_generator() {
    std::cout << "Testing M3U8 generator..." << std::endl;

    HlsPlaylist playlist;
    playlist.type = HlsPlaylistType::Live;
    playlist.version = 3;
    playlist.target_duration = 6;
    playlist.media_sequence = 0;

    auto segment1 = std::make_shared<HlsSegment>();
    segment1->sequence_number = 0;
    segment1->filename = "segment_0.ts";
    segment1->duration = 6.0;
    playlist.segments.push_back(segment1);

    auto segment2 = std::make_shared<HlsSegment>();
    segment2->sequence_number = 1;
    segment2->filename = "segment_1.ts";
    segment2->duration = 5.5;
    playlist.segments.push_back(segment2);

    std::string m3u8 = M3u8Generator::generate_media_playlist(playlist);

    assert(m3u8.find("#EXTM3U") != std::string::npos);
    assert(m3u8.find("#EXT-X-VERSION:3") != std::string::npos);
    assert(m3u8.find("#EXT-X-TARGETDURATION:6") != std::string::npos);
    assert(m3u8.find("segment_0.ts") != std::string::npos);
    assert(m3u8.find("segment_1.ts") != std::string::npos);

    std::cout << "  M3U8 generator tests passed!" << std::endl;
}

// 测试 STUN 消息
void test_stun_message() {
    std::cout << "Testing STUN message..." << std::endl;

    StunMessage msg;
    msg.set_type(StunMessageType::BindingRequest);

    // 创建事务ID
    Buffer transaction_id(12, 0);
    for (int i = 0; i < 12; ++i) {
        transaction_id[i] = static_cast<uint8_t>(i);
    }
    msg.set_transaction_id(transaction_id);

    // 序列化
    auto data = msg.serialize();
    assert(data.size() >= 20);

    // 验证魔术字
    assert(data[4] == 0x21);
    assert(data[5] == 0x12);
    assert(data[6] == 0xA4);
    assert(data[7] == 0x42);

    std::cout << "  STUN message tests passed!" << std::endl;
}

// 测试 TS 封装器
void test_ts_muxer() {
    std::cout << "Testing TS muxer..." << std::endl;

    TsMuxer muxer;

    MediaParams params;
    params.video.codec = VideoCodec::H264;
    params.audio.codec = AudioCodec::AAC;

    assert(muxer.initialize(params));

    // 获取 PAT/PMT
    auto pat = muxer.get_pat();
    assert(pat.size() == 188);
    assert(pat[0] == 0x47);  // 同步字节

    auto pmt = muxer.get_pmt();
    assert(pmt.size() == 188);
    assert(pmt[0] == 0x47);

    muxer.close();

    std::cout << "  TS muxer tests passed!" << std::endl;
}

// 测试会话管理器
void test_session_manager() {
    std::cout << "Testing SessionManager..." << std::endl;

    SessionManager manager;
    manager.initialize(100, std::chrono::seconds(300));

    // 创建会话
    auto session1 = manager.create_session(SessionType::Publisher, ProtocolType::RTMP);
    assert(session1 != nullptr);
    assert(manager.get_session_count() == 1);

    auto session2 = manager.create_session(SessionType::Subscriber, ProtocolType::HLS);
    assert(session2 != nullptr);
    assert(manager.get_session_count() == 2);

    // 获取会话
    auto retrieved = manager.get_session(session1->get_id());
    assert(retrieved == session1);

    // 移除会话
    manager.remove_session(session1->get_id());
    assert(manager.get_session_count() == 1);

    manager.close_all_sessions();
    assert(manager.get_session_count() == 0);

    std::cout << "  SessionManager tests passed!" << std::endl;
}

int main() {
    LogManager::instance().initialize(LogLevel::Error, "", false);

    std::cout << "Running protocol tests..." << std::endl;

    test_amf_codec();
    test_m3u8_generator();
    test_stun_message();
    test_ts_muxer();
    test_session_manager();

    std::cout << "\nAll protocol tests passed!" << std::endl;
    return 0;
}
