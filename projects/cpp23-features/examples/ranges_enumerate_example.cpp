/**
 * @file ranges_enumerate_example.cpp
 * @brief C++23 std::views::enumerate 示例
 *
 * std::views::enumerate 是 C++23 引入的带索引迭代视图。
 * 它可以同时获取元素的索引和值。
 *
 * 主要特点：
 * - 同时获取索引和值
 * - 替代传统的 for 循环
 * - 支持结构化绑定
 * - 适用于需要索引的场景
 *
 * 编译命令：
 * g++ -std=c++23 -o ranges_enumerate_example ranges_enumerate_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>
#include <map>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<std::string> fruits = {"Apple", "Banana", "Cherry", "Date", "Elderberry"};

    // 使用 enumerate 获取索引和值
    std::cout << "Fruits with index:" << std::endl;
    for (auto [index, fruit] : std::views::enumerate(fruits)) {
        std::cout << "  " << index << ": " << fruit << std::endl;
    }
}

// ========== 2. 替代传统循环 ==========

void replace_traditional_loop() {
    std::cout << "\n=== 替代传统循环 ===" << std::endl;

    std::vector<int> numbers = {10, 20, 30, 40, 50};

    // 传统方式
    std::cout << "Traditional loop:" << std::endl;
    for (size_t i = 0; i < numbers.size(); ++i) {
        std::cout << "  " << i << ": " << numbers[i] << std::endl;
    }

    // 使用 enumerate
    std::cout << "\nUsing enumerate:" << std::endl;
    for (auto [index, value] : std::views::enumerate(numbers)) {
        std::cout << "  " << index << ": " << value << std::endl;
    }
}

// ========== 3. 实际应用：查找特定元素 ==========

void find_element() {
    std::cout << "\n=== 实际应用：查找特定元素 ===" << std::endl;

    std::vector<std::string> users = {"Alice", "Bob", "Charlie", "David", "Eve"};
    std::string target = "Charlie";

    // 查找元素的索引
    std::cout << "Looking for '" << target << "':" << std::endl;
    for (auto [index, user] : std::views::enumerate(users)) {
        if (user == target) {
            std::cout << "  Found at index " << index << std::endl;
            break;
        }
    }
}

// ========== 4. 实际应用：数据处理 ==========

void data_processing() {
    std::cout << "\n=== 实际应用：数据处理 ===" << std::endl;

    // 学生成绩
    std::vector<std::string> students = {"Alice", "Bob", "Charlie", "David", "Eve"};
    std::vector<int> scores = {95, 87, 92, 78, 88};

    // 找出高于平均分的学生
    double average = 0;
    for (int score : scores) average += score;
    average /= scores.size();

    std::cout << "Average score: " << average << std::endl;
    std::cout << "Students above average:" << std::endl;

    for (auto [index, score] : std::views::enumerate(scores)) {
        if (score > average) {
            std::cout << "  " << students[index] << ": " << score << std::endl;
        }
    }
}

// ========== 5. 实际应用：数组操作 ==========

void array_operations() {
    std::cout << "\n=== 实际应用：数组操作 ===" << std::endl;

    std::vector<int> data = {5, 2, 8, 1, 9, 3, 7, 4, 6};

    // 找出最大值及其索引
    auto max_element = std::views::enumerate(data)
        | std::ranges::max_element([](auto a, auto b) {
            return std::get<1>(a) < std::get<1>(b);
        });

    if (max_element != std::ranges::end(std::views::enumerate(data))) {
        auto [index, value] = *max_element;
        std::cout << "Maximum value: " << value << " at index " << index << std::endl;
    }

    // 找出最小值及其索引
    auto min_element = std::views::enumerate(data)
        | std::ranges::min_element([](auto a, auto b) {
            return std::get<1>(a) < std::get<1>(b);
        });

    if (min_element != std::ranges::end(std::views::enumerate(data))) {
        auto [index, value] = *min_element;
        std::cout << "Minimum value: " << value << " at index " << index << std::endl;
    }
}

// ========== 6. 实际应用：数据转换 ==========

void data_transformation() {
    std::cout << "\n=== 实际应用：数据转换 ===" << std::endl;

    std::vector<std::string> names = {"Alice", "Bob", "Charlie"};

    // 创建带索引的映射
    std::map<std::string, size_t> name_to_index;
    for (auto [index, name] : std::views::enumerate(names)) {
        name_to_index[name] = index;
    }

    std::cout << "Name to index mapping:" << std::endl;
    for (const auto& [name, index] : name_to_index) {
        std::cout << "  " << name << " -> " << index << std::endl;
    }
}

// ========== 7. 实际应用：数据验证 ==========

void data_validation() {
    std::cout << "\n=== 实际应用：数据验证 ===" << std::endl;

    // 表单字段
    std::vector<std::string> fields = {"Name", "Email", "Age", "Phone"};
    std::vector<std::string> values = {"Alice", "", "25", "1234567890"};
    std::vector<bool> required = {true, true, true, false};

    // 验证数据
    std::cout << "Form validation:" << std::endl;
    bool all_valid = true;

    for (auto [index, field] : std::views::enumerate(fields)) {
        bool valid = true;
        std::string message;

        if (required[index] && values[index].empty()) {
            valid = false;
            message = "Required field is empty";
        }

        if (!valid) {
            all_valid = false;
            std::cout << "  " << field << " (index " << index << "): INVALID - " << message << std::endl;
        } else {
            std::cout << "  " << field << " (index " << index << "): OK" << std::endl;
        }
    }

    std::cout << "\nOverall: " << (all_valid ? "Valid" : "Invalid") << std::endl;
}

// ========== 8. 实际应用：性能分析 ==========

void performance_analysis() {
    std::cout << "\n=== 实际应用：性能分析 ===" << std::endl;

    // 执行时间数据
    std::vector<std::string> operations = {"Sort", "Search", "Insert", "Delete"};
    std::vector<double> times_ms = {12.5, 3.2, 8.7, 5.1};

    // 找出最慢的操作
    auto slowest = std::views::enumerate(times_ms)
        | std::ranges::max_element([](auto a, auto b) {
            return std::get<1>(a) < std::get<1>(b);
        });

    if (slowest != std::ranges::end(std::views::enumerate(times_ms))) {
        auto [index, time] = *slowest;
        std::cout << "Slowest operation: " << operations[index]
                  << " (" << time << " ms)" << std::endl;
    }

    // 找出最快的操作
    auto fastest = std::views::enumerate(times_ms)
        | std::ranges::min_element([](auto a, auto b) {
            return std::get<1>(a) < std::get<1>(b);
        });

    if (fastest != std::ranges::end(std::views::enumerate(times_ms))) {
        auto [index, time] = *fastest;
        std::cout << "Fastest operation: " << operations[index]
                  << " (" << time << " ms)" << std::endl;
    }

    // 显示所有操作的时间
    std::cout << "\nAll operations:" << std::endl;
    for (auto [index, time] : std::views::enumerate(times_ms)) {
        std::cout << "  " << operations[index] << ": " << time << " ms" << std::endl;
    }
}

// ========== 9. 实际应用：字符串处理 ==========

void string_processing() {
    std::cout << "\n=== 实际应用：字符串处理 ===" << std::endl;

    std::string text = "Hello, World!";

    // 显示每个字符及其索引
    std::cout << "Characters in '" << text << "':" << std::endl;
    for (auto [index, ch] : std::views::enumerate(text)) {
        std::cout << "  " << index << ": '" << ch << "' (ASCII: " << static_cast<int>(ch) << ")" << std::endl;
    }

    // 找出特定字符的位置
    char target = 'o';
    std::cout << "\nPositions of '" << target << "':" << std::endl;
    for (auto [index, ch] : std::views::enumerate(text)) {
        if (ch == target) {
            std::cout << "  Index " << index << std::endl;
        }
    }
}

int main() {
    std::cout << "C++23 std::views::enumerate 示例\n" << std::endl;

    basic_usage();
    replace_traditional_loop();
    find_element();
    data_processing();
    array_operations();
    data_transformation();
    data_validation();
    performance_analysis();
    string_processing();

    return 0;
}
