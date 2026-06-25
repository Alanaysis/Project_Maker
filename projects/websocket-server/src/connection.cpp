/**
 * @file connection.cpp
 * @brief WebSocket 连接管理实现
 *
 * 实现 WebSocket 连接的生命周期管理，包括：
 * - TCP 套接字读写
 * - WebSocket 握手处理
 * - 帧读写
 * - 心跳检测
 * - 分片消息重组
 */

#include "websocket/connection.h"
#include "websocket/server.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>
#include <iostream>

namespace ws {

std::atomic<uint64_t> Connection::next_id_{1};

// ============================================================================
// 构造和析构
// ============================================================================

Connection::Connection(int fd, Server* server)
    : id_(next_id_++), fd_(fd), server_(server) {
    read_buffer_.reserve(READ_BUFFER_SIZE);
    get_peer_address();
    update_active_time();
}

Connection::~Connection() {
    if (fd_ >= 0) {
        ::close(fd_);
        fd_ = -1;
    }
}

// ============================================================================
// 连接信息
// ============================================================================

void Connection::get_peer_address() {
    struct sockaddr_in addr;
    socklen_t addr_len = sizeof(addr);
    if (getpeername(fd_, reinterpret_cast<struct sockaddr*>(&addr), &addr_len) == 0) {
        remote_addr_ = inet_ntoa(addr.sin_addr);
        remote_port_ = ntohs(addr.sin_port);
    }
}

void Connection::update_active_time() {
    last_active_time_ = utils::timestamp_ms();
}

// ============================================================================
// 握手处理
// ============================================================================

bool Connection::handle_handshake() {
    // 读取握手数据
    char buf[4096];
    ssize_t n = recv(fd_, buf, sizeof(buf), 0);
    if (n <= 0) {
        return false;
    }

    handshake_data_.append(buf, n);

    // 检查是否收到完整的 HTTP 请求
    if (handshake_data_.find("\r\n\r\n") == std::string::npos) {
        return true;  // 继续等待数据
    }

    // 解析 HTTP 请求
    std::string request = handshake_data_;

    // 提取 Sec-WebSocket-Key
    std::string ws_key;
    size_t key_pos = request.find("Sec-WebSocket-Key:");
    if (key_pos == std::string::npos) {
        key_pos = request.find("sec-websocket-key:");
    }

    if (key_pos != std::string::npos) {
        key_pos += 18;  // 跳过 "Sec-WebSocket-Key:"
        while (key_pos < request.size() && request[key_pos] == ' ') {
            key_pos++;
        }
        size_t key_end = request.find("\r\n", key_pos);
        if (key_end != std::string::npos) {
            ws_key = request.substr(key_pos, key_end - key_pos);
        }
    }

    if (ws_key.empty()) {
        // 无效的握手请求
        std::string response = "HTTP/1.1 400 Bad Request\r\n\r\n";
        ::send(fd_, response.c_str(), response.size(), 0);
        return false;
    }

    // 计算 Sec-WebSocket-Accept
    const std::string ws_magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
    std::string accept_input = ws_key + ws_magic;
    auto sha1_hash = utils::sha1(accept_input);
    std::string ws_accept = utils::base64_encode(sha1_hash.data(), sha1_hash.size());

    // 构建握手响应
    std::string response = "HTTP/1.1 101 Switching Protocols\r\n"
                          "Upgrade: websocket\r\n"
                          "Connection: Upgrade\r\n"
                          "Sec-WebSocket-Accept: " + ws_accept + "\r\n"
                          "Server: WebSocket-Server/1.0\r\n"
                          "\r\n";

    // 发送握手响应
    ssize_t sent = ::send(fd_, response.c_str(), response.size(), 0);
    if (sent != static_cast<ssize_t>(response.size())) {
        return false;
    }

    // 握手成功，更新状态
    state_ = ConnectionState::Open;

    // 触发 on_open 回调
    if (callbacks_.on_open) {
        callbacks_.on_open(shared_from_this());
    }

    return true;
}

// ============================================================================
// 消息发送
// ============================================================================

void Connection::send_text(const std::string& text) {
    if (state_ != ConnectionState::Open) return;

    auto data = FrameCodec::encode_text(text);
    enqueue_send(data);
}

void Connection::send_binary(const std::vector<uint8_t>& data) {
    if (state_ != ConnectionState::Open) return;

    auto frame_data = FrameCodec::encode_binary(data);
    enqueue_send(frame_data);
}

void Connection::send(const Message& msg) {
    if (state_ != ConnectionState::Open) return;

    std::vector<uint8_t> frame_data;
    if (msg.type == Opcode::Text) {
        frame_data = FrameCodec::encode_text(msg.text());
    } else {
        frame_data = FrameCodec::encode_binary(msg.data);
    }
    enqueue_send(frame_data);
}

void Connection::send_ping(const std::vector<uint8_t>& payload) {
    if (state_ != ConnectionState::Open) return;

    auto data = FrameCodec::create_ping(payload);
    enqueue_send(data);
}

void Connection::send_pong(const std::vector<uint8_t>& payload) {
    if (state_ != ConnectionState::Open) return;

    auto data = FrameCodec::create_pong(payload);
    enqueue_send(data);
}

void Connection::close(CloseCode code, const std::string& reason) {
    if (state_ == ConnectionState::Closed || state_ == ConnectionState::Closing) {
        return;
    }

    state_ = ConnectionState::Closing;

    // 发送关闭帧
    auto close_data = FrameCodec::create_close_frame(code, reason);
    enqueue_send(close_data);

    // 刷新发送缓冲区
    flush_send_buffer();

    // 触发关闭回调
    trigger_close(code, reason);
}

void Connection::enqueue_send(const std::vector<uint8_t>& data) {
    std::lock_guard<std::mutex> lock(write_mutex_);
    write_buffer_.insert(write_buffer_.end(), data.begin(), data.end());
}

void Connection::flush_send_buffer() {
    std::lock_guard<std::mutex> lock(write_mutex_);

    while (!write_buffer_.empty()) {
        ssize_t sent = ::send(fd_, write_buffer_.data(), write_buffer_.size(), MSG_NOSIGNAL);
        if (sent <= 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                break;
            }
            // 发送错误
            write_buffer_.clear();
            return;
        }
        write_buffer_.erase(write_buffer_.begin(), write_buffer_.begin() + sent);
    }
}

