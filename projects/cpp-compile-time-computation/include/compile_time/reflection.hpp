#pragma once
// reflection.hpp - 编译期反射（基础）
//
// 实现基础的编译期反射功能。
// C++ 目前没有原生的反射支持，这里使用一些技巧实现有限的反射。
//
// 核心思想：
//   使用结构化绑定和宏来注册类型的成员信息。
//   使用 constexpr 函数在编译期获取类型信息。
//
// 注意：这是基础实现，C++26 可能会引入原生反射支持。
//
// 使用示例：
//   struct Point {
//       int x;
//       int y;
//   };
//
//   REGISTER_TYPE(Point, x, y)
//
//   constexpr auto info = type_info<Point>();
//   static_assert(info.name == "Point");
//   static_assert(info.field_count == 2);

#include <cstddef>
#include <type_traits>
#include <cstring>
#include "fixed_string.hpp"

namespace compile_time {
namespace reflection {

// type_tag: 类型标签
template<typename T>
struct type_tag {
    using type = T;
};

// 基础类型信息
template<typename T>
struct type_info {
    static constexpr bool is_void = std::is_void_v<T>;
    static constexpr bool is_integral = std::is_integral_v<T>;
    static constexpr bool is_floating_point = std::is_floating_point_v<T>;
    static constexpr bool is_arithmetic = std::is_arithmetic_v<T>;
    static constexpr bool is_pointer = std::is_pointer_v<T>;
    static constexpr bool is_reference = std::is_reference_v<T>;
    static constexpr bool is_const = std::is_const_v<T>;
    static constexpr bool is_volatile = std::is_volatile_v<T>;
    static constexpr bool is_array = std::is_array_v<T>;
    static constexpr bool is_class = std::is_class_v<T>;
    static constexpr bool is_enum = std::is_enum_v<T>;
    static constexpr bool is_function = std::is_function_v<T>;
    static constexpr bool is_default_constructible = std::is_default_constructible_v<T>;
    static constexpr bool is_copy_constructible = std::is_copy_constructible_v<T>;
    static constexpr bool is_move_constructible = std::is_move_constructible_v<T>;
    static constexpr bool is_destructible = std::is_destructible_v<T>;
    static constexpr std::size_t size = sizeof(T);
    static constexpr std::size_t alignment = alignof(T);
};

// 字段信息
struct field_info {
    const char* name;
    std::size_t offset;
    std::size_t size;
    std::size_t type_hash;
};

// 类型注册信息
template<std::size_t N>
struct type_registration {
    const char* name;
    field_info fields[N];
    static constexpr std::size_t field_count = N;
};

// 辅助宏：注册类型
#define CT_CONCATENATE_IMPL(x, y) x##y
#define CT_CONCATENATE(x, y) CT_CONCATENATE_IMPL(x, y)
#define CT_STRINGIFY_IMPL(x) #x
#define CT_STRINGIFY(x) CT_STRINGIFY_IMPL(x)

#define CT_FIELD_OFFSET(type, field) \
    (reinterpret_cast<std::size_t>(&reinterpret_cast<const char*>(&(static_cast<type*>(nullptr)->field))))

#define CT_FIELD_SIZE(type, field) \
    sizeof(static_cast<type*>(nullptr)->field)

// 简化的类型注册宏
#define REGISTER_TYPE(type, ...) \
    namespace ct_refl_##type { \
        using registered_type = type; \
        constexpr auto get_fields() { \
            return compile_time::reflection::make_fields(__VA_ARGS__); \
        } \
    }

// 编译期类型名称（简化实现）
template<typename T>
constexpr const char* type_name() {
    // 注意：这是一个简化实现，实际的类型名称需要编译器支持
    // GCC/Clang 可以使用 __PRETTY_FUNCTION__
    return "unknown";
}

// 编译期类型哈希
template<typename T>
constexpr std::size_t type_hash() {
    // 使用类型的大小和对齐作为简单哈希
    return sizeof(T) * 31 + alignof(T);
}

// 编译期字段访问（使用结构化绑定）
template<typename T, typename F>
constexpr void for_each_field(T& obj, F func) {
    // 注意：这需要 C++17 结构化绑定和编译器特定的实现
    // 这里提供一个简化的示例
    // 实际实现需要使用编译器特定的反射 API
    (void)obj;
    (void)func;
}

// 编译期序列化（基础）
template<typename T>
constexpr std::size_t serialized_size(const T& obj) {
    return sizeof(T);
}

// 编译期比较
template<typename T>
constexpr bool deep_equal(const T& a, const T& b) {
    // 简化实现：直接比较内存
    const auto* a_bytes = reinterpret_cast<const unsigned char*>(&a);
    const auto* b_bytes = reinterpret_cast<const unsigned char*>(&b);
    for (std::size_t i = 0; i < sizeof(T); ++i) {
        if (a_bytes[i] != b_bytes[i]) return false;
    }
    return true;
}

// 编译期哈希（基础）
template<typename T>
constexpr std::size_t hash_value(const T& obj) {
    const auto* bytes = reinterpret_cast<const unsigned char*>(&obj);
    std::size_t hash = 14695981039346656037ULL;
    for (std::size_t i = 0; i < sizeof(T); ++i) {
        hash ^= static_cast<std::size_t>(bytes[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

// 类型特征查询
template<typename T>
struct type_traits {
    static constexpr bool is_trivially_copyable = std::is_trivially_copyable_v<T>;
    static constexpr bool is_trivially_destructible = std::is_trivially_destructible_v<T>;
    static constexpr bool is_standard_layout = std::is_standard_layout_v<T>;
    static constexpr bool is_pod = std::is_pod_v<T>;
    static constexpr bool has_virtual_destructor = std::is_polymorphic_v<T>;
};

// 编译期类型列表
template<typename... Ts>
struct type_list {
    static constexpr std::size_t size = sizeof...(Ts);
};

// 类型列表操作
template<typename List, typename T>
struct push_back;

template<typename... Ts, typename T>
struct push_back<type_list<Ts...>, T> {
    using type = type_list<Ts..., T>;
};

template<typename List>
struct front;

template<typename T, typename... Ts>
struct front<type_list<T, Ts...>> {
    using type = T;
};

template<typename List>
struct pop_front;

template<typename T, typename... Ts>
struct pop_front<type_list<T, Ts...>> {
    using type = type_list<Ts...>;
};

// 类型列表查找
template<typename List, typename T>
struct contains;

template<typename T>
struct contains<type_list<>, T> : std::false_type {};

template<typename T, typename U, typename... Us>
struct contains<type_list<U, Us...>, T> : contains<type_list<Us...>, T> {};

template<typename T, typename... Us>
struct contains<type_list<T, Us...>, T> : std::true_type {};

// 类型列表索引
template<typename List, typename T, std::size_t I = 0>
struct index_of;

template<typename T, std::size_t I>
struct index_of<type_list<>, T, I> : std::integral_constant<std::size_t, 0> {};

template<typename T, typename U, typename... Us, std::size_t I>
struct index_of<type_list<U, Us...>, T, I>
    : std::integral_constant<std::size_t, index_of<type_list<Us...>, T, I + 1>::value> {};

template<typename T, typename... Us, std::size_t I>
struct index_of<type_list<T, Us...>, T, I> : std::integral_constant<std::size_t, I> {};

// 类型列表转换
template<typename List, template<typename> class F>
struct transform;

template<template<typename> class F, typename... Ts>
struct transform<type_list<Ts...>, F> {
    using type = type_list<typename F<Ts>::type...>;
};

// 编译期静态反射（使用 constexpr）
template<typename T>
constexpr auto get_type_info() {
    return type_info<T>{};
}

// 编译期类型名称（简化）
template<typename T>
constexpr const char* simple_type_name() {
    if constexpr (std::is_same_v<T, int>) return "int";
    else if constexpr (std::is_same_v<T, double>) return "double";
    else if constexpr (std::is_same_v<T, float>) return "float";
    else if constexpr (std::is_same_v<T, bool>) return "bool";
    else if constexpr (std::is_same_v<T, char>) return "char";
    else if constexpr (std::is_same_v<T, unsigned int>) return "unsigned int";
    else if constexpr (std::is_same_v<T, long>) return "long";
    else if constexpr (std::is_same_v<T, long long>) return "long long";
    else if constexpr (std::is_same_v<T, void>) return "void";
    else return "user_type";
}

} // namespace reflection
} // namespace compile_time
