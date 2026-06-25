#pragma once

/**
 * @file live_server.hpp
 * @brief 直播服务器
 *
 * 实现直播流媒体服务器，支持：
 * - 推流/拉流
 * - 多协议输出
 * - 流录制
 * - 弹幕/聊天
 */

#include "streaming/types.hpp"
#include "streaming/protocol/rtmp_server.hpp"
#include "streaming/protocol/hls_server.hpp"
#include "streaming/session/session_manager.hpp"
#include "streaming/monitor/stats_collector.hpp"
#include "streaming/monitor/logger.hpp"

#include <string>
#include <memory>
#include <unordered_map>
#include <vector>
#include <mutex>
#include <thread>
#include <atomic>
#include <functional>

namespace streaming {

// 直播流状态
enum class LiveStreamState {
    Idle,
    Preparing,
    Live,
    Paused,
    Ended
};

// 直播流信息
struct LiveStreamInfo {
    std::string stream_name;
    std::string stream_key;
    std::string title;
    std::string description;
    std::string category;
    std::string thumbnail_url;

    LiveStreamState state = LiveStreamState::Idle;
    MediaParams media_params;

    Timestamp start_time;
    Timestamp end_time;
    uint32_t viewer_count = 0;
    uint32_t max_viewers = 0;
    uint32_t like_count = 0;

    // 推流信息
    std::string publisher_ip;
    uint64_t publisher_session_id = 0;

    // 统计
    StreamStats stats;
    StreamQualityMetrics quality;
};

using LiveStreamInfoPtr = std::shared_ptr<LiveStreamInfo>;

/**
 * @brief 直播流管理器
 */
class LiveStreamManager {
public:
    LiveStreamManager();
    ~LiveStreamManager();

    /**
     * @brief 创建直播流
     * @param stream_name 流名称
     * @param stream_key 流密钥
     * @return 流信息
     */
    LiveStreamInfoPtr create_stream(const std::string& stream_name,
                                   const std::string& stream_key);

    /**
     * @brief 开始推流
     * @param stream_name 流名称
     * @param session_id 推流会话ID
     * @return 是否成功
     */
    bool start_publish(const std::string& stream_name, uint64_t session_id);

    /**
     * @brief 停止推流
     */
    bool stop_publish(const std::string& stream_name);

    /**
     * @brief 获取流信息
     */
    LiveStreamInfoPtr get_stream(const std::string& stream_name) const;

    /**
     * @brief 获取所有直播流
     */
    std::vector<LiveStreamInfoPtr> get_all_streams() const;

    /**
     * @brief 获取正在直播的流
     */
    std::vector<LiveStreamInfoPtr> get_live_streams() const;

    /**
     * @brief 添加观看者
     */
    bool add_viewer(const std::string& stream_name, uint64_t session_id);

    /**
     * @brief 移除观看者
     */
    void remove_viewer(const std::string& stream_name, uint64_t session_id);

    /**
     * @brief 更新流统计
     */
    void update_stats(const std::string& stream_name, const StreamStats& stats);

    /**
     * @brief 删除流
     */
    void delete_stream(const std::string& stream_name);

private:
    std::unordered_map<std::string, LiveStreamInfoPtr> streams_;
    std::unordered_map<std::string, std::vector<uint64_t>> viewers_;
    mutable std::mutex mutex_;
};

/**
 * @brief 聊天/弹幕系统
 */
class ChatSystem {
public:
    ChatSystem();
    ~ChatSystem();

    /**
     * @brief 发送消息
     * @param stream_name 流名称
     * @param user 用户名
     * @param message 消息内容
     */
    void send_message(const std::string& stream_name,
                     const std::string& user,
                     const std::string& message);

    /**
     * @brief 获取消息历史
     */
    struct ChatMessage {
        std::string user;
        std::string message;
        Timestamp time;
        std::string stream_name;
    };
    std::vector<ChatMessage> get_history(const std::string& stream_name, uint32_t count = 50);

    /**
     * @brief 订阅消息
     */
    using MessageCallback = std::function<void(const ChatMessage&)>;
    void subscribe(const std::string& stream_name, uint64_t session_id, MessageCallback callback);

    /**
     * @brief 取消订阅
     */
    void unsubscribe(const std::string& stream_name, uint64_t session_id);

private:
    struct StreamChat {
        std::deque<ChatMessage> history;
        std::unordered_map<uint64_t, MessageCallback> subscribers;
    };

    std::unordered_map<std::string, std::unique_ptr<StreamChat>> chats_;
    std::mutex mutex_;
};

/**
 * @brief 直播服务器
 */
class LiveServer {
public:
    LiveServer();
    ~LiveServer();

    /**
     * @brief 初始化直播服务器
     * @param config 服务器配置
     */
    bool initialize(const ServerConfig& config);

    /**
     * @brief 启动服务器
     */
    bool start();

    /**
     * @brief 停止服务器
     */
    void stop();

    /**
     * @brief 是否运行中
     */
    bool is_running() const { return running_; }

    /**
     * @brief 获取流管理器
     */
    LiveStreamManager& get_stream_manager() { return stream_manager_; }

    /**
     * @brief 获取聊天系统
     */
    ChatSystem& get_chat_system() { return chat_system_; }

    /**
     * @brief 获取统计管理器
     */
    StatsManager& get_stats_manager() { return stats_manager_; }

    /**
     * @brief 获取在线用户数
     */
    uint32_t get_online_users() const;

    /**
     * @brief 获取直播流数量
     */
    uint32_t get_live_stream_count() const;

    /**
     * @brief 获取服务器信息
     */
    std::string get_server_info() const;

    /**
     * @brief 设置回调
     */
    using StreamCallback = std::function<void(const std::string&, LiveStreamState)>;
    void set_stream_state_callback(StreamCallback callback) {
        stream_state_callback_ = std::move(callback);
    }

private:
    // RTMP 回调处理
    void on_rtmp_frame(const std::string& stream_name, MediaFramePtr frame);
    void on_rtmp_connect(uint64_t session_id, bool connected);

    // 流状态更新
    void update_streams();

    ServerConfig config_;
    std::atomic<bool> running_{false};

    // 服务器组件
    std::unique_ptr<RtmpServer> rtmp_server_;
    std::unique_ptr<HlsServer> hls_server_;
    std::unique_ptr<SessionManager> session_manager_;

    // 管理器
    LiveStreamManager stream_manager_;
    ChatSystem chat_system_;
    StatsManager stats_manager_;

    // 线程
    std::thread update_thread_;

    // 回调
    StreamCallback stream_state_callback_;

    std::shared_ptr<Logger> logger_;
};

} // namespace streaming
