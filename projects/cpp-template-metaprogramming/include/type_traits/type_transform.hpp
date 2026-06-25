#pragma once
// =============================================================================
// type_transform.hpp - 类型转换萃取 (Type Transformation Traits)
// =============================================================================
// 实现编译期类型转换：remove_const, add_pointer, decay 等
// 原理：通过模板偏特化剥离或添加类型修饰符
// =============================================================================

#include <cstddef>
#include "basic_traits.hpp"

namespace tmp {

// ---------------------------------------------------------------------------
// remove_const - 移除顶层 const
// ---------------------------------------------------------------------------
template <typename T>
struct remove_const { using type = T; };

template <typename T>
struct remove_const<const T> { using type = T; };

template <typename T>
using remove_const_t = typename remove_const<T>::type;

// ---------------------------------------------------------------------------
// remove_volatile - 移除顶层 volatile
// ---------------------------------------------------------------------------
template <typename T>
struct remove_volatile { using type = T; };

template <typename T>
struct remove_volatile<volatile T> { using type = T; };

template <typename T>
using remove_volatile_t = typename remove_volatile<T>::type;

// ---------------------------------------------------------------------------
// remove_cv - 移除顶层 const 和 volatile
// ---------------------------------------------------------------------------
template <typename T>
struct remove_cv {
    using type = remove_const_t<remove_volatile_t<T>>;
};

template <typename T>
using remove_cv_t = typename remove_cv<T>::type;

// ---------------------------------------------------------------------------
// remove_reference - 移除引用
// ---------------------------------------------------------------------------
template <typename T>
struct remove_reference { using type = T; };

template <typename T>
struct remove_reference<T&>  { using type = T; };

template <typename T>
struct remove_reference<T&&> { using type = T; };

template <typename T>
using remove_reference_t = typename remove_reference<T>::type;

// ---------------------------------------------------------------------------
// remove_cvref - 移除 const/volatile 和引用 (C++20)
// ---------------------------------------------------------------------------
template <typename T>
struct remove_cvref {
    using type = remove_cv_t<remove_reference_t<T>>;
};

template <typename T>
using remove_cvref_t = typename remove_cvref<T>::type;

// ---------------------------------------------------------------------------
// add_pointer - 添加指针
// ---------------------------------------------------------------------------
// 主模板：对非引用类型添加指针
namespace detail {
    template <typename T, bool = is_reference_v<T> || is_void_v<T>>
    struct add_pointer_impl { using type = T; };

    template <typename T>
    struct add_pointer_impl<T, false> {
        using type = remove_reference_t<T>*;
    };
}

template <typename T>
struct add_pointer : detail::add_pointer_impl<T> {};

template <typename T>
using add_pointer_t = typename add_pointer<T>::type;

// ---------------------------------------------------------------------------
// add_lvalue_reference - 添加左值引用
// ---------------------------------------------------------------------------
namespace detail {
    template <typename T, bool = is_void_v<T>>
    struct add_lvalue_reference_impl { using type = T&; };

    template <typename T>
    struct add_lvalue_reference_impl<T, true> { using type = T; };
}

template <typename T>
struct add_lvalue_reference : detail::add_lvalue_reference_impl<T> {};

template <typename T>
using add_lvalue_reference_t = typename add_lvalue_reference<T>::type;

// ---------------------------------------------------------------------------
// add_rvalue_reference - 添加右值引用
// ---------------------------------------------------------------------------
namespace detail {
    template <typename T, bool = is_void_v<T>>
    struct add_rvalue_reference_impl { using type = T&&; };

