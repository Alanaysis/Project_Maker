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
                   std::unique_ptr<AbstractExecutor> child,
                   const TableDef& table_def)
        : AbstractExecutor(ctx), predicate_(predicate), child_(std::move(child)),
          table_def_(table_def) {}

    void init() override {
        child_->init();
    }

    bool next(Row* row) override {
        while (child_->next(row)) {
            if (evaluatePredicate(predicate_, *row)) {
                return true;
            }
        }
        return false;
    }

private:
    // 根据列名查找列索引，未找到返回 -1
    int findColumnIndex(const std::string& col_name) const {
        for (size_t i = 0; i < table_def_.columns.size(); ++i) {
            if (table_def_.columns[i].name == col_name) {
                return static_cast<int>(i);
            }
        }
        return -1;
    }

    // 求值表达式，返回 Value
    Value evaluateExpression(const Expression* expr, const Row& row) const {
        switch (expr->type()) {
            case ExpressionType::LITERAL_INT:
                return static_cast<const LiteralInt*>(expr)->getValue();
            case ExpressionType::LITERAL_FLOAT:
                return static_cast<const LiteralFloat*>(expr)->getValue();
            case ExpressionType::LITERAL_STRING:
                return static_cast<const LiteralString*>(expr)->getValue();
            case ExpressionType::COLUMN_REF: {
                const auto* col_ref = static_cast<const ColumnRef*>(expr);
                int idx = findColumnIndex(col_ref->getColumnName());
                if (idx >= 0 && static_cast<size_t>(idx) < row.size()) {
                    return row.getValue(static_cast<size_t>(idx));
                }
                // 列未找到，返回默认整数 0
                return static_cast<int32_t>(0);
            }
            default:
                return static_cast<int32_t>(0);
        }
    }

    // 比较两个 Value
    static int compareValues(const Value& lhs, const Value& rhs) {
        // 两个值类型相同时直接比较
        if (lhs.index() == rhs.index()) {
            if (std::holds_alternative<int32_t>(lhs)) {
                int32_t a = std::get<int32_t>(lhs), b = std::get<int32_t>(rhs);
                return (a < b) ? -1 : (a > b) ? 1 : 0;
            }
            if (std::holds_alternative<float>(lhs)) {
                float a = std::get<float>(lhs), b = std::get<float>(rhs);
                return (a < b) ? -1 : (a > b) ? 1 : 0;
            }
            if (std::holds_alternative<std::string>(lhs)) {
                return std::get<std::string>(lhs).compare(std::get<std::string>(rhs));
            }
        }
        // int32_t 和 float 之间可以互相比较
        if (std::holds_alternative<int32_t>(lhs) && std::holds_alternative<float>(rhs)) {
            float a = static_cast<float>(std::get<int32_t>(lhs));
            float b = std::get<float>(rhs);
            return (a < b) ? -1 : (a > b) ? 1 : 0;
        }
        if (std::holds_alternative<float>(lhs) && std::holds_alternative<int32_t>(rhs)) {
            float a = std::get<float>(lhs);
            float b = static_cast<float>(std::get<int32_t>(rhs));
            return (a < b) ? -1 : (a > b) ? 1 : 0;
        }
        // 类型不兼容，按索引排序
        return (lhs.index() < rhs.index()) ? -1 : 1;
    }

    // 求值谓词表达式（比较 / 逻辑），返回 bool
    bool evaluatePredicate(const Expression* expr, const Row& row) const {
        if (!expr) return true;

        switch (expr->type()) {
            case ExpressionType::COMPARISON: {
                const auto* cmp = static_cast<const ComparisonExpression*>(expr);
                Value lhs = evaluateExpression(cmp->getLeft(), row);
                Value rhs = evaluateExpression(cmp->getRight(), row);
                int c = compareValues(lhs, rhs);
                switch (cmp->getOp()) {
                    case ComparisonOp::EQUAL:         return c == 0;
                    case ComparisonOp::NOT_EQUAL:      return c != 0;
                    case ComparisonOp::LESS:           return c < 0;
                    case ComparisonOp::GREATER:        return c > 0;
                    case ComparisonOp::LESS_EQUAL:     return c <= 0;
                    case ComparisonOp::GREATER_EQUAL:  return c >= 0;
                }
                return false;
            }
            case ExpressionType::BINARY_OP: {
                const auto* logic = static_cast<const LogicalExpression*>(expr);
                switch (logic->getOp()) {
                    case LogicalOp::AND:
                        return evaluatePredicate(logic->getLeft(), row)
                            && evaluatePredicate(logic->getRight(), row);
                    case LogicalOp::OR:
                        return evaluatePredicate(logic->getLeft(), row)
                            || evaluatePredicate(logic->getRight(), row);
                    case LogicalOp::NOT:
                        return !evaluatePredicate(logic->getLeft(), row);
                }
                return false;
            }
            default:
                return true;
        }
    }

    const Expression* predicate_;
    std::unique_ptr<AbstractExecutor> child_;
    TableDef table_def_;
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
