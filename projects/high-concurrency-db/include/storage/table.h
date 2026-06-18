#pragma once

#include "core/common.h"
#include "core/status.h"
#include "storage/page.h"
#include "storage/buffer_pool.h"
#include "storage/bplus_tree.h"
#include <string>
#include <vector>
#include <memory>

namespace minidb {

// 表迭代器
class TableIterator {
public:
    TableIterator(BufferPoolManager* bpm, page_id_t first_page_id);
    ~TableIterator() = default;

    // 检查是否有效
    bool hasNext() const;

    // 获取下一行
    bool next(Row* row);

    // 重置迭代器
    void reset();

private:
    BufferPoolManager* bpm_;
    page_id_t current_page_id_;
    uint32_t current_slot_;
    bool is_valid_;
};

// 表类
class Table {
public:
    /**
     * @brief 构造函数
     * @param bpm 缓冲池管理器
     * @param table_def 表定义
     */
    Table(BufferPoolManager* bpm, const TableDef& table_def);

    /**
     * @brief 析构函数
     */
    ~Table();

    /**
     * @brief 插入一行
     * @param row 行数据
     * @return 状态
     */
    Status insertRow(const Row& row);

    /**
     * @brief 删除一行
     * @param row_id 行 ID
     * @return 状态
     */
    Status deleteRow(const RowId& row_id);

    /**
     * @brief 更新一行
     * @param row_id 行 ID
     * @param row 新行数据
     * @return 状态
     */
    Status updateRow(const RowId& row_id, const Row& row);

    /**
     * @brief 读取一行
     * @param row_id 行 ID
     * @param row 输出行数据
     * @return 状态
     */
    Status getRow(const RowId& row_id, Row* row);

    /**
     * @brief 获取表定义
     * @return 表定义
     */
    const TableDef& getTableDef() const { return table_def_; }

    /**
     * @brief 获取表名
     * @return 表名
     */
    const std::string& getName() const { return table_def_.name; }

    /**
     * @brief 获取第一个数据页面 ID
     * @return 页面 ID
     */
    page_id_t getFirstPageId() const { return first_page_id_; }

    /**
     * @brief 创建迭代器
     * @return 迭代器
     */
    std::unique_ptr<TableIterator> createIterator();

    /**
     * @brief 获取行数
     * @return 行数
     */
    size_t getRowCount() const { return row_count_; }

    /**
     * @brief 创建新表
     * @param bpm 缓冲池管理器
     * @param table_def 表定义
     * @return 表指针
     */
    static std::unique_ptr<Table> create(BufferPoolManager* bpm,
                                         const TableDef& table_def);

    /**
     * @brief 加载已有表
     * @param bpm 缓冲池管理器
     * @param table_def 表定义
     * @param first_page_id 第一个数据页面 ID
     * @return 表指针
     */
    static std::unique_ptr<Table> load(BufferPoolManager* bpm,
                                       const TableDef& table_def,
                                       page_id_t first_page_id);

private:
    BufferPoolManager* bpm_;
    TableDef table_def_;
    page_id_t first_page_id_;
    page_id_t last_page_id_;
    size_t row_count_;
};

// 目录 (管理所有表)
class Catalog {
public:
    Catalog(BufferPoolManager* bpm) : bpm_(bpm) {}

    /**
     * @brief 创建表
     * @param table_def 表定义
     * @return 状态
     */
    Status createTable(const TableDef& table_def);

    /**
     * @brief 删除表
     * @param table_name 表名
     * @return 状态
     */
    Status dropTable(const std::string& table_name);

    /**
     * @brief 获取表
     * @param table_name 表名
     * @return 表指针，如果不存在返回 nullptr
     */
    Table* getTable(const std::string& table_name);

    /**
     * @brief 检查表是否存在
     * @param table_name 表名
     * @return 是否存在
     */
    bool tableExists(const std::string& table_name) const;

    /**
     * @brief 获取所有表名
     * @return 表名列表
     */
    std::vector<std::string> getAllTableNames() const;

private:
    BufferPoolManager* bpm_;
    std::unordered_map<std::string, std::unique_ptr<Table>> tables_;
};

}  // namespace minidb
