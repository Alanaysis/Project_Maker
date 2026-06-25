#pragma once
/**
 * @file type_list.hpp
 * @brief 类型列表 (Type List) - 模板元编程的核心数据结构
 *
 * 类型列表是模板元编程中最基础的数据结构，类似于函数式编程中的列表。
 * 所有类型操作都在编译期完成，运行时零开销。
 *
 * 核心操作：
 *   - push_front / push_back: 在头部/尾部添加类型
 *   - pop_front / pop_back: 移除头部/尾部类型
 *   - front / back: 获取头部/尾部类型
 *   - at: 按索引获取类型
 *   - size: 获取列表大小
 *   - concat: 连接两个类型列表
 *   - reverse: 反转类型列表
 *   - contains: 检查是否包含某类型
 *   - index_of: 查找类型索引
 *   - transform: 类型变换
 *   - filter: 类型过滤
 */

#include <cstddef>
#include <type_traits>

namespace tmp {

// ============================================================================
// 基础类型列表定义
// ============================================================================

/**
 * @brief 类型列表 - 模板元编程的核心数据结构
 * @tparam Ts 类型参数包
 */
template <typename... Ts>
struct type_list {
    static constexpr std::size_t size = sizeof...(Ts);
    static constexpr bool empty = (size == 0);
};

// ============================================================================
// 前置声明
// ============================================================================
template <typename List>
struct front_impl;

template <typename List>
struct back_impl;

template <typename List>
struct pop_front_impl;

template <typename List>
struct pop_back_impl;

template <typename List, typename T>
struct push_front_impl;

template <typename List, typename T>
struct push_back_impl;

template <typename List, std::size_t N>
struct at_impl;

template <typename List, typename T>
struct contains_impl;

template <typename List, typename T>
struct index_of_impl;

template <typename List>
struct reverse_impl;

template <typename List1, typename List2>
struct concat_impl;

template <typename List, template <typename> class F>
struct transform_impl;

template <typename List, template <typename> class Pred>
struct filter_impl;

template <typename List, template <typename, typename> class F, typename Init>
struct fold_impl;

// ============================================================================
// front / back - 获取首尾元素
// ============================================================================

/// @brief 获取类型列表的第一个类型
template <typename List>
using front = typename front_impl<List>::type;

/// @brief 获取类型列表的最后一个类型
template <typename List>
using back = typename back_impl<List>::type;

template <typename Head, typename... Tail>
struct front_impl<type_list<Head, Tail...>> {
    using type = Head;
};

template <typename T>
struct back_impl<type_list<T>> {
    using type = T;
};

template <typename Head, typename... Tail>
struct back_impl<type_list<Head, Tail...>> {
    using type = typename back_impl<type_list<Tail...>>::type;
};

// ============================================================================
// push_front / push_back - 添加元素
// ============================================================================

/// @brief 在类型列表头部添加类型
template <typename List, typename T>
using push_front = typename push_front_impl<List, T>::type;

/// @brief 在类型列表尾部添加类型
template <typename List, typename T>
using push_back = typename push_back_impl<List, T>::type;

template <typename T, typename... Ts>
struct push_front_impl<type_list<Ts...>, T> {
    using type = type_list<T, Ts...>;
};

template <typename T, typename... Ts>
struct push_back_impl<type_list<Ts...>, T> {
    using type = type_list<Ts..., T>;
};

// ============================================================================
// pop_front / pop_back - 移除元素
// ============================================================================

/// @brief 移除类型列表的第一个类型
template <typename List>
using pop_front = typename pop_front_impl<List>::type;

/// @brief 移除类型列表的最后一个类型
template <typename List>
using pop_back = typename pop_back_impl<List>::type;

template <typename Head, typename... Tail>
struct pop_front_impl<type_list<Head, Tail...>> {
    using type = type_list<Tail...>;
};

// pop_back 需要递归实现
template <typename... Ts>
struct pop_back_impl_helper;

template <typename Last>
struct pop_back_impl_helper<Last> {
    using type = type_list<>;
};

template <typename Head, typename... Tail>
struct pop_back_impl_helper<Head, Tail...> {
    using rest = typename pop_back_impl_helper<Tail...>::type;
    using type = typename push_front_impl<rest, Head>::type;
};

template <typename... Ts>
struct pop_back_impl<type_list<Ts...>> {
    using type = typename pop_back_impl_helper<Ts...>::type;
};

// ============================================================================
// at - 按索引访问
// ============================================================================

/// @brief 按索引获取类型列表中的类型
template <typename List, std::size_t N>
using at = typename at_impl<List, N>::type;

// 递归实现 at
template <std::size_t N, typename... Ts>
struct at_helper;

template <typename Head, typename... Tail>
struct at_helper<0, Head, Tail...> {
    using type = Head;
};

template <std::size_t N, typename Head, typename... Tail>
struct at_helper<N, Head, Tail...> {
    static_assert(N < sizeof...(Tail) + 1, "Index out of bounds");
    using type = typename at_helper<N - 1, Tail...>::type;
};

template <typename... Ts, std::size_t N>
struct at_impl<type_list<Ts...>, N> {
    using type = typename at_helper<N, Ts...>::type;
};

// ============================================================================
// contains - 包含检查
// ============================================================================

/// @brief 检查类型列表是否包含指定类型
template <typename List, typename T>
inline constexpr bool contains = contains_impl<List, T>::value;

template <typename T>
struct contains_impl<type_list<>, T> : std::false_type {};

template <typename T, typename Head, typename... Tail>
struct contains_impl<type_list<Head, Tail...>, T>
    : std::conditional_t<
          std::is_same_v<Head, T>,
          std::true_type,
          contains_impl<type_list<Tail...>, T>
      > {};

// ============================================================================
// index_of - 索引查找
// ============================================================================

/// @brief 查找类型在列表中的索引（未找到返回 size）
template <typename List, typename T>
inline constexpr std::size_t index_of = index_of_impl<List, T>::value;

template <typename T>
struct index_of_impl<type_list<>, T> {
    static constexpr std::size_t value = 0;  // 返回空列表size=0，调用者需检查
};

template <typename T, typename Head, typename... Tail>
struct index_of_impl<type_list<Head, Tail...>, T> {
    static constexpr std::size_t value =
        std::is_same_v<Head, T>
            ? 0
            : 1 + index_of_impl<type_list<Tail...>, T>::value;
};

// ============================================================================
// concat - 连接两个类型列表
// ============================================================================

/// @brief 连接两个类型列表
template <typename List1, typename List2>
using concat = typename concat_impl<List1, List2>::type;

template <typename... Ts, typename... Us>
struct concat_impl<type_list<Ts...>, type_list<Us...>> {
    using type = type_list<Ts..., Us...>;
};

// ============================================================================
// reverse - 反转
// ============================================================================

/// @brief 反转类型列表
template <typename List>
using reverse = typename reverse_impl<List>::type;

template <>
struct reverse_impl<type_list<>> {
    using type = type_list<>;
};

template <typename Head, typename... Tail>
struct reverse_impl<type_list<Head, Tail...>> {
    using rest = typename reverse_impl<type_list<Tail...>>::type;
    using type = typename push_back_impl<rest, Head>::type;
};

// ============================================================================
// transform - 类型变换
// ============================================================================

/// @brief 对类型列表中的每个类型应用变换函数
template <typename List, template <typename> class F>
using transform = typename transform_impl<List, F>::type;

template <template <typename> class F, typename... Ts>
struct transform_impl<type_list<Ts...>, F> {
    using type = type_list<typename F<Ts>::type...>;
};

// ============================================================================
// filter - 类型过滤
// ============================================================================

/// @brief 按谓词过滤类型列表
template <typename List, template <typename> class Pred>
using filter = typename filter_impl<List, Pred>::type;

template <template <typename> class Pred>
struct filter_impl<type_list<>, Pred> {
    using type = type_list<>;
};

template <template <typename> class Pred, typename Head, typename... Tail>
struct filter_impl<type_list<Head, Tail...>, Pred> {
    using rest = typename filter_impl<type_list<Tail...>, Pred>::type;
    using type = std::conditional_t<
        Pred<Head>::value,
        typename push_front_impl<rest, Head>::type,
        rest
    >;
};

// ============================================================================
// fold - 折叠/归约
// ============================================================================

/// @brief 对类型列表进行左折叠
template <typename List, template <typename, typename> class F, typename Init>
using fold = typename fold_impl<List, F, Init>::type;

template <template <typename, typename> class F, typename Init>
struct fold_impl<type_list<>, F, Init> {
    using type = Init;
};

template <template <typename, typename> class F, typename Init,
          typename Head, typename... Tail>
struct fold_impl<type_list<Head, Tail...>, F, Init> {
    using new_init = typename F<Init, Head>::type;
    using type = typename fold_impl<type_list<Tail...>, F, new_init>::type;
};

// ============================================================================
// 辅助工具
// ============================================================================

/// @brief 创建 type_list 的别名（用于 make_type_list<int, double, char> 等）
template <typename... Ts>
using make_type_list = type_list<Ts...>;

/// @brief 获取类型列表的大小
template <typename List>
inline constexpr std::size_t list_size = List::size;

/// @brief 检查类型列表是否为空
template <typename List>
inline constexpr bool list_empty = List::empty;

/// @brief 条件类型选择
template <bool Cond, typename T, typename F>
using conditional = std::conditional_t<Cond, T, F>;

}  // namespace tmp
