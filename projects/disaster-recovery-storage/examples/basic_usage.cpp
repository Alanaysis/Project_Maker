/**
 * @file basic_usage.cpp
 * @brief 基本使用示例
 *
 * 演示容灾数据存储系统的基本功能
 */

#include <iostream>
#include <vector>
#include <string>
#include <random>
#include <cassert>

// 包含核心头文件
#include "ec/galois_field.h"
#include "ec/reed_solomon.h"
#include "storage/data_sharder.h"
#include "storage/replica_manager.h"
#include "node/storage_node.h"
#include "network/failure_detector.h"
#include "utils/checksum.h"

using namespace disaster_recovery;

// 生成随机数据
std::vector<uint8_t> generateRandomData(size_t size) {
    std::vector<uint8_t> data(size);
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(0, 255);
    for (auto& byte : data) {
        byte = static_cast<uint8_t>(dist(rng));
    }
    return data;
}

// 演示有限域运算
void demoGaloisField() {
    std::cout << "=== 有限域 GF(2^8) 演示 ===" << std::endl;

    ec::GaloisField gf;
    gf.init();

    // 基本运算
    uint8_t a = 0x53;
    uint8_t b = 0xCA;

    std::cout << "a = 0x" << std::hex << (int)a << std::endl;
    std::cout << "b = 0x" << std::hex << (int)b << std::endl;
    std::cout << "a + b = 0x" << std::hex << (int)gf.add(a, b) << std::endl;
    std::cout << "a * b = 0x" << std::hex << (int)gf.multiply(a, b) << std::endl;
    std::cout << "a / b = 0x" << std::hex << (int)gf.divide(a, b) << std::endl;
    std::cout << "a^(-1) = 0x" << std::hex << (int)gf.inverse(a) << std::endl;

    // 验证: a * a^(-1) = 1
    uint8_t a_inv = gf.inverse(a);
    uint8_t product = gf.multiply(a, a_inv);
    std::cout << "a * a^(-1) = 0x" << std::hex << (int)product << std::endl;
    assert(product == 0x01);

    std::cout << std::endl;
}

// 演示纠删码编解码
void demoErasureCoding() {
    std::cout << "=== 纠删码编解码演示 ===" << std::endl;

    // 创建Reed-Solomon编解码器: 4个数据分片，2个校验分片
    ec::ReedSolomon rs(4, 2);
    std::cout << "数据分片数: " << rs.getDataShards() << std::endl;
    std::cout << "校验分片数: " << rs.getParityShards() << std::endl;
    std::cout << "总分片数: " << rs.getTotalShards() << std::endl;

    // 生成测试数据
    size_t data_size = 1024;
    auto original_data = generateRandomData(data_size);
    std::cout << "原始数据大小: " << data_size << " 字节" << std::endl;

    // 编码
    std::vector<std::vector<uint8_t>> shards;
    int result = rs.encode(original_data.data(), data_size, shards);
    assert(result == 0);
    std::cout << "编码成功，生成 " << shards.size() << " 个分片" << std::endl;

    // 显示分片信息
    for (size_t i = 0; i < shards.size(); i++) {
        std::cout << "  分片 " << i << ": " << shards[i].size() << " 字节";
        if (i < rs.getDataShards()) {
            std::cout << " (数据)" << std::endl;
        } else {
            std::cout << " (校验)" << std::endl;
        }
    }

    // 解码（使用所有分片）
    std::vector<bool> available(rs.getTotalShards(), true);
    std::vector<uint8_t> decoded_data;
    result = rs.decode(shards, available, decoded_data);
    assert(result == 0);

    // 验证数据
    bool data_match = (decoded_data.size() == data_size);
    for (size_t i = 0; i < data_size && data_match; i++) {
        if (decoded_data[i] != original_data[i]) {
            data_match = false;
        }
    }
    std::cout << "解码验证: " << (data_match ? "成功" : "失败") << std::endl;

    // 模拟丢失一个分片
    std::cout << "\n模拟丢失分片 0..." << std::endl;
    available[0] = false;
    result = rs.decode(shards, available, decoded_data);
    assert(result == 0);

    data_match = (decoded_data.size() == data_size);
    for (size_t i = 0; i < data_size && data_match; i++) {
        if (decoded_data[i] != original_data[i]) {
            data_match = false;
        }
    }
    std::cout << "从5个分片恢复数据: " << (data_match ? "成功" : "失败") << std::endl;

    std::cout << std::endl;
}

