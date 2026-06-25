/**
 * @file webrtc_server.cpp
 * @brief WebRTC 服务器实现
 */

#include "streaming/protocol/webrtc_server.hpp"
#include "streaming/monitor/logger.hpp"

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <sstream>

namespace streaming {

// ============================================================================
// SDP 解析器实现
// ============================================================================

SdpInfo SdpParser::parse(const std::string& sdp_string) {
    SdpInfo info;
    info.raw_sdp = sdp_string;

    std::istringstream iss(sdp_string);
    std::string line;

    while (std::getline(iss, line)) {
        // 移除回车符
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        if (line.empty()) continue;

        if (line.substr(0, 2) == "v=") {
            // 版本行，跳过
        } else if (line.substr(0, 2) == "o=") {
            parse_session_level(info, line);
        } else if (line.substr(0, 2) == "m=") {
            parse_media_level(info, line);
        } else if (line.substr(0, 2) == "a=") {
            parse_attribute(info, line);
        }
    }

    return info;
}

void SdpParser::parse_session_level(SdpInfo& info, const std::string& line) {
    // o=<username> <sess-id> <sess-version> <nettype> <addrtype> <unicast-address>
    // 简化解析
}

void SdpParser::parse_media_level(SdpInfo& info, const std::string& line) {
    info.media_section = line;
}

void SdpParser::parse_attribute(SdpInfo& info, const std::string& line) {
    std::string attr = line.substr(2);

    if (attr.substr(0, 10) == "ice-ufrag:") {
        info.ice_ufrag = attr.substr(10);
    } else if (attr.substr(0, 8) == "ice-pwd:") {
        info.ice_pwd = attr.substr(8);
    } else if (attr.substr(0, 19) == "fingerprint:sha-256") {
        info.fingerprint_algorithm = "sha-256";
        info.fingerprint = attr.substr(20);
    } else if (attr.substr(0, 6) == "setup:") {
        info.setup = attr.substr(6);
    } else if (attr.substr(0, 11) == "candidate:") {
        IceCandidate candidate = parse_candidate(attr.substr(11));
        info.candidates.push_back(candidate);
    } else if (attr.substr(0, 4) == "mid:") {
        std::string mid = attr.substr(4);
        if (info.video_mid.empty()) {
            info.video_mid = mid;
        } else {
            info.audio_mid = mid;
        }
    }
}

IceCandidate SdpParser::parse_candidate(const std::string& candidate_str) {
    IceCandidate candidate;

    // candidate:<foundation> <component> <protocol> <priority> <address> <port> typ <type>
    std::istringstream iss(candidate_str);
    iss >> candidate.foundation >> candidate.component >> candidate.protocol
        >> candidate.priority >> candidate.address >> candidate.port;

    std::string typ;
    iss >> typ >> candidate.type_str;

    if (candidate.type_str == "host") {
        candidate.type = IceCandidateType::Host;
    } else if (candidate.type_str == "srflx") {
        candidate.type = IceCandidateType::Srflx;
    } else if (candidate.type_str == "relay") {
        candidate.type = IceCandidateType::Relay;
    }

    return candidate;
}

std::string SdpParser::generate(const SdpInfo& info) {
    std::ostringstream sdp;

    sdp << "v=0\r\n";
    sdp << "o=- " << info.session_id << " " << info.session_version << " IN IP4 0.0.0.0\r\n";
    sdp << "s=-\r\n";
    sdp << "t=0 0\r\n";

    // ICE 凭证
    if (!info.ice_ufrag.empty()) {
        sdp << "a=ice-ufrag:" << info.ice_ufrag << "\r\n";
    }
    if (!info.ice_pwd.empty()) {
        sdp << "a=ice-pwd:" << info.ice_pwd << "\r\n";
    }

    // 指纹
    if (!info.fingerprint.empty()) {
        sdp << "a=fingerprint:" << info.fingerprint_algorithm << " " << info.fingerprint << "\r\n";
    }

    // 媒体部分
    if (!info.media_section.empty()) {
        sdp << info.media_section << "\r\n";
    }

    return sdp.str();
}

// ============================================================================
// STUN 消息实现
// ============================================================================

StunMessage::StunMessage() = default;
StunMessage::~StunMessage() = default;

bool StunMessage::parse(const Buffer& data) {
    if (data.size() < 20) return false;

    type_ = static_cast<StunMessageType>((data[0] << 8) | data[1]);
    uint16_t length = (data[2] << 8) | data[3];

    if (data.size() < 20 + length) return false;

    // 魔术字
    if (data[4] != 0x21 || data[5] != 0x12 || data[6] != 0xA4 || data[7] != 0x42) {
        return false;
    }

    // 事务ID
    transaction_id_ = Buffer(data.begin() + 8, data.begin() + 20);

    // 解析属性
    size_t offset = 20;
    while (offset + 4 <= 20 + length) {
        uint16_t attr_type = (data[offset] << 8) | data[offset + 1];
        uint16_t attr_length = (data[offset + 2] << 8) | data[offset + 3];
        offset += 4;

        if (offset + attr_length > 20 + length) break;

        Buffer attr_value(data.begin() + offset, data.begin() + offset + attr_length);
        attributes_[attr_type] = attr_value;

        // 对齐到4字节
        offset += (attr_length + 3) & ~3;
    }

    return true;
}

Buffer StunMessage::serialize() const {
    Buffer data;

    // 消息类型
    data.push_back((static_cast<uint16_t>(type_) >> 8) & 0xFF);
    data.push_back(static_cast<uint16_t>(type_) & 0xFF);

    // 长度（占位）
    size_t length_pos = data.size();
    data.push_back(0);
    data.push_back(0);

    // 魔术字
    data.push_back(0x21);
    data.push_back(0x12);
    data.push_back(0xA4);
    data.push_back(0x42);

    // 事务ID
    data.insert(data.end(), transaction_id_.begin(), transaction_id_.end());

    // 属性
    for (const auto& [attr_type, attr_value] : attributes_) {
        data.push_back((attr_type >> 8) & 0xFF);
        data.push_back(attr_type & 0xFF);
        data.push_back((attr_value.size() >> 8) & 0xFF);
        data.push_back(attr_value.size() & 0xFF);
        data.insert(data.end(), attr_value.begin(), attr_value.end());

        // 对齐到4字节
        size_t padding = (4 - (attr_value.size() % 4)) % 4;
        for (size_t i = 0; i < padding; ++i) {
            data.push_back(0);
        }
    }

    // 更新长度
    uint16_t length = static_cast<uint16_t>(data.size() - 20);
    data[length_pos] = (length >> 8) & 0xFF;
    data[length_pos + 1] = length & 0xFF;

    return data;
}

void StunMessage::add_attribute(StunAttributeType attr_type, const Buffer& value) {
    attributes_[static_cast<uint16_t>(attr_type)] = value;
}

Buffer StunMessage::get_attribute(StunAttributeType attr_type) const {
    auto it = attributes_.find(static_cast<uint16_t>(attr_type));
    if (it != attributes_.end()) {
        return it->second;
    }
    return {};
}

bool StunMessage::validate(const std::string& password) const {
    // 简化实现
    return true;
}

// ============================================================================
// WebRTC 服务器实现
// ============================================================================

WebRtcServer::WebRtcServer() = default;
WebRtcServer::~WebRtcServer() { stop(); }

bool WebRtcServer::start(const std::string& host, uint16_t port) {
    host_ = host;
    port_ = port;

    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        LOG_ERROR("Failed to create WebRTC socket");
        return false;
    }

