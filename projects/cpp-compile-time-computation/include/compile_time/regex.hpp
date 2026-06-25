#pragma once
// regex.hpp - 编译期正则表达式匹配
//
// 实现简单的编译期正则表达式匹配器。
// 支持的语法：
//   - 普通字符：匹配字符本身
//   - .（点）：匹配任意字符
//   - *：匹配零个或多个前一个字符
//   - +：匹配一个或多个前一个字符
//   - ?：匹配零个或一个前一个字符
//   - ^：匹配字符串开头
//   - $：匹配字符串结尾
//   - [abc]：匹配字符集合中的任意一个
//   - [^abc]：匹配不在字符集合中的任意一个
//
// 使用示例：
//   constexpr bool match = ct_regex::match("hello", "h.llo");
//   constexpr bool match2 = ct_regex::match("aaa", "a*");

#include <cstddef>
#include "fixed_string.hpp"

namespace compile_time {
namespace regex {

namespace detail {

// 辅助函数：检查字符是否匹配
constexpr bool match_char(char pattern, char text) {
    return pattern == '.' || pattern == text;
}

// 辅助函数：检查字符是否在集合中
constexpr bool match_char_class(const char* pattern, char text, bool negated) {
    bool found = false;
    while (*pattern && *pattern != ']') {
        if (*pattern == text) {
            found = true;
        }
        ++pattern;
    }
    return negated ? !found : found;
}

// 辅助函数：跳过字符类
constexpr const char* skip_char_class(const char* pattern) {
    while (*pattern && *pattern != ']') {
        ++pattern;
    }
    if (*pattern == ']') ++pattern;
    return pattern;
}

// 递归匹配函数
constexpr bool match_here(const char* pattern, const char* text);

// 匹配星号
constexpr bool match_star(char c, const char* pattern, const char* text) {
    do {
        if (match_here(pattern, text)) return true;
    } while (*text != '\0' && (c == '.' || c == *text++));
    return false;
}

// 匹配加号
constexpr bool match_plus(char c, const char* pattern, const char* text) {
    if (*text == '\0' || (c != '.' && c != *text)) return false;
    ++text;
    do {
        if (match_here(pattern, text)) return true;
    } while (*text != '\0' && (c == '.' || c == *text++));
    return false;
}

// 匹配问号
constexpr bool match_question(char c, const char* pattern, const char* text) {
    if (match_here(pattern, text)) return true;
    if (*text != '\0' && (c == '.' || c == *text)) {
        return match_here(pattern, text + 1);
    }
    return false;
}

// 匹配字符类
constexpr bool match_char_class_here(const char** pattern_ptr, const char* text) {
    const char* pattern = *pattern_ptr;
    bool negated = false;

    if (*pattern == '^') {
        negated = true;
        ++pattern;
    }

    bool matched = false;
    const char* start = pattern;
    while (*pattern && *pattern != ']') {
        if (*pattern == '-' && pattern > start && *(pattern + 1) != ']') {
            // 范围匹配
            char low = *(pattern - 1);
            char high = *(pattern + 1);
            if (*text >= low && *text <= high) {
                matched = true;
            }
            pattern += 2;
        } else {
            if (*pattern == *text) {
                matched = true;
            }
            ++pattern;
        }
    }

    if (*pattern == ']') ++pattern;
    *pattern_ptr = pattern;

    return negated ? !matched : matched;
}

// 主匹配函数
constexpr bool match_here(const char* pattern, const char* text) {
    while (*pattern) {
        // 处理字符类
        if (*pattern == '[') {
            ++pattern;
            if (*text == '\0') return false;
            if (!match_char_class_here(&pattern, text)) return false;
            ++text;
            continue;
        }

        // 处理特殊字符
        if (*(pattern + 1) == '*') {
            return match_star(*pattern, pattern + 2, text);
        }
        if (*(pattern + 1) == '+') {
            return match_plus(*pattern, pattern + 2, text);
        }
        if (*(pattern + 1) == '?') {
            return match_question(*pattern, pattern + 2, text);
        }

        // 处理结尾
        if (*pattern == '$') {
            return *text == '\0';
        }

        // 匹配普通字符
        if (*text == '\0' || !match_char(*pattern, *text)) {
            return false;
        }

        ++pattern;
        ++text;
    }
    return *text == '\0';
}

} // namespace detail

// 匹配函数：检查整个字符串是否匹配模式
constexpr bool match(const char* text, const char* pattern) {
    // 处理 ^ 锚点（只匹配开头）
    if (*pattern == '^') {
        // 逐字符匹配，不要求完全匹配整个文本
        const char* p = pattern + 1;
        const char* t = text;
        while (*p && *t) {
            if (*p == '.') {
                // 通配符匹配任意字符
                ++p;
                ++t;
            } else if (*p == *t) {
                ++p;
                ++t;
            } else {
                return false;
            }
        }
        // 模式消耗完毕即为匹配成功
        return *p == '\0';
    }

    // 尝试在每个位置匹配
    do {
        if (detail::match_here(pattern, text)) return true;
    } while (*text++ != '\0');

    return false;
}

// 搜索函数：在字符串中搜索匹配的子串
constexpr bool search(const char* text, const char* pattern) {
    return match(text, pattern);
}

// 编译期匹配（使用 fixed_string）
template<std::size_t N, std::size_t M>
constexpr bool match(const fixed_string<N>& text, const fixed_string<M>& pattern) {
    return match(text.c_str(), pattern.c_str());
}

// 编译期匹配（使用字符串字面量）
template<std::size_t N, std::size_t M>
constexpr bool match(const char (&text)[N], const char (&pattern)[M]) {
    return match(text, pattern);
}

// 辅助函数：检查是否是有效的正则表达式
constexpr bool is_valid_pattern(const char* pattern) {
    int brackets = 0;
    while (*pattern) {
        if (*pattern == '[') ++brackets;
        if (*pattern == ']') --brackets;
        if (brackets < 0) return false;
        ++pattern;
    }
    return brackets == 0;
}

// 辅助函数：获取匹配的长度
constexpr std::size_t match_length(const char* text, const char* pattern) {
    if (*pattern == '^') {
        const char* start = text;
        if (detail::match_here(pattern + 1, text)) {
            return text - start;
        }
        return 0;
    }

    const char* original = text;
    do {
        const char* match_start = text;
        if (detail::match_here(pattern, text)) {
            return text - original;
        }
        text = match_start + 1;
    } while (*text != '\0');

    return 0;
}

} // namespace regex
} // namespace compile_time
