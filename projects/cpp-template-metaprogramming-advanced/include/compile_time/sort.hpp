#pragma once
/**
 * @file sort.hpp
 * @brief 编译期排序算法
 *
 * 实现多种编译期排序算法，所有排序在编译期完成：
 *   - 编译期冒泡排序
 *   - 编译期选择排序
 *   - 编译期插入排序
 *
 * 使用整数序列表示，排序结果在编译期确定。
 */

#include <cstddef>
#include <type_traits>
#include <array>
#include <limits>

namespace tmp {

// ============================================================================
// 整数序列 (Integer Sequence) - C++14 标准库已有，这里提供扩展
// ============================================================================

using std::index_sequence;
using std::integer_sequence;
using std::make_index_sequence;
using std::make_integer_sequence;

// ============================================================================
// 编译期值列表
// ============================================================================

/**
 * @brief 编译期值列表 - 存储一组编译期常量
 * @tparam T 值类型
 * @tparam Values 值列表
 */
template <typename T, T... Values>
struct value_list {
    using value_type = T;
    static constexpr std::size_t size = sizeof...(Values);
    static constexpr bool empty = (size == 0);
};

// ============================================================================
// 辅助工具（必须在排序算法之前定义）
// ============================================================================

namespace detail {

/// @brief 在值列表头部添加值
template <typename T, T V, typename List>
struct prepend_value_impl;

template <typename T, T V, T... Values>
struct prepend_value_impl<T, V, value_list<T, Values...>> {
    using type = value_list<T, V, Values...>;
};

template <typename T, T V, typename List>
using prepend_value = typename prepend_value_impl<T, V, List>::type;

/// @brief 从值列表中提取尾部（去掉第一个元素）
template <typename List>
struct extract_tail_impl;

template <typename T, T Head, T... Tail>
struct extract_tail_impl<value_list<T, Head, Tail...>> {
    using type = value_list<T, Tail...>;
};

template <typename List>
using extract_tail = typename extract_tail_impl<List>::type;

/// @brief 根据是否交换来构造结果
template <bool Swapped, typename T, T First, T Second, typename Rest>
struct prepend_bubbled_impl;

template <typename T, T First, T Second, T... Rest>
struct prepend_bubbled_impl<true, T, First, Second, value_list<T, Rest...>> {
    using type = value_list<T, Second, First, Rest...>;
};

template <typename T, T First, T Second, T... Rest>
struct prepend_bubbled_impl<false, T, First, Second, value_list<T, Rest...>> {
    using type = value_list<T, First, Second, Rest...>;
};

template <bool Swapped, typename T, T First, T Second, typename Rest>
using prepend_bubbled = typename prepend_bubbled_impl<Swapped, T, First, Second, Rest>::type;

/// @brief 移除指定索引的元素
template <typename List, std::size_t N>
struct remove_at_impl;

template <typename T, T Head, T... Tail>
struct remove_at_impl<value_list<T, Head, Tail...>, 0> {
    using type = value_list<T, Tail...>;
};

template <typename T, T Head, T... Tail, std::size_t N>
struct remove_at_impl<value_list<T, Head, Tail...>, N> {
    using rest = typename remove_at_impl<value_list<T, Tail...>, N - 1>::type;
    using type = prepend_value<T, Head, rest>;
};

template <typename List, std::size_t N>
using remove_at = typename remove_at_impl<List, N>::type;

}  // namespace detail

// ============================================================================
// 获取值列表中指定索引的值
// ============================================================================

template <typename List, std::size_t N>
struct value_at_impl;

template <typename T, T Head, T... Tail>
struct value_at_impl<value_list<T, Head, Tail...>, 0> {
    static constexpr T value = Head;
};

template <typename T, T Head, T... Tail, std::size_t N>
struct value_at_impl<value_list<T, Head, Tail...>, N> {
    static constexpr T value =
        value_at_impl<value_list<T, Tail...>, N - 1>::value;
};

template <typename List, std::size_t N>
inline constexpr auto value_at = value_at_impl<List, N>::value;

// ============================================================================
// 编译期冒泡排序
// ============================================================================

namespace detail {

// 冒泡排序的单趟操作
template <typename List>
struct bubble_pass;

// 空列表
template <typename T>
struct bubble_pass<value_list<T>> {
    using type = value_list<T>;
};

// 单元素列表
template <typename T, T V>
struct bubble_pass<value_list<T, V>> {
    using type = value_list<T, V>;
};

// 两个元素
template <typename T, T First, T Second>
struct bubble_pass<value_list<T, First, Second>> {
    using type = std::conditional_t<
        (First > Second),
        value_list<T, Second, First>,
        value_list<T, First, Second>>;
};

// 三个及以上元素
template <typename T, T First, T Second, T... Rest>
struct bubble_pass<value_list<T, First, Second, Rest...>> {
    // 先对剩余部分做冒泡
    using rest_pass = typename bubble_pass<value_list<T, Second, Rest...>>::type;
    // 获取剩余部分的第一个元素
    static constexpr T rest_first = value_at_impl<rest_pass, 0>::value;
    // 比较并交换
    static constexpr bool swapped = (First > rest_first);
    // 构造结果
    using type = prepend_bubbled<swapped, T, First, rest_first,
                                  detail::extract_tail<rest_pass>>;
};

// 多趟冒泡
template <typename List, std::size_t N>
struct bubble_sort_impl {
    using passed = typename bubble_pass<List>::type;
    using type = typename bubble_sort_impl<passed, N - 1>::type;
};

template <typename List>
struct bubble_sort_impl<List, 0> {
    using type = List;
};

}  // namespace detail

/**
 * @brief 编译期冒泡排序
 * @tparam T 值类型
 * @tparam Values 待排序的值
 */
template <typename T, T... Values>
using bubble_sort = typename detail::bubble_sort_impl<
    value_list<T, Values...>, sizeof...(Values)>::type;

// ============================================================================
// 编译期选择排序
// ============================================================================

namespace detail {

// 查找最小值的索引
template <typename List, std::size_t Start>
struct find_min_index;

template <typename T, T Head, T... Tail, std::size_t Start>
struct find_min_index<value_list<T, Head, Tail...>, Start> {
    using rest = find_min_index<value_list<T, Tail...>, Start + 1>;
    static constexpr std::size_t rest_min_idx = rest::value;
    static constexpr T rest_min_val = value_at_impl<
        value_list<T, Tail...>, rest_min_idx - Start - 1>::value;

