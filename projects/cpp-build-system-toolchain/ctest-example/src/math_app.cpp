#include <iostream>
#include <string>
#include <stdexcept>
#include "math_lib.h"

/**
 * @file math_app.cpp
 * @brief CTest 集成示例 - 应用程序
 *
 * 命令行计算器，用于演示 CTest 测试。
 */

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cout << "用法: math_app <operation> <a> <b>" << std::endl;
        std::cout << "操作: add, subtract, multiply, divide" << std::endl;
        return 1;
    }

    std::string op = argv[1];
    double a = std::stod(argv[2]);
    double b = std::stod(argv[3]);

    try {
        double result = 0;
        if (op == "add") {
            result = math::add(static_cast<int>(a), static_cast<int>(b));
        } else if (op == "subtract") {
            result = math::subtract(static_cast<int>(a), static_cast<int>(b));
        } else if (op == "multiply") {
            result = math::multiply(static_cast<int>(a), static_cast<int>(b));
        } else if (op == "divide") {
            result = math::divide(a, b);
        } else {
            std::cerr << "未知操作: " << op << std::endl;
            return 1;
        }
        std::cout << "Result: " << result << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
