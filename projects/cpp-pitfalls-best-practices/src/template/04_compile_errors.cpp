/**
 * @file 04_compile_errors.cpp
 * @brief 模板编译错误示例
 *
 * 模板编译错误：模板代码的编译错误难以理解
 * 危害：错误信息冗长、难以定位问题
 */

#include <iostream>
#include <vector>
#include <string>
#include <type_traits>

// ============================================================================
// 错误示例
// ============================================================================

/**
 * 错误示例 1：模板中类型不匹配
 *
 * 问题：模板实例化时类型不匹配，错误信息冗长
 */
template <typename T>
void bad_type_mismatch(T a, T b) {
    // 如果 a 和 b 类型不同，编译错误
    auto result = a + b;
    std::cout << result << std::endl;
}

/**
 * 错误示例 2：嵌套模板错误
 *
 * 问题：嵌套模板的错误信息更难理解
 */
template <typename T>
struct BadOuter {
    template <typename U>
    struct BadInner {
        static void process() {
            // 如果 U 不支持某些操作，错误信息很长
            U::nonexistent_function();
        }
    };
};

/**
 * 错误示例 3：SFINAE 失败
 *
 * 问题：SFINAE 失败时错误信息不明确
 */
template <typename T>
auto bad_sfinae(T value) -> decltype(std::declval<T>().nonexistent()) {
    return value.nonexistent();
}

/**
 * 错误示例 4：模板参数推导失败
 *
 * 问题：模板参数推导失败时错误信息不清晰
 */
template <typename T>
void bad_deduction(T a, typename T::type b) {
    // 如果 T 没有 type 成员，推导失败
}

// ============================================================================
// 正确示例
// ============================================================================

/**
 * 正确示例 1：使用 static_assert 提供清晰错误信息
 *
 * 解决方案：使用 static_assert 提供有意义的错误信息
 */
template <typename T>
void good_static_assert(T a, T b) {
    static_assert(std::is_arithmetic_v<T>, "T must be an arithmetic type");
    auto result = a + b;
    std::cout << result << std::endl;
}

/**
 * 正确示例 2：使用 concepts (C++20)
 *
 * 解决方案：使用 concepts 提供清晰的约束
 */
#if __cplusplus >= 202002L
#include <concepts>

template <typename T>
concept Arithmetic = std::is_arithmetic_v<T>;

template <Arithmetic T>
void good_concepts(T a, T b) {
    auto result = a + b;
    std::cout << result << std::endl;
}
#else
// C++17 替代方案
template <typename T, typename = std::enable_if_t<std::is_arithmetic_v<T>>>
void good_concepts(T a, T b) {
    auto result = a + b;
    std::cout << result << std::endl;
}
#endif

/**
 * 正确示例 3：使用 constexpr if 简化模板
 *
 * 解决方案：使用 constexpr if 减少模板特化
 */
template <typename T>
void good_constexpr_if(T value) {
    if constexpr (std::is_arithmetic_v<T>) {
        std::cout << "算术类型: " << value << std::endl;
    } else if constexpr (std::is_same_v<T, std::string>) {
        std::cout << "字符串: " << value << std::endl;
    } else {
        static_assert(std::is_arithmetic_v<T> || std::is_same_v<T, std::string>,
                      "Unsupported type");
    }
}

/**
 * 正确示例 4：使用类型萃取检查
 *
 * 解决方案：使用 type_traits 在编译时检查类型
 */
template <typename T>
void good_type_check(T value) {
    static_assert(std::is_default_constructible_v<T>,
                  "T must be default constructible");
    static_assert(std::is_copy_constructible_v<T>,
                  "T must be copy constructible");

    std::cout << "值: " << value << std::endl;
}

/**
 * 正确示例 5：使用模板别名简化
 *
 * 解决方案：使用模板别名简化复杂类型
 */
template <typename T>
using Vector = std::vector<T>;

template <typename T>
using EnableIfArithmetic = std::enable_if_t<std::is_arithmetic_v<T>>;

template <typename T, typename = EnableIfArithmetic<T>>
void good_alias(const Vector<T>& vec) {
    for (const auto& val : vec) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

/**
 * 正确示例 6：使用 requires 子句 (C++20)
 *
 * 解决方案：使用 requires 子句提供清晰约束
 */
#if __cplusplus >= 202002L
template <typename T>
requires std::is_arithmetic_v<T>
void good_requires(T a, T b) {
    auto result = a + b;
    std::cout << result << std::endl;
}
#endif

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 模板编译错误示例 ===" << std::endl;
    std::cout << std::endl;

    // 正确示例
    std::cout << "[正确示例 1] 使用 static_assert" << std::endl;
    good_static_assert(1, 2);
    // good_static_assert("a", "b");  // 编译错误：清晰的错误信息
    std::cout << std::endl;

    std::cout << "[正确示例 2] 使用 concepts/enable_if" << std::endl;
    good_concepts(1, 2);
    std::cout << std::endl;

    std::cout << "[正确示例 3] 使用 constexpr if" << std::endl;
    good_constexpr_if(42);
    good_constexpr_if(std::string("hello"));
    std::cout << std::endl;

    std::cout << "[正确示例 4] 使用类型萃取检查" << std::endl;
    good_type_check(42);
    std::cout << std::endl;

    std::cout << "[正确示例 5] 使用模板别名" << std::endl;
    Vector<int> vec = {1, 2, 3};
    good_alias(vec);
    std::cout << std::endl;

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}
