/**
 * @file fault_tolerance.cpp
 * @brief 容错机制示例
 *
 * 演示容灾存储系统的故障检测和恢复机制
 */

#include <iostream>
#include <vector>
#include <memory>
#include <thread>
#include <chrono>
#include <random>

#include "node/storage_node.h"
#include "network/failure_detector.h"
#include "storage/replica_manager.h"
#include "ec/reed_solomon.h"
#include "storage/data_sharder.h"
#include "utils/checksum.h"

using namespace disaster_recovery;

// 创建存储节点
std::unique_ptr<node::StorageNode> createNode(
    const std::string& id,
    const std::string& address,
    uint16_t port) {
    node::StorageNodeConfig config;
    config.id = id;
    config.address = address;
    config.port = port;
    config.data_dir = "/tmp/" + id;
    config.capacity = 1024 * 1024 * 100;  // 100MB

    auto node = std::make_unique<node::StorageNode>(config);
    node->init();
    return node;
}

// 演示多副本存储
void demoReplicatedStorage() {
    std::cout << "=== 多副本存储演示 ===" << std::endl;
    std::cout << std::endl;

    // 创建3个存储节点
    std::vector<std::unique_ptr<node::StorageNode>> nodes;
    nodes.push_back(createNode("node_1", "192.168.1.1", 8001));
    nodes.push_back(createNode("node_2", "192.168.1.2", 8002));
    nodes.push_back(createNode("node_3", "192.168.1.3", 8003));

    std::cout << "创建了 " << nodes.size() << " 个存储节点" << std::endl;

    // 创建副本管理器
    storage::ReplicaManager replica_manager(3, 2, 2);

    // 创建测试数据
    storage::DataSharder sharder(256);
    std::vector<uint8_t> original_data(1024, 0x42);  // 1KB数据

    // 分片
    std::vector<storage::Shard> shards;
    sharder.shard(original_data.data(), original_data.size(), shards);
    std::cout << "数据已分片: " << shards.size() << " 个分片" << std::endl;

    // 写入到多个节点
    std::cout << "写入数据到多个节点..." << std::endl;
    for (size_t i = 0; i < shards.size(); i++) {
        // 选择写入节点
        std::vector<storage::NodeInfo> node_infos;
        for (const auto& node : nodes) {
            node_infos.push_back(node->getNodeInfo());
        }

        auto selected_nodes = replica_manager.selectWriteNodes(
            node_infos, shards[i].id);

        // 写入到选中的节点
        for (const auto& node_id : selected_nodes) {
            for (auto& node : nodes) {
                if (node->getId() == node_id) {
                    storage::Status status = node->storeShard(shards[i]);
                    if (status.ok()) {
                        replica_manager.addReplica(
                            shards[i].id, node_id,
                            storage::ReplicaStatus::HEALTHY);
                        std::cout << "  分片 " << shards[i].id
                                  << " 写入到 " << node_id << std::endl;
                    }
                    break;
                }
            }
        }
    }

    // 显示存储状态
    std::cout << "\n存储状态:" << std::endl;
    for (const auto& node : nodes) {
        auto info = node->getNodeInfo();
        std::cout << "  " << info.id << ": "
                  << info.shard_count << " 个分片, "
                  << info.used / 1024 << " KB 已用" << std::endl;
    }

    // 模拟节点故障
    std::cout << "\n模拟 node_3 故障..." << std::endl;
    nodes[2]->setStatus(storage::NodeStatus::OFFLINE);

    // 检查数据可用性
    std::cout << "检查数据可用性:" << std::endl;
    for (const auto& shard : shards) {
        bool healthy = replica_manager.isShardHealthy(shard.id);
        std::cout << "  分片 " << shard.id << ": "
                  << (healthy ? "可用" : "不可用") << std::endl;
    }

    std::cout << std::endl;
}

