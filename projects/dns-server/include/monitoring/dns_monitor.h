#pragma once

/**
 * @file dns_monitor.h
 * @brief DNS 监控和日志系统
 *
 * 实现：
 * - 查询统计
 * - 性能监控
 * - 错误日志
 * - 审计日志
 */

#include "../protocol/dns_message.h"
#include <string>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <chrono>
#include <fstream>
#include <functional>
#include <memory>
#include <sstream>
#include <thread>

namespace dns {

// ============================================================================
// 日志级别
// ============================================================================

enum class LogLevel {
    TRACE,
    DEBUG,
    INFO,
    WARN,
    ERROR,
    FATAL,
};

const char* log_level_to_string(LogLevel level);

// ============================================================================
// 日志条目
// ============================================================================

struct LogEntry {
    LogLevel level;
    std::chrono::system_clock::time_point timestamp;
    std::string source;     // 来源模块
    std::string message;    // 日志消息
    std::string client_ip;  // 客户端 IP (可选)
    uint16_t query_id = 0;  // 查询 ID (可选)
};

// ============================================================================
// 日志输出接口
// ============================================================================

class LogSink {
public:
    virtual ~LogSink() = default;
    virtual void write(const LogEntry& entry) = 0;
    virtual void flush() = 0;
};

// 控制台日志
class ConsoleSink : public LogSink {
public:
    explicit ConsoleSink(bool color = true);
    void write(const LogEntry& entry) override;
    void flush() override;

private:
    bool color_;
};

// 文件日志
class FileSink : public LogSink {
public:
    explicit FileSink(const std::string& filename,
                      size_t max_size = 10 * 1024 * 1024);  // 10MB
    ~FileSink();
    void write(const LogEntry& entry) override;
    void flush() override;

private:
    void rotate();

    std::string filename_;
    size_t max_size_;
    size_t current_size_ = 0;
    std::ofstream file_;
    std::mutex mutex_;
};

// ============================================================================
// 日志器
// ============================================================================

class Logger {
public:
    static Logger& instance();

    // 配置
    void set_level(LogLevel level);
    void add_sink(std::unique_ptr<LogSink> sink);

    // 日志方法
    void log(LogLevel level, const std::string& source,
             const std::string& message);

    void trace(const std::string& source, const std::string& message);
    void debug(const std::string& source, const std::string& message);
    void info(const std::string& source, const std::string& message);
    void warn(const std::string& source, const std::string& message);
    void error(const std::string& source, const std::string& message);
    void fatal(const std::string& source, const std::string& message);

    // 获取最近的日志
    std::vector<LogEntry> get_recent(size_t count = 100) const;

private:
    Logger() = default;

    LogLevel level_ = LogLevel::INFO;
    std::vector<std::unique_ptr<LogSink>> sinks_;
    mutable std::mutex mutex_;

    // 最近日志缓冲
    std::vector<LogEntry> recent_logs_;
    static constexpr size_t MAX_RECENT = 1000;
};

// ============================================================================
// 便捷日志宏
// ============================================================================

#define DNS_LOG_TRACE(source, msg) \
    dns::Logger::instance().trace(source, msg)
#define DNS_LOG_DEBUG(source, msg) \
    dns::Logger::instance().debug(source, msg)
#define DNS_LOG_INFO(source, msg) \
    dns::Logger::instance().info(source, msg)
#define DNS_LOG_WARN(source, msg) \
    dns::Logger::instance().warn(source, msg)
#define DNS_LOG_ERROR(source, msg) \
    dns::Logger::instance().error(source, msg)
#define DNS_LOG_FATAL(source, msg) \
    dns::Logger::instance().fatal(source, msg)

// ============================================================================
// 查询统计
// ============================================================================

struct QueryStats {
    // 总查询数
    uint64_t total_queries{0};
    uint64_t successful_queries{0};
    uint64_t failed_queries{0};

    // 按类型统计
    std::unordered_map<RecordType, uint64_t> queries_by_type;

    // 按响应码统计
    std::unordered_map<ResponseCode, uint64_t> responses_by_code;

    // 按来源统计
    std::unordered_map<std::string, uint64_t> queries_by_client;

    // 时间统计
    uint64_t total_response_time_us{0};
    uint64_t min_response_time_us{UINT64_MAX};
    uint64_t max_response_time_us{0};

    // 协议统计
    uint64_t udp_queries{0};
    uint64_t tcp_queries{0};

