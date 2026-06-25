#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "calculator.h"

/**
 * @file test_calculator_advanced.cpp
 * @brief Google Test 高级测试示例
 *
 * 演示 Google Test 的高级用法:
 * - 异常测试
 * - 浮点数比较
 * - 自定义断言
 * - 类型参数化测试
 */

// ============================================================================
// 1. 异常测试
// ============================================================================
TEST(CalculatorExceptionTest, DivisionByZero) {
    Calculator calc;
    EXPECT_THROW(calc.divide(1.0, 0.0), std::invalid_argument);
}

TEST(CalculatorExceptionTest, SqrtOfNegative) {
    Calculator calc;
    EXPECT_THROW(calc.sqrt(-1.0), std::invalid_argument);
}

TEST(CalculatorExceptionTest, FactorialOfNegative) {
    Calculator calc;
    EXPECT_THROW(calc.factorial(-1), std::invalid_argument);
}

TEST(CalculatorExceptionTest, NoException) {
    Calculator calc;
    EXPECT_NO_THROW(calc.add(1.0, 2.0));
}

// ============================================================================
// 2. 浮点数比较
// ============================================================================
TEST(CalculatorFloatTest, Power) {
    Calculator calc;

    // 使用 EXPECT_NEAR 处理浮点数精度
    EXPECT_NEAR(calc.power(2.0, 10), 1024.0, 1e-10);
    EXPECT_NEAR(calc.power(3.0, 3), 27.0, 1e-10);
    EXPECT_NEAR(calc.power(2.0, 0), 1.0, 1e-10);
}

TEST(CalculatorFloatTest, Sqrt) {
    Calculator calc;

    EXPECT_NEAR(calc.sqrt(4.0), 2.0, 1e-10);
    EXPECT_NEAR(calc.sqrt(9.0), 3.0, 1e-10);
    EXPECT_NEAR(calc.sqrt(2.0), 1.4142135623730951, 1e-10);
}

TEST(CalculatorFloatTest, Factorial) {
    Calculator calc;

    EXPECT_DOUBLE_EQ(calc.factorial(0), 1.0);
    EXPECT_DOUBLE_EQ(calc.factorial(1), 1.0);
    EXPECT_DOUBLE_EQ(calc.factorial(5), 120.0);
    EXPECT_DOUBLE_EQ(calc.factorial(10), 3628800.0);
}

// ============================================================================
// 3. 自定义断言
// ============================================================================
::testing::AssertionResult IsPositive(double value) {
    if (value > 0) {
        return ::testing::AssertionSuccess();
    }
    return ::testing::AssertionFailure() << value << " is not positive";
}

TEST(CalculatorCustomTest, ResultIsPositive) {
    Calculator calc;
    calc.add(5.0, 3.0);
    EXPECT_TRUE(IsPositive(calc.get_result()));
}

// ============================================================================
// 4. 测试套件组织
// ============================================================================
class CalculatorAdvancedTest : public ::testing::Test {
protected:
    Calculator calc;
};

TEST_F(CalculatorAdvancedTest, ChainedOperations) {
    calc.add(1.0, 2.0);
    EXPECT_DOUBLE_EQ(calc.get_result(), 3.0);

    calc.multiply(calc.get_result(), 4.0);
    EXPECT_DOUBLE_EQ(calc.get_result(), 12.0);

    calc.subtract(calc.get_result(), 2.0);
    EXPECT_DOUBLE_EQ(calc.get_result(), 10.0);
}

TEST_F(CalculatorAdvancedTest, MultipleCalculators) {
    Calculator calc1, calc2;

    calc1.add(1.0, 2.0);
    calc2.add(3.0, 4.0);

    EXPECT_DOUBLE_EQ(calc1.get_result(), 3.0);
    EXPECT_DOUBLE_EQ(calc2.get_result(), 7.0);
}
