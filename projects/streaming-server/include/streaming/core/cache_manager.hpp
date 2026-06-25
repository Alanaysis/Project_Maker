#pragma once

/**
 * @file cache_manager.hpp
 * @brief 缓存管理器
 *
 * 实现流媒体数据缓存，支持：
 * - 分段缓存
 * - LRU 淘汰策略
 * - 内存和磁盘缓存
 * - 预加载策略
 */

#include "streaming/types.hpp"
#include <string>
#include <memory>
#include <unordered_map>
#include <list>
#include <mutex>
#include <functional>
#include <chrono>

namespace streaming {

// 缓存策略
enum class CachePolicy {
    LRU,        // 最近最少使用
    LFU,        // 最不经常使用
    FIFO,       // 先进先出
    TTL         // 基于时间
};

// 缓存位置
enum class CacheLocation {
    Memory,     // 内存缓存
    Disk,       // 磁盘缓存
    Hybrid      // 混合缓存
};

// 缓存项
struct CacheItem {
    std::string key;
    Buffer data;
    uint64_t size = 0;
    uint32_t access_count = 0;
    Timestamp create_time;
    Timestamp last_access;
    std::chrono::seconds ttl{0};
    bool pinned = false;    // 是否固定（不被淘汰）
};

using CacheItemPtr = std::shared_ptr<CacheItem>;

/**
 * @brief 内存缓存
 *
 * 基于 LRU 策略的内存缓存实现。
 */
class MemoryCache {
public:
    /**
     * @brief 构造函数
     * @param max_size 最大缓存大小（字节）
     * @param max_items 最大缓存项数
     */
    explicit MemoryCache(uint64_t max_size = 100 * 1024 * 1024,  // 100MB
                        uint32_t max_items = 1000);
    ~MemoryCache();

    /**
     * @brief 获取缓存项
     * @param key 缓存键
     * @return 缓存项，不存在返回 nullptr
     */
    CacheItemPtr get(const std::string& key);

    /**
     * @brief 设置缓存项
     * @param key 缓存键
     * @param data 数据
     * @param ttl 生存时间（秒），0 表示永不过期
     * @return 是否成功
     */
    bool set(const std::string& key, const Buffer& data, uint32_t ttl = 0);

    /**
     * @brief 设置缓存项（带大小限制）
     */
    bool set(const std::string& key, const Buffer& data, uint64_t max_size, uint32_t ttl = 0);

    /**
     * @brief 删除缓存项
     * @param key 缓存键
     * @return 是否成功
     */
    bool remove(const std::string& key);

    /**
     * @brief 检查缓存项是否存在
     */
    bool exists(const std::string& key) const;

    /**
     * @brief 清空缓存
     */
    void clear();

    /**
     * @brief 获取缓存大小
     */
    uint64_t get_size() const { return current_size_; }

    /**
     * @brief 获取缓存项数
     */
    uint32_t get_count() const { return items_.size(); }

    /**
     * @brief 获取缓存命中率
     */
    double get_hit_rate() const;

    /**
     * @brief 设置固定项
     */
    void pin(const std::string& key);
    void unpin(const std::string& key);

private:
    // LRU 链表
    using LruList = std::list<std::string>;
    using LruIterator = LruList::iterator;

    void evict();
    void update_access(const std::string& key);
    bool is_expired(const CacheItem& item) const;

    uint64_t max_size_;
    uint32_t max_items_;
    uint64_t current_size_ = 0;

    std::unordered_map<std::string, CacheItemPtr> items_;
    LruList lru_list_;
    std::unordered_map<std::string, LruIterator> lru_map_;

    mutable std::mutex mutex_;

    // 统计
    std::atomic<uint64_t> hits_{0};
    std::atomic<uint64_t> misses_{0};
};

/**
 * @brief 磁盘缓存
 *
 * 基于文件系统的缓存实现。
 */
class DiskCache {
public:
    /**
     * @brief 构造函数
     * @param cache_dir 缓存目录
     * @param max_size 最大缓存大小（字节）
     */
    explicit DiskCache(const std::string& cache_dir,
                      uint64_t max_size = 1024 * 1024 * 1024);  // 1GB
    ~DiskCache();

    /**
     * @brief 初始化缓存目录
     */
    bool initialize();

    /**
     * @brief 获取缓存项
     */
    CacheItemPtr get(const std::string& key);

    /**
     * @brief 设置缓存项
     */
    bool set(const std::string& key, const Buffer& data, uint32_t ttl = 0);

    /**
     * @brief 删除缓存项
     */
    bool remove(const std::string& key);

    /**
     * @brief 检查缓存项是否存在
     */
    bool exists(const std::string& key) const;

    /**
     * @brief 清空缓存
     */
    void clear();

    /**
     * @brief 获取缓存大小
     */
    uint64_t get_size() const { return current_size_; }

private:
    std::string get_cache_path(const std::string& key) const;
    std::string hash_key(const std::string& key) const;
    void evict_if_needed();

    std::string cache_dir_;
    uint64_t max_size_;
    uint64_t current_size_ = 0;
    std::unordered_map<std::string, std::string> key_to_path_;
    mutable std::mutex mutex_;
};

/**
 * @brief 缓存管理器
 *
 * 统一管理内存缓存和磁盘缓存。
 */
class CacheManager {
public:
    /**
     * @brief 构造函数
     * @param policy 缓存策略
     * @param memory_size 内存缓存大小
     * @param disk_size 磁盘缓存大小
     * @param disk_dir 磁盘缓存目录
     */
    explicit CacheManager(
        CachePolicy policy = CachePolicy::LRU,
        uint64_t memory_size = 100 * 1024 * 1024,
        uint64_t disk_size = 1024 * 1024 * 1024,
        const std::string& disk_dir = "./cache"
    );
    ~CacheManager();

    /**
     * @brief 初始化缓存管理器
     */
    bool initialize();

    /**
     * @brief 获取缓存项
     * @param key 缓存键
     * @param location 缓存位置
     * @return 缓存项
     */
    CacheItemPtr get(const std::string& key,
                    CacheLocation location = CacheLocation::Memory);

    /**
     * @brief 设置缓存项
     * @param key 缓存键
     * @param data 数据
     * @param location 缓存位置
     * @param ttl 生存时间
     * @return 是否成功
     */
    bool set(const std::string& key, const Buffer& data,
             CacheLocation location = CacheLocation::Memory,
             uint32_t ttl = 0);

    /**
     * @brief 删除缓存项
     */
    bool remove(const std::string& key);

    /**
     * @brief 预加载数据
     * @param keys 要预加载的键列表
     * @param loader 加载函数
     */
    void preload(const std::vector<std::string>& keys,
                std::function<Buffer(const std::string&)> loader);

    /**
     * @brief 获取缓存统计
     */
    struct CacheStats {
        uint64_t memory_size = 0;
        uint64_t disk_size = 0;
        uint32_t memory_items = 0;
        uint64_t memory_hits = 0;
        uint64_t memory_misses = 0;
        uint64_t disk_hits = 0;
        uint64_t disk_misses = 0;
        double hit_rate = 0.0;
    };
    CacheStats get_stats() const;

    /**
     * @brief 清空所有缓存
     */
    void clear_all();

private:
    CachePolicy policy_;
    std::unique_ptr<MemoryCache> memory_cache_;
    std::unique_ptr<DiskCache> disk_cache_;
};

} // namespace streaming
