#pragma once
/**
 * @file map_filter_reduce.hpp
 * @brief 编译期 Map / Filter / Reduce 函数式编程操作
 *
 * 对值列表进行函数式编程风格的操作：
 *   - map: 对每个元素应用变换
 *   - filter: 按条件过滤元素
 *   - reduce: 将元素归约为单个值
 *   - zip: 将两个列表配对
 *   - flatten: 展平嵌套列表
 */

#include "sort.hpp"
#include <cstddef>
#include <type_traits>
#include <array>

namespace tmp {

// ============================================================================
// 编译期 Map
// ============================================================================

namespace detail {

template <typename List, template <typename T, T> class F>
struct value_map_impl;

template <typename T, T... Values, template <typename, T> class F>
struct value_map_impl<value_list<T, Values...>, F> {
    using type = value_list<T, F<T, Values>::value...>;
};

}  // namespace detail

/**
 * @brief 编译期 Map 操作
 * 对值列表中的每个值应用变换函数 F
 *
 * 使用方法:
 *   template <typename T, T V> struct double_it {
 *       static constexpr T value = V * 2;
 *   };
 *   using result = value_map<my_list, double_it>;
 */
template <typename List, template <typename T, T> class F>
using value_map = typename detail::value_map_impl<List, F>::type;

// ============================================================================
// 编译期 Filter
// ============================================================================

namespace detail {

template <typename List, template <typename T, T> class Pred>
struct value_filter_impl;

template <typename T, template <typename, T> class Pred>
struct value_filter_impl<value_list<T>, Pred> {
    using type = value_list<T>;
};

template <typename T, T Head, T... Tail, template <typename, T> class Pred>
struct value_filter_impl<value_list<T, Head, Tail...>, Pred> {
    using rest = typename value_filter_impl<value_list<T, Tail...>, Pred>::type;
    using type = std::conditional_t<
        Pred<T, Head>::value,
        typename prepend_value_impl<T, Head, rest>::type,
        rest>;
};

}  // namespace detail

/**
 * @brief 编译期 Filter 操作
 * 过滤掉不满足谓词 Pred 的元素
 *
 * 使用方法:
 *   template <typename T, T V> struct is_even {
 *       static constexpr bool value = (V % 2 == 0);
 *   };
 *   using evens = value_filter<my_list, is_even>;
 */
template <typename List, template <typename T, T> class Pred>
using value_filter = typename detail::value_filter_impl<List, Pred>::type;

// ============================================================================
// 编译期 Reduce
// ============================================================================

namespace detail {

template <typename T, T Init, typename List, template <typename, T, T> class F>
struct value_reduce_impl;

template <typename T, T Init, template <typename, T, T> class F>
struct value_reduce_impl<T, Init, value_list<T>, F> {
    static constexpr T value = Init;
};

template <typename T, T Init, T Head, T... Tail, template <typename, T, T> class F>
struct value_reduce_impl<T, Init, value_list<T, Head, Tail...>, F> {
    static constexpr T new_acc = F<T, Init, Head>::value;
    static constexpr T value =
        value_reduce_impl<T, new_acc, value_list<T, Tail...>, F>::value;
};

}  // namespace detail

/**
 * @brief 编译期 Reduce 操作（左折叠）
 *
 * 使用方法:
 *   template <typename T, T Acc, T V> struct add {
 *       static constexpr T value = Acc + V;
 *   };
 *   constexpr auto total = value_reduce<int, value_list<int, 1,2,3>, add, 0>;
 */
template <typename T, typename List, template <typename, T, T> class F, T Init>
inline constexpr T value_reduce =
    detail::value_reduce_impl<T, Init, List, F>::value;

// ============================================================================
// 编译期 Zip
// ============================================================================

namespace detail {

template <typename List1, typename List2>
struct zip_impl;

template <typename T, T... Vs, T... Us>
struct zip_impl<value_list<T, Vs...>, value_list<T, Us...>> {
    // 创建一对对的值
    // 简化实现：将两个列表的值配对存储
    static constexpr std::size_t size = sizeof...(Vs);
    static_assert(sizeof...(Us) == size, "Lists must have same size for zip");

