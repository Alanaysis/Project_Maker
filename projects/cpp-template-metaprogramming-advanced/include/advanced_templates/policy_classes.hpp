#pragma once
/**
 * @file policy_classes.hpp
 * @brief 策略类 (Policy Classes)
 *
 * 策略类是一种通过模板参数配置类行为的技术。
 * 每个策略类定义一组行为，通过组合不同的策略类来
 * 定制最终类的行为。
 *
 * 核心思想：
 *   - 将可变行为抽取为策略类
 *   - 通过模板参数组合策略
 *   - 编译期确定行为
 *   - 零运行时开销
 *
 * 应用场景：
 *   - 智能指针（所有权策略）
 *   - 容器（内存分配策略）
 *   - 线程模型（同步策略）
 */

#include <iostream>
#include <string>
#include <memory>
#include <mutex>
#include <vector>
#include <cstddef>

namespace tmp {

// ============================================================================
// 1. 创建策略 (Creation Policy)
// ============================================================================

/**
 * @brief 使用 new 创建对象
 */
template <typename T>
struct CreateUsingNew {
    static T* create() {
        return new T();
    }

    static void destroy(T* ptr) {
        delete ptr;
    }
};

/**
 * @brief 使用自定义分配器创建对象
 */
template <typename T>
struct CreateUsingMalloc {
    static T* create() {
        void* mem = std::malloc(sizeof(T));
        if (!mem) return nullptr;
        return new(mem) T();
    }

    static void destroy(T* ptr) {
        if (ptr) {
            ptr->~T();
            std::free(ptr);
        }
    }
};

/**
 * @brief 使用静态存储创建对象（单例模式）
 */
template <typename T>
struct CreateStatic {
    static T* create() {
        static T instance;
        return &instance;
    }

    static void destroy(T*) {
        // 静态对象不销毁
    }
};

// ============================================================================
// 2. 所有权策略 (Ownership Policy)
// ============================================================================

/**
 * @brief 深拷贝所有权
 */
template <typename T>
struct DeepCopy {
    using storage_type = T*;

    static void clone(T* source, T*& dest) {
        if (source) {
            dest = new T(*source);
        } else {
            dest = nullptr;
        }
    }

    static void release(T*& ptr) {
        delete ptr;
        ptr = nullptr;
    }
};

/**
 * @brief 浅拷贝所有权（引用计数）
 */
template <typename T>
struct RefCounted {
    struct ControlBlock {
        T* ptr;
        std::size_t count;
    };

    using storage_type = ControlBlock*;

    static void clone(ControlBlock* source, ControlBlock*& dest) {
        dest = source;
        if (dest) {
            ++dest->count;
        }
    }

    static void release(ControlBlock*& cb) {
        if (cb && --cb->count == 0) {
            delete cb->ptr;
            delete cb;
        }
        cb = nullptr;
    }
};

/**
 * @brief 独占所有权
 */
template <typename T>
struct UniqueOwnership {
    using storage_type = T*;

    static void clone(T*, T*&) {
        // 独占所有权不能拷贝
        static_assert(sizeof(T) == 0,
                      "Unique ownership cannot be cloned");
    }

    static void release(T*& ptr) {
        delete ptr;
        ptr = nullptr;
    }
};

// ============================================================================
// 3. 线程模型策略 (Threading Policy)
// ============================================================================

/**
 * @brief 单线程模型 - 无锁
 */
struct SingleThreaded {
    struct Lock {
        Lock() {}
        ~Lock() {}
    };
};

/**
 * @brief 多线程模型 - 使用互斥锁
 */
struct MultiThreaded {
    static std::mutex& get_mutex() {
        static std::mutex mtx;
        return mtx;
    }

    struct Lock {
        std::lock_guard<std::mutex> guard_;
        Lock() : guard_(get_mutex()) {}
    };
};

// ============================================================================
// 4. 智能指针 - 使用策略组合
// ============================================================================

/**
 * @brief 策略化智能指针
 * @tparam T 指向的类型
 * @tparam CreationPolicy 创建策略
 * @tparam OwnershipPolicy 所有权策略
 * @tparam ThreadingPolicy 线程策略
 */
template <typename T,
          template <typename> class CreationPolicy = CreateUsingNew,
          template <typename> class OwnershipPolicy = DeepCopy,
          typename ThreadingPolicy = SingleThreaded>
class SmartPtr {
    typename OwnershipPolicy<T>::storage_type pointee_;

public:
    explicit SmartPtr(T* ptr = nullptr) : pointee_(ptr) {}

