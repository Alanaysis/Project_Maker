#include <gtest/gtest.h>
#include "mylib/core.h"

TEST(MathUtilsTest, Add) {
    EXPECT_EQ(mylib::MathUtils::add(2, 3), 5);
    EXPECT_EQ(mylib::MathUtils::add(-1, 1), 0);
}

TEST(MathUtilsTest, Subtract) {
    EXPECT_EQ(mylib::MathUtils::subtract(10, 3), 7);
    EXPECT_EQ(mylib::MathUtils::subtract(3, 10), -7);
}

TEST(MathUtilsTest, Multiply) {
    EXPECT_EQ(mylib::MathUtils::multiply(3, 4), 12);
    EXPECT_EQ(mylib::MathUtils::multiply(0, 100), 0);
}

TEST(MathUtilsTest, Divide) {
    EXPECT_DOUBLE_EQ(mylib::MathUtils::divide(10.0, 2.0), 5.0);
    EXPECT_THROW(mylib::MathUtils::divide(1.0, 0.0), std::invalid_argument);
}

TEST(MathUtilsTest, Power) {
    EXPECT_DOUBLE_EQ(mylib::MathUtils::power(2.0, 10), 1024.0);
    EXPECT_DOUBLE_EQ(mylib::MathUtils::power(3.0, 0), 1.0);
}

TEST(MathUtilsTest, IsPrime) {
    EXPECT_TRUE(mylib::MathUtils::is_prime(2));
    EXPECT_TRUE(mylib::MathUtils::is_prime(7));
    EXPECT_FALSE(mylib::MathUtils::is_prime(4));
    EXPECT_FALSE(mylib::MathUtils::is_prime(1));
}
