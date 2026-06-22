#include <gtest/gtest.h>
#include "ec/galois_field.h"

using namespace disaster_recovery::ec;

class GaloisFieldTest : public ::testing::Test {
protected:
    void SetUp() override {
        gf_.init();
    }

    GaloisField gf_;
};

TEST_F(GaloisFieldTest, Initialization) {
    EXPECT_TRUE(gf_.isInitialized());
}

TEST_F(GaloisFieldTest, Addition) {
    // GF(2^8)中的加法就是XOR
    EXPECT_EQ(gf_.add(0x53, 0xCA), 0x99);
    EXPECT_EQ(gf_.add(0x00, 0xFF), 0xFF);
    EXPECT_EQ(gf_.add(0xFF, 0xFF), 0x00);
    EXPECT_EQ(gf_.add(0x12, 0x34), 0x26);
}

TEST_F(GaloisFieldTest, Subtraction) {
    // 在GF(2^8)中，减法和加法相同
    EXPECT_EQ(gf_.subtract(0x53, 0xCA), 0x99);
    EXPECT_EQ(gf_.subtract(0x00, 0xFF), 0xFF);
    EXPECT_EQ(gf_.subtract(0xFF, 0xFF), 0x00);
}

TEST_F(GaloisFieldTest, Multiplication) {
    // 测试乘法
    EXPECT_EQ(gf_.multiply(0x02, 0x02), 0x04);
    EXPECT_EQ(gf_.multiply(0x03, 0x05), 0x0F);
    EXPECT_EQ(gf_.multiply(0x53, 0xCA), 0x01);  // 53 * CA = 1 in GF(2^8)

    // 乘以0应该得0
    EXPECT_EQ(gf_.multiply(0x53, 0x00), 0x00);
    EXPECT_EQ(gf_.multiply(0x00, 0xCA), 0x00);

    // 乘以1应该得原数
    EXPECT_EQ(gf_.multiply(0x53, 0x01), 0x53);
    EXPECT_EQ(gf_.multiply(0x01, 0xCA), 0xCA);
}

TEST_F(GaloisFieldTest, Division) {
    // 测试除法
    EXPECT_EQ(gf_.divide(0x0F, 0x03), 0x05);
    EXPECT_EQ(gf_.divide(0x01, 0x53), 0xCA);  // 1 / 53 = CA in GF(2^8)

    // 除以0应该返回0
    EXPECT_EQ(gf_.divide(0x53, 0x00), 0x00);

    // 0除以任何数应该返回0
    EXPECT_EQ(gf_.divide(0x00, 0x53), 0x00);
}

TEST_F(GaloisFieldTest, Inverse) {
    // 测试逆元
    // a * a^(-1) = 1
    uint8_t a = 0x53;
    uint8_t a_inv = gf_.inverse(a);
    EXPECT_EQ(gf_.multiply(a, a_inv), 0x01);

    // 0没有逆元
    EXPECT_EQ(gf_.inverse(0x00), 0x00);

    // 1的逆元是1
    EXPECT_EQ(gf_.inverse(0x01), 0x01);
}

TEST_F(GaloisFieldTest, Power) {
    // 测试幂运算
    EXPECT_EQ(gf_.power(0x02, 0), 0x01);  // 2^0 = 1
    EXPECT_EQ(gf_.power(0x02, 1), 0x02);  // 2^1 = 2
    EXPECT_EQ(gf_.power(0x02, 2), 0x04);  // 2^2 = 4
    EXPECT_EQ(gf_.power(0x02, 3), 0x08);  // 2^3 = 8

    // 0的任何次幂都是0（除了0次幂）
    EXPECT_EQ(gf_.power(0x00, 5), 0x00);
}

TEST_F(GaloisFieldTest, LogAndExp) {
    // 测试对数和反对数
    // exp(log(a)) = a
    for (int i = 1; i < 256; i++) {
        uint8_t a = static_cast<uint8_t>(i);
        uint8_t log_a = gf_.log(a);
        uint8_t exp_log_a = gf_.exp(log_a);
        EXPECT_EQ(exp_log_a, a);
    }
}

TEST_F(GaloisFieldTest, DistributiveProperty) {
    // 测试分配律: a * (b + c) = a*b + a*c
    uint8_t a = 0x07;
    uint8_t b = 0x13;
    uint8_t c = 0x25;

    uint8_t left = gf_.multiply(a, gf_.add(b, c));
    uint8_t right = gf_.add(gf_.multiply(a, b), gf_.multiply(a, c));

    EXPECT_EQ(left, right);
}

TEST_F(GaloisFieldTest, AssociativeProperty) {
    // 测试结合律: (a * b) * c = a * (b * c)
    uint8_t a = 0x07;
    uint8_t b = 0x13;
    uint8_t c = 0x25;

    uint8_t left = gf_.multiply(gf_.multiply(a, b), c);
    uint8_t right = gf_.multiply(a, gf_.multiply(b, c));

    EXPECT_EQ(left, right);
}

TEST_F(GaloisFieldTest, CommutativeProperty) {
    // 测试交换律: a * b = b * a
    uint8_t a = 0x07;
    uint8_t b = 0x13;

    EXPECT_EQ(gf_.multiply(a, b), gf_.multiply(b, a));
}

TEST_F(GaloisFieldTest, LogOfZero) {
    // log(0)未定义，应该返回0
    EXPECT_EQ(gf_.log(0x00), 0x00);
}
