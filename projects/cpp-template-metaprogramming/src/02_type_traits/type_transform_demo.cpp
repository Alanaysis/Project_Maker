// =============================================================================
// type_transform_demo.cpp - 类型转换萃取演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o type_transform_demo type_transform_demo.cpp
// 运行: ./type_transform_demo
// =============================================================================

#include <iostream>
#include <string>
#include <type_traits>
#include "type_traits/type_transform.hpp"

// 辅助函数：打印类型名称
template <typename T>
const char* type_name() {
    if constexpr (std::is_same_v<T, int>) return "int";
    else if constexpr (std::is_same_v<T, double>) return "double";
    else if constexpr (std::is_same_v<T, const int>) return "const int";
    else if constexpr (std::is_same_v<T, volatile int>) return "volatile int";
    else if constexpr (std::is_same_v<T, int&>) return "int&";
    else if constexpr (std::is_same_v<T, int&&>) return "int&&";
    else if constexpr (std::is_same_v<T, int*>) return "int*";
    else if constexpr (std::is_same_v<T, const int*>) return "const int*";
    else if constexpr (std::is_same_v<T, int* const>) return "int* const";
    else if constexpr (std::is_same_v<T, int[]>) return "int[]";
    else if constexpr (std::is_same_v<T, int[5]>) return "int[5]";
    else return "unknown";
}

