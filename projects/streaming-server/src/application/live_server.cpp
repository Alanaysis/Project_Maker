/**
 * @file live_server.cpp
 * @brief 直播服务器实现
 */

#include "streaming/application/live_server.hpp"
#include "streaming/monitor/logger.hpp"

namespace streaming {

// ============================================================================
// LiveStreamManager 实现
// ============================================================================

LiveStreamManager::LiveStreamManager() = default;
LiveStreamManager::~LiveStreamManager() = default;

LiveStreamInfoPtr LiveStreamManager::create_stream(const std::string& stream_name,
                                                    const std::string& stream_key) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (streams_.count(stream_name)) {
        LOG_WARN("Stream already exists: " + stream_name);
        return streams_[stream_name];
    }

    auto info = std::make_shared<LiveStreamInfo>();
    info->stream_name = stream_name;
    info->stream_key = stream_key;
    info->state = LiveStreamState::Idle;
    info->stats.start_time = std::chrono::steady_clock::now();

    streams_[stream_name] = info;
    viewers_[stream_name] = {};

    LOG_INFO("Stream created: " + stream_name);
    return info;
}

bool LiveStreamManager::start_publish(const std::string& stream_name, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = streams_.find(stream_name);
    if (it == streams_.end()) {
        LOG_ERROR("Stream not found: " + stream_name);
        return false;
    }

    it->second->state = LiveStreamState::Live;
    it->second->publisher_session_id = session_id;
    it->second->start_time = std::chrono::steady_clock::now();

    LOG_INFO("Stream started: " + stream_name + " by session " + std::to_string(session_id));
    return true;
}

bool LiveStreamManager::stop_publish(const std::string& stream_name) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = streams_.find(stream_name);
    if (it == streams_.end()) {
        return false;
    }

    it->second->state = LiveStreamState::Ended;
    it->second->end_time = std::chrono::steady_clock::now();

    LOG_INFO("Stream stopped: " + stream_name);
    return true;
}

LiveStreamInfoPtr LiveStreamManager::get_stream(const std::string& stream_name) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = streams_.find(stream_name);
    return (it != streams_.end()) ? it->second : nullptr;
}

std::vector<LiveStreamInfoPtr> LiveStreamManager::get_all_streams() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<LiveStreamInfoPtr> result;
    for (const auto& [name, info] : streams_) {
        result.push_back(info);
    }
    return result;
}

std::vector<LiveStreamInfoPtr> LiveStreamManager::get_live_streams() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<LiveStreamInfoPtr> result;
    for (const auto& [name, info] : streams_) {
        if (info->state == LiveStreamState::Live) {
            result.push_back(info);
        }
    }
    return result;
}

bool LiveStreamManager::add_viewer(const std::string& stream_name, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = streams_.find(stream_name);
    if (it == streams_.end()) {
        return false;
    }

    viewers_[stream_name].push_back(session_id);
    it->second->viewer_count = static_cast<uint32_t>(viewers_[stream_name].size());
    it->second->max_viewers = std::max(it->second->max_viewers, it->second->viewer_count);

    return true;
}

void LiveStreamManager::remove_viewer(const std::string& stream_name, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto& viewer_list = viewers_[stream_name];
    viewer_list.erase(
        std::remove(viewer_list.begin(), viewer_list.end(), session_id),
        viewer_list.end()
    );

    auto it = streams_.find(stream_name);
    if (it != streams_.end()) {
        it->second->viewer_count = static_cast<uint32_t>(viewer_list.size());
    }
}

void LiveStreamManager::update_stats(const std::string& stream_name, const StreamStats& stats) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = streams_.find(stream_name);
    if (it != streams_.end()) {
        it->second->stats = stats;
    }
}

void LiveStreamManager::delete_stream(const std::string& stream_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    streams_.erase(stream_name);
    viewers_.erase(stream_name);

    LOG_INFO("Stream deleted: " + stream_name);
}

// ============================================================================
// ChatSystem 实现
// ============================================================================

ChatSystem::ChatSystem() = default;
ChatSystem::~ChatSystem() = default;

void ChatSystem::send_message(const std::string& stream_name,
                              const std::string& user,
                              const std::string& message) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto& chat = chats_[stream_name];
    if (!chat) {
        chat = std::make_unique<StreamChat>();
    }

    ChatMessage msg;
    msg.user = user;
    msg.message = message;
    msg.time = std::chrono::steady_clock::now();
    msg.stream_name = stream_name;

    chat->history.push_back(msg);

    // 限制历史记录
    while (chat->history.size() > 100) {
        chat->history.pop_front();
    }

    // 通知订阅者
    for (const auto& [session_id, callback] : chat->subscribers) {
        if (callback) {
            callback(msg);
        }
    }
}

