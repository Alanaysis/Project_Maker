/**
 * @file basic_test.cpp
 * @brief Google Test 基础示例
 * @details 展示 Google Test 的基本用法
 *          包括断言、测试宏、测试套件等
 */

#include <gtest/gtest.h>
#include <string>
#include <vector>
#include <cmath>

/**
 * @brief 基础断言示例
 * @details 展示 EXPECT_* 和 ASSERT_* 宏的使用
 */
TEST(BasicAssertion, Equality) {
    // EXPECT_* 失败后继续执行
    EXPECT_EQ(1 + 1, 2);
    EXPECT_NE(1, 2);
    EXPECT_TRUE(true);
    EXPECT_FALSE(false);

    // 浮点数比较
    EXPECT_DOUBLE_EQ(3.14, 3.14);
    EXPECT_NEAR(3.14, 3.141, 0.01);
}

TEST(BasicAssertion, Comparison) {
    // 比较断言
    EXPECT_GT(5, 3);
    EXPECT_GE(5, 5);
    EXPECT_LT(3, 5);
    EXPECT_LE(3, 5);

    // 字符串比较
    std::string str = "Hello";
    EXPECT_EQ(str, "Hello");
    EXPECT_NE(str, "World");
}

/**
 * @brief 字符串测试示例
 * @details 展示字符串相关的测试
 */
TEST(StringTest, BasicOperations) {
    std::string str = "Hello, World!";

    // 长度测试
    EXPECT_EQ(str.length(), 13);

    // 子串测试
    EXPECT_EQ(str.substr(0, 5), "Hello");

    // 查找测试
    EXPECT_NE(str.find("World"), std::string::npos);
    EXPECT_EQ(str.find("Foo"), std::string::npos);
}

TEST(StringTest, Modification) {
    std::string str = "Hello";

    // 追加
    str += " World";
    EXPECT_EQ(str, "Hello World");

    // 替换
    str.replace(6, 5, "C++");
    EXPECT_EQ(str, "Hello C++");
}

/**
 * @brief 容器测试示例
 * @details 展示容器相关的测试
 */
TEST(ContainerTest, Vector) {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    // 大小测试
    EXPECT_EQ(vec.size(), 5);
    EXPECT_FALSE(vec.empty());

    // 元素访问
    EXPECT_EQ(vec.front(), 1);
    EXPECT_EQ(vec.back(), 5);
    EXPECT_EQ(vec[2], 3);

    // 修改
    vec.push_back(6);
    EXPECT_EQ(vec.size(), 6);
    EXPECT_EQ(vec.back(), 6);
}

TEST(ContainerTest, Search) {
    std::vector<int> vec = {1, 2, 3, 4, 5};

    // 查找
    auto it = std::find(vec.begin(), vec.end(), 3);
    EXPECT_NE(it, vec.end());
    EXPECT_EQ(*it, 3);

    // 计数
    EXPECT_EQ(std::count(vec.begin(), vec.end(), 3), 1);
    EXPECT_EQ(std::count(vec.begin(), vec.end(), 6), 0);
}

/**
 * @brief 异常测试示例
 * @details 展示异常相关的测试
 */
TEST(ExceptionTest, ThrowException) {
    // 测试是否抛出异常
    EXPECT_THROW({
        throw std::runtime_error("Test error");
    }, std::runtime_error);

    // 测试是否不抛出异常
    EXPECT_NO_THROW({
        int x = 1 + 1;
        (void)x;
    });

    // 测试任意异常
    EXPECT_ANY_THROW({
        throw 42;
    });
}

/**
 * @brief 类型测试示例
 * @details 展示类型相关的测试
 */
TEST(TypeTest, TypeChecks) {
    // 类型检查
    EXPECT_TRUE((std::is_same<int, int>::value));
    EXPECT_FALSE((std::is_same<int, float>::value));

    // 类型特性
    EXPECT_TRUE(std::is_integral<int>::value);
    EXPECT_FALSE(std::is_integral<double>::value);
    EXPECT_TRUE(std::is_floating_point<double>::value);
}

/**
 * @brief 死亡测试示例
 * @details 展示死亡测试的使用
 *          注意：死亡测试在某些平台上可能不可用
 */
// TEST(DeathTest, Abort) {
//     EXPECT_DEATH({
//         abort();
//     }, "");
// }

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}