/**
 * @file dns_monitor.cpp
 * @brief DNS 监控和日志系统实现
 *
 * 实现：
 * - 查询统计
 * - 性能监控
 * - 错误日志
 * - 审计日志
 */

#include "monitoring/dns_monitor.h"

#include <iostream>
#include <iomanip>
#include <sstream>
#include <chrono>
#include <fstream>

#ifdef __linux__
#include <sys/resource.h>
#include <unistd.h>
#endif

namespace dns {

// ============================================================================
// 日志级别转换
// ============================================================================

const char* log_level_to_string(LogLevel level) {
    switch (level) {
        case LogLevel::TRACE: return "TRACE";
        case LogLevel::DEBUG: return "DEBUG";
        case LogLevel::INFO:  return "INFO";
        case LogLevel::WARN:  return "WARN";
        case LogLevel::ERROR: return "ERROR";
        case LogLevel::FATAL: return "FATAL";
        default:              return "UNKNOWN";
    }
}

// ============================================================================
// ConsoleSink 实现
// ============================================================================

ConsoleSink::ConsoleSink(bool color) : color_(color) {}

void ConsoleSink::write(const LogEntry& entry) {
    auto time_t = std::chrono::system_clock::to_time_t(entry.timestamp);
    auto tm = *std::localtime(&time_t);

    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");

    if (color_) {
        // ANSI 颜色代码
        const char* color = "";
        switch (entry.level) {
            case LogLevel::TRACE: color = "\033[90m"; break;  // 灰色
            case LogLevel::DEBUG: color = "\033[36m"; break;  // 青色
            case LogLevel::INFO:  color = "\033[32m"; break;  // 绿色
            case LogLevel::WARN:  color = "\033[33m"; break;  // 黄色
            case LogLevel::ERROR: color = "\033[31m"; break;  // 红色
            case LogLevel::FATAL: color = "\033[35m"; break;  // 紫色
        }
        std::cout << color << "[" << oss.str() << "] "
                  << "[" << log_level_to_string(entry.level) << "] "
                  << "[" << entry.source << "] "
                  << entry.message << "\033[0m" << std::endl;
    } else {
        std::cout << "[" << oss.str() << "] "
                  << "[" << log_level_to_string(entry.level) << "] "
                  << "[" << entry.source << "] "
                  << entry.message << std::endl;
    }
}

void ConsoleSink::flush() {
    std::cout.flush();
}

// ============================================================================
// FileSink 实现
// ============================================================================

FileSink::FileSink(const std::string& filename, size_t max_size)
    : filename_(filename), max_size_(max_size) {
    file_.open(filename, std::ios::app);
}

FileSink::~FileSink() {
    if (file_.is_open()) {
        file_.close();
    }
}

void FileSink::write(const LogEntry& entry) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!file_.is_open()) return;

    auto time_t = std::chrono::system_clock::to_time_t(entry.timestamp);
    auto tm = *std::localtime(&time_t);

    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S")
        << " [" << log_level_to_string(entry.level) << "]"
        << " [" << entry.source << "]"
        << " " << entry.message;

    if (!entry.client_ip.empty()) {
        oss << " (client: " << entry.client_ip << ")";
    }

    std::string line = oss.str();
    file_ << line << std::endl;
    current_size_ += line.size() + 1;

    // 检查是否需要轮转
    if (current_size_ >= max_size_) {
        rotate();
    }
}

void FileSink::flush() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (file_.is_open()) {
        file_.flush();
    }
}

void FileSink::rotate() {
    file_.close();

    // 重命名旧文件
    std::string backup = filename_ + "." +
        std::to_string(std::chrono::system_clock::now()
            .time_since_epoch().count());
    std::rename(filename_.c_str(), backup.c_str());

    // 打开新文件
    file_.open(filename_, std::ios::app);
    current_size_ = 0;
}

// ============================================================================
// Logger 实现
// ============================================================================

Logger& Logger::instance() {
    static Logger logger;
    return logger;
}

void Logger::set_level(LogLevel level) {
    level_ = level;
}

void Logger::add_sink(std::unique_ptr<LogSink> sink) {
    std::lock_guard<std::mutex> lock(mutex_);
    sinks_.push_back(std::move(sink));
}

void Logger::log(LogLevel level, const std::string& source,
                 const std::string& message) {
    if (level < level_) return;

    LogEntry entry;
    entry.level = level;
    entry.timestamp = std::chrono::system_clock::now();
    entry.source = source;
    entry.message = message;

    std::lock_guard<std::mutex> lock(mutex_);

    // 写入所有 sink
    for (auto& sink : sinks_) {
        sink->write(entry);
    }

    // 保存到最近日志
    recent_logs_.push_back(entry);
    if (recent_logs_.size() > MAX_RECENT) {
        recent_logs_.erase(recent_logs_.begin());
    }
}

void Logger::trace(const std::string& source, const std::string& message) {
    log(LogLevel::TRACE, source, message);
}

