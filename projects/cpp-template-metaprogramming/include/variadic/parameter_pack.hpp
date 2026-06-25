#pragma once
// =============================================================================
// parameter_pack.hpp - 可变参数模板 (Variadic Templates)
// =============================================================================
// 可变参数模板是模板元编程最重要的特性之一
// 支持任意数量和类型的模板参数
// =============================================================================

#include <iostream>
#include <string>
#include <tuple>
#include <cstddef>

namespace tmp {
namespace variadic {

// ---------------------------------------------------------------------------
// 参数包基础 - 递归展开
// ---------------------------------------------------------------------------

// 递归终止条件（基本情况）
inline void print() {
    std::cout << std::endl;
}

// 递归展开：每次处理一个参数，递归处理剩余参数
template <typename T, typename... Args>
void print(const T& first, const Args&... rest) {
    std::cout << first;
    if constexpr (sizeof...(rest) > 0) {
        std::cout << ", ";
    }
    print(rest...);
}

// ---------------------------------------------------------------------------
// sizeof... 运算符 - 获取参数包大小
// ---------------------------------------------------------------------------

template <typename... Args>
constexpr std::size_t count_args() {
    return sizeof...(Args);
}

template <typename... Args>
constexpr std::size_t count_args_values(const Args&...) {
    return sizeof...(Args);
}

// ---------------------------------------------------------------------------
// 参数包展开技巧
// ---------------------------------------------------------------------------

// 技巧1：通过初始化列表展开
template <typename... Args>
void print_with_index(const Args&... args) {
    std::size_t index = 0;
    // 使用初始化列表和逗号运算符展开参数包
    ((std::cout << "[" << index++ << "] " << args << "\n"), ...);
}

// 技巧2：使用折叠表达式 (C++17)
template <typename... Args>
auto sum(const Args&... args) {
    return (args + ...);
}

template <typename... Args>
auto product(const Args&... args) {
    return (args * ...);
}

// 技巧3：参数包用于构造 tuple
template <typename... Args>
auto make_tuple_wrapper(Args&&... args) {
    return std::make_tuple(std::forward<Args>(args)...);
}

// ---------------------------------------------------------------------------
// 递归模板类 - 编译期递归处理参数包
// ---------------------------------------------------------------------------

// 求和的递归模板
template <typename T, typename... Args>
struct Sum {
    static constexpr auto value = T::value + Sum<Args...>::value;
};

// 递归终止
template <typename T>
struct Sum<T> {
    static constexpr auto value = T::value;
};

// ---------------------------------------------------------------------------
// 索引序列技巧 (Index Sequence)
// ---------------------------------------------------------------------------

// 编译期生成索引 0, 1, 2, ..., N-1
template <std::size_t... Is>
struct index_sequence {};

// 递归构建 index_sequence
template <std::size_t N, std::size_t... Is>
struct make_index_sequence_impl : make_index_sequence_impl<N - 1, N - 1, Is...> {};

template <std::size_t... Is>
struct make_index_sequence_impl<0, Is...> {
    using type = index_sequence<Is...>;
};

template <std::size_t N>
using make_index_sequence = typename make_index_sequence_impl<N>::type;

// 使用索引序列展开 tuple
template <typename Tuple, std::size_t... Is>
void print_tuple_impl(const Tuple& t, index_sequence<Is...>) {
    ((std::cout << std::get<Is>(t) << (Is < sizeof...(Is) - 1 ? ", " : "")), ...);
}

template <typename... Args>
void print_tuple(const std::tuple<Args...>& t) {
    std::cout << "(";
    print_tuple_impl(t, make_index_sequence<sizeof...(Args)>{});
    std::cout << ")" << std::endl;
}

// ---------------------------------------------------------------------------
// 参数包过滤与转换
// ---------------------------------------------------------------------------

// 过滤：只处理满足条件的参数
template <typename Pred, typename... Args>
void for_each_if(Pred pred, const Args&... args) {
    ((pred(args) ? (std::cout << args << " ", 0) : 0), ...);
    std::cout << std::endl;
}

// 转换：对每个参数应用函数
template <typename Func, typename... Args>
auto transform(Func func, const Args&... args) {
    return std::make_tuple(func(args)...);
}

// ---------------------------------------------------------------------------
// 多参数包展开
// ---------------------------------------------------------------------------

// 同时展开两个参数包
template <typename... Types, typename... Values>
void assign_pairs(const Values&... values) {
    // 注意：这里只是演示，实际使用需要更复杂的实现
    static_assert(sizeof...(Types) == sizeof...(Values),
                  "Types and Values must have the same size");
    ((std::cout << values << " "), ...);
    std::cout << std::endl;
}

// ---------------------------------------------------------------------------
// 递归终止的不同策略
// ---------------------------------------------------------------------------

// 策略1：空函数重载
inline void strategy1_print() {}
template <typename T, typename... Args>
void strategy1_print(const T& first, const Args&... rest) {
    std::cout << first << " ";
    strategy1_print(rest...);
}

// 策略2：if constexpr (C++17)
template <typename T, typename... Args>
void strategy2_print(const T& first, const Args&... rest) {
    std::cout << first << " ";
    if constexpr (sizeof...(rest) > 0) {
        strategy2_print(rest...);
    }
}

// 策略3：折叠表达式 (C++17)
template <typename... Args>
void strategy3_print(const Args&... args) {
    ((std::cout << args << " "), ...);
    std::cout << std::endl;
}

// ---------------------------------------------------------------------------
// 实用：类型安全的 printf
// ---------------------------------------------------------------------------

// 简化版的类型安全 printf
void safe_printf(const char* format) {
    std::cout << format;
}

template <typename T, typename... Args>
void safe_printf(const char* format, const T& value, const Args&... args) {
    while (*format) {
        if (*format == '{' && *(format + 1) == '}') {
            std::cout << value;
            safe_printf(format + 2, args...);
            return;
        }
        std::cout << *format;
        ++format;
    }
}

} // namespace variadic
} // namespace tmp
