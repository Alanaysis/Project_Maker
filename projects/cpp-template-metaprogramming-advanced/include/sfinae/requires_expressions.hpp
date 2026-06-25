#pragma once
/**
 * @file requires_expressions.hpp
 * @brief C++20 requires 表达式
 *
 * C++20 的 requires 表达式提供了比 SFINAE 更清晰的语法
 * 来检测类型的约束。
 *
 * 包含：
 *   - 简单需求 (Simple Requirements)
 *   - 类型需求 (Type Requirements)
 *   - 复合需求 (Compound Requirements)
 *   - 嵌套需求 (Nested Requirements)
 *   - 约束 (Concepts)
 */

#include <concepts>
#include <type_traits>
#include <string>
#include <iostream>
#include <vector>
#include <iterator>
#include <cstddef>

namespace tmp {

// ============================================================================
// 1. 基础 requires 表达式
// ============================================================================

/**
 * @brief 简单需求 - 检测表达式是否有效
 */
template <typename T>
concept HasSize = requires(T t) {
    { t.size() } -> std::convertible_to<std::size_t>;
};

/**
 * @brief 检测是否有 begin 和 end
 */
template <typename T>
concept HasBeginEnd = requires(T t) {
    { t.begin() } -> std::input_or_output_iterator;
    { t.end() } -> std::input_or_output_iterator;
};

/**
 * @brief 检测是否可迭代
 */
template <typename T>
concept Iterable = HasBeginEnd<T>;

/**
 * @brief 检测是否可索引
 */
template <typename T>
concept Indexable = requires(T t, std::size_t i) {
    { t[i] } -> std::same_as<typename T::reference>;
};

// ============================================================================
// 2. 类型需求
// ============================================================================

/**
 * @brief 检测类型是否有 value_type 成员类型
 */
template <typename T>
concept HasValueType = requires {
    typename T::value_type;
};

/**
 * @brief 检测类型是否有 iterator 成员类型
 */
template <typename T>
concept HasIterator = requires {
    typename T::iterator;
};

/**
 * @brief 检测类型是否有 allocator_type
 */
template <typename T>
concept HasAllocator = requires {
    typename T::allocator_type;
};

// ============================================================================
// 3. 复合需求
// ============================================================================

/**
 * @brief 检测类型是否为容器
 */
template <typename T>
concept Container = requires(T t) {
    typename T::value_type;
    typename T::iterator;
    { t.begin() } -> std::same_as<typename T::iterator>;
    { t.end() } -> std::same_as<typename T::iterator>;
    { t.size() } -> std::convertible_to<std::size_t>;
    { t.empty() } -> std::convertible_to<bool>;
};

/**
 * @brief 检测类型是否为序列容器
 */
template <typename T>
concept SequenceContainer = Container<T> && requires(T t, typename T::value_type v) {
    t.push_back(v);
    { t.front() } -> std::same_as<typename T::reference>;
    { t.back() } -> std::same_as<typename T::reference>;
};

// ============================================================================
// 4. 嵌套需求
// ============================================================================

/**
 * @brief 嵌套需求 - 使用 requires 子句添加额外约束
 */
template <typename T>
concept Sortable = requires(T t) {
    typename T::value_type;
    { t.begin() } -> std::random_access_iterator;
    { t.end() } -> std::random_access_iterator;
} && requires(typename T::value_type a, typename T::value_type b) {
    { a < b } -> std::convertible_to<bool>;
    { a == b } -> std::convertible_to<bool>;
};

// ============================================================================
// 5. 数值概念
// ============================================================================

/**
 * @brief 检测是否为数值类型
 */
template <typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

/**
 * @brief 检测是否为算术类型
 */
template <typename T>
concept Arithmetic = requires(T a, T b) {
    { a + b } -> std::same_as<T>;
    { a - b } -> std::same_as<T>;
    { a * b } -> std::same_as<T>;
    { a / b } -> std::same_as<T>;
    { -a } -> std::same_as<T>;
};

/**
 * @brief 检测是否可加
 */
template <typename T, typename U = T>
concept Addable = requires(T a, U b) {
    { a + b };
};

/**
 * @brief 检测是否可减
 */
template <typename T, typename U = T>
concept Subtractable = requires(T a, U b) {
    { a - b };
};

// ============================================================================
// 6. 序列化相关概念
// ============================================================================

/**
 * @brief 检测类型是否可序列化
 */
template <typename T>
concept Serializable = requires(const T& t) {
    { t.serialize() } -> std::convertible_to<std::string>;
};

/**
 * @brief 检测类型是否可反序列化
 */
template <typename T>
concept Deserializable = requires(T& t, const std::string& s) {
    { t.deserialize(s) };
};

/**
 * @brief 检测类型是否可完整序列化
 */
template <typename T>
concept FullySerializable = Serializable<T> && Deserializable<T>;

// ============================================================================
// 7. 流操作概念
// ============================================================================

/**
 * @brief 检测类型是否可输出到流
 */
template <typename T>
concept Streamable = requires(std::ostream& os, const T& t) {
    { os << t } -> std::same_as<std::ostream&>;
};

/**
 * @brief 检测类型是否可从流输入
 */
template <typename T>
concept InputStreamable = requires(std::istream& is, T& t) {
    { is >> t } -> std::same_as<std::istream&>;
};

// ============================================================================
// 8. 可调用概念
// ============================================================================

/**
 * @brief 检测是否为一元函数
 */
template <typename F, typename Arg>
concept UnaryFunction = requires(F f, Arg a) {
    { f(a) };
};

/**
 * @brief 检测是否为二元函数
 */
template <typename F, typename Arg1, typename Arg2>
concept BinaryFunction = requires(F f, Arg1 a, Arg2 b) {
    { f(a, b) };
};

/**
 * @brief 检测是否为谓词（返回 bool 的函数）
 */
template <typename F, typename... Args>
concept Predicate = requires(F f, Args... args) {
    { f(args...) } -> std::convertible_to<bool>;
};

// ============================================================================
// 9. 使用 requires 约束的算法
// ============================================================================

/**
 * @brief 约束的查找算法
 */
template <Container C, typename T>
    requires std::equality_comparable_with<typename C::value_type, T>
auto constrained_find(const C& container, const T& value) {
    for (auto it = container.begin(); it != container.end(); ++it) {
        if (*it == value) return it;
    }
    return container.end();
}

/**
 * @brief 约束的打印函数
 */
template <typename T>
    requires Streamable<T>
void constrained_print(const T& value) {
    std::cout << value << std::endl;
}

/**
 * @brief 约束的容器打印
 */
template <Container C>
    requires Streamable<typename C::value_type>
void constrained_print_container(const C& container) {
    std::cout << "[";
    bool first = true;
    for (const auto& item : container) {
        if (!first) std::cout << ", ";
        std::cout << item;
        first = false;
    }
    std::cout << "]" << std::endl;
}

// ============================================================================
// 10. 编译期 requires 检测
// ============================================================================

/**
 * @brief 编译期检测是否满足概念
 */
template <typename T>
inline constexpr bool is_container_v = Container<T>;

template <typename T>
inline constexpr bool is_sequence_container_v = SequenceContainer<T>;

template <typename T>
inline constexpr bool is_sortable_v = Sortable<T>;

template <typename T>
inline constexpr bool is_numeric_v = Numeric<T>;

template <typename T>
inline constexpr bool is_streamable_v = Streamable<T>;

template <typename T>
inline constexpr bool is_serializable_v = Serializable<T>;

// ============================================================================
// 11. 条件约束
// ============================================================================

/**
 * @brief 条件约束 - 根据条件选择不同的约束
 */
template <typename T>
concept Printable = requires(std::ostream& os, const T& t) {
    os << t;
} || requires(const T& t) {
    { t.to_string() } -> std::convertible_to<std::string>;
};

/**
 * @brief 多态约束 - 类型满足任一概念
 */
template <typename T>
concept NumberOrString = Numeric<T> || std::same_as<T, std::string>;

}  // namespace tmp
