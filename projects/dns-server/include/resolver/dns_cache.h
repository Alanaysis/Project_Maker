#pragma once

/**
 * @file dns_cache.h
 * @brief DNS 缓存实现
 *
 * 实现 DNS 缓存机制，包括：
 * - LRU 缓存淘汰
 * - TTL 管理
 * - 缓存统计
 * - 负缓存 (Negative Cache)
 */

#include "../protocol/dns_message.h"
#include <string>
#include <unordered_map>
#include <list>
#include <mutex>
#include <chrono>
#include <optional>
#include <atomic>

namespace dns {

// ============================================================================
// 缓存配置
// ============================================================================

struct CacheConfig {
    size_t max_entries = 10000;            // 最大缓存条目数
    size_t max_negative_entries = 1000;    // 最大负缓存条目数
    uint32_t min_ttl = 60;                 // 最小 TTL (秒)
    uint32_t max_ttl = 86400;              // 最大 TTL (秒)
    uint32_t negative_ttl = 300;           // 负缓存 TTL (秒)
    bool enable_negative_cache = true;     // 启用负缓存
};

// ============================================================================
// 缓存统计
// ============================================================================

struct CacheStats {
    uint64_t hits = 0;           // 缓存命中
    uint64_t misses = 0;         // 缓存未命中
    uint64_t evictions = 0;      // 缓存淘汰数
    uint64_t inserts = 0;        // 插入数
    uint64_t expired = 0;        // 过期数
    size_t current_size = 0;     // 当前大小
    size_t negative_size = 0;    // 负缓存大小
    double hit_rate() const {
        uint64_t total = hits + misses;
        return total > 0 ? static_cast<double>(hits) / total : 0.0;
    }
};

// ============================================================================
// 缓存键
// ============================================================================

struct CacheKey {
    std::string name;
    RecordType type;
    QueryClass qclass;

    bool operator==(const CacheKey& other) const;
    struct Hash {
        size_t operator()(const CacheKey& key) const;
    };
};

// ============================================================================
// 缓存条目
// ============================================================================

struct CacheEntry {
    std::vector<ResourceRecord> records;     // 缓存的记录
    std::chrono::steady_clock::time_point expires_at;  // 过期时间
    std::chrono::steady_clock::time_point inserted_at; // 插入时间

    bool is_expired() const {
        return std::chrono::steady_clock::now() > expires_at;
    }

    // 获取剩余 TTL
    uint32_t remaining_ttl() const {
        auto now = std::chrono::steady_clock::now();
        if (now >= expires_at) return 0;
        auto remaining = std::chrono::duration_cast<std::chrono::seconds>(
            expires_at - now);
        return static_cast<uint32_t>(remaining.count());
    }
};

// ============================================================================
// 负缓存条目
// ============================================================================

struct NegativeCacheEntry {
    ResponseCode rcode;
    std::chrono::steady_clock::time_point expires_at;

    bool is_expired() const {
        return std::chrono::steady_clock::now() > expires_at;
    }
};

// ============================================================================
// DNS 缓存
// ============================================================================

class DnsCache {
public:
    explicit DnsCache(const CacheConfig& config = CacheConfig{});
    ~DnsCache();

    // 查询缓存
    std::optional<CacheEntry> get(const std::string& name, RecordType type);

    // 插入缓存
    void put(const std::string& name, RecordType type,
             const std::vector<ResourceRecord>& records, uint32_t ttl);

    // 插入负缓存
    void put_negative(const std::string& name, RecordType type,
                       ResponseCode rcode);

    // 查询负缓存
    bool is_negative_cached(const std::string& name, RecordType type);

    // 删除缓存条目
    void remove(const std::string& name, RecordType type);

    // 清除所有缓存
    void clear();

    // 清除过期条目
    void purge_expired();

    // 获取统计信息
    CacheStats get_stats() const;

    // 获取当前大小
    size_t size() const;

private:
    // LRU 淘汰
    void evict_if_needed();

    CacheConfig config_;

    // 正向缓存 (LRU)
    using LruList = std::list<CacheKey>;
    LruList lru_list_;
    std::unordered_map<CacheKey, std::pair<CacheEntry, LruList::iterator>,
                       CacheKey::Hash> cache_;

    // 负缓存
    std::unordered_map<CacheKey, NegativeCacheEntry,
                       CacheKey::Hash> negative_cache_;

    mutable std::mutex mutex_;

    // 统计
    std::atomic<uint64_t> hits_{0};
    std::atomic<uint64_t> misses_{0};
    std::atomic<uint64_t> evictions_{0};
    std::atomic<uint64_t> inserts_{0};
    std::atomic<uint64_t> expired_{0};
};

} // namespace dns
