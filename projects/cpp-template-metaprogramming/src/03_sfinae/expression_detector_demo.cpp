// =============================================================================
// expression_detector_demo.cpp - 表达式合法性检测演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o expression_detector_demo expression_detector_demo.cpp
// 运行: ./expression_detector_demo
// =============================================================================

#include <iostream>
#include <string>
#include <vector>
#include "sfinae/expression_detector.hpp"

struct MyType {
    std::string to_string() const { return "MyType"; }
    int hash() const { return 42; }
};

struct SimpleType {
    int value;
};

int main() {
    using namespace tmp::sfinae;

    std::cout << "=== 表达式合法性检测演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. to_string 检测
    std::cout << "1. to_string 检测:" << std::endl;
    std::cout << "  MyType has to_string: " << has_to_string_v<MyType> << std::endl;
    std::cout << "  int has to_string: " << has_to_string_v<int> << std::endl;
    std::cout << "  string has to_string: " << has_to_string_v<std::string> << std::endl;
    std::cout << std::endl;

    // 2. hash 检测
    std::cout << "2. hash 检测:" << std::endl;
    std::cout << "  MyType has hash: " << has_hash_v<MyType> << std::endl;
    std::cout << "  int has hash: " << has_hash_v<int> << std::endl;
    std::cout << std::endl;

    // 3. 操作符检测
    std::cout << "3. 操作符检测:" << std::endl;
    std::cout << "  int is dereferenceable: " << is_dereferenceable_v<int> << std::endl;
    std::cout << "  int* is dereferenceable: " << is_dereferenceable_v<int*> << std::endl;
    std::cout << "  int is incrementable: " << is_incrementable_v<int> << std::endl;
    std::cout << "  int* is incrementable: " << is_incrementable_v<int*> << std::endl;
    std::cout << "  vector is indexable: " << is_indexable_v<std::vector<int>> << std::endl;
    std::cout << "  int is indexable: " << is_indexable_v<int> << std::endl;
    std::cout << std::endl;

    // 4. 可调用性检测
    std::cout << "4. 可调用性检测:" << std::endl;
    auto lambda = []() { return 42; };
    std::cout << "  lambda is callable: " << is_callable_v<decltype(lambda)> << std::endl;
    std::cout << "  int is callable: " << is_callable_v<int> << std::endl;
    std::cout << std::endl;

    // 5. safe_to_string 应用
    std::cout << "5. safe_to_string 应用:" << std::endl;
    MyType mt;
    SimpleType st{10};
    std::cout << "  MyType: " << safe_to_string(mt) << std::endl;
    std::cout << "  SimpleType: " << safe_to_string(st) << std::endl;
    std::cout << std::endl;

    // 6. 完整类型检查
    std::cout << "6. 完整类型检查:" << std::endl;
    std::cout << "  int is complete: " << is_complete_type_check_v<int> << std::endl;
    std::cout << "  string is complete: " << is_complete_type_check_v<std::string> << std::endl;
    std::cout << std::endl;

    std::cout << "=== 表达式合法性检测演示完成 ===" << std::endl;
    return 0;
}