    // 计算平均响应时间
    double avg_response_time_ms() const {
        if (total_queries == 0) return 0.0;
        return static_cast<double>(total_response_time_us) / total_queries / 1000.0;
    }
};

// ============================================================================
// 查询统计收集器
// ============================================================================

class QueryStatsCollector {
public:
    static QueryStatsCollector& instance();

    // 记录查询
    void record_query(const std::string& client_ip,
                      RecordType type,
                      ResponseCode rcode,
                      double response_time_ms,
                      bool is_tcp);

    // 获取统计信息
    QueryStats& get_stats() { return stats_; }
    const QueryStats& get_stats() const { return stats_; }

    // 重置统计
    void reset();

    // 导出为 JSON
    std::string to_json() const;

private:
    QueryStatsCollector() = default;
    QueryStats stats_;
    mutable std::mutex mutex_;
};

// ============================================================================
// 性能监控
// ============================================================================

struct PerformanceMetrics {
    // CPU 使用率
    double cpu_usage = 0.0;

    // 内存使用
    size_t memory_usage = 0;
    size_t memory_peak = 0;

    // 网络统计
    uint64_t bytes_received = 0;
    uint64_t bytes_sent = 0;
    uint64_t packets_received = 0;
    uint64_t packets_sent = 0;

    // 连接统计
    size_t active_connections = 0;
    size_t total_connections = 0;

    // 缓存统计
    size_t cache_size = 0;
    double cache_hit_rate = 0.0;
};

class PerformanceMonitor {
public:
    static PerformanceMonitor& instance();

    // 开始监控
    void start(std::chrono::seconds interval = std::chrono::seconds(10));

    // 停止监控
    void stop();

    // 获取当前指标
    PerformanceMetrics get_metrics() const;

    // 记录网络流量
    void record_traffic(uint64_t bytes_received, uint64_t bytes_sent);

    // 记录连接
    void record_connection(bool opened);

    // 获取历史指标
    std::vector<PerformanceMetrics> get_history(
        std::chrono::minutes duration) const;

private:
    void collect_metrics();

    std::atomic<bool> running_{false};
    std::thread monitor_thread_;

    mutable std::mutex mutex_;
    PerformanceMetrics current_metrics_;
    std::vector<std::pair<std::chrono::steady_clock::time_point,
                          PerformanceMetrics>> history_;

    std::atomic<uint64_t> bytes_received_{0};
    std::atomic<uint64_t> bytes_sent_{0};
    std::atomic<size_t> active_connections_{0};
    std::atomic<size_t> total_connections_{0};
};

// ============================================================================
// 审计日志
// ============================================================================

enum class AuditEvent {
    QUERY_RECEIVED,      // 收到查询
    QUERY_RESPONDED,     // 响应查询
    ZONE_TRANSFER,       // 区域传输
    DYNAMIC_UPDATE,      // 动态更新
    CONFIG_CHANGE,       // 配置变更
    ACCESS_DENIED,       // 访问拒绝
    RATE_LIMITED,        // 速率限制
    AUTH_FAILURE,         // 认证失败
    SERVER_START,        // 服务器启动
    SERVER_STOP,         // 服务器停止
};

struct AuditEntry {
    AuditEvent event;
    std::chrono::system_clock::time_point timestamp;
    std::string client_ip;
    std::string query_name;
    RecordType query_type;
    std::string details;
    bool success;
};

class AuditLogger {
public:
    static AuditLogger& instance();

    // 配置
    void set_logfile(const std::string& filename);
    void enable(bool enabled);

    // 记录审计事件
    void log(AuditEvent event,
             const std::string& client_ip,
             const std::string& query_name,
             RecordType query_type,
             const std::string& details,
             bool success);

    // 获取最近的审计记录
    std::vector<AuditEntry> get_recent(size_t count = 100) const;

    // 导出审计日志
    bool export_json(const std::string& filename) const;

private:
    AuditLogger() = default;

    bool enabled_ = false;
    std::string logfile_;
    std::unique_ptr<std::ofstream> file_;
    mutable std::mutex mutex_;

    std::vector<AuditEntry> entries_;
    static constexpr size_t MAX_ENTRIES = 10000;
};

// ============================================================================
// DNS 查询日志 (Apache/ISC 格式)
// ============================================================================

class QueryLog {
public:
    explicit QueryLog(const std::string& filename);
    ~QueryLog();

    // 记录查询
    void log_query(const std::string& client_ip,
                   const std::string& query_name,
                   RecordType query_type,
                   ResponseCode response_code,
                   size_t answer_count,
                   double response_time_ms);

    // 刷新
    void flush();

private:
    std::ofstream file_;
    std::mutex mutex_;
};

} // namespace dns
