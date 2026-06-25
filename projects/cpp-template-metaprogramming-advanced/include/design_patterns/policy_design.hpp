#pragma once
/**
 * @file policy_design.hpp
 * @brief 策略模式 (Policy-based Design)
 *
 * 策略模式通过模板参数组合不同的策略，
 * 实现高度可配置的类设计。
 *
 * 核心模式：
 *   - 主机类 (Host Class)
 *   - 策略类 (Policy Class)
 *   - 策略组合
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <chrono>
#include <mutex>
#include <fstream>
#include <sstream>
#include <cstring>

namespace tmp {

// ============================================================================
// 1. 策略化智能指针
// ============================================================================

/// @brief 默认存储策略
template <typename T>
struct HeapStorage {
    T* allocate() { return new T(); }
    T* allocate_array(std::size_t n) { return new T[n](); }
    void deallocate(T* p) { delete p; }
    void deallocate_array(T* p) { delete[] p; }
};

/// @brief 栈存储策略
template <typename T, std::size_t MaxSize = 256>
struct StackStorage {
    alignas(T) char buffer_[MaxSize];
    bool used_ = false;

    T* allocate() {
        if (used_) return nullptr;
        used_ = true;
        return reinterpret_cast<T*>(buffer_);
    }

    void deallocate(T* p) {
        if (p == reinterpret_cast<T*>(buffer_)) {
            p->~T();
            used_ = false;
        }
    }
};

// ============================================================================
// 2. 策略化容器
// ============================================================================

/// @brief 边界检查策略：无检查
struct NoBoundsCheck {
    static void check(std::size_t, std::size_t) {}
};

/// @brief 边界检查策略：抛出异常
struct ThrowBoundsCheck {
    static void check(std::size_t index, std::size_t size) {
        if (index >= size) {
            throw std::out_of_range("Index " + std::to_string(index) +
                                     " out of range [0, " +
                                     std::to_string(size) + ")");
        }
    }
};

/// @brief 边界检查策略：断言
struct AssertBoundsCheck {
    static void check(std::size_t index, std::size_t size) {
        if (index >= size) {
            std::cerr << "FATAL: Index out of range" << std::endl;
            std::abort();
        }
    }
};

/**
 * @brief 策略化向量
 * @tparam T 元素类型
 * @tparam BoundsCheck 边界检查策略
 * @tparam Growth 增长策略
 */
template <typename T,
          typename BoundsCheck = ThrowBoundsCheck>
class PolicyBasedVector {
    std::vector<T> data_;

public:
    void push_back(const T& value) { data_.push_back(value); }
    void push_back(T&& value) { data_.push_back(std::move(value)); }

    T& operator[](std::size_t i) {
        BoundsCheck::check(i, data_.size());
        return data_[i];
    }

    const T& operator[](std::size_t i) const {
        BoundsCheck::check(i, data_.size());
        return data_[i];
    }

    std::size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
};

// ============================================================================
// 3. 策略化消息系统
// ============================================================================

/// @brief 消息格式策略
struct PlainTextFormat {
    static std::string format(const std::string& level,
                               const std::string& msg) {
        return "[" + level + "] " + msg;
    }
};

struct JsonFormat {
    static std::string format(const std::string& level,
                               const std::string& msg) {
        return "{\"level\":\"" + level + "\",\"message\":\"" + msg + "\"}";
    }
};

/// @brief 输出策略
struct ConsoleOutput {
    static void write(const std::string& msg) {
        std::cout << msg << std::endl;
    }
};

struct FileOutput {
    static void write(const std::string& msg) {
        static std::ofstream file("app.log", std::ios::app);
        file << msg << std::endl;
    }
};

struct NullOutput {
    static void write(const std::string&) {}
};

/**
 * @brief 策略化消息系统
 */
template <typename Format = PlainTextFormat, typename Output = ConsoleOutput>
class MessageSystem {
public:
    static void info(const std::string& msg) {
        Output::write(Format::format("INFO", msg));
    }

