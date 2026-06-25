#pragma once

/**
 * @file bandwidth_adaptor.hpp
 * @brief 带宽自适应
 *
 * 实现带宽自适应机制，支持：
 * - 码率检测
 * - 自适应码率切换
 * - 拥塞控制
 * - 缓冲区管理
 */

#include "streaming/types.hpp"
#include <string>
#include <vector>
#include <deque>
#include <mutex>
#include <chrono>

namespace streaming {

// 码率级别
struct BitrateLevel {
    uint32_t bitrate;       // bps
    uint32_t width;
    uint32_t height;
    double framerate;
    std::string name;       // 例如 "720p", "480p"
};

// 带宽估计结果
struct BandwidthEstimate {
    double estimated_bandwidth = 0.0;   // bps
    double confidence = 0.0;            // 0.0 - 1.0
    Timestamp timestamp;
};

// 拥塞状态
enum class CongestionState {
    Normal,
    Warning,
    Congested,
    Recovering
};

/**
 * @brief 带宽估计器
 *
 * 基于包间隔和丢包率估计可用带宽。
 */
class BandwidthEstimator {
public:
    BandwidthEstimator();
    ~BandwidthEstimator();

    /**
     * @brief 记录接收的数据包
     * @param size 数据包大小（字节）
     * @param timestamp 接收时间戳
     */
    void record_packet(uint32_t size, Timestamp timestamp);

    /**
     * @brief 记录丢包
     * @param count 丢包数量
     */
    void record_loss(uint32_t count);

    /**
     * @brief 获取带宽估计
     */
    BandwidthEstimate get_estimate() const;

    /**
     * @brief 重置估计器
     */
    void reset();

private:
    struct PacketInfo {
        uint32_t size;
        Timestamp timestamp;
    };

    void update_estimate();
    double calculate_inter_arrival_jitter() const;

    std::deque<PacketInfo> packet_history_;
    std::mutex mutex_;

    // 统计
    uint64_t total_bytes_ = 0;
    uint64_t total_packets_ = 0;
    uint64_t lost_packets_ = 0;

    // 带宽估计
    double estimated_bandwidth_ = 0.0;
    double jitter_ = 0.0;

    // 窗口大小
    size_t window_size_ = 100;
    std::chrono::seconds window_duration_{5};
};

/**
 * @brief 缓冲区估计器
 *
 * 基于播放缓冲区状态估计带宽需求。
 */
class BufferEstimator {
public:
    BufferEstimator();
    ~BufferEstimator();

    /**
     * @brief 更新缓冲区状态
     * @param buffer_size 当前缓冲区大小（字节）
     * @param playback_rate 播放速率（bytes/sec）
     */
    void update_buffer(uint64_t buffer_size, double playback_rate);

    /**
     * @brief 获取建议的码率
     * @return 建议的码率（bps）
     */
    uint32_t get_suggested_bitrate() const;

    /**
     * @brief 获取缓冲区健康状态
     * @return 0.0（危险）到 1.0（健康）
     */
    double get_buffer_health() const;

private:
    uint64_t current_buffer_size_ = 0;
    double playback_rate_ = 0.0;
    double buffer_health_ = 1.0;

    // 缓冲区阈值
    uint64_t min_buffer_threshold_ = 1024 * 100;    // 100KB
    uint64_t max_buffer_threshold_ = 1024 * 1024;   // 1MB
};

/**
 * @brief 自适应码率控制器
 *
 * 根据网络状况自动调整视频码率。
 */
class AdaptiveBitrateController {
public:
    AdaptiveBitrateController();
    ~AdaptiveBitrateController();

    /**
     * @brief 设置可用的码率级别
     */
    void set_bitrate_levels(const std::vector<BitrateLevel>& levels);

    /**
     * @brief 更新网络状况
     * @param bandwidth_estimate 带宽估计
     * @param buffer_health 缓冲区健康度
     * @param rtt 往返时间（毫秒）
     */
    void update_network_state(const BandwidthEstimate& bandwidth_estimate,
                             double buffer_health,
                             double rtt);

