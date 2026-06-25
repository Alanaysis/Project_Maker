/**
 * @file fixture_test.cpp
 * @brief Google Test 测试夹具示例
 * @details 展示如何使用测试夹具（Test Fixture）
 */

#include <gtest/gtest.h>
#include <string>
#include <vector>

/**
 * @brief 测试夹具类
 * @details 提供共享的测试数据和设置
 */
class VectorTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 测试前的设置
        vec = {1, 2, 3, 4, 5};
    }

    void TearDown() override {
        // 测试后的清理
        vec.clear();
    }

    std::vector<int> vec;
};

/**
 * @brief 使用测试夹具的测试
 * @details 使用 TEST_F 宏定义测试
 */
TEST_F(VectorTest, Size) {
    EXPECT_EQ(vec.size(), 5);
    EXPECT_FALSE(vec.empty());
}

TEST_F(VectorTest, ElementAccess) {
    EXPECT_EQ(vec.front(), 1);
    EXPECT_EQ(vec.back(), 5);
    EXPECT_EQ(vec[2], 3);
}

TEST_F(VectorTest, Modification) {
    vec.push_back(6);
    EXPECT_EQ(vec.size(), 6);
    EXPECT_EQ(vec.back(), 6);
}

TEST_F(VectorTest, Find) {
    auto it = std::find(vec.begin(), vec.end(), 3);
    EXPECT_NE(it, vec.end());
    EXPECT_EQ(*it, 3);

    it = std::find(vec.begin(), vec.end(), 6);
    EXPECT_EQ(it, vec.end());
}

/**
 * @brief 带参数的测试夹具
 * @details 展示参数化的测试夹具
 */
class MathTest : public ::testing::TestWithParam<int> {
protected:
    int GetValue() const { return GetParam(); }
};

TEST_P(MathTest, Positive) {
    EXPECT_GT(GetValue(), 0);
}

TEST_P(MathTest, LessThan100) {
    EXPECT_LT(GetValue(), 100);
}

INSTANTIATE_TEST_SUITE_P(
    IntegerValues,
    MathTest,
    ::testing::Values(1, 2, 3, 4, 5)
);

/**
 * @brief 字符串测试夹具
 * @details 展示字符串相关的测试夹具
 */
class StringTest : public ::testing::Test {
protected:
    void SetUp() override {
        str = "Hello, World!";
    }

    std::string str;
};

TEST_F(StringTest, Length) {
    EXPECT_EQ(str.length(), 13);
}

TEST_F(StringTest, Substring) {
    EXPECT_EQ(str.substr(0, 5), "Hello");
}

TEST_F(StringTest, Find) {
    EXPECT_NE(str.find("World"), std::string::npos);
    EXPECT_EQ(str.find("Foo"), std::string::npos);
}

TEST_F(StringTest, Modification) {
    str += "!!!";
    EXPECT_EQ(str, "Hello, World!!!");
}