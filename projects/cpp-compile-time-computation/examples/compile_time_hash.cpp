// compile_time_hash.cpp - 编译期哈希函数示例
//
// 本文件展示编译期哈希函数的用法，包括：
//   1. FNV-1a 哈希
//   2. DJB2 哈希
//   3. 整数哈希
//   4. 字符串字面量哈希
//
// 编译命令：
//   g++ -std=c++20 -I include examples/compile_time_hash.cpp -o compile_time_hash

#include <iostream>
#include <iomanip>
#include "compile_time/hash.hpp"

using namespace compile_time::hash;

// ============================================================================
// 第一部分：FNV-1a 哈希
// ============================================================================

// FNV-1a 哈希（C 字符串）
constexpr std::size_t fnv1a_hello = fnv1a("hello");
constexpr std::size_t fnv1a_world = fnv1a("world");
constexpr std::size_t fnv1a_hello2 = fnv1a("hello");  // 相同字符串相同哈希

// FNV-1a 哈希（带长度）
constexpr std::size_t fnv1a_len = fnv1a("hello", 5);

// ============================================================================
// 第二部分：DJB2 哈希
// ============================================================================

// DJB2 哈希
constexpr std::size_t djb2_hello = djb2("hello");
constexpr std::size_t djb2_world = djb2("world");
constexpr std::size_t djb2_hello2 = djb2("hello");  // 相同字符串相同哈希

// DJB2a 哈希（改进版）
constexpr std::size_t djb2a_hello = djb2a("hello");

// ============================================================================
// 第三部分：其他哈希函数
// ============================================================================

// SDBM 哈希
constexpr std::size_t sdbm_hello = sdbm("hello");

// BKDR 哈希
constexpr std::size_t bkdr_hello = bkdr("hello");

// 整数哈希
constexpr std::size_t int_hash_0 = integer_hash(0);
constexpr std::size_t int_hash_1 = integer_hash(1);
constexpr std::size_t int_hash_42 = integer_hash(42);
constexpr std::size_t int_hash_100 = integer_hash(100);

// ============================================================================
// 第四部分：通用哈希函数对象
// ============================================================================

// 整数哈希
constexpr hash<int> int_hasher;
constexpr std::size_t hash_int_42 = int_hasher(42);

// 浮点数哈希
constexpr hash<double> double_hasher;
constexpr std::size_t hash_double_314 = double_hasher(3.14);

// 布尔哈希
constexpr hash<bool> bool_hasher;
constexpr std::size_t hash_true = bool_hasher(true);
constexpr std::size_t hash_false = bool_hasher(false);

// ============================================================================
// 第五部分：字符串字面量哈希（用户定义字面量）
// ============================================================================

// 使用 _hash 用户定义字面量
constexpr std::size_t hash_hello = "hello"_hash;
constexpr std::size_t hash_world = "world"_hash;

// ============================================================================
// 第六部分：哈希组合
// ============================================================================

// 组合多个哈希值
constexpr std::size_t combined_hash = combine(fnv1a_hello, fnv1a_world);

// ============================================================================
// 第七部分：实际应用示例
// ============================================================================

// 编译期字符串比较（使用哈希）
template<std::size_t N, std::size_t M>
constexpr bool string_equal_hash(const char (&a)[N], const char (&b)[M]) {
    if constexpr (N != M) return false;
    return fnv1a(a, N - 1) == fnv1a(b, M - 1);
}

// 编译期哈希表（简化版）
template<std::size_t N>
struct compile_time_hash_set {
    std::size_t hashes[N]{};
    std::size_t count = 0;

    constexpr bool insert(const char* str) {
        std::size_t h = fnv1a(str);
        for (std::size_t i = 0; i < count; ++i) {
            if (hashes[i] == h) return false;  // 已存在
        }
        if (count < N) {
            hashes[count++] = h;
            return true;
        }
        return false;
    }

    constexpr bool contains(const char* str) const {
        std::size_t h = fnv1a(str);
        for (std::size_t i = 0; i < count; ++i) {
            if (hashes[i] == h) return true;
        }
        return false;
    }
};

