#pragma once
/**
 * @file type_conversion.hpp
 * @brief 类型转换链与类型转换工具
 *
 * 提供编译期类型转换功能：
 *   - 转换链 (Conversion Chain)
 *   - 类型提升 (Type Promotion)
 *   - 类型擦除辅助
 *   - 编译期类型映射
 */

#include "type_list.hpp"
#include "type_counting.hpp"
#include <type_traits>
#include <cstdint>

namespace tmp {

// ============================================================================
// 转换链 - 检查类型之间是否存在隐式转换路径
// ============================================================================

/**
 * @brief 检查类型 From 是否可以转换为类型 To
 * 使用 SFINAE 检测隐式转换和显式转换
 */
template <typename From, typename To, typename = void>
struct is_convertible : std::is_convertible<From, To> {};

/// @brief 便捷变量模板
template <typename From, typename To>
inline constexpr bool is_convertible_v = is_convertible<From, To>::value;

/**
 * @brief 检查转换链: From -> Intermediate -> To
 * 验证是否存在通过中间类型的转换路径
 */
template <typename From, typename Intermediate, typename To>
struct conversion_chain {
    static constexpr bool value =
        is_convertible_v<From, Intermediate> &&
        is_convertible_v<Intermediate, To>;
};

template <typename From, typename Intermediate, typename To>
inline constexpr bool conversion_chain_v =
    conversion_chain<From, Intermediate, To>::value;

// ============================================================================
// 类型提升 (Type Promotion)
// ============================================================================

/**
 * @brief 数值类型提升规则
 * 模拟 C++ 的隐式类型提升规则
 */
template <typename T>
struct promote {
    using type = T;
};

// 整数提升规则
template <>
struct promote<char> {
    using type = int;
};

template <>
struct promote<signed char> {
    using type = int;
};

template <>
struct promote<unsigned char> {
    using type = unsigned int;
};

template <>
struct promote<short> {
    using type = int;
};

template <>
struct promote<unsigned short> {
    using type = unsigned int;
};

// bool 提升为 int
template <>
struct promote<bool> {
    using type = int;
};

/// @brief 便捷别名
template <typename T>
using promote_t = typename promote<T>::type;

/**
 * @brief 两个类型的公共提升类型
 * 模拟算术运算中的常用算术转换
 */
template <typename T1, typename T2>
struct common_promoted {
    using type = decltype(std::declval<promote_t<T1>>() +
                          std::declval<promote_t<T2>>());
};

template <typename T1, typename T2>
using common_promoted_t = typename common_promoted<T1, T2>::type;

// ============================================================================
// 类型映射表 (Type Map)
// ============================================================================

/**
 * @brief 编译期类型映射 - 将一个类型映射到另一个类型
 * 使用特化来定义映射规则
 */
template <typename From>
struct type_map {
    using type = From;  // 默认: 恒等映射
};

/// @brief 便捷别名
template <typename From>
using type_map_t = typename type_map<From>::type;

// ============================================================================
// 类型包装器 (Type Wrapper)
// ============================================================================

/**
 * @brief 类型包装器 - 将值类型包装为引用类型，引用类型保持不变
 */
template <typename T>
struct wrap_reference {
    using type = T;
};

template <typename T>
struct wrap_reference<T&> {
    using type = T&;
};

template <typename T>
struct wrap_reference<T&&> {
    using type = T&&;
};

template <typename T>
using wrap_reference_t = typename wrap_reference<T>::type;

/**
 * @brief 移除所有修饰符（指针、引用、cv限定符）
 */
template <typename T>
struct strip_all {
    using type = std::remove_cv_t<
        std::remove_reference_t<
            std::remove_pointer_t<T>>>;
};

template <typename T>
using strip_all_t = typename strip_all<T>::type;

// ============================================================================
// 类型集合操作
// ============================================================================

/**
 * @brief 两个类型列表的并集（去重）
 */
template <typename List1, typename List2>
struct type_union_impl {
    using combined = concat<List1, List2>;
    using type = unique<combined>;
};

template <typename List1, typename List2>
using type_union = typename type_union_impl<List1, List2>::type;

/**
 * @brief 两个类型列表的交集
 */
template <typename List1, typename List2>
struct type_intersection_impl;

template <typename List2>
struct type_intersection_impl<type_list<>, List2> {
    using type = type_list<>;
};

template <typename Head, typename... Tail, typename List2>
struct type_intersection_impl<type_list<Head, Tail...>, List2> {
    using rest = typename type_intersection_impl<type_list<Tail...>, List2>::type;
    using type = std::conditional_t<
        contains<List2, Head>,
        typename push_front_impl<rest, Head>::type,
        rest>;
};

template <typename List1, typename List2>
using type_intersection = typename type_intersection_impl<List1, List2>::type;

/**
 * @brief 类型列表差集 (List1 - List2)
 */
template <typename List1, typename List2>
struct type_difference_impl;

template <typename List2>
struct type_difference_impl<type_list<>, List2> {
    using type = type_list<>;
};

template <typename Head, typename... Tail, typename List2>
struct type_difference_impl<type_list<Head, Tail...>, List2> {
    using rest = typename type_difference_impl<type_list<Tail...>, List2>::type;
    using type = std::conditional_t<
        !contains<List2, Head>,
        typename push_front_impl<rest, Head>::type,
        rest>;
};

template <typename List1, typename List2>
using type_difference = typename type_difference_impl<List1, List2>::type;

// ============================================================================
// 条件类型选择
// ============================================================================

/**
 * @brief 根据条件选择类型列表中的类型
 */
template <bool Cond, typename TrueType, typename FalseType>
using select_type = std::conditional_t<Cond, TrueType, FalseType>;

/**
 * @brief 从类型列表中选择第一个满足条件的类型
 */
template <typename List, template <typename> class Pred>
struct find_first_impl;

template <template <typename> class Pred>
struct find_first_impl<type_list<>, Pred> {
    // 没有找到满足条件的类型
    static_assert(sizeof(Pred<void>) == 0,
                  "No type satisfying the predicate was found");
};

template <template <typename> class Pred, typename Head, typename... Tail>
struct find_first_impl<type_list<Head, Tail...>, Pred> {
    using type = std::conditional_t<
        Pred<Head>::value,
        Head,
        typename find_first_impl<type_list<Tail...>, Pred>::type>;
};

/// @brief 查找第一个满足谓词的类型
template <typename List, template <typename> class Pred>
using find_first = typename find_first_impl<List, Pred>::type;

// ============================================================================
// 编译期类型断言工具
// ============================================================================

/// @brief 编译期断言两个类型相同
template <typename T, typename U>
struct assert_same {
    static_assert(std::is_same_v<T, U>, "Types are not the same");
    static constexpr bool value = true;
};

template <typename T, typename U>
inline constexpr bool assert_same_v = assert_same<T, U>::value;

/// @brief 编译期断言类型可以转换
template <typename From, typename To>
struct assert_convertible {
    static_assert(is_convertible_v<From, To>,
                  "Types are not convertible");
    static constexpr bool value = true;
};

template <typename From, typename To>
inline constexpr bool assert_convertible_v =
    assert_convertible<From, To>::value;

}  // namespace tmp
