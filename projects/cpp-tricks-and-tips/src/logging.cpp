/**
 * logging.cpp - 日志系统实现
 *
 * 本文件演示如何从零构建一个功能完善的 C++ 日志框架，包括：
 *   1. 日志级别定义 (DEBUG, INFO, WARN, ERROR, FATAL)
 *   2. 线程安全的日志输出
 *   3. 格式化字符串支持
 *   4. 同时输出到文件和控制台
 *   5. 日志宏的使用
 *
 * 编译命令:
 *   g++ -std=c++17 -pthread -o logging logging.cpp
 */

#include <iostream>
#include <fstream>
#include <string>
#include <string_view>
#include <sstream>
#include <mutex>
#include <chrono>
#include <iomanip>
#include <memory>
#include <functional>
#include <cstring>
#include <map>
#include <algorithm>
#include <optional>
#include <thread>
#include <vector>

// ============================================================================
// 第一部分: 日志级别定义
// ============================================================================
// 日志级别从低到高，用于控制输出的详细程度

enum class LogLevel {
    TRACE = 0,   // 最详细的追踪信息
    DEBUG = 1,   // 调试信息
    INFO = 2,    // 一般信息
    WARN = 3,    // 警告信息
    ERROR = 4,   // 错误信息
    FATAL = 5    // 致命错误（通常会导致程序退出）
};

// 将日志级别转换为字符串
inline const char* log_level_to_string(LogLevel level) {
    switch (level) {
        case LogLevel::TRACE: return "TRACE";
        case LogLevel::DEBUG: return "DEBUG";
        case LogLevel::INFO:  return "INFO ";
        case LogLevel::WARN:  return "WARN ";
        case LogLevel::ERROR: return "ERROR";
        case LogLevel::FATAL: return "FATAL";
        default:              return "?????";
    }
}

// 将字符串解析为日志级别（用于配置解析）
inline LogLevel string_to_log_level(std::string_view str) {
    // 转为大写后比较，忽略大小写
    std::string upper(str);
    std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);

    static const std::map<std::string, LogLevel> mapping = {
        {"TRACE", LogLevel::TRACE},
        {"DEBUG", LogLevel::DEBUG},
        {"INFO",  LogLevel::INFO},
        {"WARN",  LogLevel::WARN},
        {"ERROR", LogLevel::ERROR},
        {"FATAL", LogLevel::FATAL}
    };

    auto it = mapping.find(upper);
    if (it != mapping.end()) return it->second;
    return LogLevel::INFO;  // 默认级别
}

// ============================================================================
// 第二部分: 日志输出目标 (Sink)
// ============================================================================
// Sink 是日志的输出目标，可以是控制台、文件、网络等
// 使用抽象基类实现策略模式

class LogSink {
public:
    virtual ~LogSink() = default;
    virtual void write(std::string_view message) = 0;
    virtual void flush() = 0;
};

// 控制台输出 Sink
class ConsoleSink : public LogSink {
public:
    explicit ConsoleSink(bool use_color = true) : m_use_color(use_color) {}

    void write(std::string_view message) override {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (m_use_color) {
            // 根据日志级别使用不同颜色（ANSI 转义码）
            std::cout << m_current_color << message << "\033[0m";
        } else {
            std::cout << message;
        }
    }

    void flush() override {
        std::lock_guard<std::mutex> lock(m_mutex);
        std::cout.flush();
    }

    // 设置当前输出颜色
    void set_color(LogLevel level) {
        if (!m_use_color) return;
        switch (level) {
            case LogLevel::TRACE: m_current_color = "\033[37m";   break; // 白色
            case LogLevel::DEBUG: m_current_color = "\033[36m";   break; // 青色
            case LogLevel::INFO:  m_current_color = "\033[32m";   break; // 绿色
            case LogLevel::WARN:  m_current_color = "\033[33m";   break; // 黄色
            case LogLevel::ERROR: m_current_color = "\033[31m";   break; // 红色
            case LogLevel::FATAL: m_current_color = "\033[35;1m"; break; // 亮紫色
        }
    }

private:
    std::mutex m_mutex;
    bool m_use_color;
    std::string m_current_color;
};

