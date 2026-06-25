#include <iostream>
#include <cassert>
#include "math_utils.h"

/**
 * @file test_math.cpp
 * @brief Bazel 测试示例
 */

int main() {
    std::cout << "=== Bazel 测试示例 ===" << std::endl;

    assert(math::add(2, 3) == 5);
    assert(math::subtract(10, 3) == 7);
    assert(math::multiply(3, 4) == 12);
    assert(math::is_prime(7) == true);

    std::cout << "所有测试通过" << std::endl;
    return 0;
}
