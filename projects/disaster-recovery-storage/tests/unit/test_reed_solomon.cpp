#include <gtest/gtest.h>
#include "ec/reed_solomon.h"
#include <random>
#include <vector>

using namespace disaster_recovery::ec;

class ReedSolomonTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 创建随机数据生成器
        rng_.seed(42);  // 固定种子，保证可重复性
    }

    std::mt19937 rng_;

    std::vector<uint8_t> generateRandomData(size_t size) {
        std::vector<uint8_t> data(size);
        std::uniform_int_distribution<int> dist(0, 255);
        for (auto& byte : data) {
            byte = static_cast<uint8_t>(dist(rng_));
        }
        return data;
    }
};

TEST_F(ReedSolomonTest, BasicEncodeDecode) {
    // 测试基本的编码和解码
    ReedSolomon rs(4, 2);  // 4个数据分片，2个校验分片

    // 生成测试数据
    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    // 编码
    std::vector<std::vector<uint8_t>> shards;
    int result = rs.encode(original_data.data(), data_size, shards);
    EXPECT_EQ(result, 0);

    // 检查分片数量
    EXPECT_EQ(shards.size(), 6);  // 4 + 2

    // 检查分片大小
    size_t expected_shard_size = rs.calculateShardSize(data_size);
    for (const auto& shard : shards) {
        EXPECT_EQ(shard.size(), expected_shard_size);
    }

    // 解码（使用所有分片）
    std::vector<bool> available(6, true);
    std::vector<uint8_t> decoded_data;
    result = rs.decode(shards, available, decoded_data);
    EXPECT_EQ(result, 0);

    // 验证数据
    EXPECT_EQ(decoded_data.size(), data_size);
    for (size_t i = 0; i < data_size; i++) {
        EXPECT_EQ(decoded_data[i], original_data[i]);
    }
}

TEST_F(ReedSolomonTest, DecodeWithMissingShard) {
    // 测试丢失一个分片的情况
    ReedSolomon rs(4, 2);

    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    // 编码
    std::vector<std::vector<uint8_t>> shards;
    rs.encode(original_data.data(), data_size, shards);

    // 模拟丢失第一个数据分片
    std::vector<bool> available = {false, true, true, true, true, true};
    std::vector<uint8_t> decoded_data;
    int result = rs.decode(shards, available, decoded_data);
    EXPECT_EQ(result, 0);

    // 验证数据
    EXPECT_EQ(decoded_data.size(), data_size);
    for (size_t i = 0; i < data_size; i++) {
        EXPECT_EQ(decoded_data[i], original_data[i]);
    }
}

TEST_F(ReedSolomonTest, DecodeWithMissingParity) {
    // 测试丢失校验分片的情况
    ReedSolomon rs(4, 2);

    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    // 编码
    std::vector<std::vector<uint8_t>> shards;
    rs.encode(original_data.data(), data_size, shards);

    // 模拟丢失两个校验分片
    std::vector<bool> available = {true, true, true, true, false, false};
    std::vector<uint8_t> decoded_data;
    int result = rs.decode(shards, available, decoded_data);
    EXPECT_EQ(result, 0);

    // 验证数据
    EXPECT_EQ(decoded_data.size(), data_size);
    for (size_t i = 0; i < data_size; i++) {
        EXPECT_EQ(decoded_data[i], original_data[i]);
    }
}

TEST_F(ReedSolomonTest, DecodeWithMultipleMissing) {
    // 测试丢失多个分片的情况（但不超过parity_shards）
    ReedSolomon rs(4, 2);

    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    // 编码
    std::vector<std::vector<uint8_t>> shards;
    rs.encode(original_data.data(), data_size, shards);

    // 模拟丢失一个数据分片和一个校验分片
    std::vector<bool> available = {false, true, true, true, true, false};
    std::vector<uint8_t> decoded_data;
    int result = rs.decode(shards, available, decoded_data);
    EXPECT_EQ(result, 0);

    // 验证数据
    EXPECT_EQ(decoded_data.size(), data_size);
    for (size_t i = 0; i < data_size; i++) {
        EXPECT_EQ(decoded_data[i], original_data[i]);
    }
}