// 验证类型转换的辅助宏
#define CHECK_TYPE(from, to, expected) \
    static_assert(std::is_same_v<to, expected>, \
                  "Type transformation failed: " #from " -> " #to)

int main() {
    std::cout << "=== 类型转换萃取演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. remove_const
    std::cout << "1. remove_const:" << std::endl;
    static_assert(std::is_same_v<tmp::remove_const_t<const int>, int>);
    static_assert(std::is_same_v<tmp::remove_const_t<const int*>, const int*>);  // 不移除指向类型的 const
    static_assert(std::is_same_v<tmp::remove_const_t<int* const>, int*>);  // 移除顶层 const
    std::cout << "  const int -> int: OK" << std::endl;
    std::cout << "  const int* -> const int*: OK (不移除底层const)" << std::endl;
    std::cout << "  int* const -> int*: OK (移除顶层const)" << std::endl;
    std::cout << std::endl;

    // 2. remove_volatile
    std::cout << "2. remove_volatile:" << std::endl;
    static_assert(std::is_same_v<tmp::remove_volatile_t<volatile int>, int>);
    static_assert(std::is_same_v<tmp::remove_volatile_t<const volatile int>, const int>);
    std::cout << "  volatile int -> int: OK" << std::endl;
    std::cout << "  const volatile int -> const int: OK" << std::endl;
    std::cout << std::endl;

    // 3. remove_cv
    std::cout << "3. remove_cv:" << std::endl;
    static_assert(std::is_same_v<tmp::remove_cv_t<const volatile int>, int>);
    static_assert(std::is_same_v<tmp::remove_cv_t<const int>, int>);
    static_assert(std::is_same_v<tmp::remove_cv_t<volatile int>, int>);
    std::cout << "  const volatile int -> int: OK" << std::endl;
    std::cout << std::endl;

    // 4. remove_reference
    std::cout << "4. remove_reference:" << std::endl;
    static_assert(std::is_same_v<tmp::remove_reference_t<int&>, int>);
    static_assert(std::is_same_v<tmp::remove_reference_t<int&&>, int>);
    static_assert(std::is_same_v<tmp::remove_reference_t<const int&>, const int>);
    std::cout << "  int& -> int: OK" << std::endl;
    std::cout << "  int&& -> int: OK" << std::endl;
    std::cout << "  const int& -> const int: OK" << std::endl;
    std::cout << std::endl;

    // 5. remove_cvref (C++20)
    std::cout << "5. remove_cvref:" << std::endl;
    static_assert(std::is_same_v<tmp::remove_cvref_t<const int&>, int>);
    static_assert(std::is_same_v<tmp::remove_cvref_t<volatile int&&>, int>);
    static_assert(std::is_same_v<tmp::remove_cvref_t<const volatile int&>, int>);
    std::cout << "  const int& -> int: OK" << std::endl;
    std::cout << "  volatile int&& -> int: OK" << std::endl;
    std::cout << std::endl;

    // 6. add_pointer
    std::cout << "6. add_pointer:" << std::endl;
    static_assert(std::is_same_v<tmp::add_pointer_t<int>, int*>);
    static_assert(std::is_same_v<tmp::add_pointer_t<int&>, int&>);  // 引用不添加指针
    static_assert(std::is_same_v<tmp::add_pointer_t<int*>, int**>);
    std::cout << "  int -> int*: OK" << std::endl;
    std::cout << "  int& -> int&: OK (引用不添加指针)" << std::endl;
    std::cout << "  int* -> int**: OK" << std::endl;
    std::cout << std::endl;

    // 7. add_lvalue_reference
    std::cout << "7. add_lvalue_reference:" << std::endl;
    static_assert(std::is_same_v<tmp::add_lvalue_reference_t<int>, int&>);
    static_assert(std::is_same_v<tmp::add_lvalue_reference_t<int&>, int&>);
    static_assert(std::is_same_v<tmp::add_lvalue_reference_t<void>, void>);  // void 不添加引用
    std::cout << "  int -> int&: OK" << std::endl;
    std::cout << "  int& -> int&: OK" << std::endl;
    std::cout << "  void -> void: OK (void不添加引用)" << std::endl;
    std::cout << std::endl;

    // 8. add_rvalue_reference
    std::cout << "8. add_rvalue_reference:" << std::endl;
    static_assert(std::is_same_v<tmp::add_rvalue_reference_t<int>, int&&>);
    static_assert(std::is_same_v<tmp::add_rvalue_reference_t<int&>, int&>);  // 引用折叠
    static_assert(std::is_same_v<tmp::add_rvalue_reference_t<void>, void>);
    std::cout << "  int -> int&&: OK" << std::endl;
    std::cout << "  int& -> int&: OK (引用折叠)" << std::endl;
    std::cout << std::endl;

    // 9. add_const
    std::cout << "9. add_const:" << std::endl;
    static_assert(std::is_same_v<tmp::add_const_t<int>, const int>);
    static_assert(std::is_same_v<tmp::add_const_t<const int>, const int>);
    std::cout << "  int -> const int: OK" << std::endl;
    std::cout << "  const int -> const int: OK" << std::endl;
    std::cout << std::endl;

    // 10. make_signed / make_unsigned
    std::cout << "10. make_signed / make_unsigned:" << std::endl;
    static_assert(std::is_same_v<tmp::make_signed_t<unsigned int>, int>);
    static_assert(std::is_same_v<tmp::make_unsigned_t<int>, unsigned int>);
    static_assert(std::is_same_v<tmp::make_signed_t<unsigned long long>, long long>);
    std::cout << "  unsigned int -> int: OK" << std::endl;
    std::cout << "  int -> unsigned int: OK" << std::endl;
    std::cout << std::endl;

    // 11. decay
    std::cout << "11. decay:" << std::endl;
    static_assert(std::is_same_v<tmp::decay_t<int&>, int>);           // 引用 -> 值
    static_assert(std::is_same_v<tmp::decay_t<const int&>, int>);     // const引用 -> 值
    static_assert(std::is_same_v<tmp::decay_t<int[5]>, int*>);        // 数组 -> 指针
    static_assert(std::is_same_v<tmp::decay_t<int[]>, int*>);         // 数组 -> 指针
    static_assert(std::is_same_v<tmp::decay_t<void(int)>, void(*)(int)>);  // 函数 -> 函数指针
    static_assert(std::is_same_v<tmp::decay_t<const int>, int>);      // const -> 非const
    std::cout << "  int& -> int: OK" << std::endl;
    std::cout << "  const int& -> int: OK" << std::endl;
    std::cout << "  int[5] -> int*: OK" << std::endl;
    std::cout << "  void(int) -> void(*)(int): OK" << std::endl;
    std::cout << std::endl;

    // 12. conditional
    std::cout << "12. conditional:" << std::endl;
    using T1 = tmp::conditional_t<true, int, double>;
    using T2 = tmp::conditional_t<false, int, double>;
    static_assert(std::is_same_v<T1, int>);
    static_assert(std::is_same_v<T2, double>);
    std::cout << "  conditional<true, int, double> = int: OK" << std::endl;
    std::cout << "  conditional<false, int, double> = double: OK" << std::endl;
    std::cout << std::endl;

    // 13. enable_if
    std::cout << "13. enable_if:" << std::endl;
    using T3 = tmp::enable_if_t<true, int>;
    // using T4 = tmp::enable_if_t<false, int>;  // 编译错误：没有 type 成员
    static_assert(std::is_same_v<T3, int>);
    std::cout << "  enable_if<true, int>::type = int: OK" << std::endl;
    std::cout << "  enable_if<false, int>: SFINAE - 从重载集中移除" << std::endl;
    std::cout << std::endl;

    // 14. conjunction / disjunction / negation
    std::cout << "14. 逻辑操作:" << std::endl;
    static_assert(tmp::conjunction_v<std::true_type, std::true_type, std::true_type>);
    static_assert(!tmp::conjunction_v<std::true_type, std::false_type>);
    static_assert(tmp::disjunction_v<std::false_type, std::true_type>);
    static_assert(!tmp::disjunction_v<std::false_type, std::false_type>);
    static_assert(tmp::negation_v<std::false_type>);
    static_assert(!tmp::negation_v<std::true_type>);
    std::cout << "  conjunction(true, true, true) = true: OK" << std::endl;
    std::cout << "  conjunction(true, false) = false: OK" << std::endl;
    std::cout << "  disjunction(false, true) = true: OK" << std::endl;
    std::cout << "  negation(false) = true: OK" << std::endl;
    std::cout << std::endl;

    // 15. 实际应用：类型安全的函数
    std::cout << "15. 实际应用:" << std::endl;

    // 类型安全的移动语义
    auto forward_example = [](auto&& arg) {
        using T = std::remove_reference_t<decltype(arg)>;
        if constexpr (std::is_lvalue_reference_v<decltype(arg)>) {
            std::cout << "  Forwarding lvalue" << std::endl;
        } else {
            std::cout << "  Forwarding rvalue" << std::endl;
        }
    };

    int val = 42;
    forward_example(val);
    forward_example(42);
    forward_example(std::move(val));
    std::cout << std::endl;

    std::cout << "=== 类型转换萃取演示完成 ===" << std::endl;
    return 0;
}
