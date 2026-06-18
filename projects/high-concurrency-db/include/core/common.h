#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <atomic>
#include <cassert>
#include <cstring>
#include <iostream>
#include <sstream>
#include <algorithm>
#include <functional>
#include <unordered_map>
#include <map>
#include <set>
#include <list>
#include <queue>
#include <optional>
#include <variant>

namespace minidb {

// 页面大小常量
constexpr size_t PAGE_SIZE = 4096;  // 4KB
constexpr size_t INVALID_PAGE_ID = -1;

// 页面 ID 类型
using page_id_t = int32_t;

// 事务 ID 类型
using transaction_id_t = int64_t;

// 行 ID
struct RowId {
    page_id_t page_id;
    uint32_t slot_num;

    RowId() : page_id(INVALID_PAGE_ID), slot_num(0) {}
    RowId(page_id_t pid, uint32_t slot) : page_id(pid), slot_num(slot) {}

    bool operator==(const RowId& other) const {
        return page_id == other.page_id && slot_num == other.slot_num;
    }

    bool operator!=(const RowId& other) const {
        return !(*this == other);
    }

    bool isValid() const {
        return page_id != INVALID_PAGE_ID;
    }
};

// 值类型
enum class TypeId {
    INVALID = 0,
    INTEGER,
    FLOAT,
    VARCHAR
};

// 值类型大小
constexpr size_t getTypeSize(TypeId type) {
    switch (type) {
        case TypeId::INTEGER: return 4;
        case TypeId::FLOAT: return 4;
        default: return 0;  // VARCHAR 是变长的
    }
}

// 列定义
struct ColumnDef {
    std::string name;
    TypeId type;
    size_t max_length;  // 用于 VARCHAR
    bool is_primary_key;
    bool is_nullable;

    ColumnDef() : type(TypeId::INVALID), max_length(0),
                  is_primary_key(false), is_nullable(true) {}

    ColumnDef(const std::string& n, TypeId t, size_t len = 0,
              bool pk = false, bool nullable = true)
        : name(n), type(t), max_length(len),
          is_primary_key(pk), is_nullable(nullable) {}

    size_t getSize() const {
        if (type == TypeId::VARCHAR) {
            return max_length + 2;  // 2 bytes for length
        }
        return getTypeSize(type);
    }
};

// 表定义
struct TableDef {
    std::string name;
    std::vector<ColumnDef> columns;

    size_t getRowSize() const {
        size_t size = 0;
        for (const auto& col : columns) {
            size += col.getSize();
        }
        return size + 4;  // 4 bytes for header (null bitmap + row size)
    }
};

// 值类型
using Value = std::variant<int32_t, float, std::string>;

// 行数据
class Row {
public:
    Row() = default;
    Row(const std::vector<Value>& values) : values_(values) {}

    void addValue(const Value& value) {
        values_.push_back(value);
    }

    const Value& getValue(size_t index) const {
        return values_.at(index);
    }

    Value& getValue(size_t index) {
        return values_.at(index);
    }

    size_t size() const {
        return values_.size();
    }

    const std::vector<Value>& getValues() const {
        return values_;
    }

    void clear() {
        values_.clear();
    }

    // 序列化为字节流
    std::vector<char> serialize(const TableDef& table_def) const;

    // 从字节流反序列化
    static Row deserialize(const char* data, const TableDef& table_def);

private:
    std::vector<Value> values_;
};

// 输出操作符
inline std::ostream& operator<<(std::ostream& os, const Value& value) {
    std::visit([&os](const auto& v) {
        os << v;
    }, value);
    return os;
}

inline std::ostream& operator<<(std::ostream& os, const Row& row) {
    const auto& values = row.getValues();
    for (size_t i = 0; i < values.size(); ++i) {
        if (i > 0) os << " | ";
        os << values[i];
    }
    return os;
}

}  // namespace minidb
