#pragma once
/**
 * @file http2_stream.h
 * @brief HTTP/2 流管理
 *
 * HTTP/2 连接可以包含多个并发流，每个流有独立的状态和流量控制。
 *
 * 流状态：
 * - idle: 初始状态
 * - open: 流已打开
 * - reserved (local/remote): 服务器推送预留
 * - half-closed (local/remote): 半关闭状态
 * - closed: 流已关闭
 *
 * 流量控制：
 * - 基于窗口的流量控制
 * - 连接级别和流级别的流量控制
 * - WINDOW_UPDATE 帧更新窗口大小
 */

#include <cstdint>
#include <string>
#include <map>
#include <memory>
#include <functional>
#include <vector>
#include <queue>
#include <mutex>

namespace http2 {

// 流状态
enum class StreamState {
    IDLE,           // 空闲
    OPEN,           // 打开
    RESERVED_LOCAL, // 本地预留（服务器推送）
    RESERVED_REMOTE,// 远程预留
    HALF_CLOSED_LOCAL,  // 本地半关闭
    HALF_CLOSED_REMOTE, // 远程半关闭
    CLOSED          // 关闭
};

// 流优先级
struct StreamPriority {
    uint32_t weight = 16;      // 权重（1-256）
    uint32_t dependency = 0;   // 依赖流
    bool exclusive = false;     // 独占依赖
};

// 流类
class Stream {
public:
    Stream(uint32_t stream_id, uint32_t initial_window_size = 65535);

    // 获取流 ID
    uint32_t get_id() const { return id_; }

    // 获取流状态
    StreamState get_state() const { return state_; }

    // 设置流状态
    void set_state(StreamState state) { state_ = state; }

    // 流量控制
    int32_t get_send_window() const { return send_window_; }
    int32_t get_recv_window() const { return recv_window_; }
    void update_send_window(int32_t delta) { send_window_ += delta; }
    void update_recv_window(int32_t delta) { recv_window_ += delta; }
    bool consume_send_window(int32_t bytes);
    bool consume_recv_window(int32_t bytes);

    // 优先级
    void set_priority(const StreamPriority& priority) { priority_ = priority; }
    const StreamPriority& get_priority() const { return priority_; }

    // 数据缓冲
    void add_send_data(const std::vector<uint8_t>& data);
    std::vector<uint8_t> get_send_data(size_t max_size);

    // 状态转换
    void send_headers(bool end_stream = false);
    void recv_headers(bool end_stream = false);
    void send_data(bool end_stream = false);
    void recv_data(bool end_stream = false);
    void send_rst_stream();
    void recv_rst_stream();

private:
    uint32_t id_;
    StreamState state_;
    int32_t send_window_;
    int32_t recv_window_;
    StreamPriority priority_;

    std::queue<std::vector<uint8_t>> send_buffer_;
    std::mutex mutex_;
};

// 流管理器
class StreamManager {
public:
    StreamManager(uint32_t initial_window_size = 65535);

    // 创建新流
    std::shared_ptr<Stream> create_stream(uint32_t stream_id);

    // 获取流
    std::shared_ptr<Stream> get_stream(uint32_t stream_id);

    // 关闭流
    void close_stream(uint32_t stream_id);

    // 获取所有活跃流
    std::vector<std::shared_ptr<Stream>> get_active_streams() const;

    // 获取活跃流数量
    size_t get_active_stream_count() const;

    // 检查是否可以创建新流
    bool can_create_stream() const;

    // 设置最大并发流数
    void set_max_concurrent_streams(uint32_t max_streams) {
        max_concurrent_streams_ = max_streams;
    }

    // 获取下一个客户端流 ID
    uint32_t get_next_client_stream_id() {
        return next_client_stream_id_ += 2;
    }

    // 获取下一个服务器流 ID
    uint32_t get_next_server_stream_id() {
        return next_server_stream_id_ += 2;
    }

    // 更新所有流的窗口大小
    void update_all_windows(int32_t delta);

private:
    std::map<uint32_t, std::shared_ptr<Stream>> streams_;
    mutable std::mutex mutex_;
    uint32_t initial_window_size_;
    uint32_t max_concurrent_streams_ = 100;
    uint32_t next_client_stream_id_ = 1;   // 奇数
    uint32_t next_server_stream_id_ = 2;   // 偶数
};

} // namespace http2
