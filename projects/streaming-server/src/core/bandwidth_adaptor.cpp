/**
 * @file bandwidth_adaptor.cpp
 * @brief 带宽自适应实现
 */

#include "streaming/core/bandwidth_adaptor.hpp"
#include "streaming/monitor/logger.hpp"

#include <algorithm>
#include <cmath>
#include <numeric>

namespace streaming {

// ============================================================================
// BandwidthEstimator 实现
// ============================================================================

BandwidthEstimator::BandwidthEstimator() = default;
BandwidthEstimator::~BandwidthEstimator() = default;

void BandwidthEstimator::record_packet(uint32_t size, Timestamp timestamp) {
    std::lock_guard<std::mutex> lock(mutex_);

    PacketInfo info;
    info.size = size;
    info.timestamp = timestamp;

    packet_history_.push_back(info);
    total_bytes_ += size;
    total_packets_++;

    // 限制历史记录大小
    while (packet_history_.size() > window_size_) {
        packet_history_.pop_front();
    }

    update_estimate();
}

void BandwidthEstimator::record_loss(uint32_t count) {
    std::lock_guard<std::mutex> lock(mutex_);
    lost_packets_ += count;
}

BandwidthEstimate BandwidthEstimator::get_estimate() const {
    std::lock_guard<std::mutex> lock(mutex_);

    BandwidthEstimate estimate;
    estimate.estimated_bandwidth = estimated_bandwidth_;
    estimate.confidence = std::min(1.0, total_packets_ / 100.0);
    estimate.timestamp = std::chrono::steady_clock::now();

    return estimate;
}

void BandwidthEstimator::reset() {
    std::lock_guard<std::mutex> lock(mutex_);

    packet_history_.clear();
    total_bytes_ = 0;
    total_packets_ = 0;
    lost_packets_ = 0;
    estimated_bandwidth_ = 0.0;
    jitter_ = 0.0;
}

void BandwidthEstimator::update_estimate() {
    if (packet_history_.size() < 2) {
        return;
    }

    // 计算接收速率
    auto first = packet_history_.front();
    auto last = packet_history_.back();

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        last.timestamp - first.timestamp
    );

    if (duration.count() > 0) {
        double rate = static_cast<double>(total_bytes_) * 8000.0 / duration.count();
        estimated_bandwidth_ = rate;
    }

    // 计算抖动
    jitter_ = calculate_inter_arrival_jitter();

    // 考虑丢包率
    if (total_packets_ > 0) {
        double loss_rate = static_cast<double>(lost_packets_) / total_packets_;
        estimated_bandwidth_ *= (1.0 - loss_rate);
    }
}

double BandwidthEstimator::calculate_inter_arrival_jitter() const {
    if (packet_history_.size() < 2) {
        return 0.0;
    }

    std::vector<double> intervals;
    for (size_t i = 1; i < packet_history_.size(); ++i) {
        auto interval = std::chrono::duration_cast<std::chrono::microseconds>(
            packet_history_[i].timestamp - packet_history_[i - 1].timestamp
        );
        intervals.push_back(interval.count());
    }

    if (intervals.empty()) return 0.0;

    double mean = std::accumulate(intervals.begin(), intervals.end(), 0.0) / intervals.size();

    double variance = 0.0;
    for (double interval : intervals) {
        double diff = interval - mean;
        variance += diff * diff;
    }
    variance /= intervals.size();

    return std::sqrt(variance);
}

// ============================================================================
// BufferEstimator 实现
// ============================================================================

BufferEstimator::BufferEstimator() = default;
BufferEstimator::~BufferEstimator() = default;

void BufferEstimator::update_buffer(uint64_t buffer_size, double playback_rate) {
    current_buffer_size_ = buffer_size;
    playback_rate_ = playback_rate;

    // 计算缓冲区健康度
    if (max_buffer_threshold_ > 0) {
        buffer_health_ = std::min(1.0, static_cast<double>(buffer_size) / max_buffer_threshold_);
    }

    // 低于最小阈值时降低健康度
    if (buffer_size < min_buffer_threshold_) {
        buffer_health_ *= 0.5;
    }
}

