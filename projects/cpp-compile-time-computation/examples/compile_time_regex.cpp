// compile_time_regex.cpp - 编译期正则表达式匹配示例
//
// 本文件展示编译期正则表达式匹配的用法，包括：
//   1. 基本字符匹配
//   2. 通配符匹配
//   3. 量词匹配
//   4. 字符类匹配
//
// 编译命令：
//   g++ -std=c++20 -I include examples/compile_time_regex.cpp -o compile_time_regex

#include <iostream>
#include "compile_time/regex.hpp"

using namespace compile_time::regex;

// ============================================================================
// 第一部分：基本字符匹配
// ============================================================================

// 精确匹配
constexpr bool match_hello = match("hello", "hello");
constexpr bool match_world = match("world", "world");
constexpr bool match_no = match("hello", "world");

// ============================================================================
// 第二部分：通配符匹配
// ============================================================================

// . 匹配任意字符
constexpr bool match_dot = match("hello", "h.llo");
constexpr bool match_dot2 = match("hello", "h...o");
constexpr bool match_dot3 = match("hello", ".....");

// ============================================================================
// 第三部分：量词匹配
// ============================================================================

// * 匹配零个或多个
constexpr bool match_star = match("aaa", "a*");
constexpr bool match_star2 = match("", "a*");
constexpr bool match_star3 = match("aab", "a*b");

// + 匹配一个或多个
constexpr bool match_plus = match("aaa", "a+");
constexpr bool match_plus2 = match("a", "a+");
constexpr bool match_plus3 = match("", "a+");

// ? 匹配零个或一个
constexpr bool match_question = match("ab", "a?b");
constexpr bool match_question2 = match("b", "a?b");
constexpr bool match_question3 = match("aab", "a?b");

// ============================================================================
// 第四部分：锚点匹配
// ============================================================================

// ^ 匹配开头
constexpr bool match_start = match("hello", "^he");
constexpr bool match_start2 = match("hello", "^lo");

// $ 匹配结尾
constexpr bool match_end = match("hello", "lo$");
constexpr bool match_end2 = match("hello", "he$");

// ============================================================================
// 第五部分：字符类匹配
// ============================================================================

// [abc] 匹配字符集合
constexpr bool match_class = match("a", "[abc]");
constexpr bool match_class2 = match("d", "[abc]");
constexpr bool match_class3 = match("hello", "h[aeiou]llo");

// [^abc] 匹配不在字符集合中
constexpr bool match_neg_class = match("d", "[^abc]");
constexpr bool match_neg_class2 = match("a", "[^abc]");

// [a-z] 匹配范围
constexpr bool match_range = match("a", "[a-z]");
constexpr bool match_range2 = match("A", "[a-z]");
constexpr bool match_range3 = match("5", "[0-9]");

// ============================================================================
// 第六部分：实际应用示例
// ============================================================================

// 验证邮箱格式（简化版）
constexpr bool is_valid_email(const char* email) {
    // 简化版：检查是否包含 @ 和 .
    bool has_at = false;
    bool has_dot = false;
    const char* p = email;
    while (*p) {
        if (*p == '@') has_at = true;
        if (*p == '.' && has_at) has_dot = true;
        ++p;
    }
    return has_at && has_dot;
}

// 验证 URL 格式（简化版）
constexpr bool is_valid_url(const char* url) {
    return match(url, "http.*://.*");
}

// 验证电话号码格式（简化版）
constexpr bool is_valid_phone(const char* phone) {
    return match(phone, "[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]");
}

// ============================================================================
// 第七部分：编译期断言验证
// ============================================================================

// 精确匹配
static_assert(match_hello == true);
static_assert(match_world == true);
static_assert(match_no == false);

// 通配符
static_assert(match_dot == true);
static_assert(match_dot2 == true);
static_assert(match_dot3 == true);

// 量词
static_assert(match_star == true);
static_assert(match_star2 == true);
static_assert(match_star3 == true);
static_assert(match_plus == true);
static_assert(match_plus2 == true);
static_assert(match_plus3 == false);
static_assert(match_question == true);
static_assert(match_question2 == true);

// 锚点
static_assert(match_start == true);
static_assert(match_start2 == false);
static_assert(match_end == true);
static_assert(match_end2 == false);

// 字符类
static_assert(match_class == true);
static_assert(match_class2 == false);
static_assert(match_neg_class == true);
static_assert(match_neg_class2 == false);

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期正则表达式匹配示例 ===" << std::endl;
    std::cout << std::endl;

    // 精确匹配
    std::cout << "1. 精确匹配:" << std::endl;
    std::cout << "   match(\"hello\", \"hello\") = " << (match_hello ? "true" : "false") << std::endl;
    std::cout << "   match(\"hello\", \"world\") = " << (match_no ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 通配符
    std::cout << "2. 通配符匹配:" << std::endl;
    std::cout << "   match(\"hello\", \"h.llo\") = " << (match_dot ? "true" : "false") << std::endl;
    std::cout << "   match(\"hello\", \"h...o\") = " << (match_dot2 ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 量词
    std::cout << "3. 量词匹配:" << std::endl;
    std::cout << "   match(\"aaa\", \"a*\") = " << (match_star ? "true" : "false") << std::endl;
    std::cout << "   match(\"\", \"a*\") = " << (match_star2 ? "true" : "false") << std::endl;
    std::cout << "   match(\"aaa\", \"a+\") = " << (match_plus ? "true" : "false") << std::endl;
    std::cout << "   match(\"\", \"a+\") = " << (match_plus3 ? "true" : "false") << std::endl;
    std::cout << "   match(\"ab\", \"a?b\") = " << (match_question ? "true" : "false") << std::endl;
    std::cout << "   match(\"b\", \"a?b\") = " << (match_question2 ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 锚点
    std::cout << "4. 锚点匹配:" << std::endl;
    std::cout << "   match(\"hello\", \"^he\") = " << (match_start ? "true" : "false") << std::endl;
    std::cout << "   match(\"hello\", \"^lo\") = " << (match_start2 ? "true" : "false") << std::endl;
    std::cout << "   match(\"hello\", \"lo$\") = " << (match_end ? "true" : "false") << std::endl;
    std::cout << "   match(\"hello\", \"he$\") = " << (match_end2 ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 字符类
    std::cout << "5. 字符类匹配:" << std::endl;
    std::cout << "   match(\"a\", \"[abc]\") = " << (match_class ? "true" : "false") << std::endl;
    std::cout << "   match(\"d\", \"[abc]\") = " << (match_class2 ? "true" : "false") << std::endl;
    std::cout << "   match(\"d\", \"[^abc]\") = " << (match_neg_class ? "true" : "false") << std::endl;
    std::cout << "   match(\"a\", \"[^abc]\") = " << (match_neg_class2 ? "true" : "false") << std::endl;
    std::cout << std::endl;

    // 实际应用
    std::cout << "6. 实际应用:" << std::endl;
    std::cout << "   is_valid_email(\"user@example.com\") = " << (is_valid_email("user@example.com") ? "true" : "false") << std::endl;
    std::cout << "   is_valid_email(\"invalid-email\") = " << (is_valid_email("invalid-email") ? "true" : "false") << std::endl;
    std::cout << "   is_valid_url(\"https://example.com\") = " << (is_valid_url("https://example.com") ? "true" : "false") << std::endl;
    std::cout << "   is_valid_phone(\"123-4567-8901\") = " << (is_valid_phone("123-4567-8901") ? "true" : "false") << std::endl;

    std::cout << std::endl;
    std::cout << "所有编译期断言已通过！" << std::endl;

    return 0;
}
