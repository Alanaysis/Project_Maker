/**
 * @file cache_manager.cpp
 * @brief 缓存管理器实现
 */

#include "streaming/core/cache_manager.hpp"
#include "streaming/monitor/logger.hpp"

#include <filesystem>
#include <fstream>
#include <functional>
#include <sstream>
#include <iomanip>

namespace streaming {

// ============================================================================
// MemoryCache 实现
// ============================================================================

MemoryCache::MemoryCache(uint64_t max_size, uint32_t max_items)
    : max_size_(max_size), max_items_(max_items) {}

MemoryCache::~MemoryCache() = default;

CacheItemPtr MemoryCache::get(const std::string& key) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = items_.find(key);
    if (it == items_.end()) {
        misses_++;
        return nullptr;
    }

    // 检查是否过期
    if (is_expired(*it->second)) {
        // 删除过期项
        lru_list_.erase(lru_map_[key]);
        lru_map_.erase(key);
        current_size_ -= it->second->size;
        items_.erase(it);
        misses_++;
        return nullptr;
    }

    // 更新访问信息
    update_access(key);
    hits_++;

    return it->second;
}

bool MemoryCache::set(const std::string& key, const Buffer& data, uint32_t ttl) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 如果已存在，先删除
    auto it = items_.find(key);
    if (it != items_.end()) {
        current_size_ -= it->second->size;
        lru_list_.erase(lru_map_[key]);
        lru_map_.erase(key);
        items_.erase(it);
    }

    // 检查是否需要淘汰
    while (current_size_ + data.size() > max_size_ || items_.size() >= max_items_) {
        if (!lru_list_.empty()) {
            evict();
        } else {
            break;
        }
    }

    // 创建缓存项
    auto item = std::make_shared<CacheItem>();
    item->key = key;
    item->data = data;
    item->size = data.size();
    item->create_time = std::chrono::steady_clock::now();
    item->last_access = item->create_time;
    item->ttl = std::chrono::seconds(ttl);

    // 添加到 LRU 链表
    lru_list_.push_front(key);
    lru_map_[key] = lru_list_.begin();

    items_[key] = item;
    current_size_ += item->size;

    return true;
}

bool MemoryCache::set(const std::string& key, const Buffer& data, uint64_t max_size, uint32_t ttl) {
    if (data.size() > max_size) {
        LOG_WARN("Cache item size exceeds max_size");
        return false;
    }
    return set(key, data, ttl);
}

bool MemoryCache::remove(const std::string& key) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = items_.find(key);
    if (it == items_.end()) {
        return false;
    }

    current_size_ -= it->second->size;
    lru_list_.erase(lru_map_[key]);
    lru_map_.erase(key);
    items_.erase(it);

    return true;
}

bool MemoryCache::exists(const std::string& key) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = items_.find(key);
    if (it == items_.end()) {
        return false;
    }

    return !is_expired(*it->second);
}

void MemoryCache::clear() {
    std::lock_guard<std::mutex> lock(mutex_);

    items_.clear();
    lru_list_.clear();
    lru_map_.clear();
    current_size_ = 0;
}

double MemoryCache::get_hit_rate() const {
    uint64_t total = hits_ + misses_;
    if (total == 0) return 0.0;
    return static_cast<double>(hits_) / total;
}

void MemoryCache::pin(const std::string& key) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = items_.find(key);
    if (it != items_.end()) {
        it->second->pinned = true;
    }
}

void MemoryCache::unpin(const std::string& key) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = items_.find(key);
    if (it != items_.end()) {
        it->second->pinned = false;
    }
}

void MemoryCache::evict() {
    // 从尾部开始淘汰
    while (!lru_list_.empty()) {
        const std::string& key = lru_list_.back();
        auto it = items_.find(key);

        if (it != items_.end() && !it->second->pinned) {
            current_size_ -= it->second->size;
            lru_map_.erase(key);
            lru_list_.pop_back();
            items_.erase(it);
            return;
        }

        // 如果是固定项，跳过
        lru_list_.pop_back();
    }
}

void MemoryCache::update_access(const std::string& key) {
    auto lru_it = lru_map_.find(key);
    if (lru_it != lru_map_.end()) {
        lru_list_.erase(lru_it->second);
        lru_list_.push_front(key);
        lru_it->second = lru_list_.begin();
    }

    auto it = items_.find(key);
    if (it != items_.end()) {
        it->second->last_access = std::chrono::steady_clock::now();
        it->second->access_count++;
    }
}

bool MemoryCache::is_expired(const CacheItem& item) const {
    if (item.ttl.count() == 0) return false;

    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - item.create_time);
    return elapsed >= item.ttl;
}

// ============================================================================
// DiskCache 实现
// ============================================================================

DiskCache::DiskCache(const std::string& cache_dir, uint64_t max_size)
    : cache_dir_(cache_dir), max_size_(max_size) {}

DiskCache::~DiskCache() = default;

bool DiskCache::initialize() {
    try {
        std::filesystem::create_directories(cache_dir_);
        return true;
    } catch (const std::exception& e) {
        LOG_ERROR("Failed to create cache directory: " + std::string(e.what()));
        return false;
    }
}

CacheItemPtr DiskCache::get(const std::string& key) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto path_it = key_to_path_.find(key);
    if (path_it == key_to_path_.end()) {
        return nullptr;
    }

    auto item = std::make_shared<CacheItem>();
    item->key = key;

    std::ifstream file(path_it->second, std::ios::binary);
    if (!file) {
        return nullptr;
    }

    // 读取文件
    file.seekg(0, std::ios::end);
    item->size = file.tellg();
    file.seekg(0, std::ios::beg);

    item->data.resize(item->size);
    file.read(reinterpret_cast<char*>(item->data.data()), item->size);

    item->last_access = std::chrono::steady_clock::now();
    item->access_count = 1;

    return item;
}

