#include <gtest/gtest.h>
#include "mylib/core.h"

TEST(StringUtilsTest, ToUpper) {
    EXPECT_EQ(mylib::StringUtils::to_upper("hello"), "HELLO");
    EXPECT_EQ(mylib::StringUtils::to_upper(""), "");
}

TEST(StringUtilsTest, ToLower) {
    EXPECT_EQ(mylib::StringUtils::to_lower("HELLO"), "hello");
    EXPECT_EQ(mylib::StringUtils::to_lower(""), "");
}

TEST(StringUtilsTest, Trim) {
    EXPECT_EQ(mylib::StringUtils::trim("  hello  "), "hello");
    EXPECT_EQ(mylib::StringUtils::trim(""), "");
}

TEST(StringUtilsTest, Split) {
    auto result = mylib::StringUtils::split("a,b,c", ',');
    ASSERT_EQ(result.size(), 3);
    EXPECT_EQ(result[0], "a");
    EXPECT_EQ(result[1], "b");
    EXPECT_EQ(result[2], "c");
}

TEST(StringUtilsTest, Join) {
    std::vector<std::string> parts = {"a", "b", "c"};
    EXPECT_EQ(mylib::StringUtils::join(parts, ","), "a,b,c");
}
