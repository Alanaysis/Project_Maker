#include <iostream>
#include "math_utils.h"
#include "string_utils.h"

/**
 * @file hello.cpp
 * @brief xmake 构建系统示例 - 主程序
 */

int main() {
    std::cout << "=== xmake 构建系统示例 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "数学工具:" << std::endl;
    std::cout << "  3 + 4 = " << math::add(3, 4) << std::endl;
    std::cout << "  10 - 3 = " << math::subtract(10, 3) << std::endl;

    std::cout << std::endl;
    std::cout << "字符串工具:" << std::endl;
    std::cout << "  大写: " << str::to_upper("hello xmake") << std::endl;
    std::cout << "  小写: " << str::to_lower("HELLO XMAKE") << std::endl;

    return 0;
}
