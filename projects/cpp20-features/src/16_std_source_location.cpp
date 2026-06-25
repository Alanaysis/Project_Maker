/**
 * 16_std_source_location.cpp - C++20 std::source_location
 *
 * std::source_location 替代了 __FILE__, __LINE__, __func__ 等宏。
 *
 * 核心要点：
 * 1. 编译期获取源代码位置信息
 * 2. 替代 __FILE__, __LINE__, __FUNCTION__ 宏
 * 3. 支持 constexpr
 * 4. 更优雅的调试和日志支持
 */

#include <iostream>
#include <source_location>
#include <string>
#include <vector>
#include <stdexcept>
#include <chrono>
#include <format>

// ============================================================
// 1. 基本用法
// ============================================================

void log(const std::string& message,
         std::source_location loc = std::source_location::current()) {
    std::cout << "[" << loc.file_name() << ":" << loc.line() << "] "
              << message << "\n";
}

// ============================================================
// 2. 调试信息输出
// ============================================================

void debug_info(std::source_location loc = std::source_location::current()) {
    std::cout << "函数: " << loc.function_name() << "\n";
    std::cout << "文件: " << loc.file_name() << "\n";
    std::cout << "行号: " << loc.line() << "\n";
    std::cout << "列号: " << loc.column() << "\n\n";
}

// ============================================================
// 3. 日志级别封装
// ============================================================

enum class LogLevel { Debug, Info, Warning, Error };

std::string to_string(LogLevel level) {
    switch (level) {
        case LogLevel::Debug:   return "DEBUG";
        case LogLevel::Info:    return "INFO";
        case LogLevel::Warning: return "WARN";
        case LogLevel::Error:   return "ERROR";
    }
    return "UNKNOWN";
}

class Logger {
public:
    static void log(LogLevel level, const std::string& message,
                    std::source_location loc = std::source_location::current()) {
        std::cout << "[" << to_string(level) << "] "
                  << loc.file_name() << ":" << loc.line() << " - "
                  << message << "\n";
    }
};

// ============================================================
// 4. 异常包装
// ============================================================

template <typename Exception>
void throw_with_location(
    const std::string& message,
    std::source_location loc = std::source_location::current()) {
    throw Exception(message + " (at " + loc.file_name() + ":" +
                    std::to_string(loc.line()) + ")");
}

// ============================================================
// 5. 性能测量
// ============================================================

struct ScopeTimer {
    std::source_location loc;
    std::chrono::high_resolution_clock::time_point start;

    ScopeTimer(std::source_location l = std::source_location::current())
        : loc(l), start(std::chrono::high_resolution_clock::now()) {}

    ~ScopeTimer() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        std::cout << "[TIMER] " << loc.function_name() << " took "
                  << duration.count() << " μs\n";
    }
};

// ============================================================
// 6. 断言增强
// ============================================================

void assert_msg(bool condition, const std::string& msg,
                std::source_location loc = std::source_location::current()) {
    if (!condition) {
        std::cerr << "Assertion failed: " << msg << "\n"
                  << "  at " << loc.file_name() << ":" << loc.line() << "\n"
                  << "  in " << loc.function_name() << "\n";
        std::abort();
    }
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 std::source_location 示例 ===\n\n";

    // 1. 基本日志
    std::cout << "【1. 带位置信息的日志】\n";
    log("应用启动");
    log("初始化完成");
    std::cout << "\n";

    // 2. 调试信息
    std::cout << "【2. 详细调试信息】\n";
    debug_info();

    // 3. 日志级别
    std::cout << "【3. 日志级别】\n";
    Logger::log(LogLevel::Debug, "调试信息");
    Logger::log(LogLevel::Info, "应用启动");
    Logger::log(LogLevel::Warning, "内存使用率高");
    Logger::log(LogLevel::Error, "连接失败");
    std::cout << "\n";

    // 4. 嵌套调用中的位置追踪
    std::cout << "【4. 嵌套调用追踪】\n";
    log("main 函数开始");

    auto inner = []() {
        log("lambda 内部调用");
    };
    inner();

    log("main 函数结束");
    std::cout << "\n";

    // 5. 异常包装
    std::cout << "【5. 异常包装】\n";
    try {
        throw_with_location<std::runtime_error>("Something went wrong");
    } catch (const std::exception& e) {
        std::cout << "捕获异常: " << e.what() << "\n\n";
    }

    // 6. 断言增强
    std::cout << "【6. 增强断言】\n";
    assert_msg(1 + 1 == 2, "数学正确");
    assert_msg(42 > 0, "42 是正数");
    std::cout << "\n";

    // 7. 与宏对比
    std::cout << "【7. source_location vs 宏】\n";
    std::cout << "+-------------------+-------------------+\n";
    std::cout << "| 宏                | source_location   |\n";
    std::cout << "+-------------------+-------------------+\n";
    std::cout << "| __FILE__          | file_name()       |\n";
    std::cout << "| __LINE__          | line()            |\n";
    std::cout << "| __FUNCTION__      | function_name()   |\n";
    std::cout << "| __func__          | function_name()   |\n";
    std::cout << "| (无)              | column()          |\n";
    std::cout << "+-------------------+-------------------+\n";
    std::cout << "优势: 类型安全、constexpr、无需宏\n";

    std::cout << "\n=== source_location 示例完成 ===\n";
    return 0;
}
