#include "storage/buffer_pool.h"
#include <iostream>

namespace minidb {

// ==================== LRUReplacer ====================

LRUReplacer::LRUReplacer(size_t num_pages) : num_pages_(num_pages) {}

bool LRUReplacer::victim(size_t* frame_id) {
    std::lock_guard<std::mutex> lock(latch_);

    if (lru_list_.empty()) {
        return false;
    }

    // 获取最久未使用的帧
    *frame_id = lru_list_.back();
    lru_list_.pop_back();
    lru_map_.erase(*frame_id);

    return true;
}

void LRUReplacer::pin(size_t frame_id) {
    std::lock_guard<std::mutex> lock(latch_);

    auto it = lru_map_.find(frame_id);
    if (it != lru_map_.end()) {
        // 从 LRU 列表中移除
        lru_list_.erase(it->second);
        lru_map_.erase(it);
    }
}

void LRUReplacer::unpin(size_t frame_id) {
    std::lock_guard<std::mutex> lock(latch_);

    // 如果已经在 LRU 列表中，先移除
    auto it = lru_map_.find(frame_id);
    if (it != lru_map_.end()) {
        lru_list_.erase(it->second);
        lru_map_.erase(it);
    }

    // 添加到列表前端 (最近使用)
    lru_list_.push_front(frame_id);
    lru_map_[frame_id] = lru_list_.begin();
}

size_t LRUReplacer::size() const {
    std::lock_guard<std::mutex> lock(latch_);
    return lru_list_.size();
}

// ==================== BufferPoolManager ====================

BufferPoolManager::BufferPoolManager(size_t pool_size, DiskManager* disk_manager)
    : pool_size_(pool_size), disk_manager_(disk_manager) {
    // 分配页面数组
    pages_ = new Page[pool_size];

    // 初始化空闲帧列表
    for (size_t i = 0; i < pool_size; ++i) {
        free_list_.push_back(i);
    }

    // 创建 LRU 替换器
    replacer_ = std::make_unique<LRUReplacer>(pool_size);

    MINIDB_LOG("BufferPoolManager initialized with " +
               std::to_string(pool_size) + " pages");
}

BufferPoolManager::~BufferPoolManager() {
    // 刷新所有脏页
    flushAllPages();

    // 释放页面数组
    delete[] pages_;
}

Page* BufferPoolManager::fetchPage(page_id_t page_id) {
    std::lock_guard<std::mutex> lock(latch_);

    // 检查页面是否已在缓冲池中
    auto it = page_table_.find(page_id);
    if (it != page_table_.end()) {
        // 页面命中
        size_t frame = it->second;
        replacer_->pin(frame);
        pages_[frame].incrementPinCount();
        return &pages_[frame];
    }

    // 页面未命中，需要从磁盘加载
    size_t frame;
    if (!free_list_.empty()) {
        // 使用空闲帧
        frame = free_list_.front();
        free_list_.pop_front();
    } else {
        // 需要替换
        if (!replacer_->victim(&frame)) {
            MINIDB_ERROR("BufferPoolManager: No available frame");
            return nullptr;
        }

        // 如果是脏页，先写回磁盘
        if (pages_[frame].isDirty()) {
            disk_manager_->writePage(pages_[frame].getPageId(),
                                     pages_[frame].getData());
        }

        // 从页面表中移除旧映射
        page_table_.erase(pages_[frame].getPageId());
    }

    // 从磁盘读取页面
    disk_manager_->readPage(page_id, pages_[frame].getData());
    pages_[frame].setPageId(page_id);
    pages_[frame].setDirty(false);
    pages_[frame].incrementPinCount();

    // 更新页面表
    page_table_[page_id] = frame;
    replacer_->pin(frame);

    return &pages_[frame];
}

Page* BufferPoolManager::newPage(page_id_t* page_id) {
    std::lock_guard<std::mutex> lock(latch_);

    size_t frame;
    if (!free_list_.empty()) {
        // 使用空闲帧
        frame = free_list_.front();
        free_list_.pop_front();
    } else {
        // 需要替换
        if (!replacer_->victim(&frame)) {
            MINIDB_ERROR("BufferPoolManager: No available frame");
            return nullptr;
        }

        // 如果是脏页，先写回磁盘
        if (pages_[frame].isDirty()) {
            disk_manager_->writePage(pages_[frame].getPageId(),
                                     pages_[frame].getData());
        }

        // 从页面表中移除旧映射
        page_table_.erase(pages_[frame].getPageId());
    }

    // 分配新页面
    *page_id = disk_manager_->allocatePage();

    // 初始化页面
    pages_[frame].reset();
    pages_[frame].setPageId(*page_id);
    pages_[frame].setDirty(true);
    pages_[frame].incrementPinCount();

    // 更新页面表
    page_table_[*page_id] = frame;
    replacer_->pin(frame);

    return &pages_[frame];
}

bool BufferPoolManager::unpinPage(page_id_t page_id, bool is_dirty) {
    std::lock_guard<std::mutex> lock(latch_);

    auto it = page_table_.find(page_id);
    if (it == page_table_.end()) {
        return false;
    }

    size_t frame = it->second;

    // 检查 pin count
    if (pages_[frame].getPinCount() <= 0) {
        return false;
    }

    // 减少 pin count
    pages_[frame].decrementPinCount();

    // 设置脏页标记
    if (is_dirty) {
        pages_[frame].setDirty(true);
    }

    // 如果 pin count 为 0，可以被替换
    if (pages_[frame].getPinCount() == 0) {
        replacer_->unpin(frame);
    }

    return true;
}

bool BufferPoolManager::flushPage(page_id_t page_id) {
    std::lock_guard<std::mutex> lock(latch_);

    auto it = page_table_.find(page_id);
    if (it == page_table_.end()) {
        return false;
    }

    size_t frame = it->second;
    disk_manager_->writePage(page_id, pages_[frame].getData());
    pages_[frame].setDirty(false);

    return true;
}

void BufferPoolManager::flushAllPages() {
    std::lock_guard<std::mutex> lock(latch_);

    for (auto& [page_id, frame] : page_table_) {
        if (pages_[frame].isDirty()) {
            disk_manager_->writePage(page_id, pages_[frame].getData());
            pages_[frame].setDirty(false);
        }
    }
}

bool BufferPoolManager::deletePage(page_id_t page_id) {
    std::lock_guard<std::mutex> lock(latch_);

    auto it = page_table_.find(page_id);
    if (it == page_table_.end()) {
        return true;  // 页面不在缓冲池中
    }

    size_t frame = it->second;

    // 检查是否可以删除
    if (pages_[frame].getPinCount() > 0) {
        return false;  // 页面正在使用
    }

    // 从页面表中移除
    page_table_.erase(it);

    // 重置页面
    pages_[frame].reset();

    // 添加到空闲列表
    free_list_.push_back(frame);

    // 从磁盘释放页面
    disk_manager_->deallocatePage(page_id);

    return true;
}

size_t BufferPoolManager::getAvailableFrameCount() const {
    std::lock_guard<std::mutex> lock(latch_);
    return free_list_.size() + replacer_->size();
}

int BufferPoolManager::findFrame(page_id_t page_id) const {
    auto it = page_table_.find(page_id);
    if (it != page_table_.end()) {
        return static_cast<int>(it->second);
    }
    return -1;
}

int BufferPoolManager::getFreeFrame() {
    if (!free_list_.empty()) {
        int frame = free_list_.front();
        free_list_.pop_front();
        return frame;
    }
    return -1;
}

}  // namespace minidb