// ============================================================================
// 事件处理
// ============================================================================

void Connection::handle_read() {
    if (state_ == ConnectionState::Connecting) {
        if (!handle_handshake()) {
            state_ = ConnectionState::Closed;
        }
        return;
    }

    if (state_ != ConnectionState::Open) {
        return;
    }

    // 读取数据
    char buf[READ_BUFFER_SIZE];
    ssize_t n = recv(fd_, buf, sizeof(buf), 0);

    if (n <= 0) {
        if (n == 0) {
            // 连接关闭
            trigger_close(CloseCode::GoingAway, "Connection closed by peer");
        } else if (errno != EAGAIN && errno != EWOULDBLOCK) {
            // 读取错误
            trigger_close(CloseCode::InternalError, "Read error");
        }
        return;
    }

    update_active_time();

    // 添加到读缓冲区
    read_buffer_.insert(read_buffer_.end(), buf, buf + n);

    // 解析帧
    size_t offset = 0;
    while (offset < read_buffer_.size()) {
        size_t consumed = 0;
        auto frame = FrameCodec::decode_frame(read_buffer_.data() + offset,
                                               read_buffer_.size() - offset,
                                               consumed);
        if (!frame) {
            break;  // 数据不足，等待更多数据
        }

        offset += consumed;
        process_frame(*frame);
    }

    // 移除已处理的数据
    if (offset > 0) {
        read_buffer_.erase(read_buffer_.begin(), read_buffer_.begin() + offset);
    }
}

