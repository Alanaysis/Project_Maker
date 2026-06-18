#pragma once

#include <list>
#include <unordered_map>
#include <mutex>
#include <optional>

namespace minidb {

/**
 * @brief LRU 缓存
 *
 * Least Recently Used 缓存实现
 * 当缓存满时，淘汰最近最少使用的元素
 *
 * @tparam Key 键类型
 * @tparam Value 值类型
 */
template <typename Key, typename Value>
class LRUCache {
public:
    /**
     * @brief 构造函数
     * @param capacity 缓存容量
     */
    explicit LRUCache(size_t capacity) : capacity_(capacity) {}

    /**
     * @brief 获取缓存值
     * @param key 键
     * @return 值，如果不存在返回 std::nullopt
     */
    std::optional<Value> get(const Key& key) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = cache_map_.find(key);
        if (it == cache_map_.end()) {
            return std::nullopt;
        }

        // 移动到链表前端 (最近使用)
        cache_list_.splice(cache_list_.begin(), cache_list_, it->second);
        return it->second->second;
    }

    /**
     * @brief 插入或更新缓存
     * @param key 键
     * @param value 值
     */
    void put(const Key& key, const Value& value) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = cache_map_.find(key);
        if (it != cache_map_.end()) {
            // 更新现有项
            it->second->second = value;
            cache_list_.splice(cache_list_.begin(), cache_list_, it->second);
            return;
        }

        // 检查是否需要淘汰
        if (cache_map_.size() >= capacity_) {
            // 淘汰最久未使用的元素
            auto last = cache_list_.back();
            cache_map_.erase(last.first);
            cache_list_.pop_back();
        }

        // 插入新元素
        cache_list_.emplace_front(key, value);
        cache_map_[key] = cache_list_.begin();
    }

    /**
     * @brief 删除缓存项
     * @param key 键
     * @return 是否成功删除
     */
    bool remove(const Key& key) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto it = cache_map_.find(key);
        if (it == cache_map_.end()) {
            return false;
        }

        cache_list_.erase(it->second);
        cache_map_.erase(it);
        return true;
    }

    /**
     * @brief 检查缓存是否包含指定键
     * @param key 键
     * @return 是否包含
     */
    bool contains(const Key& key) const {
        std::lock_guard<std::mutex> lock(mutex_);
        return cache_map_.find(key) != cache_map_.end();
    }

    /**
     * @brief 获取缓存大小
     * @return 缓存中的元素数量
     */
    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return cache_map_.size();
    }

    /**
     * @brief 获取缓存容量
     * @return 缓存容量
     */
    size_t capacity() const {
        return capacity_;
    }

    /**
     * @brief 清空缓存
     */
    void clear() {
        std::lock_guard<std::mutex> lock(mutex_);
        cache_list_.clear();
        cache_map_.clear();
    }

private:
    using CacheItem = std::pair<Key, Value>;
    using CacheList = std::list<CacheItem>;
    using CacheMap = std::unordered_map<Key, typename CacheList::iterator>;

    size_t capacity_;
    CacheList cache_list_;
    CacheMap cache_map_;
    mutable std::mutex mutex_;
};

/**
 * @brief 线程安全的 LRU 缓存 (简化版本，与 LRUCache 相同)
 */
template <typename Key, typename Value>
class ThreadSafeLRUCache : public LRUCache<Key, Value> {
public:
    explicit ThreadSafeLRUCache(size_t capacity)
        : LRUCache<Key, Value>(capacity) {}
};

}  // namespace minidb
