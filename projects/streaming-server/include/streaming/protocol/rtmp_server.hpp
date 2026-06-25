#pragma once

/**
 * @file rtmp_server.hpp
 * @brief RTMP 协议服务器
 *
 * 实现 RTMP (Real-Time Messaging Protocol) 服务器，支持：
 * - RTMP 推流 (Publish)
 * - RTMP 拉流 (Play)
 * - AMF 编解码
 * - 握手协议
 * - 消息分块
 */

#include "streaming/types.hpp"
#include <string>
#include <memory>
#include <functional>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>

namespace streaming {

// RTMP 消息类型
enum class RtmpMessageType : uint8_t {
    SetChunkSize = 1,
    Abort = 2,
    Acknowledgement = 3,
    UserControl = 4,
    WindowAckSize = 5,
    SetPeerBandwidth = 6,
    Audio = 8,
    Video = 9,
    DataAmf3 = 15,
    CommandAmf3 = 17,
    DataAmf0 = 18,
    CommandAmf0 = 20,
    Aggregate = 22
};

// RTMP 命令类型
enum class RtmpCommand {
    Connect,
    CreateStream,
    Publish,
    Play,
    DeleteStream,
    CloseStream,
    ReleaseStream,
    FCPublish,
    FCUnpublish,
    Unknown
};

// RTMP 状态
enum class RtmpState {
    Uninitialized,
    VersionSent,
    AckSent,
    HandshakeDone,
    Connected,
    Created,
    Publishing,
    Playing
};

// RTMP 块头
struct RtmpChunkHeader {
    uint8_t fmt = 0;
    uint32_t cs_id = 0;
    uint32_t timestamp = 0;
    uint32_t msg_length = 0;
    uint8_t msg_type_id = 0;
    uint32_t msg_stream_id = 0;
};

// RTMP 消息
struct RtmpMessage {
    RtmpMessageType type;
    uint32_t stream_id = 0;
    Buffer payload;
    Timestamp received_time;
};

// AMF 值类型
enum class AmfType : uint8_t {
    Number = 0x00,
    Boolean = 0x01,
    String = 0x02,
    Object = 0x03,
    Null = 0x05,
    EcmaArray = 0x08,
    ObjectEnd = 0x09
};

// AMF 值
struct AmfValue {
    AmfType type;
    double number_val = 0.0;
    bool bool_val = false;
    std::string string_val;
    std::unordered_map<std::string, AmfValue> object_val;
};

/**
 * @brief AMF 编解码器
 */
class AmfCodec {
public:
    // 编码
    static Buffer encodeNumber(double value);
    static Buffer encodeBoolean(bool value);
    static Buffer encodeString(const std::string& value);
    static Buffer encodeNull();
    static Buffer encodeObject(const std::unordered_map<std::string, AmfValue>& obj);

    // 解码
    static AmfValue decode(const Buffer& data, size_t& offset);

private:
    static AmfValue decodeNumber(const Buffer& data, size_t& offset);
    static AmfValue decodeBoolean(const Buffer& data, size_t& offset);
    static AmfValue decodeString(const Buffer& data, size_t& offset);
    static AmfValue decodeObject(const Buffer& data, size_t& offset);
};

/**
 * @brief RTMP 会话
 */
class RtmpSession {
public:
    RtmpSession(uint64_t session_id, int socket_fd);
    ~RtmpSession();

    // 会话控制
    void start();
    void stop();
    bool is_active() const { return active_; }

    // 数据处理
    void on_data_received(const Buffer& data);
    void send_message(const RtmpMessage& msg);

    // 回调设置
    void set_frame_callback(FrameCallback callback) { frame_callback_ = std::move(callback); }
    void set_close_callback(std::function<void()> callback) { close_callback_ = std::move(callback); }

    // 状态查询
    uint64_t get_session_id() const { return session_id_; }
    RtmpState get_state() const { return state_; }
    const std::string& get_stream_name() const { return stream_name_; }
    const std::string& get_app_name() const { return app_name_; }
    bool is_publisher() const { return is_publisher_; }

private:
    // 握手处理
    void handle_handshake(const Buffer& data);
    void send_handshake_c0c1();
    void send_handshake_s0s1s2(const Buffer& c1);
    void send_handshake_c2(const Buffer& s1);

    // 消息处理
    void handle_chunk(const Buffer& data, size_t& offset);
    void handle_message(const RtmpMessage& msg);
    void handle_command(const RtmpMessage& msg);
    void handle_audio(const RtmpMessage& msg);
    void handle_video(const RtmpMessage& msg);

    // 命令处理
    void handle_connect(const std::vector<AmfValue>& params);
    void handle_create_stream(const std::vector<AmfValue>& params);
    void handle_publish(const std::vector<AmfValue>& params);
    void handle_play(const std::vector<AmfValue>& params);
    void handle_delete_stream(const std::vector<AmfValue>& params);

    // 发送响应
    void send_connect_result();
    void send_create_stream_result(double transaction_id);
    void send_publish_start();
    void send_play_start();
    void send_stream_eof();
    void send_on_status(const std::string& level, const std::string& code, const std::string& description);

    // 块处理
    void send_chunk(const RtmpChunkHeader& header, const Buffer& payload);
    void set_chunk_size(uint32_t size);

    // 成员变量
    uint64_t session_id_;
    int socket_fd_;
    std::atomic<bool> active_{false};
    RtmpState state_ = RtmpState::Uninitialized;

    std::string app_name_;
    std::string stream_name_;
    bool is_publisher_ = false;

    uint32_t in_chunk_size_ = 128;
    uint32_t out_chunk_size_ = 128;
    uint32_t window_ack_size_ = 2500000;
    uint64_t sequence_number_ = 0;

    Buffer recv_buffer_;
    std::unordered_map<uint32_t, RtmpChunkHeader> chunk_headers_;
    std::unordered_map<uint32_t, Buffer> chunk_buffers_;

    FrameCallback frame_callback_;
    std::function<void()> close_callback_;

    std::mutex send_mutex_;
};

/**
 * @brief RTMP 服务器
 */
class RtmpServer {
public:
    RtmpServer();
    ~RtmpServer();

    // 服务器控制
    bool start(const std::string& host, uint16_t port);
    void stop();
    bool is_running() const { return running_; }

    // 会话管理
    void set_connection_callback(ConnectionCallback callback) { connection_callback_ = std::move(callback); }
    void set_frame_callback(FrameCallback callback) { frame_callback_ = std::move(callback); }

    // 统计
    uint32_t get_session_count() const;
    std::vector<uint64_t> get_session_ids() const;

private:
    void accept_loop();
    void handle_accept(int client_fd, const std::string& client_addr);
    void remove_session(uint64_t session_id);

    std::string host_;
    uint16_t port_ = 1935;
    int listen_fd_ = -1;
    std::atomic<bool> running_{false};

    std::thread accept_thread_;
    std::unordered_map<uint64_t, std::shared_ptr<RtmpSession>> sessions_;
    mutable std::mutex sessions_mutex_;

    ConnectionCallback connection_callback_;
    FrameCallback frame_callback_;

    uint64_t next_session_id_ = 1;
};

} // namespace streaming
