#include <gtest/gtest.h>
#include "storage/data_sharder.h"
#include <random>
#include <vector>

using namespace disaster_recovery::storage;

class DataSharderTest : public ::testing::Test {
protected:
    void SetUp() override {
        rng_.seed(42);
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

TEST_F(DataSharderTest, BasicSharding) {
    // 测试基本分片
    DataSharder sharder(256);  // 256字节分片

    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    std::vector<Shard> shards;
    Status status = sharder.shard(original_data.data(), data_size, shards);
    EXPECT_TRUE(status.ok());

    // 检查分片数量
    EXPECT_EQ(shards.size(), 4);  // 1024 / 256 = 4

    // 检查每个分片
    for (size_t i = 0; i < shards.size(); i++) {
        EXPECT_EQ(shards[i].index, i);
        EXPECT_EQ(shards[i].data.size(), 256);
        EXPECT_FALSE(shards[i].is_parity);
        EXPECT_FALSE(shards[i].checksum.empty());
    }
}

TEST_F(DataSharderTest, ShardingWithRemainder) {
    // 测试有余数的分片
    DataSharder sharder(256);

    size_t data_size = 1000;  // 不是256的整数倍
    auto original_data = generateRandomData(data_size);

    std::vector<Shard> shards;
    Status status = sharder.shard(original_data.data(), data_size, shards);
    EXPECT_TRUE(status.ok());

    // 检查分片数量: ceil(1000 / 256) = 4
    EXPECT_EQ(shards.size(), 4);

    // 检查最后一个分片大小
    EXPECT_EQ(shards[3].data.size(), 1000 - 256 * 3);  // 1000 - 768 = 232
}

TEST_F(DataSharderTest, Reassembly) {
    // 测试数据重组
    DataSharder sharder(256);

    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    // 分片
    std::vector<Shard> shards;
    sharder.shard(original_data.data(), data_size, shards);

    // 重组
    std::vector<uint8_t> reassembled_data;
    Status status = sharder.reassemble(shards, reassembled_data, data_size);
    EXPECT_TRUE(status.ok());

    // 验证数据
    EXPECT_EQ(reassembled_data.size(), data_size);
    for (size_t i = 0; i < data_size; i++) {
        EXPECT_EQ(reassembled_data[i], original_data[i]);
    }
}

TEST_F(DataSharderTest, ReassemblyWithRemainder) {
    // 测试有余数的数据重组
    DataSharder sharder(256);

    size_t data_size = 1000;
    auto original_data = generateRandomData(data_size);

    // 分片
    std::vector<Shard> shards;
    sharder.shard(original_data.data(), data_size, shards);

    // 重组
    std::vector<uint8_t> reassembled_data;
    Status status = sharder.reassemble(shards, reassembled_data, data_size);
    EXPECT_TRUE(status.ok());

    // 验证数据
    EXPECT_EQ(reassembled_data.size(), data_size);
    for (size_t i = 0; i < data_size; i++) {
        EXPECT_EQ(reassembled_data[i], original_data[i]);
    }
}

TEST_F(DataSharderTest, ShardCount) {
    // 测试分片数量计算
    DataSharder sharder(256);

    EXPECT_EQ(sharder.calculateShardCount(0), 0);
    EXPECT_EQ(sharder.calculateShardCount(1), 1);
    EXPECT_EQ(sharder.calculateShardCount(256), 1);
    EXPECT_EQ(sharder.calculateShardCount(257), 2);
    EXPECT_EQ(sharder.calculateShardCount(1024), 4);
    EXPECT_EQ(sharder.calculateShardCount(1000), 4);
}

TEST_F(DataSharderTest, ShardSize) {
    // 测试分片大小计算
    DataSharder sharder(256);

    // 第一个分片
    EXPECT_EQ(sharder.calculateShardSize(0, 1024), 256);

    // 最后一个分片（有余数）
    EXPECT_EQ(sharder.calculateShardSize(3, 1000), 232);

    // 超出范围
    EXPECT_EQ(sharder.calculateShardSize(5, 1024), 0);
}

TEST_F(DataSharderTest, EmptyData) {
    // 测试空数据
    DataSharder sharder(256);

    std::vector<Shard> shards;
    Status status = sharder.shard(nullptr, 0, shards);
    EXPECT_FALSE(status.ok());
}

TEST_F(DataSharderTest, DifferentShardSizes) {
    // 测试不同的分片大小
    std::vector<size_t> shard_sizes = {64, 128, 256, 512, 1024};

    for (size_t shard_size : shard_sizes) {
        DataSharder sharder(shard_size);

        size_t data_size = 2048;
        auto original_data = generateRandomData(data_size);

        std::vector<Shard> shards;
        Status status = sharder.shard(original_data.data(), data_size, shards);
        EXPECT_TRUE(status.ok()) << "Failed for shard_size=" << shard_size;

        // 验证分片大小
        for (const auto& shard : shards) {
            EXPECT_LE(shard.data.size(), shard_size);
        }
    }
}

TEST_F(DataSharderTest, LargeData) {
    // 测试大数据
    DataSharder sharder(65536);  // 64KB分片

    size_t data_size = 1024 * 1024;  // 1MB
    auto original_data = generateRandomData(data_size);

    // 分片
    std::vector<Shard> shards;
    Status status = sharder.shard(original_data.data(), data_size, shards);
    EXPECT_TRUE(status.ok());

    // 重组
    std::vector<uint8_t> reassembled_data;
    status = sharder.reassemble(shards, reassembled_data, data_size);
    EXPECT_TRUE(status.ok());

    // 验证
    EXPECT_EQ(reassembled_data.size(), data_size);
    EXPECT_EQ(memcmp(reassembled_data.data(), original_data.data(), data_size), 0);
}

TEST_F(DataSharderTest, Checksum) {
    // 测试校验和
    DataSharder sharder(256);

    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    std::vector<Shard> shards;
    sharder.shard(original_data.data(), data_size, shards);

    // 验证每个分片都有校验和
    for (const auto& shard : shards) {
        EXPECT_FALSE(shard.checksum.empty());
        EXPECT_EQ(shard.checksum.size(), 8);  // CRC32是8个十六进制字符
    }
}

TEST_F(DataSharderTest, ShardId) {
    // 测试分片ID生成
    DataSharder sharder(256);

    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);

    std::vector<Shard> shards;
    sharder.shard(original_data.data(), data_size, shards);

    // 验证每个分片都有ID
    for (const auto& shard : shards) {
        EXPECT_FALSE(shard.id.empty());
    }

    // 验证ID唯一
    std::set<std::string> ids;
    for (const auto& shard : shards) {
        ids.insert(shard.id);
    }
    EXPECT_EQ(ids.size(), shards.size());
}
