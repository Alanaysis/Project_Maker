/**
 * @file compile_time_regex.cpp
 * @brief 编译期正则表达式示例
 */

#include <iostream>
#include <string_view>
#include "../include/applications/compile_time_regex.hpp"

int main() {
    using namespace tmp::regex;

    std::cout << "=== Compile-time Regex ===" << std::endl;
    std::cout << std::endl;

    // 1. 字符匹配
    std::cout << "--- 1. Character Matching ---" << std::endl;
    static_assert(Char<'a'>::match('a'));
    static_assert(!Char<'a'>::match('b'));
    static_assert(Any::match('x'));
    static_assert(Any::match('5'));
    std::cout << "Char<'a'> matches 'a': " << Char<'a'>::match('a') << std::endl;
    std::cout << "Any matches 'x': " << Any::match('x') << std::endl;
    std::cout << std::endl;

    // 2. 字符范围
    std::cout << "--- 2. Character Ranges ---" << std::endl;
    static_assert(CharRange<'a','z'>::match('m'));
    static_assert(!CharRange<'a','z'>::match('A'));
    static_assert(CharRange<'0','9'>::match('5'));
    std::cout << "['a'-'z'] matches 'm': " << CharRange<'a','z'>::match('m') << std::endl;
    std::cout << "['0'-'9'] matches '5': " << CharRange<'0','9'>::match('5') << std::endl;
    std::cout << std::endl;

    // 3. 预定义模式
    std::cout << "--- 3. Predefined Patterns ---" << std::endl;
    static_assert(Digits::match("12345", 5));
    static_assert(!Digits::match("123a5", 5));
    static_assert(Alpha::match("hello", 5));
    static_assert(!Alpha::match("hel1o", 5));
    static_assert(Alnum::match("hello123", 8));
    static_assert(HexDigits::match("1a2B3c", 6));

    std::cout << "Digits('12345'): " << Digits::match("12345", 5) << std::endl;
    std::cout << "Digits('123a5'): " << Digits::match("123a5", 5) << std::endl;
    std::cout << "Alpha('hello'): " << Alpha::match("hello", 5) << std::endl;
    std::cout << "Alnum('hello123'): " << Alnum::match("hello123", 8) << std::endl;
    std::cout << "HexDigits('1a2B3c'): " << HexDigits::match("1a2B3c", 6) << std::endl;
    std::cout << std::endl;

    // 4. 通配符匹配
    std::cout << "--- 4. Wildcard Matching ---" << std::endl;
    static_assert(wildcard_match("hello", 5, "hello", 5));
    static_assert(wildcard_match("hello", 5, "h*o", 3));
    static_assert(wildcard_match("hello", 5, "h?llo", 5));
    static_assert(!wildcard_match("hello", 5, "h?l", 3));
    static_assert(wildcard_match("hello", 5, "*", 1));
    static_assert(wildcard_match("hello", 5, "h*", 2));

    std::cout << "'hello' matches 'hello': " << wildcard_match("hello", 5, "hello", 5) << std::endl;
    std::cout << "'hello' matches 'h*o': " << wildcard_match("hello", 5, "h*o", 3) << std::endl;
    std::cout << "'hello' matches 'h?llo': " << wildcard_match("hello", 5, "h?llo", 5) << std::endl;
    std::cout << "'hello' matches 'h?l': " << wildcard_match("hello", 5, "h?l", 3) << std::endl;
    std::cout << std::endl;

    // 5. 验证函数
    std::cout << "--- 5. Validation Functions ---" << std::endl;

    // IPv4 验证
    static_assert(is_valid_ipv4("192.168.1.1", 11));
    static_assert(is_valid_ipv4("0.0.0.0", 7));
    static_assert(!is_valid_ipv4("256.1.1.1", 9));
    static_assert(!is_valid_ipv4("1.2.3", 5));

    std::cout << "IPv4 '192.168.1.1': " << is_valid_ipv4("192.168.1.1", 11) << std::endl;
    std::cout << "IPv4 '256.1.1.1': " << is_valid_ipv4("256.1.1.1", 9) << std::endl;
    std::cout << std::endl;

    // 邮箱验证
    static_assert(is_valid_email("test@example.com", 16));
    static_assert(!is_valid_email("invalid", 7));
    static_assert(!is_valid_email("@example.com", 12));

    std::cout << "Email 'test@example.com': " << is_valid_email("test@example.com", 16) << std::endl;
    std::cout << "Email 'invalid': " << is_valid_email("invalid", 7) << std::endl;
    std::cout << std::endl;

    std::cout << "All regex matching happens at compile time!" << std::endl;
    std::cout << "Zero runtime overhead for pattern validation." << std::endl;

    return 0;
}
