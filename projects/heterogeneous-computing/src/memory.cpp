/**
 * @file memory.cpp
 * @brief 内存管理实现
 */

#include "heterogeneous/memory.h"
#include "heterogeneous/device.h"
#include <cstring>
#include <algorithm>

namespace heterogeneous {

// MemoryPool 实现

MemoryPool::MemoryPool(MemoryLocation location, std::shared_ptr<Device> device,
                       size_t initial_size)
    : location_(location)
    , device_(device) {
    if (initial_size > 0) {
        expand(initial_size);
    }
}

MemoryPool::~MemoryPool() {
    if (pool_ptr_ && location_ == MemoryLocation::Host) {
        std::free(pool_ptr_);
    } else if (pool_ptr_ && device_) {
        device_->deallocate(pool_ptr_);
    }
}

void* MemoryPool::allocate(size_t size) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 查找合适的空闲块
    for (auto it = free_blocks_.begin(); it != free_blocks_.end(); ++it) {
        if (it->size >= size) {
            void* ptr = it->ptr;
            size_t remaining = it->size - size;

            if (remaining > 0) {
                // 分割块
                *it = {static_cast<char*>(ptr) + size, remaining};
            } else {
                free_blocks_.erase(it);
            }

            allocated_size_ += size;
            allocated_blocks_[ptr] = size;
            return ptr;
        }
    }

    // 没有合适的空闲块，扩展内存池
    expand(size);
    return allocate(size);
}

void MemoryPool::deallocate(void* ptr) {
    if (!ptr) return;

    std::lock_guard<std::mutex> lock(mutex_);

    // 查找实际块大小
    auto block_it = allocated_blocks_.find(ptr);
    if (block_it == allocated_blocks_.end()) {
        return;  // 未知指针，忽略
    }

    size_t block_size = block_it->second;
    allocated_blocks_.erase(block_it);
    allocated_size_ -= block_size;

    char* block_start = static_cast<char*>(ptr);
    char* block_end = block_start + block_size;

    // 尝试与相邻空闲块合并
    for (auto it = free_blocks_.begin(); it != free_blocks_.end(); ++it) {
        char* free_start = static_cast<char*>(it->ptr);
        char* free_end = free_start + it->size;

        if (block_end == free_start) {
            // 当前块在空闲块之前，合并: 扩展当前块并替换空闲块
            it->ptr = ptr;
            it->size += block_size;

            // 检查是否还能与前一个空闲块合并
            for (auto it2 = free_blocks_.begin(); it2 != free_blocks_.end(); ++it2) {
                if (it2 == it) continue;
                char* free2_end = static_cast<char*>(it2->ptr) + it2->size;
                if (free2_end == block_start) {
                    it2->size += it->size;
                    free_blocks_.erase(it);
                    return;
                }
            }
            return;
        }

        if (free_end == block_start) {
            // 当前块在空闲块之后，合并: 扩展空闲块
            it->size += block_size;

            // 检查是否还能与后一个空闲块合并
            char* new_end = block_end;
            for (auto it2 = free_blocks_.begin(); it2 != free_blocks_.end(); ++it2) {
                if (it2 == it) continue;
                if (static_cast<char*>(it2->ptr) == new_end) {
                    it->size += it2->size;
                    free_blocks_.erase(it2);
                    return;
                }
            }
            return;
        }
    }

    // 没有相邻块，添加新的空闲块
    free_blocks_.push_back({ptr, block_size});
}

double MemoryPool::get_utilization() const {
    std::lock_guard<std::mutex> lock(mutex_);
    if (total_size_ == 0) return 0.0;
    return static_cast<double>(allocated_size_) / total_size_;
}

void MemoryPool::expand(size_t size) {
    // 对齐到 4KB
    size_t aligned_size = (size + 4095) & ~4095;

    void* new_ptr = nullptr;
    if (location_ == MemoryLocation::Host) {
        new_ptr = std::malloc(aligned_size);
    } else if (device_) {
        new_ptr = device_->allocate(aligned_size);
    }

    if (!new_ptr) {
        throw MemoryException("Failed to allocate memory", ErrorCode::MemoryAllocationFailed);
    }

    // 添加到空闲块列表
    free_blocks_.push_back({new_ptr, aligned_size});
    total_size_ += aligned_size;
}

