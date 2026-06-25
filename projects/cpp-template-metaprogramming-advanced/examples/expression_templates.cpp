/**
 * @file expression_templates.cpp
 * @brief 表达式模板示例 - 高效向量运算
 *
 * 表达式模板通过延迟求值避免创建临时对象，
 * 将多个运算融合为一次遍历。
 */

#include <iostream>
#include <chrono>
#include "../include/advanced_templates/expression_templates.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Expression Templates Demo ===" << std::endl;
    std::cout << std::endl;

    // 创建向量
    Vector<double, 4> a = {1.0, 2.0, 3.0, 4.0};
    Vector<double, 4> b = {5.0, 6.0, 7.0, 8.0};
    Vector<double, 4> c = {9.0, 10.0, 11.0, 12.0};

    std::cout << "a = " << a << std::endl;
    std::cout << "b = " << b << std::endl;
    std::cout << "c = " << c << std::endl;
    std::cout << std::endl;

    // 基本运算
    auto sum = a + b;
    std::cout << "a + b = " << sum << std::endl;

    auto diff = b - a;
    std::cout << "b - a = " << diff << std::endl;

    auto scaled = 2.0 * a;
    std::cout << "2 * a = " << scaled << std::endl;
    std::cout << std::endl;

    // 复合表达式 - 不创建临时对象！
    // a + b + c 被编译为一个表达式树
    // 只在赋值时遍历一次
    auto result = a + b + c;
    std::cout << "a + b + c = " << result << std::endl;

    // 更复杂的表达式
    auto complex = 2.0 * a + 3.0 * b - c;
    std::cout << "2*a + 3*b - c = " << complex << std::endl;
    std::cout << std::endl;

    // 点积
    double dot_product = a.dot(b);
    std::cout << "a . b = " << dot_product << std::endl;

    // 向量模
    std::cout << "|a| = " << a.norm() << std::endl;

    // 归一化
    auto normalized = normalize(a);
    std::cout << "normalize(a) = " << normalized << std::endl;
    std::cout << "|normalize(a)| = " << normalized.norm() << std::endl;
    std::cout << std::endl;

    // 取负
    auto neg = -a;
    std::cout << "-a = " << neg << std::endl;

    // 逐元素乘法
    auto elem_mul = a * b;
    std::cout << "a * b (element-wise) = " << elem_mul << std::endl;

    // 性能对比说明
    std::cout << std::endl;
    std::cout << "--- Performance Notes ---" << std::endl;
    std::cout << "Without expression templates:" << std::endl;
    std::cout << "  a + b + c creates 2 temporary vectors" << std::endl;
    std::cout << "  3 memory allocations, 2 loops" << std::endl;
    std::cout << std::endl;
    std::cout << "With expression templates:" << std::endl;
    std::cout << "  a + b + c creates 0 temporary vectors" << std::endl;
    std::cout << "  0 memory allocations, 1 loop" << std::endl;
    std::cout << "  Compiler can also auto-vectorize the single loop" << std::endl;

    // 编译期断言
    // Vector::size() is a member function, use constexpr instance
    constexpr Vector<double, 4> test_vec;
    static_assert(test_vec.size() == 4, "Vector size should be 4");

    return 0;
}
