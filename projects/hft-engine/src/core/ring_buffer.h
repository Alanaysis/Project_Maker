/**
 * @file ring_buffer.h
 * @brief 无锁环形缓冲区
 *
 * 单生产者单消费者 (SPSC) 无锁环形缓冲区实现。
 * 用于高频交易系统中的线程间数据传递。
 */

#pragma once

#include <atomic>
#include <cstddef>
#include <new>
#include <optional>

namespace hft {

/**
 * @class RingBuffer
 * @brief 无锁环形缓冲区
 *
 * 特性：
 * - 单生产者单消费者 (SPSC) 模型
 * - 无锁设计，高并发性能
 * - 缓存行对齐，避免伪共享
 * - 固定大小，内存可预测
 *
 * @tparam T 元素类型
 * @tparam Size 缓冲区大小（必须是 2 的幂）
 */
template<typename T, size_t Size>
class RingBuffer {
    static_assert((Size & (Size - 1)) == 0, "Size must be a power of 2");
    static_assert(Size > 0, "Size must be greater than 0");

public:
    /**
     * @brief 默认构造函数
     */
    RingBuffer() : read_pos_(0), write_pos_(0) {}

    /**
     * @brief 析构函数
     */
    ~RingBuffer() = default;

    // 禁止拷贝和移动
    RingBuffer(const RingBuffer&) = delete;
    RingBuffer& operator=(const RingBuffer&) = delete;
    RingBuffer(RingBuffer&&) = delete;
    RingBuffer& operator=(RingBuffer&&) = delete;

    /**
     * @brief 尝试写入元素
     * @param value 要写入的值
     * @return 成功返回 true，缓冲区满返回 false
     */
    bool try_push(const T& value) {
        const size_t write = write_pos_.load(std::memory_order_relaxed);
        const size_t next = (write + 1) & mask_;

        // 检查缓冲区是否已满
        if (next == read_pos_.load(std::memory_order_acquire)) {
            return false;
        }

        // 写入数据
        buffer_[write] = value;

        // 更新写位置
        write_pos_.store(next, std::memory_order_release);
        return true;
    }

    /**
     * @brief 尝试写入元素（移动语义）
     * @param value 要写入的值
     * @return 成功返回 true，缓冲区满返回 false
     */
    bool try_push(T&& value) {
        const size_t write = write_pos_.load(std::memory_order_relaxed);
        const size_t next = (write + 1) & mask_;

        if (next == read_pos_.load(std::memory_order_acquire)) {
            return false;
        }

        buffer_[write] = std::move(value);
        write_pos_.store(next, std::memory_order_release);
        return true;
    }

    /**
     * @brief 尝试读取元素
     * @return 读取的元素，缓冲区空返回 std::nullopt
     */
    std::optional<T> try_pop() {
        const size_t read = read_pos_.load(std::memory_order_relaxed);

        // 检查缓冲区是否为空
        if (read == write_pos_.load(std::memory_order_acquire)) {
            return std::nullopt;
        }

        // 读取数据
        T value = std::move(buffer_[read]);

        // 更新读位置
        read_pos_.store((read + 1) & mask_, std::memory_order_release);
        return value;
    }

    /**
     * @brief 检查缓冲区是否为空
     * @return 为空返回 true
     */
    bool empty() const {
        return read_pos_.load(std::memory_order_acquire) ==
               write_pos_.load(std::memory_order_acquire);
    }

    /**
     * @brief 检查缓冲区是否已满
     * @return 已满返回 true
     */
    bool full() const {
        const size_t write = write_pos_.load(std::memory_order_acquire);
        const size_t next = (write + 1) & mask_;
        return next == read_pos_.load(std::memory_order_acquire);
    }

    /**
     * @brief 获取当前元素数量
     * @return 元素数量
     */
    size_t size() const {
        const size_t write = write_pos_.load(std::memory_order_acquire);
        const size_t read = read_pos_.load(std::memory_order_acquire);
        return (write - read) & mask_;
    }

    /**
     * @brief 获取缓冲区容量
     * @return 缓冲区容量
     */
    constexpr size_t capacity() const {
        return Size;
    }

    /**
     * @brief 清空缓冲区
     */
    void clear() {
        read_pos_.store(0, std::memory_order_relaxed);
        write_pos_.store(0, std::memory_order_relaxed);
    }

private:
    static constexpr size_t mask_ = Size - 1;  ///< 掩码，用于快速取模

    // 缓存行对齐，避免伪共享
    alignas(64) std::atomic<size_t> read_pos_;   ///< 读位置
    alignas(64) std::atomic<size_t> write_pos_;  ///< 写位置

    T buffer_[Size];  ///< 数据缓冲区
};

/**
 * @class MultiProducerRingBuffer
 * @brief 多生产者环形缓冲区
 *
 * 支持多个生产者同时写入的环形缓冲区。
 * 使用 CAS 操作实现线程安全。
 */
template<typename T, size_t Size>
class MultiProducerRingBuffer {
    static_assert((Size & (Size - 1)) == 0, "Size must be a power of 2");

public:
    MultiProducerRingBuffer() : read_pos_(0), write_pos_(0) {}

    ~MultiProducerRingBuffer() = default;

    /**
     * @brief 尝试写入元素（线程安全）
     * @param value 要写入的值
     * @return 成功返回 true
     */
    bool try_push(const T& value) {
        size_t current_write = write_pos_.load(std::memory_order_relaxed);

        while (true) {
            const size_t next = (current_write + 1) & mask_;

            // 检查是否已满
            if (next == read_pos_.load(std::memory_order_acquire)) {
                return false;
            }

            // 尝试 CAS 更新写位置
            if (write_pos_.compare_exchange_weak(
                    current_write, next,
                    std::memory_order_acq_rel,
                    std::memory_order_relaxed)) {
                // 成功获取位置，写入数据
                buffer_[current_write] = value;
                return true;
            }
            // CAS 失败，重试
        }
    }

    /**
     * @brief 尝试读取元素（线程安全）
     * @return 读取的元素
     */
    std::optional<T> try_pop() {
        size_t current_read = read_pos_.load(std::memory_order_relaxed);

        while (true) {
            // 检查是否为空
            if (current_read == write_pos_.load(std::memory_order_acquire)) {
                return std::nullopt;
            }

            // 尝试 CAS 更新读位置
            const size_t next = (current_read + 1) & mask_;
            if (read_pos_.compare_exchange_weak(
                    current_read, next,
                    std::memory_order_acq_rel,
                    std::memory_order_relaxed)) {
                // 成功获取位置，读取数据
                return buffer_[current_read];
            }
            // CAS 失败，重试
        }
    }

    bool empty() const {
        return read_pos_.load(std::memory_order_acquire) ==
               write_pos_.load(std::memory_order_acquire);
    }

    size_t size() const {
        const size_t write = write_pos_.load(std::memory_order_acquire);
        const size_t read = read_pos_.load(std::memory_order_acquire);
        return (write - read) & mask_;
    }

private:
    static constexpr size_t mask_ = Size - 1;

    alignas(64) std::atomic<size_t> read_pos_;
    alignas(64) std::atomic<size_t> write_pos_;
    T buffer_[Size];
};

} // namespace hft
