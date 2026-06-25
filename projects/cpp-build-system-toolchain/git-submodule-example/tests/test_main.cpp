#include <gtest/gtest.h>

/**
 * @file test_main.cpp
 * @brief Git Submodule 测试示例
 */

TEST(SubmoduleTest, BasicAssertion) {
    EXPECT_EQ(1 + 1, 2);
    EXPECT_TRUE(true);
}

TEST(SubmoduleTest, StringAssertion) {
    std::string hello = "Hello";
    EXPECT_EQ(hello.size(), 5);
    EXPECT_STREQ(hello.c_str(), "Hello");
}
