/**
 * @file logger.h
 * @brief 日志系统
 *
 * 异步日志系统，支持分级日志和结构化输出。
 */

#pragma once

#include <string>
#include <fstream>
#include <mutex>
#include <queue>
#include <thread>
#include <atomic>
#include <condition_variable>
#include <functional>
#include <sstream>
#include <iostream>
#include <chrono>
#include <iomanip>

namespace hft {

/**
 * @enum LogLevel
 * @brief 日志级别
 */
enum class LogLevel {
    DEBUG,    ///< 调试信息
    INFO,     ///< 运行信息
    WARN,     ///< 警告信息
    ERROR,    ///< 错误信息
    FATAL     ///< 致命错误
};

/**
 * @brief 日志级别转字符串
 */
inline const char* log_level_to_string(LogLevel level) {
    switch (level) {
        case LogLevel::DEBUG: return "DEBUG";
        case LogLevel::INFO:  return "INFO";
        case LogLevel::WARN:  return "WARN";
        case LogLevel::ERROR: return "ERROR";
        case LogLevel::FATAL: return "FATAL";
        default: return "UNKNOWN";
    }
}

/**
 * @struct LogEntry
 * @brief 日志条目
 */
struct LogEntry {
    LogLevel level;           ///< 日志级别
    std::string message;      ///< 日志消息
    std::string file;         ///< 源文件名
    int line;                 ///< 行号
    std::string function;     ///< 函数名
    std::thread::id thread_id; ///< 线程 ID
    std::string timestamp;    ///< 时间戳
};

/**
 * @class Logger
 * @brief 日志系统
 *
 * 特性：
 * - 异步写入
 * - 分级日志
 * - 多输出目标（控制台、文件）
 * - 日志轮转
 */
class Logger {
public:
    /**
     * @brief 获取单例实例
     * @return Logger 实例
     */
    static Logger& instance() {
        static Logger instance;
        return instance;
    }

    /**
     * @brief 初始化日志系统
     * @param log_file 日志文件路径
     * @param min_level 最小日志级别
     */
    void init(const std::string& log_file = "", LogLevel min_level = LogLevel::INFO) {
        min_level_ = min_level;

        if (!log_file.empty()) {
            file_.open(log_file, std::ios::app);
            if (!file_.is_open()) {
                std::cerr << "Failed to open log file: " << log_file << std::endl;
            }
        }

        running_ = true;
        worker_thread_ = std::thread(&Logger::worker, this);
    }

    /**
     * @brief 关闭日志系统
     */
    void shutdown() {
        running_ = false;
        cv_.notify_all();

        if (worker_thread_.joinable()) {
            worker_thread_.join();
        }

        if (file_.is_open()) {
            file_.close();
        }
    }

    /**
     * @brief 记录日志
     * @param level 日志级别
     * @param message 日志消息
     * @param file 源文件名
     * @param line 行号
     * @param function 函数名
     */
    void log(LogLevel level, const std::string& message,
             const char* file = "", int line = 0,
             const char* function = "") {
        if (level < min_level_) return;

        LogEntry entry;
        entry.level = level;
        entry.message = message;
        entry.file = file ? file : "";
        entry.line = line;
        entry.function = function ? function : "";
        entry.thread_id = std::this_thread::get_id();

        // 生成时间戳
        auto now = std::chrono::system_clock::now();
        auto time = std::chrono::system_clock::to_time_t(now);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;

        std::ostringstream oss;
        oss << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S");
        oss << '.' << std::setfill('0') << std::setw(3) << ms.count();
        entry.timestamp = oss.str();

        // 添加到队列
        {
            std::lock_guard<std::mutex> lock(mutex_);
            queue_.push(std::move(entry));
        }
        cv_.notify_one();
    }

    /**
     * @brief 设置最小日志级别
     * @param level 日志级别
     */
    void set_level(LogLevel level) {
        min_level_ = level;
    }

    /**
     * @brief 设置日志回调
     * @param callback 回调函数
     */
    void set_callback(std::function<void(const LogEntry&)> callback) {
        callback_ = std::move(callback);
    }

private:
    Logger() : running_(false), min_level_(LogLevel::INFO) {}

    ~Logger() {
        shutdown();
    }

    /**
     * @brief 工作线程函数
     */
    void worker() {
        while (running_ || !queue_.empty()) {
            std::unique_lock<std::mutex> lock(mutex_);
            cv_.wait(lock, [this] {
                return !queue_.empty() || !running_;
            });

            while (!queue_.empty()) {
                LogEntry entry = std::move(queue_.front());
                queue_.pop();
                lock.unlock();

                // 输出到控制台
                output_to_console(entry);

                // 输出到文件
                if (file_.is_open()) {
                    output_to_file(entry);
                }

                // 调用回调
                if (callback_) {
                    callback_(entry);
                }

                lock.lock();
            }
        }
    }

    /**
     * @brief 输出到控制台
     */
    void output_to_console(const LogEntry& entry) {
        std::ostringstream oss;
        oss << "[" << entry.timestamp << "] "
            << "[" << log_level_to_string(entry.level) << "] "
            << entry.message;

        if (!entry.file.empty()) {
            oss << " (" << entry.file << ":" << entry.line << ")";
        }

        oss << "\n";

        if (entry.level >= LogLevel::ERROR) {
            std::cerr << oss.str();
        } else {
            std::cout << oss.str();
        }
    }

    /**
     * @brief 输出到文件
     */
    void output_to_file(const LogEntry& entry) {
        std::ostringstream oss;
        oss << entry.timestamp << "\t"
            << log_level_to_string(entry.level) << "\t"
            << entry.thread_id << "\t"
            << entry.message;

        if (!entry.file.empty()) {
            oss << "\t" << entry.file << ":" << entry.line
                << " " << entry.function;
        }

        oss << "\n";

        file_ << oss.str();
        file_.flush();
    }

    std::thread worker_thread_;          ///< 工作线程
    std::mutex mutex_;                   ///< 互斥锁
    std::condition_variable cv_;         ///< 条件变量
    std::queue<LogEntry> queue_;         ///< 日志队列
    std::atomic<bool> running_;          ///< 运行标志
    LogLevel min_level_;                 ///< 最小日志级别
    std::ofstream file_;                 ///< 日志文件
    std::function<void(const LogEntry&)> callback_;  ///< 日志回调
};

// 便捷宏定义
#define LOG_DEBUG(msg) \
    hft::Logger::instance().log(hft::LogLevel::DEBUG, msg, __FILE__, __LINE__, __FUNCTION__)

#define LOG_INFO(msg) \
    hft::Logger::instance().log(hft::LogLevel::INFO, msg, __FILE__, __LINE__, __FUNCTION__)

#define LOG_WARN(msg) \
    hft::Logger::instance().log(hft::LogLevel::WARN, msg, __FILE__, __LINE__, __FUNCTION__)

#define LOG_ERROR(msg) \
    hft::Logger::instance().log(hft::LogLevel::ERROR, msg, __FILE__, __LINE__, __FUNCTION__)

#define LOG_FATAL(msg) \
    hft::Logger::instance().log(hft::LogLevel::FATAL, msg, __FILE__, __LINE__, __FUNCTION__)

} // namespace hft
