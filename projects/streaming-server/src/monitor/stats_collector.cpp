/**
 * @file stats_collector.cpp
 * @brief 统计收集器实现
 */

#include "streaming/monitor/stats_collector.hpp"
#include "streaming/monitor/logger.hpp"

#include <sstream>
#include <iomanip>
#include <algorithm>

namespace streaming {

// ============================================================================
// MetricsCollector 实现
// ============================================================================

MetricsCollector::MetricsCollector() = default;
MetricsCollector::~MetricsCollector() = default;

void MetricsCollector::register_metric(const std::string& name, MetricType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    Metric metric;
    metric.name = name;
    metric.type = type;
    metric.last_update = std::chrono::steady_clock::now();

    metrics_[name] = metric;
}

void MetricsCollector::update_metric(const std::string& name, double value) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = metrics_.find(name);
    if (it == metrics_.end()) return;

    auto& metric = it->second;
    metric.value = value;
    metric.count++;
    metric.last_update = std::chrono::steady_clock::now();

    if (metric.count == 1) {
        metric.min_value = value;
        metric.max_value = value;
        metric.avg_value = value;
    } else {
        metric.min_value = std::min(metric.min_value, value);
        metric.max_value = std::max(metric.max_value, value);
        metric.avg_value = (metric.avg_value * (metric.count - 1) + value) / metric.count;
    }
}

void MetricsCollector::increment_counter(const std::string& name, double value) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = metrics_.find(name);
    if (it == metrics_.end()) return;

    it->second.value += value;
    it->second.count++;
    it->second.last_update = std::chrono::steady_clock::now();
}

double MetricsCollector::get_metric_value(const std::string& name) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = metrics_.find(name);
    if (it == metrics_.end()) return 0.0;

    return it->second.value;
}

Metric MetricsCollector::get_metric(const std::string& name) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = metrics_.find(name);
    if (it == metrics_.end()) {
        return Metric{};
    }

    return it->second;
}

std::vector<Metric> MetricsCollector::get_all_metrics() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<Metric> result;
    for (const auto& [name, metric] : metrics_) {
        result.push_back(metric);
    }
    return result;
}

void MetricsCollector::reset_metric(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = metrics_.find(name);
    if (it != metrics_.end()) {
        it->second.value = 0;
        it->second.count = 0;
        it->second.min_value = 0;
        it->second.max_value = 0;
        it->second.avg_value = 0;
    }
}

void MetricsCollector::reset_all() {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& [name, metric] : metrics_) {
        metric.value = 0;
        metric.count = 0;
        metric.min_value = 0;
        metric.max_value = 0;
        metric.avg_value = 0;
    }
}

// ============================================================================
// TimeSeriesStore 实现
// ============================================================================

TimeSeriesStore::TimeSeriesStore(StatsGranularity granularity, uint32_t max_points)
    : granularity_(granularity), max_points_(max_points) {}

TimeSeriesStore::~TimeSeriesStore() = default;

void TimeSeriesStore::add_point(double value, Timestamp timestamp) {
    std::lock_guard<std::mutex> lock(mutex_);

    data_.push_back({timestamp, value});

    while (data_.size() > max_points_) {
        data_.pop_front();
    }
}

std::vector<std::pair<Timestamp, double>> TimeSeriesStore::get_recent(uint32_t count) const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<std::pair<Timestamp, double>> result;
    uint32_t start = (count < data_.size()) ? data_.size() - count : 0;

    for (uint32_t i = start; i < data_.size(); ++i) {
        result.push_back(data_[i]);
    }

    return result;
}

std::vector<std::pair<Timestamp, double>> TimeSeriesStore::get_range(
    Timestamp start, Timestamp end) const {

    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<std::pair<Timestamp, double>> result;

    for (const auto& [ts, value] : data_) {
        if (ts >= start && ts <= end) {
            result.push_back({ts, value});
        }
    }

    return result;
}

