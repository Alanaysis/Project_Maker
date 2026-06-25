#pragma once
/**
 * @file type_counting.hpp
 * @brief 类型计数与类型统计工具
 *
 * 提供编译期类型统计功能：
 *   - count: 统计某类型在列表中出现的次数
 *   - count_if: 统计满足谓词的类型数量
 *   - unique: 去重，保留唯一类型
 *   - duplicate: 查找重复类型
 */

#include "type_list.hpp"
#include <cstddef>
#include <type_traits>

namespace tmp {

// ============================================================================
// count - 统计类型出现次数
// ============================================================================

template <typename List, typename T>
struct count_impl;

/// @brief 统计类型T在列表中出现的次数
template <typename List, typename T>
inline constexpr std::size_t count = count_impl<List, T>::value;

template <typename T>
struct count_impl<type_list<>, T> : std::integral_constant<std::size_t, 0> {};

template <typename T, typename Head, typename... Tail>
struct count_impl<type_list<Head, Tail...>, T>
    : std::integral_constant<
          std::size_t,
          (std::is_same_v<Head, T> ? 1 : 0) +
              count_impl<type_list<Tail...>, T>::value> {};

// ============================================================================
// count_if - 按谓词统计
// ============================================================================

template <typename List, template <typename> class Pred>
struct count_if_impl;

/// @brief 统计满足谓词的类型数量
template <typename List, template <typename> class Pred>
inline constexpr std::size_t count_if = count_if_impl<List, Pred>::value;

template <template <typename> class Pred>
struct count_if_impl<type_list<>, Pred>
    : std::integral_constant<std::size_t, 0> {};

template <template <typename> class Pred, typename Head, typename... Tail>
struct count_if_impl<type_list<Head, Tail...>, Pred>
    : std::integral_constant<
          std::size_t,
          (Pred<Head>::value ? 1 : 0) +
              count_if_impl<type_list<Tail...>, Pred>::value> {};

// ============================================================================
// unique - 去重
// ============================================================================

template <typename List>
struct unique_impl;

/// @brief 去除类型列表中的重复类型（保留第一次出现的顺序）
template <typename List>
using unique = typename unique_impl<List>::type;

template <>
struct unique_impl<type_list<>> {
    using type = type_list<>;
};

template <typename Head, typename... Tail>
struct unique_impl<type_list<Head, Tail...>> {
    using rest_unique = typename unique_impl<type_list<Tail...>>::type;
    using type = std::conditional_t<
        contains<rest_unique, Head>,
        rest_unique,
        typename push_front_impl<rest_unique, Head>::type>;
};

// ============================================================================
// has_duplicates - 检查是否有重复
// ============================================================================

template <typename List>
struct has_duplicates_impl;

/// @brief 检查类型列表中是否有重复类型
template <typename List>
inline constexpr bool has_duplicates = has_duplicates_impl<List>::value;

template <>
struct has_duplicates_impl<type_list<>> : std::false_type {};

template <typename Head, typename... Tail>
struct has_duplicates_impl<type_list<Head, Tail...>>
    : std::conditional_t<
          contains<type_list<Tail...>, Head>,
          std::true_type,
          has_duplicates_impl<type_list<Tail...>>> {};

// ============================================================================
// all_same - 检查是否所有类型都相同
// ============================================================================

template <typename List>
struct all_same_impl;

/// @brief 检查类型列表中所有类型是否相同
template <typename List>
inline constexpr bool all_same = all_same_impl<List>::value;

template <>
struct all_same_impl<type_list<>> : std::true_type {};

template <typename T>
struct all_same_impl<type_list<T>> : std::true_type {};

template <typename Head, typename Head2, typename... Tail>
struct all_same_impl<type_list<Head, Head2, Tail...>>
    : std::conditional_t<
          std::is_same_v<Head, Head2>,
          all_same_impl<type_list<Head2, Tail...>>,
          std::false_type> {};

// ============================================================================
// distinct_count - 不同类型的数量
// ============================================================================

/// @brief 统计类型列表中不同类型的数量
template <typename List>
inline constexpr std::size_t distinct_count = unique<List>::size;

// ============================================================================
// max_type / min_type - 按大小获取最大/最小类型
// ============================================================================

template <typename List>
struct max_sizeof_impl;

/// @brief 获取类型列表中 sizeof 最大的类型大小
template <typename List>
inline constexpr std::size_t max_sizeof = max_sizeof_impl<List>::value;

template <typename T>
struct max_sizeof_impl<type_list<T>>
    : std::integral_constant<std::size_t, sizeof(T)> {};

template <typename Head, typename... Tail>
struct max_sizeof_impl<type_list<Head, Tail...>>
    : std::integral_constant<
          std::size_t,
          (sizeof(Head) > max_sizeof_impl<type_list<Tail...>>::value
               ? sizeof(Head)
               : max_sizeof_impl<type_list<Tail...>>::value)> {};

template <typename List>
struct min_sizeof_impl;

/// @brief 获取类型列表中 sizeof 最小的类型大小
template <typename List>
inline constexpr std::size_t min_sizeof = min_sizeof_impl<List>::value;

template <typename T>
struct min_sizeof_impl<type_list<T>>
    : std::integral_constant<std::size_t, sizeof(T)> {};

template <typename Head, typename... Tail>
struct min_sizeof_impl<type_list<Head, Tail...>>
    : std::integral_constant<
          std::size_t,
          (sizeof(Head) < min_sizeof_impl<type_list<Tail...>>::value
               ? sizeof(Head)
               : min_sizeof_impl<type_list<Tail...>>::value)> {};

// ============================================================================
// total_sizeof - 总大小
// ============================================================================

// plus_sizeof 辅助: 计算两个类型的 sizeof 之和
template <typename Acc, typename T>
struct plus_sizeof {
    using type = std::integral_constant<std::size_t, Acc::value + sizeof(T)>;
};

/// @brief 获取类型列表中所有类型的 sizeof 之和
template <typename List>
inline constexpr std::size_t total_sizeof = fold<List, plus_sizeof, std::integral_constant<std::size_t, 0>>::value;

}  // namespace tmp