uint32_t BufferEstimator::get_suggested_bitrate() const {
    // 基于缓冲区状态建议码率
    double base_bitrate = 2000000.0;  // 2Mbps

    if (buffer_health_ > 0.8) {
        return static_cast<uint32_t>(base_bitrate * 1.5);
    } else if (buffer_health_ > 0.5) {
        return static_cast<uint32_t>(base_bitrate);
    } else if (buffer_health_ > 0.2) {
        return static_cast<uint32_t>(base_bitrate * 0.7);
    } else {
        return static_cast<uint32_t>(base_bitrate * 0.4);
    }
}

double BufferEstimator::get_buffer_health() const {
    return buffer_health_;
}

// ============================================================================
// AdaptiveBitrateController 实现
// ============================================================================

AdaptiveBitrateController::AdaptiveBitrateController() = default;
AdaptiveBitrateController::~AdaptiveBitrateController() = default;

void AdaptiveBitrateController::set_bitrate_levels(const std::vector<BitrateLevel>& levels) {
    levels_ = levels;

    // 按码率排序
    std::sort(levels_.begin(), levels_.end(),
              [](const BitrateLevel& a, const BitrateLevel& b) {
                  return a.bitrate < b.bitrate;
              });

    // 选择初始级别
    current_level_index_ = 0;
}

void AdaptiveBitrateController::update_network_state(
    const BandwidthEstimate& bandwidth_estimate,
    double buffer_health,
    double rtt) {

    bandwidth_estimate_ = bandwidth_estimate;
    buffer_health_ = buffer_health;
    rtt_ = rtt;

    // 评估拥塞状态
    evaluate_congestion();

    // 计算目标码率
    uint32_t target_bitrate = static_cast<uint32_t>(bandwidth_estimate.estimated_bandwidth * 0.7);

    // 考虑缓冲区健康度
    if (buffer_health < 0.3) {
        target_bitrate = static_cast<uint32_t>(target_bitrate * 0.5);
    } else if (buffer_health > 0.8) {
        target_bitrate = static_cast<uint32_t>(target_bitrate * 1.2);
    }

    // 找到最佳级别
    uint32_t best_index = find_best_level(target_bitrate);

    // 检查是否需要切换
    if (best_index != current_level_index_) {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(
            now - last_switch_time_
        );

        if (elapsed >= switch_cooldown_) {
            should_switch_ = true;
            current_level_index_ = best_index;
            last_switch_time_ = now;
        }
    }
}

const BitrateLevel& AdaptiveBitrateController::get_suggested_level() const {
    if (levels_.empty()) {
        static BitrateLevel default_level{2000000, 1280, 720, 30.0, "720p"};
        return default_level;
    }

    return levels_[current_level_index_];
}

bool AdaptiveBitrateController::should_switch() const {
    return should_switch_;
}

void AdaptiveBitrateController::evaluate_congestion() {
    // 基于带宽估计和 RTT 评估拥塞状态
    double loss_rate = 0.0;

    if (bandwidth_estimate_.estimated_bandwidth > 0) {
        // 简化的拥塞检测
        if (rtt_ > 200) {  // RTT > 200ms
            congestion_state_ = CongestionState::Congested;
            congestion_factor_ = 0.5;
        } else if (rtt_ > 100) {  // RTT > 100ms
            congestion_state_ = CongestionState::Warning;
            congestion_factor_ = 0.8;
        } else {
            congestion_state_ = CongestionState::Normal;
            congestion_factor_ = 1.0;
        }
    }

    should_switch_ = false;
}

uint32_t AdaptiveBitrateController::find_best_level(uint32_t target_bitrate) const {
    if (levels_.empty()) return 0;

    // 找到不超过目标码率的最高级别
    uint32_t best_index = 0;
    for (size_t i = 0; i < levels_.size(); ++i) {
        if (levels_[i].bitrate <= target_bitrate) {
            best_index = static_cast<uint32_t>(i);
        }
    }

    return best_index;
}

