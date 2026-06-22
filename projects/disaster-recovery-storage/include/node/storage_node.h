#ifndef DISASTER_RECOVERY_STORAGE_NODE_STORAGE_NODE_H_
#define DISASTER_RECOVERY_STORAGE_NODE_STORAGE_NODE_H_

#include <string>
#include <unordered_map>
#include <mutex>
#include <vector>
#include "storage/types.h"

namespace disaster_recovery {
namespace node {

/**
 * @brief 存储节点配置
 */
struct StorageNodeConfig {
    NodeId id;                      // 节点ID
    std::string address;            // 网络地址
    uint16_t port;                  // 端口
    std::string data_dir;           // 数据目录
    uint64_t capacity;              // 总容量
};

/**
 * @brief 存储节点
 *
 * 模拟单个存储节点，负责本地数据的存储和管理
 *
 * @note 在实际系统中，每个节点运行独立的进程
 */
class StorageNode {
public:
    /**
     * @brief 构造函数
     *
     * @param config 节点配置
     */
    explicit StorageNode(const StorageNodeConfig& config);

    /**
     * @brief 析构函数
     */
    ~StorageNode() = default;

    /**
     * @brief 初始化节点
     *
     * @return 操作状态
     */
    Status init();

    /**
     * @brief 存储分片
     *
     * @param shard 分片数据
     * @return 操作状态
     */
    Status storeShard(const Shard& shard);

    /**
     * @brief 读取分片
     *
     * @param shard_id 分片ID
     * @param shard 输出的分片数据
     * @return 操作状态
     */
    Status readShard(const ShardId& shard_id, Shard& shard);

    /**
     * @brief 删除分片
     *
     * @param shard_id 分片ID
     * @return 操作状态
     */
    Status deleteShard(const ShardId& shard_id);

    /**
     * @brief 检查分片是否存在
     *
     * @param shard_id 分片ID
     * @return true 如果存在，false 否则
     */
    bool hasShard(const ShardId& shard_id) const;

    /**
     * @brief 获取节点信息
     *
     * @return 节点信息
     */
    NodeInfo getNodeInfo() const;

    /**
     * @brief 获取节点ID
     *
     * @return 节点ID
     */
    NodeId getId() const { return config_.id; }

    /**
     * @brief 获取节点状态
     *
     * @return 节点状态
     */
    NodeStatus getStatus() const { return status_; }

    /**
     * @brief 设置节点状态
     *
     * @param status 新状态
     */
    void setStatus(NodeStatus status) { status_ = status; }

    /**
     * @brief 获取存储的分片数量
     *
     * @return 分片数量
     */
    size_t getShardCount() const;

    /**
     * @brief 获取已用容量
     *
     * @return 已用容量（字节）
     */
    uint64_t getUsedCapacity() const;

    /**
     * @brief 获取可用容量
     *
     * @return 可用容量（字节）
     */
    uint64_t getAvailableCapacity() const;

    /**
     * @brief 获取所有分片ID
     *
     * @return 分片ID列表
     */
    std::vector<ShardId> getAllShardIds() const;

    /**
     * @brief 处理心跳
     *
     * @return 心跳响应
     */
    HeartbeatResponse handleHeartbeat();

    /**
     * @brief 验证分片完整性
     *
     * @param shard_id 分片ID
     * @return true 如果完整，false 否则
     */
    bool verifyShard(const ShardId& shard_id) const;

    /**
     * @brief 获取节点地址
     *
     * @return 节点地址
     */
    std::string getAddress() const { return config_.address; }

    /**
     * @brief 获取节点端口
     *
     * @return 节点端口
     */
    uint16_t getPort() const { return config_.port; }

private:
    StorageNodeConfig config_;     // 节点配置
    NodeStatus status_;            // 节点状态

    // 分片存储: shard_id -> Shard
    mutable std::mutex mutex_;
    std::unordered_map<ShardId, Shard> shards_;

    // 统计信息
    uint64_t used_capacity_;       // 已用容量
    std::chrono::system_clock::time_point last_heartbeat_;

    /**
     * @brief 计算校验和
     *
     * @param data 数据指针
     * @param size 数据大小
     * @return 校验和字符串
     */
    std::string calculateChecksum(const uint8_t* data, size_t size) const;

    /**
     * @brief 检查容量
     *
     * @param size 需要的容量
     * @return true 如果有足够空间，false 否则
     */
    bool checkCapacity(uint64_t size) const;
};

}  // namespace node
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_NODE_STORAGE_NODE_H_
