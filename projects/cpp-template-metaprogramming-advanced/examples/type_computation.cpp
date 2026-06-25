/**
 * @file type_computation.cpp
 * @brief 类型计算示例
 */

#include <iostream>
#include <type_traits>
#include <cstdint>
#include "../include/type_computation/type_conversion.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Type Computation ===" << std::endl;
    std::cout << std::endl;

    // 1. 类型提升
    std::cout << "--- 1. Type Promotion ---" << std::endl;
    std::cout << "promote<char> = int: "
              << std::is_same_v<promote_t<char>, int> << std::endl;
    std::cout << "promote<short> = int: "
              << std::is_same_v<promote_t<short>, int> << std::endl;
    std::cout << "promote<bool> = int: "
              << std::is_same_v<promote_t<bool>, int> << std::endl;
    std::cout << "promote<int> = int: "
              << std::is_same_v<promote_t<int>, int> << std::endl;
    std::cout << std::endl;

    // 2. 公共提升类型
    std::cout << "--- 2. Common Promoted Type ---" << std::endl;
    using cp1 = common_promoted_t<int, double>;
    std::cout << "common_promoted<int, double> is double: "
              << std::is_same_v<cp1, double> << std::endl;
    std::cout << std::endl;

    // 3. 转换链检测
    std::cout << "--- 3. Conversion Chain ---" << std::endl;
    std::cout << "int -> double -> long double: "
              << conversion_chain_v<int, double, long double> << std::endl;
    std::cout << "int -> string -> double: "
              << conversion_chain_v<int, std::string, double> << std::endl;
    std::cout << std::endl;

    // 4. strip_all
    std::cout << "--- 4. Strip All Modifiers ---" << std::endl;
    std::cout << "strip_all<int**&> is int: "
              << std::is_same_v<strip_all_t<int**&>, int> << std::endl;
    std::cout << "strip_all<const volatile int*> is int: "
              << std::is_same_v<strip_all_t<const volatile int*>, int> << std::endl;
    std::cout << std::endl;

    // 5. 类型断言
    std::cout << "--- 5. Type Assertions ---" << std::endl;
    static_assert(assert_same_v<int, int>, "int == int");
    static_assert(is_convertible_v<int, double>, "int -> double");
    static_assert(is_convertible_v<double, int>, "double -> int");
    std::cout << "All type assertions passed!" << std::endl;

    return 0;
}
