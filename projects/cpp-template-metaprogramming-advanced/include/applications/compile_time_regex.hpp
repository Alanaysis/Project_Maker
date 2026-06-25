#pragma once
/**
 * @file compile_time_regex.hpp
 * @brief 编译期正则表达式
 *
 * 使用模板元编程实现简单的编译期正则表达式匹配器。
 * 支持基本的正则语法：字符、通配符、量词等。
 *
 * 核心特性：
 *   - 编译期模式匹配
 *   - 零运行时开销
 *   - 类型安全
 *
 * 支持的语法：
 *   - 普通字符
 *   - . (任意字符)
 *   - * (零个或多个)
 *   - + (一个或多个)
 *   - ? (零个或一个)
 *   - [abc] (字符类)
 *   - [a-z] (字符范围)
 */

#include <cstddef>
#include <string_view>
#include <type_traits>
#include <array>
#include <iostream>

namespace tmp {
namespace regex {

// ============================================================================
// 1. 基本模式元素
// ============================================================================

/**
 * @brief 字面字符匹配
 */
template <char C>
struct Char {
    static constexpr bool match(char c) { return c == C; }
    static constexpr const char pattern[] = {C, '\0'};
};

/**
 * @brief 任意字符匹配 (.)
 */
struct Any {
    static constexpr bool match(char) { return true; }
    static constexpr const char pattern[] = {'.', '\0'};
};

/**
 * @brief 字符范围匹配 [a-z]
 */
template <char Low, char High>
struct CharRange {
    static constexpr bool match(char c) { return c >= Low && c <= High; }
};

/**
 * @brief 字符类匹配 [abc]
 */
template <char... Chars>
struct CharClass {
    static constexpr bool match(char c) { return ((c == Chars) || ...); }
};

/**
 * @brief 否定字符类 [^abc]
 */
template <char... Chars>
struct NegCharClass {
    static constexpr bool match(char c) { return ((c != Chars) && ...); }
};

// ============================================================================
// 2. 量词
// ============================================================================

/**
 * @brief 零个或多个 (*)
 */
template <typename Pattern>
struct ZeroOrMore {
    static constexpr bool match(const char* str, std::size_t len) {
        // 匹配零个
        if (len == 0) return true;
        // 尝试匹配一个或多个
        for (std::size_t i = 0; i <= len; ++i) {
            if (Pattern::match(str[0]) &&
                (i == 0 || ZeroOrMore<Pattern>::match(str + 1, len - 1))) {
                return true;
            }
        }
        return false;
    }
};

/**
 * @brief 一个或多个 (+)
 */
template <typename Pattern>
struct OneOrMore {
    static constexpr bool match(const char* str, std::size_t len) {
        if (len == 0) return false;
        if (!Pattern::match(str[0])) return false;
        return ZeroOrMore<Pattern>::match(str + 1, len - 1);
    }
};

/**
 * @brief 零个或一个 (?)
 */
template <typename Pattern>
struct Optional {
    static constexpr bool match(const char* str, std::size_t len) {
        // 匹配零个
        if (len == 0) return true;
        // 匹配一个
        if (Pattern::match(str[0])) return true;
        return false;
    }
};

// ============================================================================
// 3. 序列和选择
// ============================================================================

/**
 * @brief 序列匹配 - 按顺序匹配多个模式
 */
template <typename... Patterns>
struct Sequence;

// 基础情况：空序列
template <>
struct Sequence<> {
    static constexpr bool match(const char*, std::size_t len) {
        return len == 0;
    }
};

// 递归情况
template <typename First, typename... Rest>
struct Sequence<First, Rest...> {
    static constexpr bool match(const char* str, std::size_t len) {
        if (len == 0) return Sequence<Rest...>::match(str, 0);
        if (!First::match(str[0])) return false;
        return Sequence<Rest...>::match(str + 1, len - 1);
    }
};

/**
 * @brief 选择匹配 - 匹配任一模式
 */
template <typename... Patterns>
struct Choice;

template <typename Pattern>
struct Choice<Pattern> {
    static constexpr bool match(const char* str, std::size_t len) {
        return Pattern::match(str, len);
    }
};

template <typename First, typename... Rest>
struct Choice<First, Rest...> {
    static constexpr bool match(const char* str, std::size_t len) {
        return First::match(str, len) || Choice<Rest...>::match(str, len);
    }
};

// ============================================================================
// 4. 锚点
// ============================================================================

/**
 * @brief 字符串开始锚点 (^)
 */
struct StartAnchor {
    static constexpr bool match(const char*, std::size_t, std::size_t pos) {
        return pos == 0;
    }
};

/**
 * @brief 字符串结束锚点 ($)
 */
struct EndAnchor {
    static constexpr bool match(const char*, std::size_t len, std::size_t pos) {
        return pos == len;
    }
};

// ============================================================================
// 5. 编译期正则表达式引擎
// ============================================================================

/**
 * @brief 编译期正则匹配
 * @tparam Pattern 模式类型
 * @param str 待匹配字符串
 * @return 是否匹配
 */
template <typename Pattern>
constexpr bool matches(const char* str, std::size_t len) {
    // 尝试从每个位置开始匹配
    for (std::size_t i = 0; i <= len; ++i) {
        if (Pattern::match(str + i, len - i)) {
            return true;
        }
    }
    return false;
}

/**
 * @brief 完全匹配（整个字符串）
 */
template <typename Pattern>
constexpr bool full_match(const char* str, std::size_t len) {
    return Pattern::match(str, len);
}

// ============================================================================
// 6. 简化的模式语法（使用字符串字面量）
// ============================================================================

/**
 * @brief 编译期字符串视图
 */
template <std::size_t N>
struct FixedString {
    char data[N]{};
    std::size_t size = N - 1;