// ============================================================================
// 第八部分：编译期断言验证
// ============================================================================

// FNV-1a 哈希
static_assert(fnv1a_hello == fnv1a_hello2);  // 相同字符串相同哈希
static_assert(fnv1a_hello != fnv1a_world);   // 不同字符串不同哈希
static_assert(fnv1a_len == fnv1a_hello);     // 带长度版本结果相同

// DJB2 哈希
static_assert(djb2_hello == djb2_hello2);    // 相同字符串相同哈希
static_assert(djb2_hello != djb2_world);     // 不同字符串不同哈希

// 整数哈希
static_assert(int_hash_0 != int_hash_1);
static_assert(int_hash_42 != int_hash_100);

// 通用哈希
static_assert(hash_int_42 == integer_hash(42));

// 用户定义字面量
static_assert(hash_hello == fnv1a_hello);

// 字符串比较
static_assert(string_equal_hash("hello", "hello") == true);
static_assert(string_equal_hash("hello", "world") == false);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期哈希函数示例 ===" << std::endl;
    std::cout << std::endl;

    // FNV-1a 哈希
    std::cout << "1. FNV-1a 哈希:" << std::endl;
    std::cout << "   fnv1a(\"hello\") = " << fnv1a_hello << std::endl;
    std::cout << "   fnv1a(\"world\") = " << fnv1a_world << std::endl;
    std::cout << "   fnv1a(\"hello\") == fnv1a(\"hello\"): " << (fnv1a_hello == fnv1a_hello2 ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // DJB2 哈希
    std::cout << "2. DJB2 哈希:" << std::endl;
    std::cout << "   djb2(\"hello\") = " << djb2_hello << std::endl;
    std::cout << "   djb2(\"world\") = " << djb2_world << std::endl;
    std::cout << std::endl;

    // 其他哈希函数
    std::cout << "3. 其他哈希函数:" << std::endl;
    std::cout << "   sdbm(\"hello\") = " << sdbm_hello << std::endl;
    std::cout << "   bkdr(\"hello\") = " << bkdr_hello << std::endl;
    std::cout << std::endl;

    // 整数哈希
    std::cout << "4. 整数哈希:" << std::endl;
    std::cout << "   integer_hash(0) = " << int_hash_0 << std::endl;
    std::cout << "   integer_hash(1) = " << int_hash_1 << std::endl;
    std::cout << "   integer_hash(42) = " << int_hash_42 << std::endl;
    std::cout << "   integer_hash(100) = " << int_hash_100 << std::endl;
    std::cout << std::endl;

    // 通用哈希
    std::cout << "5. 通用哈希:" << std::endl;
    std::cout << "   hash<int>(42) = " << hash_int_42 << std::endl;
    std::cout << "   hash<double>(3.14) = " << hash_double_314 << std::endl;
    std::cout << "   hash<bool>(true) = " << hash_true << std::endl;
    std::cout << "   hash<bool>(false) = " << hash_false << std::endl;
    std::cout << std::endl;

    // 用户定义字面量
    std::cout << "6. 用户定义字面量:" << std::endl;
    std::cout << "   \"hello\"_hash = " << hash_hello << std::endl;
    std::cout << "   \"world\"_hash = " << hash_world << std::endl;
    std::cout << std::endl;

    // 哈希组合
    std::cout << "7. 哈希组合:" << std::endl;
    std::cout << "   combine(fnv1a(\"hello\"), fnv1a(\"world\")) = " << combined_hash << std::endl;
    std::cout << std::endl;

    // 编译期哈希集合
    std::cout << "8. 编译期哈希集合:" << std::endl;
    compile_time_hash_set<10> set;
    set.insert("hello");
    set.insert("world");
    set.insert("foo");
    std::cout << "   set.contains(\"hello\"): " << (set.contains("hello") ? "true" : "false") << std::endl;
    std::cout << "   set.contains(\"world\"): " << (set.contains("world") ? "true" : "false") << std::endl;
    std::cout << "   set.contains(\"bar\"): " << (set.contains("bar") ? "true" : "false") << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
