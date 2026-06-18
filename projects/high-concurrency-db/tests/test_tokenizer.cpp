// Tokenizer 单元测试
// 当没有 Google Test 时，使用 simple_test.cpp 中的测试

#include <iostream>
#include <cassert>
#include <string>
#include <vector>

#include "sql/tokenizer.h"

using namespace minidb;

// 如果使用 Google Test，取消注释以下代码
// #include <gtest/gtest.h>
//
// TEST(TokenizerTest, BasicSQL) {
//     Tokenizer tokenizer("SELECT * FROM users WHERE id = 1");
//     auto tokens = tokenizer.tokenize();
//     ASSERT_GE(tokens.size(), 7);
//     EXPECT_EQ(tokens[0].type, TokenType::SELECT);
//     EXPECT_EQ(tokens[1].type, TokenType::STAR);
//     EXPECT_EQ(tokens[2].type, TokenType::FROM);
//     EXPECT_EQ(tokens[3].type, TokenType::IDENTIFIER);
//     EXPECT_EQ(tokens[3].value, "users");
// }
