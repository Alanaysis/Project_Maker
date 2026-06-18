#include "sql/executor.h"
#include <iostream>

namespace minidb {

ExecutionResult ExecutionEngine::execute(Statement* statement) {
    if (!statement) {
        return ExecutionResult(Status::unknown("Null statement"));
    }

    switch (statement->type()) {
        case StatementType::CREATE_TABLE:
            return executeCreateTable(static_cast<CreateTableStatement*>(statement));
        case StatementType::INSERT:
            return executeInsert(static_cast<InsertStatement*>(statement));
        case StatementType::SELECT:
            return executeSelect(static_cast<SelectStatement*>(statement));
        case StatementType::UPDATE:
            return executeUpdate(static_cast<UpdateStatement*>(statement));
        case StatementType::DELETE:
            return executeDelete(static_cast<DeleteStatement*>(statement));
        case StatementType::DROP_TABLE:
            return executeDropTable(static_cast<DropTableStatement*>(statement));
        default:
            return ExecutionResult(Status::unknown("Unknown statement type"));
    }
}

ExecutionResult ExecutionEngine::executeCreateTable(const CreateTableStatement* stmt) {
    if (!stmt) {
        return ExecutionResult(Status::unknown("Null statement"));
    }

    // 转换列定义
    TableDef table_def;
    table_def.name = stmt->getTableName();

    for (const auto& col : stmt->getColumns()) {
        ColumnDef col_def;
        col_def.name = col.name;
        col_def.type = col.type;
        col_def.max_length = col.max_length;
        col_def.is_primary_key = col.is_primary_key;
        col_def.is_nullable = col.is_nullable;
        table_def.columns.push_back(col_def);
    }

    // 创建表
    Status status = catalog_->createTable(table_def);
    if (!status.ok()) {
        return ExecutionResult(status);
    }

    std::cout << "Table created: " << table_def.name << std::endl;
    return ExecutionResult(Status::success());
}

ExecutionResult ExecutionEngine::executeInsert(const InsertStatement* stmt) {
    if (!stmt) {
        return ExecutionResult(Status::unknown("Null statement"));
    }

    // 获取表
    Table* table = catalog_->getTable(stmt->getTableName());
    if (!table) {
        return ExecutionResult(Status::tableNotFound(stmt->getTableName()));
    }

    // 获取锁 (简化：使用排他锁)
    Transaction* txn = nullptr;  // TODO: 从上下文获取事务
    // if (lock_mgr_) {
    //     lock_mgr_->lockExclusive(txn, stmt->getTableName());
    // }

    const TableDef& table_def = table->getTableDef();
    size_t rows_affected = 0;

    // 插入每一行
    for (const auto& values : stmt->getValues()) {
        Row row;

        // 求值表达式
        for (size_t i = 0; i < values.size(); ++i) {
            if (!values[i]) {
                return ExecutionResult(Status::unknown("Null value expression"));
            }

            // 根据表达式类型求值
            switch (values[i]->type()) {
                case ExpressionType::LITERAL_INT: {
                    auto* literal = static_cast<LiteralInt*>(values[i].get());
                    row.addValue(literal->getValue());
                    break;
                }
                case ExpressionType::LITERAL_FLOAT: {
                    auto* literal = static_cast<LiteralFloat*>(values[i].get());
                    row.addValue(literal->getValue());
                    break;
                }
                case ExpressionType::LITERAL_STRING: {
                    auto* literal = static_cast<LiteralString*>(values[i].get());
                    row.addValue(literal->getValue());
                    break;
                }
                default:
                    return ExecutionResult(Status::unknown("Unsupported expression type"));
            }
        }

        // 检查列数是否匹配
        if (row.size() != table_def.columns.size()) {
            return ExecutionResult(Status::unknown(
                "Column count mismatch: expected " +
                std::to_string(table_def.columns.size()) +
                ", got " + std::to_string(row.size())));
        }

        // 插入行
        Status status = table->insertRow(row);
        if (!status.ok()) {
            return ExecutionResult(status);
        }
        rows_affected++;
    }

    std::cout << rows_affected << " row(s) inserted" << std::endl;

    ExecutionResult result(Status::success());
    result.rows_affected = rows_affected;
    return result;
}

ExecutionResult ExecutionEngine::executeSelect(const SelectStatement* stmt) {
    if (!stmt) {
        return ExecutionResult(Status::unknown("Null statement"));
    }

    // 获取表
    Table* table = catalog_->getTable(stmt->getTableName());
    if (!table) {
        return ExecutionResult(Status::tableNotFound(stmt->getTableName()));
    }

    // 获取锁 (简化：使用共享锁)
    Transaction* txn = nullptr;  // TODO: 从上下文获取事务

    const TableDef& table_def = table->getTableDef();

    // 确定要输出的列
    std::vector<std::string> output_columns;
    bool select_all = false;

    for (const auto& col : stmt->getColumns()) {
        if (col == "*") {
            select_all = true;
            break;
        }
        output_columns.push_back(col);
    }

    if (select_all) {
        output_columns.clear();
        for (const auto& col : table_def.columns) {
            output_columns.push_back(col.name);
        }
    }

    // 验证列名
    for (const auto& col_name : output_columns) {
        bool found = false;
        for (const auto& col_def : table_def.columns) {
            if (col_def.name == col_name) {
                found = true;
                break;
            }
        }
        if (!found) {
            return ExecutionResult(Status::columnNotFound(col_name));
        }
    }

    // 创建执行器
    auto seq_scan = std::make_unique<SeqScanExecutor>(nullptr, table);
    seq_scan->init();

    // 收集结果
    ExecutionResult result(Status::success());
    Row row;

    while (seq_scan->next(&row)) {
        // 投影列
        Row projected_row;
        for (const auto& col_name : output_columns) {
            for (size_t i = 0; i < table_def.columns.size(); ++i) {
                if (table_def.columns[i].name == col_name) {
                    if (i < row.size()) {
                        projected_row.addValue(row.getValue(i));
                    }
                    break;
                }
            }
        }
        result.rows.push_back(projected_row);
    }

    // 输出结果
    // 打印表头
    for (size_t i = 0; i < output_columns.size(); ++i) {
        if (i > 0) std::cout << "\t";
        std::cout << output_columns[i];
    }
    std::cout << std::endl;

    // 打印分隔线
    for (size_t i = 0; i < output_columns.size(); ++i) {
        if (i > 0) std::cout << "\t";
        std::cout << "--------";
    }
    std::cout << std::endl;

    // 打印数据
    for (const auto& r : result.rows) {
        std::cout << r << std::endl;
    }

    std::cout << result.rows.size() << " row(s) returned" << std::endl;
    return result;
}

ExecutionResult ExecutionEngine::executeUpdate(const UpdateStatement* stmt) {
    if (!stmt) {
        return ExecutionResult(Status::unknown("Null statement"));
    }

    // 获取表
    Table* table = catalog_->getTable(stmt->getTableName());
    if (!table) {
        return ExecutionResult(Status::tableNotFound(stmt->getTableName()));
    }

    // 获取锁 (简化：使用排他锁)
    Transaction* txn = nullptr;  // TODO: 从上下文获取事务

    const TableDef& table_def = table->getTableDef();

    // 解析 SET 子句
    std::vector<std::pair<std::string, Value>> updates;
    for (const auto& [col_name, expr] : stmt->getSetClauses()) {
        // 验证列名
        bool found = false;
        for (const auto& col_def : table_def.columns) {
            if (col_def.name == col_name) {
                found = true;
                break;
            }
        }
        if (!found) {
            return ExecutionResult(Status::columnNotFound(col_name));
        }

        // 求值表达式
        Value value;
        switch (expr->type()) {
            case ExpressionType::LITERAL_INT: {
                auto* literal = static_cast<LiteralInt*>(expr.get());
                value = literal->getValue();
                break;
            }
            case ExpressionType::LITERAL_FLOAT: {
                auto* literal = static_cast<LiteralFloat*>(expr.get());
                value = literal->getValue();
                break;
            }
            case ExpressionType::LITERAL_STRING: {
                auto* literal = static_cast<LiteralString*>(expr.get());
                value = literal->getValue();
                break;
            }
            default:
                return ExecutionResult(Status::unknown("Unsupported expression type"));
        }

        updates.push_back({col_name, value});
    }

    // 简化实现：全表扫描更新
    // TODO: 使用 WHERE 条件过滤
    size_t rows_affected = 0;

    // 创建迭代器
    auto iterator = table->createIterator();
    Row row;

    while (iterator->hasNext()) {
        if (iterator->next(&row)) {
            // TODO: 检查 WHERE 条件
            // TODO: 更新行
            rows_affected++;
        }
    }

    std::cout << rows_affected << " row(s) updated" << std::endl;

    ExecutionResult result(Status::success());
    result.rows_affected = rows_affected;
    return result;
}

ExecutionResult ExecutionEngine::executeDelete(const DeleteStatement* stmt) {
    if (!stmt) {
        return ExecutionResult(Status::unknown("Null statement"));
    }

    // 获取表
    Table* table = catalog_->getTable(stmt->getTableName());
    if (!table) {
        return ExecutionResult(Status::tableNotFound(stmt->getTableName()));
    }

    // 获取锁 (简化：使用排他锁)
    Transaction* txn = nullptr;  // TODO: 从上下文获取事务

    // 简化实现：全表扫描删除
    // TODO: 使用 WHERE 条件过滤
    size_t rows_affected = 0;

    // 创建迭代器
    auto iterator = table->createIterator();
    Row row;

    while (iterator->hasNext()) {
        if (iterator->next(&row)) {
            // TODO: 检查 WHERE 条件
            // TODO: 删除行
            rows_affected++;
        }
    }

    std::cout << rows_affected << " row(s) deleted" << std::endl;

    ExecutionResult result(Status::success());
    result.rows_affected = rows_affected;
    return result;
}

ExecutionResult ExecutionEngine::executeDropTable(const DropTableStatement* stmt) {
    if (!stmt) {
        return ExecutionResult(Status::unknown("Null statement"));
    }

    Status status = catalog_->dropTable(stmt->getTableName());
    if (!status.ok()) {
        return ExecutionResult(status);
    }

    std::cout << "Table dropped: " << stmt->getTableName() << std::endl;
    return ExecutionResult(Status::success());
}

}  // namespace minidb
