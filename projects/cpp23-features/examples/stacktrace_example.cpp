/**
 * @file stacktrace_example.cpp
 * @brief C++23 std::stacktrace 示例
 *
 * std::stacktrace 是 C++23 引入的堆栈跟踪工具，用于在运行时获取调用栈信息。
 * 它对于调试和错误报告非常有用。
 *
 * 主要特点：
 * - 运行时获取调用栈
 * - 跨平台支持
 * - 便于调试和错误报告
 * - 可以捕获当前堆栈
 *
 * 编译命令：
 * g++ -std=c++23 -o stacktrace_example stacktrace_example.cpp
 * 注意：某些系统可能需要链接额外的库
 */

#include <iostream>
#include <stacktrace>
#include <string>
#include <vector>
#include <stdexcept>
#include <sstream>

// ========== 1. 基本用法 ==========

// 获取当前堆栈
void print_current_stacktrace() {
    std::stacktrace st = std::stacktrace::current();
    std::cout << "Current stacktrace:" << std::endl;
    std::cout << st << std::endl;
}

// 嵌套函数调用
void function_c() {
    std::cout << "=== In function_c ===" << std::endl;
    print_current_stacktrace();
}

void function_b() {
    function_c();
}

void function_a() {
    function_b();
}

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 获取当前堆栈
    std::stacktrace st = std::stacktrace::current();
    std::cout << "Stacktrace size: " << st.size() << std::endl;

    // 打印堆栈
    std::cout << "\nFull stacktrace:" << std::endl;
    std::cout << to_string(st) << std::endl;

    // 嵌套调用
    std::cout << "\nNested function calls:" << std::endl;
    function_a();
}

// ========== 2. 堆栈帧信息 ==========

void frame_info() {
    std::cout << "\n=== 堆栈帧信息 ===" << std::endl;

    std::stacktrace st = std::stacktrace::current();

    for (size_t i = 0; i < st.size(); ++i) {
        const auto& frame = st[i];
        std::cout << "Frame " << i << ":" << std::endl;
        std::cout << "  Description: " << frame.description() << std::endl;
        std::cout << "  Source file: " << frame.source_file() << std::endl;
        std::cout << "  Source line: " << frame.source_line() << std::endl;
        std::cout << "  Native address: " << frame.native_handle() << std::endl;
        std::cout << std::endl;
    }
}

// ========== 3. 异常中的堆栈跟踪 ==========

class StackTraceException : public std::runtime_error {
private:
    std::stacktrace trace_;

public:
    StackTraceException(const std::string& msg)
        : std::runtime_error(msg), trace_(std::stacktrace::current()) {}

    const std::stacktrace& stacktrace() const { return trace_; }
};

void risky_function() {
    throw StackTraceException("Something went wrong!");
}

void caller_function() {
    risky_function();
}

void exception_example() {
    std::cout << "\n=== 异常中的堆栈跟踪 ===" << std::endl;

    try {
        caller_function();
    } catch (const StackTraceException& e) {
        std::cout << "Exception: " << e.what() << std::endl;
        std::cout << "Stacktrace:" << std::endl;
        std::cout << e.stacktrace() << std::endl;
    }
}

// ========== 4. 堆栈跟踪格式化 ==========

std::string format_stacktrace(const std::stacktrace& st, int max_frames = 10) {
    std::ostringstream oss;
    oss << "Stacktrace (" << st.size() << " frames):" << std::endl;

    size_t count = std::min(static_cast<size_t>(max_frames), st.size());
    for (size_t i = 0; i < count; ++i) {
        const auto& frame = st[i];
        oss << "  #" << i << ": " << frame.description();
        if (!frame.source_file().empty()) {
            oss << " at " << frame.source_file() << ":" << frame.source_line();
        }
        oss << std::endl;
    }

    if (st.size() > static_cast<size_t>(max_frames)) {
        oss << "  ... and " << (st.size() - max_frames) << " more frames" << std::endl;
    }

    return oss.str();
}