    constexpr FixedString(const char (&str)[N]) {
        for (std::size_t i = 0; i < N; ++i) {
            data[i] = str[i];
        }
    }

    constexpr char operator[](std::size_t i) const { return data[i]; }
};

/**
 * @brief 编译期模式解析器
 */
template <FixedString Pattern>
struct PatternParser {
    static constexpr std::size_t length = Pattern.size;

    /**
     * @brief 检查字符是否为特殊字符
     */
    static constexpr bool is_special(char c) {
        return c == '.' || c == '*' || c == '+' || c == '?' ||
               c == '[' || c == ']' || c == '^' || c == '$';
    }

    /**
     * @brief 检查是否匹配字面字符串
     */
    static constexpr bool match_literal(const char* str, std::size_t len) {
        if (len != length) return false;
        for (std::size_t i = 0; i < length; ++i) {
            if (Pattern[i] != '.' && Pattern[i] != str[i]) {
                return false;
            }
        }
        return true;
    }
};

// ============================================================================
// 7. 编译期模式匹配（简化版）
// ============================================================================

/**
 * @brief 编译期字符串比较
 */
constexpr bool str_equal(const char* a, const char* b, std::size_t len) {
    for (std::size_t i = 0; i < len; ++i) {
        if (a[i] != b[i]) return false;
    }
    return true;
}

/**
 * @brief 编译期通配符匹配 (* 和 ?)
 */
constexpr bool wildcard_match(const char* str, std::size_t slen,
                               const char* pattern, std::size_t plen) {
    std::size_t si = 0, pi = 0;
    std::size_t star_pi = std::size_t(-1);
    std::size_t star_si = 0;

    while (si < slen) {
        if (pi < plen && (pattern[pi] == '?' || pattern[pi] == str[si])) {
            ++si;
            ++pi;
        } else if (pi < plen && pattern[pi] == '*') {
            star_pi = pi;
            star_si = si;
            ++pi;
        } else if (star_pi != std::size_t(-1)) {
            pi = star_pi + 1;
            ++star_si;
            si = star_si;
        } else {
            return false;
        }
    }

    while (pi < plen && pattern[pi] == '*') {
        ++pi;
    }

    return pi == plen;
}

// ============================================================================
// 8. 预定义模式
// ============================================================================

/// @brief 匹配数字 [0-9]+
struct Digits {
    static constexpr bool match(const char* str, std::size_t len) {
        if (len == 0) return false;
        for (std::size_t i = 0; i < len; ++i) {
            if (str[i] < '0' || str[i] > '9') return false;
        }
        return true;
    }
};

/// @brief 匹配字母 [a-zA-Z]+
struct Alpha {
    static constexpr bool match(const char* str, std::size_t len) {
        if (len == 0) return false;
        for (std::size_t i = 0; i < len; ++i) {
            char c = str[i];
            if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'))) {
                return false;
            }
        }
        return true;
    }
};

/// @brief 匹配字母数字 [a-zA-Z0-9]+
struct Alnum {
    static constexpr bool match(const char* str, std::size_t len) {
        if (len == 0) return false;
        for (std::size_t i = 0; i < len; ++i) {
            char c = str[i];
            if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                  (c >= '0' && c <= '9'))) {
                return false;
            }
        }
        return true;
    }
};

/// @brief 匹配十六进制 [0-9a-fA-F]+
struct HexDigits {
    static constexpr bool match(const char* str, std::size_t len) {
        if (len == 0) return false;
        for (std::size_t i = 0; i < len; ++i) {
            char c = str[i];
            if (!((c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') ||
                  (c >= 'A' && c <= 'F'))) {
                return false;
            }
        }
        return true;
    }
};

/// @brief 匹配空白字符
struct Whitespace {
    static constexpr bool match(const char* str, std::size_t len) {
        if (len == 0) return false;
        for (std::size_t i = 0; i < len; ++i) {
            if (str[i] != ' ' && str[i] != '\t' && str[i] != '\n' &&
                str[i] != '\r') {
                return false;
            }
        }
        return true;
    }
};

// ============================================================================
// 9. 编译期匹配验证
// ============================================================================

/// @brief 验证 IPv4 地址格式（简化版）
constexpr bool is_valid_ipv4(const char* str, std::size_t len) {
    std::size_t dots = 0;
    std::size_t num = 0;
    bool has_digit = false;

    for (std::size_t i = 0; i < len; ++i) {
        if (str[i] == '.') {
            if (!has_digit || num > 255) return false;
            ++dots;
            num = 0;
            has_digit = false;
        } else if (str[i] >= '0' && str[i] <= '9') {
            num = num * 10 + (str[i] - '0');
            has_digit = true;
        } else {
            return false;
        }
    }

    return has_digit && dots == 3 && num <= 255;
}

/// @brief 验证邮箱格式（简化版）
constexpr bool is_valid_email(const char* str, std::size_t len) {
    bool has_at = false;
    bool has_dot_after_at = false;
    std::size_t at_pos = 0;

    for (std::size_t i = 0; i < len; ++i) {
        if (str[i] == '@') {
            if (has_at || i == 0) return false;
            has_at = true;
            at_pos = i;
        } else if (str[i] == '.' && has_at && i > at_pos + 1) {
            has_dot_after_at = true;
        }
    }

    return has_at && has_dot_after_at && at_pos < len - 1;
}

}  // namespace regex
}  // namespace tmp
