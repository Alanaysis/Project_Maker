#include "node/storage_node.h"
#include <cstring>
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace disaster_recovery {
namespace node {

StorageNode::StorageNode(const StorageNodeConfig& config)
    : config_(config),
      status_(NodeStatus::OFFLINE),
      used_capacity_(0) {
}

Status StorageNode::init() {
    // 在实际系统中，这里会创建数据目录、初始化存储引擎等
    status_ = NodeStatus::ONLINE;
    last_heartbeat_ = std::chrono::system_clock::now();
    return Status::OK();
}

Status StorageNode::storeShard(const Shard& shard) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 检查节点状态
    if (status_ != NodeStatus::ONLINE) {
        return Status(StatusCode::UNAVAILABLE, "Node is not online");
    }

    // 检查容量
    if (!checkCapacity(shard.data.size())) {
        return Status(StatusCode::RESOURCE_EXHAUSTED, "Not enough capacity");
    }

    // 检查是否已存在
    if (shards_.find(shard.id) != shards_.end()) {
        return Status(StatusCode::ALREADY_EXISTS, "Shard already exists");
    }

    // 存储分片
    shards_[shard.id] = shard;
    used_capacity_ += shard.data.size();

    return Status::OK();
}

Status StorageNode::readShard(const ShardId& shard_id, Shard& shard) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 检查节点状态
    if (status_ != NodeStatus::ONLINE) {
        return Status(StatusCode::UNAVAILABLE, "Node is not online");
    }

    // 查找分片
    auto it = shards_.find(shard_id);
    if (it == shards_.end()) {
        return Status(StatusCode::NOT_FOUND, "Shard not found");
    }

    // 复制分片数据
    shard = it->second;

    return Status::OK();
}

Status StorageNode::deleteShard(const ShardId& shard_id) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 查找分片
    auto it = shards_.find(shard_id);
    if (it == shards_.end()) {
        return Status(StatusCode::NOT_FOUND, "Shard not found");
    }

    // 更新容量
    used_capacity_ -= it->second.data.size();

    // 删除分片
    shards_.erase(it);

    return Status::OK();
}

bool StorageNode::hasShard(const ShardId& shard_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return shards_.find(shard_id) != shards_.end();
}

NodeInfo StorageNode::getNodeInfo() const {
    std::lock_guard<std::mutex> lock(mutex_);

    NodeInfo info;
    info.id = config_.id;
    info.address = config_.address;
    info.port = config_.port;
    info.status = status_;
    info.capacity = config_.capacity;
    info.used = used_capacity_;
    info.available = config_.capacity - used_capacity_;
    info.last_heartbeat = last_heartbeat_;
    info.shard_count = shards_.size();

    return info;
}

size_t StorageNode::getShardCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return shards_.size();
}

uint64_t StorageNode::getUsedCapacity() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return used_capacity_;
}

uint64_t StorageNode::getAvailableCapacity() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return config_.capacity - used_capacity_;
}

std::vector<ShardId> StorageNode::getAllShardIds() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::vector<ShardId> ids;
    ids.reserve(shards_.size());
    for (const auto& pair : shards_) {
        ids.push_back(pair.first);
    }
    return ids;
}

HeartbeatResponse StorageNode::handleHeartbeat() {
    std::lock_guard<std::mutex> lock(mutex_);

    last_heartbeat_ = std::chrono::system_clock::now();

    HeartbeatResponse response;
    response.status = Status::OK();
    response.timestamp = last_heartbeat_;
    response.need_recovery = false;

    return response;
}

bool StorageNode::verifyShard(const ShardId& shard_id) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = shards_.find(shard_id);
    if (it == shards_.end()) {
        return false;
    }

    // 验证校验和
    std::string current_checksum = calculateChecksum(
        it->second.data.data(), it->second.data.size());
    return current_checksum == it->second.checksum;
}

std::string StorageNode::calculateChecksum(const uint8_t* data,
                                           size_t size) const {
    // 简单的CRC32校验和实现
    uint32_t crc = 0xFFFFFFFF;

    for (size_t i = 0; i < size; i++) {
        crc ^= data[i];
        for (int j = 0; j < 8; j++) {
            if (crc & 1) {
                crc = (crc >> 1) ^ 0xEDB88320;
            } else {
                crc >>= 1;
            }
        }
    }

    crc ^= 0xFFFFFFFF;

    // 转换为十六进制字符串
    std::stringstream ss;
    ss << std::hex << std::setw(8) << std::setfill('0') << crc;
    return ss.str();
}

bool StorageNode::checkCapacity(uint64_t size) const {
    return (used_capacity_ + size) <= config_.capacity;
}

}  // namespace node
}  // namespace disaster_recovery