    int opt = 1;
    setsockopt(listen_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(listen_fd_, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        LOG_ERROR("Failed to bind WebRTC socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    if (listen(listen_fd_, 128) < 0) {
        LOG_ERROR("Failed to listen on WebRTC socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    running_ = true;
    signaling_thread_ = std::thread(&WebRtcServer::signaling_loop, this);

    LOG_INFO("WebRTC server started on " + host + ":" + std::to_string(port));
    return true;
}

void WebRtcServer::stop() {
    running_ = false;

    if (listen_fd_ >= 0) {
        ::close(listen_fd_);
        listen_fd_ = -1;
    }

    if (signaling_thread_.joinable()) {
        signaling_thread_.join();
    }

    std::lock_guard<std::mutex> lock(mutex_);
    rooms_.clear();
    connections_.clear();

    LOG_INFO("WebRTC server stopped");
}

void WebRtcServer::handle_signaling_message(const SignalingMessage& msg) {
    std::lock_guard<std::mutex> lock(mutex_);

    switch (msg.type) {
        case SignalingMessageType::Offer: {
            // 创建或获取房间
            auto room = get_or_create_room(msg.room);

            // 创建对等连接
            auto pc = std::make_shared<PeerConnection>(next_session_id_++);
            SdpInfo remote_sdp = SdpParser::parse(msg.sdp);
            pc->set_remote_description(remote_sdp);

            connections_[pc->get_session_id()] = pc;
            room->add_peer(pc->get_session_id(), pc);

            break;
        }

        case SignalingMessageType::Answer: {
            // 处理应答
            break;
        }

        case SignalingMessageType::IceCandidate: {
            // 处理 ICE 候选
            break;
        }

        case SignalingMessageType::Bye: {
            // 处理离开
            break;
        }

        default:
            break;
    }
}

std::shared_ptr<WebRtcRoom> WebRtcServer::get_or_create_room(const std::string& room_id) {
    auto it = rooms_.find(room_id);
    if (it != rooms_.end()) {
        return it->second;
    }

    auto room = std::make_shared<WebRtcRoom>(room_id);
    rooms_[room_id] = room;
    return room;
}

void WebRtcServer::signaling_loop() {
    while (running_) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept(listen_fd_, (struct sockaddr*)&client_addr, &addr_len);
        if (client_fd < 0) {
            if (running_) {
                LOG_ERROR("Failed to accept WebRTC connection");
            }
            continue;
        }

        handle_websocket_connection(client_fd);
        ::close(client_fd);
    }
}

void WebRtcServer::handle_websocket_connection(int client_fd) {
    // 简化的 WebSocket 处理
    char buffer[4096];
    ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
    if (n > 0) {
        buffer[n] = '\0';
        process_signaling_message(std::string(buffer, n));
    }
}

void WebRtcServer::process_signaling_message(const std::string& raw_message) {
    // 简化的 JSON 解析
    SignalingMessage msg;

    if (raw_message.find("\"offer\"") != std::string::npos) {
        msg.type = SignalingMessageType::Offer;
    } else if (raw_message.find("\"answer\"") != std::string::npos) {
        msg.type = SignalingMessageType::Answer;
    } else if (raw_message.find("\"candidate\"") != std::string::npos) {
        msg.type = SignalingMessageType::IceCandidate;
    }

    handle_signaling_message(msg);
}

// ============================================================================
// WebRTC Room 实现
// ============================================================================

WebRtcRoom::WebRtcRoom(const std::string& room_id) : room_id_(room_id) {}
WebRtcRoom::~WebRtcRoom() = default;

void WebRtcRoom::add_peer(uint64_t session_id, std::shared_ptr<PeerConnection> peer) {
    std::lock_guard<std::mutex> lock(mutex_);
    peers_[session_id] = peer;
}

void WebRtcRoom::remove_peer(uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    peers_.erase(session_id);
}

void WebRtcRoom::handle_signaling_message(const SignalingMessage& msg) {
    // 转发信令消息
}

void WebRtcRoom::forward_video(uint64_t from_session, const MediaFrame& frame) {
    std::lock_guard<std::mutex> lock(mutex_);

    for (const auto& [session_id, peer] : peers_) {
        if (session_id != from_session && peer->is_connected()) {
            peer->send_video_frame(frame);
        }
    }
}

void WebRtcRoom::forward_audio(uint64_t from_session, const MediaFrame& frame) {
    std::lock_guard<std::mutex> lock(mutex_);

    for (const auto& [session_id, peer] : peers_) {
        if (session_id != from_session && peer->is_connected()) {
            peer->send_audio_frame(frame);
        }
    }
}

uint32_t WebRtcRoom::get_peer_count() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return static_cast<uint32_t>(peers_.size());
}

std::vector<uint64_t> WebRtcRoom::get_peer_ids() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<uint64_t> ids;
    for (const auto& [id, peer] : peers_) {
        ids.push_back(id);
    }
    return ids;
}

// ============================================================================
// PeerConnection 实现
// ============================================================================

PeerConnection::PeerConnection(uint64_t session_id) : session_id_(session_id) {
    local_ssrc_ = static_cast<uint32_t>(session_id);
}

PeerConnection::~PeerConnection() = default;

bool PeerConnection::set_remote_description(const SdpInfo& sdp) {
    remote_sdp_ = sdp;
    return true;
}

SdpInfo PeerConnection::create_offer() {
    SdpInfo offer;
    offer.session_id = std::to_string(session_id_);
    offer.session_version = "1";
    offer.ice_ufrag = "random_ufrag";
    offer.ice_pwd = "random_pwd_123456789012345";
    offer.setup = "actpass";
    return offer;
}

bool PeerConnection::set_local_description(const SdpInfo& sdp) {
    local_sdp_ = sdp;
    return true;
}

void PeerConnection::add_ice_candidate(const IceCandidate& candidate) {
    remote_candidates_.push_back(candidate);
}

std::vector<IceCandidate> PeerConnection::get_local_candidates() const {
    return local_candidates_;
}

void PeerConnection::send_video_frame(const MediaFrame& frame) {
    // 简化的 RTP 发送
}

void PeerConnection::send_audio_frame(const MediaFrame& frame) {
    // 简化的 RTP 发送
}

} // namespace streaming
