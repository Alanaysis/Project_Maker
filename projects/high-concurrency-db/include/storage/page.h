#pragma once

#include "core/common.h"
#include "core/config.h"
#include <cstring>

namespace minidb {

// 页面类型
enum class PageType {
    INVALID = 0,
    DATA_PAGE,          // 数据页
    INDEX_PAGE,         // 索引页（内部节点）
    LEAF_PAGE,          // 叶子页
    TABLE_PAGE,         // 表元数据页
};

// 页面头
struct PageHeader {
    page_id_t page_id;      // 页面 ID
    uint32_t lsn;           // 日志序列号
    PageType page_type;     // 页面类型
    uint16_t slot_count;    // 槽位数量
    uint16_t free_space_offset;  // 空闲空间偏移
    uint32_t free_space_size;    // 空闲空间大小

    PageHeader()
        : page_id(INVALID_PAGE_ID),
          lsn(0),
          page_type(PageType::INVALID),
          slot_count(0),
          free_space_offset(sizeof(PageHeader)),
          free_space_size(PAGE_SIZE - sizeof(PageHeader)) {}
};

// 槽位
struct Slot {
    uint16_t offset;  // 数据偏移
    uint16_t size;    // 数据大小
    bool is_deleted;  // 是否已删除

    Slot() : offset(0), size(0), is_deleted(false) {}
    Slot(uint16_t off, uint16_t sz)
        : offset(off), size(sz), is_deleted(false) {}
};

// 页面类
class Page {
public:
    Page() : is_dirty_(false), pin_count_(0) {
        resetMemory();
    }

    ~Page() = default;

    // 禁止拷贝
    Page(const Page&) = delete;
    Page& operator=(const Page&) = delete;

    // 获取页面数据
    char* getData() { return data_; }
    const char* getData() const { return data_; }

    // 获取页面头
    PageHeader* getHeader() {
        return reinterpret_cast<PageHeader*>(data_);
    }

    const PageHeader* getHeader() const {
        return reinterpret_cast<const PageHeader*>(data_);
    }

    // 获取页面 ID
    page_id_t getPageId() const {
        return getHeader()->page_id;
    }

    // 设置页面 ID
    void setPageId(page_id_t page_id) {
        getHeader()->page_id = page_id;
    }

    // 获取页面类型
    PageType getPageType() const {
        return getHeader()->page_type;
    }

    // 设置页面类型
    void setPageType(PageType type) {
        getHeader()->page_type = type;
    }

    // 脏页标记
    bool isDirty() const { return is_dirty_; }
    void setDirty(bool dirty) { is_dirty_ = dirty; }

    // 引用计数
    int getPinCount() const { return pin_count_; }
    void incrementPinCount() { ++pin_count_; }
    void decrementPinCount() {
        if (pin_count_ > 0) --pin_count_;
    }

    // 重置页面
    void reset() {
        resetMemory();
        is_dirty_ = false;
        pin_count_ = 0;
    }

    // 写入数据到页面
    bool insertRecord(const char* record_data, size_t record_size,
                      uint32_t* slot_num) {
        PageHeader* header = getHeader();
        size_t needed = record_size;

        // 检查是否有足够空间
        if (header->free_space_size < needed + sizeof(Slot)) {
            return false;
        }

        // 写入数据
        uint16_t offset = header->free_space_offset;
        std::memcpy(data_ + offset, record_data, record_size);

        // 更新槽位
        uint32_t new_slot = header->slot_count;
        Slot* slots = getSlots();
        slots[new_slot] = Slot(offset, record_size);

        // 更新头部
        header->slot_count++;
        header->free_space_offset += record_size;
        header->free_space_size -= (record_size + sizeof(Slot));

        if (slot_num) *slot_num = new_slot;
        setDirty(true);
        return true;
    }

    // 读取记录
    bool getRecord(uint32_t slot_num, const char** data, size_t* size) const {
        const PageHeader* header = getHeader();
        if (slot_num >= header->slot_count) {
            return false;
        }

        const Slot* slots = getSlots();
        const Slot& slot = slots[slot_num];
        if (slot.is_deleted) {
            return false;
        }

        *data = data_ + slot.offset;
        *size = slot.size;
        return true;
    }

    // 删除记录
    bool deleteRecord(uint32_t slot_num) {
        PageHeader* header = getHeader();
        if (slot_num >= header->slot_count) {
            return false;
        }

        Slot* slots = getSlots();
        if (slots[slot_num].is_deleted) {
            return false;
        }

        slots[slot_num].is_deleted = true;
        setDirty(true);
        return true;
    }

    // 获取槽数量
    uint32_t getSlotCount() const {
        return getHeader()->slot_count;
    }

private:
    // 重置内存
    void resetMemory() {
        std::memset(data_, 0, PAGE_SIZE);
    }

    // 获取槽位数组
    Slot* getSlots() {
        return reinterpret_cast<Slot*>(data_ + PAGE_SIZE - sizeof(Slot) * getHeader()->slot_count);
    }

    const Slot* getSlots() const {
        return reinterpret_cast<const Slot*>(data_ + PAGE_SIZE - sizeof(Slot) * getHeader()->slot_count);
    }

    char data_[PAGE_SIZE];  // 页面数据
    bool is_dirty_;         // 脏页标记
    int pin_count_;         // 引用计数
};

}  // namespace minidb
