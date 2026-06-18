#pragma once

#include "core/common.h"
#include "sql/tokenizer.h"
#include <memory>
#include <vector>
#include <string>

namespace minidb {

// ==================== 表达式 ====================

// 表达式类型
enum class ExpressionType {
    LITERAL_INT,
    LITERAL_FLOAT,
    LITERAL_STRING,
    COLUMN_REF,
    BINARY_OP,
    UNARY_OP,
    COMPARISON
};

// 表达式基类
class Expression {
public:
    virtual ~Expression() = default;
    virtual ExpressionType type() const = 0;
    virtual std::string toString() const = 0;
};

// 整数字面量
class LiteralInt : public Expression {
public:
    explicit LiteralInt(int32_t val) : value_(val) {}
    ExpressionType type() const override { return ExpressionType::LITERAL_INT; }
    std::string toString() const override;
    int32_t getValue() const { return value_; }

private:
    int32_t value_;
};

// 浮点字面量
class LiteralFloat : public Expression {
public:
    explicit LiteralFloat(float val) : value_(val) {}
    ExpressionType type() const override { return ExpressionType::LITERAL_FLOAT; }
    std::string toString() const override;
    float getValue() const { return value_; }

private:
    float value_;
};

// 字符串字面量
class LiteralString : public Expression {
public:
    explicit LiteralString(const std::string& val) : value_(val) {}
    ExpressionType type() const override { return ExpressionType::LITERAL_STRING; }
    std::string toString() const override;
    const std::string& getValue() const { return value_; }

private:
    std::string value_;
};

// 列引用
class ColumnRef : public Expression {
public:
    ColumnRef(const std::string& table, const std::string& column)
        : table_name_(table), column_name_(column) {}
    explicit ColumnRef(const std::string& column)
        : column_name_(column) {}

    ExpressionType type() const override { return ExpressionType::COLUMN_REF; }
    std::string toString() const override;
    const std::string& getTableName() const { return table_name_; }
    const std::string& getColumnName() const { return column_name_; }

private:
    std::string table_name_;
    std::string column_name_;
};

// 比较运算符
enum class ComparisonOp {
    EQUAL,
    NOT_EQUAL,
    LESS,
    GREATER,
    LESS_EQUAL,
    GREATER_EQUAL
};

// 比较表达式
class ComparisonExpression : public Expression {
public:
    ComparisonExpression(std::unique_ptr<Expression> left, ComparisonOp op,
                         std::unique_ptr<Expression> right)
        : left_(std::move(left)), op_(op), right_(std::move(right)) {}

    ExpressionType type() const override { return ExpressionType::COMPARISON; }
    std::string toString() const override;
    const Expression* getLeft() const { return left_.get(); }
    ComparisonOp getOp() const { return op_; }
    const Expression* getRight() const { return right_.get(); }

private:
    std::unique_ptr<Expression> left_;
    ComparisonOp op_;
    std::unique_ptr<Expression> right_;
};

// 逻辑运算符
enum class LogicalOp {
    AND,
    OR,
    NOT
};

// 逻辑表达式
class LogicalExpression : public Expression {
public:
    LogicalExpression(std::unique_ptr<Expression> left, LogicalOp op,
                      std::unique_ptr<Expression> right)
        : left_(std::move(left)), op_(op), right_(std::move(right)) {}

    ExpressionType type() const override { return ExpressionType::BINARY_OP; }
    std::string toString() const override;
    const Expression* getLeft() const { return left_.get(); }
    LogicalOp getOp() const { return op_; }
    const Expression* getRight() const { return right_.get(); }

private:
    std::unique_ptr<Expression> left_;
    LogicalOp op_;
    std::unique_ptr<Expression> right_;
};

// ==================== 语句 ====================

// 语句类型
enum class StatementType {
    CREATE_TABLE,
    DROP_TABLE,
    INSERT,
    SELECT,
    UPDATE,
    DELETE
};

// 语句基类
class Statement {
public:
    virtual ~Statement() = default;
    virtual StatementType type() const = 0;
    virtual std::string toString() const = 0;
};

// 列定义
struct ColumnDefinition {
    std::string name;
    TypeId type;
    size_t max_length;
    bool is_primary_key;
    bool is_nullable;
};

// CREATE TABLE 语句
class CreateTableStatement : public Statement {
public:
    CreateTableStatement(const std::string& name,
                         const std::vector<ColumnDefinition>& columns)
        : table_name_(name), columns_(columns) {}