    static constexpr std::size_t value =
        (Head <= rest_min_val) ? Start : rest_min_idx;
};

template <typename T, T V, std::size_t Start>
struct find_min_index<value_list<T, V>, Start> {
    static constexpr std::size_t value = Start;
};

// 选择排序主体
template <typename List>
struct selection_sort_impl;

template <typename T>
struct selection_sort_impl<value_list<T>> {
    using type = value_list<T>;
};

template <typename T, T V>
struct selection_sort_impl<value_list<T, V>> {
    using type = value_list<T, V>;
};

template <typename T, T Head, T... Tail>
struct selection_sort_impl<value_list<T, Head, Tail...>> {
    using list = value_list<T, Head, Tail...>;
    static constexpr std::size_t min_idx = find_min_index<list, 0>::value;
    static constexpr T min_val = value_at_impl<list, min_idx>::value;

    using remaining = remove_at<list, min_idx>;
    using sorted_rest = typename selection_sort_impl<remaining>::type;
    using type = detail::prepend_value<T, min_val, sorted_rest>;
};

}  // namespace detail

/**
 * @brief 编译期选择排序
 */
template <typename T, T... Values>
using selection_sort = typename detail::selection_sort_impl<
    value_list<T, Values...>>::type;

// ============================================================================
// 编译期插入排序
// ============================================================================

namespace detail {

// 在已排序序列中插入一个值
template <typename T, T Value, typename List>
struct sorted_insert_impl;

template <typename T, T Value>
struct sorted_insert_impl<T, Value, value_list<T>> {
    using type = value_list<T, Value>;
};

template <typename T, T Value, T Head>
struct sorted_insert_impl<T, Value, value_list<T, Head>> {
    using type = std::conditional_t<
        (Value <= Head),
        value_list<T, Value, Head>,
        value_list<T, Head, Value>>;
};

template <typename T, T Value, T Head, T... Tail>
struct sorted_insert_impl<T, Value, value_list<T, Head, Tail...>> {
    using type = std::conditional_t<
        (Value <= Head),
        value_list<T, Value, Head, Tail...>,
        prepend_value<T, Head,
            typename sorted_insert_impl<T, Value, value_list<T, Tail...>>::type>>;
};

template <typename T, T Value, typename List>
using sorted_insert = typename sorted_insert_impl<T, Value, List>::type;

// 插入排序主体
template <typename List>
struct insertion_sort_impl;

template <typename T>
struct insertion_sort_impl<value_list<T>> {
    using type = value_list<T>;
};

template <typename T, T V>
struct insertion_sort_impl<value_list<T, V>> {
    using type = value_list<T, V>;
};

template <typename T, T Head, T... Tail>
struct insertion_sort_impl<value_list<T, Head, Tail...>> {
    using sorted_rest = typename insertion_sort_impl<value_list<T, Tail...>>::type;
    using type = sorted_insert<T, Head, sorted_rest>;
};

}  // namespace detail

/**
 * @brief 编译期插入排序
 */
template <typename T, T... Values>
using insertion_sort = typename detail::insertion_sort_impl<
    value_list<T, Values...>>::type;

// ============================================================================
// 编译期排序验证
// ============================================================================

/// @brief 验证值列表是否已排序
template <typename List>
struct is_sorted_impl;

template <typename T>
struct is_sorted_impl<value_list<T>> : std::true_type {};

template <typename T, T V>
struct is_sorted_impl<value_list<T, V>> : std::true_type {};

template <typename T, T First, T Second, T... Rest>
struct is_sorted_impl<value_list<T, First, Second, Rest...>>
    : std::conditional_t<
          (First <= Second),
          is_sorted_impl<value_list<T, Second, Rest...>>,
          std::false_type> {};

template <typename List>
inline constexpr bool is_sorted = is_sorted_impl<List>::value;

// ============================================================================
// 辅助: 从整数序列创建值列表
// ============================================================================

template <typename T, T... Values>
constexpr value_list<T, Values...> make_value_list(integer_sequence<T, Values...>) {
    return {};
}

// ============================================================================
// 编译期最大值/最小值
// ============================================================================

template <typename List>
struct max_value_impl;

template <typename T, T V>
struct max_value_impl<value_list<T, V>> {
    static constexpr T value = V;
};

template <typename T, T Head, T... Tail>
struct max_value_impl<value_list<T, Head, Tail...>> {
    static constexpr T rest_max =
        max_value_impl<value_list<T, Tail...>>::value;
    static constexpr T value = (Head > rest_max) ? Head : rest_max;
};

template <typename List>
inline constexpr auto max_value = max_value_impl<List>::value;

template <typename List>
struct min_value_impl;

template <typename T, T V>
struct min_value_impl<value_list<T, V>> {
    static constexpr T value = V;
};

template <typename T, T Head, T... Tail>
struct min_value_impl<value_list<T, Head, Tail...>> {
    static constexpr T rest_min =
        min_value_impl<value_list<T, Tail...>>::value;
    static constexpr T value = (Head < rest_min) ? Head : rest_min;
};

template <typename List>
inline constexpr auto min_value = min_value_impl<List>::value;

// ============================================================================
// 编译期求和
// ============================================================================

template <typename List>
struct sum_impl;

template <typename T>
struct sum_impl<value_list<T>> {
    static constexpr T value = T{0};
};

template <typename T, T V>
struct sum_impl<value_list<T, V>> {
    static constexpr T value = V;
};

template <typename T, T Head, T... Tail>
struct sum_impl<value_list<T, Head, Tail...>> {
    static constexpr T value = Head + sum_impl<value_list<T, Tail...>>::value;
};

template <typename List>
inline constexpr auto sum = sum_impl<List>::value;

}  // namespace tmp
