#pragma once
/**
 * @file tag_dispatching.hpp
 * @brief 标签分发 (Tag Dispatching)
 *
 * 标签分发是一种编译期多态技术，通过空类型标签来选择
 * 不同的函数重载实现，避免运行时分支。
 *
 * 核心思想：
 *   - 定义一组空类型作为标签
 *   - 函数通过标签参数选择实现
 *   - 编译期消除分支
 *   - 可与 SFINAE 结合使用
 *
 * 应用场景：
 *   - STL 迭代器类别
 *   - 容器的优化路径选择
 *   - 数值类型分发
 */

#include <type_traits>
#include <iostream>
#include <string>
#include <vector>
#include <list>
#include <iterator>
#include <chrono>
#include <cstring>

namespace tmp {

// ============================================================================
// 1. 基础标签定义 - 使用标准库标签
// ============================================================================

using input_iterator_tag = std::input_iterator_tag;
using forward_iterator_tag = std::forward_iterator_tag;
using bidirectional_iterator_tag = std::bidirectional_iterator_tag;
using random_access_iterator_tag = std::random_access_iterator_tag;

// contiguous_iterator_tag 在 C++20 中可用
#if __cplusplus >= 202002L
using contiguous_iterator_tag = std::contiguous_iterator_tag;
#else
struct contiguous_iterator_tag : random_access_iterator_tag {};
#endif

// ============================================================================
// 2. 迭代器特性萃取
// ============================================================================

/**
 * @brief 迭代器特性萃取 - 默认实现
 */
template <typename Iterator>
struct iterator_traits {
    using iterator_category = typename Iterator::iterator_category;
    using value_type = typename Iterator::value_type;
    using difference_type = typename Iterator::difference_type;
    using pointer = typename Iterator::pointer;
    using reference = typename Iterator::reference;
};

/// @brief 原始指针特化
template <typename T>
struct iterator_traits<T*> {
    using iterator_category = contiguous_iterator_tag;
    using value_type = T;
    using difference_type = std::ptrdiff_t;
    using pointer = T*;
    using reference = T&;
};

// ============================================================================
// 3. 标签分发示例：advance 算法
// ============================================================================

namespace detail {

// 输入迭代器版本：逐个前进
template <typename Iterator, typename Distance>
void advance_impl(Iterator& it, Distance n, input_iterator_tag) {
    while (n-- > 0) {
        ++it;
    }
}

// 双向迭代器版本：可以后退
template <typename Iterator, typename Distance>
void advance_impl(Iterator& it, Distance n, bidirectional_iterator_tag) {
    if (n > 0) {
        while (n-- > 0) ++it;
    } else {
        while (n++ < 0) --it;
    }
}

// 随机访问迭代器版本：直接跳转
template <typename Iterator, typename Distance>
void advance_impl(Iterator& it, Distance n, random_access_iterator_tag) {
    it += n;
}

}  // namespace detail

/**
 * @brief 标签分发的 advance 算法
 * 根据迭代器类别选择最优实现
 */
template <typename Iterator, typename Distance>
void advance_tagged(Iterator& it, Distance n) {
    using category = typename iterator_traits<Iterator>::iterator_category;
    detail::advance_impl(it, n, category{});
}

// ============================================================================
// 4. 标签分发示例：distance 算法
// ============================================================================

namespace detail {

// 输入迭代器版本：逐个计数
template <typename Iterator>
auto distance_impl(Iterator first, Iterator last, input_iterator_tag) {
    typename iterator_traits<Iterator>::difference_type count = 0;
    while (first != last) {
        ++first;
        ++count;
    }
    return count;
}

// 随机访问迭代器版本：直接相减
template <typename Iterator>
auto distance_impl(Iterator first, Iterator last,
                    random_access_iterator_tag) {
    return last - first;
}

}  // namespace detail

/**
 * @brief 标签分发的 distance 算法
 */
template <typename Iterator>
auto distance_tagged(Iterator first, Iterator last) {
    using category = typename iterator_traits<Iterator>::iterator_category;
    return detail::distance_impl(first, last, category{});
}

// ============================================================================
// 5. 标签分发示例：copy 算法优化
// ============================================================================

namespace detail {

// 普通版本：逐个复制
template <typename InputIt, typename OutputIt>
OutputIt copy_impl(InputIt first, InputIt last, OutputIt dest,
                    input_iterator_tag) {
    while (first != last) {
        *dest = *first;
        ++first;
        ++dest;
    }
    return dest;
}

// 平凡可复制版本：使用 memcpy 优化
template <typename T>
T* copy_impl(const T* first, const T* last, T* dest,
              contiguous_iterator_tag) {
    std::size_t count = last - first;
    std::memmove(dest, first, count * sizeof(T));
    return dest + count;
}

}  // namespace detail

/**
 * @brief 标签分发的 copy 算法
 */
template <typename InputIt, typename OutputIt>
OutputIt copy_tagged(InputIt first, InputIt last, OutputIt dest) {
    using category = typename iterator_traits<InputIt>::iterator_category;
    return detail::copy_impl(first, last, dest, category{});
}

// ============================================================================
// 6. 标签分发示例：数值类型优化
// ============================================================================

/// @brief 整数类型标签
struct integral_tag {};

/// @brief 浮点类型标签
struct floating_point_tag {};

/// @brief 其他类型标签
struct other_tag {};

/**
 * @brief 数值类型萃取
 */
template <typename T>
struct numeric_tag {
    using type = std::conditional_t<
        std::is_integral_v<T>,
        integral_tag,
        std::conditional_t<
            std::is_floating_point_v<T>,
            floating_point_tag,
            other_tag>>;
};

template <typename T>
using numeric_tag_t = typename numeric_tag<T>::type;

// ============================================================================
// 7. 标签分发示例：序列化优化
// ============================================================================

namespace detail {

// 整数类型：直接二进制拷贝
template <typename T>
std::string serialize_impl(T value, integral_tag) {
    const char* bytes = reinterpret_cast<const char*>(&value);
    return std::string(bytes, sizeof(T));
}

// 浮点类型：转换为字符串
template <typename T>
std::string serialize_impl(T value, floating_point_tag) {
    return std::to_string(value);
}

// 其他类型：使用通用方法
template <typename T>
std::string serialize_impl(const T& value, other_tag) {
    return value.serialize();
}

}  // namespace detail

/**
 * @brief 标签分发的序列化函数
 */
template <typename T>
std::string serialize_tagged(const T& value) {
    return detail::serialize_impl(value, numeric_tag_t<T>{});
}

// ============================================================================
// 8. 编译期标签选择
// ============================================================================

/**
 * @brief 根据编译期条件选择标签
 */
template <bool Condition>
using condition_tag = std::conditional_t<Condition, std::true_type, std::false_type>;

/**
 * @brief 多条件标签选择
 */
template <typename... Tags>
struct tag_or;

template <typename Tag>
struct tag_or<Tag> : Tag {};

template <typename First, typename... Rest>
struct tag_or<First, Rest...>
    : std::conditional_t<First::value, First, tag_or<Rest...>> {};

// ============================================================================
// 9. 标签分发与 if constexpr 结合
// ============================================================================

/**
 * @brief 使用 if constexpr 实现类似标签分发的效果
 * C++17 的 if constexpr 可以替代部分标签分发场景
 */
template <typename Iterator>
auto distance_if_constexpr(Iterator first, Iterator last) {
    using category = typename iterator_traits<Iterator>::iterator_category;

    if constexpr (std::is_base_of_v<random_access_iterator_tag, category>) {
        return last - first;
    } else {
        typename iterator_traits<Iterator>::difference_type count = 0;
        while (first != last) {
            ++first;
            ++count;
        }
        return count;
    }
}

}  // namespace tmp
