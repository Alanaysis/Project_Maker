/**
 * @file optional_ranges_example.cpp
 * @brief C++23 std::optional 范围转换示例
 *
 * C++23 改进了 std::optional 与 ranges 的结合使用。
 *
 * 主要特点：
 * - optional 可以转换为范围
 * - 支持 ranges 算法
 * - 简化空值处理
 * - 支持 monadic 操作
 *
 * 编译命令：
 * g++ -std=c++23 -o optional_ranges_example optional_ranges_example.cpp
 */

#include <iostream>
#include <optional>
#include <vector>
#include <ranges>
#include <algorithm>
#include <string>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // optional 可以视为 0 或 1 个元素的范围
    std::optional<int> opt1 = 42;
    std::optional<int> opt2 = std::nullopt;

    // 遍历 optional
    std::cout << "opt1 has value: " << opt1.has_value() << std::endl;
    if (opt1) {
        std::cout << "opt1 value: " << *opt1 << std::endl;
    }

    std::cout << "opt2 has value: " << opt2.has_value() << std::endl;
}

// ========== 2. 实际应用：数据过滤 ==========

void data_filtering() {
    std::cout << "\n=== 实际应用：数据过滤 ===" << std::endl;

    // 模拟可能为空的数据
    std::vector<std::optional<int>> data = {1, std::nullopt, 3, std::nullopt, 5};

    // 过滤掉空值
    auto filtered = data
        | std::views::filter([](const auto& opt) { return opt.has_value(); })
        | std::views::transform([](const auto& opt) { return *opt; })
        | std::ranges::to<std::vector>();

    std::cout << "Filtered data: ";
    for (int n : filtered) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 3. 实际应用：错误处理 ==========

std::optional<int> parse_int(const std::string& str) {
    try {
        return std::stoi(str);
    } catch (...) {
        return std::nullopt;
    }
}

void error_handling() {
    std::cout << "\n=== 实际应用：错误处理 ===" << std::endl;

    std::vector<std::string> inputs = {"123", "abc", "456", "xyz", "789"};

    // 解析所有输入
    auto results = inputs
        | std::views::transform([](const std::string& s) { return parse_int(s); })
        | std::views::filter([](const auto& opt) { return opt.has_value(); })
        | std::views::transform([](const auto& opt) { return *opt; })
        | std::ranges::to<std::vector>();

    std::cout << "Parsed values: ";
    for (int n : results) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 4. 实际应用：数据转换 ==========

void data_transformation() {
    std::cout << "\n=== 实际应用：数据转换 ===" << std::endl;

    // 模拟数据库查询结果
    std::vector<std::optional<std::string>> names = {
        "Alice", std::nullopt, "Charlie", std::nullopt, "Eve"
    };

    // 转换为有效名称列表
    auto valid_names = names
        | std::views::filter([](const auto& opt) { return opt.has_value(); })
        | std::views::transform([](const auto& opt) { return *opt; })
        | std::ranges::to<std::vector>();

    std::cout << "Valid names: ";
    for (const auto& name : valid_names) std::cout << name << " ";
    std::cout << std::endl;
}

// ========== 5. 实际应用：默认值处理 ==========

void default_values() {
    std::cout << "\n=== 实际应用：默认值处理 ===" << std::endl;

    std::vector<std::optional<int>> data = {1, std::nullopt, 3, std::nullopt, 5};

    // 使用默认值替换空值
    auto with_defaults = data
        | std::views::transform([](const auto& opt) { return opt.value_or(0); })
        | std::ranges::to<std::vector>();

    std::cout << "With defaults: ";
    for (int n : with_defaults) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 6. 实际应用：链式操作 ==========

void chaining_operations() {
    std::cout << "\n=== 实际应用：链式操作 ===" << std::endl;

    // 链式 monadic 操作
    auto result = std::optional<int>(10)
        .transform([](int x) { return x * 2; })
        .transform([](int x) { return x + 5; })
        .and_then([](int x) -> std::optional<int> {
            if (x > 20) return x;
            return std::nullopt;
        });

    if (result) {
        std::cout << "Result: " << *result << std::endl;
    } else {
        std::cout << "Result: nullopt" << std::endl;
    }
}

// ========== 7. 实际应用：数据验证 ==========

void data_validation() {
    std::cout << "\n=== 实际应用：数据验证 ===" << std::endl;

    // 验证数据
    std::vector<std::optional<int>> data = {1, 2, std::nullopt, 4, 5};

    // 检查是否所有值都存在
    bool all_present = std::ranges::all_of(data, [](const auto& opt) {
        return opt.has_value();
    });

    std::cout << "All values present: " << (all_present ? "yes" : "no") << std::endl;

    // 检查是否存在空值
    bool any_missing = std::ranges::any_of(data, [](const auto& opt) {
        return !opt.has_value();
    });

    std::cout << "Any missing: " << (any_missing ? "yes" : "no") << std::endl;
}

// ========== 8. 实际应用：数据聚合 ==========

void data_aggregation() {
    std::cout << "\n=== 实际应用：数据聚合 ===" << std::endl;

    // 模拟传感器数据
    std::vector<std::optional<double>> sensor_data = {
        10.5, 11.2, std::nullopt, 12.8, std::nullopt, 13.1
    };

    // 计算有效数据的平均值
    double sum = 0;
    int count = 0;
    for (const auto& opt : sensor_data) {
        if (opt) {
            sum += *opt;
            ++count;
        }
    }

    if (count > 0) {
        std::cout << "Average: " << (sum / count) << std::endl;
        std::cout << "Valid readings: " << count << std::endl;
        std::cout << "Missing readings: " << (sensor_data.size() - count) << std::endl;
    }
}

// ========== 9. 实际应用：条件处理 ==========

void conditional_processing() {
    std::cout << "\n=== 实际应用：条件处理 ===" << std::endl;

    // 处理可能为空的配置
    std::optional<std::string> config = "production";

    // 根据配置值执行不同操作
    config
        .transform([](const std::string& cfg) {
            std::cout << "Running in " << cfg << " mode" << std::endl;
            return cfg;
        })
        .or_else([]() -> std::optional<std::string> {
            std::cout << "No config found, using default" << std::endl;
            return "default";
        });
}

// ========== 10. 实际应用：数据管道 ==========

void data_pipeline() {
    std::cout << "\n=== 实际应用：数据管道 ===" << std::endl;

    // 模拟数据管道
    std::vector<std::optional<int>> input = {1, 2, std::nullopt, 4, 5, std::nullopt, 7};

    // 管道处理
    auto output = input
        | std::views::filter([](const auto& opt) { return opt.has_value(); })
        | std::views::transform([](const auto& opt) { return *opt; })
        | std::views::transform([](int x) { return x * x; })
        | std::views::filter([](int x) { return x > 10; })
        | std::ranges::to<std::vector>();

    std::cout << "Pipeline output: ";
    for (int n : output) std::cout << n << " ";
    std::cout << std::endl;
}

int main() {
    std::cout << "C++23 std::optional 范围转换示例\n" << std::endl;

    basic_usage();
    data_filtering();
    error_handling();
    data_transformation();
    default_values();
    chaining_operations();
    data_validation();
    data_aggregation();
    conditional_processing();
    data_pipeline();

    return 0;
}
