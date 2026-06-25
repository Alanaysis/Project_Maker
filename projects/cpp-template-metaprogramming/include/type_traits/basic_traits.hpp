#pragma once
// =============================================================================
// basic_traits.hpp - 基础类型判断 (Basic Type Classification Traits)
// =============================================================================
// 实现编译期类型判断：is_integral, is_floating_point, is_pointer 等
// 原理：通过模板特化匹配不同类型，返回编译期常量
// =============================================================================

#include <cstddef>

namespace tmp {

// ---------------------------------------------------------------------------
// integral_constant - 所有类型萃取的基类
// ---------------------------------------------------------------------------
// 编译期常量包装器，true_type/false_type 的基础
template <typename T, T Value>
struct integral_constant {
    static constexpr T value = Value;
    using value_type = T;
    using type = integral_constant<T, Value>;
    constexpr operator value_type() const noexcept { return value; }
    constexpr value_type operator()() const noexcept { return value; }
};

// true_type / false_type 预定义
using true_type  = integral_constant<bool, true>;
using false_type = integral_constant<bool, false>;

// ---------------------------------------------------------------------------
// is_integral - 判断是否为整数类型
// ---------------------------------------------------------------------------
// 主模板：默认返回 false
template <typename T>
struct is_integral : false_type {};

// 对所有整数类型特化为 true
template <> struct is_integral<bool>               : true_type {};
template <> struct is_integral<char>               : true_type {};
template <> struct is_integral<signed char>        : true_type {};
template <> struct is_integral<unsigned char>      : true_type {};
template <> struct is_integral<wchar_t>            : true_type {};
template <> struct is_integral<char16_t>           : true_type {};
template <> struct is_integral<char32_t>           : true_type {};
template <> struct is_integral<short>              : true_type {};
template <> struct is_integral<unsigned short>     : true_type {};
template <> struct is_integral<int>                : true_type {};
template <> struct is_integral<unsigned int>       : true_type {};
template <> struct is_integral<long>               : true_type {};
template <> struct is_integral<unsigned long>      : true_type {};
template <> struct is_integral<long long>          : true_type {};
template <> struct is_integral<unsigned long long> : true_type {};

// C++20: char8_t
#if __cplusplus >= 202002L
template <> struct is_integral<char8_t>            : true_type {};
#endif

// 便捷变量模板
template <typename T>
inline constexpr bool is_integral_v = is_integral<T>::value;

// ---------------------------------------------------------------------------
// is_floating_point - 判断是否为浮点类型
// ---------------------------------------------------------------------------
template <typename T>
struct is_floating_point : false_type {};

template <> struct is_floating_point<float>       : true_type {};
template <> struct is_floating_point<double>      : true_type {};
template <> struct is_floating_point<long double> : true_type {};

template <typename T>
inline constexpr bool is_floating_point_v = is_floating_point<T>::value;

// ---------------------------------------------------------------------------
// is_arithmetic - 判断是否为算术类型 (整数 + 浮点)
// ---------------------------------------------------------------------------
template <typename T>
struct is_arithmetic
    : integral_constant<bool, is_integral_v<T> || is_floating_point_v<T>> {};

template <typename T>
inline constexpr bool is_arithmetic_v = is_arithmetic<T>::value;

// ---------------------------------------------------------------------------
// is_pointer - 判断是否为指针类型
// ---------------------------------------------------------------------------
// 主模板：非指针
template <typename T>
struct is_pointer : false_type {};

// 偏特化：匹配所有指针类型
template <typename T>
struct is_pointer<T*> : true_type {};

template <typename T>
inline constexpr bool is_pointer_v = is_pointer<T>::value;

// ---------------------------------------------------------------------------
// is_reference - 判断是否为引用类型
// ---------------------------------------------------------------------------
template <typename T>
struct is_reference : false_type {};

template <typename T>
struct is_reference<T&>  : true_type {};
template <typename T>
struct is_reference<T&&> : true_type {};

template <typename T>
inline constexpr bool is_reference_v = is_reference<T>::value;

// ---------------------------------------------------------------------------
// is_void - 判断是否为 void 类型
// ---------------------------------------------------------------------------
template <typename T>
struct is_void : false_type {};

template <> struct is_void<void>                : true_type {};
template <> struct is_void<const void>          : true_type {};
template <> struct is_void<volatile void>       : true_type {};
template <> struct is_void<const volatile void> : true_type {};

template <typename T>
inline constexpr bool is_void_v = is_void<T>::value;

// ---------------------------------------------------------------------------
// is_array - 判断是否为数组类型
// ---------------------------------------------------------------------------
template <typename T>
struct is_array : false_type {};

template <typename T>
struct is_array<T[]> : true_type {};

template <typename T, std::size_t N>
struct is_array<T[N]> : true_type {};

template <typename T>
inline constexpr bool is_array_v = is_array<T>::value;

// ---------------------------------------------------------------------------
// is_const - 判断是否为 const 类型
// ---------------------------------------------------------------------------
template <typename T>
struct is_const : false_type {};

template <typename T>
struct is_const<const T> : true_type {};

template <typename T>
inline constexpr bool is_const_v = is_const<T>::value;

// ---------------------------------------------------------------------------
// is_function - 判断是否为函数类型
// ---------------------------------------------------------------------------
// 利用函数类型不能 const 修饰的特性
template <typename T>
struct is_function : integral_constant<bool,
    !is_const_v<const T> && !is_reference_v<T>> {};

template <typename T>
inline constexpr bool is_function_v = is_function<T>::value;

} // namespace tmp
