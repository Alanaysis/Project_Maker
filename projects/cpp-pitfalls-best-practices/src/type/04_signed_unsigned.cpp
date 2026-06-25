/**
 * @file 04_signed_unsigned.cpp
 * @brief 有符号/无符号混用陷阱示例
 *
 * 有符号/无符号混用：混合使用有符号和无符号整数
 * 危害：意外的比较结果、隐式转换、数据错误
 */

#include <iostream>
#include <cstdint>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：有符号与无符号比较
 *
 * 问题：有符号数被转换为无符号数，负数变成大正数
 */
void bad_comparison() {
    int a = -1;
    unsigned int b = 1;

    if (a < b) {
        std::cout << "a < b" << std::endl;
    } else {
        std::cout << "a >= b" << std::endl;
        // 实际输出：a >= b
        // 因为 -1 被转换为 UINT_MAX
    }
}

/**
 * 错误示例 2：有符号与无符号运算
 *
 * 问题：混合运算导致意外结果
 */
void bad_arithmetic() {
    int a = -1;
    unsigned int b = 2;
    auto result = a + b;
    std::cout << "result = " << result << std::endl;
    // result 是 unsigned int，-1 + 2 = UINT_MAX + 1 + 2
}

/**
 * 错误示例 3：循环中的混用
 *
 * 问题：有符号与无符号比较导致逻辑错误
 */
void bad_loop() {
    std::vector<int> vec = {1, 2, 3};
    for (int i = 0; i < vec.size(); i++) {  // 警告：有符号/无符号比较
        std::cout << vec[i] << " ";
    }
    std::cout << std::endl;
}

/**
 * 错误示例 4：函数返回值混用
 *
 * 问题：函数返回无符号数，但调用者期望有符号数
 */
unsigned int get_size() {
    return 10;
}

void bad_return_type() {
    int size = get_size();  // 隐式转换
    if (size - 20 > 0) {  // size - 20 是 unsigned，永远 >= 0
        std::cout << "size > 20" << std::endl;
    }
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用相同类型比较
 *
 * 解决方案：确保比较双方类型相同
 */
void good_same_type() {
    int a = -1;
    int b = 1;

    if (a < b) {
        std::cout << "a < b" << std::endl;
    } else {
        std::cout << "a >= b" << std::endl;
    }
}

/**
 * 正确示例 2：显式转换
 *
 * 解决方案：显式转换，明确意图
 */
void good_explicit_cast() {
    int a = -1;
    unsigned int b = 1;

    // 显式转换，明确意图
    if (static_cast<unsigned int>(a) < b) {
        std::cout << "a < b (as unsigned)" << std::endl;
    }
}

/**
 * 正确示例 3：使用 auto 和类型推导
 *
 * 解决方案：让编译器推导正确类型
 */
void good_auto() {
    int a = -1;
    unsigned int b = 1;

    // 使用 auto 推导类型
    auto result = static_cast<int64_t>(a) + static_cast<int64_t>(b);
    std::cout << "result = " << result << std::endl;
}

/**
 * 正确示例 4：使用 std::ssize (C++20)
 *
 * 解决方案：使用 ssize 获取有符号大小
 */
#include <vector>
#include <iterator>

void good_ssize() {
    std::vector<int> vec = {1, 2, 3};

    // C++20: std::ssize 返回有符号大小
    #if __cplusplus >= 202002L
    for (int i = 0; i < std::ssize(vec); i++) {
        std::cout << vec[i] << " ";
    }
    #else
    for (size_t i = 0; i < vec.size(); i++) {
        std::cout << vec[i] << " ";
    }
    #endif
    std::cout << std::endl;
}

/**
 * 正确示例 5：使用范围 for 循环
 *
 * 解决方案：避免直接比较索引和大小
 */
void good_range_for() {
    std::vector<int> vec = {1, 2, 3};

    for (const auto& val : vec) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

/**
 * 正确示例 6：使用 gsl::index
 *
 * 解决方案：使用明确的索引类型
 */
#include <cstddef>

using index_t = std::ptrdiff_t;  // 有符号索引类型

void good_index_type() {
    std::vector<int> vec = {1, 2, 3};

    for (index_t i = 0; i < static_cast<index_t>(vec.size()); i++) {
        std::cout << vec[i] << " ";
    }
    std::cout << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 有符号/无符号混用陷阱示例 ===" << std::endl;
    std::cout << std::endl;

    // 错误示例
    std::cout << "[错误示例 1] 有符号与无符号比较" << std::endl;
    bad_comparison();
    std::cout << "问题：-1 被转换为 UINT_MAX" << std::endl;
    std::cout << std::endl;

    std::cout << "[错误示例 2] 有符号与无符号运算" << std::endl;
    bad_arithmetic();
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用相同类型比较" << std::endl;
    good_same_type();
    std::cout << std::endl;

    std::cout << "[正确示例 2] 显式转换" << std::endl;
    good_explicit_cast();
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 auto" << std::endl;
    good_auto();
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用 std::ssize" << std::endl;
    good_ssize();
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用范围 for 循环" << std::endl;
    good_range_for();
    std::cout << std::endl;

    std::cout << "[正确示例 6] 使用明确索引类型" << std::endl;
    good_index_type();
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