std::vector<ChatSystem::ChatMessage> ChatSystem::get_history(
    const std::string& stream_name, uint32_t count) {

    std::lock_guard<std::mutex> lock(mutex_);

    auto it = chats_.find(stream_name);
    if (it == chats_.end()) {
        return {};
    }

    auto& history = it->second->history;
    uint32_t start = (count < history.size()) ? history.size() - count : 0;

    return std::vector<ChatMessage>(history.begin() + start, history.end());
}

void ChatSystem::subscribe(const std::string& stream_name, uint64_t session_id,
                           MessageCallback callback) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto& chat = chats_[stream_name];
    if (!chat) {
        chat = std::make_unique<StreamChat>();
    }

    chat->subscribers[session_id] = std::move(callback);
}

void ChatSystem::unsubscribe(const std::string& stream_name, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = chats_.find(stream_name);
    if (it != chats_.end()) {
        it->second->subscribers.erase(session_id);
    }
}

// ============================================================================
// LiveServer 实现
// ============================================================================

LiveServer::LiveServer() = default;
LiveServer::~LiveServer() { stop(); }

bool LiveServer::initialize(const ServerConfig& config) {
    config_ = config;

    // 初始化日志
    logger_ = LogManager::instance().get_logger("LiveServer");

    // 初始化会话管理器
    session_manager_ = std::make_unique<SessionManager>();
    session_manager_->initialize(config.max_connections);

    // 初始化 RTMP 服务器
    rtmp_server_ = std::make_unique<RtmpServer>();
    rtmp_server_->set_frame_callback([this](MediaFramePtr frame) {
        // 处理接收到的帧
    });
    rtmp_server_->set_connection_callback([this](uint64_t session_id, bool connected) {
        on_rtmp_connect(session_id, connected);
    });

    // 初始化 HLS 服务器
    hls_server_ = std::make_unique<HlsServer>();
    hls_server_->set_output_path(config.hls_path);

    // 初始化统计管理器
    stats_manager_.initialize(1);

    STREAMING_LOG_INFO(logger_, "LiveServer initialized");
    return true;
}

bool LiveServer::start() {
    // 启动 RTMP 服务器
    if (!rtmp_server_->start(config_.host, config_.rtmp_port)) {
        STREAMING_LOG_ERROR(logger_, "Failed to start RTMP server");
        return false;
    }

    // 启动 HLS 服务器
    if (config_.enable_hls) {
        if (!hls_server_->start(config_.host, config_.http_port)) {
            STREAMING_LOG_ERROR(logger_, "Failed to start HLS server");
            return false;
        }
    }

    // 启动会话清理线程
    session_manager_->start_cleanup_thread();

    // 启动统计收集
    stats_manager_.start();

    // 启动流更新线程
    running_ = true;
    update_thread_ = std::thread(&LiveServer::update_streams, this);

    STREAMING_LOG_INFO(logger_, "LiveServer started");
    return true;
}

void LiveServer::stop() {
    running_ = false;

    if (update_thread_.joinable()) {
        update_thread_.join();
    }

    stats_manager_.stop();
    session_manager_->stop_cleanup_thread();

    if (rtmp_server_) {
        rtmp_server_->stop();
    }

    if (hls_server_) {
        hls_server_->stop();
    }

    STREAMING_LOG_INFO(logger_, "LiveServer stopped");
}

uint32_t LiveServer::get_online_users() const {
    return session_manager_->get_active_session_count();
}

uint32_t LiveServer::get_live_stream_count() const {
    return static_cast<uint32_t>(stream_manager_.get_live_streams().size());
}

std::string LiveServer::get_server_info() const {
    std::ostringstream info;
    info << "LiveServer Info:\n";
    info << "  Online Users: " << get_online_users() << "\n";
    info << "  Live Streams: " << get_live_stream_count() << "\n";
    info << "  RTMP Port: " << config_.rtmp_port << "\n";
    info << "  HTTP Port: " << config_.http_port << "\n";
    return info.str();
}

void LiveServer::on_rtmp_frame(const std::string& stream_name, MediaFramePtr frame) {
    // 转发到 HLS
    if (config_.enable_hls && hls_server_) {
        hls_server_->push_frame(stream_name, *frame);
    }
}

void LiveServer::on_rtmp_connect(uint64_t session_id, bool connected) {
    if (connected) {
        auto session = session_manager_->create_session(SessionType::Publisher, ProtocolType::RTMP);
        STREAMING_LOG_INFO(logger_, "Client connected: " + std::to_string(session_id));
    } else {
        session_manager_->remove_session(session_id);
        STREAMING_LOG_INFO(logger_, "Client disconnected: " + std::to_string(session_id));
    }
}

void LiveServer::update_streams() {
    while (running_) {
        // 更新流统计
        auto live_streams = stream_manager_.get_live_streams();
        for (const auto& stream : live_streams) {
            // 更新统计信息
            StreamStats stats;
            stats.viewers = stream->viewer_count;
            stats.uptime = std::chrono::steady_clock::now() - stream->start_time;
            stream_manager_.update_stats(stream->stream_name, stats);
        }

        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

} // namespace streaming
