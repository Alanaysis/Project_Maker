/**
 * @file ranges_zip_example.cpp
 * @brief C++23 std::views::zip 示例
 *
 * std::views::zip 是 C++23 引入的并行迭代视图。
 * 它可以同时迭代多个范围，将它们的元素配对。
 *
 * 主要特点：
 * - 同时迭代多个范围
 * - 自动处理不同长度的范围
 * - 支持结构化绑定
 * - 适用于数据合并和关联操作
 *
 * 编译命令：
 * g++ -std=c++23 -o ranges_zip_example ranges_zip_example.cpp
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

    std::vector<int> ids = {1, 2, 3, 4, 5};
    std::vector<std::string> names = {"Alice", "Bob", "Charlie", "David", "Eve"};

    // 并行迭代两个范围
    std::cout << "Zip of ids and names:" << std::endl;
    for (auto [id, name] : std::views::zip(ids, names)) {
        std::cout << "  " << id << ": " << name << std::endl;
    }
}

// ========== 2. 三个范围的 zip ==========

void three_ranges() {
    std::cout << "\n=== 三个范围的 zip ===" << std::endl;

    std::vector<int> ids = {1, 2, 3};
    std::vector<std::string> names = {"Alice", "Bob", "Charlie"};
    std::vector<double> scores = {95.5, 87.3, 92.1};

    std::cout << "Zip of ids, names, and scores:" << std::endl;
    for (auto [id, name, score] : std::views::zip(ids, names, scores)) {
        std::cout << "  " << id << ": " << name << " - " << score << std::endl;
    }
}

// ========== 3. 实际应用：数据关联 ==========

void data_association() {
    std::cout << "\n=== 实际应用：数据关联 ===" << std::endl;

    // 产品数据
    std::vector<std::string> products = {"Laptop", "Phone", "Tablet", "Monitor"};
    std::vector<double> prices = {999.99, 699.99, 449.99, 299.99};
    std::vector<int> quantities = {10, 25, 15, 20};

    // 计算总价值
    std::cout << "Product inventory:" << std::endl;
    double total_value = 0;

    for (auto [product, price, qty] : std::views::zip(products, prices, quantities)) {
        double value = price * qty;
        total_value += value;
        std::cout << "  " << product << ": $" << price << " x " << qty
                  << " = $" << value << std::endl;
    }

    std::cout << "\nTotal inventory value: $" << total_value << std::endl;
}

// ========== 4. 实际应用：向量运算 ==========

void vector_operations() {
    std::cout << "\n=== 实际应用：向量运算 ===" << std::endl;

    std::vector<double> vec1 = {1.0, 2.0, 3.0, 4.0, 5.0};
    std::vector<double> vec2 = {5.0, 4.0, 3.0, 2.0, 1.0};

    // 向量加法
    std::cout << "Vector addition:" << std::endl;
    std::cout << "  vec1: ";
    for (double v : vec1) std::cout << v << " ";
    std::cout << std::endl;

    std::cout << "  vec2: ";
    for (double v : vec2) std::cout << v << " ";
    std::cout << std::endl;

    std::cout << "  sum:  ";
    for (auto [a, b] : std::views::zip(vec1, vec2)) {
        std::cout << a + b << " ";
    }
    std::cout << std::endl;

    // 向量点积
    double dot_product = 0;
    for (auto [a, b] : std::views::zip(vec1, vec2)) {
        dot_product += a * b;
    }
    std::cout << "\nDot product: " << dot_product << std::endl;

    // 向量乘法 (逐元素)
    std::cout << "Element-wise multiplication: ";
    for (auto [a, b] : std::views::zip(vec1, vec2)) {
        std::cout << a * b << " ";
    }
    std::cout << std::endl;
}

// ========== 5. 实际应用：数据转换 ==========

void data_transformation() {
    std::cout << "\n=== 实际应用：数据转换 ===" << std::endl;

    // 温度数据 (摄氏度)
    std::vector<double> celsius = {0, 20, 37, 100};

    // 转换为华氏度
    std::vector<double> fahrenheit;
    for (auto [c] : std::views::zip(celsius)) {
        fahrenheit.push_back(c * 9.0 / 5.0 + 32);
    }

    std::cout << "Temperature conversion:" << std::endl;
    for (auto [c, f] : std::views::zip(celsius, fahrenheit)) {
        std::cout << "  " << c << "°C = " << f << "°F" << std::endl;
    }
}

// ========== 6. 实际应用：排名和排序 ==========

void ranking() {
    std::cout << "\n=== 实际应用：排名和排序 ===" << std::endl;

    // 学生成绩
    std::vector<std::string> students = {"Alice", "Bob", "Charlie", "David", "Eve"};
    std::vector<int> scores = {95, 87, 92, 78, 88};

    // 创建索引
    std::vector<size_t> indices(students.size());
    std::iota(indices.begin(), indices.end(), 0);

    // 按分数排序
    std::ranges::sort(indices, [&](size_t a, size_t b) {
        return scores[a] > scores[b];
    });

    // 显示排名
    std::cout << "Student rankings:" << std::endl;
    int rank = 1;
    for (auto [idx, student, score] : std::views::zip(indices, students, scores)) {
        std::cout << "  " << rank++ << ". " << students[idx]
                  << " - " << scores[idx] << std::endl;
    }
}

// ========== 7. 实际应用：数据验证 ==========

void data_validation() {
    std::cout << "\n=== 实际应用：数据验证 ===" << std::endl;

    // 表单数据
    std::vector<std::string> fields = {"Name", "Email", "Age", "Phone"};
    std::vector<std::string> values = {"Alice", "alice@example.com", "25", "1234567890"};
    std::vector<bool> required = {true, true, true, false};

    // 验证数据
    std::cout << "Form validation:" << std::endl;
    bool all_valid = true;

    for (auto [field, value, req] : std::views::zip(fields, values, required)) {
        bool valid = true;
        std::string message;

        if (req && value.empty()) {
            valid = false;
            message = "Required field is empty";
        }

        if (!valid) {
            all_valid = false;
            std::cout << "  " << field << ": INVALID - " << message << std::endl;
        } else {
            std::cout << "  " << field << ": OK" << std::endl;
        }
    }

    std::cout << "\nOverall: " << (all_valid ? "Valid" : "Invalid") << std::endl;
}

// ========== 8. 实际应用：时间序列 ==========

void time_series() {
    std::cout << "\n=== 实际应用：时间序列 ===" << std::endl;

    // 时间序列数据
    std::vector<std::string> timestamps = {
        "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"
    };
    std::vector<double> values = {100.0, 102.5, 101.0, 103.5, 105.0};

    // 计算变化率
    std::cout << "Time series analysis:" << std::endl;
    std::cout << "  " << timestamps[0] << ": " << values[0] << " (base)" << std::endl;

    for (size_t i = 1; i < timestamps.size(); ++i) {
        double change = values[i] - values[i-1];
        double percent = (change / values[i-1]) * 100;

        std::cout << "  " << timestamps[i] << ": " << values[i]
                  << " (change: " << (change >= 0 ? "+" : "") << change
                  << ", " << (percent >= 0 ? "+" : "") << percent << "%)" << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::views::zip 示例\n" << std::endl;

    basic_usage();
    three_ranges();
    data_association();
    vector_operations();
    data_transformation();
    ranking();
    data_validation();
    time_series();

    return 0;
}
