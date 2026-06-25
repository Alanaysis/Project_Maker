/**
 * @file http2_connection.cpp
 * @brief HTTP/2 连接管理实现
 */

#include "http2_connection.h"
#include <sys/socket.h>
#include <unistd.h>
#include <cstring>
#include <stdexcept>
#include <iostream>
#include <thread>

namespace http2 {

Connection::Connection(int socket_fd, bool is_server)
    : socket_fd_(socket_fd),
      is_server_(is_server),
      stream_manager_(65535) {}

Connection::~Connection() {
    stop();
}

void Connection::start() {
    is_open_ = true;

    if (is_server_) {
        // 服务器等待客户端前言
        // 客户端前言是 24 字节的 "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"
        std::vector<uint8_t> preface(24);
        ssize_t n = recv(socket_fd_, preface.data(), 24, 0);
        if (n != 24 || memcmp(preface.data(), "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n", 24) != 0) {
            handle_error(ErrorCode::PROTOCOL_ERROR, "Invalid connection preface");
            return;
        }

        // 发送设置帧
        send_settings();
    }

    // 启动接收线程
    std::thread receive_thread(&Connection::receive_loop, this);
    receive_thread.detach();
}

void Connection::stop() {
    is_open_ = false;
    if (socket_fd_ >= 0) {
        close(socket_fd_);
        socket_fd_ = -1;
    }
}

bool Connection::send_frame(const Frame& frame) {
    std::lock_guard<std::mutex> lock(write_mutex_);

    auto data = const_cast<Frame&>(frame).serialize();
    ssize_t sent = 0;
    while (sent < static_cast<ssize_t>(data.size())) {
        ssize_t n = send(socket_fd_, data.data() + sent, data.size() - sent, 0);
        if (n <= 0) {
            return false;
        }
        sent += n;
    }

    return true;
}

void Connection::send_response(std::shared_ptr<HttpResponse> response) {
    auto stream = stream_manager_.get_stream(response->get_stream_id());
    if (!stream) {
        return;
    }

    // 编码响应头
    std::vector<HeaderField> header_fields;
    header_fields.push_back({":status", std::to_string(response->get_status_code())});

    for (const auto& header : response->get_headers()) {
        header_fields.push_back({header.first, header.second});
    }

    auto header_block = hpack_encoder_.encode(header_fields);

    // 发送 HEADERS 帧
    bool end_stream = response->get_body_size() == 0 && !response->is_streaming();
    HeadersFrame headers_frame(response->get_stream_id(), header_block, end_stream, true);
    send_frame(headers_frame);

    // 发送 DATA 帧
    if (response->get_body_size() > 0) {
        const auto& body = response->get_body();
        size_t offset = 0;
        size_t max_frame_size = peer_settings_.max_frame_size;

        while (offset < body.size()) {
            size_t chunk_size = std::min(body.size() - offset, static_cast<size_t>(max_frame_size));
            std::vector<uint8_t> chunk(body.begin() + offset, body.begin() + offset + chunk_size);
            offset += chunk_size;

            bool is_last = (offset >= body.size()) && !response->is_streaming();
            DataFrame data_frame(response->get_stream_id(), chunk, is_last);
            send_frame(data_frame);
        }
    }

    stream->send_headers(end_stream);
}

void Connection::receive_loop() {
    std::vector<uint8_t> buffer(16384);

    while (is_open_) {
        ssize_t n = recv(socket_fd_, buffer.data(), buffer.size(), 0);
        if (n <= 0) {
            if (n == 0) {
                // 连接关闭
                is_open_ = false;
            } else {
                // 错误
                handle_error(ErrorCode::INTERNAL_ERROR, "Receive error");
            }
            break;
        }

        read_buffer_.insert(read_buffer_.end(), buffer.begin(), buffer.begin() + n);

        // 处理所有完整的帧
        while (read_buffer_.size() >= 9) {
            auto header = FrameHeader::deserialize(read_buffer_.data());

            if (read_buffer_.size() < 9 + header.length) {
                break;  // 等待更多数据
            }

            process_frame(header, read_buffer_.data() + 9);
            read_buffer_.erase(read_buffer_.begin(), read_buffer_.begin() + 9 + header.length);
        }
    }
}

void Connection::process_frame(const FrameHeader& header, const uint8_t* payload) {
    switch (header.type) {
        case FrameType::DATA:
            handle_data_frame(header, payload);
            break;
        case FrameType::HEADERS:
            handle_headers_frame(header, payload);
            break;
        case FrameType::SETTINGS:
            handle_settings_frame(header, payload);
            break;
        case FrameType::WINDOW_UPDATE:
            handle_window_update_frame(header, payload);
            break;
        case FrameType::PING:
            handle_ping_frame(header, payload);
            break;
        case FrameType::GOAWAY:
            handle_goaway_frame(header, payload);
            break;
        case FrameType::RST_STREAM:
            handle_rst_stream_frame(header, payload);
            break;
        case FrameType::PRIORITY:
            handle_priority_frame(header, payload);
            break;
        default:
            // 忽略未知帧类型
            break;
    }
}

void Connection::handle_data_frame(const FrameHeader& header, const uint8_t* payload) {
    auto stream = stream_manager_.get_stream(header.stream_id);
    if (!stream) {
        handle_error(ErrorCode::PROTOCOL_ERROR, "Data frame for unknown stream");
        return;
    }

    // 检查流量控制
    if (!stream->consume_recv_window(header.length)) {
        handle_error(ErrorCode::FLOW_CONTROL_ERROR, "Flow control error");
        return;
    }

    // 发送 WINDOW_UPDATE
    send_window_update(0, header.length);  // 连接级别
    send_window_update(header.stream_id, header.length);  // 流级别

    bool end_stream = (header.flags & static_cast<uint8_t>(FrameFlag::END_STREAM)) != 0;
    stream->recv_data(end_stream);

    // 如果结束流，处理请求
    if (end_stream) {
        // 这里应该已经收到了头部，现在处理完整请求
        // 实际实现中需要存储头部信息
    }
}

void Connection::handle_headers_frame(const FrameHeader& header, const uint8_t* payload) {
    auto stream = stream_manager_.get_stream(header.stream_id);
    if (!stream) {
        stream = stream_manager_.create_stream(header.stream_id);
        if (!stream) {
            handle_error(ErrorCode::REFUSED_STREAM, "Too many concurrent streams");
            return;
        }
    }

    // 解码头部
    auto headers = hpack_encoder_.decode(payload, header.length);

    bool end_stream = (header.flags & static_cast<uint8_t>(FrameFlag::END_STREAM)) != 0;
    bool end_headers = (header.flags & static_cast<uint8_t>(FrameFlag::END_HEADERS)) != 0;

    stream->recv_headers(end_stream);

    if (end_headers && is_server_) {
        // 处理请求
        process_request(stream, headers, {}, end_stream);
    }
}

void Connection::handle_settings_frame(const FrameHeader& header, const uint8_t* payload) {
    if (header.stream_id != 0) {
        handle_error(ErrorCode::PROTOCOL_ERROR, "Settings frame must be on stream 0");
        return;
    }

    // ACK 标志
    if (header.flags & 0x01) {
        // 设置确认，不做处理
        return;
    }

    // 解析设置
    for (size_t i = 0; i < header.length; i += 6) {
        uint16_t id = (static_cast<uint16_t>(payload[i]) << 8) | payload[i + 1];
        uint32_t value = (static_cast<uint32_t>(payload[i + 2]) << 24) |
                        (static_cast<uint32_t>(payload[i + 3]) << 16) |
                        (static_cast<uint32_t>(payload[i + 4]) << 8) |
                        static_cast<uint32_t>(payload[i + 5]);

        switch (static_cast<SettingsFrame::SettingId>(id)) {
            case SettingsFrame::SettingId::HEADER_TABLE_SIZE:
                peer_settings_.header_table_size = value;
                hpack_encoder_.set_max_dynamic_table_size(value);
                break;
            case SettingsFrame::SettingId::ENABLE_PUSH:
                peer_settings_.enable_push = value;
                break;
            case SettingsFrame::SettingId::MAX_CONCURRENT_STREAMS:
                peer_settings_.max_concurrent_streams = value;
                break;
            case SettingsFrame::SettingId::INITIAL_WINDOW_SIZE:
                peer_settings_.initial_window_size = value;
                stream_manager_.update_all_windows(value - 65535);
                break;
            case SettingsFrame::SettingId::MAX_FRAME_SIZE:
                peer_settings_.max_frame_size = value;
                break;
            case SettingsFrame::SettingId::MAX_HEADER_LIST_SIZE:
                peer_settings_.max_header_list_size = value;
                break;
        }
    }

    // 发送确认
    send_settings_ack();
}

void Connection::handle_window_update_frame(const FrameHeader& header, const uint8_t* payload) {
    uint32_t increment = (static_cast<uint32_t>(payload[0] & 0x7F) << 24) |
                        (static_cast<uint32_t>(payload[1]) << 16) |
                        (static_cast<uint32_t>(payload[2]) << 8) |
                        static_cast<uint32_t>(payload[3]);

    if (increment == 0) {
        handle_error(ErrorCode::PROTOCOL_ERROR, "Window update increment is 0");
        return;
    }

    if (header.stream_id == 0) {
        // 连接级别窗口更新
        stream_manager_.update_all_windows(increment);
    } else {
        // 流级别窗口更新
        auto stream = stream_manager_.get_stream(header.stream_id);
        if (stream) {
            stream->update_send_window(increment);
        }
    }
}

void Connection::handle_ping_frame(const FrameHeader& header, const uint8_t* payload) {
    if (header.length != 8) {
        handle_error(ErrorCode::FRAME_SIZE_ERROR, "Ping frame must be 8 bytes");
        return;
    }

    bool ack = (header.flags & 0x01) != 0;
    if (!ack) {
        // 回复 PING
        uint64_t ping_data = 0;
        for (int i = 0; i < 8; ++i) {
            ping_data = (ping_data << 8) | payload[i];
        }
        PingFrame ping_frame(ping_data, true);
        send_frame(ping_frame);
    }
}

void Connection::handle_goaway_frame(const FrameHeader& header, const uint8_t* payload) {
    is_open_ = false;
    // 处理关闭
}

void Connection::handle_rst_stream_frame(const FrameHeader& header, const uint8_t* payload) {
    auto stream = stream_manager_.get_stream(header.stream_id);
    if (stream) {
        stream->recv_rst_stream();
        stream_manager_.close_stream(header.stream_id);
    }
}

void Connection::handle_priority_frame(const FrameHeader& header, const uint8_t* payload) {
    // 简化处理
}

void Connection::send_connection_preface() {
    // 客户端发送前言
    const char* preface = "PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n";
    send(socket_fd_, preface, 24, 0);
    send_settings();
}

void Connection::send_settings() {
    SettingsFrame settings_frame;
    settings_frame.add_setting(SettingsFrame::SettingId::HEADER_TABLE_SIZE, settings_.header_table_size);
    settings_frame.add_setting(SettingsFrame::SettingId::ENABLE_PUSH, settings_.enable_push);
    settings_frame.add_setting(SettingsFrame::SettingId::MAX_CONCURRENT_STREAMS, settings_.max_concurrent_streams);
    settings_frame.add_setting(SettingsFrame::SettingId::INITIAL_WINDOW_SIZE, settings_.initial_window_size);
    settings_frame.add_setting(SettingsFrame::SettingId::MAX_FRAME_SIZE, settings_.max_frame_size);
    settings_frame.add_setting(SettingsFrame::SettingId::MAX_HEADER_LIST_SIZE, settings_.max_header_list_size);

    send_frame(settings_frame);
}

void Connection::send_settings_ack() {
    SettingsFrame ack_frame;
    ack_frame.header.flags = 0x01;  // ACK 标志
    send_frame(ack_frame);
}

void Connection::process_request(std::shared_ptr<Stream> stream,
                                const std::vector<HeaderField>& headers,
                                const std::vector<uint8_t>& body,
                                bool end_stream) {
    auto request = std::make_shared<HttpRequest>();
    auto response = std::make_shared<HttpResponse>();

    request->set_stream_id(stream->get_id());
    response->set_stream_id(stream->get_id());

    // 解析头部
    for (const auto& header : headers) {
        if (header.name == ":method") {
            request->set_method(header.value);
        } else if (header.name == ":path") {
            size_t query_pos = header.value.find('?');
            if (query_pos != std::string::npos) {
                request->set_path(header.value.substr(0, query_pos));
                request->set_query(header.value.substr(query_pos + 1));
                request->parse_query_string();
            } else {
                request->set_path(header.value);
            }
        } else if (header.name == ":authority") {
            request->set_header("host", header.value);
        } else if (header.name == ":scheme") {
            // 忽略 scheme
        } else {
            request->set_header(header.name, header.value);
        }
    }

    request->set_body(body);

    // 调用请求处理器
    if (request_handler_) {
        request_handler_(request, response);
        send_response(response);
    }
}

void Connection::send_window_update(uint32_t stream_id, uint32_t increment) {
    WindowUpdateFrame frame(stream_id, increment);
    send_frame(frame);
}

void Connection::send_goaway(ErrorCode error_code, const std::string& debug_data) {
    GoAwayFrame frame(0, error_code, debug_data);
    send_frame(frame);
}

void Connection::handle_error(ErrorCode error_code, const std::string& message) {
    std::cerr << "Connection error: " << message << std::endl;
    send_goaway(error_code, message);
    is_open_ = false;
}

} // namespace http2
