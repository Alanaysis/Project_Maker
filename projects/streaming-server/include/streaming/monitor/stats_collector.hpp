#pragma once

/**
 * @file stats_collector.hpp
 * @brief 统计收集器
 *
 * 实现服务器和流的统计信息收集，支持：
 * - 流量监控
 * - 质量统计
 * - 性能指标
 * - 历史数据
 */

#include "streaming/types.hpp"
#include <string>
#include <vector>
#include <deque>
#include <unordered_map>
#include <mutex>
#include <thread>
#include <atomic>
#include <functional>
#include <chrono>

namespace streaming {

// 统计时间粒度
enum class StatsGranularity {
    Second,
    Minute,
    Hour,
    Day
};

// 统计指标类型
enum class MetricType {
    Counter,        // 计数器（只增不减）
    Gauge,          // 仪表（可增可减）
    Histogram,      // 直方图
    Summary         // 摘要
};

// 统计指标
struct Metric {
    std::string name;
    MetricType type = MetricType::Counter;
    double value = 0.0;
    double min_value = 0.0;
    double max_value = 0.0;
    double avg_value = 0.0;
    uint64_t count = 0;
    Timestamp last_update;
};

// 流质量指标
struct StreamQualityMetrics {
    std::string stream_name;

    // 视频质量
    double video_bitrate = 0.0;         // bps
    double video_framerate = 0.0;       // fps
    uint32_t video_width = 0;
    uint32_t video_height = 0;
    double video_buffer_level = 0.0;    // 秒
    uint64_t video_frames_total = 0;
    uint64_t video_frames_dropped = 0;
    double video_frame_loss_rate = 0.0;

    // 音频质量
    double audio_bitrate = 0.0;
    double audio_sample_rate = 0;
    uint32_t audio_channels = 0;

    // 网络质量
    double latency = 0.0;               // 毫秒
    double jitter = 0.0;                // 毫秒
    double packet_loss_rate = 0.0;
    double bandwidth = 0.0;             // bps

    // 播放质量
    double rebuffer_count = 0;
    double rebuffer_duration = 0.0;     // 秒
    double startup_delay = 0.0;         // 秒
    double quality_score = 0.0;         // 0-100

    Timestamp last_update;
};

// 服务器性能指标
struct ServerPerformanceMetrics {
    // CPU
    double cpu_usage = 0.0;             // 百分比
    uint32_t cpu_cores = 0;

    // 内存
    double memory_usage = 0.0;          // 百分比
    uint64_t memory_total = 0;          // 字节
    uint64_t memory_used = 0;
    uint64_t memory_available = 0;

    // 网络
    double network_bandwidth_in = 0.0;  // bps
    double network_bandwidth_out = 0.0;
    uint64_t network_bytes_in = 0;
    uint64_t network_bytes_out = 0;

    // 磁盘
    double disk_usage = 0.0;
    uint64_t disk_total = 0;
    uint64_t disk_used = 0;
    double disk_io_read = 0.0;          // bytes/sec
    double disk_io_write = 0.0;

    // 线程
    uint32_t thread_count = 0;
    uint32_t thread_active = 0;

    Timestamp last_update;
};

/**
 * @brief 指标收集器
 */
class MetricsCollector {
public:
    MetricsCollector();
    ~MetricsCollector();

    /**
     * @brief 注册指标
     */
    void register_metric(const std::string& name, MetricType type);

    /**
     * @brief 更新指标值
     */
    void update_metric(const std::string& name, double value);

    /**
     * @brief 增加计数器
     */
    void increment_counter(const std::string& name, double value = 1.0);

    /**
     * @brief 获取指标值
     */
    double get_metric_value(const std::string& name) const;

    /**
     * @brief 获取指标
     */
    Metric get_metric(const std::string& name) const;

    /**
     * @brief 获取所有指标
     */
    std::vector<Metric> get_all_metrics() const;

    /**
     * @brief 重置指标
     */
    void reset_metric(const std::string& name);

