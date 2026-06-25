/**
 * @file dns_cache.cpp
 * @brief DNS 缓存实现
 *
 * 实现 DNS 缓存机制，包括：
 * - LRU 缓存淘汰
 * - TTL 管理
 * - 缓存统计
 * - 负缓存 (Negative Cache)
 */

#include "resolver/dns_cache.h"
#include "monitoring/dns_monitor.h"

#include <algorithm>
#include <chrono>

namespace dns {

// ============================================================================
// CacheKey 实现
// ============================================================================

bool CacheKey::operator==(const CacheKey& other) const {
    return name == other.name && type == other.type && qclass == other.qclass;
}

size_t CacheKey::Hash::operator()(const CacheKey& key) const {
    size_t h1 = std::hash<std::string>{}(key.name);
    size_t h2 = std::hash<uint16_t>{}(static_cast<uint16_t>(key.type));
    size_t h3 = std::hash<uint16_t>{}(static_cast<uint16_t>(key.qclass));
    return h1 ^ (h2 << 1) ^ (h3 << 2);
}

// ============================================================================
// DnsCache 实现
// ============================================================================

DnsCache::DnsCache(const CacheConfig& config) : config_(config) {}

DnsCache::~DnsCache() {}

std::optional<CacheEntry> DnsCache::get(const std::string& name,
                                          RecordType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    CacheKey key{name, type, QueryClass::IN};
    auto it = cache_.find(key);
    if (it == cache_.end()) {
        misses_++;
        return std::nullopt;
    }

    auto& [entry, lru_iter] = it->second;

    // 检查是否过期
    if (entry.is_expired()) {
        // 删除过期条目
        lru_list_.erase(lru_iter);
        cache_.erase(it);
        expired_++;
        misses_++;
        return std::nullopt;
    }

    // 移到 LRU 列表头部
    lru_list_.splice(lru_list_.begin(), lru_list_, lru_iter);

    hits_++;

    // 调整 TTL
    CacheEntry result = entry;
    for (auto& rr : result.records) {
        rr.ttl = result.remaining_ttl();
    }

    return result;
}

void DnsCache::put(const std::string& name, RecordType type,
                    const std::vector<ResourceRecord>& records, uint32_t ttl) {
    if (records.empty()) return;

    std::lock_guard<std::mutex> lock(mutex_);

    // 调整 TTL
    uint32_t adjusted_ttl = std::clamp(ttl, config_.min_ttl, config_.max_ttl);

    CacheKey key{name, type, QueryClass::IN};
    auto now = std::chrono::steady_clock::now();

    CacheEntry entry;
    entry.records = records;
    entry.inserted_at = now;
    entry.expires_at = now + std::chrono::seconds(adjusted_ttl);

    // 检查是否已存在
    auto it = cache_.find(key);
    if (it != cache_.end()) {
        // 更新现有条目
        lru_list_.erase(it->second.second);
        cache_.erase(it);
    }

    // 插入新条目
    lru_list_.push_front(key);
    cache_[key] = std::make_pair(std::move(entry), lru_list_.begin());
    inserts_++;

    // 检查是否需要淘汰
    evict_if_needed();
}

void DnsCache::put_negative(const std::string& name, RecordType type,
                              ResponseCode rcode) {
    if (!config_.enable_negative_cache) return;

    std::lock_guard<std::mutex> lock(mutex_);

    CacheKey key{name, type, QueryClass::IN};
    auto now = std::chrono::steady_clock::now();

    NegativeCacheEntry entry;
    entry.rcode = rcode;
    entry.expires_at = now + std::chrono::seconds(config_.negative_ttl);

    // 限制负缓存大小
    if (negative_cache_.size() >= config_.max_negative_entries) {
        // 删除最旧的条目
        auto oldest = negative_cache_.begin();
        for (auto it = negative_cache_.begin();
             it != negative_cache_.end(); ++it) {
            if (it->second.expires_at < oldest->second.expires_at) {
                oldest = it;
            }
        }
        negative_cache_.erase(oldest);
    }

    negative_cache_[key] = entry;
}

bool DnsCache::is_negative_cached(const std::string& name, RecordType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    CacheKey key{name, type, QueryClass::IN};
    auto it = negative_cache_.find(key);
    if (it == negative_cache_.end()) {
        return false;
    }

    if (it->second.is_expired()) {
        negative_cache_.erase(it);
        return false;
    }

    return true;
}

void DnsCache::remove(const std::string& name, RecordType type) {
    std::lock_guard<std::mutex> lock(mutex_);

    CacheKey key{name, type, QueryClass::IN};

    auto it = cache_.find(key);
    if (it != cache_.end()) {
        lru_list_.erase(it->second.second);
        cache_.erase(it);
    }

    negative_cache_.erase(key);
}

void DnsCache::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    cache_.clear();
    lru_list_.clear();
    negative_cache_.clear();
}

void DnsCache::purge_expired() {
    std::lock_guard<std::mutex> lock(mutex_);

    // 清除过期的正向缓存
    for (auto it = cache_.begin(); it != cache_.end();) {
        if (it->second.first.is_expired()) {
            lru_list_.erase(it->second.second);
            it = cache_.erase(it);
            expired_++;
        } else {
            ++it;
        }
    }

    // 清除过期的负缓存
    for (auto it = negative_cache_.begin(); it != negative_cache_.end();) {
        if (it->second.is_expired()) {
            it = negative_cache_.erase(it);
        } else {
            ++it;
        }
    }
}

CacheStats DnsCache::get_stats() const {
    std::lock_guard<std::mutex> lock(mutex_);

    CacheStats stats;
    stats.hits = hits_.load();
    stats.misses = misses_.load();
    stats.evictions = evictions_.load();
    stats.inserts = inserts_.load();
    stats.expired = expired_.load();
    stats.current_size = cache_.size();
    stats.negative_size = negative_cache_.size();

    return stats;
}

size_t DnsCache::size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return cache_.size();
}

void DnsCache::evict_if_needed() {
    while (cache_.size() > config_.max_entries) {
        // 淘汰 LRU 列表末尾的条目
        auto last_key = lru_list_.back();
        lru_list_.pop_back();
        cache_.erase(last_key);
        evictions_++;
    }
}

} // namespace dns
