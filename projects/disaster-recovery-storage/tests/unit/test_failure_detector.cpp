#include <gtest/gtest.h>
#include "network/failure_detector.h"
#include <thread>
#include <chrono>

using namespace disaster_recovery::network;

class FailureDetectorTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 创建故障检测器: 心跳间隔100ms，超时300ms，怀疑超时500ms
        detector_ = std::make_unique<FailureDetector>(100, 300, 500);
    }

    void TearDown() override {
        if (detector_) {
            detector_->stop();
        }
    }

    std::unique_ptr<FailureDetector> detector_;
};

TEST_F(FailureDetectorTest, RegisterAndRemoveNode) {
    // 测试注册和移除节点
    detector_->registerNode("node_1");
    detector_->registerNode("node_2");

    EXPECT_TRUE(detector_->isNodeOnline("node_1"));
    EXPECT_TRUE(detector_->isNodeOnline("node_2"));

    detector_->removeNode("node_1");
    EXPECT_FALSE(detector_->isNodeOnline("node_1"));
    EXPECT_TRUE(detector_->isNodeOnline("node_2"));
}

TEST_F(FailureDetectorTest, GetOnlineNodes) {
    // 测试获取在线节点
    detector_->registerNode("node_1");
    detector_->registerNode("node_2");
    detector_->registerNode("node_3");

    auto online = detector_->getOnlineNodes();
    EXPECT_EQ(online.size(), 3);
}

TEST_F(FailureDetectorTest, HeartbeatReport) {
    // 测试心跳报告
    detector_->registerNode("node_1");

    // 初始状态应该是在线
    EXPECT_EQ(detector_->getNodeStatus("node_1"),
              disaster_recovery::storage::NodeStatus::ONLINE);

    // 报告心跳
    detector_->reportHeartbeat("node_1");
    EXPECT_EQ(detector_->getNodeStatus("node_1"),
              disaster_recovery::storage::NodeStatus::ONLINE);
}

TEST_F(FailureDetectorTest, FailureDetection) {
    // 测试故障检测
    detector_->registerNode("node_1");

    // 启动检测器
    detector_->start();

    // 等待超时
    std::this_thread::sleep_for(std::chrono::milliseconds(400));

    // 节点应该被标记为疑似故障或离线
    auto status = detector_->getNodeStatus("node_1");
    EXPECT_TRUE(status == disaster_recovery::storage::NodeStatus::SUSPECTED ||
                status == disaster_recovery::storage::NodeStatus::OFFLINE);

    detector_->stop();
}

TEST_F(FailureDetectorTest, HeartbeatKeepsAlive) {
    // 测试心跳保活
    detector_->registerNode("node_1");
    detector_->start();

    // 持续发送心跳
    for (int i = 0; i < 5; i++) {
        detector_->reportHeartbeat("node_1");
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    // 节点应该保持在线
    EXPECT_EQ(detector_->getNodeStatus("node_1"),
              disaster_recovery::storage::NodeStatus::ONLINE);

    detector_->stop();
}

TEST_F(FailureDetectorTest, FailureCallback) {
    // 测试故障回调
    bool callback_called = false;
    disaster_recovery::storage::NodeId failed_node;

    detector_->setFailureCallback(
        [&](const disaster_recovery::storage::NodeId& node_id) {
            callback_called = true;
            failed_node = node_id;
        });

    detector_->registerNode("node_1");
    detector_->start();

    // 等待超时
    std::this_thread::sleep_for(std::chrono::milliseconds(600));

    EXPECT_TRUE(callback_called);
    EXPECT_EQ(failed_node, "node_1");

    detector_->stop();
}

TEST_F(FailureDetectorTest, RecoveryCallback) {
    // 测试恢复回调
    bool recovery_called = false;
    disaster_recovery::storage::NodeId recovered_node;

    detector_->setRecoveryCallback(
        [&](const disaster_recovery::storage::NodeId& node_id) {
            recovery_called = true;
            recovered_node = node_id;
        });

    detector_->registerNode("node_1");
    detector_->start();

    // 等待节点被标记为故障
    std::this_thread::sleep_for(std::chrono::milliseconds(600));

    // 报告心跳，触发恢复
    detector_->reportHeartbeat("node_1");

    EXPECT_TRUE(recovery_called);
    EXPECT_EQ(recovered_node, "node_1");

    detector_->stop();
}

TEST_F(FailureDetectorTest, GetNodeInfo) {
    // 测试获取节点信息
    detector_->registerNode("node_1");

    auto info = detector_->getNodeInfo("node_1");
    EXPECT_EQ(info.id, "node_1");
    EXPECT_EQ(info.status, disaster_recovery::storage::NodeStatus::ONLINE);
    EXPECT_EQ(info.missed_heartbeats, 0);
}

TEST_F(FailureDetectorTest, GetAllNodeInfo) {
    // 测试获取所有节点信息
    detector_->registerNode("node_1");
    detector_->registerNode("node_2");

    auto infos = detector_->getAllNodeInfo();
    EXPECT_EQ(infos.size(), 2);
}

TEST_F(FailureDetectorTest, NonExistentNode) {
    // 测试不存在的节点
    EXPECT_FALSE(detector_->isNodeOnline("non_existent"));
    EXPECT_EQ(detector_->getNodeStatus("non_existent"),
              disaster_recovery::storage::NodeStatus::OFFLINE);
}

TEST_F(FailureDetectorTest, MultipleNodes) {
    // 测试多节点场景
    detector_->registerNode("node_1");
    detector_->registerNode("node_2");
    detector_->registerNode("node_3");

    detector_->start();

    // node_1持续心跳
    for (int i = 0; i < 5; i++) {
        detector_->reportHeartbeat("node_1");
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    // node_1应该在线，其他节点可能离线
    EXPECT_EQ(detector_->getNodeStatus("node_1"),
              disaster_recovery::storage::NodeStatus::ONLINE);

    detector_->stop();
}

TEST_F(FailureDetectorTest, ConfigGetters) {
    // 测试配置获取
    EXPECT_EQ(detector_->getHeartbeatInterval(), 100);
    EXPECT_EQ(detector_->getHeartbeatTimeout(), 300);
    EXPECT_EQ(detector_->getSuspectTimeout(), 500);
}