// 文件输出 Sink
class FileSink : public LogSink {
public:
    explicit FileSink(const std::string& filename) {
        m_file.open(filename, std::ios::app);  // 追加模式
        if (!m_file.is_open()) {
            throw std::runtime_error("无法打开日志文件: " + filename);
        }
    }

    void write(std::string_view message) override {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_file << message;
    }

    void flush() override {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_file.flush();
    }

private:
    std::ofstream m_file;
    std::mutex m_mutex;
};

// 多目标输出 Sink（同时输出到多个目标）
class MultiSink : public LogSink {
public:
    void add_sink(std::shared_ptr<LogSink> sink) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_sinks.push_back(std::move(sink));
    }

    void write(std::string_view message) override {
        std::lock_guard<std::mutex> lock(m_mutex);
        for (auto& sink : m_sinks) {
            sink->write(message);
        }
    }

    void flush() override {
        std::lock_guard<std::mutex> lock(m_mutex);
        for (auto& sink : m_sinks) {
            sink->flush();
        }
    }

private:
    std::vector<std::shared_ptr<LogSink>> m_sinks;
    std::mutex m_mutex;
};

// ============================================================================
// 第三部分: 日志格式化器
// ============================================================================
// 控制日志消息的格式，支持多种占位符

class LogFormatter {
public:
    /**
     * 格式化日志消息
     * 支持的占位符:
     *   %Y-%m-%d  - 日期 (如 2024-01-15)
     *   %H:%M:%S  - 时间 (如 14:30:45)
     *   %L        - 日志级别 (如 INFO)
     *   %t        - 线程 ID
     *   %s        - 源文件名
     *   %n        - 行号
     *   %f        - 函数名
     *   %m        - 日志消息
     *
     * 示例格式: "[%Y-%m-%d %H:%M:%S] [%L] [%t] %f:%n - %m"
     */
    static std::string format(LogLevel level,
                              std::string_view file,
                              int line,
                              std::string_view function,
                              std::string_view message,
                              const std::string& pattern = "") {
        // 获取当前时间
        auto now = std::chrono::system_clock::now();
        auto time_t_now = std::chrono::system_clock::to_time_t(now);
        auto tm_now = *std::localtime(&time_t_now);
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()) % 1000;

        // 获取线程 ID
        auto thread_id = std::this_thread::get_id();

        std::ostringstream oss;

        // 使用自定义格式还是默认格式
        if (!pattern.empty()) {
            // 自定义格式化（简化实现）
            oss << pattern;  // 占位符替换在实际实现中更复杂
        } else {
            // 默认格式: [时间] [级别] [线程] 文件:行 函数 - 消息
            oss << "[" << std::put_time(&tm_now, "%Y-%m-%d %H:%M:%S")
                << "." << std::setfill('0') << std::setw(3) << ms.count()
                << "] ";
            oss << "[" << log_level_to_string(level) << "] ";
            oss << "[TID:" << thread_id << "] ";

            // 提取文件名（去掉路径前缀）
            std::string_view filename(file);
            auto pos = filename.find_last_of("/\\");
            if (pos != std::string_view::npos) {
                filename = filename.substr(pos + 1);
            }

            oss << filename << ":" << line << " "
                << function << "() - "
                << message << "\n";
        }

        return oss.str();
    }
};

// ============================================================================
// 第四部分: 核心日志器 (Logger)
// ============================================================================
// Logger 是日志系统的核心，负责协调格式化和输出

class Logger {
public:
    // 获取全局默认日志器（单例模式）
    static Logger& instance() {
        static Logger logger;
        return logger;
    }

    // 设置日志级别（低于此级别的日志将被忽略）
    void set_level(LogLevel level) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_level = level;
    }

    LogLevel get_level() const {
        return m_level;
    }

    // 设置输出目标
    void set_sink(std::shared_ptr<LogSink> sink) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_sink = std::move(sink);
    }

    // 设置日志格式
    void set_pattern(const std::string& pattern) {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_pattern = pattern;
    }

    // 核心日志方法
    void log(LogLevel level,
             std::string_view file,
             int line,
             std::string_view function,
             std::string_view message) {
        // 级别过滤
        if (level < m_level) return;

        // 格式化消息
        std::string formatted = LogFormatter::format(
            level, file, line, function, message, m_pattern);

        // 输出
        if (m_sink) {
            m_sink->write(formatted);
            m_sink->flush();
        }
    }

