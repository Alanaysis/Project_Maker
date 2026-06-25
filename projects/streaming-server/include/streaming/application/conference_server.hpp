#pragma once

/**
 * @file conference_server.hpp
 * @brief 视频会议服务器
 *
 * 实现视频会议服务器，支持：
 * - 多人音视频通话
 * - 屏幕共享
 * - 会议管理
 * - 录制功能
 */

#include "streaming/types.hpp"
#include "streaming/protocol/webrtc_server.hpp"
#include "streaming/session/session_manager.hpp"
#include "streaming/monitor/logger.hpp"

#include <string>
#include <memory>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>
#include <functional>

namespace streaming {

// 会议状态
enum class ConferenceState {
    Scheduled,
    Active,
    Ended,
    Cancelled
};

// 参与者角色
enum class ParticipantRole {
    Host,           // 主持人
    CoHost,         // 联合主持人
    Speaker,        // 发言人
    Attendee        // 参会者
};

// 参与者状态
enum class ParticipantState {
    Joining,
    Connected,
    AudioOnly,
    VideoOnly,
    Muted,
    Disconnected
};

// 参与者信息
struct ParticipantInfo {
    uint64_t session_id = 0;
    std::string user_id;
    std::string display_name;
    std::string avatar_url;
    ParticipantRole role = ParticipantRole::Attendee;
    ParticipantState state = ParticipantState::Joining;

    bool audio_enabled = true;
    bool video_enabled = true;
    bool screen_sharing = false;

    MediaParams media_params;
    Timestamp join_time;
    Timestamp last_active;

    // 网络质量
    double latency = 0.0;
    double packet_loss = 0.0;
    double bandwidth = 0.0;
};

using ParticipantInfoPtr = std::shared_ptr<ParticipantInfo>;

// 会议信息
struct ConferenceInfo {
    std::string conference_id;
    std::string title;
    std::string description;
    std::string host_user_id;
    std::string password;

    ConferenceState state = ConferenceState::Scheduled;
    Timestamp scheduled_start;
    Timestamp scheduled_end;
    Timestamp actual_start;
    Timestamp actual_end;

    uint32_t max_participants = 100;
    bool recording_enabled = false;
    bool waiting_room_enabled = false;
    bool mute_on_join = true;

    // 参与者
    std::vector<ParticipantInfoPtr> participants;

    // 统计
    uint32_t total_participants = 0;
    double total_duration = 0.0;
};

using ConferenceInfoPtr = std::shared_ptr<ConferenceInfo>;

/**
 * @brief 参与者管理器
 */
class ParticipantManager {
public:
    ParticipantManager();
    ~ParticipantManager();

    /**
     * @brief 添加参与者
     */
    ParticipantInfoPtr add_participant(const std::string& conference_id,
                                      const std::string& user_id,
                                      const std::string& display_name,
                                      ParticipantRole role = ParticipantRole::Attendee);

    /**
     * @brief 移除参与者
     */
    void remove_participant(const std::string& conference_id, uint64_t session_id);

    /**
     * @brief 获取参与者
     */
    ParticipantInfoPtr get_participant(const std::string& conference_id,
                                      uint64_t session_id) const;

    /**
     * @brief 获取会议的所有参与者
     */
    std::vector<ParticipantInfoPtr> get_participants(const std::string& conference_id) const;

    /**
     * @brief 更新参与者状态
     */
    void update_participant_state(const std::string& conference_id,
                                 uint64_t session_id,
                                 ParticipantState state);

    /**
     * @brief 切换音频
     */
    void toggle_audio(const std::string& conference_id, uint64_t session_id);

    /**
     * @brief 切换视频
     */
    void toggle_video(const std::string& conference_id, uint64_t session_id);

    /**
     * @brief 开始屏幕共享
     */
    void start_screen_sharing(const std::string& conference_id, uint64_t session_id);

    /**
     * @brief 停止屏幕共享
     */
    void stop_screen_sharing(const std::string& conference_id, uint64_t session_id);

private:
    std::unordered_map<std::string, std::vector<ParticipantInfoPtr>> participants_;
    mutable std::mutex mutex_;
};

/**
 * @brief 媒体混合器
 *
 * 将多个音视频流混合成一个流。
 */
class MediaMixer {
public:
    MediaMixer();
    ~MediaMixer();

    /**
     * @brief 初始化混合器
     * @param output_width 输出宽度
     * @param output_height 输出高度
     */
    bool initialize(uint32_t output_width, uint32_t output_height);

    /**
     * @brief 添加输入流
     */
    void add_input(uint64_t session_id, const MediaParams& params);

    /**
     * @brief 移除输入流
     */
    void remove_input(uint64_t session_id);

    /**
     * @brief 更新输入帧
     */
    void update_frame(uint64_t session_id, const MediaFrame& frame);

