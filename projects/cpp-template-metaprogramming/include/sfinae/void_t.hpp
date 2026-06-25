#pragma once
// =============================================================================
// void_t.hpp - void_t 技巧 (The void_t Trick)
// =============================================================================
// void_t 是 C++17 引入的 SFINAE 工具
// 原理：将任意类型映射为 void，利用 SFINAE 检测表达式是否合法
// =============================================================================

#include <type_traits>
#include <iostream>
#include <vector>
#include <string>

namespace tmp {
namespace sfinae {

// ---------------------------------------------------------------------------
// void_t 定义
// ---------------------------------------------------------------------------
// 核心：任何有效类型经过 void_t 映射后都是 void
template <typename...>
using void_t = void;

// ---------------------------------------------------------------------------
// void_t 检测成员类型
// ---------------------------------------------------------------------------

// 检测类型是否有 value_type 成员
template <typename T, typename = void>
struct has_value_type : std::false_type {};

template <typename T>
struct has_value_type<T, void_t<typename T::value_type>> : std::true_type {};

template <typename T>
inline constexpr bool has_value_type_v = has_value_type<T>::value;

// 检测类型是否有 iterator 成员
template <typename T, typename = void>
struct has_iterator : std::false_type {};

template <typename T>
struct has_iterator<T, void_t<typename T::iterator>> : std::true_type {};

template <typename T>
inline constexpr bool has_iterator_v = has_iterator<T>::value;

// 检测类型是否有 size_type 成员
template <typename T, typename = void>
struct has_size_type : std::false_type {};

template <typename T>
struct has_size_type<T, void_t<typename T::size_type>> : std::true_type {};

template <typename T>
inline constexpr bool has_size_type_v = has_size_type<T>::value;

// ---------------------------------------------------------------------------
// void_t 检测成员函数
// ---------------------------------------------------------------------------

// 检测是否有 begin() 成员函数
template <typename T, typename = void>
struct has_begin : std::false_type {};

template <typename T>
struct has_begin<T, void_t<decltype(std::declval<T>().begin())>> : std::true_type {};

template <typename T>
inline constexpr bool has_begin_v = has_begin<T>::value;

// 检测是否有 end() 成员函数
template <typename T, typename = void>
struct has_end : std::false_type {};

template <typename T>
struct has_end<T, void_t<decltype(std::declval<T>().end())>> : std::true_type {};

template <typename T>
inline constexpr bool has_end_v = has_end<T>::value;

// 检测是否有 push_back() 成员函数
template <typename T, typename = void>
struct has_push_back : std::false_type {};

template <typename T>
struct has_push_back<T, void_t<decltype(
    std::declval<T>().push_back(std::declval<typename T::value_type>())
)>> : std::true_type {};

template <typename T>
inline constexpr bool has_push_back_v = has_push_back<T>::value;

// 检测是否有 emplace_back() 成员函数
template <typename T, typename = void>
struct has_emplace_back : std::false_type {};

template <typename T>
struct has_emplace_back<T, void_t<decltype(
    std::declval<T>().emplace_back()
)>> : std::true_type {};

template <typename T>
inline constexpr bool has_emplace_back_v = has_emplace_back<T>::value;

// ---------------------------------------------------------------------------
// void_t 检测操作符
// ---------------------------------------------------------------------------

// 检测是否有 operator==
template <typename T, typename U = T, typename = void>
struct has_equal : std::false_type {};

template <typename T, typename U>
struct has_equal<T, U, void_t<decltype(
    std::declval<T>() == std::declval<U>()
)>> : std::true_type {};

template <typename T, typename U = T>
inline constexpr bool has_equal_v = has_equal<T, U>::value;

// 检测是否有 operator<
template <typename T, typename U = T, typename = void>
struct has_less : std::false_type {};

template <typename T, typename U>
struct has_less<T, U, void_t<decltype(
    std::declval<T>() < std::declval<U>()
)>> : std::true_type {};

template <typename T, typename U = T>
inline constexpr bool has_less_v = has_less<T, U>::value;

// 检测是否有 operator<<（可输出到 ostream）
template <typename T, typename = void>
struct is_printable : std::false_type {};

template <typename T>
struct is_printable<T, void_t<decltype(
    std::declval<std::ostream&>() << std::declval<T>()
)>> : std::true_type {};

template <typename T>
inline constexpr bool is_printable_v = is_printable<T>::value;

// ---------------------------------------------------------------------------
// void_t 综合能力检测
// ---------------------------------------------------------------------------

// 检测是否为容器类型（同时具有多种容器特征）
template <typename T, typename = void>
struct is_container : std::false_type {};

template <typename T>
struct is_container<T, void_t<
    typename T::value_type,
    typename T::size_type,
    typename T::iterator,
    decltype(std::declval<T>().size()),
    decltype(std::declval<T>().begin()),
    decltype(std::declval<T>().end())
>> : std::true_type {};

template <typename T>
inline constexpr bool is_container_v = is_container<T>::value;

// ---------------------------------------------------------------------------
// void_t 用于条件打印
// ---------------------------------------------------------------------------

// 只有可打印类型才能调用此函数
template <typename T>
std::enable_if_t<is_printable_v<T>>
print_if_possible(const T& value) {
    std::cout << value << std::endl;
}

template <typename T>
std::enable_if_t<!is_printable_v<T>>
print_if_possible(const T&) {
    std::cout << "[not printable]" << std::endl;
}

} // namespace sfinae
} // namespace tmp
