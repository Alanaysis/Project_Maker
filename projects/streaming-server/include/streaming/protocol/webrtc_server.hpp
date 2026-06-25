#pragma once

/**
 * @file webrtc_server.hpp
 * @brief WebRTC 协议服务器
 *
 * 实现 WebRTC (Web Real-Time Communication) 服务器，支持：
 * - 信令服务器
 * - ICE/STUN/TURN
 * - SDP 协商
 * - SRTP 加密
 * - 拥塞控制
 */

#include "streaming/types.hpp"
#include <string>
#include <memory>
#include <vector>
#include <functional>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>

namespace streaming {

// WebRTC 信令消息类型
enum class SignalingMessageType {
    Offer,
    Answer,
    IceCandidate,
    Bye,
    Unknown
};

// ICE 候选类型
enum class IceCandidateType {
    Host,
    Srflx,      // Server Reflexive
    Relay,      // TURN Relay
    Unknown
};

// DTLS 状态
enum class DtlsState {
    New,
    Connecting,
    Connected,
    Failed,
    Closed
};

// SRTP 加密套件
enum class SrtpProfile {
    AES128_CM_SHA1_80,
    AES128_CM_SHA1_32,
    AEAD_AES128_GCM,
    AEAD_AES256_GCM
};

// 信令消息
struct SignalingMessage {
    SignalingMessageType type = SignalingMessageType::Unknown;
    std::string from;
    std::string to;
    std::string room;
    std::string sdp;
    std::string candidate;
    std::string sdp_mid;
    int sdp_mline_index = 0;
};

// ICE 候选
struct IceCandidate {
    IceCandidateType type = IceCandidateType::Unknown;
    std::string foundation;
    uint32_t component = 0;
    std::string protocol;       // udp or tcp
    uint32_t priority = 0;
    std::string address;
    uint16_t port = 0;
    std::string type_str;
};

// SDP 信息
struct SdpInfo {
    std::string raw_sdp;
    std::string session_id;
    std::string session_version;
    std::string media_section;

    // 视频信息
    std::vector<std::string> video_codecs;
    std::string video_ssrc;
    std::string video_mid;

    // 音频信息
    std::vector<std::string> audio_codecs;
    std::string audio_ssrc;
    std::string audio_mid;

    // ICE 信息
    std::string ice_ufrag;
    std::string ice_pwd;
    std::vector<IceCandidate> candidates;

    // DTLS 信息
    std::string fingerprint;
    std::string fingerprint_algorithm;
    std::string setup;          // actpass, active, passive
};

/**
 * @brief SDP 解析器
 */
class SdpParser {
public:
    /**
     * @brief 解析 SDP
     * @param sdp_string SDP 字符串
     * @return SDP 信息
     */
    static SdpInfo parse(const std::string& sdp_string);

    /**
     * @brief 生成 SDP
     * @param info SDP 信息
     * @return SDP 字符串
     */
    static std::string generate(const SdpInfo& info);

private:
    static void parse_session_level(SdpInfo& info, const std::string& line);
    static void parse_media_level(SdpInfo& info, const std::string& line);
    static void parse_attribute(SdpInfo& info, const std::string& line);
    static IceCandidate parse_candidate(const std::string& candidate_str);
};

/**
 * @brief STUN 消息类型
 */
enum class StunMessageType : uint16_t {
    BindingRequest = 0x0001,
    BindingResponse = 0x0101,
    BindingErrorResponse = 0x0111,
    SharedSecretRequest = 0x0002,
    SharedSecretResponse = 0x0102,
    SharedSecretErrorResponse = 0x0112
};

// STUN 属性类型
enum class StunAttributeType : uint16_t {
    MappedAddress = 0x0001,
    ResponseAddress = 0x0002,
    ChangeRequest = 0x0003,
    SourceAddress = 0x0004,
    ChangedAddress = 0x0005,
    Username = 0x0006,
    Password = 0x0007,
    MessageIntegrity = 0x0008,
    ErrorCode = 0x0009,
    UnknownAttributes = 0x000A,
    ReflectedFrom = 0x000B,
    XorMappedAddress = 0x0020,
    Priority = 0x0024,
    UseCandidate = 0x0025,
    IceControlling = 0x802A,
    IceControlled = 0x8029
};

/**
 * @brief STUN 消息处理
 */
class StunMessage {
public:
    StunMessage();
    ~StunMessage();

    // 解析
    bool parse(const Buffer& data);

    // 生成
    Buffer serialize() const;

    // 属性操作
    void set_type(StunMessageType type) { type_ = type; }
    StunMessageType get_type() const { return type_; }

    void set_transaction_id(const Buffer& id) { transaction_id_ = id; }
    const Buffer& get_transaction_id() const { return transaction_id_; }

