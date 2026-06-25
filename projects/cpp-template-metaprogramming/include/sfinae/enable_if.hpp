#pragma once
// =============================================================================
// enable_if.hpp - SFINAE 与 enable_if 技术
// =============================================================================
// SFINAE: Substitution Failure Is Not An Error
// 核心思想：模板参数替换失败不会导致编译错误，而是将该重载从候选集中移除
// =============================================================================

#include <type_traits>
#include <iostream>
#include <string>

namespace tmp {
namespace sfinae {

// ---------------------------------------------------------------------------
// enable_if 基本用法 - 限制模板参数类型
// ---------------------------------------------------------------------------

// 示例1：只接受整数类型
template <typename T>
std::enable_if_t<std::is_integral_v<T>, T>
safe_add(T a, T b) {
    // 检查溢出（简化版）
    return a + b;
}

// 示例2：只接受浮点类型
template <typename T>
std::enable_if_t<std::is_floating_point_v<T>, T>
safe_add(T a, T b) {
    return a + b;
}

// ---------------------------------------------------------------------------
// enable_if 用于返回类型
// ---------------------------------------------------------------------------

// 根据类型返回不同的字符串描述
template <typename T>
std::enable_if_t<std::is_integral_v<T>, std::string>
type_name(T) { return "integral"; }

template <typename T>
std::enable_if_t<std::is_floating_point_v<T>, std::string>
type_name(T) { return "floating_point"; }

template <typename T>
std::enable_if_t<std::is_pointer_v<T>, std::string>
type_name(T) { return "pointer"; }

// ---------------------------------------------------------------------------
// enable_if 用于模板参数（默认参数）
// ---------------------------------------------------------------------------

// 打印整数（二进制表示的简化版）
template <typename T,
          std::enable_if_t<std::is_integral_v<T>, int> = 0>
void print_info(T value) {
    std::cout << "[integral] value = " << value << std::endl;
}

// 打印浮点数
template <typename T,
          std::enable_if_t<std::is_floating_point_v<T>, int> = 0>
void print_info(T value) {
    std::cout << "[float]    value = " << value << std::endl;
}

// 打印指针
template <typename T,
          std::enable_if_t<std::is_pointer_v<T>, int> = 0>
void print_info(T value) {
    std::cout << "[pointer]  value = " << value
              << ", deref = " << *value << std::endl;
}

// ---------------------------------------------------------------------------
// enable_if 用于类模板特化
// ---------------------------------------------------------------------------

// 通用序列化器
template <typename T, typename Enable = void>
struct Serializer {
    static std::string serialize(const T& value) {
        return "unknown(" + std::to_string(sizeof(T)) + " bytes)";
    }
};

// 整数特化
template <typename T>
struct Serializer<T, std::enable_if_t<std::is_integral_v<T>>> {
    static std::string serialize(const T& value) {
        return "int:" + std::to_string(value);
    }
};

// 浮点特化
template <typename T>
struct Serializer<T, std::enable_if_t<std::is_floating_point_v<T>>> {
    static std::string serialize(const T& value) {
        return "float:" + std::to_string(value);
    }
};

// 指针特化
template <typename T>
struct Serializer<T, std::enable_if_t<std::is_pointer_v<T>>> {
    static std::string serialize(const T& value) {
        if (value) return "ptr:" + serialize(*value);  // 递归序列化
        return "nullptr";
    }
};

// ---------------------------------------------------------------------------
// SFINAE 检测成员函数是否存在
// ---------------------------------------------------------------------------

// 检测类型是否有 size() 成员函数
namespace detail {
    // 优先匹配的版本（当 T 有 size() 时）
    template <typename T>
    auto has_size_impl(int) -> decltype(std::declval<T>().size(), std::true_type{});

    // 兜底版本
    template <typename T>
    std::false_type has_size_impl(...);
}

template <typename T>
struct has_size : decltype(detail::has_size_impl<T>(0)) {};

template <typename T>
inline constexpr bool has_size_v = has_size<T>::value;

// 使用 has_size 来约束模板
template <typename Container>
std::enable_if_t<has_size_v<Container>, std::size_t>
get_size(const Container& c) {
    return c.size();
}

// 对没有 size() 的容器使用 std::distance
template <typename Container>
std::enable_if_t<!has_size_v<Container>, std::size_t>
get_size(const Container& c) {
    return std::distance(std::begin(c), std::end(c));
}

} // namespace sfinae
} // namespace tmp