// MemoryManager 实现

MemoryManager& MemoryManager::instance() {
    static MemoryManager instance;
    return instance;
}

bool MemoryManager::initialize() {
    std::lock_guard<std::mutex> lock(mutex_);

    if (initialized_) {
        return true;
    }

    initialized_ = true;
    return true;
}

void MemoryManager::shutdown() {
    std::lock_guard<std::mutex> lock(mutex_);

    // 释放所有内存块
    for (auto& pair : blocks_) {
        if (pair.second->is_allocated) {
            if (pair.second->location == MemoryLocation::Host) {
                std::free(pair.first);
            } else if (pair.second->location == MemoryLocation::Device) {
                auto device = DeviceManager::instance().get_device(pair.second->device_id);
                if (device) {
                    device->deallocate(pair.first);
                }
            }
        }
    }
    blocks_.clear();
    pools_.clear();

    initialized_ = false;
}

void* MemoryManager::allocate(size_t size, MemoryLocation location,
                               const std::string& device_id) {
    if (size == 0) {
        return nullptr;
    }

    std::lock_guard<std::mutex> lock(mutex_);

    void* ptr = nullptr;

    if (location == MemoryLocation::Host) {
        ptr = std::malloc(size);
    } else if (location == MemoryLocation::Device) {
        auto device = DeviceManager::instance().get_device(device_id);
        if (!device) {
            throw MemoryException("Device not found: " + device_id,
                                 ErrorCode::DeviceNotFound);
        }
        ptr = device->allocate(size);
    } else if (location == MemoryLocation::Unified) {
        // 统一内存需要 CUDA 支持
        // cudaMallocManaged(&ptr, size);
        ptr = std::malloc(size);  // 降级到主机内存
    }

    if (!ptr) {
        throw MemoryException("Failed to allocate " + std::to_string(size) + " bytes",
                             ErrorCode::MemoryAllocationFailed);
    }

    // 记录内存块
    auto block = std::make_unique<MemoryBlock>();
    block->ptr = ptr;
    block->size = size;
    block->location = location;
    block->device_id = device_id;
    block->is_allocated = true;
    block->ref_count = 1;
    block->last_access = std::chrono::steady_clock::now();

    blocks_[ptr] = std::move(block);

    // 更新统计
    total_allocated_ += size;
    size_t current = total_allocated_.load();
    size_t peak = peak_allocated_.load();
    while (current > peak && !peak_allocated_.compare_exchange_weak(peak, current)) {
        // 自旋等待
    }

    return ptr;
}

void MemoryManager::deallocate(void* ptr) {
    if (!ptr) return;

    std::lock_guard<std::mutex> lock(mutex_);

    auto it = blocks_.find(ptr);
    if (it == blocks_.end()) {
        return;
    }

    auto& block = it->second;
    if (block->is_allocated) {
        // 释放内存
        if (block->location == MemoryLocation::Host ||
            block->location == MemoryLocation::Unified) {
            std::free(ptr);
        } else if (block->location == MemoryLocation::Device) {
            auto device = DeviceManager::instance().get_device(block->device_id);
            if (device) {
                device->deallocate(ptr);
            }
        }

        // 更新统计
        total_allocated_ -= block->size;
        block->is_allocated = false;

        // 移除记录
        blocks_.erase(it);
    }
}