void Logger::debug(const std::string& source, const std::string& message) {
    log(LogLevel::DEBUG, source, message);
}

void Logger::info(const std::string& source, const std::string& message) {
    log(LogLevel::INFO, source, message);
}

void Logger::warn(const std::string& source, const std::string& message) {
    log(LogLevel::WARN, source, message);
}

void Logger::error(const std::string& source, const std::string& message) {
    log(LogLevel::ERROR, source, message);
}

void Logger::fatal(const std::string& source, const std::string& message) {
    log(LogLevel::FATAL, source, message);
}

std::vector<LogEntry> Logger::get_recent(size_t count) const {
    std::lock_guard<std::mutex> lock(mutex_);

    if (count >= recent_logs_.size()) {
        return recent_logs_;
    }

    return std::vector<LogEntry>(
        recent_logs_.end() - count, recent_logs_.end());
}

// ============================================================================
// QueryStatsCollector 实现
// ============================================================================

QueryStatsCollector& QueryStatsCollector::instance() {
    static QueryStatsCollector collector;
    return collector;
}

void QueryStatsCollector::record_query(
    const std::string& client_ip,
    RecordType type,
    ResponseCode rcode,
    double response_time_ms,
    bool is_tcp) {

    std::lock_guard<std::mutex> lock(mutex_);

    stats_.total_queries++;
    if (rcode == ResponseCode::NO_ERROR) {
        stats_.successful_queries++;
    } else {
        stats_.failed_queries++;
    }

    // 按类型统计
    stats_.queries_by_type[type]++;

    // 按响应码统计
    stats_.responses_by_code[rcode]++;

    // 按来源统计
    stats_.queries_by_client[client_ip]++;

    // 时间统计
    uint64_t time_us = static_cast<uint64_t>(response_time_ms * 1000);
    stats_.total_response_time_us += time_us;
    stats_.min_response_time_us = std::min(stats_.min_response_time_us, time_us);
    stats_.max_response_time_us = std::max(stats_.max_response_time_us, time_us);

    // 协议统计
    if (is_tcp) {
        stats_.tcp_queries++;
    } else {
        stats_.udp_queries++;
    }
}

void QueryStatsCollector::reset() {
    std::lock_guard<std::mutex> lock(mutex_);
    stats_ = QueryStats();
}

std::string QueryStatsCollector::to_json() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::ostringstream json;
    json << "{\n";
    json << "  \"total_queries\": " << stats_.total_queries << ",\n";
    json << "  \"successful_queries\": " << stats_.successful_queries << ",\n";
    json << "  \"failed_queries\": " << stats_.failed_queries << ",\n";
    json << "  \"udp_queries\": " << stats_.udp_queries << ",\n";
    json << "  \"tcp_queries\": " << stats_.tcp_queries << ",\n";
    json << "  \"avg_response_time_ms\": " << stats_.avg_response_time_ms() << "\n";
    json << "}";

    return json.str();
}

// ============================================================================
// PerformanceMonitor 实现
// ============================================================================

PerformanceMonitor& PerformanceMonitor::instance() {
    static PerformanceMonitor monitor;
    return monitor;
}

void PerformanceMonitor::start(std::chrono::seconds interval) {
    running_ = true;
    monitor_thread_ = std::thread([this, interval]() {
        while (running_) {
            collect_metrics();
            std::this_thread::sleep_for(interval);
        }
    });
}

void PerformanceMonitor::stop() {
    running_ = false;
    if (monitor_thread_.joinable()) {
        monitor_thread_.join();
    }
}

PerformanceMetrics PerformanceMonitor::get_metrics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return current_metrics_;
}

void PerformanceMonitor::record_traffic(uint64_t bytes_received,
                                          uint64_t bytes_sent) {
    bytes_received_ += bytes_received;
    bytes_sent_ += bytes_sent;
}

void PerformanceMonitor::record_connection(bool opened) {
    if (opened) {
        active_connections_++;
        total_connections_++;
    } else {
        active_connections_--;
    }
}

std::vector<PerformanceMetrics> PerformanceMonitor::get_history(
    std::chrono::minutes duration) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto cutoff = std::chrono::steady_clock::now() - duration;
    std::vector<PerformanceMetrics> result;

    for (const auto& [time, metrics] : history_) {
        if (time >= cutoff) {
            result.push_back(metrics);
        }
    }

    return result;
}

