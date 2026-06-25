#pragma once
// =============================================================================
// expression_detector.hpp - 表达式合法性检测 (Expression Validity Detection)
// =============================================================================
// 通用的表达式检测框架，可以检测任意表达式是否合法
// 这是 void_t 的进阶应用，也是 C++20 Concepts 的替代方案
// =============================================================================

#include <type_traits>
#include <string>

namespace tmp {
namespace sfinae {

// ---------------------------------------------------------------------------
// 通用检测宏 - 定义检测器的快捷方式
// ---------------------------------------------------------------------------
// 用法：DEFINE_DETECTOR(name, expression)
// 生成 has_name<T> 和 has_name_v<T>

#define DEFINE_DETECTOR(NAME, EXPR)                                  \
    template <typename T, typename = void>                           \
    struct has_##NAME : std::false_type {};                          \
                                                                     \
    template <typename T>                                            \
    struct has_##NAME<T, decltype(void(EXPR))> : std::true_type {};  \
                                                                     \
    template <typename T>                                            \
    inline constexpr bool has_##NAME##_v = has_##NAME<T>::value

// ---------------------------------------------------------------------------
// 手动实现的检测器示例
// ---------------------------------------------------------------------------

// 检测是否有 to_string() 成员函数
template <typename T, typename = void>
struct has_to_string : std::false_type {};

template <typename T>
struct has_to_string<T, decltype(void(std::declval<T>().to_string()))>
    : std::true_type {};

template <typename T>
inline constexpr bool has_to_string_v = has_to_string<T>::value;

// 检测是否有 hash() 成员函数
template <typename T, typename = void>
struct has_hash : std::false_type {};

template <typename T>
struct has_hash<T, decltype(void(std::declval<T>().hash()))>
    : std::true_type {};

template <typename T>
inline constexpr bool has_hash_v = has_hash<T>::value;

// 检测是否可以用 {} 初始化列表构造
template <typename T, typename = void>
struct is_brace_constructible : std::false_type {};

template <typename T>
struct is_brace_constructible<T, decltype(void(T{}))>
    : std::true_type {};

template <typename T>
inline constexpr bool is_brace_constructible_v = is_brace_constructible<T>::value;

// ---------------------------------------------------------------------------
// 复合条件检测
// ---------------------------------------------------------------------------

// 检测是否同时满足多个条件
template <typename T>
struct is_complete_type_check {
    // 必须可以默认构造
    static constexpr bool default_constructible = std::is_default_constructible_v<T>;
    // 必须可以拷贝构造
    static constexpr bool copy_constructible = std::is_copy_constructible_v<T>;
    // 必须可以拷贝赋值
    static constexpr bool copy_assignable = std::is_copy_assignable_v<T>;
    // 必须可以析构
    static constexpr bool destructible = std::is_destructible_v<T>;

    static constexpr bool value = default_constructible &&
                                   copy_constructible &&
                                   copy_assignable &&
                                   destructible;
};

template <typename T>
inline constexpr bool is_complete_type_check_v = is_complete_type_check<T>::value;

// ---------------------------------------------------------------------------
// 检测是否存在特定的嵌套类型
// ---------------------------------------------------------------------------

// 检测是否有嵌套的 traits 类型
template <typename T, typename = void>
struct has_traits : std::false_type {};

template <typename T>
struct has_traits<T, void_t<typename T::traits>> : std::true_type {};

template <typename T>
inline constexpr bool has_traits_v = has_traits<T>::value;

// 检测是否有嵌套的 allocator_type
template <typename T, typename = void>
struct has_allocator_type : std::false_type {};

template <typename T>
struct has_allocator_type<T, void_t<typename T::allocator_type>> : std::true_type {};

template <typename T>
inline constexpr bool has_allocator_type_v = has_allocator_type<T>::value;

// ---------------------------------------------------------------------------
// 使用检测器进行条件分发
// ---------------------------------------------------------------------------

// 通用的 to_string 封装
template <typename T>
auto safe_to_string(const T& obj) -> std::string {
    if constexpr (has_to_string_v<T>) {
        return obj.to_string();
    } else {
        return "[no to_string]";
    }
}

// ---------------------------------------------------------------------------
// 检测运算符是否可用
// ---------------------------------------------------------------------------

// 检测是否可以解引用
template <typename T, typename = void>
struct is_dereferenceable : std::false_type {};

template <typename T>
struct is_dereferenceable<T, void_t<decltype(*std::declval<T>())>>
    : std::true_type {};

template <typename T>
inline constexpr bool is_dereferenceable_v = is_dereferenceable<T>::value;

// 检测是否可以用 ++ 自增
template <typename T, typename = void>
struct is_incrementable : std::false_type {};

template <typename T>
struct is_incrementable<T, void_t<decltype(++std::declval<T&>())>>
    : std::true_type {};

template <typename T>
inline constexpr bool is_incrementable_v = is_incrementable<T>::value;

// 检测是否可以用 [] 索引
template <typename T, typename Index = std::size_t, typename = void>
struct is_indexable : std::false_type {};

template <typename T, typename Index>
struct is_indexable<T, Index, void_t<decltype(std::declval<T>()[std::declval<Index>()])>>
    : std::true_type {};

template <typename T, typename Index = std::size_t>
inline constexpr bool is_indexable_v = is_indexable<T, Index>::value;

// 检测是否可以用 () 调用
template <typename T, typename = void>
struct is_callable : std::false_type {};

template <typename T>
struct is_callable<T, void_t<decltype(std::declval<T>()())>>
    : std::true_type {};

template <typename T>
inline constexpr bool is_callable_v = is_callable<T>::value;

} // namespace sfinae
} // namespace tmp
