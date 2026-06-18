#pragma once

#include "core/common.h"
#include "core/config.h"
#include "storage/page.h"
#include "storage/disk_manager.h"
#include <list>
#include <unordered_map>
#include <mutex>
#include <condition_variable>

namespace minidb {

// LRU 替换器
class LRUReplacer {
public:
    explicit LRUReplacer(size_t num_pages);

    /**
     * @brief 选择一个 victim 页面进行替换
     * @param frame_id 输出参数，被选中的帧 ID
     * @return 是否成功找到 victim
     */
    bool victim(size_t* frame_id);

    /**
     * @brief 固定一个页面 (不可被替换)
     * @param frame_id 帧 ID
     */
    void pin(size_t frame_id);

    /**
     * @brief 取消固定一个页面 (可被替换)
     * @param frame_id 帧 ID
     */
    void unpin(size_t frame_id);

    /**
     * @brief 获取可替换的页面数量
     * @return 可替换页面数量
     */
    size_t size() const;

private:
    mutable std::mutex latch_;
    std::list<size_t> lru_list_;  // LRU 链表
    std::unordered_map<size_t, std::list<size_t>::iterator> lru_map_;  // 快速查找
    size_t num_pages_;
};

// 缓冲池管理器
class BufferPoolManager {
public:
    /**
     * @brief 构造函数
     * @param pool_size 缓冲池大小 (页面数量)
     * @param disk_manager 磁盘管理器
     */
    BufferPoolManager(size_t pool_size, DiskManager* disk_manager);

    /**
     * @brief 析构函数
     */
    ~BufferPoolManager();

    // 禁止拷贝
    BufferPoolManager(const BufferPoolManager&) = delete;
    BufferPoolManager& operator=(const BufferPoolManager&) = delete;

    /**
     * @brief 获取页面
     * @param page_id 页面 ID
     * @return 页面指针，如果无法获取返回 nullptr
     */
    Page* fetchPage(page_id_t page_id);

    /**
     * @brief 创建新页面
     * @param page_id 输出参数，新页面的 ID
     * @return 页面指针，如果无法创建返回 nullptr
     */
    Page* newPage(page_id_t* page_id);

    /**
     * @brief 取消固定页面
     * @param page_id 页面 ID
     * @param is_dirty 是否被修改
     * @return 是否成功
     */
    bool unpinPage(page_id_t page_id, bool is_dirty);

    /**
     * @brief 刷新页面到磁盘
     * @param page_id 页面 ID
     * @return 是否成功
     */
    bool flushPage(page_id_t page_id);

    /**
     * @brief 刷新所有页面到磁盘
     */
    void flushAllPages();

    /**
     * @brief 删除页面
     * @param page_id 页面 ID
     * @return 是否成功
     */
    bool deletePage(page_id_t page_id);

    /**
     * @brief 获取缓冲池大小
     * @return 缓冲池大小
     */
    size_t getPoolSize() const { return pool_size_; }

    /**
     * @brief 获取可用帧数量
     * @return 可用帧数量
     */
    size_t getAvailableFrameCount() const;

private:
    /**
     * @brief 查找页面在缓冲池中的位置
     * @param page_id 页面 ID
     * @return 帧索引，如果未找到返回 -1
     */
    int findFrame(page_id_t page_id) const;

    /**
     * @brief 获取一个空闲帧
     * @return 帧索引，如果没有空闲帧返回 -1
     */
    int getFreeFrame();

    size_t pool_size_;  // 缓冲池大小
    Page* pages_;       // 页面数组
    DiskManager* disk_manager_;  // 磁盘管理器

    // 页面表: page_id -> frame_index
    std::unordered_map<page_id_t, size_t> page_table_;

    // 空闲帧列表
    std::list<size_t> free_list_;

    // LRU 替换器
    std::unique_ptr<LRUReplacer> replacer_;

    // 互斥锁
    std::mutex latch_;
};

}  // namespace minidb
