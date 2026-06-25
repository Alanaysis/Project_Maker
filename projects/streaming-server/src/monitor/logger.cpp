/**
 * @file logger.cpp
 * @brief 日志系统实现
 */

#include "streaming/monitor/logger.hpp"

#include <iostream>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <cstring>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif

namespace streaming {

// ============================================================================
// LogFormatter 实现
// ============================================================================

LogFormatter::LogFormatter() = default;
LogFormatter::~LogFormatter() = default;

void LogFormatter::set_pattern(const std::string& pattern) {
    pattern_ = pattern;
}

std::string LogFormatter::format(const LogEntry& entry) const {
    std::string result = pattern_;

    // 获取时间字符串
    auto time_t = std::chrono::system_clock::to_time_t(
        std::chrono::system_clock::now()
    );
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()
    ) % 1000;

    std::ostringstream time_ss;
    time_ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    time_ss << "." << std::setfill('0') << std::setw(3) << ms.count();
    std::string time_str = time_ss.str();

    // 日志级别字符串
    std::string level_str;
    switch (entry.level) {
        case LogLevel::Trace: level_str = "TRACE"; break;
        case LogLevel::Debug: level_str = "DEBUG"; break;
        case LogLevel::Info:  level_str = "INFO "; break;
        case LogLevel::Warn:  level_str = "WARN "; break;
        case LogLevel::Error: level_str = "ERROR"; break;
        case LogLevel::Fatal: level_str = "FATAL"; break;
        default: level_str = "?????"; break;
    }

    // 线程ID
    std::ostringstream thread_ss;
    thread_ss << std::this_thread::get_id();
    std::string thread_str = thread_ss.str();

    // 替换占位符
    size_t pos;
    while ((pos = result.find('%')) != std::string::npos) {
        if (pos + 1 >= result.size()) break;

        char placeholder = result[pos + 1];
        std::string replacement;

        switch (placeholder) {
            case 'd': replacement = time_str; break;
            case 'l': replacement = level_str; break;
            case 'n': replacement = entry.logger_name; break;
            case 't': replacement = thread_str; break;
            case 'f': replacement = entry.file; break;
            case 'L': replacement = std::to_string(entry.line); break;
            case 'F': replacement = entry.function; break;
            case 'm': replacement = entry.message; break;
            case '%': replacement = "%"; break;
            default:
                result.erase(pos, 1);
                continue;
        }

        result.replace(pos, 2, replacement);
    }

    return result;
}

// ============================================================================
// ConsoleAppender 实现
// ============================================================================

ConsoleAppender::ConsoleAppender() {
    if (!formatter_) {
        formatter_ = std::make_shared<LogFormatter>();
    }
}

ConsoleAppender::~ConsoleAppender() = default;

void ConsoleAppender::append(const LogEntry& entry) {
    std::lock_guard<std::mutex> lock(mutex_);

    std::string formatted = formatter_->format(entry);

    if (color_output_) {
        // ANSI 颜色代码
        const char* color = "";
        const char* reset = "\033[0m";

        switch (entry.level) {
            case LogLevel::Trace: color = "\033[90m"; break;  // 灰色
            case LogLevel::Debug: color = "\033[36m"; break;  // 青色
            case LogLevel::Info:  color = "\033[32m"; break;  // 绿色
            case LogLevel::Warn:  color = "\033[33m"; break;  // 黄色
            case LogLevel::Error: color = "\033[31m"; break;  // 红色
            case LogLevel::Fatal: color = "\033[35m"; break;  // 紫色
            default: break;
        }

        std::cerr << color << formatted << reset << std::endl;
    } else {
        std::cerr << formatted << std::endl;
    }
}

void ConsoleAppender::flush() {
    std::cerr.flush();
}

// ============================================================================
// FileAppender 实现
// ============================================================================

FileAppender::FileAppender(const std::string& filename)
    : filename_(filename) {
    if (!formatter_) {
        formatter_ = std::make_shared<LogFormatter>();
    }

    file_.open(filename, std::ios::app);
    if (file_) {
        file_.seekp(0, std::ios::end);
        current_size_ = file_.tellp();
    }
}

FileAppender::~FileAppender() {
    if (file_.is_open()) {
        file_.close();
    }
}

