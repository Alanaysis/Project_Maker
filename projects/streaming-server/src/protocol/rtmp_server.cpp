/**
 * @file rtmp_server.cpp
 * @brief RTMP 服务器实现
 */

#include "streaming/protocol/rtmp_server.hpp"
#include "streaming/monitor/logger.hpp"

#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>
#include <algorithm>
#include <random>

namespace streaming {

// ============================================================================
// AMF 编解码器实现
// ============================================================================

Buffer AmfCodec::encodeNumber(double value) {
    Buffer result(9);
    result[0] = static_cast<uint8_t>(AmfType::Number);
    std::memcpy(result.data() + 1, &value, 8);
    return result;
}

Buffer AmfCodec::encodeBoolean(bool value) {
    Buffer result(2);
    result[0] = static_cast<uint8_t>(AmfType::Boolean);
    result[1] = value ? 1 : 0;
    return result;
}

Buffer AmfCodec::encodeString(const std::string& value) {
    Buffer result;
    result.push_back(static_cast<uint8_t>(AmfType::String));

    uint16_t len = static_cast<uint16_t>(value.size());
    result.push_back((len >> 8) & 0xFF);
    result.push_back(len & 0xFF);

    result.insert(result.end(), value.begin(), value.end());
    return result;
}

Buffer AmfCodec::encodeNull() {
    return Buffer{static_cast<uint8_t>(AmfType::Null)};
}

Buffer AmfCodec::encodeObject(const std::unordered_map<std::string, AmfValue>& obj) {
    Buffer result;
    result.push_back(static_cast<uint8_t>(AmfType::Object));

    for (const auto& [key, value] : obj) {
        // 属性名
        uint16_t key_len = static_cast<uint16_t>(key.size());
        result.push_back((key_len >> 8) & 0xFF);
        result.push_back(key_len & 0xFF);
        result.insert(result.end(), key.begin(), key.end());

        // 属性值
        switch (value.type) {
            case AmfType::Number: {
                auto encoded = encodeNumber(value.number_val);
                result.insert(result.end(), encoded.begin(), encoded.end());
                break;
            }
            case AmfType::Boolean: {
                auto encoded = encodeBoolean(value.bool_val);
                result.insert(result.end(), encoded.begin(), encoded.end());
                break;
            }
            case AmfType::String: {
                auto encoded = encodeString(value.string_val);
                result.insert(result.end(), encoded.begin(), encoded.end());
                break;
            }
            case AmfType::Null: {
                auto encoded = encodeNull();
                result.insert(result.end(), encoded.begin(), encoded.end());
                break;
            }
            default:
                break;
        }
    }

    // 对象结束标记
    result.push_back(0x00);
    result.push_back(0x00);
    result.push_back(static_cast<uint8_t>(AmfType::ObjectEnd));

    return result;
}

AmfValue AmfCodec::decode(const Buffer& data, size_t& offset) {
    if (offset >= data.size()) {
        return {AmfType::Null};
    }

    AmfType type = static_cast<AmfType>(data[offset++]);

    switch (type) {
        case AmfType::Number:
            return decodeNumber(data, offset);
        case AmfType::Boolean:
            return decodeBoolean(data, offset);
        case AmfType::String:
            return decodeString(data, offset);
        case AmfType::Object:
        case AmfType::EcmaArray:
            return decodeObject(data, offset);
        case AmfType::Null:
            return {AmfType::Null};
        default:
            return {AmfType::Null};
    }
}

AmfValue AmfCodec::decodeNumber(const Buffer& data, size_t& offset) {
    AmfValue value;
    value.type = AmfType::Number;

    if (offset + 8 <= data.size()) {
        std::memcpy(&value.number_val, data.data() + offset, 8);
        offset += 8;
    }

    return value;
}

AmfValue AmfCodec::decodeBoolean(const Buffer& data, size_t& offset) {
    AmfValue value;
    value.type = AmfType::Boolean;

    if (offset < data.size()) {
        value.bool_val = data[offset++] != 0;
    }

    return value;
}

AmfValue AmfCodec::decodeString(const Buffer& data, size_t& offset) {
    AmfValue value;
    value.type = AmfType::String;

    if (offset + 2 <= data.size()) {
        uint16_t len = (data[offset] << 8) | data[offset + 1];
        offset += 2;

        if (offset + len <= data.size()) {
            value.string_val = std::string(data.begin() + offset, data.begin() + offset + len);
            offset += len;
        }
    }

    return value;
}

AmfValue AmfCodec::decodeObject(const Buffer& data, size_t& offset) {
    AmfValue value;
    value.type = AmfType::Object;

    while (offset + 3 <= data.size()) {
        // 检查对象结束标记
        if (data[offset] == 0x00 && data[offset + 1] == 0x00 &&
            data[offset + 2] == static_cast<uint8_t>(AmfType::ObjectEnd)) {
            offset += 3;
            break;
        }

        // 属性名
        uint16_t key_len = (data[offset] << 8) | data[offset + 1];
        offset += 2;

        if (offset + key_len > data.size()) break;

        std::string key(data.begin() + offset, data.begin() + offset + key_len);
        offset += key_len;

        // 属性值
        AmfValue prop_value = decode(data, offset);
        value.object_val[key] = prop_value;
    }

    return value;
}

// ============================================================================
// RTMP 会话实现
// ============================================================================

RtmpSession::RtmpSession(uint64_t session_id, int socket_fd)
    : session_id_(session_id), socket_fd_(socket_fd) {
    recv_buffer_.reserve(65536);
}

RtmpSession::~RtmpSession() {
    stop();
    if (socket_fd_ >= 0) {
        ::close(socket_fd_);
        socket_fd_ = -1;
    }
}

void RtmpSession::start() {
    active_ = true;
    state_ = RtmpState::Uninitialized;
}

void RtmpSession::stop() {
    active_ = false;
    state_ = RtmpState::Uninitialized;
}

void RtmpSession::on_data_received(const Buffer& data) {
    if (!active_) return;

    recv_buffer_.insert(recv_buffer_.end(), data.begin(), data.end());

    // 处理握手
    if (state_ == RtmpState::Uninitialized || state_ == RtmpState::VersionSent) {
        handle_handshake(recv_buffer_);
        return;
    }

    // 处理数据块
    size_t offset = 0;
    while (offset < recv_buffer_.size()) {
        size_t remaining = recv_buffer_.size() - offset;
        if (remaining < 1) break;

        handle_chunk(recv_buffer_, offset);
    }

    // 清除已处理的数据
    if (offset > 0) {
        recv_buffer_.erase(recv_buffer_.begin(), recv_buffer_.begin() + offset);
    }
}

void RtmpSession::handle_handshake(const Buffer& data) {
    if (state_ == RtmpState::Uninitialized) {
        // 接收 C0 + C1
        if (data.size() < 1537) return;

        uint8_t version = data[0];
        if (version != 3) {
            LOG_ERROR("Unsupported RTMP version: " + std::to_string(version));
            return;
        }

        // 发送 S0 + S1 + S2
        Buffer c1(data.begin() + 1, data.begin() + 1537);
        send_handshake_s0s1s2(c1);

        state_ = RtmpState::VersionSent;
        recv_buffer_.erase(recv_buffer_.begin(), recv_buffer_.begin() + 1537);
    } else if (state_ == RtmpState::VersionSent) {
        // 接收 C2
        if (data.size() < 1536) return;

        state_ = RtmpState::HandshakeDone;
        recv_buffer_.erase(recv_buffer_.begin(), recv_buffer_.begin() + 1536);

        LOG_INFO("RTMP handshake completed");
    }
}

void RtmpSession::send_handshake_s0s1s2(const Buffer& c1) {
    Buffer response;

    // S0 - 版本
    response.push_back(3);

    // S1 - 时间戳 + 零 + 随机数据
    Buffer s1(1536, 0);
    uint32_t timestamp = static_cast<uint32_t>(
        std::chrono::steady_clock::now().time_since_epoch().count() / 1000000
    );
    std::memcpy(s1.data(), &timestamp, 4);
    std::memset(s1.data() + 4, 0, 4);

    // 填充随机数据
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(0, 255);
    for (size_t i = 8; i < 1536; ++i) {
        s1[i] = static_cast<uint8_t>(dist(gen));
    }
    response.insert(response.end(), s1.begin(), s1.end());

    // S2 - 回显 C1
    response.insert(response.end(), c1.begin(), c1.end());

    std::lock_guard<std::mutex> lock(send_mutex_);
    ::send(socket_fd_, response.data(), response.size(), 0);
}

void RtmpSession::handle_chunk(const Buffer& data, size_t& offset) {
    if (offset >= data.size()) return;

    // 解析块头
    RtmpChunkHeader header;
    header.fmt = (data[offset] >> 6) & 0x03;
    header.cs_id = data[offset] & 0x3F;
    offset++;

    // 处理扩展 cs_id
    if (header.cs_id == 0) {
        if (offset >= data.size()) return;
        header.cs_id = data[offset] + 64;
        offset++;
    } else if (header.cs_id == 1) {
        if (offset + 1 >= data.size()) return;
        header.cs_id = data[offset] + (data[offset + 1] << 8) + 64;
        offset += 2;
    }

    // 获取之前的块头
    auto it = chunk_headers_.find(header.cs_id);
    const RtmpChunkHeader* prev = (it != chunk_headers_.end()) ? &it->second : nullptr;

    // 根据 fmt 解析块头
    switch (header.fmt) {
        case 0: // 完整头
            if (offset + 11 > data.size()) return;
            header.timestamp = (data[offset] << 16) | (data[offset + 1] << 8) | data[offset + 2];
            header.msg_length = (data[offset + 3] << 16) | (data[offset + 4] << 8) | data[offset + 5];
            header.msg_type_id = data[offset + 6];
            header.msg_stream_id = data[offset + 7] | (data[offset + 8] << 8) |
                                   (data[offset + 9] << 16) | (data[offset + 10] << 24);
            offset += 11;
            break;

        case 1: // 时间戳增量
            if (offset + 7 > data.size()) return;
            header.timestamp = (data[offset] << 16) | (data[offset + 1] << 8) | data[offset + 2];
            header.msg_length = (data[offset + 3] << 16) | (data[offset + 4] << 8) | data[offset + 5];
            header.msg_type_id = data[offset + 6];
            offset += 7;
            if (prev) header.msg_stream_id = prev->msg_stream_id;
            break;

        case 2: // 时间戳增量
            if (offset + 3 > data.size()) return;
            header.timestamp = (data[offset] << 16) | (data[offset + 1] << 8) | data[offset + 2];
            offset += 3;
            if (prev) {
                header.msg_length = prev->msg_length;
                header.msg_type_id = prev->msg_type_id;
                header.msg_stream_id = prev->msg_stream_id;
            }
            break;

        case 3: // 无头
            if (prev) {
                header.timestamp = prev->timestamp;
                header.msg_length = prev->msg_length;
                header.msg_type_id = prev->msg_type_id;
                header.msg_stream_id = prev->msg_stream_id;
            }
            break;
    }

    // 处理扩展时间戳
    if (header.timestamp == 0xFFFFFF) {
        if (offset + 4 > data.size()) return;
        header.timestamp = (data[offset] << 24) | (data[offset + 1] << 16) |
                          (data[offset + 2] << 8) | data[offset + 3];
        offset += 4;
    }

    // 读取块数据
    size_t chunk_size = std::min(static_cast<size_t>(in_chunk_size_),
                                 static_cast<size_t>(header.msg_length));
    if (offset + chunk_size > data.size()) return;

    Buffer& chunk_buffer = chunk_buffers_[header.cs_id];
    chunk_buffer.insert(chunk_buffer.end(), data.begin() + offset, data.begin() + offset + chunk_size);
    offset += chunk_size;

    // 检查消息是否完整
    if (chunk_buffer.size() >= header.msg_length) {
        RtmpMessage msg;
        msg.type = static_cast<RtmpMessageType>(header.msg_type_id);
        msg.stream_id = header.msg_stream_id;
        msg.payload = std::move(chunk_buffer);
        msg.received_time = std::chrono::steady_clock::now();

        handle_message(msg);
        chunk_buffers_.erase(header.cs_id);
    }

    // 更新块头
    chunk_headers_[header.cs_id] = header;
}

void RtmpSession::handle_message(const RtmpMessage& msg) {
    switch (msg.type) {
        case RtmpMessageType::SetChunkSize:
            if (msg.payload.size() >= 4) {
                in_chunk_size_ = (msg.payload[0] << 24) | (msg.payload[1] << 16) |
                                 (msg.payload[2] << 8) | msg.payload[3];
                LOG_DEBUG("RTMP chunk size set to " + std::to_string(in_chunk_size_));
            }
            break;

        case RtmpMessageType::CommandAmf0:
            handle_command(msg);
            break;

        case RtmpMessageType::Audio:
            handle_audio(msg);
            break;

        case RtmpMessageType::Video:
            handle_video(msg);
            break;

        case RtmpMessageType::WindowAckSize:
            if (msg.payload.size() >= 4) {
                window_ack_size_ = (msg.payload[0] << 24) | (msg.payload[1] << 16) |
                                   (msg.payload[2] << 8) | msg.payload[3];
            }
            break;

        default:
            break;
    }
}

void RtmpSession::handle_command(const RtmpMessage& msg) {
    size_t offset = 0;
    std::vector<AmfValue> params;

    while (offset < msg.payload.size()) {
        params.push_back(AmfCodec::decode(msg.payload, offset));
    }

    if (params.empty() || params[0].type != AmfType::String) return;

    const std::string& command = params[0].string_val;

    if (command == "connect") {
        handle_connect(params);
    } else if (command == "createStream") {
        handle_create_stream(params);
    } else if (command == "publish") {
        handle_publish(params);
    } else if (command == "play") {
        handle_play(params);
    } else if (command == "deleteStream") {
        handle_delete_stream(params);
    }
}

void RtmpSession::handle_connect(const std::vector<AmfValue>& params) {
    if (params.size() >= 4 && params[3].type == AmfType::Object) {
        auto it = params[3].object_val.find("app");
        if (it != params[3].object_val.end() && it->second.type == AmfType::String) {
            app_name_ = it->second.string_val;
        }
    }

    state_ = RtmpState::Connected;
    send_connect_result();

    LOG_INFO("RTMP connect: app=" + app_name_);
}

void RtmpSession::handle_create_stream(const std::vector<AmfValue>& params) {
    double transaction_id = 0;
    if (params.size() >= 2 && params[1].type == AmfType::Number) {
        transaction_id = params[1].number_val;
    }

    send_create_stream_result(transaction_id);
    state_ = RtmpState::Created;
}

void RtmpSession::handle_publish(const std::vector<AmfValue>& params) {
    if (params.size() >= 4 && params[3].type == AmfType::String) {
        stream_name_ = params[3].string_val;
    }

    is_publisher_ = true;
    state_ = RtmpState::Publishing;
    send_publish_start();

    LOG_INFO("RTMP publish: stream=" + stream_name_);
}

void RtmpSession::handle_play(const std::vector<AmfValue>& params) {
    if (params.size() >= 4 && params[3].type == AmfType::String) {
        stream_name_ = params[3].string_val;
    }

    is_publisher_ = false;
    state_ = RtmpState::Playing;
    send_play_start();

    LOG_INFO("RTMP play: stream=" + stream_name_);
}

void RtmpSession::handle_delete_stream(const std::vector<AmfValue>& params) {
    state_ = RtmpState::Connected;
    LOG_INFO("RTMP deleteStream: stream=" + stream_name_);
}

void RtmpSession::handle_audio(const RtmpMessage& msg) {
    if (!is_publisher_ || !frame_callback_) return;

    auto frame = std::make_shared<MediaFrame>();
    frame->type = FrameType::AudioFrame;
    frame->media_type = MediaType::Audio;
    frame->data = msg.payload;
    frame->timestamp = msg.received_time;

    frame_callback_(frame);
}

void RtmpSession::handle_video(const RtmpMessage& msg) {
    if (!is_publisher_ || !frame_callback_ || msg.payload.empty()) return;

    auto frame = std::make_shared<MediaFrame>();

    // 检查是否是关键帧
    uint8_t frame_type = (msg.payload[0] >> 4) & 0x0F;
    if (frame_type == 1) {
        frame->type = FrameType::VideoKeyFrame;
        frame->is_keyframe = true;
    } else {
        frame->type = FrameType::VideoInterFrame;
        frame->is_keyframe = false;
    }

    frame->media_type = MediaType::Video;
    frame->data = msg.payload;
    frame->timestamp = msg.received_time;

    frame_callback_(frame);
}

void RtmpSession::send_connect_result() {
    RtmpMessage msg;
    msg.type = RtmpMessageType::CommandAmf0;
    msg.stream_id = 0;

    // 编码响应
    auto command = AmfCodec::encodeString("_result");
    auto trans_id = AmfCodec::encodeNumber(1);
    auto props = AmfCodec::encodeObject({
        {"fmsVer", {AmfType::String, 0, false, "FMS/3,0,1,123"}},
        {"capabilities", {AmfType::Number, 31, false, ""}}
    });
    auto info = AmfCodec::encodeObject({
        {"level", {AmfType::String, 0, false, "status"}},
        {"code", {AmfType::String, 0, false, "NetConnection.Connect.Success"}},
        {"description", {AmfType::String, 0, false, "Connection succeeded."}}
    });

    msg.payload.insert(msg.payload.end(), command.begin(), command.end());
    msg.payload.insert(msg.payload.end(), trans_id.begin(), trans_id.end());
    msg.payload.insert(msg.payload.end(), props.begin(), props.end());
    msg.payload.insert(msg.payload.end(), info.begin(), info.end());

    send_message(msg);
}

void RtmpSession::send_create_stream_result(double transaction_id) {
    RtmpMessage msg;
    msg.type = RtmpMessageType::CommandAmf0;
    msg.stream_id = 0;

    auto command = AmfCodec::encodeString("_result");
    auto trans_id = AmfCodec::encodeNumber(transaction_id);
    auto null = AmfCodec::encodeNull();
    auto stream_id = AmfCodec::encodeNumber(1);

    msg.payload.insert(msg.payload.end(), command.begin(), command.end());
    msg.payload.insert(msg.payload.end(), trans_id.begin(), trans_id.end());
    msg.payload.insert(msg.payload.end(), null.begin(), null.end());
    msg.payload.insert(msg.payload.end(), stream_id.begin(), stream_id.end());

    send_message(msg);
}

void RtmpSession::send_publish_start() {
    send_on_status("status", "NetStream.Publish.Start", "Publishing started.");
}

void RtmpSession::send_play_start() {
    send_on_status("status", "NetStream.Play.Start", "Playing started.");
}

void RtmpSession::send_stream_eof() {
    send_on_status("status", "NetStream.Play.Stop", "Stream stopped.");
}

void RtmpSession::send_on_status(const std::string& level, const std::string& code,
                                  const std::string& description) {
    RtmpMessage msg;
    msg.type = RtmpMessageType::CommandAmf0;
    msg.stream_id = 1;

    auto command = AmfCodec::encodeString("onStatus");
    auto trans_id = AmfCodec::encodeNumber(0);
    auto null = AmfCodec::encodeNull();
    auto info = AmfCodec::encodeObject({
        {"level", {AmfType::String, 0, false, level}},
        {"code", {AmfType::String, 0, false, code}},
        {"description", {AmfType::String, 0, false, description}}
    });

    msg.payload.insert(msg.payload.end(), command.begin(), command.end());
    msg.payload.insert(msg.payload.end(), trans_id.begin(), trans_id.end());
    msg.payload.insert(msg.payload.end(), null.begin(), null.end());
    msg.payload.insert(msg.payload.end(), info.begin(), info.end());

    send_message(msg);
}

void RtmpSession::send_message(const RtmpMessage& msg) {
    RtmpChunkHeader header;
    header.fmt = 0;
    header.cs_id = 2;
    header.msg_type_id = static_cast<uint8_t>(msg.type);
    header.msg_stream_id = msg.stream_id;
    header.msg_length = static_cast<uint32_t>(msg.payload.size());

    send_chunk(header, msg.payload);
}

void RtmpSession::send_chunk(const RtmpChunkHeader& header, const Buffer& payload) {
    std::lock_guard<std::mutex> lock(send_mutex_);

    Buffer header_data;
    header_data.push_back((header.fmt << 6) | (header.cs_id & 0x3F));

    if (header.cs_id >= 64 + 256) {
        header_data.push_back((header.cs_id - 64) & 0xFF);
        header_data.push_back(((header.cs_id - 64) >> 8) & 0xFF);
    } else if (header.cs_id >= 64) {
        header_data.push_back(header.cs_id - 64);
    }

    header_data.push_back((header.timestamp >> 16) & 0xFF);
    header_data.push_back((header.timestamp >> 8) & 0xFF);
    header_data.push_back(header.timestamp & 0xFF);

    header_data.push_back((header.msg_length >> 16) & 0xFF);
    header_data.push_back((header.msg_length >> 8) & 0xFF);
    header_data.push_back(header.msg_length & 0xFF);

    header_data.push_back(header.msg_type_id);

    header_data.push_back(header.msg_stream_id & 0xFF);
    header_data.push_back((header.msg_stream_id >> 8) & 0xFF);
    header_data.push_back((header.msg_stream_id >> 16) & 0xFF);
    header_data.push_back((header.msg_stream_id >> 24) & 0xFF);

    // 发送头
    ::send(socket_fd_, header_data.data(), header_data.size(), 0);

    // 分块发送数据
    size_t offset = 0;
    while (offset < payload.size()) {
        size_t chunk_size = std::min(static_cast<size_t>(out_chunk_size_),
                                     payload.size() - offset);
        ::send(socket_fd_, payload.data() + offset, chunk_size, 0);
        offset += chunk_size;

        if (offset < payload.size()) {
            // 发送后续块头
            Buffer cont_header;
            cont_header.push_back(0xC0 | (header.cs_id & 0x3F));
            ::send(socket_fd_, cont_header.data(), cont_header.size(), 0);
        }
    }
}

void RtmpSession::set_chunk_size(uint32_t size) {
    out_chunk_size_ = size;

    RtmpMessage msg;
    msg.type = RtmpMessageType::SetChunkSize;
    msg.stream_id = 0;

    msg.payload.push_back((size >> 24) & 0xFF);
    msg.payload.push_back((size >> 16) & 0xFF);
    msg.payload.push_back((size >> 8) & 0xFF);
    msg.payload.push_back(size & 0xFF);

    send_message(msg);
}

// ============================================================================
// RTMP 服务器实现
// ============================================================================

RtmpServer::RtmpServer() = default;

RtmpServer::~RtmpServer() {
    stop();
}

bool RtmpServer::start(const std::string& host, uint16_t port) {
    host_ = host;
    port_ = port;

    // 创建 socket
    listen_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd_ < 0) {
        LOG_ERROR("Failed to create RTMP socket");
        return false;
    }