    /**
     * @brief 重置所有指标
     */
    void reset_all();

private:
    std::unordered_map<std::string, Metric> metrics_;
    mutable std::mutex mutex_;
};

/**
 * @brief 时间序列数据存储
 */
class TimeSeriesStore {
public:
    TimeSeriesStore(StatsGranularity granularity = StatsGranularity::Minute,
                   uint32_t max_points = 1440);  // 默认保存一天的分钟数据
    ~TimeSeriesStore();

    /**
     * @brief 添加数据点
     */
    void add_point(double value, Timestamp timestamp = std::chrono::steady_clock::now());

    /**
     * @brief 获取最近的数据点
     */
    std::vector<std::pair<Timestamp, double>> get_recent(uint32_t count) const;

    /**
     * @brief 获取时间范围内的数据
     */
    std::vector<std::pair<Timestamp, double>> get_range(Timestamp start, Timestamp end) const;

    /**
     * @brief 获取统计摘要
     */
    struct Summary {
        double min = 0.0;
        double max = 0.0;
        double avg = 0.0;
        double sum = 0.0;
        uint64_t count = 0;
    };
    Summary get_summary() const;

    /**
     * @brief 清空数据
     */
    void clear();

private:
    StatsGranularity granularity_;
    uint32_t max_points_;

    std::deque<std::pair<Timestamp, double>> data_;
    mutable std::mutex mutex_;
};

/**
 * @brief 流统计收集器
 */
class StreamStatsCollector {
public:
    StreamStatsCollector();
    ~StreamStatsCollector();

    /**
     * @brief 添加流
     */
    void add_stream(const std::string& stream_name);

    /**
     * @brief 移除流
     */
    void remove_stream(const std::string& stream_name);

    /**
     * @brief 更新流质量指标
     */
    void update_quality(const std::string& stream_name, const StreamQualityMetrics& metrics);

    /**
     * @brief 获取流质量指标
     */
    StreamQualityMetrics get_quality(const std::string& stream_name) const;

    /**
     * @brief 获取所有流的质量指标
     */
    std::vector<StreamQualityMetrics> get_all_quality() const;

    /**
     * @brief 更新流统计
     */
    void update_stream_stats(const std::string& stream_name,
                            uint64_t bytes_sent,
                            uint64_t bytes_received,
                            uint64_t frames_sent,
                            uint64_t frames_received);

    /**
     * @brief 获取流统计
     */
    StreamStats get_stream_stats(const std::string& stream_name) const;

private:
    std::unordered_map<std::string, StreamQualityMetrics> quality_metrics_;
    std::unordered_map<std::string, StreamStats> stream_stats_;
    mutable std::mutex mutex_;
};

/**
 * @brief 统计管理器
 *
 * 统一管理所有统计信息的收集和查询。
 */
class StatsManager {
public:
    StatsManager();
    ~StatsManager();

    /**
     * @brief 初始化统计管理器
     * @param collection_interval 采集间隔（秒）
     */
    bool initialize(uint32_t collection_interval = 1);

    /**
     * @brief 启动统计收集
     */
    void start();

    /**
     * @brief 停止统计收集
     */
    void stop();

    /**
     * @brief 获取指标收集器
     */
    MetricsCollector& get_metrics() { return metrics_; }

    /**
     * @brief 获取流统计收集器
     */
    StreamStatsCollector& get_stream_stats() { return stream_stats_; }

    /**
     * @brief 获取服务器性能指标
     */
    ServerPerformanceMetrics get_server_metrics() const;

    /**
     * @brief 更新服务器性能指标
     */
    void update_server_metrics(const ServerPerformanceMetrics& metrics);

    /**
     * @brief 获取统计报告
     */
    std::string generate_report() const;

    /**
     * @brief 导出统计为 JSON
     */
    std::string to_json() const;

    /**
     * @brief 设置报告回调
     */
    using ReportCallback = std::function<void(const std::string&)>;
    void set_report_callback(ReportCallback callback) { report_callback_ = std::move(callback); }

private:
    void collection_loop();
    void collect_server_metrics();

    uint32_t collection_interval_;
    MetricsCollector metrics_;
    StreamStatsCollector stream_stats_;
    ServerPerformanceMetrics server_metrics_;
    mutable std::mutex server_metrics_mutex_;

    std::thread collection_thread_;
    std::atomic<bool> running_{false};

    ReportCallback report_callback_;
};

} // namespace streaming