void formatting_example() {
    std::cout << "\n=== 堆栈跟踪格式化 ===" << std::endl;

    std::stacktrace st = std::stacktrace::current();
    std::cout << format_stacktrace(st, 5);
}

// ========== 5. 实际应用：调试工具 ==========

class Debugger {
public:
    static void breakpoint(const std::string& label = "") {
        std::stacktrace st = std::stacktrace::current();

        std::cout << "=== BREAKPOINT";
        if (!label.empty()) {
            std::cout << ": " << label;
        }
        std::cout << " ===" << std::endl;

        std::cout << format_stacktrace(st, 3);
        std::cout << "================================" << std::endl;
    }

    static void trace(const std::string& function_name) {
        std::cout << "[TRACE] Entering: " << function_name << std::endl;
    }
};

void debuggable_function() {
    Debugger::trace("debuggable_function");
    Debugger::breakpoint("Inside debuggable_function");

    // Some work
    int x = 42;
    std::cout << "x = " << x << std::endl;

    Debugger::breakpoint("After computation");
}

void debugging_example() {
    std::cout << "\n=== 实际应用：调试工具 ===" << std::endl;

    debuggable_function();
}

// ========== 6. 性能监控 ==========

class PerformanceMonitor {
private:
    std::string name_;
    std::stacktrace start_trace_;

public:
    PerformanceMonitor(const std::string& name)
        : name_(name), start_trace_(std::stacktrace::current()) {
        std::cout << "[PERF] Starting: " << name_ << std::endl;
    }

    ~PerformanceMonitor() {
        std::cout << "[PERF] Ending: " << name_ << std::endl;
    }

    void print_start_trace() const {
        std::cout << "Start trace:" << std::endl;
        std::cout << format_stacktrace(start_trace_, 2);
    }
};

void monitored_function() {
    PerformanceMonitor pm("monitored_function");
    pm.print_start_trace();

    // Simulate work
    volatile int sum = 0;
    for (int i = 0; i < 1000000; ++i) {
        sum += i;
    }
}

void performance_monitoring() {
    std::cout << "\n=== 性能监控 ===" << std::endl;

    monitored_function();
}

// ========== 7. 错误报告系统 ==========

class ErrorReporter {
public:
    struct ErrorInfo {
        std::string message;
        std::string file;
        int line;
        std::stacktrace trace;
    };

    static void report(const std::string& message, const std::string& file, int line) {
        ErrorInfo info{
            message,
            file,
            line,
            std::stacktrace::current()
        };

        std::cout << "=== ERROR REPORT ===" << std::endl;
        std::cout << "Message: " << info.message << std::endl;
        std::cout << "Location: " << info.file << ":" << info.line << std::endl;
        std::cout << "Stacktrace:" << std::endl;
        std::cout << format_stacktrace(info.trace, 5);
        std::cout << "====================" << std::endl;
    }
};

#define REPORT_ERROR(msg) ErrorReporter::report(msg, __FILE__, __LINE__)

void error_prone_function() {
    // Simulate an error
    REPORT_ERROR("Null pointer dereference");
}

void error_reporting() {
    std::cout << "\n=== 错误报告系统 ===" << std::endl;

    error_prone_function();
}

// ========== 8. 堆栈跟踪比较 ==========

void compare_stacktraces() {
    std::cout << "\n=== 堆栈跟踪比较 ===" << std::endl;

    std::stacktrace st1 = std::stacktrace::current();
    std::stacktrace st2 = std::stacktrace::current();

    std::cout << "Stacktrace 1 size: " << st1.size() << std::endl;
    std::cout << "Stacktrace 2 size: " << st2.size() << std::endl;

    // 比较堆栈
    std::cout << "Stacktraces are " << (st1 == st2 ? "equal" : "different") << std::endl;
}

int main() {
    std::cout << "C++23 std::stacktrace 示例\n" << std::endl;

    basic_usage();
    frame_info();
    exception_example();
    formatting_example();
    debugging_example();
    performance_monitoring();
    error_reporting();
    compare_stacktraces();

    return 0;
}
