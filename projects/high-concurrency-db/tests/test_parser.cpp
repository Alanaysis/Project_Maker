// Parser 单元测试
// 当没有 Google Test 时，使用 simple_test.cpp 中的测试

#include <iostream>
#include <cassert>
#include <memory>

#include "sql/parser.h"
#include "sql/ast.h"

using namespace minidb;

// 如果使用 Google Test，取消注释以下代码
// #include <gtest/gtest.h>
//
// TEST(ParserTest, CreateTable) {
//     Parser parser("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))");
//     auto stmt = parser.parse();
//     ASSERT_NE(stmt, nullptr);
//     EXPECT_EQ(stmt->type(), StatementType::CREATE_TABLE);
// }
