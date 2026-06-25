#pragma once
/**
 * @file http2_connection.h
 * @brief HTTP/2 连接管理
 *
 * 连接管理包括：
 * - TCP 连接建立和维护
 * - TLS 握手（可选）
 * - HTTP/2 连接预face
 * - 连接复用
 * - 优雅关闭
 */

#include <cstdint>
#include <string>
#include <memory>
#include <functional>
#include <vector>
#include <map>
#include <mutex>
#include <atomic>

#include "http2_frame.h"
#include "http2_stream.h"
#include "http2_hpack.h"
#include "http2_request.h"
#include "http2_response.h"

namespace http2 {

// 连接设置
struct ConnectionSettings {
    uint32_t header_table_size = 4096;       // HPACK 动态表大小
    uint32_t enable_push = 0;                // 是否启用服务器推送
    uint32_t max_concurrent_streams = 100;   // 最大并发流数
    uint32_t initial_window_size = 65535;    // 初始窗口大小
    uint32_t max_frame_size = 16384;         // 最大帧大小
    uint32_t max_header_list_size = 8192;    // 最大头部列表大小
};

// 请求处理回调
using RequestHandler = std::function<void(std::shared_ptr<HttpRequest> request,
                                         std::shared_ptr<HttpResponse> response)>;

// 连接类
class Connection {
public:
    Connection(int socket_fd, bool is_server = true);
    ~Connection();

    // 设置请求处理器
    void set_request_handler(RequestHandler handler) { request_handler_ = handler; }

    // 启动连接
    void start();

    // 停止连接
    void stop();

    // 发送帧
    bool send_frame(const Frame& frame);

    // 发送响应
    void send_response(std::shared_ptr<HttpResponse> response);

    // 获取连接设置
    const ConnectionSettings& get_settings() const { return settings_; }

    // 获取对端设置
    const ConnectionSettings& get_peer_settings() const { return peer_settings_; }

    // 获取流管理器
    StreamManager& get_stream_manager() { return stream_manager_; }

    // 连接状态
    bool is_open() const { return is_open_; }
    bool is_server() const { return is_server_; }

    // 优雅关闭
    void shutdown(ErrorCode error_code = ErrorCode::NO_ERROR, const std::string& debug_data = "");

private:
    int socket_fd_;
    bool is_server_;
    std::atomic<bool> is_open_{false};

    ConnectionSettings settings_;
    ConnectionSettings peer_settings_;
    StreamManager stream_manager_;
    HPACKEncoder hpack_encoder_;

    RequestHandler request_handler_;

    std::mutex write_mutex_;
    std::vector<uint8_t> read_buffer_;

    // 接收循环
    void receive_loop();

    // 处理帧
    void process_frame(const FrameHeader& header, const uint8_t* payload);

    // 处理各种帧类型
    void handle_data_frame(const FrameHeader& header, const uint8_t* payload);
    void handle_headers_frame(const FrameHeader& header, const uint8_t* payload);
    void handle_settings_frame(const FrameHeader& header, const uint8_t* payload);
    void handle_window_update_frame(const FrameHeader& header, const uint8_t* payload);
    void handle_ping_frame(const FrameHeader& header, const uint8_t* payload);
    void handle_goaway_frame(const FrameHeader& header, const uint8_t* payload);
    void handle_rst_stream_frame(const FrameHeader& header, const uint8_t* payload);
    void handle_priority_frame(const FrameHeader& header, const uint8_t* payload);

    // 发送连接前言
    void send_connection_preface();

    // 发送设置帧
    void send_settings();

    // 发送设置确认
    void send_settings_ack();

    // 处理请求
    void process_request(std::shared_ptr<Stream> stream,
                        const std::vector<HeaderField>& headers,
                        const std::vector<uint8_t>& body,
                        bool end_stream);

    // 发送 WINDOW_UPDATE
    void send_window_update(uint32_t stream_id, uint32_t increment);

    // 发送 GOAWAY
    void send_goaway(ErrorCode error_code, const std::string& debug_data = "");

    // 错误处理
    void handle_error(ErrorCode error_code, const std::string& message);
};

} // namespace http2
