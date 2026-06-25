#pragma once

/**
 * @file vod_server.hpp
 * @brief 点播服务器
 *
 * 实现视频点播服务器，支持：
 * - 视频文件管理
 * - 多码率转码
 * - 自适应播放
 * - 进度控制
 */

#include "streaming/types.hpp"
#include "streaming/protocol/hls_server.hpp"
#include "streaming/protocol/dash_server.hpp"
#include "streaming/session/session_manager.hpp"
#include "streaming/monitor/logger.hpp"

#include <string>
#include <memory>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <filesystem>

namespace streaming {

// 视频状态
enum class VideoStatus {
    Uploading,
    Processing,
    Ready,
    Error,
    Deleted
};

// 转码配置
struct TranscodeConfig {
    uint32_t width = 1280;
    uint32_t height = 720;
    uint32_t video_bitrate = 2000000;   // 2Mbps
    uint32_t audio_bitrate = 128000;    // 128kbps
    double framerate = 30.0;
    std::string video_codec = "h264";
    std::string audio_codec = "aac";
};

// 视频信息
struct VideoInfo {
    std::string video_id;
    std::string title;
    std::string description;
    std::string filename;
    std::string file_path;
    std::string thumbnail_path;

    VideoStatus status = VideoStatus::Uploading;
    MediaParams media_params;

    uint64_t file_size = 0;
    double duration = 0.0;

    Timestamp upload_time;
    Timestamp process_time;

    // 多码率版本
    std::vector<TranscodeConfig> transcode_configs;
    std::vector<std::string> hls_paths;
    std::vector<std::string> dash_paths;

    // 统计
    uint64_t view_count = 0;
    uint64_t total_watch_time = 0;  // 秒
};

using VideoInfoPtr = std::shared_ptr<VideoInfo>;

/**
 * @brief 视频管理器
 */
class VideoManager {
public:
    VideoManager();
    ~VideoManager();

    /**
     * @brief 初始化视频管理器
     * @param storage_path 存储路径
     */
    bool initialize(const std::string& storage_path);

    /**
     * @brief 上传视频
     * @param title 标题
     * @param file_path 文件路径
     * @return 视频信息
     */
    VideoInfoPtr upload_video(const std::string& title, const std::string& file_path);

    /**
     * @brief 获取视频信息
     */
    VideoInfoPtr get_video(const std::string& video_id) const;

    /**
     * @brief 获取所有视频
     */
    std::vector<VideoInfoPtr> get_all_videos() const;

    /**
     * @brief 搜索视频
     */
    std::vector<VideoInfoPtr> search_videos(const std::string& keyword) const;

    /**
     * @brief 删除视频
     */
    bool delete_video(const std::string& video_id);

    /**
     * @brief 更新视频信息
     */
    bool update_video(const VideoInfoPtr& video);

    /**
     * @brief 开始转码
     * @param video_id 视频ID
     * @param configs 转码配置
     * @return 是否成功
     */
    bool start_transcode(const std::string& video_id,
                        const std::vector<TranscodeConfig>& configs);

    /**
     * @brief 获取转码进度
     * @return 进度百分比 (0-100)
     */
    double get_transcode_progress(const std::string& video_id) const;

    /**
     * @brief 记录观看
     */
    void record_view(const std::string& video_id, uint64_t watch_time);

private:
    std::string generate_video_id();
    bool process_video(VideoInfoPtr video, const std::vector<TranscodeConfig>& configs);

    std::string storage_path_;
    std::unordered_map<std::string, VideoInfoPtr> videos_;
    std::unordered_map<std::string, double> transcode_progress_;
    mutable std::mutex mutex_;
};

/**
 * @brief 播放会话
 */
class PlaybackSession {
public:
    PlaybackSession(uint64_t session_id, const std::string& video_id);
    ~PlaybackSession();

    /**
     * @brief 开始播放
     * @param position 开始位置（秒）
     */
    bool start(double position = 0.0);

    /**
     * @brief 暂停播放
     */
    void pause();

    /**
     * @brief 恢复播放
     */
    void resume();

    /**
     * @brief 停止播放
     */
    void stop();

    /**
     * @brief 跳转
     * @param position 目标位置（秒）
     */
    bool seek(double position);

    /**
     * @brief 获取当前播放位置
     */
    double get_position() const;

    /**
     * @brief 获取播放状态
     */
    bool is_playing() const { return playing_; }

    /**
     * @brief 获取会话ID
     */
    uint64_t get_session_id() const { return session_id_; }

private:
    uint64_t session_id_;
    std::string video_id_;
    bool playing_ = false;
    bool paused_ = false;
    double current_position_ = 0.0;
    Timestamp start_time_;
};

/**
 * @brief 点播服务器
 */
class VodServer {
public:
    VodServer();
    ~VodServer();

    /**
     * @brief 初始化点播服务器
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
     * @brief 获取视频管理器
     */
    VideoManager& get_video_manager() { return video_manager_; }

    /**
     * @brief 上传视频
     */
    std::string upload_video(const std::string& title, const std::string& file_path);

    /**
     * @brief 获取视频列表
     */
    std::vector<VideoInfoPtr> get_video_list() const;

    /**
     * @brief 获取视频播放地址
     */
    std::string get_playback_url(const std::string& video_id, ProtocolType protocol) const;

    /**
     * @brief 开始播放会话
     */
    uint64_t start_playback(const std::string& video_id, double position = 0.0);

    /**
     * @brief 停止播放会话
     */
    void stop_playback(uint64_t session_id);

    /**
     * @brief 获取统计信息
     */
    std::string get_stats() const;

private:
    void on_playback_frame(uint64_t session_id, MediaFramePtr frame);

    ServerConfig config_;
    std::atomic<bool> running_{false};

    VideoManager video_manager_;
    std::unique_ptr<HlsServer> hls_server_;
    std::unique_ptr<DashServer> dash_server_;

    std::unordered_map<uint64_t, std::unique_ptr<PlaybackSession>> playback_sessions_;
    std::mutex sessions_mutex_;

    std::shared_ptr<Logger> logger_;
};

} // namespace streaming
