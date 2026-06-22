#include <gtest/gtest.h>
#include "storage/replica_manager.h"

using namespace disaster_recovery::storage;

class ReplicaManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 创建副本管理器: N=3, W=2, R=2
        manager_ = std::make_unique<ReplicaManager>(3, 2, 2);
    }

    std::unique_ptr<ReplicaManager> manager_;

    NodeInfo createNode(const std::string& id, NodeStatus status) {
        NodeInfo node;
        node.id = id;
        node.address = "192.168.1." + id;
        node.port = 8000;
        node.status = status;
        node.capacity = 1024 * 1024 * 1024;  // 1GB
        node.used = 0;
        node.available = node.capacity;
        node.shard_count = 0;
        return node;
    }
};

TEST_F(ReplicaManagerTest, ConfigValidation) {
    // 测试配置验证
    EXPECT_TRUE(manager_->validateConfig());

    // 无效配置: W + R <= N
    ReplicaManager invalid1(3, 1, 1);
    EXPECT_FALSE(invalid1.validateConfig());

    // 无效配置: W > N
    ReplicaManager invalid2(3, 4, 1);
    EXPECT_FALSE(invalid2.validateConfig());

    // 无效配置: R > N
    ReplicaManager invalid3(3, 1, 4);
    EXPECT_FALSE(invalid3.validateConfig());
}

TEST_F(ReplicaManagerTest, SelectWriteNodes) {
    // 测试选择写入节点
    std::vector<NodeInfo> nodes;
    nodes.push_back(createNode("1", NodeStatus::ONLINE));
    nodes.push_back(createNode("2", NodeStatus::ONLINE));
    nodes.push_back(createNode("3", NodeStatus::ONLINE));
    nodes.push_back(createNode("4", NodeStatus::ONLINE));

    auto selected = manager_->selectWriteNodes(nodes, "shard_1");
    EXPECT_EQ(selected.size(), 3);  // replication_factor = 3
}

TEST_F(ReplicaManagerTest, SelectWriteNodesWithOffline) {
    // 测试有离线节点时的选择
    std::vector<NodeInfo> nodes;
    nodes.push_back(createNode("1", NodeStatus::ONLINE));
    nodes.push_back(createNode("2", NodeStatus::OFFLINE));
    nodes.push_back(createNode("3", NodeStatus::ONLINE));
    nodes.push_back(createNode("4", NodeStatus::ONLINE));

    auto selected = manager_->selectWriteNodes(nodes, "shard_1");
    EXPECT_EQ(selected.size(), 3);  // 应该跳过离线节点
}

TEST_F(ReplicaManagerTest, SelectReadNodes) {
    // 测试选择读取节点
    std::vector<ReplicaInfo> replicas;
    ReplicaInfo r1;
    r1.node_id = "1";
    r1.status = ReplicaStatus::HEALTHY;
    replicas.push_back(r1);

    ReplicaInfo r2;
    r2.node_id = "2";
    r2.status = ReplicaStatus::HEALTHY;
    replicas.push_back(r2);

    ReplicaInfo r3;
    r3.node_id = "3";
    r3.status = ReplicaStatus::LOST;
    replicas.push_back(r3);

    auto selected = manager_->selectReadNodes(replicas);
    EXPECT_EQ(selected.size(), 2);  // read_quorum = 2
}

TEST_F(ReplicaManagerTest, QuorumCheck) {
    // 测试Quorum检查
    std::vector<Status> responses;

    // 2个成功，1个失败
    responses.push_back(Status::OK());
    responses.push_back(Status::OK());
    responses.push_back(Status(StatusCode::UNAVAILABLE, "Node offline"));

    EXPECT_TRUE(manager_->checkWriteQuorum(responses));
    EXPECT_TRUE(manager_->checkReadQuorum(responses));

    // 1个成功，2个失败
    responses.clear();
    responses.push_back(Status::OK());
    responses.push_back(Status(StatusCode::UNAVAILABLE, "Node offline"));
    responses.push_back(Status(StatusCode::UNAVAILABLE, "Node offline"));

    EXPECT_FALSE(manager_->checkWriteQuorum(responses));
    EXPECT_FALSE(manager_->checkReadQuorum(responses));
}

TEST_F(ReplicaManagerTest, AddAndRemoveReplica) {
    // 测试添加和移除副本
    manager_->addReplica("shard_1", "node_1");
    manager_->addReplica("shard_1", "node_2");
    manager_->addReplica("shard_1", "node_3");

    auto replicas = manager_->getReplicas("shard_1");
    EXPECT_EQ(replicas.size(), 3);

    // 移除一个副本
    manager_->removeReplica("shard_1", "node_2");
    replicas = manager_->getReplicas("shard_1");
    EXPECT_EQ(replicas.size(), 2);
}

TEST_F(ReplicaManagerTest, GetShardsOnNode) {
    // 测试获取节点上的分片
    manager_->addReplica("shard_1", "node_1");
    manager_->addReplica("shard_2", "node_1");
    manager_->addReplica("shard_3", "node_2");

    auto shards = manager_->getShardsOnNode("node_1");
    EXPECT_EQ(shards.size(), 2);

    shards = manager_->getShardsOnNode("node_2");
    EXPECT_EQ(shards.size(), 1);
}

TEST_F(ReplicaManagerTest, ShardHealthCheck) {
    // 测试分片健康检查
    manager_->addReplica("shard_1", "node_1", ReplicaStatus::HEALTHY);
    manager_->addReplica("shard_1", "node_2", ReplicaStatus::HEALTHY);
    manager_->addReplica("shard_1", "node_3", ReplicaStatus::LOST);

    // 2个健康副本，满足read_quorum=2
    EXPECT_TRUE(manager_->isShardHealthy("shard_1"));

    // 更新一个副本为LOST
    manager_->updateReplicaStatus("shard_1", "node_2", ReplicaStatus::LOST);

    // 只有1个健康副本，不满足read_quorum=2
    EXPECT_FALSE(manager_->isShardHealthy("shard_1"));
}

TEST_F(ReplicaManagerTest, GetShardsToRecover) {
    // 测试获取需要恢复的分片
    manager_->addReplica("shard_1", "node_1", ReplicaStatus::HEALTHY);
    manager_->addReplica("shard_1", "node_2", ReplicaStatus::HEALTHY);
    manager_->addReplica("shard_1", "node_3", ReplicaStatus::LOST);

    manager_->addReplica("shard_2", "node_1", ReplicaStatus::HEALTHY);
    manager_->addReplica("shard_2", "node_2", ReplicaStatus::LOST);

    // node_2故障，shard_2需要恢复
    auto shards = manager_->getShardsToRecover("node_2");
    EXPECT_EQ(shards.size(), 1);
    EXPECT_EQ(shards[0], "shard_2");
}

TEST_F(ReplicaManagerTest, UpdateReplicaStatus) {
    // 测试更新副本状态
    manager_->addReplica("shard_1", "node_1", ReplicaStatus::HEALTHY);

    auto replicas = manager_->getReplicas("shard_1");
    EXPECT_EQ(replicas[0].status, ReplicaStatus::HEALTHY);

    manager_->updateReplicaStatus("shard_1", "node_1", ReplicaStatus::DEGRADED);

    replicas = manager_->getReplicas("shard_1");
    EXPECT_EQ(replicas[0].status, ReplicaStatus::DEGRADED);
}

TEST_F(ReplicaManagerTest, NonExistentShard) {
    // 测试不存在的分片
    auto replicas = manager_->getReplicas("non_existent");
    EXPECT_TRUE(replicas.empty());

    EXPECT_FALSE(manager_->isShardHealthy("non_existent"));
}
