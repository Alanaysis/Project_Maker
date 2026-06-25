#pragma once
/**
 * @file member_detection.hpp
 * @brief SFINAE 成员检测 - 检测类型是否具有特定成员
 *
 * 使用 SFINAE (Substitution Failure Is Not An Error) 技术
 * 在编译期检测类型是否具有特定的成员函数、成员类型或成员变量。
 *
 * 包含：
 *   - 成员函数检测
 *   - 成员类型检测
 *   - 成员变量检测
 *   - C++20 requires 表达式版本
 */

#include <type_traits>
#include <string>
#include <iostream>
#include <vector>

namespace tmp {

// ============================================================================
// 1. 经典 SFINAE 成员函数检测 (void_t 技巧)
// ============================================================================

/**
 * @brief void_t - C++17 标准库已有，这里演示原理
 * 将任意类型映射为 void，如果替换失败则 SFINAE 生效
 */
template <typename...>
using void_t = void;

// --- 检测 size() 成员函数 ---

template <typename T, typename = void>
struct has_size : std::false_type {};

template <typename T>
struct has_size<T, void_t<decltype(std::declval<T>().size())>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_size_v = has_size<T>::value;

// --- 检测 begin() / end() 成员函数 ---

template <typename T, typename = void>
struct has_begin_end : std::false_type {};

template <typename T>
struct has_begin_end<T, void_t<
    decltype(std::declval<T>().begin()),
    decltype(std::declval<T>().end())>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_begin_end_v = has_begin_end<T>::value;

// --- 检测 push_back() 成员函数 ---

template <typename T, typename Arg, typename = void>
struct has_push_back : std::false_type {};

template <typename T, typename Arg>
struct has_push_back<T, Arg, void_t<
    decltype(std::declval<T>().push_back(std::declval<Arg>()))>>
    : std::true_type {};

template <typename T, typename Arg>
inline constexpr bool has_push_back_v = has_push_back<T, Arg>::value;

// --- 检测 reserve() 成员函数 ---

template <typename T, typename = void>
struct has_reserve : std::false_type {};

template <typename T>
struct has_reserve<T, void_t<
    decltype(std::declval<T>().reserve(std::declval<std::size_t>()))>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_reserve_v = has_reserve<T>::value;

// --- 检测 clear() 成员函数 ---

template <typename T, typename = void>
struct has_clear : std::false_type {};

template <typename T>
struct has_clear<T, void_t<decltype(std::declval<T>().clear())>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_clear_v = has_clear<T>::value;

// --- 检测 empty() 成员函数 ---

template <typename T, typename = void>
struct has_empty : std::false_type {};

template <typename T>
struct has_empty<T, void_t<decltype(std::declval<T>().empty())>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_empty_v = has_empty<T>::value;

// --- 检测 to_string() 成员函数 ---

template <typename T, typename = void>
struct has_to_string : std::false_type {};

template <typename T>
struct has_to_string<T, void_t<decltype(std::declval<T>().to_string())>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_to_string_v = has_to_string<T>::value;

// --- 检测指定签名的成员函数 ---

template <typename T, typename Ret, typename... Args>
struct has_method_with_signature {
private:
    template <typename U>
    static auto test(int) -> decltype(
        std::declval<U>().operator()(std::declval<Args>()...),
        std::true_type{});

