/**
 * 02_ranges.cpp - C++20 范围库 (Ranges)
 *
 * Ranges 是对 STL 算法的重大升级，支持惰性求值和管道操作。
 *
 * 核心要点：
 * 1. 视图 (Views) - 惰性、可组合的数据变换
 * 2. 管道操作符 | - 链式组合算法
 * 3. 范围适配器 (range adaptors)
 * 4. 投影 (projections)
 * 5. 常用视图：filter, transform, take, drop, join, split
 */

#include <iostream>
#include <vector>
#include <list>
#include <string>
#include <ranges>
#include <algorithm>
#include <numeric>
#include <functional>
#include <cmath>

// 辅助函数：打印范围
template <std::ranges::range R>
void print_range(R&& range, const std::string& label) {
    std::cout << label << ": [";
    bool first = true;
    for (const auto& item : range) {
        if (!first) std::cout << ", ";
        std::cout << item;
        first = false;
    }
    std::cout << "]\n";
}

// ============================================================
// 1. 基础视图 (Basic Views)
// ============================================================

void basic_views() {
    std::cout << "【1. 基础视图】\n";

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    print_range(data, "原始数据");

    // views::filter - 过滤
    auto evens = data | std::views::filter([](int x) { return x % 2 == 0; });
    print_range(evens, "偶数");

    // views::transform - 映射变换
    auto squares = data | std::views::transform([](int x) { return x * x; });
    print_range(squares, "平方");

    // views::take - 取前 N 个
    auto first3 = data | std::views::take(3);
    print_range(first3, "前3个");

    // views::drop - 跳过前 N 个
    auto skip3 = data | std::views::drop(3);
    print_range(skip3, "跳过前3个");

    // views::reverse - 反转
    auto reversed = data | std::views::reverse;
    print_range(reversed, "反转");
    std::cout << "\n";
}

// ============================================================
// 2. 管道操作 (Pipe Operations)
// ============================================================

void pipe_operations() {
    std::cout << "【2. 管道操作 - 链式组合】\n";

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 组合：过滤偶数 -> 平方 -> 取前 3 个
    auto result = data
        | std::views::filter([](int x) { return x % 2 == 0; })
        | std::views::transform([](int x) { return x * x; })
        | std::views::take(3);
    print_range(result, "偶数的平方取前3");

    // 组合：生成无限序列 -> 取前 10 个 -> 过滤
    auto naturals = std::views::iota(1);  // 无限自然数序列
    auto first5_odd = naturals
        | std::views::filter([](int x) { return x % 2 != 0; })
        | std::views::take(5);
    print_range(first5_odd, "前5个奇数");

    // 手动模拟带索引遍历
    std::cout << "带索引的数据: ";
    for (size_t i = 0; i < data.size(); ++i) {
        std::cout << "(" << i << ":" << data[i] << ") ";
    }
    std::cout << "\n\n";
}

// ============================================================
// 3. 常用视图详解
// ============================================================

void detailed_views() {
    std::cout << "【3. 常用视图详解】\n";

    // views::iota - 生成整数范围
    auto range_1_to_10 = std::views::iota(1, 11);
    print_range(range_1_to_10, "iota(1,11)");

    // views::take_while - 满足条件时取元素
    std::vector<int> data = {1, 4, 6, 8, 3, 2};
    auto small_ones = data | std::views::take_while([](int x) { return x < 5; });
    print_range(small_ones, "take_while < 5");

    // views::drop_while - 满足条件时跳过
    auto after_small = data | std::views::drop_while([](int x) { return x < 5; });
    print_range(after_small, "drop_while < 5");

    // views::transform + views::filter 组合
    std::vector<std::string> words = {"hello", "world", "cpp", "ranges", "is", "awesome"};
    auto long_upper = words
        | std::views::filter([](const std::string& s) { return s.size() > 3; })
        | std::views::transform([](const std::string& s) {
            std::string upper = s;
            std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);
            return upper;
        });
    print_range(long_upper, "长度>3的词大写");

    // views::join - 展平嵌套范围
    std::vector<std::vector<int>> nested = {{1, 2}, {3, 4}, {5}};
    auto flat = nested | std::views::join;
    print_range(flat, "展平嵌套");

    // views::split - 按分隔符切分
    std::string csv = "hello,world,cpp,ranges";
    auto parts = csv | std::views::split(',');
    std::cout << "split CSV: ";
    for (auto&& part : parts) {
        std::cout << "[";
        for (auto c : part) std::cout << c;
        std::cout << "] ";
    }
    std::cout << "\n\n";
}

// ============================================================
// 4. 范围算法 (Range Algorithms)
// ============================================================

