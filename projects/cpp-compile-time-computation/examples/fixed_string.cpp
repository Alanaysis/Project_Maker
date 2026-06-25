// fixed_string.cpp - 编译期字符串示例
//
// 本文件展示编译期字符串 fixed_string 的用法，包括：
//   1. 基本构造和访问
//   2. 字符串操作
//   3. 模板参数推导
//   4. 编译期字符串哈希
//
// 编译命令：
//   g++ -std=c++20 -I include examples/fixed_string.cpp -o fixed_string

#include <iostream>
#include "compile_time/fixed_string.hpp"

using compile_time::fixed_string;
using compile_time::operator+;

// ============================================================================
// 第一部分：基本构造和访问
// ============================================================================

// 使用字面量构造
constexpr fixed_string hello = "hello";
constexpr fixed_string world = "world";

// 访问字符
constexpr char first = hello[0];  // 'h'
constexpr char last = hello[4];   // 'o'

// 长度
constexpr std::size_t len = hello.size();  // 5
constexpr bool is_empty = hello.empty();   // false

// ============================================================================
// 第二部分：字符串操作
// ============================================================================

// 比较
constexpr bool eq = (hello == hello);  // true
constexpr bool ne = (hello != world);  // true
constexpr bool lt = (hello < world);   // true

// 查找
constexpr std::size_t pos = hello.find('l');  // 2
constexpr std::size_t not_found = hello.find('z');  // npos

// 前缀和后缀
constexpr bool starts = hello.starts_with(fixed_string("he"));  // true
constexpr bool ends = hello.ends_with(fixed_string("lo"));      // true

// ============================================================================
// 第三部分：模板参数推导（C++20）
// ============================================================================

// 使用 CTAD 推导
constexpr fixed_string s1 = "abc";  // fixed_string<4>
constexpr fixed_string s2 = "def";  // fixed_string<4>

// 字符串拼接
constexpr auto concatenated = s1 + s2;  // fixed_string<7>

// ============================================================================
// 第四部分：编译期字符串哈希
// ============================================================================

// FNV-1a 哈希
constexpr std::size_t hash1 = compile_time::string_hash(hello);
constexpr std::size_t hash2 = compile_time::string_hash(world);
constexpr std::size_t hash3 = compile_time::string_hash(hello);  // 相同字符串相同哈希

// ============================================================================
// 第五部分：实际应用示例
// ============================================================================

// 编译期字符串比较函数
template<std::size_t N, std::size_t M>
constexpr bool string_less(const fixed_string<N>& a, const fixed_string<M>& b) {
    return a < b;
}

// 编译期字符串包含检查
template<std::size_t N, std::size_t M>
constexpr bool contains(const fixed_string<N>& haystack, const fixed_string<M>& needle) {
    return haystack.find(needle) != fixed_string<N>::npos;
}

// 编译期字符串反转
template<std::size_t N>
constexpr auto reverse_string(const fixed_string<N>& str) {
    char buf[N]{};
    for (std::size_t i = 0; i < str.size(); ++i) {
        buf[i] = str[str.size() - 1 - i];
    }
    return fixed_string<N>(buf);
}

// 编译期字符串计数
template<std::size_t N>
constexpr std::size_t count_char(const fixed_string<N>& str, char c) {
    std::size_t count = 0;
    for (std::size_t i = 0; i < str.size(); ++i) {
        if (str[i] == c) ++count;
    }
    return count;
}

// ============================================================================
// 第六部分：编译期断言验证
// ============================================================================

// 基本构造和访问
static_assert(first == 'h');
static_assert(last == 'o');
static_assert(len == 5);
static_assert(is_empty == false);

// 比较
static_assert(eq == true);
static_assert(ne == true);
static_assert(lt == true);

// 查找
static_assert(pos == 2);
static_assert(not_found == fixed_string<6>::npos);

// 前缀和后缀
static_assert(starts == true);
static_assert(ends == true);

// 拼接
static_assert(concatenated.size() == 6);

// 哈希
static_assert(hash1 == hash3);  // 相同字符串相同哈希

// 实际应用
static_assert(string_less(hello, world) == true);
static_assert(contains(hello, fixed_string("ell")) == true);
static_assert(count_char(hello, 'l') == 2);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期字符串 fixed_string 示例 ===" << std::endl;
    std::cout << std::endl;

    // 基本构造和访问
    std::cout << "1. 基本构造和访问:" << std::endl;
    std::cout << "   hello = " << hello.c_str() << std::endl;
    std::cout << "   hello[0] = " << hello[0] << std::endl;
    std::cout << "   hello.size() = " << hello.size() << std::endl;
    std::cout << std::endl;

    // 字符串操作
    std::cout << "2. 字符串操作:" << std::endl;
    std::cout << "   hello == hello: " << (eq ? "true" : "false") << std::endl;
    std::cout << "   hello != world: " << (ne ? "true" : "false") << std::endl;
    std::cout << "   hello < world: " << (lt ? "true" : "false") << std::endl;
    std::cout << "   hello.find('l') = " << pos << std::endl;
    std::cout << "   hello.starts_with(\"he\"): " << (starts ? "true" : "false") << std::endl;
    std::cout << "   hello.ends_with(\"lo\"): " << (ends ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 拼接
    std::cout << "3. 字符串拼接:" << std::endl;
    std::cout << "   \"abc\" + \"def\" = " << concatenated.c_str() << std::endl;
    std::cout << "   拼接后长度 = " << concatenated.size() << std::endl;
    std::cout << std::endl;

    // 哈希
    std::cout << "4. 编译期字符串哈希:" << std::endl;
    std::cout << "   hash(hello) = " << hash1 << std::endl;
    std::cout << "   hash(world) = " << hash2 << std::endl;
    std::cout << "   hash(hello) == hash(hello): " << (hash1 == hash3 ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 实际应用
    std::cout << "5. 实际应用:" << std::endl;
    std::cout << "   contains(hello, \"ell\"): " << (contains(hello, fixed_string("ell")) ? "true" : "false") << std::endl;
    std::cout << "   count_char(hello, 'l') = " << count_char(hello, 'l') << std::endl;

    // 运行时使用
    std::cout << std::endl;
    std::cout << "6. 运行时使用:" << std::endl;
    std::cout << "   hello.c_str() = " << hello.c_str() << std::endl;
    std::cout << "   hello.length() = " << hello.length() << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
