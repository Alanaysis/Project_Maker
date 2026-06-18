#pragma once

#include "sql/tokenizer.h"
#include "sql/ast.h"
#include "core/status.h"
#include <memory>
#include <vector>
#include <string>

namespace minidb {

/**
 * @brief 语法分析器
 *
 * 使用递归下降法解析 SQL 语句，生成 AST
 *
 * 支持的语法:
 * - CREATE TABLE table_name (col1 type1, col2 type2, ...)
 * - INSERT INTO table_name VALUES (val1, val2, ...)
 * - SELECT col1, col2 FROM table_name [WHERE condition]
 * - UPDATE table_name SET col1 = val1, col2 = val2 [WHERE condition]
 * - DELETE FROM table_name [WHERE condition]
 * - DROP TABLE table_name
 */
class Parser {
public:
    /**
     * @brief 构造函数
     * @param tokens Token 列表
     */
    explicit Parser(const std::vector<Token>& tokens);

    /**
     * @brief 构造函数
     * @param sql SQL 语句
     */
    explicit Parser(const std::string& sql);

    /**
     * @brief 解析 SQL 语句
     * @return AST 根节点
     */
    std::unique_ptr<Statement> parse();

    /**
     * @brief 获取错误信息
     * @return 错误信息
     */
    const std::string& getError() const { return error_; }

    /**
     * @brief 检查是否有错误
     * @return 是否有错误
     */
    bool hasError() const { return !error_.empty(); }

private:
    // ==================== 语句解析 ====================

    /**
     * @brief 解析 CREATE TABLE 语句
     */
    std::unique_ptr<Statement> parseCreateTable();

    /**
     * @brief 解析 INSERT 语句
     */
    std::unique_ptr<Statement> parseInsert();

    /**
     * @brief 解析 SELECT 语句
     */
    std::unique_ptr<Statement> parseSelect();

    /**
     * @brief 解析 UPDATE 语句
     */
    std::unique_ptr<Statement> parseUpdate();

    /**
     * @brief 解析 DELETE 语句
     */
    std::unique_ptr<Statement> parseDelete();

    /**
     * @brief 解析 DROP TABLE 语句
     */
    std::unique_ptr<Statement> parseDropTable();

    // ==================== 表达式解析 ====================

    /**
     * @brief 解析表达式
     */
    std::unique_ptr<Expression> parseExpression();

    /**
     * @brief 解析 OR 表达式
     */
    std::unique_ptr<Expression> parseOrExpression();

    /**
     * @brief 解析 AND 表达式
     */
    std::unique_ptr<Expression> parseAndExpression();

    /**
     * @brief 解析比较表达式
     */
    std::unique_ptr<Expression> parseComparison();

    /**
     * @brief 解析主表达式 (字面量、列引用、括号表达式)
     */
    std::unique_ptr<Expression> parsePrimary();

    // ==================== 辅助方法 ====================

    /**
     * @brief 获取当前 Token
     */
    const Token& currentToken() const;

    /**
     * @brief 获取下一个 Token (前进)
     */
    const Token& nextToken();

    /**
     * @brief 检查当前 Token 类型
     */
    bool check(TokenType type) const;

    /**
     * @brief 匹配并消费 Token
     */
    bool match(TokenType type);

    /**
     * @brief 期望当前 Token 类型，否则报错
     */
    bool expect(TokenType type);

    /**
     * @brief 检查是否到达末尾
     */
    bool isAtEnd() const;

    /**
     * @brief 设置错误信息
     */
    void setError(const std::string& message);

    /**
     * @brief 解析列定义
     */
    ColumnDefinition parseColumnDefinition();

    /**
     * @brief 解析数据类型
     */
    TypeId parseDataType(size_t* max_length);

    // Token 列表
    std::vector<Token> tokens_;
    size_t current_;

    // 错误信息
    std::string error_;
};

}  // namespace minidb