    /**
     * @brief 获取建议的码率级别
     */
    const BitrateLevel& get_suggested_level() const;

    /**
     * @brief 获取当前码率级别索引
     */
    uint32_t get_current_level_index() const { return current_level_index_; }

    /**
     * @brief 是否需要切换码率
     */
    bool should_switch() const;

    /**
     * @brief 获取拥塞状态
     */
    CongestionState get_congestion_state() const { return congestion_state_; }

private:
    void evaluate_congestion();
    uint32_t find_best_level(uint32_t target_bitrate) const;

    std::vector<BitrateLevel> levels_;
    uint32_t current_level_index_ = 0;

    // 网络状态
    BandwidthEstimate bandwidth_estimate_;
    double buffer_health_ = 1.0;
    double rtt_ = 0.0;

    // 拥塞控制
    CongestionState congestion_state_ = CongestionState::Normal;
    double congestion_factor_ = 1.0;

    // 切换控制
    bool should_switch_ = false;
    Timestamp last_switch_time_;
    std::chrono::seconds switch_cooldown_{5};
};

/**
 * @brief 拥塞控制器
 *
 * 实现基于 AIMD 的拥塞控制。
 */
class CongestionController {
public:
    CongestionController();
    ~CongestionController();

    /**
     * @brief 更新拥塞窗口
     * @param rtt 往返时间
     * @param loss_rate 丢包率
     */
    void update(double rtt, double loss_rate);

    /**
     * @brief 获取拥塞窗口大小（字节）
     */
    uint64_t get_congestion_window() const { return congestion_window_; }

    /**
     * @brief 获取发送速率（bytes/sec）
     */
    double get_send_rate() const;

    /**
     * @brief 是否应该降低发送速率
     */
    bool should_reduce_rate() const;

    /**
     * @brief 获取拥塞状态
     */
    CongestionState get_state() const { return state_; }

private:
    void increase_window();
    void decrease_window();

    uint64_t congestion_window_ = 65535;   // 初始窗口
    uint64_t slow_start_threshold_ = 65535;
    double rtt_ = 0.0;
    double min_rtt_ = 1e9;
    double loss_rate_ = 0.0;

    CongestionState state_ = CongestionState::Normal;

    // AIMD 参数
    double increase_factor_ = 1.0;
    double decrease_factor_ = 0.5;
    double loss_threshold_ = 0.02;     // 2% 丢包率阈值

    Timestamp last_update_;
};

/**
 * @brief 带宽管理器
 *
 * 统一管理带宽估计、自适应码率和拥塞控制。
 */
class BandwidthManager {
public:
    BandwidthManager();
    ~BandwidthManager();

    /**
     * @brief 设置码率级别
     */
    void set_bitrate_levels(const std::vector<BitrateLevel>& levels);

    /**
     * @brief 更新网络状态
     */
    void update_network(uint32_t packet_size, Timestamp timestamp,
                       uint32_t lost_packets, double rtt);

    /**
     * @brief 更新缓冲区状态
     */
    void update_buffer(uint64_t buffer_size, double playback_rate);

    /**
     * @brief 获取建议的码率
     */
    uint32_t get_suggested_bitrate() const;

    /**
     * @brief 获取建议的码率级别
     */
    const BitrateLevel& get_suggested_level() const;

    /**
     * @brief 是否需要切换码率
     */
    bool should_switch_bitrate() const;

    /**
     * @brief 获取拥塞状态
     */
    CongestionState get_congestion_state() const;

    /**
     * @brief 获取发送速率限制
     */
    double get_send_rate_limit() const;

private:
    BandwidthEstimator bandwidth_estimator_;
    BufferEstimator buffer_estimator_;
    AdaptiveBitrateController abr_controller_;
    CongestionController congestion_controller_;
};

} // namespace streaming
