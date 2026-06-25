#pragma once
// hash.hpp - 编译期哈希函数
//
// 实现常用的编译期哈希函数，用于字符串、整数等类型的哈希计算。
//
// 实现的哈希算法：
//   - FNV-1a：快速、简单的哈希函数
//   - DJB2：Daniel J. Bernstein 的哈希函数
//   - MurmurHash：高性能哈希函数（简化版）
//
// 使用示例：
//   constexpr auto hash1 = ct_hash::fnv1a("hello");
//   constexpr auto hash2 = ct_hash::djb2("world");

#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace compile_time {
namespace hash {

// FNV-1a 哈希函数
// 常量
constexpr std::size_t fnv_offset_basis = 14695981039346656037ULL;
constexpr std::size_t fnv_prime = 1099511628211ULL;

// FNV-1a 哈希（字节序列）
constexpr std::size_t fnv1a(const void* data, std::size_t size) {
    const auto* bytes = static_cast<const unsigned char*>(data);
    std::size_t hash = fnv_offset_basis;
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= static_cast<std::size_t>(bytes[i]);
        hash *= fnv_prime;
    }
    return hash;
}

// FNV-1a 哈希（C 字符串）
constexpr std::size_t fnv1a(const char* str) {
    std::size_t hash = fnv_offset_basis;
    while (*str) {
        hash ^= static_cast<std::size_t>(*str++);
        hash *= fnv_prime;
    }
    return hash;
}

// FNV-1a 哈希（带长度的字符串）
constexpr std::size_t fnv1a(const char* str, std::size_t len) {
    std::size_t hash = fnv_offset_basis;
    for (std::size_t i = 0; i < len; ++i) {
        hash ^= static_cast<std::size_t>(str[i]);
        hash *= fnv_prime;
    }
    return hash;
}

// DJB2 哈希函数
constexpr std::size_t djb2(const char* str) {
    std::size_t hash = 5381;
    while (*str) {
        hash = ((hash << 5) + hash) + static_cast<std::size_t>(*str++);
    }
    return hash;
}

// DJB2a 哈希函数（改进版）
constexpr std::size_t djb2a(const char* str) {
    std::size_t hash = 5381;
    while (*str) {
        hash = ((hash << 5) + hash) ^ static_cast<std::size_t>(*str++);
    }
    return hash;
}

// SDBM 哈希函数
constexpr std::size_t sdbm(const char* str) {
    std::size_t hash = 0;
    while (*str) {
        hash = static_cast<std::size_t>(*str++) + (hash << 6) + (hash << 16) - hash;
    }
    return hash;
}

// BKDR 哈希函数
constexpr std::size_t bkdr(const char* str) {
    std::size_t hash = 0;
    while (*str) {
        hash = hash * 131 + static_cast<std::size_t>(*str++);
    }
    return hash;
}

// 整数哈希函数（Thomas Wang 的方法）
constexpr std::size_t integer_hash(std::size_t key) {
    key = (~key) + (key << 21);
    key = key ^ (key >> 24);
    key = (key + (key << 3)) + (key << 8);
    key = key ^ (key >> 14);
    key = (key + (key << 2)) + (key << 4);
    key = key ^ (key >> 28);
    key = key + (key << 31);
    return key;
}

// 混合哈希（组合多个哈希值）
constexpr std::size_t combine(std::size_t hash1, std::size_t hash2) {
    return hash1 ^ (hash2 + 0x9e3779b9 + (hash1 << 6) + (hash1 >> 2));
}

// 通用哈希函数对象
template<typename T>
struct hash;

// 特化：整数类型
template<>
struct hash<int> {
    constexpr std::size_t operator()(int value) const {
        return integer_hash(static_cast<std::size_t>(value));
    }
};

template<>
struct hash<unsigned int> {
    constexpr std::size_t operator()(unsigned int value) const {
        return integer_hash(static_cast<std::size_t>(value));
    }
};

template<>
struct hash<long> {
    constexpr std::size_t operator()(long value) const {
        return integer_hash(static_cast<std::size_t>(value));
    }
};

template<>
struct hash<unsigned long> {
    constexpr std::size_t operator()(unsigned long value) const {
        return integer_hash(static_cast<std::size_t>(value));
    }
};

template<>
struct hash<long long> {
    constexpr std::size_t operator()(long long value) const {
        return integer_hash(static_cast<std::size_t>(value));
    }
};

template<>
struct hash<unsigned long long> {
    constexpr std::size_t operator()(unsigned long long value) const {
        return integer_hash(static_cast<std::size_t>(value));
    }
};

// 特化：字符类型
template<>
struct hash<char> {
    constexpr std::size_t operator()(char value) const {
        return integer_hash(static_cast<std::size_t>(value));
    }
};

template<>
struct hash<unsigned char> {
    constexpr std::size_t operator()(unsigned char value) const {
        return integer_hash(static_cast<std::size_t>(value));
    }
};

// 特化：指针类型
template<typename T>
struct hash<T*> {
    constexpr std::size_t operator()(T* value) const {
        return integer_hash(reinterpret_cast<std::size_t>(value));
    }
};

// 特化：bool 类型
template<>
struct hash<bool> {
    constexpr std::size_t operator()(bool value) const {
        return static_cast<std::size_t>(value);
    }
};

// 特化：浮点类型
template<>
struct hash<float> {
    constexpr std::size_t operator()(float value) const {
        // 使用整数部分和小数部分的组合
        int int_part = static_cast<int>(value);
        int frac_part = static_cast<int>((value - int_part) * 1000000);
        return integer_hash(static_cast<std::size_t>(int_part)) ^
               integer_hash(static_cast<std::size_t>(frac_part));
    }
};

template<>
struct hash<double> {
    constexpr std::size_t operator()(double value) const {
        // 使用整数部分和小数部分的组合
        long long int_part = static_cast<long long>(value);
        long long frac_part = static_cast<long long>((value - int_part) * 1000000000LL);
        return integer_hash(static_cast<std::size_t>(int_part)) ^
               integer_hash(static_cast<std::size_t>(frac_part));
    }
};

// 字符串字面量哈希（编译期）
template<std::size_t N>
constexpr std::size_t literal_hash(const char (&str)[N]) {
    return fnv1a(str, N - 1);
}

// 编译期字符串哈希运算符
constexpr std::size_t operator""_hash(const char* str, std::size_t len) {
    return fnv1a(str, len);
}

} // namespace hash
} // namespace compile_time
