/**
 * @file requires_expressions.cpp
 * @brief C++20 requires 表达式示例
 */

#include <iostream>
#include <string>
#include <vector>
#include <list>
#include <concepts>
#include "../include/sfinae/requires_expressions.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== C++20 Requires Expressions ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本概念检查
    std::cout << "--- 1. Basic Concepts ---" << std::endl;
    std::cout << "vector is Container: " << Container<std::vector<int>> << std::endl;
    std::cout << "int is Container: " << Container<int> << std::endl;
    std::cout << "string is Container: " << Container<std::string> << std::endl;
    std::cout << std::endl;

    std::cout << "vector is SequenceContainer: " << SequenceContainer<std::vector<int>> << std::endl;
    std::cout << "list is SequenceContainer: " << SequenceContainer<std::list<int>> << std::endl;
    std::cout << std::endl;

    // 2. 数值概念
    std::cout << "--- 2. Numeric Concepts ---" << std::endl;
    std::cout << "int is Numeric: " << Numeric<int> << std::endl;
    std::cout << "double is Numeric: " << Numeric<double> << std::endl;
    std::cout << "string is Numeric: " << Numeric<std::string> << std::endl;
    std::cout << std::endl;

    std::cout << "int is Arithmetic: " << Arithmetic<int> << std::endl;
    std::cout << "double is Arithmetic: " << Arithmetic<double> << std::endl;
    std::cout << std::endl;

    // 3. 流操作概念
    std::cout << "--- 3. Stream Concepts ---" << std::endl;
    std::cout << "int is Streamable: " << Streamable<int> << std::endl;
    std::cout << "string is Streamable: " << Streamable<std::string> << std::endl;
    std::cout << std::endl;

    // 4. 检测函数
    std::cout << "--- 4. Constrained Functions ---" << std::endl;

    std::vector<int> vec = {1, 2, 3, 4, 5};
    auto it = constrained_find(vec, 3);
    if (it != vec.end()) {
        std::cout << "Found: " << *it << std::endl;
    }

    constrained_print(42);
    constrained_print(std::string("Hello"));
    constrained_print_container(vec);
    std::cout << std::endl;

    // 5. 编译期检测
    std::cout << "--- 5. Compile-time Detection ---" << std::endl;
    std::cout << "is_container_v<vector<int>>: " << is_container_v<std::vector<int>> << std::endl;
    std::cout << "is_numeric_v<int>: " << is_numeric_v<int> << std::endl;
    std::cout << "is_streamable_v<string>: " << is_streamable_v<std::string> << std::endl;
    std::cout << std::endl;

    // 6. 使用 requires 约束的模板
    std::cout << "--- 6. Constrained Templates ---" << std::endl;

    // 使用 if constexpr 结合概念
    auto smart_print = [](auto&& value) {
        if constexpr (Streamable<std::decay_t<decltype(value)>>) {
            std::cout << "Streamable: " << value << std::endl;
        } else if constexpr (HasSize<std::decay_t<decltype(value)>>) {
            std::cout << "Has size: " << value.size() << std::endl;
        } else {
            std::cout << "Unknown type" << std::endl;
        }
    };

    smart_print(42);
    smart_print(std::string("hello"));
    smart_print(std::vector<int>{1, 2, 3});

    return 0;
}
