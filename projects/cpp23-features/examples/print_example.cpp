/**
 * @file print_example.cpp
 * @brief C++23 std::print/std::println 示例
 *
 * std::print 和 std::println 是 C++23 引入的现代化格式化输出。
 * 它们提供了类似 Python f-string 的格式化语法，比 printf 更安全，比 cout 更简洁。
 *
 * 主要特点：
 * - 类型安全的格式化
 * - 高性能输出
 * - 支持自定义类型的格式化
 * - 支持 Unicode
 *
 * 编译命令：
 * g++ -std=c++23 -o print_example print_example.cpp
 */

#include <iostream>
#include <print>
#include <string>
#include <vector>
#include <map>
#include <format>
#include <ranges>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // std::print 不带换行
    std::print("Hello, ");
    std::print("World!");
    std::print("\n");

    // std::println 带换行
    std::println("Hello, World!");
    std::println("This is C++23");

    // 格式化输出
    std::println("Name: {}, Age: {}", "Alice", 25);
    std::println("Pi is approximately {:.4f}", 3.14159265358979);
}

// ========== 2. 格式化语法 ==========

void format_syntax() {
    std::cout << "\n=== 格式化语法 ===" << std::endl;

    // 基本占位符
    std::println("{}", "Hello");           // 简单替换
    std::println("{0}, {1}", "Hello", "World");  // 位置参数
    std::println("{1}, {0}", "Hello", "World");  // 位置参数调换

    // 命名参数 (需要使用 std::format)
    auto msg = std::format("{name} is {age} years old",
        std::make_format_args(std::make_pair("name", "Alice"), std::make_pair("age", 25)));
    std::println("{}", msg);

    // 对齐和填充
    std::println("|{:>10}|", "right");     // 右对齐，宽度 10
    std::println("|{:<10}|", "left");      // 左对齐，宽度 10
    std::println("|{:^10}|", "center");    // 居中，宽度 10
    std::println("|{:*^10}|", "center");   // 居中，用 * 填充

    // 数字格式化
    std::println("{:d}", 42);              // 十进制
    std::println("{:x}", 255);             // 十六进制
    std::println("{:o}", 255);             // 八进制
    std::println("{:b}", 255);             // 二进制
    std::println("{:#x}", 255);            // 带前缀的十六进制
    std::println("{:#b}", 255);            // 带前缀的二进制
}

// ========== 3. 浮点数格式化 ==========

void floating_point() {
    std::cout << "\n=== 浮点数格式化 ===" << std::endl;

    double pi = 3.14159265358979;

    // 默认格式
    std::println("Default: {}", pi);

    // 指定精度
    std::println("2 decimal places: {:.2f}", pi);
    std::println("4 decimal places: {:.4f}", pi);
    std::println("6 decimal places: {:.6f}", pi);

    // 科学记数法
    std::println("Scientific: {:e}", pi);
    std::println("Scientific (2 decimals): {:.2e}", pi);

    // 通用格式
    std::println("General: {:g}", pi);

    // 百分比
    std::println("Percentage: {:.1%}", 0.85);
}

// ========== 4. 字符串格式化 ==========

void string_formatting() {
    std::cout << "\n=== 字符串格式化 ===" << std::endl;

    std::string name = "Alice";
    int age = 25;

    // 基本字符串格式化
    std::println("{} is {} years old", name, age);

    // 字符串宽度和对齐
    std::println("|{:>20}|", name);        // 右对齐，宽度 20
    std::println("|{:<20}|", name);        // 左对齐，宽度 20
    std::println("|{:^20}|", name);        // 居中，宽度 20

    // 填充字符
    std::println("|{:*^20}|", name);       // 用 * 填充
    std::println("|{:-^20}|", name);       // 用 - 填充

    // 截断字符串
    std::println("{:.3}", "Hello World");  // 只取前 3 个字符
}

// ========== 5. 容器格式化 ==========

// 自定义类型的格式化
struct Point {
    int x, y;
};

// 为 Point 特化 std::formatter
template<>
struct std::formatter<Point> : std::formatter<std::string> {
    auto format(const Point& p, auto& ctx) const {
        return std::format_to(ctx.out(), "({}, {})", p.x, p.y);
    }
};

// 为 vector 特化 std::formatter
template<typename T>
struct std::formatter<std::vector<T>> : std::formatter<std::string> {
    auto format(const std::vector<T>& vec, auto& ctx) const {
        auto out = ctx.out();
        *out++ = '[';
        for (size_t i = 0; i < vec.size(); ++i) {
            if (i > 0) {
                *out++ = ',';
                *out++ = ' ';
            }
            out = std::format_to(out, "{}", vec[i]);
        }
        *out++ = ']';
        return out;
    }
};

