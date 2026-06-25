#pragma once

/**
 * @file session_manager.hpp
 * @brief 会话管理器
 *
 * 实现客户端会话管理，支持：
 * - 会话创建和销毁
 * - 会话状态跟踪
 * - 会话超时处理
 * - 会话统计
 */

#include "streaming/types.hpp"
#include <string>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>
#include <functional>

namespace streaming {

// 会话状态
enum class SessionState {
    Created,
    Authenticating,
    Connected,
    Streaming,
    Paused,
    Disconnecting,
    Disconnected,
    Error
};

// 会话类型
enum class SessionType {
    Publisher,      // 推流者
    Subscriber,     // 订阅者
    Bidirectional   // 双向
};

// 会话信息
struct SessionInfo {
    uint64_t session_id = 0;
    SessionType type = SessionType::Subscriber;
    SessionState state = SessionState::Created;
    ProtocolType protocol = ProtocolType::RTMP;

    std::string client_ip;
    uint16_t client_port = 0;
    std::string stream_name;
    std::string app_name;

    Timestamp create_time;
    Timestamp last_active;
    Timestamp start_streaming;

    // 统计
    uint64_t bytes_sent = 0;
    uint64_t bytes_received = 0;
    uint64_t frames_sent = 0;
    uint64_t frames_received = 0;
    uint64_t frames_dropped = 0;

    // 媒体参数
    MediaParams media_params;
};

using SessionInfoPtr = std::shared_ptr<SessionInfo>;

/**
 * @brief 会话
 *
 * 表示一个客户端会话。
 */
class Session {
public:
    Session(uint64_t session_id, SessionType type, ProtocolType protocol);
    ~Session();

    // 状态管理
    void set_state(SessionState state);
    SessionState get_state() const { return info_->state; }

    // 信息访问
    SessionInfoPtr get_info() const { return info_; }
    uint64_t get_id() const { return info_->session_id; }

    // 网络信息
    void set_client_info(const std::string& ip, uint16_t port);
    void set_stream_name(const std::string& name);
    void set_app_name(const std::string& name);

    // 媒体参数
    void set_media_params(const MediaParams& params);
    const MediaParams& get_media_params() const { return info_->media_params; }

    // 统计更新
    void update_bytes_sent(uint64_t bytes);
    void update_bytes_received(uint64_t bytes);
    void update_frames_sent(uint64_t count);
    void update_frames_received(uint64_t count);
    void update_frames_dropped(uint64_t count);

    // 活跃状态
    void update_activity();
    bool is_active(std::chrono::seconds timeout) const;

    // 回调
    using StateCallback = std::function<void(uint64_t, SessionState)>;
    void set_state_callback(StateCallback callback) { state_callback_ = std::move(callback); }

private:
    SessionInfoPtr info_;
    StateCallback state_callback_;
    mutable std::mutex mutex_;
};

/**
 * @brief 会话管理器
 *
 * 管理所有客户端会话的生命周期。
 */
class SessionManager {
public:
    SessionManager();
    ~SessionManager();

    /**
     * @brief 初始化会话管理器
     * @param max_sessions 最大会话数
     * @param session_timeout 会话超时时间
     */
    bool initialize(uint32_t max_sessions = 1000,
                   std::chrono::seconds session_timeout = std::chrono::seconds(300));

    /**
     * @brief 创建会话
     * @param type 会话类型
     * @param protocol 协议类型
     * @return 会话对象
     */
    std::shared_ptr<Session> create_session(SessionType type, ProtocolType protocol);

    /**
     * @brief 获取会话
     * @param session_id 会话ID
     * @return 会话对象
     */
    std::shared_ptr<Session> get_session(uint64_t session_id) const;

    /**
     * @brief 移除会话
     * @param session_id 会话ID
     */
    void remove_session(uint64_t session_id);

    /**
     * @brief 获取所有会话
     */
    std::vector<std::shared_ptr<Session>> get_all_sessions() const;

    /**
     * @brief 获取指定流的所有会话
     */
    std::vector<std::shared_ptr<Session>> get_sessions_by_stream(const std::string& stream_name) const;

    /**
     * @brief 获取指定状态的会话
     */
    std::vector<std::shared_ptr<Session>> get_sessions_by_state(SessionState state) const;

    /**
     * @brief 获取会话数量
     */
    uint32_t get_session_count() const;

    /**
     * @brief 获取活跃会话数量
     */
    uint32_t get_active_session_count() const;

    /**
     * @brief 检查是否达到最大会话数
     */
    bool is_full() const;

    /**
     * @brief 清理超时会话
     * @return 清理的会话数量
     */
    uint32_t cleanup_timeout_sessions();

    /**
     * @brief 关闭所有会话
     */
    void close_all_sessions();

    /**
     * @brief 设置会话回调
     */
    using SessionCallback = std::function<void(std::shared_ptr<Session>)>;
    void set_session_created_callback(SessionCallback callback) {
        session_created_callback_ = std::move(callback);
    }
    void set_session_removed_callback(SessionCallback callback) {
        session_removed_callback_ = std::move(callback);
    }

    /**
     * @brief 启动清理线程
     */
    void start_cleanup_thread();

    /**
     * @brief 停止清理线程
     */
    void stop_cleanup_thread();

private:
    void cleanup_loop();

    uint32_t max_sessions_;
    std::chrono::seconds session_timeout_;

    std::unordered_map<uint64_t, std::shared_ptr<Session>> sessions_;
    mutable std::mutex sessions_mutex_;

    std::atomic<uint64_t> next_session_id_{1};
    std::atomic<uint32_t> active_sessions_{0};

    SessionCallback session_created_callback_;
    SessionCallback session_removed_callback_;

    // 清理线程
    std::thread cleanup_thread_;
    std::atomic<bool> cleanup_running_{false};
};

} // namespace streaming
