#include <iostream>
#include <cassert>
#include "math_utils.h"

/**
 * @file test_math.cpp
 * @brief 数学工具库简单测试
 */

int main() {
    std::cout << "=== 数学工具库测试 ===" << std::endl;

    // 测试加法
    assert(math::add(2, 3) == 5);
    assert(math::add(-1, 1) == 0);
    std::cout << "加法测试通过" << std::endl;

    // 测试减法
    assert(math::subtract(10, 3) == 7);
    assert(math::subtract(3, 10) == -7);
    std::cout << "减法测试通过" << std::endl;

    // 测试乘法
    assert(math::multiply(3, 4) == 12);
    assert(math::multiply(0, 100) == 0);
    std::cout << "乘法测试通过" << std::endl;

    // 测试素数判断
    assert(math::is_prime(2) == true);
    assert(math::is_prime(7) == true);
    assert(math::is_prime(4) == false);
    assert(math::is_prime(1) == false);
    std::cout << "素数判断测试通过" << std::endl;

    std::cout << "=== 所有测试通过 ===" << std::endl;
    return 0;
}