private:
    Logger() : m_level(LogLevel::INFO) {
        // 默认输出到控制台
        m_sink = std::make_shared<ConsoleSink>(true);
    }

    LogLevel m_level;
    std::shared_ptr<LogSink> m_sink;
    std::string m_pattern;
    std::mutex m_mutex;
};

// ============================================================================
// 第五部分: 便捷日志宏
// ============================================================================
// 宏能够自动捕获 __FILE__, __LINE__, __func__
// 使用 do-while(0) 确保宏在所有上下文中安全使用

#define LOG_TRACE(msg) \
    Logger::instance().log(LogLevel::TRACE, __FILE__, __LINE__, __func__, msg)

#define LOG_DEBUG(msg) \
    Logger::instance().log(LogLevel::DEBUG, __FILE__, __LINE__, __func__, msg)

#define LOG_INFO(msg) \
    Logger::instance().log(LogLevel::INFO, __FILE__, __LINE__, __func__, msg)

#define LOG_WARN(msg) \
    Logger::instance().log(LogLevel::WARN, __FILE__, __LINE__, __func__, msg)

#define LOG_ERROR(msg) \
    Logger::instance().log(LogLevel::ERROR, __FILE__, __LINE__, __func__, msg)

#define LOG_FATAL(msg) \
    Logger::instance().log(LogLevel::FATAL, __FILE__, __LINE__, __func__, msg)

// 流式日志宏 - 支持 << 操作符
// 用法: LOG_STREAM(INFO) << "x = " << x << ", y = " << y;
#define LOG_STREAM(level) \
    LogStreamHelper(__FILE__, __LINE__, __func__, LogLevel::level)

// 流式日志辅助类
class LogStreamHelper {
public:
    LogStreamHelper(const char* file, int line, const char* func, LogLevel level)
        : m_file(file), m_line(line), m_func(func), m_level(level) {}

    ~LogStreamHelper() {
        // 析构时输出日志（RAII 模式）
        Logger::instance().log(m_level, m_file, m_line, m_func, m_stream.str());
    }

    // 支持 << 操作符
    template <typename T>
    LogStreamHelper& operator<<(const T& value) {
        m_stream << value;
        return *this;
    }

    // 支持 std::endl 等操纵符
    LogStreamHelper& operator<<(std::ostream& (*manip)(std::ostream&)) {
        manip(m_stream);
        return *this;
    }

private:
    const char* m_file;
    int m_line;
    const char* m_func;
    LogLevel m_level;
    std::ostringstream m_stream;
};

// 格式化日志宏 - 支持 printf 风格
// 用法: LOG_FMT(INFO, "x = %d, name = %s", 42, "test");
template <typename... Args>
std::string format_log_string(const char* fmt, Args... args) {
    // 计算所需缓冲区大小
    int size = std::snprintf(nullptr, 0, fmt, args...);
    if (size <= 0) return std::string(fmt);

    std::string result(size + 1, '\0');
    std::snprintf(result.data(), result.size() + 1, fmt, args...);
    result.resize(size);  // 去掉尾部的 '\0'
    return result;
}

#define LOG_FMT(level, fmt, ...) \
    do { \
        std::string _msg = format_log_string(fmt, __VA_ARGS__); \
        Logger::instance().log(LogLevel::level, __FILE__, __LINE__, \
                               __func__, _msg); \
    } while(0)

// ============================================================================
// 演示代码
// ============================================================================

// 模拟一个简单的业务逻辑，展示日志的实际使用场景
class UserService {
public:
    struct User {
        int id;
        std::string name;
        std::string email;
    };

