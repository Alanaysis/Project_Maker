#include <iostream>
#include "math_utils.h"
#include "string_utils.h"

/**
 * @file hello.cpp
 * @brief CMake 基础示例 - 主程序
 *
 * 演示如何使用 CMake 创建的静态库和动态库。
 */

int main() {
    std::cout << "=== CMake 基础示例 ===" << std::endl;
    std::cout << std::endl;

    // 使用静态库 math_utils
    std::cout << "--- 数学工具库 (静态库) ---" << std::endl;
    std::cout << "3 + 4 = " << math::add(3, 4) << std::endl;
    std::cout << "10 - 3 = " << math::subtract(10, 3) << std::endl;
    std::cout << "6 * 7 = " << math::multiply(6, 7) << std::endl;
    std::cout << "15 / 4 = " << math::divide(15, 4) << std::endl;
    std::cout << "5! = " << math::factorial(5) << std::endl;
    std::cout << "7 是素数? " << (math::is_prime(7) ? "是" : "否") << std::endl;
    std::cout << "10 是素数? " << (math::is_prime(10) ? "是" : "否") << std::endl;
    std::cout << std::endl;

    // 使用动态库 string_utils
    std::cout << "--- 字符串工具库 (动态库) ---" << std::endl;
    std::string text = "  Hello, CMake!  ";
    std::cout << "原始: '" << text << "'" << std::endl;
    std::cout << "去空白: '" << str::trim(text) << "'" << std::endl;
    std::cout << "大写: " << str::to_upper(str::trim(text)) << std::endl;
    std::cout << "小写: " << str::to_lower(str::trim(text)) << std::endl;

    // 分割和连接
    std::string csv = "apple,banana,cherry";
    auto parts = str::split(csv, ',');
    std::cout << "分割 '" << csv << "': ";
    for (const auto& part : parts) {
        std::cout << "[" << part << "] ";
    }
    std::cout << std::endl;
    std::cout << "连接: " << str::join(parts, " | ") << std::endl;

    // 前缀后缀判断
    std::cout << "starts_with('Hello', 'He'): " << (str::starts_with("Hello", "He") ? "true" : "false") << std::endl;
    std::cout << "ends_with('Hello', 'lo'): " << (str::ends_with("Hello", "lo") ? "true" : "false") << std::endl;

    std::cout << std::endl;
    std::cout << "=== CMake 基础示例完成 ===" << std::endl;
    return 0;
}