    template <typename T>
    struct add_rvalue_reference_impl<T, true> { using type = T; };
}

template <typename T>
struct add_rvalue_reference : detail::add_rvalue_reference_impl<T> {};

template <typename T>
using add_rvalue_reference_t = typename add_rvalue_reference<T>::type;

// ---------------------------------------------------------------------------
// add_const - 添加 const
// ---------------------------------------------------------------------------
template <typename T>
struct add_const { using type = const T; };

template <typename T>
using add_const_t = typename add_const<T>::type;

// ---------------------------------------------------------------------------
// make_signed - 转为有符号类型
// ---------------------------------------------------------------------------
template <typename T>
struct make_signed { using type = T; };  // 简化版

template <> struct make_signed<unsigned char>      { using type = signed char; };
template <> struct make_signed<unsigned short>     { using type = short; };
template <> struct make_signed<unsigned int>       { using type = int; };
template <> struct make_signed<unsigned long>      { using type = long; };
template <> struct make_signed<unsigned long long> { using type = long long; };

template <typename T>
using make_signed_t = typename make_signed<T>::type;

// ---------------------------------------------------------------------------
// make_unsigned - 转为无符号类型
// ---------------------------------------------------------------------------
template <typename T>
struct make_unsigned { using type = T; };  // 简化版

template <> struct make_unsigned<signed char> { using type = unsigned char; };
template <> struct make_unsigned<short>       { using type = unsigned short; };
template <> struct make_unsigned<int>         { using type = unsigned int; };
template <> struct make_unsigned<long>        { using type = unsigned long; };
template <> struct make_unsigned<long long>   { using type = unsigned long long; };

template <typename T>
using make_unsigned_t = typename make_unsigned<T>::type;

// ---------------------------------------------------------------------------
// decay - 类型退化 (最核心的类型转换)
// ---------------------------------------------------------------------------
// 模拟函数参数传递时的类型退化：
// 1. 移除引用
// 2. 数组转指针
// 3. 函数转函数指针
namespace detail {
    template <typename T, bool = is_array_v<T>, bool = is_function_v<T>>
    struct decay_impl {
        using type = remove_cv_t<T>;
    };

    // 数组 -> 指针
    template <typename T>
    struct decay_impl<T, true, false> {
        using type = std::remove_extent_t<T>*;
    };

    // 函数 -> 函数指针
    template <typename T>
    struct decay_impl<T, false, true> {
        using type = add_pointer_t<T>;
    };
}

template <typename T>
struct decay {
    using type = typename detail::decay_impl<remove_reference_t<T>>::type;
};

template <typename T>
using decay_t = typename decay<T>::type;

// ---------------------------------------------------------------------------
// conditional - 编译期条件选择
// ---------------------------------------------------------------------------
template <bool Condition, typename TrueType, typename FalseType>
struct conditional { using type = TrueType; };

template <typename TrueType, typename FalseType>
struct conditional<false, TrueType, FalseType> { using type = FalseType; };

template <bool Condition, typename TrueType, typename FalseType>
using conditional_t = typename conditional<Condition, TrueType, FalseType>::type;

// ---------------------------------------------------------------------------
// enable_if - 条件启用 (SFINAE 核心)
// ---------------------------------------------------------------------------
template <bool Condition, typename T = void>
struct enable_if {};

template <typename T>
struct enable_if<true, T> { using type = T; };

template <bool Condition, typename T = void>
using enable_if_t = typename enable_if<Condition, T>::type;

// ---------------------------------------------------------------------------
// conjunction / disjunction / negation - 逻辑操作
// ---------------------------------------------------------------------------

// conjunction (逻辑与) - 短路求值
template <typename...>
struct conjunction : true_type {};

template <typename B1>
struct conjunction<B1> : B1 {};

template <typename B1, typename... Bn>
struct conjunction<B1, Bn...>
    : conditional_t<bool(B1::value), conjunction<Bn...>, B1> {};

template <typename... Bs>
inline constexpr bool conjunction_v = conjunction<Bs...>::value;

// disjunction (逻辑或) - 短路求值
template <typename...>
struct disjunction : false_type {};

template <typename B1>
struct disjunction<B1> : B1 {};

template <typename B1, typename... Bn>
struct disjunction<B1, Bn...>
    : conditional_t<bool(B1::value), B1, disjunction<Bn...>> {};

template <typename... Bs>
inline constexpr bool disjunction_v = disjunction<Bs...>::value;

// negation (逻辑非)
template <typename B>
struct negation : integral_constant<bool, !bool(B::value)> {};

template <typename B>
inline constexpr bool negation_v = negation<B>::value;

} // namespace tmp
