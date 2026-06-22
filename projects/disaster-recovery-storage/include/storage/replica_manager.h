#ifndef DISASTER_RECOVERY_STORAGE_STORAGE_REPLICA_MANAGER_H_
#define DISASTER_RECOVERY_STORAGE_STORAGE_REPLICA_MANAGER_H_

#include <vector>
#include <unordered_map>
#include <string>
#include "storage/types.h"

namespace disaster_recovery {
namespace storage {

/**
 * @brief 副本管理器
 *
 * 管理数据副本的放置、一致性和恢复
 *
 * @note 实现NWR Quorum机制
 */
class ReplicaManager {
public:
    /**
     * @brief 构造函数
     *
     * @param replication_factor 副本因子
     * @param write_quorum 写入Quorum
     * @param read_quorum 读取Quorum
     */
    ReplicaManager(int replication_factor = 3,
                   int write_quorum = 2,
                   int read_quorum = 2);

    /**
     * @brief 析构函数
     */
    ~ReplicaManager() = default;

    /**
     * @brief 选择写入节点
     *
     * 根据副本策略选择节点
     *
     * @param available_nodes 可用节点列表
     * @param shard_id 分片ID
     * @return 选择的节点ID列表
     */
    std::vector<NodeId> selectWriteNodes(
        const std::vector<NodeInfo>& available_nodes,
        const ShardId& shard_id);

    /**
     * @brief 选择读取节点
     *
     * 从副本中选择节点进行读取
     *
     * @param replicas 副本列表
     * @return 选择的节点ID列表
     */
    std::vector<NodeId> selectReadNodes(
        const std::vector<ReplicaInfo>& replicas);

    /**
     * @brief 检查写入Quorum
     *
     * @param responses 写入响应列表
     * @return true 如果达到Quorum，false 否则
     */
    bool checkWriteQuorum(const std::vector<Status>& responses);

    /**
     * @brief 检查读取Quorum
     *
     * @param responses 读取响应列表
     * @return true 如果达到Quorum，false 否则
     */
    bool checkReadQuorum(const std::vector<Status>& responses);

    /**
     * @brief 添加副本记录
     *
     * @param shard_id 分片ID
     * @param node_id 节点ID
     * @param status 副本状态
     */
    void addReplica(const ShardId& shard_id,
                    const NodeId& node_id,
                    ReplicaStatus status = ReplicaStatus::HEALTHY);

    /**
     * @brief 移除副本记录
     *
     * @param shard_id 分片ID
     * @param node_id 节点ID
     */
    void removeReplica(const ShardId& shard_id,
                       const NodeId& node_id);

    /**
     * @brief 获取分片的所有副本
     *
     * @param shard_id 分片ID
     * @return 副本列表
     */
    std::vector<ReplicaInfo> getReplicas(const ShardId& shard_id) const;

    /**
     * @brief 获取节点上的所有分片
     *
     * @param node_id 节点ID
     * @return 分片ID列表
     */
    std::vector<ShardId> getShardsOnNode(const NodeId& node_id) const;

    /**
     * @brief 更新副本状态
     *
     * @param shard_id 分片ID
     * @param node_id 节点ID
     * @param status 新状态
     */
    void updateReplicaStatus(const ShardId& shard_id,
                             const NodeId& node_id,
                             ReplicaStatus status);

    /**
     * @brief 检查分片是否健康
     *
     * @param shard_id 分片ID
     * @return true 如果健康，false 否则
     */
    bool isShardHealthy(const ShardId& shard_id) const;

    /**
     * @brief 获取需要恢复的分片
     *
     * @param failed_node_id 故障节点ID
     * @return 需要恢复的分片ID列表
     */
    std::vector<ShardId> getShardsToRecover(
        const NodeId& failed_node_id) const;

    /**
     * @brief 获取副本因子
     *
     * @return 副本因子
     */
    int getReplicationFactor() const { return replication_factor_; }

    /**
     * @brief 获取写入Quorum
     *
     * @return 写入Quorum
     */
    int getWriteQuorum() const { return write_quorum_; }

    /**
     * @brief 获取读取Quorum
     *
     * @return 读取Quorum
     */
    int getReadQuorum() const { return read_quorum_; }

    /**
     * @brief 验证Quorum配置
     *
     * @return true 如果配置有效，false 否则
     */
    bool validateConfig() const;

private:
    int replication_factor_;  // 副本因子
    int write_quorum_;        // 写入Quorum
    int read_quorum_;         // 读取Quorum

    // 副本索引: shard_id -> [ReplicaInfo]
    std::unordered_map<ShardId, std::vector<ReplicaInfo>> shard_replicas_;

    // 节点索引: node_id -> [shard_id]
    std::unordered_map<NodeId, std::vector<ShardId>> node_shards_;

    /**
     * @brief 计算节点哈希值
     *
     * @param node_id 节点ID
     * @param shard_id 分片ID
     * @return 哈希值
     */
    size_t hashNode(const NodeId& node_id,
                    const ShardId& shard_id) const;
};

}  // namespace storage
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_STORAGE_REPLICA_MANAGER_H_
