#pragma once

#include "core/common.h"
#include "core/config.h"
#include "core/status.h"
#include <fstream>
#include <string>
#include <mutex>

namespace minidb {

// 磁盘管理器
// 负责数据库文件的读写操作
class DiskManager {
public:
    /**
     * @brief 构造函数
     * @param db_file 数据库文件路径
     */
    explicit DiskManager(const std::string& db_file);

    /**
     * @brief 析构函数
     */
    ~DiskManager();

    // 禁止拷贝
    DiskManager(const DiskManager&) = delete;
    DiskManager& operator=(const DiskManager&) = delete;

    /**
     * @brief 从磁盘读取页面
     * @param page_id 页面 ID
     * @param page_data 页面数据缓冲区 (必须至少 PAGE_SIZE 字节)
     */
    void readPage(page_id_t page_id, char* page_data);

    /**
     * @brief 写入页面到磁盘
     * @param page_id 页面 ID
     * @param page_data 页面数据
     */
    void writePage(page_id_t page_id, const char* page_data);

    /**
     * @brief 分配新页面
     * @return 新页面的 ID
     */
    page_id_t allocatePage();

    /**
     * @brief 释放页面
     * @param page_id 要释放的页面 ID
     */
    void deallocatePage(page_id_t page_id);

    /**
     * @brief 获取数据库文件大小
     * @return 文件大小 (字节)
     */
    size_t getFileSize() const;

    /**
     * @brief 获取页面数量
     * @return 页面数量
     */
    size_t getPageCount() const;

    /**
     * @brief 刷新所有数据到磁盘
     */
    void flush();

    /**
     * @brief 检查数据库文件是否存在
     * @return 是否存在
     */
    bool exists() const;

    /**
     * @brief 获取数据库文件路径
     * @return 文件路径
     */
    const std::string& getFilePath() const { return db_file_; }

private:
    /**
     * @brief 打开数据库文件
     */
    void openFile();

    /**
     * @brief 关闭数据库文件
     */
    void closeFile();

    std::string db_file_;           // 数据库文件路径
    std::fstream db_io_;            // 文件流
    std::atomic<page_id_t> next_page_id_;  // 下一个可用页面 ID
    std::mutex latch_;              // 互斥锁
    bool is_open_;                  // 文件是否已打开
};

}  // namespace minidb
