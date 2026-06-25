/**
 * @file vod_server.cpp
 * @brief 点播服务器实现
 */

#include "streaming/application/vod_server.hpp"
#include "streaming/monitor/logger.hpp"

#include <filesystem>
#include <random>

namespace streaming {

// ============================================================================
// VideoManager 实现
// ============================================================================

VideoManager::VideoManager() = default;
VideoManager::~VideoManager() = default;

bool VideoManager::initialize(const std::string& storage_path) {
    storage_path_ = storage_path;

    try {
        std::filesystem::create_directories(storage_path);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Failed to create storage path: " + std::string(e.what()));
        return false;
    }
}

VideoInfoPtr VideoManager::upload_video(const std::string& title, const std::string& file_path) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto video = std::make_shared<VideoInfo>();
    video->video_id = generate_video_id();
    video->title = title;
    video->file_path = file_path;
    video->status = VideoStatus::Uploading;
    video->upload_time = std::chrono::steady_clock::now();

    // 获取文件大小
    try {
        video->file_size = std::filesystem::file_size(file_path);
    } catch (...) {
        video->file_size = 0;
    }

    videos_[video->video_id] = video;

    LOG_INFO("Video uploaded: " + video->video_id + " - " + title);
    return video;
}

VideoInfoPtr VideoManager::get_video(const std::string& video_id) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = videos_.find(video_id);
    return (it != videos_.end()) ? it->second : nullptr;
}

std::vector<VideoInfoPtr> VideoManager::get_all_videos() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<VideoInfoPtr> result;
    for (const auto& [id, video] : videos_) {
        result.push_back(video);
    }
    return result;
}

std::vector<VideoInfoPtr> VideoManager::search_videos(const std::string& keyword) const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<VideoInfoPtr> result;
    for (const auto& [id, video] : videos_) {
        if (video->title.find(keyword) != std::string::npos ||
            video->description.find(keyword) != std::string::npos) {
            result.push_back(video);
        }
    }
    return result;
}

bool VideoManager::delete_video(const std::string& video_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = videos_.find(video_id);
    if (it == videos_.end()) {
        return false;
    }

    // 删除文件
    try {
        std::filesystem::remove(it->second->file_path);
    } catch (...) {
        // 忽略错误
    }

    videos_.erase(it);
    LOG_INFO("Video deleted: " + video_id);
    return true;
}

bool VideoManager::update_video(const VideoInfoPtr& video) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = videos_.find(video->video_id);
    if (it == videos_.end()) {
        return false;
    }

    it->second = video;
    return true;
}

bool VideoManager::start_transcode(const std::string& video_id,
                                    const std::vector<TranscodeConfig>& configs) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = videos_.find(video_id);
    if (it == videos_.end()) {
        return false;
    }

    it->second->status = VideoStatus::Processing;
    it->second->transcode_configs = configs;

    // 启动转码线程（简化）
    transcode_progress_[video_id] = 0.0;

    LOG_INFO("Transcode started: " + video_id);
    return true;
}

double VideoManager::get_transcode_progress(const std::string& video_id) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = transcode_progress_.find(video_id);
    return (it != transcode_progress_.end()) ? it->second : 0.0;
}

void VideoManager::record_view(const std::string& video_id, uint64_t watch_time) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = videos_.find(video_id);
    if (it != videos_.end()) {
        it->second->view_count++;
        it->second->total_watch_time += watch_time;
    }
}

std::string VideoManager::generate_video_id() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(0, 15);

    std::string id;
    for (int i = 0; i < 16; ++i) {
        id += "0123456789abcdef"[dist(gen)];
    }
    return id;
}

bool VideoManager::process_video(VideoInfoPtr video, const std::vector<TranscodeConfig>& configs) {
    // 转码处理（简化）
    video->status = VideoStatus::Ready;
    return true;
}

// ============================================================================
// PlaybackSession 实现
// ============================================================================

PlaybackSession::PlaybackSession(uint64_t session_id, const std::string& video_id)
    : session_id_(session_id), video_id_(video_id) {}

PlaybackSession::~PlaybackSession() = default;

bool PlaybackSession::start(double position) {
    playing_ = true;
    paused_ = false;
    current_position_ = position;
    start_time_ = std::chrono::steady_clock::now();

    LOG_INFO("Playback started: session=" + std::to_string(session_id_) +
             ", video=" + video_id_ + ", position=" + std::to_string(position));
    return true;
}

