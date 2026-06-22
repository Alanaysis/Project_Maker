#include "storage/data_sharder.h"
#include <cstring>
#include <sstream>
#include <iomanip>

namespace disaster_recovery {
namespace storage {

DataSharder::DataSharder(size_t shard_size)
    : shard_size_(shard_size) {
    if (shard_size == 0) {
        shard_size_ = 65536;  // 默认64KB
    }
}

Status DataSharder::shard(const uint8_t* data, size_t size,
                          std::vector<Shard>& shards) {
    if (data == nullptr || size == 0) {
        return Status(StatusCode::INVALID_ARGUMENT, "Invalid data");
    }

    // 计算分片数量
    size_t shard_count = calculateShardCount(size);

    // 清空输出
    shards.clear();
    shards.reserve(shard_count);

    // 分片数据
    size_t offset = 0;
    for (size_t i = 0; i < shard_count; i++) {
        // 计算当前分片大小
        size_t current_shard_size = calculateShardSize(i, size);

        // 创建分片
        Shard shard;
        shard.index = i;
        shard.is_parity = false;
        shard.data.resize(current_shard_size, 0);

        // 复制数据
        if (offset < size) {
            size_t copy_size = std::min(current_shard_size, size - offset);
            std::memcpy(shard.data.data(), data + offset, copy_size);
            offset += copy_size;
        }

        // 计算校验和
        shard.checksum = calculateChecksum(shard.data.data(),
                                           current_shard_size);

        // 生成分片ID
        shard.id = generateShardId("", i);

        shards.push_back(std::move(shard));
    }

    return Status::OK();
}

Status DataSharder::reassemble(const std::vector<Shard>& shards,
                               std::vector<uint8_t>& data,
                               size_t original_size) {
    if (shards.empty()) {
        return Status(StatusCode::INVALID_ARGUMENT, "No shards provided");
    }
    if (original_size == 0) {
        return Status(StatusCode::INVALID_ARGUMENT, "Invalid original size");
    }

    // 分配输出缓冲区
    data.resize(original_size, 0);

    // 按序号排序分片
    std::vector<const Shard*> sorted_shards;
    sorted_shards.reserve(shards.size());
    for (const auto& shard : shards) {
        sorted_shards.push_back(&shard);
    }
    std::sort(sorted_shards.begin(), sorted_shards.end(),
              [](const Shard* a, const Shard* b) {
                  return a->index < b->index;
              });

    // 重组数据
    size_t offset = 0;
    for (const auto* shard : sorted_shards) {
        if (offset >= original_size) {
            break;
        }

        size_t copy_size = std::min(shard->data.size(),
                                    original_size - offset);
        std::memcpy(data.data() + offset, shard->data.data(), copy_size);
        offset += copy_size;
    }

    return Status::OK();
}

size_t DataSharder::calculateShardCount(size_t data_size) const {
    if (data_size == 0) {
        return 0;
    }
    return (data_size + shard_size_ - 1) / shard_size_;
}

size_t DataSharder::calculateShardSize(size_t shard_index,
                                       size_t data_size) const {
    if (shard_index >= calculateShardCount(data_size)) {
        return 0;
    }

    size_t start = shard_index * shard_size_;
    size_t end = std::min(start + shard_size_, data_size);

    return end - start;
}

std::string DataSharder::generateShardId(const std::string& object_id,
                                         size_t shard_index) const {
    std::stringstream ss;
    ss << object_id << "_shard_" << std::setw(6) << std::setfill('0')
       << shard_index;
    return ss.str();
}

std::string DataSharder::calculateChecksum(const uint8_t* data,
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

}  // namespace storage
}  // namespace disaster_recovery