void Connection::handle_write() {
    flush_send_buffer();
}

// ============================================================================
// 帧处理
// ============================================================================

void Connection::process_frame(const Frame& frame) {
    // 控制帧
    if (static_cast<uint8_t>(frame.header.opcode) & 0x08) {
        process_control_frame(frame);
        return;
    }

    // 数据帧
    process_data_frame(frame);
}

void Connection::process_data_frame(const Frame& frame) {
    if (frame.header.opcode == Opcode::Continuation) {
        // 继续帧
        if (!message_in_progress_) {
            // 没有正在进行的消息，协议错误
            close(CloseCode::ProtocolError, "Unexpected continuation frame");
            return;
        }

        // 追加数据
        current_message_data_.insert(current_message_data_.end(),
                                     frame.payload.begin(), frame.payload.end());
    } else {
        // 新消息开始
        if (message_in_progress_) {
            // 已经有消息在进行中，协议错误
            close(CloseCode::ProtocolError, "New message while previous message in progress");
            return;
        }

        current_message_type_ = frame.header.opcode;
        current_message_data_ = frame.payload;
        message_in_progress_ = true;
    }

    // 检查是否是最后一帧
    if (frame.header.fin) {
        finalize_message();
        message_in_progress_ = false;
        current_message_data_.clear();
    }
}

void Connection::process_control_frame(const Frame& frame) {
    // 控制帧不能被分片
    if (!frame.header.fin) {
        close(CloseCode::ProtocolError, "Control frame must not be fragmented");
        return;
    }

    // 控制帧载荷不能超过 125 字节
    if (frame.payload.size() > 125) {
        close(CloseCode::ProtocolError, "Control frame payload too large");
        return;
    }

    switch (frame.header.opcode) {
        case Opcode::Close: {
            auto [code, reason] = FrameCodec::parse_close_payload(frame.payload);

            // 发送关闭帧作为响应
            if (state_ == ConnectionState::Open) {
                auto close_data = FrameCodec::create_close_frame(
                    static_cast<CloseCode>(code), reason);
                enqueue_send(close_data);
                flush_send_buffer();
            }

            trigger_close(static_cast<CloseCode>(code), reason);
            break;
        }

        case Opcode::Ping: {
            // 回复 Pong
            send_pong(frame.payload);

            if (callbacks_.on_ping) {
                callbacks_.on_ping(shared_from_this());
            }
            break;
        }

        case Opcode::Pong: {
            update_active_time();

            if (callbacks_.on_pong) {
                callbacks_.on_pong(shared_from_this());
            }
            break;
        }

        default:
            close(CloseCode::ProtocolError, "Unknown control frame opcode");
            break;
    }
}

void Connection::finalize_message() {
    Message msg;
    msg.type = current_message_type_;
    msg.data = std::move(current_message_data_);

    // 触发消息回调
    if (callbacks_.on_message) {
        callbacks_.on_message(shared_from_this(), msg);
    }
}

// ============================================================================
// 房间管理
// ============================================================================

void Connection::join_room(const std::string& room_name) {
    auto it = std::find(rooms_.begin(), rooms_.end(), room_name);
    if (it == rooms_.end()) {
        rooms_.push_back(room_name);
    }
}

void Connection::leave_room(const std::string& room_name) {
    auto it = std::find(rooms_.begin(), rooms_.end(), room_name);
    if (it != rooms_.end()) {
        rooms_.erase(it);
    }
}

// ============================================================================
// 关闭处理
// ============================================================================

void Connection::trigger_close(CloseCode code, const std::string& reason) {
    if (state_ == ConnectionState::Closed) {
        return;
    }

    state_ = ConnectionState::Closed;

    if (callbacks_.on_close) {
        callbacks_.on_close(shared_from_this(), code, reason);
    }
}

} // namespace ws