void PlaybackSession::pause() {
    paused_ = true;
}

void PlaybackSession::resume() {
    paused_ = false;
}

void PlaybackSession::stop() {
    playing_ = false;
    LOG_INFO("Playback stopped: session=" + std::to_string(session_id_));
}

bool PlaybackSession::seek(double position) {
    current_position_ = position;
    return true;
}

double PlaybackSession::get_position() const {
    if (!playing_ || paused_) {
        return current_position_;
    }

    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        now - start_time_
    );

    return current_position_ + elapsed.count() / 1000.0;
}

// ============================================================================
// VodServer 实现
// ============================================================================

VodServer::VodServer() = default;
VodServer::~VodServer() { stop(); }

bool VodServer::initialize(const ServerConfig& config) {
    config_ = config;

    logger_ = LogManager::instance().get_logger("VodServer");

    // 初始化视频管理器
    if (!video_manager_.initialize(config.recording_path)) {
        STREAMING_LOG_ERROR(logger_, "Failed to initialize VideoManager");
        return false;
    }

    // 初始化 HLS 服务器
    hls_server_ = std::make_unique<HlsServer>();
    hls_server_->set_output_path(config.hls_path);

    // 初始化 DASH 服务器
    dash_server_ = std::make_unique<DashServer>();
    dash_server_->set_output_path(config.dash_path);

    STREAMING_LOG_INFO(logger_, "VodServer initialized");
    return true;
}

bool VodServer::start() {
    // 启动 HLS 服务器
    if (config_.enable_hls) {
        if (!hls_server_->start(config_.host, config_.http_port)) {
            STREAMING_LOG_ERROR(logger_, "Failed to start HLS server");
            return false;
        }
    }

    // 启动 DASH 服务器
    if (config_.enable_dash) {
        if (!dash_server_->start(config_.host, config_.http_port + 1)) {
            STREAMING_LOG_ERROR(logger_, "Failed to start DASH server");
            return false;
        }
    }

    running_ = true;

    STREAMING_LOG_INFO(logger_, "VodServer started");
    return true;
}

void VodServer::stop() {
    running_ = false;

    if (hls_server_) {
        hls_server_->stop();
    }

    if (dash_server_) {
        dash_server_->stop();
    }

    STREAMING_LOG_INFO(logger_, "VodServer stopped");
}

std::string VodServer::upload_video(const std::string& title, const std::string& file_path) {
    auto video = video_manager_.upload_video(title, file_path);
    return video ? video->video_id : "";
}

std::vector<VideoInfoPtr> VodServer::get_video_list() const {
    return video_manager_.get_all_videos();
}

std::string VodServer::get_playback_url(const std::string& video_id, ProtocolType protocol) const {
    auto video = video_manager_.get_video(video_id);
    if (!video) return "";

    std::string base_url = "http://" + config_.host + ":" + std::to_string(config_.http_port);

    switch (protocol) {
        case ProtocolType::HLS:
            return base_url + "/" + video_id + "/playlist.m3u8";
        case ProtocolType::DASH:
            return base_url + "/" + video_id + "/manifest.mpd";
        default:
            return base_url + "/" + video_id;
    }
}

uint64_t VodServer::start_playback(const std::string& video_id, double position) {
    static uint64_t next_id = 1;
    uint64_t session_id = next_id++;

    auto session = std::make_unique<PlaybackSession>(session_id, video_id);
    session->start(position);

    std::lock_guard<std::mutex> lock(sessions_mutex_);
    playback_sessions_[session_id] = std::move(session);

    return session_id;
}

void VodServer::stop_playback(uint64_t session_id) {
    std::lock_guard<std::mutex> lock(sessions_mutex_);

    auto it = playback_sessions_.find(session_id);
    if (it != playback_sessions_.end()) {
        it->second->stop();
        playback_sessions_.erase(it);
    }
}

std::string VodServer::get_stats() const {
    std::ostringstream stats;
    stats << "VodServer Stats:\n";
    stats << "  Total Videos: " << video_manager_.get_all_videos().size() << "\n";
    stats << "  Active Sessions: " << playback_sessions_.size() << "\n";
    return stats.str();
}

void VodServer::on_playback_frame(uint64_t session_id, MediaFramePtr frame) {
    // 处理播放帧
}

} // namespace streaming
