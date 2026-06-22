#ifndef DISASTER_RECOVERY_STORAGE_STORAGE_TYPES_H_
#define DISASTER_RECOVERY_STORAGE_STORAGE_TYPES_H_

#include <cstdint>
#include <string>
#include <vector>
#include <chrono>
#include <functional>

namespace disaster_recovery {
namespace storage {

/**
 * @brief 操作状态码
 */
enum class StatusCode {
    OK = 0,                    // 成功
    INVALID_ARGUMENT = 1,      // 参数无效
    NOT_FOUND = 2,             // 未找到
    ALREADY_EXISTS = 3,        // 已存在
    PERMISSION_DENIED = 4,     // 权限不足
    RESOURCE_EXHAUSTED = 5,    // 资源耗尽
    UNAVAILABLE = 6,           // 不可用
    INTERNAL_ERROR = 7,        // 内部错误
    DATA_CORRUPTION = 8,       // 数据损坏
    TIMEOUT = 9,               // 超时
    NETWORK_ERROR = 10,        // 网络错误
    NODE_FAILURE = 11,         // 节点故障
    QUORUM_FAILED = 12,        // Quorum失败
    ENCODING_ERROR = 13,       // 编码错误
    DECODING_ERROR = 14,       // 解码错误
};

/**
 * @brief 操作结果
 */
struct Status {
    StatusCode code;
    std::string message;

    Status() : code(StatusCode::OK) {}
    Status(StatusCode c, const std::string& msg) : code(c), message(msg) {}

    bool ok() const { return code == StatusCode::OK; }
    bool isNotFound() const { return code == StatusCode::NOT_FOUND; }
    bool isUnavailable() const { return code == StatusCode::UNAVAILABLE; }

