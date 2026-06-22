#ifndef DISASTER_RECOVERY_STORAGE_STORAGE_DATA_SHARDER_H_
#define DISASTER_RECOVERY_STORAGE_STORAGE_DATA_SHARDER_H_

#include <cstdint>
#include <vector>
#include <string>
#include "storage/types.h"

namespace disaster_recovery {
namespace storage {

/**
 * @brief 数据分片器
 *
 * 将大数据分割成固定大小的分片，便于分布式存储和纠删码编码
 *
 * @note 分片是分布式存储的基本单位
 */
class DataSharder {
public:
    /**
     * @brief 构造函数
     *
     * @param shard_size 分片大小（字节）
     */
    explicit DataSharder(size_t shard_size = 65536);

    /**
     * @brief 析构函数
     */
    ~DataSharder() = default;

    /**
     * @brief 分片数据
     *
     * 将原始数据分割成多个分片
     *
     * @param data 原始数据
     * @param size 数据大小
     * @param shards 输出的分片列表
     * @return 操作状态
     */
    Status shard(const uint8_t* data, size_t size,
                 std::vector<Shard>& shards);

    /**
     * @brief 重组数据
     *
     * 将分片重组为原始数据
     *
     * @param shards 分片列表
     * @param data 输出的原始数据
     * @param original_size 原始数据大小
     * @return 操作状态
     */
    Status reassemble(const std::vector<Shard>& shards,
                      std::vector<uint8_t>& data,
                      size_t original_size);

    /**
     * @brief 计算分片数量
     *
     * @param data_size 数据大小
     * @return 分片数量
     */
    size_t calculateShardCount(size_t data_size) const;

    /**
     * @brief 计算分片大小
     *
     * @param shard_index 分片序号
     * @param data_size 数据大小
     * @return 分片大小
     */
    size_t calculateShardSize(size_t shard_index, size_t data_size) const;

    /**
     * @brief 获取分片大小配置
     *
     * @return 分片大小
     */
    size_t getShardSize() const { return shard_size_; }

    /**
     * @brief 设置分片大小
     *
     * @param shard_size 分片大小
     */
    void setShardSize(size_t shard_size) { shard_size_ = shard_size; }

private:
    size_t shard_size_;  // 分片大小

    /**
     * @brief 生成分片ID
     *
     * @param object_id 对象ID
     * @param shard_index 分片序号
     * @return 分片ID
     */
    std::string generateShardId(const std::string& object_id,
                                size_t shard_index) const;

    /**
     * @brief 计算校验和
     *
     * @param data 数据指针
     * @param size 数据大小
     * @return 校验和字符串
     */
    std::string calculateChecksum(const uint8_t* data, size_t size) const;
};

}  // namespace storage
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_STORAGE_DATA_SHARDER_H_
