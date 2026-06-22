#include <gtest/gtest.h>
#include "utils/checksum.h"
#include <vector>
#include <string>

using namespace disaster_recovery::utils;

class ChecksumTest : public ::testing::Test {
protected:
    std::vector<uint8_t> testData() {
        return {0x48, 0x65, 0x6C, 0x6C, 0x6F};  // "Hello"
    }
};

TEST_F(ChecksumTest, Crc32Basic) {
    // 测试基本的CRC32计算
    auto data = testData();
    uint32_t crc = Checksum::crc32(data.data(), data.size());

    // CRC32应该是非零值
    EXPECT_NE(crc, 0);

    // 相同数据应该产生相同校验和
    uint32_t crc2 = Checksum::crc32(data.data(), data.size());
    EXPECT_EQ(crc, crc2);
}

TEST_F(ChecksumTest, Crc32String) {
    // 测试CRC32字符串形式
    auto data = testData();
    std::string crc_str = Checksum::crc32String(data.data(), data.size());

    // 应该是8个字符的十六进制字符串
    EXPECT_EQ(crc_str.size(), 8);

    // 应该是有效的十六进制
    for (char c : crc_str) {
        EXPECT_TRUE((c >= '0' && c <= '9') ||
                    (c >= 'a' && c <= 'f'));
    }
}

TEST_F(ChecksumTest, Crc32Vector) {
    // 测试向量形式的CRC32
    auto data = testData();
    uint32_t crc1 = Checksum::crc32(data);
    uint32_t crc2 = Checksum::crc32(data.data(), data.size());

    EXPECT_EQ(crc1, crc2);
}

TEST_F(ChecksumTest, Crc32DifferentData) {
    // 测试不同数据产生不同校验和
    std::vector<uint8_t> data1 = {0x48, 0x65, 0x6C, 0x6C, 0x6F};  // "Hello"
    std::vector<uint8_t> data2 = {0x57, 0x6F, 0x72, 0x6C, 0x64};  // "World"

    uint32_t crc1 = Checksum::crc32(data1);
    uint32_t crc2 = Checksum::crc32(data2);

    EXPECT_NE(crc1, crc2);
}

TEST_F(ChecksumTest, Crc32EmptyData) {
    // 测试空数据
    uint32_t crc = Checksum::crc32(nullptr, 0);
    EXPECT_NE(crc, 0);  // 空数据也有校验和
}

TEST_F(ChecksumTest, Crc32Verification) {
    // 测试校验和验证
    auto data = testData();
    uint32_t crc = Checksum::crc32(data);

    EXPECT_TRUE(Checksum::verifyCrc32(data.data(), data.size(), crc));
    EXPECT_FALSE(Checksum::verifyCrc32(data.data(), data.size(), crc + 1));
}

TEST_F(ChecksumTest, Crc32VerificationString) {
    // 测试字符串形式的校验和验证
    auto data = testData();
    std::string crc_str = Checksum::crc32String(data);

    EXPECT_TRUE(Checksum::verifyCrc32(data.data(), data.size(), crc_str));
    EXPECT_FALSE(Checksum::verifyCrc32(data.data(), data.size(), "00000000"));
}

TEST_F(ChecksumTest, Adler32Basic) {
    // 测试Adler32
    auto data = testData();
    uint32_t adler = Checksum::adler32(data.data(), data.size());

    // Adler32应该是非零值
    EXPECT_NE(adler, 0);

    // 相同数据应该产生相同校验和
    uint32_t adler2 = Checksum::adler32(data.data(), data.size());
    EXPECT_EQ(adler, adler2);
}

TEST_F(ChecksumTest, Fnv1aBasic) {
    // 测试FNV-1a哈希
    auto data = testData();
    uint64_t hash = Checksum::fnv1a(data.data(), data.size());

    // 哈希应该是非零值
    EXPECT_NE(hash, 0);

    // 相同数据应该产生相同哈希
    uint64_t hash2 = Checksum::fnv1a(data.data(), data.size());
    EXPECT_EQ(hash, hash2);
}

TEST_F(ChecksumTest, SimpleHash) {
    // 测试简单哈希
    auto data = testData();
    uint32_t hash = Checksum::simple(data.data(), data.size());

    // 哈希应该是非零值
    EXPECT_NE(hash, 0);

    // 相同数据应该产生相同哈希
    uint32_t hash2 = Checksum::simple(data.data(), data.size());
    EXPECT_EQ(hash, hash2);
}

TEST_F(ChecksumTest, BlockCrc32) {
    // 测试分块CRC32
    std::vector<uint8_t> data(1024, 0x42);  // 1024字节

    auto checksums = Checksum::blockCrc32(data.data(), data.size(), 256);

    // 应该有4个块
    EXPECT_EQ(checksums.size(), 4);

    // 每个块的校验和应该相同（因为数据相同）
    for (size_t i = 1; i < checksums.size(); i++) {
        EXPECT_EQ(checksums[i], checksums[0]);
    }
}

TEST_F(ChecksumTest, BlockCrc32WithRemainder) {
    // 测试有余数的分块CRC32
    std::vector<uint8_t> data(1000, 0x42);  // 1000字节

    auto checksums = Checksum::blockCrc32(data.data(), data.size(), 256);

    // 应该有4个块: 256 + 256 + 256 + 232
    EXPECT_EQ(checksums.size(), 4);
}

TEST_F(ChecksumTest, DifferentAlgorithms) {
    // 测试不同算法产生不同结果
    auto data = testData();

    uint32_t crc = Checksum::crc32(data);
    uint32_t adler = Checksum::adler32(data.data(), data.size());
    uint64_t fnv = Checksum::fnv1a(data.data(), data.size());
    uint32_t simple = Checksum::simple(data.data(), data.size());

    // 不同算法应该产生不同结果
    // 注意：这不是绝对的，但概率很高
    EXPECT_NE(crc, adler);
    EXPECT_NE(crc, static_cast<uint32_t>(fnv));
    EXPECT_NE(crc, simple);
}

TEST_F(ChecksumTest, LargeData) {
    // 测试大数据
    std::vector<uint8_t> data(1024 * 1024, 0x42);  // 1MB

    uint32_t crc = Checksum::crc32(data);
    EXPECT_NE(crc, 0);

    std::string crc_str = Checksum::crc32String(data);
    EXPECT_EQ(crc_str.size(), 8);
}