void container_formatting() {
    std::cout << "\n=== 容器格式化 ===" << std::endl;

    // 自定义类型格式化
    Point p = {3, 4};
    std::println("Point: {}", p);

    // vector 格式化
    std::vector<int> nums = {1, 2, 3, 4, 5};
    std::println("Vector: {}", nums);

    // 嵌套容器
    std::vector<std::vector<int>> matrix = {{1, 2}, {3, 4}, {5, 6}};
    std::println("Matrix: {}", matrix);
}

// ========== 6. 输出到不同目标 ==========

void output_targets() {
    std::cout << "\n=== 输出到不同目标 ===" << std::endl;

    // 输出到标准输出
    std::println("To stdout");

    // 输出到标准错误
    std::println(stderr, "To stderr");

    // 输出到文件
    // std::FILE* file = fopen("output.txt", "w");
    // std::println(file, "To file");
    // fclose(file);

    // 输出到字符串
    std::string result = std::format("Formatted: {}", 42);
    std::println("String result: {}", result);
}

// ========== 7. 实际应用：日志系统 ==========

enum class LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR
};

// 日志格式化
template<>
struct std::formatter<LogLevel> : std::formatter<std::string> {
    auto format(LogLevel level, auto& ctx) const {
        std::string_view level_str;
        switch (level) {
            case LogLevel::DEBUG:   level_str = "DEBUG"; break;
            case LogLevel::INFO:    level_str = "INFO"; break;
            case LogLevel::WARNING: level_str = "WARN"; break;
            case LogLevel::ERROR:   level_str = "ERROR"; break;
        }
        return std::format_to(ctx.out(), "{}", level_str);
    }
};

class Logger {
public:
    static void log(LogLevel level, const std::string& message) {
        std::println("[{:>5}] {}", level, message);
    }

    static void debug(const std::string& msg) { log(LogLevel::DEBUG, msg); }
    static void info(const std::string& msg) { log(LogLevel::INFO, msg); }
    static void warning(const std::string& msg) { log(LogLevel::WARNING, msg); }
    static void error(const std::string& msg) { log(LogLevel::ERROR, msg); }
};

void logging_example() {
    std::cout << "\n=== 实际应用：日志系统 ===" << std::endl;

    Logger::debug("Starting application");
    Logger::info("Loading configuration");
    Logger::warning("Configuration file not found, using defaults");
    Logger::error("Failed to connect to database");
}

// ========== 8. 性能对比 ==========

void performance_comparison() {
    std::cout << "\n=== 性能对比 ===" << std::endl;

    const int iterations = 1000;

    // std::print 性能测试
    auto start1 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        std::print("", i);  // 抑制输出
    }
    auto end1 = std::chrono::high_resolution_clock::now();
    auto duration1 = std::chrono::duration_cast<std::chrono::microseconds>(end1 - start1);

    // std::cout 性能测试
    auto start2 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        std::cout << i;
    }
    auto end2 = std::chrono::high_resolution_clock::now();
    auto duration2 = std::chrono::duration_cast<std::chrono::microseconds>(end2 - start2);

    std::println("std::print: {} microseconds", duration1.count());
    std::println("std::cout: {} microseconds", duration2.count());
    std::println("std::print is {:.1f}x faster",
        static_cast<double>(duration2.count()) / duration1.count());
}

// ========== 9. 格式化特性和技巧 ==========

void formatting_tips() {
    std::cout << "\n=== 格式化技巧 ===" << std::endl;

    // 转义大括号
    std::println("{{escaped}}");  // 输出: {escaped}

    // 动态宽度和精度
    int width = 15;
    int precision = 3;
    double value = 3.14159;
    std::println("{:{}.{}}", value, width, precision);

    // 格式化到迭代器
    std::string buffer;
    std::format_to(std::back_inserter(buffer), "Formatted: {}", 42);
    std::println("Buffer: {}", buffer);

    // 格式化当前时间
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::println("Current time: {}", std::ctime(&time_t));
}

int main() {
    std::cout << "C++23 std::print/std::println 示例\n" << std::endl;

    basic_usage();
    format_syntax();
    floating_point();
    string_formatting();
    container_formatting();
    output_targets();
    logging_example();
    performance_comparison();
    formatting_tips();

    return 0;
}