TimeSeriesStore::Summary TimeSeriesStore::get_summary() const {
    std::lock_guard<std::mutex> lock(mutex_);

    Summary summary;
    if (data_.empty()) return summary;

    summary.min = data_[0].second;
    summary.max = data_[0].second;
    summary.count = data_.size();

    for (const auto& [ts, value] : data_) {
        summary.sum += value;
        summary.min = std::min(summary.min, value);
        summary.max = std::max(summary.max, value);
    }

    summary.avg = summary.sum / summary.count;
    return summary;
}

void TimeSeriesStore::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    data_.clear();
}

// ============================================================================
// StreamStatsCollector 实现
// ============================================================================

StreamStatsCollector::StreamStatsCollector() = default;
StreamStatsCollector::~StreamStatsCollector() = default;

void StreamStatsCollector::add_stream(const std::string& stream_name) {
    std::lock_guard<std::mutex> lock(mutex_);

    StreamQualityMetrics metrics;
    metrics.stream_name = stream_name;
    metrics.last_update = std::chrono::steady_clock::now();

    quality_metrics_[stream_name] = metrics;

    StreamStats stats;
    stats.start_time = std::chrono::steady_clock::now();
    stream_stats_[stream_name] = stats;
}

void StreamStatsCollector::remove_stream(const std::string& stream_name) {
    std::lock_guard<std::mutex> lock(mutex_);
    quality_metrics_.erase(stream_name);
    stream_stats_.erase(stream_name);
}

void StreamStatsCollector::update_quality(const std::string& stream_name,
                                          const StreamQualityMetrics& metrics) {
    std::lock_guard<std::mutex> lock(mutex_);
    quality_metrics_[stream_name] = metrics;
    quality_metrics_[stream_name].last_update = std::chrono::steady_clock::now();
}

StreamQualityMetrics StreamStatsCollector::get_quality(const std::string& stream_name) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = quality_metrics_.find(stream_name);
    if (it == quality_metrics_.end()) {
        return StreamQualityMetrics{};
    }

    return it->second;
}

std::vector<StreamQualityMetrics> StreamStatsCollector::get_all_quality() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<StreamQualityMetrics> result;
    for (const auto& [name, metrics] : quality_metrics_) {
        result.push_back(metrics);
    }
    return result;
}

void StreamStatsCollector::update_stream_stats(const std::string& stream_name,
                                               uint64_t bytes_sent,
                                               uint64_t bytes_received,
                                               uint64_t frames_sent,
                                               uint64_t frames_received) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = stream_stats_.find(stream_name);
    if (it == stream_stats_.end()) return;

    it->second.bytes_sent += bytes_sent;
    it->second.bytes_received += bytes_received;
    it->second.frames_sent += frames_sent;
    it->second.frames_received += frames_received;

    // 计算当前码率
    auto now = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::seconds>(
        now - it->second.start_time
    );

    if (duration.count() > 0) {
        it->second.current_bitrate = static_cast<double>(it->second.bytes_sent * 8) / duration.count();
    }
}

StreamStats StreamStatsCollector::get_stream_stats(const std::string& stream_name) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = stream_stats_.find(stream_name);
    if (it == stream_stats_.end()) {
        return StreamStats{};
    }

    return it->second;
}

// ============================================================================
// StatsManager 实现
// ============================================================================

StatsManager::StatsManager() = default;
StatsManager::~StatsManager() { stop(); }

bool StatsManager::initialize(uint32_t collection_interval) {
    collection_interval_ = collection_interval;

    // 注册常用指标
    metrics_.register_metric("connections.total", MetricType::Counter);
    metrics_.register_metric("connections.active", MetricType::Gauge);
    metrics_.register_metric("streams.total", MetricType::Counter);
    metrics_.register_metric("streams.active", MetricType::Gauge);
    metrics_.register_metric("bytes.sent", MetricType::Counter);
    metrics_.register_metric("bytes.received", MetricType::Counter);
    metrics_.register_metric("frames.sent", MetricType::Counter);
    metrics_.register_metric("frames.received", MetricType::Counter);
    metrics_.register_metric("cpu.usage", MetricType::Gauge);
    metrics_.register_metric("memory.usage", MetricType::Gauge);
    metrics_.register_metric("bandwidth.usage", MetricType::Gauge);

    LOG_INFO("StatsManager initialized");
    return true;
}

