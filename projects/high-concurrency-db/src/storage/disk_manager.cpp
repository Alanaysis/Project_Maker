#include "storage/disk_manager.h"
#include <filesystem>
#include <iostream>

namespace minidb {

DiskManager::DiskManager(const std::string& db_file)
    : db_file_(db_file), next_page_id_(0), is_open_(false) {
    openFile();
}

DiskManager::~DiskManager() {
    closeFile();
}

void DiskManager::openFile() {
    std::lock_guard<std::mutex> lock(latch_);

    // 检查文件是否存在
    bool file_exists = std::filesystem::exists(db_file_);

    // 打开文件
    db_io_.open(db_file_, std::ios::binary | std::ios::in | std::ios::out);

    if (!db_io_.is_open()) {
        // 文件不存在，创建新文件
        db_io_.clear();
        db_io_.open(db_file_, std::ios::binary | std::ios::in |
                               std::ios::out | std::ios::trunc);
    }

    if (!db_io_.is_open()) {
        MINIDB_ERROR("Failed to open database file: " + db_file_);
        return;
    }

    // 如果是已有文件，计算页面数量
    if (file_exists) {
        db_io_.seekg(0, std::ios::end);
        size_t file_size = db_io_.tellg();
        next_page_id_ = file_size / PAGE_SIZE;
    }

    is_open_ = true;
    MINIDB_LOG("DiskManager opened file: " + db_file_);
}

void DiskManager::closeFile() {
    std::lock_guard<std::mutex> lock(latch_);
    if (db_io_.is_open()) {
        db_io_.close();
    }
    is_open_ = false;
}

void DiskManager::readPage(page_id_t page_id, char* page_data) {
    std::lock_guard<std::mutex> lock(latch_);

    if (!is_open_) {
        MINIDB_ERROR("DiskManager: File not open");
        return;
    }

    // 计算文件偏移
    size_t offset = static_cast<size_t>(page_id) * PAGE_SIZE;

    // 检查偏移是否有效
    db_io_.seekg(0, std::ios::end);
    size_t file_size = db_io_.tellg();
    if (offset + PAGE_SIZE > file_size) {
        MINIDB_ERROR("DiskManager: Read beyond end of file");
        return;
    }

    // 读取页面
    db_io_.seekg(offset);
    db_io_.read(page_data, PAGE_SIZE);

    if (!db_io_.good()) {
        MINIDB_ERROR("DiskManager: Failed to read page " +
                     std::to_string(page_id));
    }
}

void DiskManager::writePage(page_id_t page_id, const char* page_data) {
    std::lock_guard<std::mutex> lock(latch_);

    if (!is_open_) {
        MINIDB_ERROR("DiskManager: File not open");
        return;
    }

    // 计算文件偏移
    size_t offset = static_cast<size_t>(page_id) * PAGE_SIZE;

    // 写入页面
    db_io_.seekp(offset);
    db_io_.write(page_data, PAGE_SIZE);

    if (!db_io_.good()) {
        MINIDB_ERROR("DiskManager: Failed to write page " +
                     std::to_string(page_id));
    }

    // 刷新到磁盘
    db_io_.flush();
}

page_id_t DiskManager::allocatePage() {
    std::lock_guard<std::mutex> lock(latch_);
    page_id_t new_page_id = next_page_id_.fetch_add(1);

    // 使用 page_id * PAGE_SIZE 计算正确的偏移量
    if (is_open_) {
        db_io_.seekp(static_cast<size_t>(new_page_id) * PAGE_SIZE);
        char empty_page[PAGE_SIZE] = {0};
        db_io_.write(empty_page, PAGE_SIZE);
        db_io_.flush();
    }

    MINIDB_LOG("DiskManager: Allocated page " + std::to_string(new_page_id));
    return new_page_id;
}

void DiskManager::deallocatePage(page_id_t page_id) {
    // 简化实现：不实际回收页面
    // 实际实现中应该维护一个空闲列表
    MINIDB_LOG("DiskManager: Deallocated page " + std::to_string(page_id));
}

size_t DiskManager::getFileSize() const {
    std::lock_guard<std::mutex> lock(latch_);
    if (!is_open_) return 0;

    // 保存当前位置
    auto current_pos = db_io_.tellg();

    // 获取文件大小
    const_cast<std::fstream&>(db_io_).seekg(0, std::ios::end);
    size_t size = const_cast<std::fstream&>(db_io_).tellg();

    // 恢复位置
    const_cast<std::fstream&>(db_io_).seekg(current_pos);

    return size;
}

size_t DiskManager::getPageCount() const {
    return next_page_id_;
}

void DiskManager::flush() {
    std::lock_guard<std::mutex> lock(latch_);
    if (is_open_) {
        db_io_.flush();
    }
}

bool DiskManager::exists() const {
    return std::filesystem::exists(db_file_);
}

}  // namespace minidb
