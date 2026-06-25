#pragma once
// =============================================================================
// type_relations.hpp - 类型关系萃取 (Type Relation Traits)
// =============================================================================
// 实现编译期类型关系判断：is_same, is_base_of, is_convertible 等
// =============================================================================

#include "basic_traits.hpp"
#include "type_transform.hpp"

namespace tmp {

// ---------------------------------------------------------------------------
// is_same - 判断两个类型是否相同
// ---------------------------------------------------------------------------
// 主模板：类型不同
template <typename T, typename U>
struct is_same : false_type {};

// 特化：类型相同
template <typename T>
struct is_same<T, T> : true_type {};

template <typename T, typename U>
inline constexpr bool is_same_v = is_same<T, U>::value;

// ---------------------------------------------------------------------------
// is_base_of - 判断是否为基类关系
// ---------------------------------------------------------------------------
// 利用派生类指针可以隐式转换为基类指针的特性
namespace detail {
    // 两个重载版本，返回不同大小的类型
    using Yes = char[1];
    using No  = char[2];

    // 接受 Base* 的版本（优先匹配）
    template <typename Base>
    Yes& test_base(Base*);

    // 接受任意参数的兜底版本
    template <typename Base>
    No& test_base(...);

    // 辅助：检查 Derived* 能否转换为 Base*
    template <typename Base, typename Derived>
    struct is_base_of_helper {
        static constexpr bool value =
            sizeof(test_base<Base>(static_cast<Derived*>(nullptr))) == sizeof(Yes);
    };
}

template <typename Base, typename Derived>
struct is_base_of
    : integral_constant<bool,
        detail::is_base_of_helper<
            remove_cv_t<Base>,
            remove_cv_t<Derived>
        >::value> {};

// 特化：相同类型
template <typename T>
struct is_base_of<T, T> : true_type {};

template <typename Base, typename Derived>
inline constexpr bool is_base_of_v = is_base_of<Base, Derived>::value;

// ---------------------------------------------------------------------------
// is_convertible - 判断类型是否可隐式转换
// ---------------------------------------------------------------------------
// 检查 From 类型是否可以隐式转换为 To 类型
namespace detail {
    // 辅助函数：接受 To 类型
    template <typename To>
    void test_convertible(To);

    template <typename From, typename To, typename = void>
    struct is_convertible_helper : false_type {};

    template <typename From, typename To>
    struct is_convertible_helper<From, To,
        decltype(test_convertible<To>(std::declval<From>()))> : true_type {};
}

template <typename From, typename To>
struct is_convertible : detail::is_convertible_helper<From, To> {};

// void -> void 特化
template <>
struct is_convertible<void, void> : true_type {};

template <typename From, typename To>
inline constexpr bool is_convertible_v = is_convertible<From, To>::value;

// ---------------------------------------------------------------------------
// is_invocable - 判断是否可调用 (C++17)
// ---------------------------------------------------------------------------
namespace detail {
    template <typename F, typename... Args, typename = void>
    struct is_invocable_helper : false_type {};

    template <typename F, typename... Args>
    struct is_invocable_helper<F, Args...,
        decltype(void(std::declval<F>()(std::declval<Args>()...)))> : true_type {};
}

template <typename F, typename... Args>
struct is_invocable : detail::is_invocable_helper<F, Args...> {};

template <typename F, typename... Args>
inline constexpr bool is_invocable_v = is_invocable<F, Args...>::value;

// ---------------------------------------------------------------------------
// is_assignable - 判断是否可赋值
// ---------------------------------------------------------------------------
namespace detail {
    template <typename T, typename U, typename = void>
    struct is_assignable_helper : false_type {};

    template <typename T, typename U>
    struct is_assignable_helper<T, U,
        decltype(void(std::declval<T>() = std::declval<U>()))> : true_type {};
}

template <typename T, typename U>
struct is_assignable : detail::is_assignable_helper<T, U> {};

template <typename T, typename U>
inline constexpr bool is_assignable_v = is_assignable<T, U>::value;

// ---------------------------------------------------------------------------
// is_constructible - 判断是否可构造
// ---------------------------------------------------------------------------
namespace detail {
    template <typename T, typename... Args, typename = void>
    struct is_constructible_helper : false_type {};

    template <typename T, typename... Args>
    struct is_constructible_helper<T, Args...,
        decltype(void(T(std::declval<Args>()...)))> : true_type {};
}

template <typename T, typename... Args>
struct is_constructible : detail::is_constructible_helper<T, Args...> {};

template <typename T, typename... Args>
inline constexpr bool is_constructible_v = is_constructible<T, Args...>::value;

// ---------------------------------------------------------------------------
// is_default_constructible - 判断是否可默认构造
// ---------------------------------------------------------------------------
template <typename T>
struct is_default_constructible : is_constructible<T> {};

template <typename T>
inline constexpr bool is_default_constructible_v = is_default_constructible<T>::value;

// ---------------------------------------------------------------------------
// is_copy_constructible - 判断是否可拷贝构造
// ---------------------------------------------------------------------------
template <typename T>
struct is_copy_constructible
    : is_constructible<T, add_lvalue_reference_t<const T>> {};

template <typename T>
inline constexpr bool is_copy_constructible_v = is_copy_constructible<T>::value;

// ---------------------------------------------------------------------------
// is_move_constructible - 判断是否可移动构造
// ---------------------------------------------------------------------------
template <typename T>
struct is_move_constructible
    : is_constructible<T, add_rvalue_reference_t<T>> {};

template <typename T>
inline constexpr bool is_move_constructible_v = is_move_constructible<T>::value;

} // namespace tmp
