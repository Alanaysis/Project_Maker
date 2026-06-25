/**
 * @file views_as_const_example.cpp
 * @brief C++23 std::views::as_const 示例
 *
 * std::views::as_const 是 C++23 引入的常量视图。
 * 它将范围中的元素视为常量，防止意外修改。
 *
 * 主要特点：
 * - 将范围元素视为常量
 * - 防止意外修改
 * - 支持只读访问
 * - 适用于函数参数和接口设计
 *
 * 编译命令：
 * g++ -std=c++23 -o views_as_const_example views_as_const_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5};

    // 创建常量视图
    auto const_view = data | std::views::as_const;

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Const view: ";
    for (int n : const_view) std::cout << n << " ";
    std::cout << std::endl;

    // 尝试修改会导致编译错误
    // for (int& n : const_view) n = 10;  // 编译错误
}

// ========== 2. 防止意外修改 ==========

void prevent_modification() {
    std::cout << "\n=== 防止意外修改 ===" << std::endl;

    std::vector<std::string> names = {"Alice", "Bob", "Charlie"};

    // 创建常量视图
    auto const_names = names | std::views::as_const;

    // 只能读取，不能修改
    std::cout << "Names (read-only):" << std::endl;
    for (const auto& name : const_names) {
        std::cout << "  " << name << std::endl;
        // name = "Modified";  // 编译错误
    }
}

// ========== 3. 实际应用：函数参数 ==========

// 接受常量视图的函数
void process_data(std::views::all_t<const std::vector<int>&> data) {
    std::cout << "Processing data:" << std::endl;
    for (int n : data) {
        std::cout << "  " << n << std::endl;
    }
    // data.push_back(6);  // 编译错误
}

void function_parameters() {
    std::cout << "\n=== 实际应用：函数参数 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5};

    // 传递常量视图
    process_data(data | std::views::as_const);
}

// ========== 4. 实际应用：接口设计 ==========

class DataProcessor {
public:
    // 接受只读视图
    void process(std::views::all_t<const std::vector<int>&> data) {
        std::cout << "Processing:" << std::endl;
        for (int n : data) {
            std::cout << "  " << n << std::endl;
        }
    }

    // 计算统计信息
    double average(std::views::all_t<const std::vector<int>&> data) {
        double sum = 0;
        int count = 0;
        for (int n : data) {
            sum += n;
            ++count;
        }
        return count > 0 ? sum / count : 0;
    }
};

void interface_design() {
    std::cout << "\n=== 实际应用：接口设计 ===" << std::endl;

    DataProcessor processor;
    std::vector<int> data = {10, 20, 30, 40, 50};

    // 使用常量视图
    auto const_data = data | std::views::as_const;

    processor.process(const_data);
    std::cout << "Average: " << processor.average(const_data) << std::endl;
}

// ========== 5. 实际应用：数据验证 ==========

void data_validation() {
    std::cout << "\n=== 实际应用：数据验证 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5};

    // 验证数据
    auto const_data = data | std::views::as_const;

    bool all_positive = std::ranges::all_of(const_data, [](int n) {
        return n > 0;
    });

    bool has_even = std::ranges::any_of(const_data, [](int n) {
        return n % 2 == 0;
    });

    std::cout << "All positive: " << (all_positive ? "yes" : "no") << std::endl;
    std::cout << "Has even: " << (has_even ? "yes" : "no") << std::endl;
}

// ========== 6. 实际应用：数据转换 ==========

void data_transformation() {
    std::cout << "\n=== 实际应用：数据转换 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5};

    // 使用常量视图进行转换
    auto const_data = data | std::views::as_const;

    // 转换为字符串
    auto strings = const_data
        | std::views::transform([](int n) {
            return std::to_string(n);
        })
        | std::ranges::to<std::vector>();

    std::cout << "Strings: ";
    for (const auto& s : strings) std::cout << s << " ";
    std::cout << std::endl;
}

// ========== 7. 实际应用：数据聚合 ==========

void data_aggregation() {
    std::cout << "\n=== 实际应用：数据聚合 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 使用常量视图进行聚合
    auto const_data = data | std::views::as_const;

    // 计算总和
    int sum = 0;
    for (int n : const_data) {
        sum += n;
    }
    std::cout << "Sum: " << sum << std::endl;

    // 计算乘积
    int product = 1;
    for (int n : const_data) {
        product *= n;
    }
    std::cout << "Product: " << product << std::endl;
}

// ========== 8. 实际应用：数据过滤 ==========

void data_filtering() {
    std::cout << "\n=== 实际应用：数据过滤 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 使用常量视图进行过滤
    auto const_data = data | std::views::as_const;

    // 过滤偶数
    auto evens = const_data
        | std::views::filter([](int n) { return n % 2 == 0; })
        | std::ranges::to<std::vector>();

    std::cout << "Evens: ";
    for (int n : evens) std::cout << n << " ";
    std::cout << std::endl;

    // 过滤大于 5 的数
    auto greater_than_5 = const_data
        | std::views::filter([](int n) { return n > 5; })
        | std::ranges::to<std::vector>();

    std::cout << "Greater than 5: ";
    for (int n : greater_than_5) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 9. 实际应用：数据排序 ==========

void data_sorting() {
    std::cout << "\n=== 实际应用：数据排序 ===" << std::endl;

    std::vector<int> data = {5, 2, 8, 1, 9, 3, 7, 4, 6};

    // 使用常量视图获取排序后的副本
    auto const_data = data | std::views::as_const;

    // 创建排序后的副本
    auto sorted = const_data | std::ranges::to<std::vector>();
    std::ranges::sort(sorted);

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Sorted: ";
    for (int n : sorted) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 10. 实际应用：数据比较 ==========

void data_comparison() {
    std::cout << "\n=== 实际应用：数据比较 ===" << std::endl;

    std::vector<int> data1 = {1, 2, 3, 4, 5};
    std::vector<int> data2 = {1, 2, 3, 4, 5};
    std::vector<int> data3 = {1, 2, 3, 4, 6};

    // 使用常量视图进行比较
    auto const1 = data1 | std::views::as_const;
    auto const2 = data2 | std::views::as_const;
    auto const3 = data3 | std::views::as_const;

    std::cout << "data1 == data2: " << (std::ranges::equal(const1, const2) ? "yes" : "no") << std::endl;
    std::cout << "data1 == data3: " << (std::ranges::equal(const1, const3) ? "yes" : "no") << std::endl;
}

int main() {
    std::cout << "C++23 std::views::as_const 示例\n" << std::endl;

    basic_usage();
    prevent_modification();
    function_parameters();
    interface_design();
    data_validation();
    data_transformation();
    data_aggregation();
    data_filtering();
    data_sorting();
    data_comparison();

    return 0;
}
