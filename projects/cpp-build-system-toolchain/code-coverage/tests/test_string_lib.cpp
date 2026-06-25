#include <gtest/gtest.h>
#include "string_lib.h"

/**
 * @file test_string_lib.cpp
 * @brief 代码覆盖率测试示例
 */

TEST(StringLibTest, Reverse) {
    EXPECT_EQ(str::reverse("hello"), "olleh");
    EXPECT_EQ(str::reverse(""), "");
    EXPECT_EQ(str::reverse("a"), "a");
    EXPECT_EQ(str::reverse("abba"), "abba");
}

TEST(StringLibTest, ToUpper) {
    EXPECT_EQ(str::to_upper("hello"), "HELLO");
    EXPECT_EQ(str::to_upper("Hello"), "HELLO");
    EXPECT_EQ(str::to_upper("HELLO"), "HELLO");
    EXPECT_EQ(str::to_upper(""), "");
}

TEST(StringLibTest, ToLower) {
    EXPECT_EQ(str::to_lower("HELLO"), "hello");
    EXPECT_EQ(str::to_lower("Hello"), "hello");
    EXPECT_EQ(str::to_lower("hello"), "hello");
    EXPECT_EQ(str::to_lower(""), "");
}

TEST(StringLibTest, Split) {
    auto result = str::split("a,b,c", ',');
    ASSERT_EQ(result.size(), 3);
    EXPECT_EQ(result[0], "a");
    EXPECT_EQ(result[1], "b");
    EXPECT_EQ(result[2], "c");

    auto single = str::split("hello", ',');
    ASSERT_EQ(single.size(), 1);
    EXPECT_EQ(single[0], "hello");

    auto empty = str::split("", ',');
    ASSERT_EQ(empty.size(), 1);
    EXPECT_EQ(empty[0], "");
}

TEST(StringLibTest, IsPalindrome) {
    EXPECT_TRUE(str::is_palindrome("racecar"));
    EXPECT_TRUE(str::is_palindrome("A man a plan a canal Panama"));
    EXPECT_TRUE(str::is_palindrome(""));
    EXPECT_TRUE(str::is_palindrome("a"));
    EXPECT_FALSE(str::is_palindrome("hello"));
    EXPECT_FALSE(str::is_palindrome("world"));
}

TEST(StringLibTest, CountWords) {
    EXPECT_EQ(str::count_words("hello world"), 2);
    EXPECT_EQ(str::count_words("one two three four five"), 5);
    EXPECT_EQ(str::count_words(""), 0);
    EXPECT_EQ(str::count_words("hello"), 1);
    EXPECT_EQ(str::count_words("  hello  world  "), 2);
}