void FileAppender::append(const LogEntry& entry) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!file_.is_open()) {
        file_.open(filename_, std::ios::app);
        if (!file_) return;
    }

    std::string formatted = formatter_->format(entry) + "\n";
    file_ << formatted;
    current_size_ += formatted.size();

    // 检查是否需要轮转
    if (max_size_ > 0 && current_size_ >= max_size_) {
        rotate();
    }
}

void FileAppender::flush() {
    std::lock_guard<std::mutex> lock(mutex_);
    if (file_.is_open()) {
        file_.flush();
    }
}

void FileAppender::set_rotation(uint64_t max_size, uint32_t max_files) {
    std::lock_guard<std::mutex> lock(mutex_);
    max_size_ = max_size;
    max_files_ = max_files;
}

void FileAppender::rotate() {
    if (!file_.is_open()) return;

    file_.close();

    // 轮转文件
    for (uint32_t i = max_files_ - 1; i > 0; --i) {
        std::string old_name = filename_ + "." + std::to_string(i);
        std::string new_name = filename_ + "." + std::to_string(i + 1);

        if (i == max_files_ - 1) {
            std::remove(old_name.c_str());
        } else {
            std::rename(old_name.c_str(), new_name.c_str());
        }
    }

    std::string backup_name = filename_ + ".1";
    std::rename(filename_.c_str(), backup_name.c_str());

    // 重新打开文件
    file_.open(filename_, std::ios::app);
    current_size_ = 0;
}

// ============================================================================
// CallbackAppender 实现
// ============================================================================

CallbackAppender::CallbackAppender(LogCallback callback)
    : callback_(std::move(callback)) {
    if (!formatter_) {
        formatter_ = std::make_shared<LogFormatter>();
    }
}

CallbackAppender::~CallbackAppender() = default;

void CallbackAppender::append(const LogEntry& entry) {
    if (callback_) {
        callback_(entry);
    }
}

void CallbackAppender::flush() {
    // 回调模式不需要刷新
}

// ============================================================================
// AsyncLogger 实现
// ============================================================================

AsyncLogger::AsyncLogger() = default;
AsyncLogger::~AsyncLogger() {
    stop();
}

void AsyncLogger::start() {
    if (running_) return;

    running_ = true;
    worker_thread_ = std::thread(&AsyncLogger::process_loop, this);
}

void AsyncLogger::stop() {
    if (!running_) return;

    running_ = false;
    condition_.notify_all();

    if (worker_thread_.joinable()) {
        worker_thread_.join();
    }

    // 处理剩余的日志
    while (!queue_.empty()) {
        auto entry = std::move(queue_.front());
        queue_.pop();

        for (auto& appender : appenders_) {
            appender->append(entry);
        }
    }

    // 刷新所有输出器
    for (auto& appender : appenders_) {
        appender->flush();
    }
}

void AsyncLogger::submit(const LogEntry& entry) {
    {
        std::lock_guard<std::mutex> lock(queue_mutex_);
        queue_.push(entry);
    }
    condition_.notify_one();
}

void AsyncLogger::add_appender(std::shared_ptr<LogAppender> appender) {
    appenders_.push_back(std::move(appender));
}

void AsyncLogger::process_loop() {
    while (running_) {
        std::vector<LogEntry> entries;

        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            condition_.wait(lock, [this]() { return !running_ || !queue_.empty(); });

            // 批量处理
            while (!queue_.empty() && entries.size() < 100) {
                entries.push_back(std::move(queue_.front()));
                queue_.pop();
            }
        }

        // 输出日志
        for (const auto& entry : entries) {
            for (auto& appender : appenders_) {
                appender->append(entry);
            }
        }
    }
}

// ============================================================================
// Logger 实现
// ============================================================================

Logger::Logger(const std::string& name) : name_(name) {}

Logger::~Logger() = default;

void Logger::add_appender(std::shared_ptr<LogAppender> appender) {
    std::lock_guard<std::mutex> lock(mutex_);
    appenders_.push_back(std::move(appender));
}

void Logger::log(LogLevel level, const std::string& file, int line,
                 const std::string& function, const std::string& message) {
    if (!is_enabled(level)) return;

    LogEntry entry;
    entry.level = level;
    entry.message = message;
    entry.logger_name = name_;
    entry.file = file;
    entry.line = line;
    entry.function = function;
    entry.timestamp = std::chrono::steady_clock::now();

    std::lock_guard<std::mutex> lock(mutex_);
    for (auto& appender : appenders_) {
        appender->append(entry);
    }
}