void MemoryManager::transfer(const void* src, void* dst, size_t size,
                              MemoryLocation src_location, MemoryLocation dst_location,
                              const std::string& src_device_id,
                              const std::string& dst_device_id) {
    if (!src || !dst || size == 0) {
        return;
    }

    // 获取源和目标的锁
    std::lock_guard<std::mutex> lock(mutex_);

    if (src_location == MemoryLocation::Host && dst_location == MemoryLocation::Host) {
        // 主机到主机
        std::memcpy(dst, src, size);
    } else if (src_location == MemoryLocation::Host &&
               dst_location == MemoryLocation::Device) {
        // 主机到设备
        auto device = DeviceManager::instance().get_device(dst_device_id);
        if (device) {
            device->copy_to_device(dst, src, size);
        }
    } else if (src_location == MemoryLocation::Device &&
               dst_location == MemoryLocation::Host) {
        // 设备到主机
        auto device = DeviceManager::instance().get_device(src_device_id);
        if (device) {
            device->copy_from_device(dst, src, size);
        }
    } else if (src_location == MemoryLocation::Device &&
               dst_location == MemoryLocation::Device) {
        // 设备到设备 (需要通过主机中转)
        auto src_device = DeviceManager::instance().get_device(src_device_id);
        auto dst_device = DeviceManager::instance().get_device(dst_device_id);

        if (src_device && dst_device) {
            // 先复制到主机
            void* temp = std::malloc(size);
            src_device->copy_from_device(temp, src, size);

            // 再复制到目标设备
            dst_device->copy_to_device(dst, temp, size);

            std::free(temp);
        }
    }

    // 更新访问时间
    auto src_it = blocks_.find(const_cast<void*>(src));
    if (src_it != blocks_.end()) {
        src_it->second->last_access = std::chrono::steady_clock::now();
    }
    auto dst_it = blocks_.find(dst);
    if (dst_it != blocks_.end()) {
        dst_it->second->last_access = std::chrono::steady_clock::now();
    }
}

std::future<void> MemoryManager::transfer_async(const void* src, void* dst, size_t size,
                                                 MemoryLocation src_location,
                                                 MemoryLocation dst_location,
                                                 const std::string& src_device_id,
                                                 const std::string& dst_device_id) {
    return std::async(std::launch::async, [this, src, dst, size,
                                           src_location, dst_location,
                                           src_device_id, dst_device_id]() {
        transfer(src, dst, size, src_location, dst_location, src_device_id, dst_device_id);
    });
}

MemoryBlock* MemoryManager::get_block(const void* ptr) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = blocks_.find(const_cast<void*>(ptr));
    if (it == blocks_.end()) {
        return nullptr;
    }
    return it->second.get();
}

std::map<std::string, size_t> MemoryManager::get_usage_stats() const {
    std::lock_guard<std::mutex> lock(mutex_);

    std::map<std::string, size_t> stats;
    stats["total_allocated"] = total_allocated_.load();
    stats["peak_allocated"] = peak_allocated_.load();
    stats["block_count"] = blocks_.size();

    size_t host_memory = 0;
    size_t device_memory = 0;

    for (const auto& pair : blocks_) {
        if (pair.second->is_allocated) {
            if (pair.second->location == MemoryLocation::Host) {
                host_memory += pair.second->size;
            } else {
                device_memory += pair.second->size;
            }
        }
    }

    stats["host_memory"] = host_memory;
    stats["device_memory"] = device_memory;

    return stats;
}

size_t MemoryManager::check_leaks() const {
    std::lock_guard<std::mutex> lock(mutex_);

    size_t leak_count = 0;
    for (const auto& pair : blocks_) {
        if (pair.second->is_allocated && pair.second->ref_count > 0) {
            leak_count++;
        }
    }

    return leak_count;
}

MemoryPool* MemoryManager::get_or_create_pool(MemoryLocation location,
                                               const std::string& device_id) {
    std::string key;
    if (location == MemoryLocation::Host) {
        key = "host";
    } else {
        key = "device_" + device_id;
    }

    auto it = pools_.find(key);
    if (it != pools_.end()) {
        return it->second.get();
    }

    std::shared_ptr<Device> device;
    if (location == MemoryLocation::Device) {
        device = DeviceManager::instance().get_device(device_id);
    }

    auto pool = std::make_unique<MemoryPool>(location, device);
    auto pool_ptr = pool.get();
    pools_[key] = std::move(pool);

    return pool_ptr;
}

} // namespace heterogeneous
