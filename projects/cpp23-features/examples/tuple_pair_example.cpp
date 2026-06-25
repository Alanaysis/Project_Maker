/**
 * @file tuple_pair_example.cpp
 * @brief C++23 std::tuple 和 std::pair 改进示例
 *
 * C++23 对 std::tuple 和 std::pair 进行了改进，包括更好的结构化绑定支持。
 *
 * 主要特点：
 * - 改进的结构化绑定
 * - 更好的类型推导
 * - 支持更多的初始化方式
 * - 改进的比较操作
 *
 * 编译命令：
 * g++ -std=c++23 -o tuple_pair_example tuple_pair_example.cpp
 */

#include <iostream>
#include <tuple>
#include <pair>
#include <string>
#include <vector>
#include <algorithm>

// ========== 1. 基本结构化绑定 ==========

void basic_structured_bindings() {
    std::cout << "=== 基本结构化绑定 ===" << std::endl;

    // pair 的结构化绑定
    std::pair<int, std::string> p = {1, "Hello"};
    auto [id, name] = p;
    std::cout << "Pair: id=" << id << ", name=" << name << std::endl;

    // tuple 的结构化绑定
    std::tuple<int, std::string, double> t = {1, "World", 3.14};
    auto [id2, name2, value] = t;
    std::cout << "Tuple: id=" << id2 << ", name=" << name2 << ", value=" << value << std::endl;
}

// ========== 2. 实际应用：函数返回多个值 ==========

std::tuple<int, std::string, double> get_user_data() {
    return {1, "Alice", 25.5};
}

void multiple_return_values() {
    std::cout << "\n=== 实际应用：函数返回多个值 ===" << std::endl;

    auto [id, name, score] = get_user_data();
    std::cout << "User: id=" << id << ", name=" << name << ", score=" << score << std::endl;
}

// ========== 3. 实际应用：遍历关联容器 ==========

void iterate_associative_containers() {
    std::cout << "\n=== 实际应用：遍历关联容器 ===" << std::endl;

    std::vector<std::pair<std::string, int>> scores = {
        {"Alice", 95},
        {"Bob", 87},
        {"Charlie", 92}
    };

    // 使用结构化绑定遍历
    std::cout << "Scores:" << std::endl;
    for (const auto& [name, score] : scores) {
        std::cout << "  " << name << ": " << score << std::endl;
    }
}

// ========== 4. 实际应用：交换操作 ==========

void swap_operations() {
    std::cout << "\n=== 实际应用：交换操作 ===" << std::endl;

    int a = 1, b = 2;
    std::cout << "Before swap: a=" << a << ", b=" << b << std::endl;

    // 使用 pair 进行交换
    std::tie(a, b) = std::make_pair(b, a);
    std::cout << "After swap: a=" << a << ", b=" << b << std::endl;
}

// ========== 5. 实际应用：忽略某些值 ==========

void ignore_values() {
    std::cout << "\n=== 实际应用：忽略某些值 ===" << std::endl;

    std::tuple<int, std::string, double> data = {1, "Hello", 3.14};

    // 只绑定需要的值
    auto [id, _, value] = data;
    std::cout << "id=" << id << ", value=" << value << std::endl;

    // 使用 std::ignore
    int id2;
    double value2;
    std::tie(id2, std::ignore, value2) = data;
    std::cout << "id2=" << id2 << ", value2=" << value2 << std::endl;
}

// ========== 6. 实际应用：排序 ==========

void sorting_example() {
    std::cout << "\n=== 实际应用：排序 ===" << std::endl;

    std::vector<std::pair<std::string, int>> students = {
        {"Charlie", 92},
        {"Alice", 95},
        {"Bob", 87}
    };

    // 按分数排序
    std::sort(students.begin(), students.end(),
        [](const auto& a, const auto& b) {
            return a.second > b.second;
        });

    std::cout << "Sorted by score:" << std::endl;
    for (const auto& [name, score] : students) {
        std::cout << "  " << name << ": " << score << std::endl;
    }
}

// ========== 7. 实际应用：数据聚合 ==========