    template <typename>
    static std::false_type test(...);

public:
    static constexpr bool value = decltype(test<T>(0))::value;
};

// ============================================================================
// 2. 成员类型检测
// ============================================================================

// --- 检测 value_type ---

template <typename T, typename = void>
struct has_value_type : std::false_type {};

template <typename T>
struct has_value_type<T, void_t<typename T::value_type>> : std::true_type {};

template <typename T>
inline constexpr bool has_value_type_v = has_value_type<T>::value;

// --- 检测 iterator ---

template <typename T, typename = void>
struct has_iterator : std::false_type {};

template <typename T>
struct has_iterator<T, void_t<typename T::iterator>> : std::true_type {};

template <typename T>
inline constexpr bool has_iterator_v = has_iterator<T>::value;

// --- 检测 const_iterator ---

template <typename T, typename = void>
struct has_const_iterator : std::false_type {};

template <typename T>
struct has_const_iterator<T, void_t<typename T::const_iterator>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_const_iterator_v = has_const_iterator<T>::value;

// --- 检测 allocator_type ---

template <typename T, typename = void>
struct has_allocator_type : std::false_type {};

template <typename T>
struct has_allocator_type<T, void_t<typename T::allocator_type>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_allocator_type_v = has_allocator_type<T>::value;

// ============================================================================
// 3. 成员变量检测
// ============================================================================

// --- 检测 .data 成员变量 ---

template <typename T, typename = void>
struct has_data_member : std::false_type {};

template <typename T>
struct has_data_member<T, void_t<decltype(std::declval<T>().data)>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_data_member_v = has_data_member<T>::value;

// ============================================================================
// 4. 运算符检测
// ============================================================================

// --- 检测 operator== ---

template <typename T, typename U = T, typename = void>
struct has_equal_operator : std::false_type {};

template <typename T, typename U>
struct has_equal_operator<T, U, void_t<
    decltype(std::declval<T>() == std::declval<U>())>>
    : std::true_type {};

template <typename T, typename U = T>
inline constexpr bool has_equal_operator_v = has_equal_operator<T, U>::value;

// --- 检测 operator< ---

template <typename T, typename U = T, typename = void>
struct has_less_operator : std::false_type {};

template <typename T, typename U>
struct has_less_operator<T, U, void_t<
    decltype(std::declval<T>() < std::declval<U>())>>
    : std::true_type {};

template <typename T, typename U = T>
inline constexpr bool has_less_operator_v = has_less_operator<T, U>::value;

// --- 棣测 operator<< ---

template <typename T, typename = void>
struct has_stream_operator : std::false_type {};

template <typename T>
struct has_stream_operator<T, void_t<
    decltype(std::declval<std::ostream&>() << std::declval<T>())>>
    : std::true_type {};

template <typename T>
inline constexpr bool has_stream_operator_v = has_stream_operator<T>::value;

// --- 检测 operator+ ---

template <typename T, typename U = T, typename = void>
struct has_plus_operator : std::false_type {};

template <typename T, typename U>
struct has_plus_operator<T, U, void_t<
    decltype(std::declval<T>() + std::declval<U>())>>
    : std::true_type {};

template <typename T, typename U = T>
inline constexpr bool has_plus_operator_v = has_plus_operator<T, U>::value;

// --- 检测 operator[] ---

template <typename T, typename Index, typename = void>
struct has_subscript_operator : std::false_type {};

template <typename T, typename Index>
struct has_subscript_operator<T, Index, void_t<
    decltype(std::declval<T>()[std::declval<Index>()])>>
    : std::true_type {};

template <typename T, typename Index = std::size_t>
inline constexpr bool has_subscript_operator_v =
    has_subscript_operator<T, Index>::value;

// ============================================================================
// 5. 复杂表达式检测
// ============================================================================

/**
 * @brief 检测类型是否可迭代（范围 for 可用）
 */
template <typename T, typename = void>
struct is_iterable : std::false_type {};

template <typename T>
struct is_iterable<T, void_t<
    decltype(std::begin(std::declval<T&>())),
    decltype(std::end(std::declval<T&>()))>>
    : std::true_type {};

template <typename T>
inline constexpr bool is_iterable_v = is_iterable<T>::value;

/**
 * @brief 检测类型是否可调用（函数对象、lambda 等）
 */
template <typename T, typename = void>
struct is_callable : std::false_type {};

// 只对类类型检测 operator()
template <typename T>
struct is_callable<T, std::enable_if_t<std::is_class_v<T>,
    void_t<decltype(&T::operator())>>> : std::true_type {};

/**
 * @brief 检测类型是否可哈希
 */
template <typename T, typename = void>
struct is_hashable : std::false_type {};

template <typename T>
struct is_hashable<T, void_t<decltype(std::declval<std::hash<T>>()
                                       (std::declval<T>()))>>
    : std::true_type {};

template <typename T>
inline constexpr bool is_hashable_v = is_hashable<T>::value;

/**
 * @brief 检测类型是否可比较（支持 == 和 <）
 */
template <typename T, typename = void>
struct is_comparable : std::false_type {};

template <typename T>
struct is_comparable<T, void_t<
    decltype(std::declval<T>() == std::declval<T>()),
    decltype(std::declval<T>() < std::declval<T>())>>
    : std::true_type {};

template <typename T>
inline constexpr bool is_comparable_v = is_comparable<T>::value;

// ============================================================================
// 6. 通用检测宏（简化定义）
// ============================================================================

/**
 * @brief 定义通用成员函数检测器
 *
 * 用法：
 *   DEFINE_HAS_MEMBER(foo);       // 检测 foo 成员
 *   constexpr bool v = has_foo_v<MyType>;
 */

#define DEFINE_HAS_MEMBER(member_name)                                      \
    template <typename T, typename = void>                                  \
    struct has_##member_name : std::false_type {};                          \
                                                                            \
    template <typename T>                                                   \
    struct has_##member_name<T, ::tmp::void_t<decltype(&T::member_name)>>   \
        : std::true_type {};

// ============================================================================
// 7. 带返回类型检测的成员函数检测
// ============================================================================

/**
 * @brief 检测成员函数是否返回特定类型
 */
template <typename T, typename Ret, typename = void>
struct has_size_returning : std::false_type {};

template <typename T>
struct has_size_returning<T, std::size_t, void_t<
    decltype(std::declval<T>().size())>>
    : std::bool_constant<
          std::is_same_v<decltype(std::declval<T>().size()), std::size_t>> {};

template <typename T>
inline constexpr bool has_size_returning_size_t_v =
    has_size_returning<T, std::size_t>::value;

// ============================================================================
// 8. 类型特征组合
// ============================================================================

/**
 * @brief 检测类型是否为类容器类型
 */
template <typename T>
inline constexpr bool is_container_like_v =
    has_size_v<T> && has_begin_end_v<T> && has_value_type_v<T>;

/**
 * @brief 检测类型是否为动态容器（支持 push_back）
 */
template <typename T>
inline constexpr bool is_dynamic_container_v =
    is_container_like_v<T> && has_push_back_v<T, typename T::value_type>;

/**
 * @brief 检测类型是否为字符串类型
 */
template <typename T>
struct is_string_like : std::false_type {};

template <>
struct is_string_like<std::string> : std::true_type {};

template <typename T>
inline constexpr bool is_string_like_v = is_string_like<T>::value;

}  // namespace tmp