    // 创建用户 - 展示不同级别的日志使用
    bool create_user(const std::string& name, const std::string& email) {
        LOG_INFO("收到创建用户请求");

        // 参数验证 - 使用 WARN 级别
        if (name.empty()) {
            LOG_WARN("用户名为空，拒绝创建");
            return false;
        }

        if (email.find('@') == std::string::npos) {
            LOG_ERROR("邮箱格式无效: " + email);
            return false;
        }

        // 模拟数据库操作
        User user{++m_next_id, name, email};

        // 调试信息 - 使用 DEBUG 级别
        LOG_DEBUG("用户数据准备完成");

        // 模拟成功创建
        LOG_INFO("用户创建成功: id=" + std::to_string(user.id)
                 + ", name=" + user.name);

        return true;
    }

    // 查询用户 - 展示流式日志
    std::optional<User> find_user(int id) {
        // 使用流式日志宏，语法更自然
        LOG_STREAM(INFO) << "查询用户: id=" << id;

        // 模拟查找
        if (id > 0 && id < m_next_id) {
            User user{id, "User" + std::to_string(id), "user@test.com"};
            LOG_STREAM(DEBUG) << "找到用户: " << user.name;
            return user;
        }

        LOG_STREAM(WARN) << "未找到用户: id=" << id;
        return std::nullopt;
    }

private:
    int m_next_id = 0;
};

void demo_logging() {
    std::cout << "========================================" << std::endl;
    std::cout << "日志系统演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // 配置日志系统
    auto& logger = Logger::instance();

    // 设置日志级别
    logger.set_level(LogLevel::DEBUG);
    std::cout << "日志级别设置为: DEBUG" << std::endl;

    // 1. 基础日志使用
    std::cout << "\n--- 基础日志宏 ---" << std::endl;
    LOG_TRACE("这是一条 TRACE 日志");
    LOG_DEBUG("这是一条 DEBUG 日志");
    LOG_INFO("这是一条 INFO 日志");
    LOG_WARN("这是一条 WARN 日志");
    LOG_ERROR("这是一条 ERROR 日志");

    // 2. 流式日志
    std::cout << "\n--- 流式日志 ---" << std::endl;
    int x = 42;
    double pi = 3.14159;
    std::string name = "测试";

    LOG_STREAM(INFO) << "变量 x = " << x << ", pi = " << pi;
    LOG_STREAM(DEBUG) << "名称: " << name << ", 长度: " << name.size();

    // 3. 格式化日志
    std::cout << "\n--- 格式化日志 ---" << std::endl;
    LOG_FMT(INFO, "格式化输出: 整数=%d, 浮点=%.2f, 字符串=%s",
            100, 3.14, "hello");

    // 4. 级别过滤演示
    std::cout << "\n--- 级别过滤 (设置为 WARN) ---" << std::endl;
    logger.set_level(LogLevel::WARN);
    LOG_DEBUG("这条不会显示");    // 低于 WARN，被过滤
    LOG_INFO("这条也不会显示");   // 低于 WARN，被过滤
    LOG_WARN("这条会显示");
    LOG_ERROR("这条也会显示");

    // 恢复级别
    logger.set_level(LogLevel::DEBUG);

    // 5. 文件输出演示
    std::cout << "\n--- 文件输出 ---" << std::endl;
    try {
        // 创建同时输出到控制台和文件的 Sink
        auto multi_sink = std::make_shared<MultiSink>();
        multi_sink->add_sink(std::make_shared<ConsoleSink>(true));
        multi_sink->add_sink(std::make_shared<FileSink>("app.log"));

        logger.set_sink(multi_sink);
        LOG_INFO("这条日志同时输出到控制台和文件");
        LOG_DEBUG("文件日志测试");

        // 恢复为仅控制台
        logger.set_sink(std::make_shared<ConsoleSink>(true));
        std::cout << "日志已写入 app.log 文件" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "文件日志创建失败: " << e.what() << std::endl;
    }

    // 6. 业务场景演示
    std::cout << "\n--- 业务场景: UserService ---" << std::endl;
    UserService service;
    service.create_user("张三", "zhangsan@example.com");
    service.create_user("", "invalid");           // 警告：用户名为空
    service.create_user("李四", "invalid-email"); // 错误：邮箱无效
    service.find_user(1);
    service.find_user(999);  // 警告：未找到

    // 清理日志文件
    std::remove("app.log");
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║    C++ 日志系统实现 (logging)        ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    demo_logging();

    std::cout << "\n日志系统演示完成。" << std::endl;
    return 0;
}