void data_aggregation() {
    std::cout << "\n=== 实际应用：数据聚合 ===" << std::endl;

    // 模拟数据库查询结果
    std::vector<std::tuple<int, std::string, double>> records = {
        {1, "Alice", 100.5},
        {2, "Bob", 200.3},
        {3, "Charlie", 150.7}
    };

    // 计算总和
    double total = 0;
    for (const auto& [id, name, amount] : records) {
        total += amount;
    }
    std::cout << "Total amount: " << total << std::endl;

    // 找出最大值
    auto max_it = std::max_element(records.begin(), records.end(),
        [](const auto& a, const auto& b) {
            return std::get<2>(a) < std::get<2>(b);
        });

    if (max_it != records.end()) {
        const auto& [id, name, amount] = *max_it;
        std::cout << "Max amount: " << name << " = " << amount << std::endl;
    }
}

// ========== 8. 实际应用：配置管理 ==========

void config_management() {
    std::cout << "\n=== 实际应用：配置管理 ===" << std::endl;

    // 配置项
    std::vector<std::tuple<std::string, std::string, std::string>> config = {
        {"host", "localhost", "Server hostname"},
        {"port", "8080", "Server port"},
        {"debug", "true", "Debug mode"}
    };

    // 显示配置
    std::cout << "Configuration:" << std::endl;
    for (const auto& [key, value, description] : config) {
        std::cout << "  " << key << " = " << value << " (" << description << ")" << std::endl;
    }
}

// ========== 9. 实际应用：错误处理 ==========

void error_handling() {
    std::cout << "\n=== 实际应用：错误处理 ===" << std::endl;

    // 模拟可能失败的操作
    auto divide = [](int a, int b) -> std::pair<bool, int> {
        if (b == 0) {
            return {false, 0};
        }
        return {true, a / b};
    };

    // 使用结构化绑定处理结果
    auto [success1, result1] = divide(10, 2);
    if (success1) {
        std::cout << "10 / 2 = " << result1 << std::endl;
    }

    auto [success2, result2] = divide(10, 0);
    if (!success2) {
        std::cout << "Division by zero failed" << std::endl;
    }
}

// ========== 10. 实际应用：数据转换 ==========

void data_transformation() {
    std::cout << "\n=== 实际应用：数据转换 ===" << std::endl;

    // 原始数据
    std::vector<std::tuple<int, std::string, int>> raw_data = {
        {1, "Alice", 95},
        {2, "Bob", 87},
        {3, "Charlie", 92}
    };

    // 转换为 pair
    std::vector<std::pair<std::string, int>> transformed;
    for (const auto& [id, name, score] : raw_data) {
        transformed.emplace_back(name, score);
    }

    // 显示转换后的数据
    std::cout << "Transformed data:" << std::endl;
    for (const auto& [name, score] : transformed) {
        std::cout << "  " << name << ": " << score << std::endl;
    }
}

// ========== 11. 实际应用：元组操作 ==========

void tuple_operations() {
    std::cout << "\n=== 实际应用：元组操作 ===" << std::endl;

    // 创建元组
    auto t1 = std::make_tuple(1, "Hello", 3.14);
    auto t2 = std::make_tuple(2, "World", 2.71);

    // 元组连接
    auto t3 = std::tuple_cat(t1, t2);
    std::cout << "Concatenated tuple size: " << std::tuple_size_v<decltype(t3)> << std::endl;

    // 元组比较
    if (t1 < t2) {
        std::cout << "t1 < t2" << std::endl;
    } else {
        std::cout << "t1 >= t2" << std::endl;
    }
}

// ========== 12. 实际应用：apply 函数 ==========

void apply_example() {
    std::cout << "\n=== 实际应用：apply 函数 ===" << std::endl;

    // 使用 apply 调用函数
    auto add = [](int a, int b, int c) {
        return a + b + c;
    };

    auto args = std::make_tuple(1, 2, 3);
    int result = std::apply(add, args);
    std::cout << "apply(add, (1,2,3)) = " << result << std::endl;
}

int main() {
    std::cout << "C++23 std::tuple / std::pair 改进示例\n" << std::endl;

    basic_structured_bindings();
    multiple_return_values();
    iterate_associative_containers();
    swap_operations();
    ignore_values();
    sorting_example();
    data_aggregation();
    config_management();
    error_handling();
    data_transformation();
    tuple_operations();
    apply_example();

    return 0;
}
