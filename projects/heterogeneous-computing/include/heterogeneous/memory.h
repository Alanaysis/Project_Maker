#pragma once

/**
 * @file memory.h
 * @brief 内存管理
 *
 * 本文件定义了内存管理相关的类和接口。
 *
 * ⭐ 重点: 理解主机内存和设备内存的区别
 * 💡 思考: 如何优化数据传输以减少性能开销？
 */

#include "core.h"
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <functional>

namespace heterogeneous {

// 前向声明
class Device;

/**
 * @brief 内存块结构体
 *
 * ⭐ 重点: 理解内存块的设计
 *
 * 内存块是内存管理的基本单位，包含:
 * - 内存指针
 * - 内存大小
 * - 内存位置
 * - 引用计数
 */
struct MemoryBlock {
    void* ptr;                           // 内存指针
    size_t size;                         // 内存大小 (字节)
    MemoryLocation location;             // 内存位置
    std::string device_id;               // 设备 ID (仅设备内存)
    bool is_allocated;                   // 是否已分配

    // 引用计数
    std::atomic<int> ref_count{0};

    // 生命周期管理
    std::chrono::steady_clock::time_point last_access;

    MemoryBlock()
        : ptr(nullptr)
        , size(0)
        , location(MemoryLocation::Host)
        , is_allocated(false)
        , last_access(std::chrono::steady_clock::now()) {}

    ~MemoryBlock() = default;

    // 禁止拷贝
    MemoryBlock(const MemoryBlock&) = delete;
    MemoryBlock& operator=(const MemoryBlock&) = delete;

    // 允许移动
    MemoryBlock(MemoryBlock&& other) noexcept
        : ptr(other.ptr)
        , size(other.size)
        , location(other.location)
        , device_id(std::move(other.device_id))
        , is_allocated(other.is_allocated)
        , ref_count(other.ref_count.load())
        , last_access(other.last_access) {
        other.ptr = nullptr;
        other.size = 0;
        other.is_allocated = false;
    }
};

/**
 * @brief 内存池
 *
 * ⭐ 重点: 理解内存池的作用和实现
 *
 * 内存池通过预分配和复用内存来减少分配开销。
 *
 * 💡 思考: 内存池如何减少内存碎片？
 */
class MemoryPool {
public:
    /**
     * @brief 构造函数
     * @param location 内存位置
     * @param device 设备指针 (仅设备内存)
     * @param initial_size 初始大小
     */
    MemoryPool(MemoryLocation location, std::shared_ptr<Device> device = nullptr,
               size_t initial_size = 1024 * 1024);  // 1MB 默认

    /**
     * @brief 析构函数
     */
    ~MemoryPool();

    /**
     * @brief 分配内存
     * @param size 内存大小
     * @return 内存指针
     */
    void* allocate(size_t size);

    /**
     * @brief 释放内存
     * @param ptr 内存指针
     */
    void deallocate(void* ptr);

    /**
     * @brief 获取已分配内存大小
     */
    size_t get_allocated_size() const { return allocated_size_; }

    /**
     * @brief 获取总内存大小
     */
    size_t get_total_size() const { return total_size_; }

    /**
     * @brief 获取内存使用率
     */
    double get_utilization() const;

private:
    /**
     * @brief 扩展内存池
     * @param size 需要的大小
     */
    void expand(size_t size);

    MemoryLocation location_;
    std::shared_ptr<Device> device_;

    void* pool_ptr_ = nullptr;
    size_t total_size_ = 0;
    size_t allocated_size_ = 0;

    // 空闲块列表
    struct FreeBlock {
        void* ptr;
        size_t size;
    };
    std::vector<FreeBlock> free_blocks_;

    // 已分配块记录 (ptr -> size)，用于 deallocate 时查找实际块大小
    std::unordered_map<void*, size_t> allocated_blocks_;

    mutable std::mutex mutex_;
};

/**
 * @brief 内存管理器
 *
 * ⭐ 重点: 理解内存管理的核心功能
 *
 * 内存管理器负责:
 * - 内存分配和释放
 * - 数据传输
 * - 内存池管理
 * - 内存统计
 *
 * 💡 思考: 如何实现高效的数据传输？
 */
class MemoryManager {
public:
    /**
     * @brief 获取单例实例
     */
    static MemoryManager& instance();

    /**
     * @brief 初始化内存管理器
     * @return true 如果初始化成功
     */
    bool initialize();

    /**
     * @brief 关闭内存管理器
     */
    void shutdown();

    /**
     * @brief 分配内存
     * @param size 内存大小
     * @param location 内存位置
     * @param device_id 设备 ID (仅设备内存)
     * @return 内存指针
     */
    void* allocate(size_t size, MemoryLocation location,
                   const std::string& device_id = "");

    /**
     * @brief 释放内存
     * @param ptr 内存指针
     */
    void deallocate(void* ptr);

    /**
     * @brief 数据传输
     * @param src 源地址
     * @param dst 目标地址
     * @param size 数据大小
     * @param src_location 源内存位置
     * @param dst_location 目标内存位置
     * @param src_device_id 源设备 ID
     * @param dst_device_id 目标设备 ID
     */
    void transfer(const void* src, void* dst, size_t size,
                  MemoryLocation src_location, MemoryLocation dst_location,
                  const std::string& src_device_id = "",
                  const std::string& dst_device_id = "");