    void add_attribute(StunAttributeType attr_type, const Buffer& value);
    Buffer get_attribute(StunAttributeType attr_type) const;

    // 验证
    bool validate(const std::string& password) const;

private:
    StunMessageType type_ = StunMessageType::BindingRequest;
    Buffer transaction_id_;
    std::unordered_map<uint16_t, Buffer> attributes_;
};

/**
 * @brief DTLS 握手处理
 */
class DtlsHandler {
public:
    DtlsHandler();
    ~DtlsHandler();

    // 初始化
    bool initialize(const std::string& cert_file, const std::string& key_file);

    // 握手
    bool start_handshake();
    bool process_handshake_message(const Buffer& data);
    Buffer get_handshake_message();

    // 数据传输
    Buffer encrypt(const Buffer& data);
    Buffer decrypt(const Buffer& data);

    // 状态
    DtlsState get_state() const { return state_; }
    std::string get_fingerprint() const;

private:
    DtlsState state_ = DtlsState::New;
    // SSL* ssl_ = nullptr;  // OpenSSL SSL 对象
    Buffer pending_data_;
};

/**
 * @brief WebRTC 对等连接
 */
class PeerConnection {
public:
    PeerConnection(uint64_t session_id);
    ~PeerConnection();

    // SDP 处理
    bool set_remote_description(const SdpInfo& sdp);
    SdpInfo create_offer();
    bool set_local_description(const SdpInfo& sdp);

    // ICE 处理
    void add_ice_candidate(const IceCandidate& candidate);
    std::vector<IceCandidate> get_local_candidates() const;

    // 媒体传输
    void send_video_frame(const MediaFrame& frame);
    void send_audio_frame(const MediaFrame& frame);

    // 回调
    void set_on_frame(FrameCallback callback) { frame_callback_ = std::move(callback); }
    void set_on_ice_candidate(std::function<void(IceCandidate)> callback) {
        ice_candidate_callback_ = std::move(callback);
    }

    // 状态
    bool is_connected() const { return connected_; }
    uint64_t get_session_id() const { return session_id_; }

private:
    void setup_dtls();
    void setup_srtp();
    void handle_rtp_packet(const Buffer& data);
    void handle_rtcp_packet(const Buffer& data);

    uint64_t session_id_;
    bool connected_ = false;

    SdpInfo local_sdp_;
    SdpInfo remote_sdp_;
    std::vector<IceCandidate> local_candidates_;
    std::vector<IceCandidate> remote_candidates_;

    std::unique_ptr<DtlsHandler> dtls_handler_;
    // SRTP 相关
    uint32_t local_ssrc_ = 0;
    uint32_t remote_ssrc_ = 0;

    FrameCallback frame_callback_;
    std::function<void(IceCandidate)> ice_candidate_callback_;
};

/**
 * @brief WebRTC 房间
 */
class WebRtcRoom {
public:
    WebRtcRoom(const std::string& room_id);
    ~WebRtcRoom();

    // 房间管理
    void add_peer(uint64_t session_id, std::shared_ptr<PeerConnection> peer);
    void remove_peer(uint64_t session_id);

    // 信令
    void handle_signaling_message(const SignalingMessage& msg);

    // 媒体转发
    void forward_video(uint64_t from_session, const MediaFrame& frame);
    void forward_audio(uint64_t from_session, const MediaFrame& frame);

    // 状态
    std::string get_room_id() const { return room_id_; }
    uint32_t get_peer_count() const;
    std::vector<uint64_t> get_peer_ids() const;

private:
    std::string room_id_;
    std::unordered_map<uint64_t, std::shared_ptr<PeerConnection>> peers_;
    mutable std::mutex mutex_;
};

/**
 * @brief WebRTC 服务器
 */
class WebRtcServer {
public:
    WebRtcServer();
    ~WebRtcServer();

    // 服务器控制
    bool start(const std::string& host, uint16_t port);
    void stop();
    bool is_running() const { return running_; }

    // 信令处理
    void handle_signaling_message(const SignalingMessage& msg);

    // 房间管理
    std::shared_ptr<WebRtcRoom> get_or_create_room(const std::string& room_id);

    // 回调
    void set_frame_callback(FrameCallback callback) { frame_callback_ = std::move(callback); }

private:
    void signaling_loop();
    void handle_websocket_connection(int client_fd);
    void process_signaling_message(const std::string& raw_message);

    std::string host_;
    uint16_t port_ = 8443;
    int listen_fd_ = -1;
    std::atomic<bool> running_{false};

    std::thread signaling_thread_;
    std::unordered_map<std::string, std::shared_ptr<WebRtcRoom>> rooms_;
    std::unordered_map<uint64_t, std::shared_ptr<PeerConnection>> connections_;
    mutable std::mutex mutex_;

    FrameCallback frame_callback_;
    uint64_t next_session_id_ = 1;
};

} // namespace streaming