TEST_F(ReedSolomonTest, CannotRecoverTooManyMissing) {
    // 测试丢失过多分片无法恢复的情况
    ReedSolomon rs(4, 2);

    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    // 编码
    std::vector<std::vector<uint8_t>> shards;
    rs.encode(original_data.data(), data_size, shards);

    // 模拟丢失3个分片（超过parity_shards=2）
    std::vector<bool> available = {false, false, false, true, true, true};
    std::vector<uint8_t> decoded_data;
    int result = rs.decode(shards, available, decoded_data);
    EXPECT_NE(result, 0);  // 应该失败
}

TEST_F(ReedSolomonTest, DifferentShardCounts) {
    // 测试不同的分片配置
    std::vector<std::pair<int, int>> configs = {
        {1, 1},  // 最小配置
        {2, 1},
        {2, 2},
        {4, 2},
        {8, 4},
    };

    for (const auto& config : configs) {
        int k = config.first;
        int m = config.second;

        ReedSolomon rs(k, m);

        size_t data_size = 512;
        auto original_data = generateRandomData(data_size);

        // 编码
        std::vector<std::vector<uint8_t>> shards;
        int result = rs.encode(original_data.data(), data_size, shards);
        EXPECT_EQ(result, 0) << "Failed for k=" << k << ", m=" << m;

        // 解码
        std::vector<bool> available(k + m, true);
        std::vector<uint8_t> decoded_data;
        result = rs.decode(shards, available, decoded_data);
        EXPECT_EQ(result, 0) << "Failed for k=" << k << ", m=" << m;

        // 验证
        EXPECT_EQ(decoded_data.size(), data_size);
        for (size_t i = 0; i < data_size; i++) {
            EXPECT_EQ(decoded_data[i], original_data[i])
                << "Failed for k=" << k << ", m=" << m << " at index " << i;
        }
    }
}

TEST_F(ReedSolomonTest, LargeData) {
    // 测试大数据
    ReedSolomon rs(4, 2);

    size_t data_size = 1024 * 1024;  // 1MB
    auto original_data = generateRandomData(data_size);

    // 编码
    std::vector<std::vector<uint8_t>> shards;
    int result = rs.encode(original_data.data(), data_size, shards);
    EXPECT_EQ(result, 0);

    // 解码
    std::vector<bool> available(6, true);
    std::vector<uint8_t> decoded_data;
    result = rs.decode(shards, available, decoded_data);
    EXPECT_EQ(result, 0);

    // 验证
    EXPECT_EQ(decoded_data.size(), data_size);
    EXPECT_EQ(memcmp(decoded_data.data(), original_data.data(), data_size), 0);
}

TEST_F(ReedSolomonTest, EmptyData) {
    // 测试空数据
    ReedSolomon rs(4, 2);

    std::vector<std::vector<uint8_t>> shards;
    int result = rs.encode(nullptr, 0, shards);
    EXPECT_NE(result, 0);  // 应该失败
}

TEST_F(ReedSolomonTest, ShardSize) {
    // 测试分片大小计算
    ReedSolomon rs(4, 2);

    // 1024字节，4个分片，每个256字节
    EXPECT_EQ(rs.calculateShardSize(1024), 256);

    // 1025字节，4个分片，每个257字节（向上取整）
    EXPECT_EQ(rs.calculateShardSize(1025), 257);

    // 1字节，4个分片，每个1字节
    EXPECT_EQ(rs.calculateShardSize(1), 1);
}

TEST_F(ReedSolomonTest, CanRecover) {
    // 测试恢复能力检查
    ReedSolomon rs(4, 2);

    // 需要至少4个分片才能恢复
    EXPECT_TRUE(rs.canRecover(4));
    EXPECT_TRUE(rs.canRecover(5));
    EXPECT_TRUE(rs.canRecover(6));
    EXPECT_FALSE(rs.canRecover(3));
    EXPECT_FALSE(rs.canRecover(2));
    EXPECT_FALSE(rs.canRecover(1));
}