    // 设置 socket 选项
    int opt = 1;
    setsockopt(listen_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    // 绑定地址
    struct sockaddr_in addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);

    if (host == "0.0.0.0") {
        addr.sin_addr.s_addr = INADDR_ANY;
    } else {
        inet_pton(AF_INET, host.c_str(), &addr.sin_addr);
    }

    if (bind(listen_fd_, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        LOG_ERROR("Failed to bind RTMP socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    // 开始监听
    if (listen(listen_fd_, 128) < 0) {
        LOG_ERROR("Failed to listen on RTMP socket");
        ::close(listen_fd_);
        listen_fd_ = -1;
        return false;
    }

    running_ = true;
    accept_thread_ = std::thread(&RtmpServer::accept_loop, this);

    LOG_INFO("RTMP server started on " + host + ":" + std::to_string(port));
    return true;
}

void RtmpServer::stop() {
    running_ = false;

    if (listen_fd_ >= 0) {
        ::close(listen_fd_);
        listen_fd_ = -1;
    }

    if (accept_thread_.joinable()) {
        accept_thread_.join();
    }

    // 关闭所有会话
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    sessions_.clear();

    LOG_INFO("RTMP server stopped");
}

void RtmpServer::accept_loop() {
    while (running_) {
        struct sockaddr_in client_addr;
        socklen_t addr_len = sizeof(client_addr);

        int client_fd = accept(listen_fd_, (struct sockaddr*)&client_addr, &addr_len);
        if (client_fd < 0) {
            if (running_) {
                LOG_ERROR("Failed to accept RTMP connection");
            }
            continue;
        }

        // 设置非阻塞
        int flags = fcntl(client_fd, F_GETFL, 0);
        fcntl(client_fd, F_SETFL, flags | O_NONBLOCK);

        // 获取客户端地址
        char addr_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &client_addr.sin_addr, addr_str, sizeof(addr_str));
        std::string client_addr_str = addr_str;

        handle_accept(client_fd, client_addr_str);
    }
}

void RtmpServer::handle_accept(int client_fd, const std::string& client_addr) {
    uint64_t session_id;
    {
        std::lock_guard<std::mutex> lock(sessions_mutex_);
        session_id = next_session_id_++;
    }

    auto session = std::make_shared<RtmpSession>(session_id, client_fd);
    session->set_frame_callback([this, session_id](MediaFramePtr frame) {
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

    LOG_INFO("RTMP session created: " + std::to_string(session_id) + " from " + client_addr);
}

void RtmpServer::remove_session(uint64_t session_id) {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    sessions_.erase(session_id);
}

uint32_t RtmpServer::get_session_count() const {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    return static_cast<uint32_t>(sessions_.size());
}

std::vector<uint64_t> RtmpServer::get_session_ids() const {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    std::vector<uint64_t> ids;
    for (const auto& [id, session] : sessions_) {
        ids.push_back(id);
    }
    return ids;
}

} // namespace streaming
