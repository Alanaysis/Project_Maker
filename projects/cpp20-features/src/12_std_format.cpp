/**
 * 12_std_format.cpp - C++20 std::format
 *
 * std::format 是 C++20 引入的类型安全格式化库，类似 Python 的 format。
 *
 * 核心要点：
 * 1. 基本格式化语法 {:[fill][align][sign][#][0][width][.precision][type]}
 * 2. 位置参数和命名参数
 * 3. 自定义类型格式化
 * 4. 格式化到字符串和输出流
 */

#include <iostream>
#include <string>
#include <format>
#include <vector>
#include <map>

// ============================================================
// 1. 基本格式化
// ============================================================

void basic_format() {
    std::cout << "【1. 基本格式化】\n";

    // 简单替换
    auto s1 = std::format("Hello, {}!", "World");
    std::cout << s1 << "\n";

    // 多个参数
    auto s2 = std::format("{} is {} years old", "Alice", 25);
    std::cout << s2 << "\n";

    // 数字格式化
    auto s3 = std::format("PI = {:.4f}", 3.14159265);
    std::cout << s3 << "\n";

    // 十六进制和八进制
    auto s4 = std::format("hex: {:#x}, oct: {:#o}, bin: {:#b}", 255, 255, 255);
    std::cout << s4 << "\n\n";
}

// ============================================================
// 2. 对齐和填充
// ============================================================

void alignment() {
    std::cout << "【2. 对齐和填充】\n";

    // 宽度和对齐
    std::cout << std::format("|{:<10}|", "left") << "\n";     // 左对齐
    std::cout << std::format("|{:>10}|", "right") << "\n";    // 右对齐
    std::cout << std::format("|{:^10}|", "center") << "\n";   // 居中
    std::cout << std::format("|{:*^10}|", "fill") << "\n";    // 填充字符
    std::cout << std::format("|{:0>5}|", 42) << "\n";         // 数字补零
    std::cout << "\n";
}

// ============================================================
// 3. 数字格式化
// ============================================================

void number_format() {
    std::cout << "【3. 数字格式化】\n";

    // 整数格式
    std::cout << std::format("dec: {:d}, hex: {:x}, oct: {:o}", 42, 42, 42) << "\n";
    std::cout << std::format("带前缀: {:#x}, {:#o}, {:#b}", 255, 255, 8) << "\n";

    // 浮点格式
    double pi = 3.14159265358979;
    std::cout << std::format("默认: {}", pi) << "\n";
    std::cout << std::format("固定: {:.2f}", pi) << "\n";
    std::cout << std::format("科学: {:.4e}", pi) << "\n";
    std::cout << std::format("通用: {:.4g}", pi) << "\n";

    // 正号显示
    std::cout << std::format("{:+}", 42) << "\n";
    std::cout << std::format("{:+}", -42) << "\n";

    // 千分位分隔（C++26 部分编译器支持）
    // std::cout << std::format("{:L}", 1234567) << "\n";
    std::cout << "\n";
}

// ============================================================
// 4. 位置参数
// ============================================================

void positional_args() {
    std::cout << "【4. 位置参数】\n";

    // 使用位置索引
    auto s1 = std::format("{1} and {0}", "first", "second");
    std::cout << s1 << "\n";

    // 重复使用同一参数
    auto s2 = std::format("{0} + {0} = {1}", 5, 10);
    std::cout << s2 << "\n\n";
}

// ============================================================
// 5. 自定义类型格式化
// ============================================================

struct Point {
    int x, y;
};

// 特化 std::formatter
template <>
struct std::formatter<Point> {
    constexpr auto parse(std::format_parse_context& ctx) {
        return ctx.begin();
    }

    auto format(const Point& p, std::format_context& ctx) const {
        return std::format_to(ctx.out(), "({}, {})", p.x, p.y);
    }
};

struct Student {
    std::string name;
    int score;
};

template <>
struct std::formatter<Student> {
    char presentation = 'f';  // 'f' = full, 's' = short

    constexpr auto parse(std::format_parse_context& ctx) {
        auto it = ctx.begin();
        if (it != ctx.end() && (*it == 'f' || *it == 's')) {
            presentation = *it++;
        }
        return it;
    }

    auto format(const Student& s, std::format_context& ctx) const {
        if (presentation == 's') {
            return std::format_to(ctx.out(), "{}", s.name);
        }
        return std::format_to(ctx.out(), "{}({})", s.name, s.score);
    }
};

void custom_format() {
    std::cout << "【5. 自定义类型格式化】\n";

    Point p{3, 4};
    std::cout << std::format("Point: {}\n", p);

    Student s{"Alice", 95};
    std::cout << std::format("Student full: {}\n", s);
    std::cout << std::format("Student short: {:s}\n", s);
    std::cout << "\n";
}

// ============================================================
// 6. 实际应用
// ============================================================

void practical_usage() {
    std::cout << "【6. 实际应用】\n";

    // 表格格式化
    std::cout << std::format("| {:<10} | {:>6} | {:>8} |\n", "Name", "Score", "Grade");
    std::cout << std::format("|{:-<12}|{:-<8}|{:-<10}|\n", "", "", "");
    std::cout << std::format("| {:<10} | {:>6} | {:>8} |\n", "Alice", 95, "A");
    std::cout << std::format("| {:<10} | {:>6} | {:>8} |\n", "Bob", 82, "B");
    std::cout << std::format("| {:<10} | {:>6} | {:>8} |\n", "Charlie", 78, "C");

    // 日志格式化
    std::cout << "\n日志格式化:\n";
    auto log = [](const std::string& level, const std::string& msg) {
        std::cout << std::format("[{:<7}] {}\n", level, msg);
    };
    log("INFO", "Application started");
    log("WARNING", "Low memory");
    log("ERROR", "Connection failed");

    // 路径/URL 格式化
    std::string host = "example.com";
    int port = 8080;
    std::string path = "/api/v1";
    std::cout << "\nURL: " << std::format("http://{}:{}{}", host, port, path) << "\n\n";
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 std::format 示例 ===\n\n";

    basic_format();
    alignment();
    number_format();
    positional_args();
    custom_format();
    practical_usage();

    std::cout << "=== std::format 示例完成 ===\n";
    return 0;
}
