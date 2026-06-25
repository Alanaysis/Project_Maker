/**
 * @file conference_server.cpp
 * @brief 视频会议服务器实现（简化）
 */

#include "streaming/application/conference_server.hpp"
#include "streaming/monitor/logger.hpp"

namespace streaming {

// ============================================================================
// ParticipantManager 实现
// ============================================================================

ParticipantManager::ParticipantManager() = default;
ParticipantManager::~ParticipantManager() = default;

ParticipantInfoPtr ParticipantManager::add_participant(
    const std::string& conference_id,
    const std::string& user_id,
    const std::string& display_name,
    ParticipantRole role) {

    std::lock_guard<std::mutex> lock(mutex_);

    auto participant = std::make_shared<ParticipantInfo>();
    participant->user_id = user_id;
    participant->display_name = display_name;
    participant->role = role;
    participant->state = ParticipantState::Joining;
    participant->join_time = std::chrono::steady_clock::now();

    participants_[conference_id].push_back(participant);

    LOG_INFO("Participant added: " + display_name + " to conference " + conference_id);
    return participant;
}

void ParticipantManager::remove_participant(const std::string& conference_id, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto& list = participants_[conference_id];
    list.erase(
        std::remove_if(list.begin(), list.end(),
                      [session_id](const ParticipantInfoPtr& p) {
                          return p->session_id == session_id;
                      }),
        list.end()
    );

    LOG_INFO("Participant removed from conference " + conference_id);
}

ParticipantInfoPtr ParticipantManager::get_participant(
    const std::string& conference_id, uint64_t session_id) const {

    std::lock_guard<std::mutex> lock(mutex_);

    auto it = participants_.find(conference_id);
    if (it == participants_.end()) return nullptr;

    for (const auto& p : it->second) {
        if (p->session_id == session_id) {
            return p;
        }
    }

    return nullptr;
}

std::vector<ParticipantInfoPtr> ParticipantManager::get_participants(
    const std::string& conference_id) const {

    std::lock_guard<std::mutex> lock(mutex_);

    auto it = participants_.find(conference_id);
    return (it != participants_.end()) ? it->second : std::vector<ParticipantInfoPtr>{};
}

void ParticipantManager::update_participant_state(
    const std::string& conference_id,
    uint64_t session_id,
    ParticipantState state) {

    std::lock_guard<std::mutex> lock(mutex_);

    auto it = participants_.find(conference_id);
    if (it == participants_.end()) return;

    for (auto& p : it->second) {
        if (p->session_id == session_id) {
            p->state = state;
            break;
        }
    }
}

void ParticipantManager::toggle_audio(const std::string& conference_id, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = participants_.find(conference_id);
    if (it == participants_.end()) return;

    for (auto& p : it->second) {
        if (p->session_id == session_id) {
            p->audio_enabled = !p->audio_enabled;
            break;
        }
    }
}

void ParticipantManager::toggle_video(const std::string& conference_id, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = participants_.find(conference_id);
    if (it == participants_.end()) return;

    for (auto& p : it->second) {
        if (p->session_id == session_id) {
            p->video_enabled = !p->video_enabled;
            break;
        }
    }
}

void ParticipantManager::start_screen_sharing(const std::string& conference_id, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = participants_.find(conference_id);
    if (it == participants_.end()) return;

    for (auto& p : it->second) {
        if (p->session_id == session_id) {
            p->screen_sharing = true;
            break;
        }
    }
}

void ParticipantManager::stop_screen_sharing(const std::string& conference_id, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = participants_.find(conference_id);
    if (it == participants_.end()) return;

    for (auto& p : it->second) {
        if (p->session_id == session_id) {
            p->screen_sharing = false;
            break;
        }
    }
}

// ============================================================================
// ConferenceServer 实现
// ============================================================================

ConferenceServer::ConferenceServer() = default;
ConferenceServer::~ConferenceServer() { stop(); }

bool ConferenceServer::initialize(const ServerConfig& config) {
    config_ = config;

    logger_ = LogManager::instance().get_logger("ConferenceServer");

    session_manager_ = std::make_unique<SessionManager>();
    session_manager_->initialize(config.max_connections);

    webrtc_server_ = std::make_unique<WebRtcServer>();
    webrtc_server_->set_frame_callback([this](MediaFramePtr frame) {
        // 处理帧
    });

    STREAMING_LOG_INFO(logger_, "ConferenceServer initialized");
    return true;
}

bool ConferenceServer::start() {
    if (!webrtc_server_->start(config_.host, config_.webrtc_port)) {
        STREAMING_LOG_ERROR(logger_, "Failed to start WebRTC server");
        return false;
    }

    running_ = true;

    STREAMING_LOG_INFO(logger_, "ConferenceServer started");
    return true;
}

void ConferenceServer::stop() {
    running_ = false;

    if (webrtc_server_) {
        webrtc_server_->stop();
    }

    // 停止所有会议
    for (auto& [id, thread] : conference_threads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    conference_threads_.clear();

    STREAMING_LOG_INFO(logger_, "ConferenceServer stopped");
}

ConferenceInfoPtr ConferenceServer::create_conference(
    const std::string& title,
    const std::string& host_user_id,
    Timestamp scheduled_start,
    Timestamp scheduled_end) {

    std::lock_guard<std::mutex> lock(conferences_mutex_);

    auto conference = std::make_shared<ConferenceInfo>();
    conference->conference_id = "conf_" + std::to_string(conferences_.size() + 1);
    conference->title = title;
    conference->host_user_id = host_user_id;
    conference->scheduled_start = scheduled_start;
    conference->scheduled_end = scheduled_end;
    conference->state = ConferenceState::Scheduled;

    conferences_[conference->conference_id] = conference;

    LOG_INFO("Conference created: " + conference->conference_id + " - " + title);
    return conference;
}

uint64_t ConferenceServer::join_conference(
    const std::string& conference_id,
    const std::string& user_id,
    const std::string& display_name,
    const std::string& password) {

    std::lock_guard<std::mutex> lock(conferences_mutex_);

    auto it = conferences_.find(conference_id);
    if (it == conferences_.end()) {
        LOG_ERROR("Conference not found: " + conference_id);
        return 0;
    }

    auto conference = it->second;

    // 检查密码
    if (!conference->password.empty() && conference->password != password) {
        LOG_ERROR("Invalid password for conference: " + conference_id);
        return 0;
    }

    // 检查人数限制
    if (conference->participants.size() >= conference->max_participants) {
        LOG_ERROR("Conference is full: " + conference_id);
        return 0;
    }

    // 确定角色
    ParticipantRole role = ParticipantRole::Attendee;
    if (user_id == conference->host_user_id) {
        role = ParticipantRole::Host;
    }

    // 添加参与者
    auto participant = participant_manager_.add_participant(
        conference_id, user_id, display_name, role
    );

    static uint64_t next_session_id = 1;
    uint64_t session_id = next_session_id++;
    participant->session_id = session_id;

    conference->participants.push_back(participant);
    conference->total_participants++;

    // 如果是第一个参与者，启动会议
    if (conference->state == ConferenceState::Scheduled) {
        conference->state = ConferenceState::Active;
        conference->actual_start = std::chrono::steady_clock::now();

        // 启动会议处理线程
        conference_threads_[conference_id] = std::thread(
            &ConferenceServer::conference_loop, this, conference_id
        );

        if (conference_state_callback_) {
            conference_state_callback_(conference_id, ConferenceState::Active);
        }
    }

    if (participant_state_callback_) {
        participant_state_callback_(conference_id, session_id, ParticipantState::Connected);
    }

    LOG_INFO("User joined conference: " + display_name + " -> " + conference_id);
    return session_id;
}

void ConferenceServer::leave_conference(const std::string& conference_id, uint64_t session_id) {
    std::lock_guard<std::mutex> lock(conferences_mutex_);

    auto it = conferences_.find(conference_id);
    if (it == conferences_.end()) return;

    auto& participants = it->second->participants;
    participants.erase(
        std::remove_if(participants.begin(), participants.end(),
                      [session_id](const ParticipantInfoPtr& p) {
                          return p->session_id == session_id;
                      }),
        participants.end()
    );

    participant_manager_.remove_participant(conference_id, session_id);

    // 如果没有参与者了，结束会议
    if (participants.empty()) {
        end_conference(conference_id);
    }

    LOG_INFO("User left conference: " + conference_id);
}

void ConferenceServer::end_conference(const std::string& conference_id) {
    auto it = conferences_.find(conference_id);
    if (it == conferences_.end()) return;

    it->second->state = ConferenceState::Ended;
    it->second->actual_end = std::chrono::steady_clock::now();

    if (it->second->actual_start.time_since_epoch().count() > 0) {
        it->second->total_duration = std::chrono::duration_cast<std::chrono::seconds>(
            it->second->actual_end - it->second->actual_start
        ).count();
    }

    // 停止录制
    recorder_.stop_recording(conference_id);

    // 停止会议线程
    auto thread_it = conference_threads_.find(conference_id);
    if (thread_it != conference_threads_.end()) {
        if (thread_it->second.joinable()) {
            thread_it->second.join();
        }
        conference_threads_.erase(thread_it);
    }

    if (conference_state_callback_) {
        conference_state_callback_(conference_id, ConferenceState::Ended);
    }

    LOG_INFO("Conference ended: " + conference_id);
}

ConferenceInfoPtr ConferenceServer::get_conference(const std::string& conference_id) const {
    std::lock_guard<std::mutex> lock(conferences_mutex_);

    auto it = conferences_.find(conference_id);
    return (it != conferences_.end()) ? it->second : nullptr;
}

std::vector<ConferenceInfoPtr> ConferenceServer::get_all_conferences() const {
    std::lock_guard<std::mutex> lock(conferences_mutex_);

    std::vector<ConferenceInfoPtr> result;
    for (const auto& [id, conf] : conferences_) {
        result.push_back(conf);
    }
    return result;
}

std::vector<ConferenceInfoPtr> ConferenceServer::get_active_conferences() const {
    std::lock_guard<std::mutex> lock(conferences_mutex_);

    std::vector<ConferenceInfoPtr> result;
    for (const auto& [id, conf] : conferences_) {
        if (conf->state == ConferenceState::Active) {
            result.push_back(conf);
        }
    }
    return result;
}

bool ConferenceServer::start_recording(const std::string& conference_id) {
    return recorder_.start_recording(conference_id, config_.recording_path + "/" + conference_id);
}

bool ConferenceServer::stop_recording(const std::string& conference_id) {
    return recorder_.stop_recording(conference_id);
}

void ConferenceServer::on_participant_frame(
    const std::string& conference_id,
    uint64_t session_id,
    MediaFramePtr frame) {

    // 转发给其他参与者
    auto it = mixers_.find(conference_id);
    if (it != mixers_.end()) {
        it->second->update_frame(session_id, *frame);
    }

    // 录制
    if (recorder_.is_recording(conference_id)) {
        recorder_.write_frame(conference_id, *frame);
    }
}

void ConferenceServer::conference_loop(const std::string& conference_id) {
    while (running_) {
        auto conf = get_conference(conference_id);
        if (!conf || conf->state != ConferenceState::Active) {
            break;
        }

        // 检查是否超过计划结束时间
        auto now = std::chrono::steady_clock::now();
        if (conf->scheduled_end.time_since_epoch().count() > 0 && now >= conf->scheduled_end) {
            end_conference(conference_id);
            break;
        }

        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

} // namespace streaming
