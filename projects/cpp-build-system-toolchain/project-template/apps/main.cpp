#include <iostream>
#include "mylib/core.h"

/**
 * @file main.cpp
 * @brief 项目模板主程序
 */

int main() {
    std::cout << "=== 现代 CMake 项目模板 ===" << std::endl;
    std::cout << std::endl;

    std::cout << "版本: " << mylib::Version::string() << std::endl;
    std::cout << std::endl;

    // 使用库函数
    std::cout << "数学工具:" << std::endl;
    std::cout << "  3 + 4 = " << mylib::MathUtils::add(3, 4) << std::endl;
    std::cout << "  7 是素数: " << (mylib::MathUtils::is_prime(7) ? "是" : "否") << std::endl;

    std::cout << std::endl;
    std::cout << "字符串工具:" << std::endl;
    std::cout << "  大写: " << mylib::StringUtils::to_upper("hello cmake") << std::endl;

    return 0;
}
