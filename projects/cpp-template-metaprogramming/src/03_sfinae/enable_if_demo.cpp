// =============================================================================
// enable_if_demo.cpp - SFINAE 与 enable_if 演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o enable_if_demo enable_if_demo.cpp
// 运行: ./enable_if_demo
// =============================================================================

#include <iostream>
#include <vector>
#include <string>
#include <type_traits>
#include "sfinae/enable_if.hpp"

int main() {
    using namespace tmp::sfinae;

    std::cout << "=== SFINAE 与 enable_if 演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本 enable_if 用法
    std::cout << "1. 基本 enable_if 用法:" << std::endl;
    std::cout << "  safe_add(3, 4) = " << safe_add(3, 4) << std::endl;
    std::cout << "  safe_add(3.14, 2.71) = " << safe_add(3.14, 2.71) << std::endl;
    // safe_add(3.14, 2);  // 编译错误：没有匹配的重载
    std::cout << std::endl;

    // 2. 返回类型 enable_if
    std::cout << "2. 返回类型 enable_if:" << std::endl;
    std::cout << "  type_name(42) = " << type_name(42) << std::endl;
    std::cout << "  type_name(3.14) = " << type_name(3.14) << std::endl;
    int x = 42;
    std::cout << "  type_name(&x) = " << type_name(&x) << std::endl;
    std::cout << std::endl;

    // 3. 模板参数 enable_if
    std::cout << "3. 模板参数 enable_if:" << std::endl;
    print_info(42);
    print_info(3.14);
    print_info(&x);
    std::cout << std::endl;

    // 4. 类模板特化 enable_if
    std::cout << "4. 类模板特化 enable_if:" << std::endl;
    std::cout << "  Serializer<int>::serialize(42) = "
              << Serializer<int>::serialize(42) << std::endl;
    std::cout << "  Serializer<double>::serialize(3.14) = "
              << Serializer<double>::serialize(3.14) << std::endl;
    std::cout << std::endl;

    // 5. 成员函数检测
    std::cout << "5. 成员函数检测:" << std::endl;
    std::cout << "  vector has size: " << has_size_v<std::vector<int>> << std::endl;
    std::cout << "  int has size: " << has_size_v<int> << std::endl;

    std::vector<int> v = {1, 2, 3, 4, 5};
    int arr[] = {1, 2, 3};
    std::cout << "  get_size(vector) = " << get_size(v) << std::endl;
    std::cout << "  get_size(array) = " << get_size(arr) << std::endl;
    std::cout << std::endl;

    std::cout << "=== SFINAE 演示完成 ===" << std::endl;
    return 0;
}
