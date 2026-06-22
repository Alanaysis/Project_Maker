#include "storage/replica_manager.h"
#include <algorithm>
#include <functional>
#include <set>

namespace disaster_recovery {
namespace storage {

ReplicaManager::ReplicaManager(int replication_factor,
                               int write_quorum,
                               int read_quorum)
    : replication_factor_(replication_factor),
      write_quorum_(write_quorum),
      read_quorum_(read_quorum) {
}

std::vector<NodeId> ReplicaManager::selectWriteNodes(
    const std::vector<NodeInfo>& available_nodes,
    const ShardId& shard_id) {
    std::vector<NodeId> selected;

    if (available_nodes.empty()) {
        return selected;
    }

    // 按节点ID排序，保证一致性
    std::vector<NodeInfo> sorted_nodes = available_nodes;
    std::sort(sorted_nodes.begin(), sorted_nodes.end(),
              [](const NodeInfo& a, const NodeInfo& b) {
                  return a.id < b.id;
              });

    // 使用一致性哈希选择节点
    // 这里简化实现：选择前N个可用节点
    for (const auto& node : sorted_nodes) {
        if (selected.size() >= static_cast<size_t>(replication_factor_)) {
            break;
        }

        // 检查节点是否在线
        if (node.status == NodeStatus::ONLINE) {
            selected.push_back(node.id);
        }
    }

    // 如果在线节点不够，选择降级节点
    if (selected.size() < static_cast<size_t>(replication_factor_)) {
        for (const auto& node : sorted_nodes) {
            if (selected.size() >= static_cast<size_t>(replication_factor_)) {
                break;
            }

            if (node.status == NodeStatus::DEGRADED &&
                std::find(selected.begin(), selected.end(), node.id) == selected.end()) {
                selected.push_back(node.id);
            }
        }
    }

    return selected;
}

std::vector<NodeId> ReplicaManager::selectReadNodes(
    const std::vector<ReplicaInfo>& replicas) {
    std::vector<NodeId> selected;

    // 选择健康或降级的副本
    for (const auto& replica : replicas) {
        if (selected.size() >= static_cast<size_t>(read_quorum_)) {
            break;
        }

        if (replica.status == ReplicaStatus::HEALTHY ||
            replica.status == ReplicaStatus::DEGRADED) {
            selected.push_back(replica.node_id);
        }
    }

    return selected;
}

bool ReplicaManager::checkWriteQuorum(const std::vector<Status>& responses) {
    int success_count = 0;
    for (const auto& response : responses) {
        if (response.ok()) {
            success_count++;
        }
    }
    return success_count >= write_quorum_;
}

bool ReplicaManager::checkReadQuorum(const std::vector<Status>& responses) {
    int success_count = 0;
    for (const auto& response : responses) {
        if (response.ok()) {
            success_count++;
        }
    }
    return success_count >= read_quorum_;
}

void ReplicaManager::addReplica(const ShardId& shard_id,
                                const NodeId& node_id,
                                ReplicaStatus status) {
    // 创建副本信息
    ReplicaInfo replica;
    replica.shard_id = shard_id;
    replica.node_id = node_id;
    replica.status = status;
    replica.last_verify = std::chrono::system_clock::now();

    // 添加到副本索引
    shard_replicas_[shard_id].push_back(replica);

    // 添加到节点索引
    node_shards_[node_id].push_back(shard_id);
}

void ReplicaManager::removeReplica(const ShardId& shard_id,
                                   const NodeId& node_id) {
    // 从副本索引中移除
    auto it = shard_replicas_.find(shard_id);
    if (it != shard_replicas_.end()) {
        auto& replicas = it->second;
        replicas.erase(
            std::remove_if(replicas.begin(), replicas.end(),
                           [&node_id](const ReplicaInfo& r) {
                               return r.node_id == node_id;
                           }),
            replicas.end());

        // 如果没有副本了，删除整个条目
        if (replicas.empty()) {
            shard_replicas_.erase(it);
        }
    }

    // 从节点索引中移除
    auto node_it = node_shards_.find(node_id);
    if (node_it != node_shards_.end()) {
        auto& shards = node_it->second;
        shards.erase(
            std::remove(shards.begin(), shards.end(), shard_id),
            shards.end());

        // 如果没有分片了，删除整个条目
        if (shards.empty()) {
            node_shards_.erase(node_it);
        }
    }
}

std::vector<ReplicaInfo> ReplicaManager::getReplicas(
    const ShardId& shard_id) const {
    auto it = shard_replicas_.find(shard_id);
    if (it != shard_replicas_.end()) {
        return it->second;
    }
    return {};
}

std::vector<ShardId> ReplicaManager::getShardsOnNode(
    const NodeId& node_id) const {
    auto it = node_shards_.find(node_id);
    if (it != node_shards_.end()) {
        return it->second;
    }
    return {};
}

void ReplicaManager::updateReplicaStatus(const ShardId& shard_id,
                                         const NodeId& node_id,
                                         ReplicaStatus status) {
    auto it = shard_replicas_.find(shard_id);
    if (it != shard_replicas_.end()) {
        for (auto& replica : it->second) {
            if (replica.node_id == node_id) {
                replica.status = status;
                replica.last_verify = std::chrono::system_clock::now();
                break;
            }
        }
    }
}

bool ReplicaManager::isShardHealthy(const ShardId& shard_id) const {
    auto it = shard_replicas_.find(shard_id);
    if (it == shard_replicas_.end()) {
        return false;
    }

    // 计算健康副本数
    int healthy_count = 0;
    for (const auto& replica : it->second) {
        if (replica.status == ReplicaStatus::HEALTHY) {
            healthy_count++;
        }
    }

    // 至少需要read_quorum个健康副本
    return healthy_count >= read_quorum_;
}

std::vector<ShardId> ReplicaManager::getShardsToRecover(
    const NodeId& failed_node_id) const {
    std::vector<ShardId> shards_to_recover;

    // 获取故障节点上的所有分片
    auto it = node_shards_.find(failed_node_id);
    if (it == node_shards_.end()) {
        return shards_to_recover;
    }

    // 检查每个分片的健康状态
    for (const auto& shard_id : it->second) {
        if (!isShardHealthy(shard_id)) {
            shards_to_recover.push_back(shard_id);
        }
    }

    return shards_to_recover;
}

bool ReplicaManager::validateConfig() const {
    // 检查基本约束
    if (replication_factor_ <= 0 ||
        write_quorum_ <= 0 ||
        read_quorum_ <= 0) {
        return false;
    }

    // 检查Quorum约束: W + R > N
    if (write_quorum_ + read_quorum_ <= replication_factor_) {
        return false;
    }

    // 检查Quorum不超过副本因子
    if (write_quorum_ > replication_factor_ ||
        read_quorum_ > replication_factor_) {
        return false;
    }

    return true;
}

size_t ReplicaManager::hashNode(const NodeId& node_id,
                                const ShardId& shard_id) const {
    // 简单的哈希实现
    std::hash<std::string> hasher;
    return hasher(node_id + shard_id);
}

}  // namespace storage
}  // namespace disaster_recovery
