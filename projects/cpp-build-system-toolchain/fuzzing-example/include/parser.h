#ifndef PARSER_H
#define PARSER_H

#include <string>
#include <optional>

/**
 * @file parser.h
 * @brief 简单解析器头文件
 *
 * 用于演示模糊测试。
 */

namespace parser {
    // 解析整数
    std::optional<int> parse_int(const std::string& input);

    // 解析简单表达式 (如 "1+2")
    std::optional<double> parse_expression(const std::string& input);

    // 解析括号表达式 (如 "(1+2)*3")
    std::optional<double> parse_paren_expression(const std::string& input);

    // 验证括号匹配
    bool validate_parentheses(const std::string& input);
}

#endif