    static Status OK() { return Status(); }
    static Status NotFound(const std::string& msg = "") {
        return Status(StatusCode::NOT_FOUND, msg);
    }
    static Status Error(StatusCode code, const std::string& msg) {
        return Status(code, msg);
    }
};

/**
 * @brief 时间戳类型
 */
using Timestamp = std::chrono::time_point<std::chrono::system_clock>;

/**
 * @brief 节点ID类型
 */
using NodeId = std::string;

/**
 * @brief 对象ID类型
 */
using ObjectId = std::string;

/**
 * @brief 分片ID类型
 */
using ShardId = std::string;

/**
 * @brief 节点状态
 */
enum class NodeStatus {
    ONLINE,      // 在线
    OFFLINE,     // 离线
    SUSPECTED,   // 疑似故障
    DEGRADED,    // 降级
    RECOVERING,  // 恢复中
};

/**
 * @brief 副本状态
 */
enum class ReplicaStatus {
    HEALTHY,     // 健康
    DEGRADED,    // 降级
    LOST,        // 丢失
    RECOVERING,  // 恢复中
};

/**
 * @brief 数据对象信息
 */
struct ObjectInfo {
    ObjectId id;                 // 对象ID
    uint64_t size;               // 数据大小
    uint32_t version;            // 版本号
    std::string checksum;        // 校验和
    Timestamp create_time;       // 创建时间
    Timestamp update_time;       // 更新时间
    int data_shards;             // 数据分片数
    int parity_shards;           // 校验分片数
    int replica_count;           // 副本数
};

/**
 * @brief 分片信息
 */
struct ShardInfo {
    ShardId id;                  // 分片ID
    ObjectId object_id;          // 所属对象ID
    uint32_t index;              // 分片序号
    uint32_t total_shards;       // 总分片数
    uint64_t shard_size;         // 分片大小
    uint64_t original_size;      // 原始数据大小
    bool is_parity;              // 是否校验块
    std::string checksum;        // 分片校验和
    NodeId node_id;              // 存储节点ID
};

/**
 * @brief 存储节点信息
 */
struct NodeInfo {
    NodeId id;                   // 节点ID
    std::string address;         // 网络地址
    uint16_t port;               // 端口
    NodeStatus status;           // 节点状态
    uint64_t capacity;           // 总容量
    uint64_t used;               // 已用容量
    uint64_t available;          // 可用容量
    Timestamp last_heartbeat;    // 最后心跳时间
    int shard_count;             // 存储的分片数
};

/**
 * @brief 副本信息
 */
struct ReplicaInfo {
    ShardId shard_id;            // 分片ID
    NodeId node_id;              // 节点ID
    ReplicaStatus status;        // 副本状态
    Timestamp last_verify;       // 最后验证时间
    std::string checksum;        // 副本校验和
};

/**
 * @brief 纠删码配置
 */
struct ECConfig {
    int data_shards = 4;         // 数据分片数
    int parity_shards = 2;       // 校验分片数
    size_t shard_size = 65536;   // 分片大小 (64KB)
};

/**
 * @brief 副本配置
 */
struct ReplicaConfig {
    int replication_factor = 3;  // 副本因子
    int write_quorum = 2;        // 写入Quorum
    int read_quorum = 2;         // 读取Quorum
};

/**
 * @brief 故障检测配置
 */
struct FailureDetectionConfig {
    int heartbeat_interval_ms = 5000;    // 心跳间隔 (ms)
    int heartbeat_timeout_ms = 15000;    // 心跳超时 (ms)
    int suspect_timeout_ms = 30000;      // 怀疑超时 (ms)
    int max_retries = 3;                 // 最大重试次数
};

/**
 * @brief 存储系统配置
 */
struct StorageConfig {
    ECConfig ec;                         // 纠删码配置
    ReplicaConfig replica;               // 副本配置
    FailureDetectionConfig failure;      // 故障检测配置
    std::string data_dir = "./data";     // 数据目录
    int worker_threads = 4;              // 工作线程数
};

/**
 * @brief 分片数据
 */
struct Shard {
    ShardId id;                          // 分片ID
    std::vector<uint8_t> data;           // 分片数据
    std::string checksum;                // 校验和
    bool is_parity;                      // 是否校验块
    uint32_t index;                      // 分片序号
};

/**
 * @brief 读取请求
 */
struct ReadRequest {
    ObjectId object_id;                  // 对象ID
    uint64_t offset = 0;                 // 读取偏移
    uint64_t length = 0;                 // 读取长度（0表示全部）
};

/**
 * @brief 写入请求
 */
struct WriteRequest {
    ObjectId object_id;                  // 对象ID
    const uint8_t* data;                 // 数据指针
    uint64_t size;                       // 数据大小
    bool overwrite = false;              // 是否覆盖
};

/**
 * @brief 读取响应
 */
struct ReadResponse {
    Status status;                       // 状态
    std::vector<uint8_t> data;           // 数据
    ObjectInfo object_info;              // 对象信息
};

/**
 * @brief 写入响应
 */
struct WriteResponse {
    Status status;                       // 状态
    ObjectInfo object_info;              // 对象信息
    int shards_written = 0;              // 写入的分片数
};

/**
 * @brief 心跳请求
 */
struct HeartbeatRequest {
    NodeId node_id;                      // 节点ID
    Timestamp timestamp;                 // 时间戳
    NodeStatus status;                   // 节点状态
    uint64_t used_capacity;              // 已用容量
    int shard_count;                     // 分片数
};

/**
 * @brief 心跳响应
 */
struct HeartbeatResponse {
    Status status;                       // 状态
    Timestamp timestamp;                 // 时间戳
    bool need_recovery;                  // 是否需要恢复
    std::vector<ShardId> recovery_list;  // 需要恢复的分片列表
};

/**
 * @brief 回调函数类型
 */
using StatusCallback = std::function<void(const Status&)>;
using ReadCallback = std::function<void(const ReadResponse&)>;
using WriteCallback = std::function<void(const WriteResponse&)>;
using HeartbeatCallback = std::function<void(const HeartbeatResponse&)>;

}  // namespace storage
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_STORAGE_TYPES_H_
