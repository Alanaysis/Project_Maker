#pragma once
// =============================================================================
// compile_time_string.hpp - 编译期字符串 (Compile-Time String)
// =============================================================================
// 实现编译期字符串操作，字符串存储为模板参数
// C++20 前需要一些技巧来实现
// =============================================================================

#include <cstddef>
#include <array>
#include <string_view>
#include <algorithm>

namespace tmp {

// ---------------------------------------------------------------------------
// 编译期字符串基础 (C++17 方式)
// ---------------------------------------------------------------------------

// 使用固定大小数组存储字符串
template <std::size_t N>
struct FixedString {
    char data[N]{};
    static constexpr std::size_t size = N - 1;  // 不包含 '\0'

    constexpr FixedString() = default;

    // 从字符数组构造
    constexpr FixedString(const char (&str)[N]) {
        for (std::size_t i = 0; i < N; ++i) {
            data[i] = str[i];
        }
    }

    // 转为 string_view
    constexpr std::string_view view() const {
        return std::string_view{data, size};
    }

    // 访问特定字符
    constexpr char operator[](std::size_t i) const {
        return data[i];
    }

    // 比较操作
    template <std::size_t M>
    constexpr bool operator==(const FixedString<M>& other) const {
        if constexpr (N != M) return false;
        for (std::size_t i = 0; i < N; ++i) {
            if (data[i] != other.data[i]) return false;
        }
        return true;
    }

    template <std::size_t M>
    constexpr bool operator!=(const FixedString<M>& other) const {
        return !(*this == other);
    }
};

// CTAD 推导指引
template <std::size_t N>
FixedString(const char (&)[N]) -> FixedString<N>;

// ---------------------------------------------------------------------------
// 编译期字符串操作
// ---------------------------------------------------------------------------

// 获取字符串长度
template <FixedString Str>
constexpr std::size_t string_length() {
    return Str.size;
}

// 字符串连接
template <FixedString Str1, FixedString Str2>
constexpr auto concat_strings() {
    constexpr std::size_t N = Str1.size + Str2.size + 1;
    FixedString<N> result{};
    for (std::size_t i = 0; i < Str1.size; ++i) {
        result.data[i] = Str1[i];
    }
    for (std::size_t i = 0; i < Str2.size; ++i) {
        result.data[Str1.size + i] = Str2[i];
    }
    result.data[N - 1] = '\0';
    return result;
}

// 字符串反转
template <FixedString Str>
constexpr auto reverse_string() {
    constexpr std::size_t N = Str.size + 1;
    FixedString<N> result{};
    for (std::size_t i = 0; i < Str.size; ++i) {
        result.data[i] = Str[Str.size - 1 - i];
    }
    result.data[N - 1] = '\0';
    return result;
}

// 字符串查找
template <FixedString Str>
constexpr std::size_t find_char(char c) {
    for (std::size_t i = 0; i < Str.size; ++i) {
        if (Str[i] == c) return i;
    }
    return Str.size;  // 未找到返回 size
}

// 检查是否以特定前缀开始
template <FixedString Str, FixedString Prefix>
constexpr bool starts_with() {
    if constexpr (Prefix.size > Str.size) return false;
    for (std::size_t i = 0; i < Prefix.size; ++i) {
        if (Str[i] != Prefix[i]) return false;
    }
    return true;
}

// 检查是否以特定后缀结束
template <FixedString Str, FixedString Suffix>
constexpr bool ends_with() {
    if constexpr (Suffix.size > Str.size) return false;
    for (std::size_t i = 0; i < Suffix.size; ++i) {
        if (Str[Str.size - Suffix.size + i] != Suffix[i]) return false;
    }
    return true;
}

// 子字符串提取
template <FixedString Str, std::size_t Start, std::size_t Len>
constexpr auto substr() {
    constexpr std::size_t ActualLen = (Start + Len > Str.size) ? Str.size - Start : Len;
    FixedString<ActualLen + 1> result{};
    for (std::size_t i = 0; i < ActualLen; ++i) {
        result.data[i] = Str[Start + i];
    }
    result.data[ActualLen] = '\0';
    return result;
}

// 大小写转换
template <FixedString Str>
constexpr auto to_upper() {
    FixedString<Str.size + 1> result{};
    for (std::size_t i = 0; i < Str.size; ++i) {
        char c = Str[i];
        result.data[i] = (c >= 'a' && c <= 'z') ? c - 32 : c;
    }
    result.data[Str.size] = '\0';
    return result;
}

template <FixedString Str>
constexpr auto to_lower() {
    FixedString<Str.size + 1> result{};
    for (std::size_t i = 0; i < Str.size; ++i) {
        char c = Str[i];
        result.data[i] = (c >= 'A' && c <= 'Z') ? c + 32 : c;
    }
    result.data[Str.size] = '\0';
    return result;
}

// ---------------------------------------------------------------------------
// 编译期字符串类型萃取
// ---------------------------------------------------------------------------

// 判断是否为编译期字符串类型
template <typename T>
struct is_fixed_string : std::false_type {};

template <std::size_t N>
struct is_fixed_string<FixedString<N>> : std::true_type {};

template <typename T>
inline constexpr bool is_fixed_string_v = is_fixed_string<T>::value;

// ---------------------------------------------------------------------------
// 使用示例：编译期格式化字符串
// ---------------------------------------------------------------------------

// 简单的编译期字符串拼接
template <FixedString... Strings>
constexpr auto concat_all() {
    // 使用折叠表达式连接所有字符串
    return (FixedString{""} + ... + Strings);
}

// ---------------------------------------------------------------------------
// C++20 风格的字符串模板参数
// ---------------------------------------------------------------------------
// C++20 中可以直接使用 FixedString 作为非类型模板参数
// 例如: template <FixedString Str> struct Config {};

// 示例：编译期配置
template <FixedString Name, FixedString Value>
struct ConfigEntry {
    static constexpr auto name = Name;
    static constexpr auto value = Value;
};

// 示例配置
using HostConfig = ConfigEntry<"host", "localhost">;
using PortConfig = ConfigEntry<"port", "8080">;

// ---------------------------------------------------------------------------
// 编译期字符串哈希 (简单 FNV-1a)
// ---------------------------------------------------------------------------

constexpr std::size_t fnv1a_hash(const char* str, std::size_t len) {
    std::size_t hash = 14695981039346656037ULL;
    for (std::size_t i = 0; i < len; ++i) {
        hash ^= static_cast<std::size_t>(str[i]);
        hash *= 1099511628211ULL;
    }
    return hash;
}

template <FixedString Str>
constexpr std::size_t fixed_string_hash() {
    return fnv1a_hash(Str.data, Str.size);
}

} // namespace tmp
