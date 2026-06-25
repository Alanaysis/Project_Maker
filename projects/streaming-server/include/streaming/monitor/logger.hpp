#pragma once

/**
 * @file logger.hpp
 * @brief 日志系统
 *
 * 实现高性能日志系统，支持：
 * - 多级别日志
 * - 异步日志
 * - 日志轮转
 * - 多目标输出
 */

#include <string>
#include <memory>
#include <fstream>
#include <sstream>
#include <mutex>
#include <thread>
#include <queue>
#include <condition_variable>
#include <functional>
#include <chrono>
#include <atomic>
#include <vector>

namespace streaming {

// 日志级别
enum class LogLevel {
    Trace = 0,
    Debug = 1,
    Info = 2,
    Warn = 3,
    Error = 4,
    Fatal = 5,
    Off = 6
};

// 日志输出目标
enum class LogTarget {
    Console,
    File,
    Syslog,
    Callback
};

// 日志条目
struct LogEntry {
    LogLevel level;
    std::string message;
    std::string logger_name;
    std::string file;
    int line = 0;
    std::string function;
    Timestamp timestamp;
    uint64_t thread_id = 0;
};

/**
 * @brief 日志格式化器
 */
class LogFormatter {
public:
    LogFormatter();
    ~LogFormatter();

    /**
     * @brief 设置格式模式
     * @param pattern 格式模式
     *
     * 支持的格式占位符：
     * %d - 日期时间
     * %l - 日志级别
     * %n - 日志器名称
     * %t - 线程ID
     * %f - 文件名
     * %L - 行号
     * %F - 函数名
     * %m - 消息
     * %% - 百分号
     */
    void set_pattern(const std::string& pattern);

    /**
     * @brief 格式化日志条目
     */
    std::string format(const LogEntry& entry) const;

private:
    std::string pattern_ = "[%d] [%l] [%n] %m";
};

/**
 * @brief 日志输出器
 */
class LogAppender {
public:
    virtual ~LogAppender() = default;

    /**
     * @brief 输出日志
     */
    virtual void append(const LogEntry& entry) = 0;

    /**
     * @brief 刷新
     */
    virtual void flush() = 0;

    /**
     * @brief 设置格式化器
     */
    void set_formatter(std::shared_ptr<LogFormatter> formatter) {
        formatter_ = std::move(formatter);
    }

protected:
    std::shared_ptr<LogFormatter> formatter_;
};

/**
 * @brief 控制台输出器
 */
class ConsoleAppender : public LogAppender {
public:
    ConsoleAppender();
    ~ConsoleAppender() override;

    void append(const LogEntry& entry) override;
    void flush() override;

    /**
     * @brief 设置彩色输出
     */
    void set_color_output(bool enable) { color_output_ = enable; }

private:
    bool color_output_ = true;
    std::mutex mutex_;
};

/**
 * @brief 文件输出器
 */
class FileAppender : public LogAppender {
public:
    FileAppender(const std::string& filename);
    ~FileAppender() override;

    void append(const LogEntry& entry) override;
    void flush() override;

    /**
     * @brief 设置日志轮转
     * @param max_size 最大文件大小（字节）
     * @param max_files 最大文件数量
     */
    void set_rotation(uint64_t max_size, uint32_t max_files);

private:
    void rotate();

    std::string filename_;
    std::ofstream file_;
    uint64_t current_size_ = 0;
    uint64_t max_size_ = 0;
    uint32_t max_files_ = 0;
    std::mutex mutex_;
};

/**
 * @brief 回调输出器
 */
class CallbackAppender : public LogAppender {
public:
    using LogCallback = std::function<void(const LogEntry&)>;
    CallbackAppender(LogCallback callback);
    ~CallbackAppender() override;

    void append(const LogEntry& entry) override;
    void flush() override;

private:
    LogCallback callback_;
};

/**
 * @brief 异步日志器
 *
 * 使用单独的线程处理日志输出，避免阻塞主线程。
 */
class AsyncLogger {
public:
    AsyncLogger();
    ~AsyncLogger();

    /**
     * @brief 启动异步日志
     */
    void start();

    /**
     * @brief 停止异步日志
     */
    void stop();

    /**
     * @brief 提交日志条目
     */
    void submit(const LogEntry& entry);

    /**
     * @brief 添加输出器
     */
    void add_appender(std::shared_ptr<LogAppender> appender);

private:
    void process_loop();

    std::vector<std::shared_ptr<LogAppender>> appenders_;
    std::queue<LogEntry> queue_;
    std::mutex queue_mutex_;
    std::condition_variable condition_;
    std::thread worker_thread_;
    std::atomic<bool> running_{false};
};

/**
 * @brief 日志器
 */
class Logger {
public:
    Logger(const std::string& name);
    ~Logger();