void StatsManager::start() {
    if (running_) return;

    running_ = true;
    collection_thread_ = std::thread(&StatsManager::collection_loop, this);

    LOG_INFO("StatsManager started");
}

void StatsManager::stop() {
    running_ = false;

    if (collection_thread_.joinable()) {
        collection_thread_.join();
    }

    LOG_INFO("StatsManager stopped");
}

ServerPerformanceMetrics StatsManager::get_server_metrics() const {
    std::lock_guard<std::mutex> lock(server_metrics_mutex_);
    return server_metrics_;
}

void StatsManager::update_server_metrics(const ServerPerformanceMetrics& metrics) {
    std::lock_guard<std::mutex> lock(server_metrics_mutex_);
    server_metrics_ = metrics;
    server_metrics_.last_update = std::chrono::steady_clock::now();
}

std::string StatsManager::generate_report() const {
    std::ostringstream report;

    report << "=== Server Statistics Report ===\n\n";

    // 服务器指标
    auto server = get_server_metrics();
    report << "Server Performance:\n";
    report << "  CPU Usage: " << std::fixed << std::setprecision(1) << server.cpu_usage << "%\n";
    report << "  Memory Usage: " << server.memory_usage << "%\n";
    report << "  Network In: " << (server.network_bytes_in / 1024 / 1024) << " MB\n";
    report << "  Network Out: " << (server.network_bytes_out / 1024 / 1024) << " MB\n";
    report << "\n";

    // 指标
    auto all_metrics = metrics_.get_all_metrics();
    report << "Metrics:\n";
    for (const auto& metric : all_metrics) {
        report << "  " << metric.name << ": " << metric.value;
        if (metric.type == MetricType::Counter) {
            report << " (total: " << metric.count << ")";
        }
        report << "\n";
    }

    // 流质量
    auto qualities = stream_stats_.get_all_quality();
    if (!qualities.empty()) {
        report << "\nStream Quality:\n";
        for (const auto& q : qualities) {
            report << "  " << q.stream_name << ":\n";
            report << "    Bitrate: " << (q.video_bitrate / 1000) << " kbps\n";
            report << "    FPS: " << q.video_framerate << "\n";
            report << "    Latency: " << q.latency << " ms\n";
            report << "    Packet Loss: " << (q.packet_loss_rate * 100) << "%\n";
        }
    }

    return report.str();
}

std::string StatsManager::to_json() const {
    std::ostringstream json;

    json << "{\n";

    // 服务器指标
    auto server = get_server_metrics();
    json << "  \"server\": {\n";
    json << "    \"cpu_usage\": " << server.cpu_usage << ",\n";
    json << "    \"memory_usage\": " << server.memory_usage << ",\n";
    json << "    \"network_bytes_in\": " << server.network_bytes_in << ",\n";
    json << "    \"network_bytes_out\": " << server.network_bytes_out << "\n";
    json << "  },\n";

    // 指标
    json << "  \"metrics\": {\n";
    auto all_metrics = metrics_.get_all_metrics();
    for (size_t i = 0; i < all_metrics.size(); ++i) {
        json << "    \"" << all_metrics[i].name << "\": " << all_metrics[i].value;
        if (i < all_metrics.size() - 1) json << ",";
        json << "\n";
    }
    json << "  }\n";

    json << "}\n";

    return json.str();
}

void StatsManager::collection_loop() {
    while (running_) {
        collect_server_metrics();

        // 生成报告
        if (report_callback_) {
            report_callback_(generate_report());
        }

        std::this_thread::sleep_for(std::chrono::seconds(collection_interval_));
    }
}

void StatsManager::collect_server_metrics() {
    // 收集系统指标（简化实现）
    std::lock_guard<std::mutex> lock(server_metrics_mutex_);

    // 这里应该使用系统 API 获取实际指标
    server_metrics_.last_update = std::chrono::steady_clock::now();
}

} // namespace streaming