    // 生成配对数组
    static constexpr auto make_pairs() {
        T arr1[] = {Vs...};
        T arr2[] = {Us...};
        struct pair_t { T first; T second; };
        std::array<pair_t, size> result{};
        for (std::size_t i = 0; i < size; ++i) {
            result[i] = {arr1[i], arr2[i]};
        }
        return result;
    }

    static constexpr auto pairs = make_pairs();
};

}  // namespace detail

/**
 * @brief 编译期 Zip 操作
 * 将两个等长的值列表配对
 */
template <typename List1, typename List2>
using value_zip = detail::zip_impl<List1, List2>;

// ============================================================================
// 编译期 Flatten
// ============================================================================

/**
 * @brief 编译期 Flatten - 将多个值列表合并为一个
 */
template <typename... Lists>
struct flatten_impl;

template <typename T>
struct flatten_impl<value_list<T>> {
    using type = value_list<T>;
};

template <typename T, T... Values>
struct flatten_impl<value_list<T, Values...>> {
    using type = value_list<T, Values...>;
};

template <typename T, T... Vs, T... Us, typename... Rest>
struct flatten_impl<value_list<T, Vs...>, value_list<T, Us...>, Rest...> {
    using combined = value_list<T, Vs..., Us...>;
    using type = typename flatten_impl<combined, Rest...>::type;
};

template <typename... Lists>
using value_flatten = typename flatten_impl<Lists...>::type;

// ============================================================================
// 编译期 Take / Drop
// ============================================================================

namespace detail {

template <typename List, std::size_t N>
struct take_impl;

template <typename T, std::size_t N>
struct take_impl<value_list<T>, N> {
    using type = value_list<T>;
};

template <typename T, T Head, T... Tail>
struct take_impl<value_list<T, Head, Tail...>, 0> {
    using type = value_list<T>;
};

template <typename T, T Head, T... Tail, std::size_t N>
struct take_impl<value_list<T, Head, Tail...>, N> {
    using rest = typename take_impl<value_list<T, Tail...>, N - 1>::type;
    using type = typename prepend_value_impl<T, Head, rest>::type;
};

template <typename List, std::size_t N>
struct drop_impl;

template <typename T, std::size_t N>
struct drop_impl<value_list<T>, N> {
    using type = value_list<T>;
};

template <typename T, T Head, T... Tail>
struct drop_impl<value_list<T, Head, Tail...>, 0> {
    using type = value_list<T, Head, Tail...>;
};

template <typename T, T Head, T... Tail, std::size_t N>
struct drop_impl<value_list<T, Head, Tail...>, N> {
    using type = typename drop_impl<value_list<T, Tail...>, N - 1>::type;
};

}  // namespace detail

/// @brief 取前 N 个元素
template <typename List, std::size_t N>
using value_take = typename detail::take_impl<List, N>::type;

/// @brief 丢弃前 N 个元素
template <typename List, std::size_t N>
using value_drop = typename detail::drop_impl<List, N>::type;

// ============================================================================
// 编译期 for_each (编译期展开)
// ============================================================================

/**
 * @brief 编译期 for_each - 对值列表中的每个值执行操作
 * 使用折叠表达式实现
 */
template <typename T, T... Values, typename F>
constexpr void for_each_value(value_list<T, Values...>, F&& func) {
    (func.template operator()<Values>(), ...);
}

// ============================================================================
// 编译期 accumulate（带初始值的累加）
// ============================================================================

/**
 * @brief 编译期 accumulate
 * 使用折叠表达式直接计算
 */
template <typename T, T... Values>
constexpr T accumulate_values(value_list<T, Values...>, T init = T{0}) {
    return (init + ... + Values);
}

/**
 * @brief 编译期 product（乘积）
 */
template <typename T, T... Values>
constexpr T product_values(value_list<T, Values...>) {
    return (Values * ...);
}

}  // namespace tmp