    /**
     * @brief 设置日志级别
     */
    void set_level(LogLevel level) { level_ = level; }

    /**
     * @brief 获取日志级别
     */
    LogLevel get_level() const { return level_; }

    /**
     * @brief 添加输出器
     */
    void add_appender(std::shared_ptr<LogAppender> appender);

    /**
     * @brief 日志输出方法
     */
    void log(LogLevel level, const std::string& file, int line,
             const std::string& function, const std::string& message);

    void trace(const std::string& file, int line,
               const std::string& function, const std::string& message);
    void debug(const std::string& file, int line,
               const std::string& function, const std::string& message);
    void info(const std::string& file, int line,
              const std::string& function, const std::string& message);
    void warn(const std::string& file, int line,
              const std::string& function, const std::string& message);
    void error(const std::string& file, int line,
               const std::string& function, const std::string& message);
    void fatal(const std::string& file, int line,
               const std::string& function, const std::string& message);

    /**
     * @brief 是否启用该级别
     */
    bool is_enabled(LogLevel level) const { return level >= level_; }

private:
    std::string name_;
    LogLevel level_ = LogLevel::Info;
    std::vector<std::shared_ptr<LogAppender>> appenders_;
    mutable std::mutex mutex_;
};

/**
 * @brief 日志管理器
 */
class LogManager {
public:
    static LogManager& instance();

    /**
     * @brief 初始化日志系统
     * @param level 全局日志级别
     * @param log_file 日志文件路径
     * @param async 是否异步
     */
    bool initialize(LogLevel level = LogLevel::Info,
                   const std::string& log_file = "",
                   bool async = true);

    /**
     * @brief 关闭日志系统
     */
    void shutdown();

    /**
     * @brief 获取日志器
     */
    std::shared_ptr<Logger> get_logger(const std::string& name);

    /**
     * @brief 设置全局日志级别
     */
    void set_global_level(LogLevel level);

    /**
     * @brief 设置日志格式
     */
    void set_pattern(const std::string& pattern);

    /**
     * @brief 设置日志轮转
     */
    void set_rotation(uint64_t max_size, uint32_t max_files);

private:
    LogManager();
    ~LogManager();
    LogManager(const LogManager&) = delete;
    LogManager& operator=(const LogManager&) = delete;

    std::unordered_map<std::string, std::shared_ptr<Logger>> loggers_;
    std::shared_ptr<AsyncLogger> async_logger_;
    std::shared_ptr<LogFormatter> formatter_;
    mutable std::mutex mutex_;
    bool initialized_ = false;
};

// ============================================================================
// 日志宏
// ============================================================================

#define STREAMING_LOG_TRACE(logger, message) \
    if (logger->is_enabled(streaming::LogLevel::Trace)) \
        logger->trace(__FILE__, __LINE__, __FUNCTION__, message)

#define STREAMING_LOG_DEBUG(logger, message) \
    if (logger->is_enabled(streaming::LogLevel::Debug)) \
        logger->debug(__FILE__, __LINE__, __FUNCTION__, message)

#define STREAMING_LOG_INFO(logger, message) \
    if (logger->is_enabled(streaming::LogLevel::Info)) \
        logger->info(__FILE__, __LINE__, __FUNCTION__, message)

#define STREAMING_LOG_WARN(logger, message) \
    if (logger->is_enabled(streaming::LogLevel::Warn)) \
        logger->warn(__FILE__, __LINE__, __FUNCTION__, message)

#define STREAMING_LOG_ERROR(logger, message) \
    if (logger->is_enabled(streaming::LogLevel::Error)) \
        logger->error(__FILE__, __LINE__, __FUNCTION__, message)

#define STREAMING_LOG_FATAL(logger, message) \
    if (logger->is_enabled(streaming::LogLevel::Fatal)) \
        logger->fatal(__FILE__, __LINE__, __FUNCTION__, message)

// 获取默认日志器
#define STREAMING_DEFAULT_LOGGER \
    streaming::LogManager::instance().get_logger("default")

// 默认日志宏
#define LOG_TRACE(message) STREAMING_LOG_TRACE(STREAMING_DEFAULT_LOGGER, message)
#define LOG_DEBUG(message) STREAMING_LOG_DEBUG(STREAMING_DEFAULT_LOGGER, message)
#define LOG_INFO(message) STREAMING_LOG_INFO(STREAMING_DEFAULT_LOGGER, message)
#define LOG_WARN(message) STREAMING_LOG_WARN(STREAMING_DEFAULT_LOGGER, message)
#define LOG_ERROR(message) STREAMING_LOG_ERROR(STREAMING_DEFAULT_LOGGER, message)
#define LOG_FATAL(message) STREAMING_LOG_FATAL(STREAMING_DEFAULT_LOGGER, message)

} // namespace streaming
