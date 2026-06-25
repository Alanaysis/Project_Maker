/**
 * @file ranges_to_example.cpp
 * @brief C++23 std::ranges::to 示例
 *
 * std::ranges::to 是 C++23 引入的容器转换工具。
 * 它可以将任何范围转换为指定的容器类型。
 *
 * 主要特点：
 * - 简化范围到容器的转换
 * - 支持所有标准容器
 * - 自动推导容器类型
 * - 支持自定义容器
 *
 * 编译命令：
 * g++ -std=c++23 -o ranges_to_example ranges_to_example.cpp
 */

#include <iostream>
#include <vector>
#include <list>
#include <set>
#include <deque>
#include <string>
#include <ranges>
#include <algorithm>
#include <map>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 创建一个范围
    auto range = std::views::iota(1, 11);  // 1 到 10

    // 转换为 vector
    auto vec = range | std::ranges::to<std::vector>();
    std::cout << "vector: ";
    for (int n : vec) std::cout << n << " ";
    std::cout << std::endl;

    // 转换为 list
    auto lst = range | std::ranges::to<std::list>();
    std::cout << "list: ";
    for (int n : lst) std::cout << n << " ";
    std::cout << std::endl;

    // 转换为 set
    auto s = range | std::ranges::to<std::set>();
    std::cout << "set: ";
    for (int n : s) std::cout << n << " ";
    std::cout << std::endl;

    // 转换为 deque
    auto deq = range | std::ranges::to<std::deque>();
    std::cout << "deque: ";
    for (int n : deq) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 2. 带转换的用法 ==========

void with_transform() {
    std::cout << "\n=== 带转换的用法 ===" << std::endl;

    // 创建一个范围并转换
    auto squares = std::views::iota(1, 6)
        | std::views::transform([](int x) { return x * x; })
        | std::ranges::to<std::vector>();

    std::cout << "Squares: ";
    for (int n : squares) std::cout << n << " ";
    std::cout << std::endl;

    // 过滤后转换
    auto evens = std::views::iota(1, 11)
        | std::views::filter([](int x) { return x % 2 == 0; })
        | std::ranges::to<std::vector>();

    std::cout << "Evens: ";
    for (int n : evens) std::cout << n << " ";
    std::cout << std::endl;

    // 字符串转换
    auto chars = std::views::iota('a', 'f')
        | std::ranges::to<std::string>();

    std::cout << "Chars: " << chars << std::endl;
}

// ========== 3. 从容器到容器 ==========

void container_to_container() {
    std::cout << "\n=== 从容器到容器 ===" << std::endl;

    // vector 到 set
    std::vector<int> vec = {5, 2, 8, 1, 9, 3, 7, 4, 6, 5, 2};
    auto s = vec | std::ranges::to<std::set>();
    std::cout << "vector to set: ";
    for (int n : s) std::cout << n << " ";
    std::cout << std::endl;

    // list 到 vector
    std::list<int> lst = {10, 20, 30, 40, 50};
    auto vec2 = lst | std::ranges::to<std::vector>();
    std::cout << "list to vector: ";
    for (int n : vec2) std::cout << n << " ";
    std::cout << std::endl;

    // set 到 vector
    std::set<int> set = {3, 1, 4, 1, 5, 9};
    auto vec3 = set | std::ranges::to<std::vector>();
    std::cout << "set to vector: ";
    for (int n : vec3) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 4. 字符串处理 ==========

void string_processing() {
    std::cout << "\n=== 字符串处理 ===" << std::endl;

    // 字符串转字符 vector
    std::string str = "Hello, World!";
    auto chars = str | std::ranges::to<std::vector>();
    std::cout << "String to vector<char>: ";
    for (char c : chars) std::cout << c;
    std::cout << std::endl;

    // 字符 vector 转字符串
    std::vector<char> char_vec = {'C', '+', '+', '2', '3'};
    auto s = char_vec | std::ranges::to<std::string>();
    std::cout << "vector<char> to string: " << s << std::endl;

    // 单词分割
    std::string sentence = "the quick brown fox jumps over the lazy dog";
    auto words = sentence
        | std::views::split(' ')
        | std::views::transform([](auto word) {
            return std::string(word.begin(), word.end());
        })
        | std::ranges::to<std::vector>();

    std::cout << "Words: ";
    for (const auto& word : words) std::cout << "[" << word << "] ";
    std::cout << std::endl;
}

// ========== 5. 嵌套范围 ==========

void nested_ranges() {
    std::cout << "\n=== 嵌套范围 ===" << std::endl;

    // 二维 vector
    std::vector<std::vector<int>> matrix = {
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 9}
    };

    // 展平为一维
    auto flat = matrix
        | std::views::join
        | std::ranges::to<std::vector>();

    std::cout << "Flattened: ";
    for (int n : flat) std::cout << n << " ";
    std::cout << std::endl;

    // 将一维转换为二维
    auto reshaped = flat
        | std::views::chunk(3)
        | std::ranges::to<std::vector<std::vector<int>>>();

    std::cout << "Reshaped:" << std::endl;
    for (const auto& row : reshaped) {
        std::cout << "  ";
        for (int n : row) std::cout << n << " ";
        std::cout << std::endl;
    }
}