    /**
     * @brief 获取混合后的帧
     */
    MediaFramePtr get_mixed_frame();

    /**
     * @brief 设置布局
     */
    enum class Layout {
        Grid,           // 网格布局
        Speaker,        // 发言人为主
        Presentation    // 演示模式
    };
    void set_layout(Layout layout) { layout_ = layout; }

private:
    void mix_video();
    void mix_audio();

    struct InputInfo {
        MediaParams params;
        MediaFramePtr last_frame;
        bool active = false;
    };

    uint32_t output_width_ = 1920;
    uint32_t output_height_ = 1080;
    Layout layout_ = Layout::Grid;

    std::unordered_map<uint64_t, InputInfo> inputs_;
    Buffer mixed_buffer_;
    std::mutex mutex_;
};

/**
 * @brief 会议录制器
 */
class ConferenceRecorder {
public:
    ConferenceRecorder();
    ~ConferenceRecorder();

    /**
     * @brief 开始录制
     * @param conference_id 会议ID
     * @param output_path 输出路径
     */
    bool start_recording(const std::string& conference_id, const std::string& output_path);

    /**
     * @brief 停止录制
     */
    bool stop_recording(const std::string& conference_id);

    /**
     * @brief 是否正在录制
     */
    bool is_recording(const std::string& conference_id) const;

    /**
     * @brief 写入帧
     */
    void write_frame(const std::string& conference_id, const MediaFrame& frame);

private:
    struct RecordingInfo {
        std::string output_path;
        std::ofstream file;
        bool active = false;
        Timestamp start_time;
    };

    std::unordered_map<std::string, RecordingInfo> recordings_;
    mutable std::mutex mutex_;
};

/**
 * @brief 视频会议服务器
 */
class ConferenceServer {
public:
    ConferenceServer();
    ~ConferenceServer();

    /**
     * @brief 初始化会议服务器
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
     * @brief 创建会议
     * @param title 会议标题
     * @param host_user_id 主持人用户ID
     * @param scheduled_start 计划开始时间
     * @param scheduled_end 计划结束时间
     * @return 会议信息
     */
    ConferenceInfoPtr create_conference(const std::string& title,
                                       const std::string& host_user_id,
                                       Timestamp scheduled_start,
                                       Timestamp scheduled_end);

    /**
     * @brief 加入会议
     * @param conference_id 会议ID
     * @param user_id 用户ID
     * @param display_name 显示名称
     * @param password 会议密码
     * @return 参与者会话ID，0 表示失败
     */
    uint64_t join_conference(const std::string& conference_id,
                            const std::string& user_id,
                            const std::string& display_name,
                            const std::string& password = "");

    /**
     * @brief 离开会议
     */
    void leave_conference(const std::string& conference_id, uint64_t session_id);

    /**
     * @brief 结束会议
     */
    void end_conference(const std::string& conference_id);

    /**
     * @brief 获取会议信息
     */
    ConferenceInfoPtr get_conference(const std::string& conference_id) const;

    /**
     * @brief 获取所有会议
     */
    std::vector<ConferenceInfoPtr> get_all_conferences() const;

    /**
     * @brief 获取活跃会议
     */
    std::vector<ConferenceInfoPtr> get_active_conferences() const;

    /**
     * @brief 开始录制
     */
    bool start_recording(const std::string& conference_id);

    /**
     * @brief 停止录制
     */
    bool stop_recording(const std::string& conference_id);

    /**
     * @brief 获取参与者管理器
     */
    ParticipantManager& get_participant_manager() { return participant_manager_; }

    /**
     * @brief 设置回调
     */
    using ConferenceCallback = std::function<void(const std::string&, ConferenceState)>;
    void set_conference_state_callback(ConferenceCallback callback) {
        conference_state_callback_ = std::move(callback);
    }

    using ParticipantCallback = std::function<void(const std::string&, uint64_t, ParticipantState)>;
    void set_participant_state_callback(ParticipantCallback callback) {
        participant_state_callback_ = std::move(callback);
    }

private:
    void on_participant_frame(const std::string& conference_id,
                             uint64_t session_id,
                             MediaFramePtr frame);

    void conference_loop(const std::string& conference_id);

    ServerConfig config_;
    std::atomic<bool> running_{false};

    std::unique_ptr<WebRtcServer> webrtc_server_;
    std::unique_ptr<SessionManager> session_manager_;

    ParticipantManager participant_manager_;
    ConferenceRecorder recorder_;
    std::unordered_map<std::string, std::unique_ptr<MediaMixer>> mixers_;

    std::unordered_map<std::string, ConferenceInfoPtr> conferences_;
    mutable std::mutex conferences_mutex_;

    std::unordered_map<std::string, std::thread> conference_threads_;

    ConferenceCallback conference_state_callback_;
    ParticipantCallback participant_state_callback_;

    std::shared_ptr<Logger> logger_;
};

} // namespace streaming