    SmartPtr(const SmartPtr& other) {
        typename ThreadingPolicy::Lock lock;
        OwnershipPolicy<T>::clone(other.pointee_, pointee_);
    }

    SmartPtr& operator=(const SmartPtr& other) {
        if (this != &other) {
            typename ThreadingPolicy::Lock lock;
            OwnershipPolicy<T>::release(pointee_);
            OwnershipPolicy<T>::clone(other.pointee_, pointee_);
        }
        return *this;
    }

    ~SmartPtr() {
        OwnershipPolicy<T>::release(pointee_);
    }

    T& operator*() { return *pointee_; }
    const T& operator*() const { return *pointee_; }
    T* operator->() { return pointee_; }
    const T* operator->() const { return pointee_; }

    /// @brief 获取原始指针
    T* get() { return pointee_; }
    const T* get() const { return pointee_; }
};

// ============================================================================
// 5. 策略化容器
// ============================================================================

/**
 * @brief 增长策略 - 每次翻倍
 */
struct DoubleGrowthPolicy {
    static std::size_t grow(std::size_t current) {
        return current * 2;
    }
};

/**
 * @brief 增长策略 - 每次增加固定大小
 */
struct LinearGrowthPolicy {
    static std::size_t grow(std::size_t current) {
        return current + 16;
    }
};

/**
 * @brief 增长策略 - 黄金比例
 */
struct GoldenGrowthPolicy {
    static std::size_t grow(std::size_t current) {
        return static_cast<std::size_t>(current * 1.618);
    }
};

/**
 * @brief 策略化动态数组
 * @tparam T 元素类型
 * @tparam GrowthPolicy 增长策略
 */
template <typename T, typename GrowthPolicy = DoubleGrowthPolicy>
class PolicyVector {
    T* data_ = nullptr;
    std::size_t size_ = 0;
    std::size_t capacity_ = 0;

public:
    PolicyVector() = default;

    ~PolicyVector() {
        delete[] data_;
    }

    void push_back(const T& value) {
        if (size_ >= capacity_) {
            grow_capacity();
        }
        data_[size_++] = value;
    }

    T& operator[](std::size_t i) { return data_[i]; }
    const T& operator[](std::size_t i) const { return data_[i]; }

    std::size_t size() const { return size_; }
    std::size_t capacity() const { return capacity_; }

private:
    void grow_capacity() {
        std::size_t new_cap = capacity_ == 0 ? 8
            : GrowthPolicy::grow(capacity_);
        T* new_data = new T[new_cap];
        for (std::size_t i = 0; i < size_; ++i) {
            new_data[i] = data_[i];
        }
        delete[] data_;
        data_ = new_data;
        capacity_ = new_cap;
    }
};

// ============================================================================
// 6. 策略化日志器
// ============================================================================

/**
 * @brief 日志输出策略 - 控制台
 */
struct ConsoleOutputPolicy {
    static void output(const std::string& message) {
        std::cout << message << std::endl;
    }
};

/**
 * @brief 日志输出策略 - 空操作（用于禁用日志）
 */
struct NullOutputPolicy {
    static void output(const std::string&) {
        // 什么都不做
    }
};

/**
 * @brief 日志级别策略
 */
struct VerboseLevel {
    static constexpr int value = 0;
};

struct NormalLevel {
    static constexpr int value = 1;
};

struct ErrorOnlyLevel {
    static constexpr int value = 2;
};

/**
 * @brief 策略化日志器
 * @tparam OutputPolicy 输出策略
 * @tparam LevelPolicy 日志级别策略
 */
template <typename OutputPolicy = ConsoleOutputPolicy,
          typename LevelPolicy = NormalLevel>
class Logger {
public:
    static void debug(const std::string& msg) {
        if constexpr (LevelPolicy::value <= 0) {
            OutputPolicy::output("[DEBUG] " + msg);
        }
    }

    static void info(const std::string& msg) {
        if constexpr (LevelPolicy::value <= 1) {
            OutputPolicy::output("[INFO] " + msg);
        }
    }

    static void error(const std::string& msg) {
        if constexpr (LevelPolicy::value <= 2) {
            OutputPolicy::output("[ERROR] " + msg);
        }
    }
};

}  // namespace tmp