void range_algorithms() {
    std::cout << "【4. 范围算法】\n";

    std::vector<int> data = {5, 3, 8, 1, 9, 2, 7, 4, 6};

    // ranges::sort - 排序
    auto sorted = data;
    std::ranges::sort(sorted);
    print_range(sorted, "排序");

    // ranges::sort with projection - 使用投影排序
    struct Student {
        std::string name;
        int score;
    };

    std::vector<Student> students = {
        {"Alice", 85}, {"Bob", 92}, {"Charlie", 78},
        {"Diana", 95}, {"Eve", 88}
    };

    // 按分数排序（使用投影）
    std::ranges::sort(students, {}, &Student::score);
    std::cout << "按分数排序: ";
    for (const auto& s : students) {
        std::cout << s.name << "(" << s.score << ") ";
    }
    std::cout << "\n";

    // ranges::find - 查找
    auto it = std::ranges::find(data, 8);
    if (it != data.end()) {
        std::cout << "找到 8, 位置 = " << std::distance(data.begin(), it) << "\n";
    }

    // ranges::count_if - 计数
    auto count = std::ranges::count_if(data, [](int x) { return x > 5; });
    std::cout << "大于5的元素个数: " << count << "\n";

    // ranges::all_of, any_of, none_of
    std::cout << "所有元素 > 0: " << std::boolalpha << std::ranges::all_of(data, [](int x) { return x > 0; }) << "\n";
    std::cout << "存在元素 > 8: " << std::ranges::any_of(data, [](int x) { return x > 8; }) << "\n";
    std::cout << "没有元素 > 10: " << std::ranges::none_of(data, [](int x) { return x > 10; }) << "\n";

    // ranges::to (C++23, 手动收集)
    auto filtered = data | std::views::filter([](int x) { return x > 5; });
    std::vector<int> result(filtered.begin(), filtered.end());
    print_range(result, "> 5 的元素收集到 vector");

    std::cout << "\n";
}

// ============================================================
// 5. 自定义视图和惰性求值
// ============================================================

void lazy_evaluation() {
    std::cout << "【5. 惰性求值演示】\n";

    // 视图是惰性的 - 不会立即执行计算
    int call_count = 0;
    auto expensive = [&call_count](int x) {
        ++call_count;
        return x * x;  // 模拟昂贵计算
    };

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 创建视图链（不执行计算）
    auto pipeline = data
        | std::views::transform(expensive)
        | std::views::filter([](int x) { return x > 20; });

    std::cout << "视图已创建, 调用次数: " << call_count << "\n";

    // 只有遍历时才执行计算
    std::cout << "结果: ";
    for (auto val : pipeline) {
        std::cout << val << " ";
    }
    std::cout << "\n实际调用次数: " << call_count << " (不是10次，因为惰性求值)\n\n";
}

// ============================================================
// 6. 实际应用：数据处理管道
// ============================================================

void real_world_example() {
    std::cout << "【6. 实际应用：数据处理管道】\n";

    // 模拟日志数据
    struct LogEntry {
        std::string level;
        std::string message;
        int timestamp;
    };

    std::vector<LogEntry> logs = {
        {"INFO", "Server started", 100},
        {"ERROR", "Connection failed", 105},
        {"INFO", "Request received", 110},
        {"WARN", "High memory usage", 115},
        {"ERROR", "Timeout occurred", 120},
        {"INFO", "Response sent", 125},
        {"ERROR", "Database error", 130},
        {"DEBUG", "Variable state", 135}
    };

    // 管道：过滤错误日志 -> 提取消息 -> 取前2个
    auto error_messages = logs
        | std::views::filter([](const LogEntry& e) { return e.level == "ERROR"; })
        | std::views::transform([](const LogEntry& e) { return e.message; })
        | std::views::take(2);

    std::cout << "错误日志消息（前2条）:\n";
    for (const auto& msg : error_messages) {
        std::cout << "  - " << msg << "\n";
    }

    // 生成斐波那契数列
    std::cout << "\n斐波那契前10个: ";
    auto fib = std::views::iota(0, 10)
        | std::views::transform([](int n) {
            int a = 0, b = 1;
            for (int i = 0; i < n; ++i) { int t = a + b; a = b; b = t; }
            return a;
        });
    for (auto v : fib) std::cout << v << " ";
    std::cout << "\n\n";
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 范围库 (Ranges) 示例 ===\n\n";

    basic_views();
    pipe_operations();
    detailed_views();
    range_algorithms();
    lazy_evaluation();
    real_world_example();

    std::cout << "=== Ranges 示例完成 ===\n";
    return 0;
}