// 演示故障检测
void demoFailureDetection() {
    std::cout << "=== 故障检测演示 ===" << std::endl;
    std::cout << std::endl;

    // 创建故障检测器
    network::FailureDetector detector(1000, 3000, 5000);  // 1秒心跳，3秒超时
    std::cout << "故障检测器配置:" << std::endl;
    std::cout << "  心跳间隔: " << detector.getHeartbeatInterval() << " ms" << std::endl;
    std::cout << "  心跳超时: " << detector.getHeartbeatTimeout() << " ms" << std::endl;
    std::cout << std::endl;

    // 注册节点
    detector.registerNode("node_1");
    detector.registerNode("node_2");
    detector.registerNode("node_3");
    std::cout << "注册了 3 个节点" << std::endl;

    // 设置回调
    detector.setFailureCallback([](const storage::NodeId& node_id) {
        std::cout << "  [回调] 节点故障: " << node_id << std::endl;
    });

    detector.setRecoveryCallback([](const storage::NodeId& node_id) {
        std::cout << "  [回调] 节点恢复: " << node_id << std::endl;
    });

    // 启动检测器
    detector.start();
    std::cout << "启动故障检测器" << std::endl;

    // 模拟正常运行
    std::cout << "\n模拟正常运行 (3秒)..." << std::endl;
    for (int i = 0; i < 3; i++) {
        detector.reportHeartbeat("node_1");
        detector.reportHeartbeat("node_2");
        detector.reportHeartbeat("node_3");
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    // 显示节点状态
    auto online_nodes = detector.getOnlineNodes();
    std::cout << "在线节点数: " << online_nodes.size() << std::endl;

    // 模拟 node_3 停止心跳
    std::cout << "\n模拟 node_3 停止心跳 (4秒)..." << std::endl;
    for (int i = 0; i < 4; i++) {
        detector.reportHeartbeat("node_1");
        detector.reportHeartbeat("node_2");
        // node_3 不发送心跳
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    // 检查 node_3 状态
    auto node3_status = detector.getNodeStatus("node_3");
    std::cout << "node_3 状态: ";
    switch (node3_status) {
        case storage::NodeStatus::ONLINE:
            std::cout << "在线";
            break;
        case storage::NodeStatus::OFFLINE:
            std::cout << "离线";
            break;
        case storage::NodeStatus::SUSPECTED:
            std::cout << "疑似故障";
            break;
        default:
            std::cout << "未知";
    }
    std::cout << std::endl;

    // 模拟 node_3 恢复
    std::cout << "\n模拟 node_3 恢复心跳..." << std::endl;
    detector.reportHeartbeat("node_3");

    node3_status = detector.getNodeStatus("node_3");
    std::cout << "node_3 状态: ";
    switch (node3_status) {
        case storage::NodeStatus::ONLINE:
            std::cout << "在线";
            break;
        case storage::NodeStatus::OFFLINE:
            std::cout << "离线";
            break;
        case storage::NodeStatus::SUSPECTED:
            std::cout << "疑似故障";
            break;
        default:
            std::cout << "未知";
    }
    std::cout << std::endl;

    // 停止检测器
    detector.stop();
    std::cout << std::endl;
}

// 演示纠删码容错
void demoErasureCodingFaultTolerance() {
    std::cout << "=== 纠删码容错演示 ===" << std::endl;
    std::cout << std::endl;

    // 创建编解码器: 4个数据分片，2个校验分片
    ec::ReedSolomon rs(4, 2);
    std::cout << "纠删码配置: k=4, m=2" << std::endl;
    std::cout << "容忍故障数: " << rs.getParityShards() << std::endl;
    std::cout << std::endl;

    // 创建测试数据
    size_t data_size = 1024;
    std::vector<uint8_t> original_data(data_size);
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(0, 255);
    for (auto& byte : original_data) {
        byte = static_cast<uint8_t>(dist(rng));
    }

    // 编码
    std::vector<std::vector<uint8_t>> shards;
    rs.encode(original_data.data(), data_size, shards);
    std::cout << "数据已编码: " << shards.size() << " 个分片" << std::endl;

    // 创建6个存储节点
    std::vector<std::unique_ptr<node::StorageNode>> nodes;
    for (int i = 0; i < 6; i++) {
        std::string id = "node_" + std::to_string(i + 1);
        nodes.push_back(createNode(id, "192.168.1." + std::to_string(i + 1),
                                   8000 + i));
    }

    // 将分片存储到不同节点
    for (size_t i = 0; i < shards.size(); i++) {
        storage::Shard shard;
        shard.id = "shard_" + std::to_string(i);
        shard.data = shards[i];
        shard.index = i;
        shard.is_parity = (i >= 4);

        nodes[i]->storeShard(shard);
        std::cout << "分片 " << i << " 存储到 node_" << i + 1 << std::endl;
    }

    // 模拟丢失2个节点
    std::cout << "\n模拟丢失 node_1 和 node_5..." << std::endl;
    nodes[0]->setStatus(storage::NodeStatus::OFFLINE);
    nodes[4]->setStatus(storage::NodeStatus::OFFLINE);

    // 尝试恢复数据
    std::cout << "尝试从剩余节点恢复数据..." << std::endl;

    // 收集可用分片
    std::vector<std::vector<uint8_t>> available_shards;
    std::vector<bool> shard_available(6, false);

    for (size_t i = 0; i < nodes.size(); i++) {
        if (nodes[i]->getStatus() == storage::NodeStatus::ONLINE) {
            storage::Shard shard;
            std::string shard_id = "shard_" + std::to_string(i);
            if (nodes[i]->readShard(shard_id, shard).ok()) {
                available_shards.push_back(shard.data);
                shard_available[i] = true;
            }
        }
    }

    std::cout << "可用分片数: " << available_shards.size() << std::endl;

    // 解码恢复
    if (rs.canRecover(available_shards.size())) {
        std::vector<uint8_t> recovered_data;
        int result = rs.decode(shards, shard_available, recovered_data);

        if (result == 0) {
            // 验证数据
            bool match = (recovered_data.size() == data_size);
            for (size_t i = 0; i < data_size && match; i++) {
                if (recovered_data[i] != original_data[i]) {
                    match = false;
                }
            }
            std::cout << "数据恢复: " << (match ? "成功" : "失败") << std::endl;
        } else {
            std::cout << "数据恢复: 失败 (解码错误)" << std::endl;
        }
    } else {
        std::cout << "数据恢复: 失败 (可用分片不足)" << std::endl;
    }

    std::cout << std::endl;
}

// 演示数据校验
void demoDataVerification() {
    std::cout << "=== 数据校验演示 ===" << std::endl;
    std::cout << std::endl;

    // 创建测试数据
    std::vector<uint8_t> data = {0x48, 0x65, 0x6C, 0x6C, 0x6F};  // "Hello"
    std::cout << "原始数据: Hello" << std::endl;

    // 计算校验和
    uint32_t crc = utils::Checksum::crc32(data);
    std::cout << "CRC32 校验和: 0x" << std::hex << crc << std::endl;

    // 验证数据完整性
    std::cout << "\n验证数据完整性:" << std::endl;

    // 完整数据
    bool valid = utils::Checksum::verifyCrc32(data, crc);
    std::cout << "  完整数据: " << (valid ? "通过" : "失败") << std::endl;

    // 损坏数据
    std::vector<uint8_t> corrupted_data = data;
    corrupted_data[0] = 0x49;  // 修改一个字节
    valid = utils::Checksum::verifyCrc32(corrupted_data, crc);
    std::cout << "  损坏数据: " << (valid ? "通过" : "失败") << std::endl;

    // 演示分块校验
    std::cout << "\n分块校验演示:" << std::endl;
    std::vector<uint8_t> large_data(1024, 0x42);  // 1KB数据
    auto block_checksums = utils::Checksum::blockCrc32(
        large_data.data(), large_data.size(), 256);

    std::cout << "数据大小: 1024 字节" << std::endl;
    std::cout << "块大小: 256 字节" << std::endl;
    std::cout << "块数: " << block_checksums.size() << std::endl;
    for (size_t i = 0; i < block_checksums.size(); i++) {
        std::cout << "  块 " << i << " CRC32: 0x" << std::hex
                  << block_checksums[i] << std::endl;
    }

    std::cout << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  容错机制示例" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;

    // 运行各个演示
    demoReplicatedStorage();
    demoFailureDetection();
    demoErasureCodingFaultTolerance();
    demoDataVerification();

    std::cout << "========================================" << std::endl;
    std::cout << "  所有演示完成！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