    StatementType type() const override { return StatementType::CREATE_TABLE; }
    std::string toString() const override;
    const std::string& getTableName() const { return table_name_; }
    const std::vector<ColumnDefinition>& getColumns() const { return columns_; }

private:
    std::string table_name_;
    std::vector<ColumnDefinition> columns_;
};

// INSERT 语句
class InsertStatement : public Statement {
public:
    InsertStatement(const std::string& table,
                    const std::vector<std::vector<std::unique_ptr<Expression>>>& values)
        : table_name_(table), values_(std::move(values)) {}

    StatementType type() const override { return StatementType::INSERT; }
    std::string toString() const override;
    const std::string& getTableName() const { return table_name_; }
    const std::vector<std::vector<std::unique_ptr<Expression>>>& getValues() const {
        return values_;
    }

private:
    std::string table_name_;
    std::vector<std::vector<std::unique_ptr<Expression>>> values_;
};

// SELECT 语句
class SelectStatement : public Statement {
public:
    SelectStatement(const std::vector<std::string>& columns,
                    const std::string& table,
                    std::unique_ptr<Expression> where = nullptr)
        : columns_(columns), table_name_(table), where_clause_(std::move(where)) {}

    StatementType type() const override { return StatementType::SELECT; }
    std::string toString() const override;
    const std::vector<std::string>& getColumns() const { return columns_; }
    const std::string& getTableName() const { return table_name_; }
    const Expression* getWhereClause() const { return where_clause_.get(); }

private:
    std::vector<std::string> columns_;
    std::string table_name_;
    std::unique_ptr<Expression> where_clause_;
};

// UPDATE 语句
class UpdateStatement : public Statement {
public:
    UpdateStatement(const std::string& table,
                    const std::vector<std::pair<std::string, std::unique_ptr<Expression>>>& set,
                    std::unique_ptr<Expression> where = nullptr)
        : table_name_(table), set_clauses_(std::move(set)),
          where_clause_(std::move(where)) {}

    StatementType type() const override { return StatementType::UPDATE; }
    std::string toString() const override;
    const std::string& getTableName() const { return table_name_; }
    const std::vector<std::pair<std::string, std::unique_ptr<Expression>>>& getSetClauses() const {
        return set_clauses_;
    }
    const Expression* getWhereClause() const { return where_clause_.get(); }

private:
    std::string table_name_;
    std::vector<std::pair<std::string, std::unique_ptr<Expression>>> set_clauses_;
    std::unique_ptr<Expression> where_clause_;
};

// DELETE 语句
class DeleteStatement : public Statement {
public:
    DeleteStatement(const std::string& table,
                    std::unique_ptr<Expression> where = nullptr)
        : table_name_(table), where_clause_(std::move(where)) {}

    StatementType type() const override { return StatementType::DELETE; }
    std::string toString() const override;
    const std::string& getTableName() const { return table_name_; }
    const Expression* getWhereClause() const { return where_clause_.get(); }

private:
    std::string table_name_;
    std::unique_ptr<Expression> where_clause_;
};

// DROP TABLE 语句
class DropTableStatement : public Statement {
public:
    explicit DropTableStatement(const std::string& name)
        : table_name_(name) {}

    StatementType type() const override { return StatementType::DROP_TABLE; }
    std::string toString() const override;
    const std::string& getTableName() const { return table_name_; }

private:
    std::string table_name_;
};

}  // namespace minidb