void Logger::trace(const std::string& file, int line,
                   const std::string& function, const std::string& message) {
    log(LogLevel::Trace, file, line, function, message);
}

void Logger::debug(const std::string& file, int line,
                   const std::string& function, const std::string& message) {
    log(LogLevel::Debug, file, line, function, message);
}

void Logger::info(const std::string& file, int line,
                  const std::string& function, const std::string& message) {
    log(LogLevel::Info, file, line, function, message);
}

void Logger::warn(const std::string& file, int line,
                  const std::string& function, const std::string& message) {
    log(LogLevel::Warn, file, line, function, message);
}

void Logger::error(const std::string& file, int line,
                   const std::string& function, const std::string& message) {
    log(LogLevel::Error, file, line, function, message);
}

void Logger::fatal(const std::string& file, int line,
                   const std::string& function, const std::string& message) {
    log(LogLevel::Fatal, file, line, function, message);
}

// ============================================================================
// LogManager 实现
// ============================================================================

LogManager& LogManager::instance() {
    static LogManager instance;
    return instance;
}

LogManager::LogManager() = default;
LogManager::~LogManager() {
    shutdown();
}

bool LogManager::initialize(LogLevel level, const std::string& log_file, bool async) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (initialized_) return true;

    // 创建格式化器
    formatter_ = std::make_shared<LogFormatter>();

    // 创建异步日志器
    if (async) {
        async_logger_ = std::make_shared<AsyncLogger>();

        // 添加控制台输出器
        auto console_appender = std::make_shared<ConsoleAppender>();
        console_appender->set_formatter(formatter_);
        async_logger_->add_appender(console_appender);

        // 添加文件输出器
        if (!log_file.empty()) {
            auto file_appender = std::make_shared<FileAppender>(log_file);
            file_appender->set_formatter(formatter_);
            file_appender->set_rotation(10 * 1024 * 1024, 5);  // 10MB, 5个文件
            async_logger_->add_appender(file_appender);
        }

        async_logger_->start();
    }

    // 创建默认日志器
    auto default_logger = std::make_shared<Logger>("default");
    default_logger->set_level(level);

    if (!async) {
        // 同步模式，直接添加输出器
        auto console_appender = std::make_shared<ConsoleAppender>();
        console_appender->set_formatter(formatter_);
        default_logger->add_appender(console_appender);

        if (!log_file.empty()) {
            auto file_appender = std::make_shared<FileAppender>(log_file);
            file_appender->set_formatter(formatter_);
            default_logger->add_appender(file_appender);
        }
    } else {
        // 异步模式，添加异步输出器
        auto async_appender = std::make_shared<CallbackAppender>(
            [this](const LogEntry& entry) {
                if (async_logger_) {
                    async_logger_->submit(entry);
                }
            }
        );
        async_appender->set_formatter(formatter_);
        default_logger->add_appender(async_appender);
    }

    loggers_["default"] = default_logger;
    initialized_ = true;

    return true;
}

void LogManager::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);

    if (async_logger_) {
        async_logger_->stop();
        async_logger_.reset();
    }

    loggers_.clear();
    initialized_ = false;
}

std::shared_ptr<Logger> LogManager::get_logger(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = loggers_.find(name);
    if (it != loggers_.end()) {
        return it->second;
    }

    // 创建新的日志器
    auto logger = std::make_shared<Logger>(name);
    logger->set_level(loggers_.count("default") > 0 ?
                      loggers_["default"]->get_level() : LogLevel::Info);

    // 添加与默认日志器相同的输出器
    if (loggers_.count("default") > 0) {
        // 这里简化处理，实际应该复制输出器配置
    }

    loggers_[name] = logger;
    return logger;
}

void LogManager::set_global_level(LogLevel level) {
    std::lock_guard<std::mutex> lock(mutex_);

    for (auto& [name, logger] : loggers_) {
        logger->set_level(level);
    }
}

void LogManager::set_pattern(const std::string& pattern) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (formatter_) {
        formatter_->set_pattern(pattern);
    }
}

void LogManager::set_rotation(uint64_t max_size, uint32_t max_files) {
    // 重新创建文件输出器
    // 这里简化处理
}

} // namespace streaming
