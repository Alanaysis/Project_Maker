/**
 * @file session_manager.cpp
 * @brief 会话管理器实现
 */

#include "streaming/session/session_manager.hpp"
#include "streaming/monitor/logger.hpp"

namespace streaming {

// ============================================================================
// Session 实现
// ============================================================================

Session::Session(uint64_t session_id, SessionType type, ProtocolType protocol) {
    info_ = std::make_shared<SessionInfo>();
    info_->session_id = session_id;
    info_->type = type;
    info_->protocol = protocol;
    info_->state = SessionState::Created;
    info_->create_time = std::chrono::steady_clock::now();
    info_->last_active = info_->create_time;
}

Session::~Session() = default;

void Session::set_state(SessionState state) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->state = state;

    if (state_callback_) {
        state_callback_(info_->session_id, state);
    }
}

void Session::set_client_info(const std::string& ip, uint16_t port) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->client_ip = ip;
    info_->client_port = port;
}

void Session::set_stream_name(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->stream_name = name;
}

void Session::set_app_name(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->app_name = name;
}

void Session::set_media_params(const MediaParams& params) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->media_params = params;
}

void Session::update_bytes_sent(uint64_t bytes) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->bytes_sent += bytes;
    info_->last_active = std::chrono::steady_clock::now();
}

void Session::update_bytes_received(uint64_t bytes) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->bytes_received += bytes;
    info_->last_active = std::chrono::steady_clock::now();
}

void Session::update_frames_sent(uint64_t count) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->frames_sent += count;
}

void Session::update_frames_received(uint64_t count) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->frames_received += count;
}

void Session::update_frames_dropped(uint64_t count) {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->frames_dropped += count;
}

void Session::update_activity() {
    std::lock_guard<std::mutex> lock(mutex_);
    info_->last_active = std::chrono::steady_clock::now();
}

bool Session::is_active(std::chrono::seconds timeout) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
        now - info_->last_active
    );
    return elapsed < timeout;
}

// ============================================================================
// SessionManager 实现
// ============================================================================

SessionManager::SessionManager() = default;
SessionManager::~SessionManager() {
    stop_cleanup_thread();
}

bool SessionManager::initialize(uint32_t max_sessions, std::chrono::seconds session_timeout) {
    max_sessions_ = max_sessions;
    session_timeout_ = session_timeout;

    LOG_INFO("SessionManager initialized: max_sessions=" + std::to_string(max_sessions) +
             ", timeout=" + std::to_string(session_timeout.count()) + "s");
    return true;
}

std::shared_ptr<Session> SessionManager::create_session(SessionType type, ProtocolType protocol) {
    if (is_full()) {
        LOG_WARN("Session limit reached");
        return nullptr;
    }

    uint64_t session_id = next_session_id_++;
    auto session = std::make_shared<Session>(session_id, type, protocol);

    {
        std::lock_guard<std::mutex> lock(sessions_mutex_);
        sessions_[session_id] = session;
    }

    active_sessions_++;

    if (session_created_callback_) {
        session_created_callback_(session);
    }

    LOG_DEBUG("Session created: " + std::to_string(session_id));
    return session;
}

std::shared_ptr<Session> SessionManager::get_session(uint64_t session_id) const {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    auto it = sessions_.find(session_id);
    return (it != sessions_.end()) ? it->second : nullptr;
}

void SessionManager::remove_session(uint64_t session_id) {
    std::shared_ptr<Session> session;

    {
        std::lock_guard<std::mutex> lock(sessions_mutex_);
        auto it = sessions_.find(session_id);
        if (it == sessions_.end()) {
            return;
        }

        session = it->second;
        sessions_.erase(it);
    }

    active_sessions_--;

    if (session_removed_callback_) {
        session_removed_callback_(session);
    }

    LOG_DEBUG("Session removed: " + std::to_string(session_id));
}

std::vector<std::shared_ptr<Session>> SessionManager::get_all_sessions() const {
    std::lock_guard<std::mutex> lock(sessions_mutex_);

    std::vector<std::shared_ptr<Session>> result;
    result.reserve(sessions_.size());

    for (const auto& [id, session] : sessions_) {
        result.push_back(session);
    }

    return result;
}

std::vector<std::shared_ptr<Session>> SessionManager::get_sessions_by_stream(
    const std::string& stream_name) const {

    std::lock_guard<std::mutex> lock(sessions_mutex_);

    std::vector<std::shared_ptr<Session>> result;

    for (const auto& [id, session] : sessions_) {
        if (session->get_info()->stream_name == stream_name) {
            result.push_back(session);
        }
    }

    return result;
}

std::vector<std::shared_ptr<Session>> SessionManager::get_sessions_by_state(
    SessionState state) const {

    std::lock_guard<std::mutex> lock(sessions_mutex_);

    std::vector<std::shared_ptr<Session>> result;

    for (const auto& [id, session] : sessions_) {
        if (session->get_state() == state) {
            result.push_back(session);
        }
    }

    return result;
}

uint32_t SessionManager::get_session_count() const {
    std::lock_guard<std::mutex> lock(sessions_mutex_);
    return static_cast<uint32_t>(sessions_.size());
}

uint32_t SessionManager::get_active_session_count() const {
    return active_sessions_;
}

bool SessionManager::is_full() const {
    return sessions_.size() >= max_sessions_;
}

uint32_t SessionManager::cleanup_timeout_sessions() {
    std::vector<uint64_t> timeout_ids;

    {
        std::lock_guard<std::mutex> lock(sessions_mutex_);

        for (const auto& [id, session] : sessions_) {
            if (!session->is_active(session_timeout_)) {
                timeout_ids.push_back(id);
            }
        }
    }

    for (uint64_t id : timeout_ids) {
        remove_session(id);
    }

    if (!timeout_ids.empty()) {
        LOG_INFO("Cleaned up " + std::to_string(timeout_ids.size()) + " timeout sessions");
    }

    return static_cast<uint32_t>(timeout_ids.size());
}

void SessionManager::close_all_sessions() {
    std::vector<std::shared_ptr<Session>> sessions;

    {
        std::lock_guard<std::mutex> lock(sessions_mutex_);
        for (const auto& [id, session] : sessions_) {
            sessions.push_back(session);
        }
        sessions_.clear();
    }

    for (auto& session : sessions) {
        session->set_state(SessionState::Disconnected);
    }

    active_sessions_ = 0;
    LOG_INFO("All sessions closed");
}

void SessionManager::start_cleanup_thread() {
    if (cleanup_running_) return;

    cleanup_running_ = true;
    cleanup_thread_ = std::thread(&SessionManager::cleanup_loop, this);

    LOG_INFO("Session cleanup thread started");
}

void SessionManager::stop_cleanup_thread() {
    cleanup_running_ = false;

    if (cleanup_thread_.joinable()) {
        cleanup_thread_.join();
    }

    LOG_INFO("Session cleanup thread stopped");
}

void SessionManager::cleanup_loop() {
    while (cleanup_running_) {
        cleanup_timeout_sessions();

        // 每 30 秒检查一次
        std::this_thread::sleep_for(std::chrono::seconds(30));
    }
}

} // namespace streaming
