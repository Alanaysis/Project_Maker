#pragma once
// fixed_string.hpp - 编译期字符串实现
//
// 编译期字符串是许多编译期数据结构的基础。C++20 支持将字面量作为模板参数，
// 使得 fixed_string 可以直接用于模板参数推导。
//
// 核心思想：
//   使用 char 数组存储字符串，所有操作都是 constexpr，可以在编译期执行。
//
// 使用示例：
//   constexpr fixed_string str = "hello";
//   static_assert(str.size() == 5);
//   static_assert(str[0] == 'h');

#include <cstddef>
#include <algorithm>
#include <string_view>

namespace compile_time {

// fixed_string: 编译期字符串类
// N 表示字符串长度（包含 null 终止符）
template<std::size_t N>
struct fixed_string {
    char data_[N]{};
    static constexpr std::size_t npos = static_cast<std::size_t>(-1);

    // 构造函数：从字符数组构造
    constexpr fixed_string(const char (&str)[N]) {
        for (std::size_t i = 0; i < N; ++i) {
            data_[i] = str[i];
        }
    }

    // 默认构造函数
    constexpr fixed_string() = default;

    // 访问器
    constexpr char operator[](std::size_t i) const { return data_[i]; }
    constexpr char& operator[](std::size_t i) { return data_[i]; }
    constexpr std::size_t size() const { return N - 1; }  // 不包含 null 终止符
    constexpr std::size_t length() const { return size(); }
    constexpr bool empty() const { return size() == 0; }
    constexpr const char* c_str() const { return data_; }
    constexpr const char* data() const { return data_; }

    // 迭代器支持
    constexpr const char* begin() const { return data_; }
    constexpr const char* end() const { return data_ + size(); }

    // 转换为 string_view（C++17）
    constexpr operator std::string_view() const {
        return std::string_view(data_, size());
    }

    // 比较操作
    template<std::size_t M>
    constexpr bool operator==(const fixed_string<M>& other) const {
        if constexpr (N != M) return false;
        for (std::size_t i = 0; i < N; ++i) {
            if (data_[i] != other.data_[i]) return false;
        }
        return true;
    }

    template<std::size_t M>
    constexpr bool operator!=(const fixed_string<M>& other) const {
        return !(*this == other);
    }

    template<std::size_t M>
    constexpr bool operator<(const fixed_string<M>& other) const {
        for (std::size_t i = 0; i < N && i < M; ++i) {
            if (data_[i] < other.data_[i]) return true;
            if (data_[i] > other.data_[i]) return false;
        }
        return N < M;
    }

    // 查找字符
    constexpr std::size_t find(char c, std::size_t pos = 0) const {
        for (std::size_t i = pos; i < size(); ++i) {
            if (data_[i] == c) return i;
        }
        return npos;
    }

    // 查找子串
    template<std::size_t M>
    constexpr std::size_t find(const fixed_string<M>& substr, std::size_t pos = 0) const {
        if (substr.size() > size()) return npos;
        for (std::size_t i = pos; i <= size() - substr.size(); ++i) {
            bool found = true;
            for (std::size_t j = 0; j < substr.size(); ++j) {
                if (data_[i + j] != substr[j]) {
                    found = false;
                    break;
                }
            }
            if (found) return i;
        }
        return npos;
    }

    // 子串（编译期使用模板参数）
    template<std::size_t Pos, std::size_t Count>
    constexpr auto substr() const {
        static_assert(Pos + Count < N, "Subscript out of range");
        char buf[Count + 1]{};
        for (std::size_t i = 0; i < Count; ++i) {
            buf[i] = data_[Pos + i];
        }
        return fixed_string<Count + 1>(buf);
    }

    // 前缀判断
    template<std::size_t M>
    constexpr bool starts_with(const fixed_string<M>& prefix) const {
        if (prefix.size() > size()) return false;
        for (std::size_t i = 0; i < prefix.size(); ++i) {
            if (data_[i] != prefix[i]) return false;
        }
        return true;
    }

    // 后缀判断
    template<std::size_t M>
    constexpr bool ends_with(const fixed_string<M>& suffix) const {
        if (suffix.size() > size()) return false;
        for (std::size_t i = 0; i < suffix.size(); ++i) {
            if (data_[size() - suffix.size() + i] != suffix[i]) return false;
        }
        return true;
    }
};

// C++20 CTAD 推导指引
template<std::size_t N>
fixed_string(const char (&)[N]) -> fixed_string<N>;

// 字符串拼接
template<std::size_t N, std::size_t M>
constexpr auto operator+(const fixed_string<N>& a, const fixed_string<M>& b) {
    constexpr std::size_t len = N + M - 1;
    char buf[len]{};
    for (std::size_t i = 0; i < N - 1; ++i) {
        buf[i] = a[i];
    }
    for (std::size_t i = 0; i < M; ++i) {
        buf[N - 1 + i] = b[i];
    }
    return fixed_string<len>(buf);
}

// 从 string_view 构造（辅助函数）
template<std::size_t N>
constexpr fixed_string<N - 1> make_fixed_string(const char (&str)[N]) {
    return fixed_string<N - 1>(str);
}

// 编译期字符串哈希（FNV-1a）
constexpr std::size_t fnv1a_hash(const char* str, std::size_t len) {
    std::size_t h = 14695981039346656037ULL;
    for (std::size_t i = 0; i < len; ++i) {
        h ^= static_cast<std::size_t>(str[i]);
        h *= 1099511628211ULL;
    }
    return h;
}

template<std::size_t N>
constexpr std::size_t string_hash(const fixed_string<N>& str) {
    return fnv1a_hash(str.data(), str.size());
}

} // namespace compile_time
