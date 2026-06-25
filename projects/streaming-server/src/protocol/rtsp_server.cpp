/**
 * @file rtsp_server.cpp
 * @brief RTSP 服务器实现
 */

#include "streaming/protocol/rtsp_server.hpp"
#include "streaming/monitor/logger.hpp"

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <sstream>

namespace streaming {

// ============================================================================
// SDP 生成器实现
// ============================================================================

std::string SdpGenerator::generate(const MediaParams& params,
                                   const std::string& server_ip,
                                   uint16_t video_port,
                                   uint16_t audio_port) {
    std::ostringstream sdp;

    // 会话级
    sdp << "v=0\r\n";
    sdp << "o=- 0 0 IN IP4 " << server_ip << "\r\n";
    sdp << "s=Streaming Server\r\n";
    sdp << "c=IN IP4 " << server_ip << "\r\n";
    sdp << "t=0 0\r\n";

    // 视频媒体
    if (params.video.codec != VideoCodec::Unknown) {
        sdp << "m=video " << video_port << " RTP/AVP 96\r\n";
        sdp << "a=rtpmap:96 " << get_video_codec_name(params.video.codec)
            << "/90000\r\n";
        sdp << "a=fmtp:96 " << get_video_fmtp(params.video.codec) << "\r\n";
        sdp << "a=control:trackID=0\r\n";
    }

    // 音频媒体
    if (params.audio.codec != AudioCodec::Unknown) {
        sdp << "m=audio " << audio_port << " RTP/AVP 97\r\n";
        sdp << "a=rtpmap:97 " << get_audio_codec_name(params.audio.codec)
            << "/" << params.audio.sample_rate << "/" << params.audio.channels << "\r\n";
        sdp << "a=fmtp:97 " << get_audio_fmtp(params.audio.codec) << "\r\n";
        sdp << "a=control:trackID=1\r\n";
    }

    return sdp.str();
}

std::string SdpGenerator::get_video_codec_name(VideoCodec codec) {
    switch (codec) {
        case VideoCodec::H264: return "H264";
        case VideoCodec::H265: return "H265";
        case VideoCodec::VP8:  return "VP8";
        case VideoCodec::VP9:  return "VP9";
        default: return "H264";
    }
}

std::string SdpGenerator::get_audio_codec_name(AudioCodec codec) {
    switch (codec) {
        case AudioCodec::AAC:   return "MPEG4-GENERIC";
        case AudioCodec::OPUS:  return "opus";
        case AudioCodec::MP3:   return "MPEG1-2";
        default: return "MPEG4-GENERIC";
    }
}

std::string SdpGenerator::get_video_fmtp(VideoCodec codec) {
    switch (codec) {
        case VideoCodec::H264:
            return "packetization-mode=1;profile-level-id=42001F";
        default:
            return "";
    }
}

std::string SdpGenerator::get_audio_fmtp(AudioCodec codec) {
    switch (codec) {
        case AudioCodec::AAC:
            return "streamtype=5;profile-level-id=1;mode=AAC-hbr;sizelength=13;indexlength=3;indexdeltalength=3";
        default:
            return "";
    }
}

// ============================================================================
// RTP 打包器实现
// ============================================================================

RtpPacketizer::RtpPacketizer(uint8_t payload_type, uint32_t ssrc)
    : payload_type_(payload_type), ssrc_(ssrc) {}

std::vector<RtpPacket> RtpPacketizer::packetize(const MediaFrame& frame) {
    if (frame.media_type == MediaType::Video) {
        return packetize_h264(frame.data,
                             static_cast<uint32_t>(frame.pts),
                             frame.is_keyframe);
    } else {
        return packetize_aac(frame.data,
                            static_cast<uint32_t>(frame.pts));
    }
}

std::vector<RtpPacket> RtpPacketizer::packetize_h264(const Buffer& data,
                                                      uint32_t timestamp,
                                                      bool marker) {
    std::vector<RtpPacket> packets;

    // 简化的 H264 打包
    size_t offset = 0;
    while (offset < data.size()) {
        RtpPacket packet;
        packet.header.version = 2;
        packet.header.payload_type = payload_type_;
        packet.header.sequence_number = sequence_number_++;
        packet.header.timestamp = timestamp;
        packet.header.ssrc = ssrc_;

        size_t payload_size = std::min(static_cast<size_t>(mtu_ - 12), data.size() - offset);
        packet.payload = Buffer(data.begin() + offset, data.begin() + offset + payload_size);

        if (offset + payload_size >= data.size()) {
            packet.header.marker = marker;
        }

        packets.push_back(packet);
        offset += payload_size;
    }

    return packets;
}

std::vector<RtpPacket> RtpPacketizer::packetize_aac(const Buffer& data, uint32_t timestamp) {
    std::vector<RtpPacket> packets;

    // AAC 打包
    RtpPacket packet;
    packet.header.version = 2;
    packet.header.payload_type = payload_type_;
    packet.header.sequence_number = sequence_number_++;
    packet.header.timestamp = timestamp;
    packet.header.ssrc = ssrc_;
    packet.header.marker = true;

    // AU header
    Buffer payload;
    payload.push_back(0x00);
    payload.push_back(0x10);
    payload.push_back(static_cast<uint8_t>((data.size() >> 5) & 0xFF));
    payload.push_back(static_cast<uint8_t>((data.size() << 3) & 0xFF));
    payload.insert(payload.end(), data.begin(), data.end());

    packet.payload = payload;
    packets.push_back(packet);

    return packets;
}

// ============================================================================
// RTSP 服务器实现（简化）
// ============================================================================

RtspServer::RtspServer() = default;
RtspServer::~RtspServer() { stop(); }

bool RtspServer::start(const std::string& host, uint16_t port) {
    host_ = host;
    port_ = port;

    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        LOG_ERROR("Failed to create RTSP socket");
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
        LOG_ERROR("Failed to bind RTSP socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    if (listen(listen_fd_, 128) < 0) {
        LOG_ERROR("Failed to listen on RTSP socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    running_ = true;
    accept_thread_ = std::thread(&RtspServer::accept_loop, this);

    LOG_INFO("RTSP server started on " + host + ":" + std::to_string(port));
    return true;
}

void RtspServer::stop() {
    running_ = false;

    if (listen_fd_ >= 0) {
        ::close(listen_fd_);
        listen_fd_ = -1;
    }

    if (accept_thread_.joinable()) {
        accept_thread_.join();
    }

    std::lock_guard<std::mutex> lock(sessions_mutex_);
    sessions_.clear();

    LOG_INFO("RTSP server stopped");
}

uint32_t RtspServer::get_session_count() const {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    return static_cast<uint32_t>(sessions_.size());
}

void RtspServer::accept_loop() {
    while (running_) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept(listen_fd_, (struct sockaddr*)&client_addr, &addr_len);
        if (client_fd < 0) {
            if (running_) {
                LOG_ERROR("Failed to accept RTSP connection");
            }
            continue;
        }

        char addr_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, addr_str, sizeof(addr_str));

        handle_accept(client_fd, std::string(addr_str));
    }
}

void RtspServer::handle_accept(int client_fd, const std::string& client_addr) {
    uint64_t session_id;
    {
        std::lock_guard<std::mutex> lock(sessions_mutex_);
        session_id = next_session_id_++;
    }

    auto session = std::make_shared<RtspSession>(session_id, client_fd);
    session->set_frame_callback([this](MediaFramePtr frame) {
        if (frame_callback_) {
            frame_callback_(frame);
        }
    });
    session->set_close_callback([this, session_id]() {
        remove_session(session_id);
        if (connection_callback_) {
            connection_callback_(session_id, false);
        }
    });

    session->start();

    {
        std::lock_guard<std::mutex> lock(sessions_mutex_);
        sessions_[session_id] = session;
    }

    if (connection_callback_) {
        connection_callback_(session_id, true);
    }

    LOG_INFO("RTSP session created: " + std::to_string(session_id) + " from " + client_addr);
}

void RtspServer::remove_session(uint64_t session_id) {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    sessions_.erase(session_id);
}

// RtspSession 简化实现
RtspSession::RtspSession(uint64_t session_id, int socket_fd)
    : session_id_(session_id), socket_fd_(socket_fd) {}

RtspSession::~RtspSession() {
    stop();
    if (socket_fd_ >= 0) {
        ::close(socket_fd_);
    }
}

void RtspSession::start() {
    active_ = true;
}

void RtspSession::stop() {
    active_ = false;
}

} // namespace streaming
