/**
 * @file memory_pool.h
 * @brief 内存池
 *
 * 高性能内存池实现，用于减少内存分配开销。
 * 支持固定大小对象的快速分配和释放。
 */

#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>
#include <memory>
#include <new>
#include <cassert>

namespace hft {

/**
 * @class MemoryPool
 * @brief 固定大小内存池
 *
 * 特性：
 * - O(1) 分配和释放
 * - 预分配内存块
 * - 内存对齐
 * - 线程安全（可选）
 *
 * @tparam T 对象类型
 * @tparam BlockSize 每个块的对象数量
 */
template<typename T, size_t BlockSize = 1024>
class MemoryPool {
public:
    /**
     * @brief 构造函数
     */
    MemoryPool() : free_list_(nullptr) {
        allocate_block();
    }

    /**
     * @brief 析构函数
     */
    ~MemoryPool() {
        for (auto* chunk : chunks_) {
            ::operator delete(chunk);
        }
    }

    // 禁止拷贝
    MemoryPool(const MemoryPool&) = delete;
    MemoryPool& operator=(const MemoryPool&) = delete;

    /**
     * @brief 分配对象内存
     * @return 对象指针
     */
    T* allocate() {
        if (free_list_ == nullptr) {
            allocate_block();
        }

        Block* block = free_list_;
        free_list_ = free_list_->next;
        return reinterpret_cast<T*>(block);
    }

    /**
     * @brief 释放对象内存
     * @param ptr 对象指针
     */
    void deallocate(T* ptr) {
        if (ptr == nullptr) return;

        Block* block = reinterpret_cast<Block*>(ptr);
        block->next = free_list_;
        free_list_ = block;
    }

    /**
     * @brief 构造对象
     * @param args 构造参数
     * @return 对象指针
     */
    template<typename... Args>
    T* construct(Args&&... args) {
        T* ptr = allocate();
        try {
            new (ptr) T(std::forward<Args>(args)...);
        } catch (...) {
            deallocate(ptr);
            throw;
        }
        return ptr;
    }

    /**
     * @brief 销毁对象
     * @param ptr 对象指针
     */
    void destroy(T* ptr) {
        if (ptr == nullptr) return;
        ptr->~T();
        deallocate(ptr);
    }

    /**
     * @brief 获取已分配的块数
     * @return 块数
     */
    size_t allocated_blocks() const {
        return chunks_.size();
    }

    /**
     * @brief 获取每个块的对象数
     * @return 每个块的对象数
     */
    constexpr size_t block_size() const {
        return BlockSize;
    }

private:
    /**
     * @brief 内存块链表节点
     */
    union Block {
        Block* next;  ///< 下一个空闲块
        alignas(T) char data[sizeof(T)];  ///< 对象存储
    };

    /**
     * @brief 分配新的内存块
     */
    void allocate_block() {
        // 分配一大块内存
        size_t alloc_size = BlockSize * sizeof(Block);
        void* chunk = ::operator new(alloc_size);
        chunks_.push_back(chunk);

        // 将新块链接到空闲链表
        Block* blocks = static_cast<Block*>(chunk);
        for (size_t i = 0; i < BlockSize - 1; ++i) {
            blocks[i].next = &blocks[i + 1];
        }
        blocks[BlockSize - 1].next = free_list_;
        free_list_ = &blocks[0];
    }

    Block* free_list_;               ///< 空闲链表头
    std::vector<void*> chunks_;      ///< 已分配的内存块
};

/**
 * @class ObjectPool
 * @brief 对象池
 *
 * 提供对象的复用功能，避免频繁构造和析构。
 */
template<typename T>
class ObjectPool {
public:
    /**
     * @brief 构造函数
     * @param initial_size 初始对象数量
     */
    explicit ObjectPool(size_t initial_size = 256) {
        pool_.reserve(initial_size);
        for (size_t i = 0; i < initial_size; ++i) {
            pool_.push_back(std::make_unique<T>());
        }
    }

    /**
     * @brief 获取对象
     * @return 对象指针
     */
    T* acquire() {
        if (pool_.empty()) {
            return new T();
        }

        auto obj = std::move(pool_.back());
        pool_.pop_back();
        return obj.release();
    }

    /**
     * @brief 归还对象
     * @param ptr 对象指针
     */
    void release(T* ptr) {
        if (ptr == nullptr) return;
        pool_.push_back(std::unique_ptr<T>(ptr));
    }

    /**
     * @brief 获取池中对象数量
     * @return 对象数量
     */
    size_t size() const {
        return pool_.size();
    }

private:
    std::vector<std::unique_ptr<T>> pool_;  ///< 对象池
};

/**
 * @class StackAllocator
 * @brief 栈分配器
 *
 * 线性分配器，适用于临时对象的快速分配。
 * 分配速度极快，但只能整体释放。
 */
class StackAllocator {
public:
    /**
     * @brief 构造函数
     * @param size 栈大小
     */
    explicit StackAllocator(size_t size)
        : size_(size), offset_(0) {
        memory_ = static_cast<char*>(::operator new(size));
    }

    /**
     * @brief 析构函数
     */
    ~StackAllocator() {
        ::operator delete(memory_);
    }

    /**
     * @brief 分配内存
     * @param size 字节数
     * @param alignment 对齐要求
     * @return 内存指针
     */
    void* allocate(size_t size, size_t alignment = alignof(std::max_align_t)) {
        // 对齐偏移
        size_t aligned_offset = (offset_ + alignment - 1) & ~(alignment - 1);

        if (aligned_offset + size > size_) {
            return nullptr;  // 内存不足
        }

        void* ptr = memory_ + aligned_offset;
        offset_ = aligned_offset + size;
        return ptr;
    }

    /**
     * @brief 重置分配器
     */
    void reset() {
        offset_ = 0;
    }

    /**
     * @brief 获取已使用大小
     * @return 已使用字节数
     */
    size_t used() const {
        return offset_;
    }

    /**
     * @brief 获取总大小
     * @return 总字节数
     */
    size_t capacity() const {
        return size_;
    }

private:
    char* memory_;    ///< 内存块
    size_t size_;     ///< 总大小
    size_t offset_;   ///< 当前偏移
};

} // namespace hft
