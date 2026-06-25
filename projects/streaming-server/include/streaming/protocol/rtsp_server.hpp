#pragma once

/**
 * @file rtsp_server.hpp
 * @brief RTSP 协议服务器
 *
 * 实现 RTSP (Real-Time Streaming Protocol) 服务器，支持：
 * - RTSP 请求/响应处理
 * - RTP/RTCP 传输
 * - SDP 协商
 * - 会话管理
 * - TCP/UDP 传输
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

// RTSP 方法
enum class RtspMethod {
    OPTIONS,
    DESCRIBE,
    SETUP,
    PLAY,
    PAUSE,
    TEARDOWN,
    ANNOUNCE,
    RECORD,
    GET_PARAMETER,
    SET_PARAMETER,
    REDIRECT,
    UNKNOWN
};

// RTSP 状态码
enum class RtspStatusCode {
    OK = 200,
    MovedPermanently = 301,
    BadRequest = 400,
    Unauthorized = 401,
    NotFound = 404,
    MethodNotAllowed = 405,
    SessionNotFound = 454,
    UnsupportedTransport = 461,
    InternalError = 500,
    NotImplemented = 501,
    ServiceUnavailable = 503
};

// 传输模式
enum class TransportMode {
    TCP,
    UDP
};

// RTSP 请求
struct RtspRequest {
    RtspMethod method = RtspMethod::UNKNOWN;
    std::string uri;
    std::string version = "RTSP/1.0";
    std::unordered_map<std::string, std::string> headers;
    std::string body;
    uint32_t cseq = 0;
    std::string session_id;
};

// RTSP 响应
struct RtspResponse {
    RtspStatusCode status_code = RtspStatusCode::OK;
    std::string status_text;
    std::string version = "RTSP/1.0";
    std::unordered_map<std::string, std::string> headers;
    std::string body;
    uint32_t cseq = 0;
};

// RTP 包头
struct RtpHeader {
    uint8_t version = 2;
    bool padding = false;
    bool extension = false;
    uint8_t csrc_count = 0;
    bool marker = false;
    uint8_t payload_type = 0;
    uint16_t sequence_number = 0;
    uint32_t timestamp = 0;
    uint32_t ssrc = 0;
};

// RTP 包
struct RtpPacket {
    RtpHeader header;
    Buffer payload;
};

// RTCP 类型
enum class RtcpType : uint8_t {
    SR = 200,       // Sender Report
    RR = 201,       // Receiver Report
    SDES = 202,     // Source Description
    BYE = 203,      // Goodbye
    APP = 204       // Application-defined
};

// RTCP 包
struct RtcpPacket {
    RtcpType type;
    Buffer payload;
};

/**
 * @brief SDP 生成器
 */
class SdpGenerator {
public:
    /**
     * @brief 生成 SDP 描述
     * @param params 媒体参数
     * @param server_ip 服务器IP
     * @param video_port 视频RTP端口
     * @param audio_port 音频RTP端口
     * @return SDP 字符串
     */
    static std::string generate(const MediaParams& params,
                                const std::string& server_ip,
                                uint16_t video_port,
                                uint16_t audio_port);

private:
    static std::string get_video_codec_name(VideoCodec codec);
    static std::string get_audio_codec_name(AudioCodec codec);
    static std::string get_video_fmtp(VideoCodec codec);
    static std::string get_audio_fmtp(AudioCodec codec);
};

/**
 * @brief RTP 打包器
 */
class RtpPacketizer {
public:
    RtpPacketizer(uint8_t payload_type, uint32_t ssrc);

    // 打包媒体帧为 RTP 包
    std::vector<RtpPacket> packetize(const MediaFrame& frame);

    // 设置参数
    void set_payload_type(uint8_t pt) { payload_type_ = pt; }
    void set_mtu(uint16_t mtu) { mtu_ = mtu; }

private:
    std::vector<RtpPacket> packetize_h264(const Buffer& data, uint32_t timestamp, bool marker);
    std::vector<RtpPacket> packetize_aac(const Buffer& data, uint32_t timestamp);

    uint8_t payload_type_ = 0;
    uint32_t ssrc_ = 0;
    uint16_t sequence_number_ = 0;
    uint16_t mtu_ = 1400;
};

/**
 * @brief RTP 解包器
 */
