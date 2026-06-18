#include "storage/table.h"
#include <iostream>
#include <cstring>

namespace minidb {

// ==================== Row 序列化 ====================

std::vector<char> Row::serialize(const TableDef& table_def) const {
    size_t row_size = table_def.getRowSize();
    std::vector<char> data(row_size, 0);

    size_t offset = 4;  // 跳过头部 (null bitmap + row size)

    for (size_t i = 0; i < values_.size() && i < table_def.columns.size(); ++i) {
        const auto& col = table_def.columns[i];
        const auto& val = values_[i];

        if (col.type == TypeId::INTEGER) {
            int32_t int_val = std::get<int32_t>(val);
            std::memcpy(data.data() + offset, &int_val, sizeof(int32_t));
            offset += sizeof(int32_t);
        } else if (col.type == TypeId::FLOAT) {
            float float_val = std::get<float>(val);
            std::memcpy(data.data() + offset, &float_val, sizeof(float));
            offset += sizeof(float);
        } else if (col.type == TypeId::VARCHAR) {
            const std::string& str_val = std::get<std::string>(val);
            uint16_t len = static_cast<uint16_t>(str_val.size());
            std::memcpy(data.data() + offset, &len, sizeof(uint16_t));
            offset += sizeof(uint16_t);
            std::memcpy(data.data() + offset, str_val.data(), len);
            offset += col.max_length;
        }
    }

    // 写入行大小
    uint32_t size = static_cast<uint32_t>(row_size);
    std::memcpy(data.data(), &size, sizeof(uint32_t));

    return data;
}

Row Row::deserialize(const char* data, const TableDef& table_def) {
    Row row;

    size_t offset = 4;  // 跳过头部

    for (const auto& col : table_def.columns) {
        if (col.type == TypeId::INTEGER) {
            int32_t int_val;
            std::memcpy(&int_val, data + offset, sizeof(int32_t));
            row.addValue(int_val);
            offset += sizeof(int32_t);
        } else if (col.type == TypeId::FLOAT) {
            float float_val;
            std::memcpy(&float_val, data + offset, sizeof(float));
            row.addValue(float_val);
            offset += sizeof(float);
        } else if (col.type == TypeId::VARCHAR) {
            uint16_t len;
            std::memcpy(&len, data + offset, sizeof(uint16_t));
            offset += sizeof(uint16_t);
            std::string str_val(data + offset, len);
            row.addValue(str_val);
            offset += col.max_length;
        }
    }

    return row;
}

// ==================== TableIterator ====================

TableIterator::TableIterator(BufferPoolManager* bpm, page_id_t first_page_id)
    : bpm_(bpm), current_page_id_(first_page_id),
      current_slot_(0), is_valid_(true) {}

bool TableIterator::hasNext() const {
    return is_valid_ && current_page_id_ != INVALID_PAGE_ID;
}

bool TableIterator::next(Row* row) {
    while (current_page_id_ != INVALID_PAGE_ID) {
        Page* page = bpm_->fetchPage(current_page_id_);
        if (!page) {
            is_valid_ = false;
            return false;
        }

        // 遍历页面中的记录
        while (current_slot_ < page->getSlotCount()) {
            const char* data;
            size_t size;
            if (page->getRecord(current_slot_, &data, &size)) {
                // TODO: 需要 TableDef 来反序列化
                // 简化实现：直接返回空行
                current_slot_++;
                bpm_->unpinPage(current_page_id_, false);
                return true;
            }
            current_slot_++;
        }

        // 移动到下一个页面
        // 简化实现：假设页面是连续的
        page_id_t next_page_id = current_page_id_ + 1;
        bpm_->unpinPage(current_page_id_, false);

        // 检查下一个页面是否存在
        Page* next_page = bpm_->fetchPage(next_page_id);
        if (next_page) {
            current_page_id_ = next_page_id;
            current_slot_ = 0;
            bpm_->unpinPage(next_page_id, false);
        } else {
            current_page_id_ = INVALID_PAGE_ID;
            is_valid_ = false;
        }
    }

    return false;
}

void TableIterator::reset() {
    // 简化实现
    is_valid_ = true;
}

// ==================== Table ====================

Table::Table(BufferPoolManager* bpm, const TableDef& table_def)
    : bpm_(bpm), table_def_(table_def),
      first_page_id_(INVALID_PAGE_ID), last_page_id_(INVALID_PAGE_ID),
      row_count_(0) {}

Table::~Table() = default;

Status Table::insertRow(const Row& row) {
    // 序列化行
    std::vector<char> row_data = row.serialize(table_def_);

    // 查找有空间的页面
    if (first_page_id_ == INVALID_PAGE_ID) {
        // 创建第一个数据页面
        page_id_t page_id;
        Page* page = bpm_->newPage(&page_id);
        if (!page) {
            return Status::bufferFull();
        }

        page->setPageType(PageType::DATA_PAGE);
        first_page_id_ = page_id;
        last_page_id_ = page_id;

        // 插入记录
        uint32_t slot_num;
        if (!page->insertRecord(row_data.data(), row_data.size(), &slot_num)) {
            bpm_->unpinPage(page_id, false);
            return Status::pageFull();
        }

        page->setDirty(true);
        bpm_->unpinPage(page_id, true);
        row_count_++;
        return Status::success();
    }

    // 尝试在最后一个页面插入
    Page* page = bpm_->fetchPage(last_page_id_);
    if (!page) {
        return Status::ioError("Failed to fetch page");
    }

    uint32_t slot_num;
    if (page->insertRecord(row_data.data(), row_data.size(), &slot_num)) {
        page->setDirty(true);
        bpm_->unpinPage(last_page_id_, true);
        row_count_++;
        return Status::success();
    }

    // 最后一个页面已满，创建新页面
    bpm_->unpinPage(last_page_id_, false);

    page_id_t new_page_id;
    Page* new_page = bpm_->newPage(&new_page_id);
    if (!new_page) {
        return Status::bufferFull();
    }

    new_page->setPageType(PageType::DATA_PAGE);

    if (new_page->insertRecord(row_data.data(), row_data.size(), &slot_num)) {
        new_page->setDirty(true);
        bpm_->unpinPage(new_page_id, true);
        last_page_id_ = new_page_id;
        row_count_++;
        return Status::success();
    }

    bpm_->unpinPage(new_page_id, false);
    return Status::pageFull();
}

Status Table::deleteRow(const RowId& row_id) {
    Page* page = bpm_->fetchPage(row_id.page_id);
    if (!page) {
        return Status::ioError("Failed to fetch page");
    }

    if (page->deleteRecord(row_id.slot_num)) {
        page->setDirty(true);
        bpm_->unpinPage(row_id.page_id, true);
        row_count_--;
        return Status::success();
    }

    bpm_->unpinPage(row_id.page_id, false);
    return Status::keyNotFound("Row not found");
}

Status Table::updateRow(const RowId& row_id, const Row& row) {
    // 简化实现：删除旧行，插入新行
    Status status = deleteRow(row_id);
    if (!status.ok()) return status;

    return insertRow(row);
}

Status Table::getRow(const RowId& row_id, Row* row) {
    Page* page = bpm_->fetchPage(row_id.page_id);
    if (!page) {
        return Status::ioError("Failed to fetch page");
    }

    const char* data;
    size_t size;
    if (page->getRecord(row_id.slot_num, &data, &size)) {
        *row = Row::deserialize(data, table_def_);
        bpm_->unpinPage(row_id.page_id, false);
        return Status::success();
    }

    bpm_->unpinPage(row_id.page_id, false);
    return Status::keyNotFound("Row not found");
}

std::unique_ptr<TableIterator> Table::createIterator() {
    return std::make_unique<TableIterator>(bpm_, first_page_id_);
}

std::unique_ptr<Table> Table::create(BufferPoolManager* bpm,
                                      const TableDef& table_def) {
    return std::make_unique<Table>(bpm, table_def);
}

std::unique_ptr<Table> Table::load(BufferPoolManager* bpm,
                                    const TableDef& table_def,
                                    page_id_t first_page_id) {
    auto table = std::make_unique<Table>(bpm, table_def);
    table->first_page_id_ = first_page_id;
    return table;
}

// ==================== Catalog ====================

Status Catalog::createTable(const TableDef& table_def) {
    if (tableExists(table_def.name)) {
        return Status::tableAlreadyExists(table_def.name);
    }

    auto table = Table::create(bpm_, table_def);
    if (!table) {
        return Status::unknown("Failed to create table");
    }

    tables_[table_def.name] = std::move(table);
    return Status::success();
}

Status Catalog::dropTable(const std::string& table_name) {
    auto it = tables_.find(table_name);
    if (it == tables_.end()) {
        return Status::tableNotFound(table_name);
    }

    tables_.erase(it);
    return Status::success();
}

Table* Catalog::getTable(const std::string& table_name) {
    auto it = tables_.find(table_name);
    if (it == tables_.end()) {
        return nullptr;
    }
    return it->second.get();
}

bool Catalog::tableExists(const std::string& table_name) const {
    return tables_.find(table_name) != tables_.end();
}

std::vector<std::string> Catalog::getAllTableNames() const {
    std::vector<std::string> names;
    for (const auto& [name, table] : tables_) {
        names.push_back(name);
    }
    return names;
}

}  // namespace minidb