    /**
     * @brief 异步数据传输
     * @param src 源地址
     * @param dst 目标地址
     * @param size 数据大小
     * @param src_location 源内存位置
     * @param dst_location 目标内存位置
     * @param src_device_id 源设备 ID
     * @param dst_device_id 目标设备 ID
     * @return future 对象
     */
    std::future<void> transfer_async(const void* src, void* dst, size_t size,
                                      MemoryLocation src_location,
                                      MemoryLocation dst_location,
                                      const std::string& src_device_id = "",
                                      const std::string& dst_device_id = "");

    /**
     * @brief 获取内存块信息
     * @param ptr 内存指针
     * @return 内存块指针
     */
    MemoryBlock* get_block(const void* ptr);

    /**
     * @brief 获取总分配内存大小
     */
    size_t get_total_allocated() const { return total_allocated_; }

    /**
     * @brief 获取峰值内存大小
     */
    size_t get_peak_allocated() const { return peak_allocated_; }

    /**
     * @brief 获取内存使用统计
     */
    std::map<std::string, size_t> get_usage_stats() const;

    /**
     * @brief 检查内存泄漏
     * @return 泄漏的内存块数量
     */
    size_t check_leaks() const;

private:
    MemoryManager() = default;
    ~MemoryManager() = default;

    // 禁止拷贝和移动
    MemoryManager(const MemoryManager&) = delete;
    MemoryManager& operator=(const MemoryManager&) = delete;

    /**
     * @brief 获取或创建内存池
     * @param location 内存位置
     * @param device_id 设备 ID
     * @return 内存池指针
     */
    MemoryPool* get_or_create_pool(MemoryLocation location,
                                    const std::string& device_id = "");

    // 内存块映射
    std::unordered_map<void*, std::unique_ptr<MemoryBlock>> blocks_;

    // 内存池
    std::unordered_map<std::string, std::unique_ptr<MemoryPool>> pools_;

    // 统计信息
    std::atomic<size_t> total_allocated_{0};
    std::atomic<size_t> peak_allocated_{0};

    mutable std::mutex mutex_;
    bool initialized_ = false;
};

/**
 * @brief 自动内存管理
 *
 * ⭐ 重点: 理解 RAII 模式在内存管理中的应用
 *
 * 💡 思考: 如何实现自动内存管理？
 */
template<typename T>
class ManagedMemory {
public:
    /**
     * @brief 构造函数
     * @param size 元素数量
     * @param location 内存位置
     * @param device_id 设备 ID
     */
    ManagedMemory(size_t count, MemoryLocation location,
                  const std::string& device_id = "")
        : location_(location)
        , device_id_(device_id)
        , count_(count) {
        ptr_ = static_cast<T*>(
            MemoryManager::instance().allocate(
                count * sizeof(T), location, device_id
            )
        );
    }

    /**
     * @brief 析构函数
     */
    ~ManagedMemory() {
        if (ptr_) {
            MemoryManager::instance().deallocate(ptr_);
        }
    }

    // 禁止拷贝
    ManagedMemory(const ManagedMemory&) = delete;
    ManagedMemory& operator=(const ManagedMemory&) = delete;

    // 允许移动
    ManagedMemory(ManagedMemory&& other) noexcept
        : ptr_(other.ptr_)
        , location_(other.location_)
        , device_id_(std::move(other.device_id_))
        , count_(other.count_) {
        other.ptr_ = nullptr;
        other.count_ = 0;
    }

    /**
     * @brief 获取指针
     */
    T* get() { return ptr_; }
    const T* get() const { return ptr_; }

    /**
     * @brief 获取元素数量
     */
    size_t count() const { return count_; }

    /**
     * @brief 获取内存大小
     */
    size_t size() const { return count_ * sizeof(T); }

    /**
     * @brief 获取内存位置
     */
    MemoryLocation location() const { return location_; }

    /**
     * @brief 获取设备 ID
     */
    const std::string& device_id() const { return device_id_; }

    /**
     * @brief 传输数据到主机
     * @param host_ptr 主机内存指针
     */
    void copy_to_host(T* host_ptr) {
        MemoryManager::instance().transfer(
            ptr_, host_ptr, size(),
            location_, MemoryLocation::Host,
            device_id_, ""
        );
    }

    /**
     * @brief 从主机传输数据
     * @param host_ptr 主机内存指针
     */
    void copy_from_host(const T* host_ptr) {
        MemoryManager::instance().transfer(
            host_ptr, ptr_, size(),
            MemoryLocation::Host, location_,
            "", device_id_
        );
    }

    /**
     * @brief 运算符重载
     */
    T& operator[](size_t index) { return ptr_[index]; }
    const T& operator[](size_t index) const { return ptr_[index]; }

    /**
     * @brief 隐式转换
     */
    operator T*() { return ptr_; }
    operator const T*() const { return ptr_; }

private:
    T* ptr_ = nullptr;
    MemoryLocation location_;
    std::string device_id_;
    size_t count_;
};

} // namespace heterogeneous
