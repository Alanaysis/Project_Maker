#include <gtest/gtest.h>
#include <fmt/format.h>

/**
 * @file test_main.cpp
 * @brief FetchContent 测试示例
 *
 * 使用 FetchContent 拉取的 Google Test 进行测试。
 */

TEST(FmtTest, FormatString) {
    EXPECT_EQ(fmt::format("Hello, {}!", "World"), "Hello, World!");
}

TEST(FmtTest, FormatNumber) {
    EXPECT_EQ(fmt::format("{}", 42), "42");
    EXPECT_EQ(fmt::format("{:.2f}", 3.14), "3.14");
}

TEST(FmtTest, FormatHex) {
    EXPECT_EQ(fmt::format("{:#x}", 255), "0xff");
}
