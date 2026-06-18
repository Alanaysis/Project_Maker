#pragma once

#include "core/common.h"
#include "core/status.h"
#include "sql/ast.h"
#include "storage/table.h"
#include "storage/buffer_pool.h"
#include "concurrency/lock_manager.h"
#include "concurrency/transaction.h"
#include <memory>
#include <vector>
#include <functional>

namespace minidb {

// 执行器上下文
class ExecutorContext {
public:
    ExecutorContext(BufferPoolManager* bpm, Catalog* catalog,
                   LockManager* lock_mgr, Transaction* txn)
        : bpm_(bpm), catalog_(catalog), lock_mgr_(lock_mgr), txn_(txn) {}

    BufferPoolManager* getBufferPoolManager() { return bpm_; }
    Catalog* getCatalog() { return catalog_; }
    LockManager* getLockManager() { return lock_mgr_; }
    Transaction* getTransaction() { return txn_; }

private:
    BufferPoolManager* bpm_;
    Catalog* catalog_;
    LockManager* lock_mgr_;
    Transaction* txn_;
};

// 执行结果
struct ExecutionResult {
    Status status;
    std::vector<Row> rows;
    size_t rows_affected;

    ExecutionResult() : rows_affected(0) {}
    ExecutionResult(Status s) : status(s), rows_affected(0) {}
};

/**
 * @brief 执行器基类 (Volcano 模型)
 *
 * 每个算子实现 next() 接口，拉取式执行
 */
class AbstractExecutor {
public:
    explicit AbstractExecutor(ExecutorContext* ctx) : ctx_(ctx) {}
    virtual ~AbstractExecutor() = default;

    /**
     * @brief 初始化执行器
     */
    virtual void init() = 0;

    /**
     * @brief 获取下一行
     * @param row 输出行
     * @return 是否有更多行
     */
    virtual bool next(Row* row) = 0;

protected:
    ExecutorContext* ctx_;
};

/**
 * @brief 顺序扫描执行器
 *
 * 全表扫描，逐行返回
 */
class SeqScanExecutor : public AbstractExecutor {
public:
    SeqScanExecutor(ExecutorContext* ctx, Table* table)
        : AbstractExecutor(ctx), table_(table), iterator_(nullptr) {}

    void init() override {
        iterator_ = table_->createIterator();
    }

    bool next(Row* row) override {
        if (!iterator_ || !iterator_->hasNext()) {
            return false;
        }
        return iterator_->next(row);
    }

private:
    Table* table_;
    std::unique_ptr<TableIterator> iterator_;
};

/**
 * @brief 过滤执行器
 *
 * 根据条件过滤行
 */
class FilterExecutor : public AbstractExecutor {
public:
    FilterExecutor(ExecutorContext* ctx, const Expression* predicate,
                   std::unique_ptr<AbstractExecutor> child)
        : AbstractExecutor(ctx), predicate_(predicate), child_(std::move(child)) {}

    void init() override {
        child_->init();
    }

    bool next(Row* row) override {
        while (child_->next(row)) {
            if (evaluatePredicate(*row)) {
                return true;
            }
        }
        return false;
    }

private:
    bool evaluatePredicate(const Row& row) {
        // 简化实现：只支持简单的比较
        // TODO: 完整的表达式求值
        return true;
    }

    const Expression* predicate_;
    std::unique_ptr<AbstractExecutor> child_;
};

/**
 * @brief 投影执行器
 *
 * 选择特定的列
 */
class ProjectionExecutor : public AbstractExecutor {
public:
    ProjectionExecutor(ExecutorContext* ctx,
                       const std::vector<std::string>& columns,
                       const TableDef& table_def,
                       std::unique_ptr<AbstractExecutor> child)
        : AbstractExecutor(ctx), columns_(columns), table_def_(table_def),
          child_(std::move(child)) {}

    void init() override {
        child_->init();
        // 计算列索引
        column_indices_.clear();
        for (const auto& col_name : columns_) {
            for (size_t i = 0; i < table_def_.columns.size(); ++i) {
                if (table_def_.columns[i].name == col_name) {
                    column_indices_.push_back(i);
                    break;
                }
            }
        }
    }

