#include <gtest/gtest.h>
#include "calculator.h"

/**
 * @file test_calculator.cpp
 * @brief Google Test 基础测试示例
 *
 * 演示 Google Test 的基本用法:
 * - TEST(): 基本测试
 * - EXPECT_*: 非致命断言
 * - ASSERT_*: 致命断言
 * - 测试夹具 (Test Fixture)
 */

// ============================================================================
// 1. 基本测试 (TEST)
// ============================================================================
TEST(CalculatorTest, Addition) {
    Calculator calc;
    EXPECT_DOUBLE_EQ(calc.add(2.0, 3.0), 5.0);
    EXPECT_DOUBLE_EQ(calc.add(-1.0, 1.0), 0.0);
    EXPECT_DOUBLE_EQ(calc.add(0.0, 0.0), 0.0);
}

TEST(CalculatorTest, Subtraction) {
    Calculator calc;
    EXPECT_DOUBLE_EQ(calc.subtract(5.0, 3.0), 2.0);
    EXPECT_DOUBLE_EQ(calc.subtract(3.0, 5.0), -2.0);
}

TEST(CalculatorTest, Multiplication) {
    Calculator calc;
    EXPECT_DOUBLE_EQ(calc.multiply(3.0, 4.0), 12.0);
    EXPECT_DOUBLE_EQ(calc.multiply(0.0, 100.0), 0.0);
    EXPECT_DOUBLE_EQ(calc.multiply(-2.0, 3.0), -6.0);
}

TEST(CalculatorTest, Division) {
    Calculator calc;
    EXPECT_DOUBLE_EQ(calc.divide(10.0, 2.0), 5.0);
    EXPECT_DOUBLE_EQ(calc.divide(7.0, 2.0), 3.5);
}

TEST(CalculatorTest, DivisionByZero) {
    Calculator calc;
    EXPECT_THROW(calc.divide(1.0, 0.0), std::invalid_argument);
}

// ============================================================================
// 2. 测试夹具 (Test Fixture)
// ============================================================================
class CalculatorFixture : public ::testing::Test {
protected:
    void SetUp() override {
        calc.clear();
    }

    void TearDown() override {
        // 清理代码
    }

    Calculator calc;
};

TEST_F(CalculatorFixture, MemoryStore) {
    calc.add(42.0, 0.0);
    calc.memory_store();
    EXPECT_DOUBLE_EQ(calc.memory_recall(), 42.0);
}

TEST_F(CalculatorFixture, MemoryClear) {
    calc.add(42.0, 0.0);
    calc.memory_store();
    calc.memory_clear();
    EXPECT_DOUBLE_EQ(calc.memory_recall(), 0.0);
}

TEST_F(CalculatorFixture, Clear) {
    calc.add(42.0, 0.0);
    calc.clear();
    EXPECT_DOUBLE_EQ(calc.get_result(), 0.0);
}

// ============================================================================
// 3. 参数化测试
// ============================================================================
struct AddTestCase {
    double a;
    double b;
    double expected;
};

class CalculatorParamTest : public ::testing::TestWithParam<AddTestCase> {
protected:
    Calculator calc;
};

TEST_P(CalculatorParamTest, Addition) {
    AddTestCase test_case = GetParam();
    EXPECT_DOUBLE_EQ(calc.add(test_case.a, test_case.b), test_case.expected);
}

INSTANTIATE_TEST_SUITE_P(
    AdditionTests,
    CalculatorParamTest,
    ::testing::Values(
        AddTestCase{1.0, 2.0, 3.0},
        AddTestCase{-1.0, 1.0, 0.0},
        AddTestCase{0.0, 0.0, 0.0},
        AddTestCase{100.0, 200.0, 300.0}
    )
);
