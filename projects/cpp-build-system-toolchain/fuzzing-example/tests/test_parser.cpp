#include <gtest/gtest.h>
#include "parser.h"

/**
 * @file test_parser.cpp
 * @brief 解析器单元测试
 */

TEST(ParserTest, ParseInt) {
    EXPECT_EQ(parser::parse_int("42").value(), 42);
    EXPECT_EQ(parser::parse_int("-10").value(), -10);
    EXPECT_EQ(parser::parse_int("+5").value(), 5);
    EXPECT_FALSE(parser::parse_int("").has_value());
    EXPECT_FALSE(parser::parse_int("abc").has_value());
}

TEST(ParserTest, ParseExpression) {
    EXPECT_DOUBLE_EQ(parser::parse_expression("1+2").value(), 3.0);
    EXPECT_DOUBLE_EQ(parser::parse_expression("10-3").value(), 7.0);
    EXPECT_DOUBLE_EQ(parser::parse_expression("4*5").value(), 20.0);
    EXPECT_DOUBLE_EQ(parser::parse_expression("10/2").value(), 5.0);
    EXPECT_FALSE(parser::parse_expression("10/0").has_value());
}

TEST(ParserTest, ValidateParentheses) {
    EXPECT_TRUE(parser::validate_parentheses("(hello)"));
    EXPECT_TRUE(parser::validate_parentheses("((a+b))"));
    EXPECT_TRUE(parser::validate_parentheses(""));
    EXPECT_FALSE(parser::validate_parentheses("(hello"));
    EXPECT_FALSE(parser::validate_parentheses("hello)"));
    EXPECT_FALSE(parser::validate_parentheses(")("));
}