    bool next(Row* row) override {
        Row full_row;
        if (!child_->next(&full_row)) {
            return false;
        }

        // 投影列
        row->clear();
        for (size_t idx : column_indices_) {
            if (idx < full_row.size()) {
                row->addValue(full_row.getValue(idx));
            }
        }
        return true;
    }

private:
    std::vector<std::string> columns_;
    std::vector<size_t> column_indices_;
    TableDef table_def_;
    std::unique_ptr<AbstractExecutor> child_;
};

/**
 * @brief 插入执行器
 */
class InsertExecutor : public AbstractExecutor {
public:
    InsertExecutor(ExecutorContext* ctx, Table* table,
                   const std::vector<Row>& rows)
        : AbstractExecutor(ctx), table_(table), rows_(rows), done_(false) {}

    void init() override {
        done_ = false;
    }

    bool next(Row* row) override {
        if (done_) return false;

        for (const auto& r : rows_) {
            Status status = table_->insertRow(r);
            if (!status.ok()) {
                // 设置错误信息
                return false;
            }
        }
        done_ = true;
        return false;
    }

private:
    Table* table_;
    std::vector<Row> rows_;
    bool done_;
};

/**
 * @brief 更新执行器
 */
class UpdateExecutor : public AbstractExecutor {
public:
    UpdateExecutor(ExecutorContext* ctx, Table* table,
                   const Expression* predicate,
                   const std::vector<std::pair<std::string, Value>>& updates)
        : AbstractExecutor(ctx), table_(table), predicate_(predicate),
          updates_(updates), rows_affected_(0) {}

    void init() override {
        rows_affected_ = 0;
        iterator_ = table_->createIterator();
    }

    bool next(Row* row) override {
        // 遍历所有行，找到匹配的并更新
        while (iterator_ && iterator_->hasNext()) {
            Row current_row;
            RowId row_id;
            if (iterator_->next(&current_row)) {
                // 检查是否匹配条件
                // TODO: 实现条件检查
                // 更新行
                // TODO: 实现行更新
                rows_affected_++;
            }
        }
        return false;
    }

private:
    Table* table_;
    const Expression* predicate_;
    std::vector<std::pair<std::string, Value>> updates_;
    std::unique_ptr<TableIterator> iterator_;
    size_t rows_affected_;
};

/**
 * @brief 删除执行器
 */
class DeleteExecutor : public AbstractExecutor {
public:
    DeleteExecutor(ExecutorContext* ctx, Table* table,
                   const Expression* predicate)
        : AbstractExecutor(ctx), table_(table), predicate_(predicate),
          rows_affected_(0) {}

    void init() override {
        rows_affected_ = 0;
        iterator_ = table_->createIterator();
    }

    bool next(Row* row) override {
        // 遍历所有行，找到匹配的并删除
        while (iterator_ && iterator_->hasNext()) {
            Row current_row;
            if (iterator_->next(&current_row)) {
                // 检查是否匹配条件
                // TODO: 实现条件检查
                // 删除行
                // TODO: 实现行删除
                rows_affected_++;
            }
        }
        return false;
    }

private:
    Table* table_;
    const Expression* predicate_;
    std::unique_ptr<TableIterator> iterator_;
    size_t rows_affected_;
};

/**
 * @brief 查询执行引擎
 *
 * 负责执行 SQL 语句
 */
class ExecutionEngine {
public:
    ExecutionEngine(BufferPoolManager* bpm, Catalog* catalog,
                    LockManager* lock_mgr)
        : bpm_(bpm), catalog_(catalog), lock_mgr_(lock_mgr) {}

    /**
     * @brief 执行 SQL 语句
     * @param statement SQL 语句 AST
     * @return 执行结果
     */
    ExecutionResult execute(Statement* statement);

    /**
     * @brief 执行 CREATE TABLE 语句
     */
    ExecutionResult executeCreateTable(const CreateTableStatement* stmt);

    /**
     * @brief 执行 INSERT 语句
     */
    ExecutionResult executeInsert(const InsertStatement* stmt);

    /**
     * @brief 执行 SELECT 语句
     */
    ExecutionResult executeSelect(const SelectStatement* stmt);

    /**
     * @brief 执行 UPDATE 语句
     */
    ExecutionResult executeUpdate(const UpdateStatement* stmt);

    /**
     * @brief 执行 DELETE 语句
     */
    ExecutionResult executeDelete(const DeleteStatement* stmt);

    /**
     * @brief 执行 DROP TABLE 语句
     */
    ExecutionResult executeDropTable(const DropTableStatement* stmt);

private:
    BufferPoolManager* bpm_;
    Catalog* catalog_;
    LockManager* lock_mgr_;
};

}  // namespace minidb