void PerformanceMonitor::collect_metrics() {
    std::lock_guard<std::mutex> lock(mutex_);

#ifdef __linux__
    // 获取内存使用
    struct rusage usage;
    getrusage(RUSAGE_SELF, &usage);
    current_metrics_.memory_usage = usage.ru_maxrss * 1024;  // KB to bytes
    current_metrics_.memory_peak = std::max(current_metrics_.memory_peak,
                                             current_metrics_.memory_usage);

    // 获取 CPU 使用 (简化)
    static uint64_t last_cpu_time = 0;
    uint64_t cpu_time = usage.ru_utime.tv_sec * 1000000 +
                        usage.ru_utime.tv_usec +
                        usage.ru_stime.tv_sec * 1000000 +
                        usage.ru_stime.tv_usec;
    if (last_cpu_time > 0) {
        current_metrics_.cpu_usage =
            static_cast<double>(cpu_time - last_cpu_time) / 10000000.0 * 100.0;
    }
    last_cpu_time = cpu_time;
#endif

    // 更新网络统计
    current_metrics_.bytes_received = bytes_received_.load();
    current_metrics_.bytes_sent = bytes_sent_.load();
    current_metrics_.active_connections = active_connections_.load();
    current_metrics_.total_connections = total_connections_.load();

    // 保存历史
    history_.emplace_back(std::chrono::steady_clock::now(),
                          current_metrics_);

    // 限制历史大小
    auto cutoff = std::chrono::steady_clock::now() - std::chrono::hours(1);
    while (!history_.empty() && history_.front().first < cutoff) {
        history_.erase(history_.begin());
    }
}

// ============================================================================
// AuditLogger 实现
// ============================================================================

AuditLogger& AuditLogger::instance() {
    static AuditLogger logger;
    return logger;
}

void AuditLogger::set_logfile(const std::string& filename) {
    std::lock_guard<std::mutex> lock(mutex_);
    logfile_ = filename;
    file_ = std::make_unique<std::ofstream>(filename, std::ios::app);
}

void AuditLogger::enable(bool enabled) {
    enabled_ = enabled;
}

void AuditLogger::log(AuditEvent event,
                       const std::string& client_ip,
                       const std::string& query_name,
                       RecordType query_type,
                       const std::string& details,
                       bool success) {
    if (!enabled_) return;

    AuditEntry entry;
    entry.event = event;
    entry.timestamp = std::chrono::system_clock::now();
    entry.client_ip = client_ip;
    entry.query_name = query_name;
    entry.query_type = query_type;
    entry.details = details;
    entry.success = success;

    std::lock_guard<std::mutex> lock(mutex_);

    entries_.push_back(entry);
    if (entries_.size() > MAX_ENTRIES) {
        entries_.erase(entries_.begin());
    }

    // 写入文件
    if (file_ && file_->is_open()) {
        auto time_t = std::chrono::system_clock::to_time_t(entry.timestamp);
        auto tm = *std::localtime(&time_t);

        *file_ << std::put_time(&tm, "%Y-%m-%d %H:%M:%S")
               << " | " << static_cast<int>(event)
               << " | " << client_ip
               << " | " << query_name
               << " | " << record_type_to_string(query_type)
               << " | " << (success ? "SUCCESS" : "FAILURE")
               << " | " << details
               << std::endl;
    }
}

std::vector<AuditEntry> AuditLogger::get_recent(size_t count) const {
    std::lock_guard<std::mutex> lock(mutex_);

    if (count >= entries_.size()) {
        return entries_;
    }

    return std::vector<AuditEntry>(
        entries_.end() - count, entries_.end());
}

bool AuditLogger::export_json(const std::string& filename) const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::ofstream file(filename);
    if (!file.is_open()) return false;

    file << "[\n";
    for (size_t i = 0; i < entries_.size(); i++) {
        const auto& entry = entries_[i];
        auto time_t = std::chrono::system_clock::to_time_t(entry.timestamp);

        file << "  {\n";
        file << "    \"event\": " << static_cast<int>(entry.event) << ",\n";
        file << "    \"timestamp\": " << time_t << ",\n";
        file << "    \"client_ip\": \"" << entry.client_ip << "\",\n";
        file << "    \"query_name\": \"" << entry.query_name << "\",\n";
        file << "    \"query_type\": " << static_cast<int>(entry.query_type) << ",\n";
        file << "    \"success\": " << (entry.success ? "true" : "false") << ",\n";
        file << "    \"details\": \"" << entry.details << "\"\n";
        file << "  }";
        if (i < entries_.size() - 1) file << ",";
        file << "\n";
    }
    file << "]\n";

    return true;
}

// ============================================================================
// QueryLog 实现
// ============================================================================

QueryLog::QueryLog(const std::string& filename) {
    file_.open(filename, std::ios::app);
}

QueryLog::~QueryLog() {
    if (file_.is_open()) {
        file_.close();
    }
}

void QueryLog::log_query(const std::string& client_ip,
                          const std::string& query_name,
                          RecordType query_type,
                          ResponseCode response_code,
                          size_t answer_count,
                          double response_time_ms) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!file_.is_open()) return;

    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto tm = *std::localtime(&time_t);

    // ISC 日志格式
    file_ << std::put_time(&tm, "%d-%b-%Y %H:%M:%S")
          << " client " << client_ip
          << "#0: query: " << query_name
          << " IN " << record_type_to_string(query_type)
          << " " << response_code_to_string(response_code)
          << " (" << answer_count << ")"
          << " T=" << std::fixed << std::setprecision(3) << response_time_ms
          << std::endl;
}

void QueryLog::flush() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (file_.is_open()) {
        file_.flush();
    }
}

} // namespace dns