// ============================================================================
// CongestionController 实现
// ============================================================================

CongestionController::CongestionController() = default;
CongestionController::~CongestionController() = default;

void CongestionController::update(double rtt, double loss_rate) {
    rtt_ = rtt;
    loss_rate_ = loss_rate;

    // 更新最小 RTT
    if (rtt < min_rtt_) {
        min_rtt_ = rtt;
    }

    // 评估拥塞状态
    if (loss_rate > loss_threshold_) {
        state_ = CongestionState::Congested;
        decrease_window();
    } else if (rtt > min_rtt_ * 2) {
        state_ = CongestionState::Warning;
        // 轻微降低窗口
        congestion_window_ = static_cast<uint64_t>(congestion_window_ * 0.9);
    } else {
        state_ = CongestionState::Normal;
        increase_window();
    }

    last_update_ = std::chrono::steady_clock::now();
}

double CongestionController::get_send_rate() const {
    if (rtt_ <= 0) return 0.0;

    // 拥塞窗口 / RTT
    return congestion_window_ * 1000.0 / rtt_;
}

bool CongestionController::should_reduce_rate() const {
    return state_ == CongestionState::Congested || state_ == CongestionState::Warning;
}

void CongestionController::increase_window() {
    if (congestion_window_ < slow_start_threshold_) {
        // 慢启动阶段：指数增长
        congestion_window_ += 1024;
    } else {
        // 拥塞避免阶段：线性增长
        congestion_window_ += static_cast<uint64_t>(1024.0 * 1024.0 / congestion_window_);
    }

    // 限制最大窗口
    if (congestion_window_ > 1024 * 1024 * 10) {  // 10MB
        congestion_window_ = 1024 * 1024 * 10;
    }
}

void CongestionController::decrease_window() {
    // 乘法减少
    slow_start_threshold_ = congestion_window_ / 2;
    congestion_window_ = slow_start_threshold_;

    // 限制最小窗口
    if (congestion_window_ < 1024) {
        congestion_window_ = 1024;
    }
}

// ============================================================================
// BandwidthManager 实现
// ============================================================================

BandwidthManager::BandwidthManager() = default;
BandwidthManager::~BandwidthManager() = default;

void BandwidthManager::set_bitrate_levels(const std::vector<BitrateLevel>& levels) {
    abr_controller_.set_bitrate_levels(levels);
}

void BandwidthManager::update_network(uint32_t packet_size, Timestamp timestamp,
                                      uint32_t lost_packets, double rtt) {
    // 更新带宽估计器
    bandwidth_estimator_.record_packet(packet_size, timestamp);
    if (lost_packets > 0) {
        bandwidth_estimator_.record_loss(lost_packets);
    }

    // 获取带宽估计
    auto estimate = bandwidth_estimator_.get_estimate();

    // 更新缓冲区估计器
    // 这里需要外部提供缓冲区状态

    // 更新 ABR 控制器
    abr_controller_.update_network_state(estimate, buffer_estimator_.get_buffer_health(), rtt);

    // 更新拥塞控制器
    double loss_rate = 0.0;
    congestion_controller_.update(rtt, loss_rate);
}

void BandwidthManager::update_buffer(uint64_t buffer_size, double playback_rate) {
    buffer_estimator_.update_buffer(buffer_size, playback_rate);
}

uint32_t BandwidthManager::get_suggested_bitrate() const {
    return abr_controller_.get_suggested_level().bitrate;
}

const BitrateLevel& BandwidthManager::get_suggested_level() const {
    return abr_controller_.get_suggested_level();
}

bool BandwidthManager::should_switch_bitrate() const {
    return abr_controller_.should_switch();
}

CongestionState BandwidthManager::get_congestion_state() const {
    return abr_controller_.get_congestion_state();
}

double BandwidthManager::get_send_rate_limit() const {
    return congestion_controller_.get_send_rate();
}

} // namespace streaming