    static void warn(const std::string& msg) {
        Output::write(Format::format("WARN", msg));
    }

    static void error(const std::string& msg) {
        Output::write(Format::format("ERROR", msg));
    }
};

// ============================================================================
// 4. 策略化序列化
// ============================================================================

/// @brief 二进制序列化策略
struct BinarySerialization {
    template <typename T>
    static std::string serialize(const T& value) {
        const char* bytes = reinterpret_cast<const char*>(&value);
        return std::string(bytes, sizeof(T));
    }

    template <typename T>
    static T deserialize(const std::string& data) {
        T value;
        std::memcpy(&value, data.data(), sizeof(T));
        return value;
    }
};

/// @brief 文本序列化策略
struct TextSerialization {
    template <typename T>
    static std::string serialize(const T& value) {
        return std::to_string(value);
    }

    template <typename T>
    static T deserialize(const std::string& data) {
        if constexpr (std::is_integral_v<T>) {
            return static_cast<T>(std::stoll(data));
        } else if constexpr (std::is_floating_point_v<T>) {
            return static_cast<T>(std::stod(data));
        }
    }
};

/**
 * @brief 策略化数据存储
 */
template <typename T, typename Serialization = BinarySerialization>
class DataStore {
    std::string key_;
    T value_;

public:
    DataStore(const std::string& key, const T& value)
        : key_(key), value_(value) {}

    std::string serialize() const {
        return Serialization::serialize(value_);
    }

    void deserialize(const std::string& data) {
        value_ = Serialization::template deserialize<T>(data);
    }

    const T& get() const { return value_; }
    void set(const T& value) { value_ = value; }
};

// ============================================================================
// 5. 策略化线程安全
// ============================================================================

/// @brief 无锁策略
struct NoLocking {
    struct LockGuard {
        LockGuard() {}
    };
};

/// @brief 互斥锁策略
struct MutexLocking {
    static std::mutex& mutex() {
        static std::mutex m;
        return m;
    }

    struct LockGuard {
        std::lock_guard<std::mutex> guard_;
        LockGuard() : guard_(mutex()) {}
    };
};

/**
 * @brief 策略化线程安全容器
 */
template <typename T, typename ThreadingPolicy = NoLocking>
class ThreadSafeVector {
    std::vector<T> data_;

public:
    void push_back(const T& value) {
        typename ThreadingPolicy::LockGuard lock;
        data_.push_back(value);
    }

    T& at(std::size_t i) {
        typename ThreadingPolicy::LockGuard lock;
        return data_.at(i);
    }

    std::size_t size() const {
        typename ThreadingPolicy::LockGuard lock;
        return data_.size();
    }
};

// ============================================================================
// 6. 策略化配置系统
// ============================================================================

/// @brief 配置来源策略
struct CommandLineConfig {
    static std::string get(const std::string& key) {
        // 简化实现
        return "";
    }
};

struct EnvVarConfig {
    static std::string get(const std::string& key) {
        const char* val = std::getenv(key.c_str());
        return val ? std::string(val) : "";
    }
};

struct JsonFileConfig {
    static std::string get(const std::string& key) {
        // 简化实现
        return "";
    }
};

/**
 * @brief 策略化配置管理器
 */
template <typename Source = EnvVarConfig>
class ConfigManager {
public:
    template <typename T>
    static T get(const std::string& key, const T& default_value = T{}) {
        std::string value = Source::get(key);
        if (value.empty()) return default_value;
        if constexpr (std::is_same_v<T, std::string>) {
            return value;
        } else if constexpr (std::is_integral_v<T>) {
            return static_cast<T>(std::stoll(value));
        } else if constexpr (std::is_floating_point_v<T>) {
            return static_cast<T>(std::stod(value));
        }
        return default_value;
    }
};

}  // namespace tmp