// ========== 6. 实际应用：数据处理 ==========

struct Student {
    std::string name;
    int score;
};

void data_processing() {
    std::cout << "\n=== 实际应用：数据处理 ===" << std::endl;

    std::vector<Student> students = {
        {"Alice", 95},
        {"Bob", 87},
        {"Charlie", 92},
        {"David", 78},
        {"Eve", 88}
    };

    // 提取高分学生姓名
    auto high_scorers = students
        | std::views::filter([](const Student& s) { return s.score >= 90; })
        | std::views::transform([](const Student& s) { return s.name; })
        | std::ranges::to<std::vector>();

    std::cout << "High scorers (>=90): ";
    for (const auto& name : high_scorers) std::cout << name << " ";
    std::cout << std::endl;

    // 提取所有分数
    auto scores = students
        | std::views::transform([](const Student& s) { return s.score; })
        | std::ranges::to<std::vector>();

    std::cout << "All scores: ";
    for (int score : scores) std::cout << score << " ";
    std::cout << std::endl;

    // 创建姓名到分数的映射
    auto score_map = students
        | std::views::transform([](const Student& s) {
            return std::make_pair(s.name, s.score);
        })
        | std::ranges::to<std::map<std::string, int>>();

    std::cout << "Score map:" << std::endl;
    for (const auto& [name, score] : score_map) {
        std::cout << "  " << name << ": " << score << std::endl;
    }
}

// ========== 7. 自定义容器 ==========

// 自定义容器
template<typename T>
class CircularBuffer {
private:
    std::vector<T> data_;
    size_t capacity_;

public:
    CircularBuffer(size_t cap) : capacity_(cap) {}

    void push(const T& value) {
        if (data_.size() < capacity_) {
            data_.push_back(value);
        } else {
            data_[data_.size() % capacity_] = value;
        }
    }

    auto begin() const { return data_.begin(); }
    auto end() const { return data_.end(); }
    size_t size() const { return data_.size(); }
};

void custom_container() {
    std::cout << "\n=== 自定义容器 ===" << std::endl;

    // 创建一个范围
    auto range = std::views::iota(1, 11);

    // 转换为自定义容器
    auto buffer = range | std::ranges::to<CircularBuffer<int>>(5);

    std::cout << "CircularBuffer (capacity=5): ";
    for (int n : buffer) std::cout << n << " ";
    std::cout << std::endl;
}

// ========== 8. 链式操作 ==========

void chaining_operations() {
    std::cout << "\n=== 链式操作 ===" << std::endl;

    // 复杂的链式操作
    auto result = std::views::iota(1, 21)
        | std::views::filter([](int x) { return x % 2 == 0; })  // 偶数
        | std::views::transform([](int x) { return x * x; })    // 平方
        | std::views::take(5)                                    // 取前 5 个
        | std::ranges::to<std::vector>();                        // 转换为 vector

    std::cout << "Chain result: ";
    for (int n : result) std::cout << n << " ";
    std::cout << std::endl;

    // 转换为不同类型
    auto set_result = std::views::iota(1, 11)
        | std::views::transform([](int x) { return x * 2; })
        | std::ranges::to<std::set>();

    std::cout << "Set result: ";
    for (int n : set_result) std::cout << n << " ";
    std::cout << std::endl;
}

int main() {
    std::cout << "C++23 std::ranges::to 示例\n" << std::endl;

    basic_usage();
    with_transform();
    container_to_container();
    string_processing();
    nested_ranges();
    data_processing();
    custom_container();
    chaining_operations();

    return 0;
}
