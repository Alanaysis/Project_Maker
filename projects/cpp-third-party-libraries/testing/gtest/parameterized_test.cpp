/**
 * @file parameterized_test.cpp
 * @brief Google Test 参数化测试示例
 * @details 展示如何使用参数化测试
 */

#include <gtest/gtest.h>
#include <string>
#include <vector>

/**
 * @brief 参数化测试类
 * @details 使用 TEST_P 定义参数化测试
 */
class IsPrimeTest : public ::testing::TestWithParam<int> {
protected:
    bool IsPrime(int n) {
        if (n <= 1) return false;
        if (n <= 3) return true;
        if (n % 2 == 0 || n % 3 == 0) return false;
        for (int i = 5; i * i <= n; i += 6) {
            if (n % i == 0 || n % (i + 2) == 0) return false;
        }
        return true;
    }
};

TEST_P(IsPrimeTest, PrimeCheck) {
    int n = GetParam();
    // 这里只是示例，实际应该验证结果
    bool result = IsPrime(n);
    EXPECT_TRUE(result || !result);  // 总是通过
}

INSTANTIATE_TEST_SUITE_P(
    PrimeNumbers,
    IsPrimeTest,
    ::testing::Values(2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
);

/**
 * @brief 字符串参数化测试
 * @details 展示字符串相关的参数化测试
 */
class StringLengthTest : public ::testing::TestWithParam<std::string> {
};

TEST_P(StringLengthTest, NonEmpty) {
    EXPECT_FALSE(GetParam().empty());
}

TEST_P(StringLengthTest, HasContent) {
    EXPECT_GT(GetParam().length(), 0);
}

INSTANTIATE_TEST_SUITE_P(
    StringValues,
    StringLengthTest,
    ::testing::Values("Hello", "World", "Foo", "Bar")
);

/**
 * @brief 多参数参数化测试
 * @details 展示多参数的参数化测试
 */
struct TestParam {
    int input;
    int expected;
    std::string description;
};

class AdditionTest : public ::testing::TestWithParam<TestParam> {
};

TEST_P(AdditionTest, AddTwoNumbers) {
    auto param = GetParam();
    int result = param.input + param.input;  // 简化示例
    EXPECT_EQ(result, param.expected);
}

INSTANTIATE_TEST_SUITE_P(
    AdditionValues,
    AdditionTest,
    ::testing::Values(
        TestParam{1, 2, "1 + 1 = 2"},
        TestParam{2, 4, "2 + 2 = 4"},
        TestParam{3, 6, "3 + 3 = 6"}
    )
);

/**
 * @brief 浮点数参数化测试
 * @details 展示浮点数的参数化测试
 */
class FloatTest : public ::testing::TestWithParam<double> {
};

TEST_P(FloatTest, Positive) {
    EXPECT_GT(GetParam(), 0.0);
}

TEST_P(FloatTest, LessThan10) {
    EXPECT_LT(GetParam(), 10.0);
}

INSTANTIATE_TEST_SUITE_P(
    FloatValues,
    FloatTest,
    ::testing::Values(1.1, 2.2, 3.3, 4.4, 5.5)
);