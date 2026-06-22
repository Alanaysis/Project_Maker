#include <gtest/gtest.h>
#include "node/storage_node.h"

using namespace disaster_recovery::node;
using namespace disaster_recovery::storage;

class StorageNodeTest : public ::testing::Test {
protected:
    void SetUp() override {
        StorageNodeConfig config;
        config.id = "test_node";
        config.address = "192.168.1.100";
        config.port = 8000;
        config.data_dir = "/tmp/test_node";
        config.capacity = 1024 * 1024;  // 1MB

        node_ = std::make_unique<StorageNode>(config);
        node_->init();
    }

    std::unique_ptr<StorageNode> node_;

    Shard createShard(const std::string& id, size_t size) {
        Shard shard;
        shard.id = id;
        shard.data.resize(size, 0x42);
        shard.checksum = "00000000";
        shard.is_parity = false;
        shard.index = 0;
        return shard;
    }
};

TEST_F(StorageNodeTest, Initialization) {
    // 测试初始化
    EXPECT_EQ(node_->getStatus(), NodeStatus::ONLINE);
    EXPECT_EQ(node_->getId(), "test_node");
    EXPECT_EQ(node_->getAddress(), "192.168.1.100");
    EXPECT_EQ(node_->getPort(), 8000);
}

TEST_F(StorageNodeTest, StoreAndReadShard) {
    // 测试存储和读取分片
    Shard shard = createShard("shard_1", 256);

    Status status = node_->storeShard(shard);
    EXPECT_TRUE(status.ok());

    Shard read_shard;
    status = node_->readShard("shard_1", read_shard);
    EXPECT_TRUE(status.ok());
    EXPECT_EQ(read_shard.id, "shard_1");
    EXPECT_EQ(read_shard.data.size(), 256);
}

TEST_F(StorageNodeTest, DeleteShard) {
    // 测试删除分片
    Shard shard = createShard("shard_1", 256);
    node_->storeShard(shard);

    Status status = node_->deleteShard("shard_1");
    EXPECT_TRUE(status.ok());

    Shard read_shard;
    status = node_->readShard("shard_1", read_shard);
    EXPECT_FALSE(status.ok());
    EXPECT_TRUE(status.isNotFound());
}

TEST_F(StorageNodeTest, HasShard) {
    // 测试检查分片是否存在
    EXPECT_FALSE(node_->hasShard("shard_1"));

    Shard shard = createShard("shard_1", 256);
    node_->storeShard(shard);

    EXPECT_TRUE(node_->hasShard("shard_1"));
    EXPECT_FALSE(node_->hasShard("shard_2"));
}

TEST_F(StorageNodeTest, GetNodeInfo) {
    // 测试获取节点信息
    NodeInfo info = node_->getNodeInfo();
    EXPECT_EQ(info.id, "test_node");
    EXPECT_EQ(info.status, NodeStatus::ONLINE);
    EXPECT_EQ(info.capacity, 1024 * 1024);
    EXPECT_EQ(info.used, 0);
    EXPECT_EQ(info.shard_count, 0);
}

TEST_F(StorageNodeTest, ShardCount) {
    // 测试分片计数
    EXPECT_EQ(node_->getShardCount(), 0);

    node_->storeShard(createShard("shard_1", 256));
    EXPECT_EQ(node_->getShardCount(), 1);

    node_->storeShard(createShard("shard_2", 256));
    EXPECT_EQ(node_->getShardCount(), 2);

    node_->deleteShard("shard_1");
    EXPECT_EQ(node_->getShardCount(), 1);
}

TEST_F(StorageNodeTest, CapacityTracking) {
    // 测试容量跟踪
    EXPECT_EQ(node_->getUsedCapacity(), 0);
    EXPECT_EQ(node_->getAvailableCapacity(), 1024 * 1024);

    node_->storeShard(createShard("shard_1", 256));
    EXPECT_EQ(node_->getUsedCapacity(), 256);
    EXPECT_EQ(node_->getAvailableCapacity(), 1024 * 1024 - 256);

    node_->storeShard(createShard("shard_2", 512));
    EXPECT_EQ(node_->getUsedCapacity(), 256 + 512);
}

TEST_F(StorageNodeTest, CapacityExhausted) {
    // 测试容量耗尽
    // 尝试存储超过容量的数据
    Shard large_shard = createShard("large", 2 * 1024 * 1024);  // 2MB
    Status status = node_->storeShard(large_shard);
    EXPECT_FALSE(status.ok());
    EXPECT_EQ(status.code, StatusCode::RESOURCE_EXHAUSTED);
}

TEST_F(StorageNodeTest, DuplicateShard) {
    // 测试重复存储
    Shard shard = createShard("shard_1", 256);
    node_->storeShard(shard);

    Status status = node_->storeShard(shard);
    EXPECT_FALSE(status.ok());
    EXPECT_EQ(status.code, StatusCode::ALREADY_EXISTS);
}

TEST_F(StorageNodeTest, ReadNonExistentShard) {
    // 测试读取不存在的分片
    Shard shard;
    Status status = node_->readShard("non_existent", shard);
    EXPECT_FALSE(status.ok());
    EXPECT_TRUE(status.isNotFound());
}

TEST_F(StorageNodeTest, DeleteNonExistentShard) {
    // 测试删除不存在的分片
    Status status = node_->deleteShard("non_existent");
    EXPECT_FALSE(status.ok());
    EXPECT_TRUE(status.isNotFound());
}

TEST_F(StorageNodeTest, GetAllShardIds) {
    // 测试获取所有分片ID
    node_->storeShard(createShard("shard_1", 256));
    node_->storeShard(createShard("shard_2", 256));
    node_->storeShard(createShard("shard_3", 256));

    auto ids = node_->getAllShardIds();
    EXPECT_EQ(ids.size(), 3);
}

TEST_F(StorageNodeTest, HandleHeartbeat) {
    // 测试心跳处理
    HeartbeatResponse response = node_->handleHeartbeat();
    EXPECT_TRUE(response.status.ok());
    EXPECT_FALSE(response.need_recovery);
}

TEST_F(StorageNodeTest, VerifyShard) {
    // 测试分片验证
    Shard shard = createShard("shard_1", 256);
    // 设置正确的校验和
    shard.checksum = "00000000";  // 简化的校验和
    node_->storeShard(shard);

    // 验证应该通过（简化实现）
    EXPECT_TRUE(node_->verifyShard("shard_1"));
}

TEST_F(StorageNodeTest, NodeStatus) {
    // 测试节点状态设置
    EXPECT_EQ(node_->getStatus(), NodeStatus::ONLINE);

    node_->setStatus(NodeStatus::DEGRADED);
    EXPECT_EQ(node_->getStatus(), NodeStatus::DEGRADED);

    node_->setStatus(NodeStatus::OFFLINE);
    EXPECT_EQ(node_->getStatus(), NodeStatus::OFFLINE);
}

TEST_F(StorageNodeTest, OfflineNodeOperations) {
    // 测试离线节点的操作
    node_->setStatus(NodeStatus::OFFLINE);

    Shard shard = createShard("shard_1", 256);
    Status status = node_->storeShard(shard);
    EXPECT_FALSE(status.ok());
    EXPECT_EQ(status.code, StatusCode::UNAVAILABLE);

    Shard read_shard;
    status = node_->readShard("shard_1", read_shard);
    EXPECT_FALSE(status.ok());
    EXPECT_EQ(status.code, StatusCode::UNAVAILABLE);
}