// 演示数据分片
void demoDataSharding() {
    std::cout << "=== 数据分片演示 ===" << std::endl;

    storage::DataSharder sharder(256);  // 256字节分片
    std::cout << "分片大小: " << sharder.getShardSize() << " 字节" << std::endl;

    // 生成测试数据
    size_t data_size = 1000;  // 不是256的整数倍
    auto original_data = generateRandomData(data_size);
    std::cout << "原始数据大小: " << data_size << " 字节" << std::endl;

    // 分片
    std::vector<storage::Shard> shards;
    storage::Status status = sharder.shard(original_data.data(), data_size, shards);
    assert(status.ok());

    std::cout << "分片数量: " << shards.size() << std::endl;
    for (const auto& shard : shards) {
        std::cout << "  分片 " << shard.index << ": "
                  << shard.data.size() << " 字节, "
                  << "校验和=" << shard.checksum << std::endl;
    }

    // 重组
    std::vector<uint8_t> reassembled_data;
    status = sharder.reassemble(shards, reassembled_data, data_size);
    assert(status.ok());

    // 验证
    bool data_match = (reassembled_data.size() == data_size);
    for (size_t i = 0; i < data_size && data_match; i++) {
        if (reassembled_data[i] != original_data[i]) {
            data_match = false;
        }
    }
    std::cout << "重组验证: " << (data_match ? "成功" : "失败") << std::endl;

    std::cout << std::endl;
}

// 演示副本管理
void demoReplicaManagement() {
    std::cout << "=== 副本管理演示 ===" << std::endl;

    // 创建副本管理器: N=3, W=2, R=2
    storage::ReplicaManager manager(3, 2, 2);
    std::cout << "副本因子: " << manager.getReplicationFactor() << std::endl;
    std::cout << "写入Quorum: " << manager.getWriteQuorum() << std::endl;
    std::cout << "读取Quorum: " << manager.getReadQuorum() << std::endl;
    std::cout << "配置有效: " << (manager.validateConfig() ? "是" : "否") << std::endl;

    // 添加副本
    manager.addReplica("shard_1", "node_1", storage::ReplicaStatus::HEALTHY);
    manager.addReplica("shard_1", "node_2", storage::ReplicaStatus::HEALTHY);
    manager.addReplica("shard_1", "node_3", storage::ReplicaStatus::HEALTHY);

    // 检查分片健康状态
    std::cout << "分片 shard_1 健康: "
              << (manager.isShardHealthy("shard_1") ? "是" : "否") << std::endl;

    // 模拟节点故障
    std::cout << "模拟 node_3 故障..." << std::endl;
    manager.updateReplicaStatus("shard_1", "node_3", storage::ReplicaStatus::LOST);

    std::cout << "分片 shard_1 健康: "
              << (manager.isShardHealthy("shard_1") ? "是" : "否") << std::endl;

    // 获取需要恢复的分片
    auto shards_to_recover = manager.getShardsToRecover("node_3");
    std::cout << "需要恢复的分片数: " << shards_to_recover.size() << std::endl;

    std::cout << std::endl;
}

// 演示故障检测
void demoFailureDetection() {
    std::cout << "=== 故障检测演示 ===" << std::endl;

    network::FailureDetector detector(1000, 3000, 5000);  // 1秒心跳，3秒超时
    std::cout << "心跳间隔: " << detector.getHeartbeatInterval() << " ms" << std::endl;
    std::cout << "心跳超时: " << detector.getHeartbeatTimeout() << " ms" << std::endl;

    // 注册节点
    detector.registerNode("node_1");
    detector.registerNode("node_2");
    std::cout << "注册节点: node_1, node_2" << std::endl;

    // 初始状态
    std::cout << "node_1 在线: "
              << (detector.isNodeOnline("node_1") ? "是" : "否") << std::endl;

    // 发送心跳
    detector.reportHeartbeat("node_1");
    std::cout << "收到 node_1 心跳" << std::endl;

    // 获取节点信息
    auto info = detector.getNodeInfo("node_1");
    std::cout << "node_1 状态: ";
    switch (info.status) {
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

    std::cout << std::endl;
}

// 演示校验和
void demoChecksum() {
    std::cout << "=== 校验和演示 ===" << std::endl;

    std::vector<uint8_t> data = {0x48, 0x65, 0x6C, 0x6C, 0x6F};  // "Hello"
    std::cout << "数据: Hello" << std::endl;

    // CRC32
    uint32_t crc = utils::Checksum::crc32(data);
    std::cout << "CRC32: 0x" << std::hex << crc << std::endl;

    // Adler32
    uint32_t adler = utils::Checksum::adler32(data.data(), data.size());
    std::cout << "Adler32: 0x" << std::hex << adler << std::endl;

    // FNV-1a
    uint64_t fnv = utils::Checksum::fnv1a(data.data(), data.size());
    std::cout << "FNV-1a: 0x" << std::hex << fnv << std::endl;

    // 验证
    std::cout << "CRC32 验证: "
              << (utils::Checksum::verifyCrc32(data, crc) ? "成功" : "失败")
              << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  容灾数据存储系统 - 基本使用示例" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;

    // 运行各个演示
    demoGaloisField();
    demoErasureCoding();
    demoDataSharding();
    demoReplicaManagement();
    demoFailureDetection();
    demoChecksum();

    std::cout << "========================================" << std::endl;
    std::cout << "  所有演示完成！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