bool DiskCache::set(const std::string& key, const Buffer& data, uint32_t ttl) {
    std::lock_guard<std::mutex> lock(mutex_);

    // 检查空间
    evict_if_needed();

    if (current_size_ + data.size() > max_size_) {
        return false;
    }

    std::string path = get_cache_path(key);

    // 写入文件
    std::ofstream file(path, std::ios::binary);
    if (!file) {
        return false;
    }

    file.write(reinterpret_cast<const char*>(data.data()), data.size());
    file.close();

    key_to_path_[key] = path;
    current_size_ += data.size();

    return true;
}

bool DiskCache::remove(const std::string& key) {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = key_to_path_.find(key);
    if (it == key_to_path_.end()) {
        return false;
    }

    try {
        uintmax_t size = std::filesystem::file_size(it->second);
        std::filesystem::remove(it->second);
        current_size_ -= size;
    } catch (...) {
        // 忽略错误
    }

    key_to_path_.erase(it);
    return true;
}

bool DiskCache::exists(const std::string& key) const {
    std::lock_guard<std::mutex> lock(mutex_);

    auto it = key_to_path_.find(key);
    if (it == key_to_path_.end()) {
        return false;
    }

    return std::filesystem::exists(it->second);
}

void DiskCache::clear() {
    std::lock_guard<std::mutex> lock(mutex_);

    try {
        for (const auto& [key, path] : key_to_path_) {
            std::filesystem::remove(path);
        }
    } catch (...) {
        // 忽略错误
    }

    key_to_path_.clear();
    current_size_ = 0;
}

std::string DiskCache::get_cache_path(const std::string& key) const {
    return cache_dir_ + "/" + hash_key(key) + ".cache";
}

std::string DiskCache::hash_key(const std::string& key) const {
    // 简单哈希实现
    std::hash<std::string> hasher;
    size_t hash = hasher(key);

    std::ostringstream ss;
    ss << std::hex << std::setw(16) << std::setfill('0') << hash;
    return ss.str();
}

void DiskCache::evict_if_needed() {
    // 简单的 FIFO 淘汰策略
    while (current_size_ > max_size_ && !key_to_path_.empty()) {
        auto it = key_to_path_.begin();
        try {
            uintmax_t size = std::filesystem::file_size(it->second);
            std::filesystem::remove(it->second);
            current_size_ -= size;
        } catch (...) {
            // 忽略错误
        }
        key_to_path_.erase(it);
    }
}

// ============================================================================
// CacheManager 实现
// ============================================================================

CacheManager::CacheManager(CachePolicy policy, uint64_t memory_size,
                           uint64_t disk_size, const std::string& disk_dir)
    : policy_(policy) {
    memory_cache_ = std::make_unique<MemoryCache>(memory_size);
    disk_cache_ = std::make_unique<DiskCache>(disk_dir, disk_size);
}

CacheManager::~CacheManager() = default;

bool CacheManager::initialize() {
    if (!disk_cache_->initialize()) {
        LOG_ERROR("Failed to initialize disk cache");
        return false;
    }

    LOG_INFO("CacheManager initialized");
    return true;
}

CacheItemPtr CacheManager::get(const std::string& key, CacheLocation location) {
    switch (location) {
        case CacheLocation::Memory:
            return memory_cache_->get(key);

        case CacheLocation::Disk:
            return disk_cache_->get(key);

        case CacheLocation::Hybrid: {
            // 先从内存缓存查找
            auto item = memory_cache_->get(key);
            if (item) {
                return item;
            }

            // 再从磁盘缓存查找
            item = disk_cache_->get(key);
            if (item) {
                // 提升到内存缓存
                memory_cache_->set(key, item->data);
                return item;
            }

            return nullptr;
        }
    }

    return nullptr;
}

bool CacheManager::set(const std::string& key, const Buffer& data,
                       CacheLocation location, uint32_t ttl) {
    switch (location) {
        case CacheLocation::Memory:
            return memory_cache_->set(key, data, ttl);

        case CacheLocation::Disk:
            return disk_cache_->set(key, data, ttl);

        case CacheLocation::Hybrid: {
            // 同时写入内存和磁盘缓存
            bool memory_ok = memory_cache_->set(key, data, ttl);
            bool disk_ok = disk_cache_->set(key, data, ttl);
            return memory_ok || disk_ok;
        }
    }

    return false;
}

bool CacheManager::remove(const std::string& key) {
    bool memory_ok = memory_cache_->remove(key);
    bool disk_ok = disk_cache_->remove(key);
    return memory_ok || disk_ok;
}

void CacheManager::preload(const std::vector<std::string>& keys,
                          std::function<Buffer(const std::string&)> loader) {
    for (const auto& key : keys) {
        // 检查是否已缓存
        if (memory_cache_->exists(key)) {
            continue;
        }

        // 加载数据
        Buffer data = loader(key);
        if (!data.empty()) {
            memory_cache_->set(key, data);
        }
    }

    LOG_INFO("Preloaded " + std::to_string(keys.size()) + " cache items");
}

CacheManager::CacheStats CacheManager::get_stats() const {
    CacheStats stats;
    stats.memory_size = memory_cache_->get_size();
    stats.memory_items = memory_cache_->get_count();
    stats.disk_size = disk_cache_->get_size();

    // 计算命中率
    stats.hit_rate = memory_cache_->get_hit_rate();

    return stats;
}

void CacheManager::clear_all() {
    memory_cache_->clear();
    disk_cache_->clear();
    LOG_INFO("CacheManager cleared all caches");
}

} // namespace streaming