class RtpDepacketizer {
public:
    // 解包 RTP 包为媒体帧
    MediaFramePtr depacketize(const RtpPacket& packet);

private:
    MediaFramePtr depacketize_h264(const RtpPacket& packet);
    MediaFramePtr depacketize_aac(const RtpPacket& packet);

    Buffer fragmented_buffer_;
    uint8_t payload_type_ = 0;
};

/**
 * @brief RTSP 会话
 */
class RtspSession {
public:
    RtspSession(uint64_t session_id, int socket_fd);
    ~RtspSession();

    // 会话控制
    void start();
    void stop();
    bool is_active() const { return active_; }

    // 数据处理
    void on_data_received(const Buffer& data);
    void send_response(const RtspResponse& response);

    // RTP 传输
    void send_rtp_packet(const RtpPacket& packet);
    void send_rtcp_packet(const RtcpPacket& packet);

    // 回调设置
    void set_frame_callback(FrameCallback callback) { frame_callback_ = std::move(callback); }
    void set_close_callback(std::function<void()> callback) { close_callback_ = std::move(callback); }

    // 状态查询
    uint64_t get_session_id() const { return session_id_; }
    const std::string& get_stream_name() const { return stream_name_; }
    TransportMode get_transport_mode() const { return transport_mode_; }

private:
    // 请求处理
    void handle_request(const RtspRequest& request);
    RtspMethod parse_method(const std::string& method_str);
    RtspRequest parse_request(const std::string& data);

    // 方法处理
    void handle_options(const RtspRequest& request);
    void handle_describe(const RtspRequest& request);
    void handle_setup(const RtspRequest& request);
    void handle_play(const RtspRequest& request);
    void handle_pause(const RtspRequest& request);
    void handle_teardown(const RtspRequest& request);
    void handle_announce(const RtspRequest& request);
    void handle_record(const RtspRequest& request);

    // 传输设置
    void setup_udp_transport(const std::string& transport_header);
    void setup_tcp_transport(const std::string& transport_header);

    // RTP/RTCP 处理
    void start_rtp_send();
    void stop_rtp_send();
    void send_rtp_loop();

    // 成员变量
    uint64_t session_id_;
    int socket_fd_;
    int rtp_socket_ = -1;
    int rtcp_socket_ = -1;
    std::atomic<bool> active_{false};

    std::string stream_name_;
    std::string client_ip_;
    uint16_t client_rtp_port_ = 0;
    uint16_t client_rtcp_port_ = 0;
    uint16_t server_rtp_port_ = 0;
    uint16_t server_rtcp_port_ = 0;

    TransportMode transport_mode_ = TransportMode::UDP;
    bool is_publisher_ = false;
    uint32_t ssrc_ = 0;

    Buffer recv_buffer_;
    std::unique_ptr<RtpPacketizer> video_packetizer_;
    std::unique_ptr<RtpPacketizer> audio_packetizer_;
    std::unique_ptr<RtpDepacketizer> depacketizer_;

    FrameCallback frame_callback_;
    std::function<void()> close_callback_;

    std::thread rtp_thread_;
    std::atomic<bool> rtp_running_{false};
    std::mutex send_mutex_;
};

/**
 * @brief RTSP 服务器
 */
class RtspServer {
public:
    RtspServer();
    ~RtspServer();

    // 服务器控制
    bool start(const std::string& host, uint16_t port);
    void stop();
    bool is_running() const { return running_; }

    // 会话管理
    void set_connection_callback(ConnectionCallback callback) { connection_callback_ = std::move(callback); }
    void set_frame_callback(FrameCallback callback) { frame_callback_ = std::move(callback); }

    // 统计
    uint32_t get_session_count() const;

private:
    void accept_loop();
    void handle_accept(int client_fd, const std::string& client_addr);
    void remove_session(uint64_t session_id);

    std::string host_;
    uint16_t port_ = 554;
    int listen_fd_ = -1;
    std::atomic<bool> running_{false};

    std::thread accept_thread_;
    std::unordered_map<uint64_t, std::shared_ptr<RtspSession>> sessions_;
    mutable std::mutex sessions_mutex_;

    ConnectionCallback connection_callback_;
    FrameCallback frame_callback_;

    uint64_t next_session_id_ = 1;
};

} // namespace streaming
