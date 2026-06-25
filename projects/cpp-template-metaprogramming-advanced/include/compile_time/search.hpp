#pragma once
/**
 * @file search.hpp
 * @brief 编译期查找算法
 *
 * 实现编译期查找算法：
 *   - 线性查找
 *   - 二分查找
 *   - 查找所有匹配项
 */

#include "sort.hpp"
#include <cstddef>
#include <type_traits>
#include <limits>

namespace tmp {

// ============================================================================
// 编译期线性查找
// ============================================================================

namespace detail {

template <typename List, auto Value, std::size_t Index>
struct linear_search_impl;

template <typename T, T Value, std::size_t Index>
struct linear_search_impl<value_list<T>, Value, Index> {
    static constexpr std::size_t value = std::numeric_limits<std::size_t>::max();
    static constexpr bool found = false;
};

template <typename T, T Value, T Head, T... Tail, std::size_t Index>
struct linear_search_impl<value_list<T, Head, Tail...>, Value, Index> {
    using rest = linear_search_impl<value_list<T, Tail...>, Value, Index + 1>;
    static constexpr bool found_here = (Head == Value);
    static constexpr bool found = found_here || rest::found;
    static constexpr std::size_t value =
        found_here ? Index : rest::value;
};

}  // namespace detail

/**
 * @brief 编译期线性查找
 * @return 找到的索引，未找到返回 std::numeric_limits<size_t>::max()
 */
template <typename T, T... Values, T Value>
constexpr std::size_t linear_search(value_list<T, Values...>,
                                     std::integral_constant<T, Value>) {
    return detail::linear_search_impl<value_list<T, Values...>, Value, 0>::value;
}

/// @brief 检查值是否在列表中
template <typename List, typename List::value_type Value>
inline constexpr bool value_contains =
    detail::linear_search_impl<List, Value, 0>::found;

// ============================================================================
// 编译期二分查找（需要已排序序列）
// ============================================================================

namespace detail {

template <typename List, auto Value, std::size_t Low, std::size_t High>
struct binary_search_impl;

// 基本情况: Low >= High，未找到
template <typename T, T Value, std::size_t Low, std::size_t High>
struct binary_search_impl<value_list<T>, Value, Low, High> {
    static constexpr std::size_t value = std::numeric_limits<std::size_t>::max();
    static constexpr bool found = false;
};

template <typename T, T Value, T... Values, std::size_t Low, std::size_t High>
struct binary_search_impl<value_list<T, Values...>, Value, Low, High> {
    static constexpr std::size_t Mid = Low + (High - Low) / 2;
    static constexpr T mid_val = value_at_impl<value_list<T, Values...>, Mid>::value;

    // 递归实现
    using lower_search = std::conditional_t<
        (mid_val < Value),
        binary_search_impl<value_list<T, Values...>, Value, Mid + 1, High>,
        binary_search_impl<value_list<T, Values...>, Value, Low, Mid>>;

    static constexpr bool found = (mid_val == Value) || lower_search::found;
    static constexpr std::size_t value =
        (mid_val == Value) ? Mid : lower_search::value;
};

}  // namespace detail

/**
 * @brief 编译期二分查找（序列必须已排序）
 */
template <typename T, T... Values, T Value>
constexpr std::size_t binary_search(value_list<T, Values...>,
                                     std::integral_constant<T, Value>) {
    return detail::binary_search_impl<
        value_list<T, Values...>, Value, 0, sizeof...(Values)>::value;
}

// ============================================================================
// 查找所有匹配
// ============================================================================

namespace detail {

template <typename List, auto Value, std::size_t Index>
struct find_all_impl;

template <typename T, T Value, std::size_t Index>
struct find_all_impl<value_list<T>, Value, Index> {
    using type = value_list<std::size_t>;
};

template <typename T, T Value, T Head, T... Tail, std::size_t Index>
struct find_all_impl<value_list<T, Head, Tail...>, Value, Index> {
    using rest_indices = typename find_all_impl<
        value_list<T, Tail...>, Value, Index + 1>::type;

    using type = std::conditional_t<
        (Head == Value),
        typename prepend_value_impl<std::size_t, Index, rest_indices>::type,
        rest_indices>;
};

}  // namespace detail

/**
 * @brief 查找所有匹配的索引
 */
template <typename T, T Value, T... Values>
using find_all_indices = typename detail::find_all_impl<
    value_list<T, Values...>, Value, 0>::type;

// ============================================================================
// 编译期统计
// ============================================================================

/**
 * @brief 统计值在序列中出现的次数
 */
template <typename T, T Value, typename List>
struct count_value_impl;

template <typename T, T Value>
struct count_value_impl<T, Value, value_list<T>>
    : std::integral_constant<std::size_t, 0> {};

template <typename T, T Value, T Head, T... Tail>
struct count_value_impl<T, Value, value_list<T, Head, Tail...>>
    : std::integral_constant<
          std::size_t,
          ((Head == Value) ? 1 : 0) +
              count_value_impl<T, Value, value_list<T, Tail...>>::value> {};

template <typename T, T Value, typename List>
inline constexpr std::size_t count_value = count_value_impl<T, Value, List>::value;

// ============================================================================
// 编译期查找最大/最小值索引
// ============================================================================

template <typename List>
struct max_index_impl;

template <typename T, T V>
struct max_index_impl<value_list<T, V>> {
    static constexpr std::size_t value = 0;
};

template <typename T, T Head, T... Tail>
struct max_index_impl<value_list<T, Head, Tail...>> {
    using rest = max_index_impl<value_list<T, Tail...>>;
    static constexpr T rest_max =
        value_at_impl<value_list<T, Tail...>, rest::value>::value;
    static constexpr std::size_t value =
        (Head >= rest_max) ? 0 : (1 + rest::value);
};

template <typename List>
inline constexpr std::size_t max_index = max_index_impl<List>::value;

template <typename List>
struct min_index_impl;

template <typename T, T V>
struct min_index_impl<value_list<T, V>> {
    static constexpr std::size_t value = 0;
};

template <typename T, T Head, T... Tail>
struct min_index_impl<value_list<T, Head, Tail...>> {
    using rest = min_index_impl<value_list<T, Tail...>>;
    static constexpr T rest_min =
        value_at_impl<value_list<T, Tail...>, rest::value>::value;
    static constexpr std::size_t value =
        (Head <= rest_min) ? 0 : (1 + rest::value);
};

template <typename List>
inline constexpr std::size_t min_index = min_index_impl<List>::value;

}  // namespace tmp
