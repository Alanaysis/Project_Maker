#include "sql/parser.h"
#include <iostream>
#include <sstream>

namespace minidb {

// ==================== Expression 实现 ====================

std::string LiteralInt::toString() const {
    return std::to_string(value_);
}

std::string LiteralFloat::toString() const {
    return std::to_string(value_);
}

std::string LiteralString::toString() const {
    return "'" + value_ + "'";
}

std::string ColumnRef::toString() const {
    if (table_name_.empty()) {
        return column_name_;
    }
    return table_name_ + "." + column_name_;
}

std::string ComparisonExpression::toString() const {
    std::string op_str;
    switch (op_) {
        case ComparisonOp::EQUAL: op_str = "="; break;
        case ComparisonOp::NOT_EQUAL: op_str = "<>"; break;
        case ComparisonOp::LESS: op_str = "<"; break;
        case ComparisonOp::GREATER: op_str = ">"; break;
        case ComparisonOp::LESS_EQUAL: op_str = "<="; break;
        case ComparisonOp::GREATER_EQUAL: op_str = ">="; break;
    }
    return left_->toString() + " " + op_str + " " + right_->toString();
}

std::string LogicalExpression::toString() const {
    std::string op_str;
    switch (op_) {
        case LogicalOp::AND: op_str = "AND"; break;
        case LogicalOp::OR: op_str = "OR"; break;
        case LogicalOp::NOT: op_str = "NOT"; break;
    }
    return left_->toString() + " " + op_str + " " + right_->toString();
}

// ==================== Statement 实现 ====================

std::string CreateTableStatement::toString() const {
    std::stringstream ss;
    ss << "CREATE TABLE " << table_name_ << " (";
    for (size_t i = 0; i < columns_.size(); ++i) {
        if (i > 0) ss << ", ";
        ss << columns_[i].name << " ";
        switch (columns_[i].type) {
            case TypeId::INTEGER: ss << "INT"; break;
            case TypeId::FLOAT: ss << "FLOAT"; break;
            case TypeId::VARCHAR: ss << "VARCHAR(" << columns_[i].max_length << ")"; break;
            default: ss << "UNKNOWN"; break;
        }
        if (columns_[i].is_primary_key) ss << " PRIMARY KEY";
    }
    ss << ")";
    return ss.str();
}

std::string InsertStatement::toString() const {
    std::stringstream ss;
    ss << "INSERT INTO " << table_name_ << " VALUES ";
    for (size_t i = 0; i < values_.size(); ++i) {
        if (i > 0) ss << ", ";
        ss << "(";
        for (size_t j = 0; j < values_[i].size(); ++j) {
            if (j > 0) ss << ", ";
            if (values_[i][j]) ss << values_[i][j]->toString();
        }
        ss << ")";
    }
    return ss.str();
}

std::string SelectStatement::toString() const {
    std::stringstream ss;
    ss << "SELECT ";
    for (size_t i = 0; i < columns_.size(); ++i) {
        if (i > 0) ss << ", ";
        ss << columns_[i];
    }
    ss << " FROM " << table_name_;
    if (where_clause_) {
        ss << " WHERE " << where_clause_->toString();
    }
    return ss.str();
}

std::string UpdateStatement::toString() const {
    std::stringstream ss;
    ss << "UPDATE " << table_name_ << " SET ";
    for (size_t i = 0; i < set_clauses_.size(); ++i) {
        if (i > 0) ss << ", ";
        ss << set_clauses_[i].first << " = " << set_clauses_[i].second->toString();
    }
    if (where_clause_) {
        ss << " WHERE " << where_clause_->toString();
    }
    return ss.str();
}

std::string DeleteStatement::toString() const {
    std::stringstream ss;
    ss << "DELETE FROM " << table_name_;
    if (where_clause_) {
        ss << " WHERE " << where_clause_->toString();
    }
    return ss.str();
}

std::string DropTableStatement::toString() const {
    return "DROP TABLE " + table_name_;
}

// ==================== Parser 实现 ====================

Parser::Parser(const std::vector<Token>& tokens)
    : tokens_(tokens), current_(0) {}

Parser::Parser(const std::string& sql) : current_(0) {
    Tokenizer tokenizer(sql);
    tokens_ = tokenizer.tokenize();
    if (tokens_.empty() || tokens_.back().type != TokenType::EOF_TOKEN) {
        tokens_.push_back(Token(TokenType::EOF_TOKEN, "", 0, 0));
    }
}

std::unique_ptr<Statement> Parser::parse() {
    if (tokens_.empty()) {
        setError("Empty SQL statement");
        return nullptr;
    }

    const Token& token = currentToken();

    switch (token.type) {
        case TokenType::CREATE:
            return parseCreateTable();
        case TokenType::INSERT:
            return parseInsert();
        case TokenType::SELECT:
            return parseSelect();
        case TokenType::UPDATE:
            return parseUpdate();
        case TokenType::DELETE:
            return parseDelete();
        case TokenType::DROP:
            return parseDropTable();
        default:
            setError("Expected SQL statement, got: " + token.value);
            return nullptr;
    }
}

std::unique_ptr<Statement> Parser::parseCreateTable() {
    // CREATE TABLE table_name (col1 type1, col2 type2, ...)
    if (!expect(TokenType::CREATE)) return nullptr;
    if (!expect(TokenType::TABLE)) return nullptr;

    const Token& name_token = currentToken();
    if (!expect(TokenType::IDENTIFIER)) return nullptr;
    std::string table_name = name_token.value;

    if (!expect(TokenType::LPAREN)) return nullptr;

    std::vector<ColumnDefinition> columns;

    // 解析列定义
    do {
        ColumnDefinition col = parseColumnDefinition();
        if (hasError()) return nullptr;
        columns.push_back(col);

        if (!check(TokenType::COMMA)) break;
        nextToken();  // 跳过逗号
    } while (true);

    if (!expect(TokenType::RPAREN)) return nullptr;

    // 可选的分号
    if (check(TokenType::SEMICOLON)) {
        nextToken();
    }

    return std::make_unique<CreateTableStatement>(table_name, columns);
}

std::unique_ptr<Statement> Parser::parseInsert() {
    // INSERT INTO table_name VALUES (val1, val2, ...)
    if (!expect(TokenType::INSERT)) return nullptr;
    if (!expect(TokenType::INTO)) return nullptr;

    const Token& name_token = currentToken();
    if (!expect(TokenType::IDENTIFIER)) return nullptr;
    std::string table_name = name_token.value;

    if (!expect(TokenType::VALUES)) return nullptr;

    std::vector<std::vector<std::unique_ptr<Expression>>> all_values;

    // 解析值列表
    do {
        if (!expect(TokenType::LPAREN)) return nullptr;

        std::vector<std::unique_ptr<Expression>> values;
        do {
            auto expr = parseExpression();
            if (hasError()) return nullptr;
            values.push_back(std::move(expr));

            if (!check(TokenType::COMMA)) break;
            nextToken();  // 跳过逗号
        } while (true);

        if (!expect(TokenType::RPAREN)) return nullptr;
        all_values.push_back(std::move(values));

        if (!check(TokenType::COMMA)) break;
        nextToken();  // 跳过逗号
    } while (true);

    // 可选的分号
    if (check(TokenType::SEMICOLON)) {
        nextToken();
    }

    return std::make_unique<InsertStatement>(table_name, std::move(all_values));
}

std::unique_ptr<Statement> Parser::parseSelect() {
    // SELECT col1, col2 FROM table_name [WHERE condition]
    if (!expect(TokenType::SELECT)) return nullptr;

    std::vector<std::string> columns;

    // 解析列名
    if (check(TokenType::STAR)) {
        columns.push_back("*");
        nextToken();
    } else {
        do {
            const Token& col_token = currentToken();
            if (!expect(TokenType::IDENTIFIER)) return nullptr;
            columns.push_back(col_token.value);

            if (!check(TokenType::COMMA)) break;
            nextToken();  // 跳过逗号
        } while (true);
    }

    if (!expect(TokenType::FROM)) return nullptr;

    const Token& table_token = currentToken();
    if (!expect(TokenType::IDENTIFIER)) return nullptr;
    std::string table_name = table_token.value;

    // 可选的 WHERE 子句
    std::unique_ptr<Expression> where_clause = nullptr;
    if (check(TokenType::WHERE)) {
        nextToken();  // 跳过 WHERE
        where_clause = parseExpression();
        if (hasError()) return nullptr;
    }

    // 可选的分号
    if (check(TokenType::SEMICOLON)) {
        nextToken();
    }

    return std::make_unique<SelectStatement>(columns, table_name,
                                             std::move(where_clause));
}

std::unique_ptr<Statement> Parser::parseUpdate() {
    // UPDATE table_name SET col1 = val1, col2 = val2 [WHERE condition]
    if (!expect(TokenType::UPDATE)) return nullptr;

    const Token& table_token = currentToken();
    if (!expect(TokenType::IDENTIFIER)) return nullptr;
    std::string table_name = table_token.value;

    if (!expect(TokenType::SET)) return nullptr;

    std::vector<std::pair<std::string, std::unique_ptr<Expression>>> set_clauses;

    do {
        const Token& col_token = currentToken();
        if (!expect(TokenType::IDENTIFIER)) return nullptr;
        std::string col_name = col_token.value;

        if (!expect(TokenType::EQUAL)) return nullptr;

        auto value_expr = parseExpression();
        if (hasError()) return nullptr;

        set_clauses.push_back({col_name, std::move(value_expr)});

        if (!check(TokenType::COMMA)) break;
        nextToken();  // 跳过逗号
    } while (true);

    // 可选的 WHERE 子句
    std::unique_ptr<Expression> where_clause = nullptr;
    if (check(TokenType::WHERE)) {
        nextToken();  // 跳过 WHERE
        where_clause = parseExpression();
        if (hasError()) return nullptr;
    }

    // 可选的分号
    if (check(TokenType::SEMICOLON)) {
        nextToken();
    }

    return std::make_unique<UpdateStatement>(table_name, std::move(set_clauses),
                                              std::move(where_clause));
}

std::unique_ptr<Statement> Parser::parseDelete() {
    // DELETE FROM table_name [WHERE condition]
    if (!expect(TokenType::DELETE)) return nullptr;
    if (!expect(TokenType::FROM)) return nullptr;

    const Token& table_token = currentToken();
    if (!expect(TokenType::IDENTIFIER)) return nullptr;
    std::string table_name = table_token.value;

    // 可选的 WHERE 子句
    std::unique_ptr<Expression> where_clause = nullptr;
    if (check(TokenType::WHERE)) {
        nextToken();  // 跳过 WHERE
        where_clause = parseExpression();
        if (hasError()) return nullptr;
    }

    // 可选的分号
    if (check(TokenType::SEMICOLON)) {
        nextToken();
    }

    return std::make_unique<DeleteStatement>(table_name, std::move(where_clause));
}

std::unique_ptr<Statement> Parser::parseDropTable() {
    // DROP TABLE table_name
    if (!expect(TokenType::DROP)) return nullptr;
    if (!expect(TokenType::TABLE)) return nullptr;

    const Token& table_token = currentToken();
    if (!expect(TokenType::IDENTIFIER)) return nullptr;
    std::string table_name = table_token.value;

    // 可选的分号
    if (check(TokenType::SEMICOLON)) {
        nextToken();
    }

    return std::make_unique<DropTableStatement>(table_name);
}

// ==================== 表达式解析 ====================

std::unique_ptr<Expression> Parser::parseExpression() {
    return parseOrExpression();
}

std::unique_ptr<Expression> Parser::parseOrExpression() {
    auto left = parseAndExpression();
    if (hasError()) return nullptr;

    while (check(TokenType::OR)) {
        nextToken();  // 跳过 OR
        auto right = parseAndExpression();
        if (hasError()) return nullptr;

        left = std::make_unique<LogicalExpression>(std::move(left),
                                                    LogicalOp::OR,
                                                    std::move(right));
    }

    return left;
}

std::unique_ptr<Expression> Parser::parseAndExpression() {
    auto left = parseComparison();
    if (hasError()) return nullptr;

    while (check(TokenType::AND)) {
        nextToken();  // 跳过 AND
        auto right = parseComparison();
        if (hasError()) return nullptr;

        left = std::make_unique<LogicalExpression>(std::move(left),
                                                    LogicalOp::AND,
                                                    std::move(right));
    }

    return left;
}

std::unique_ptr<Expression> Parser::parseComparison() {
    auto left = parsePrimary();
    if (hasError()) return nullptr;

    if (check(TokenType::EQUAL) || check(TokenType::NOT_EQUAL) ||
        check(TokenType::LESS) || check(TokenType::GREATER) ||
        check(TokenType::LESS_EQUAL) || check(TokenType::GREATER_EQUAL)) {

        ComparisonOp op;
        if (check(TokenType::EQUAL)) op = ComparisonOp::EQUAL;
        else if (check(TokenType::NOT_EQUAL)) op = ComparisonOp::NOT_EQUAL;
        else if (check(TokenType::LESS)) op = ComparisonOp::LESS;
        else if (check(TokenType::GREATER)) op = ComparisonOp::GREATER;
        else if (check(TokenType::LESS_EQUAL)) op = ComparisonOp::LESS_EQUAL;
        else op = ComparisonOp::GREATER_EQUAL;

        nextToken();  // 跳过运算符

        auto right = parsePrimary();
        if (hasError()) return nullptr;

        return std::make_unique<ComparisonExpression>(std::move(left), op,
                                                       std::move(right));
    }

    return left;
}

std::unique_ptr<Expression> Parser::parsePrimary() {
    const Token& token = currentToken();

    // 整数字面量
    if (check(TokenType::INTEGER)) {
        nextToken();
        int32_t value = std::stoi(token.value);
        return std::make_unique<LiteralInt>(value);
    }

    // 浮点字面量
    if (check(TokenType::FLOAT)) {
        nextToken();
        float value = std::stof(token.value);
        return std::make_unique<LiteralFloat>(value);
    }

    // 字符串字面量
    if (check(TokenType::STRING)) {
        nextToken();
        return std::make_unique<LiteralString>(token.value);
    }

    // 标识符 (列引用)
    if (check(TokenType::IDENTIFIER)) {
        nextToken();
        std::string name = token.value;

        // 检查是否有表名前缀 (table.column)
        if (check(TokenType::DOT)) {
            nextToken();  // 跳过点
            const Token& col_token = currentToken();
            if (!expect(TokenType::IDENTIFIER)) return nullptr;
            return std::make_unique<ColumnRef>(name, col_token.value);
        }

        return std::make_unique<ColumnRef>(name);
    }

    // 括号表达式
    if (check(TokenType::LPAREN)) {
        nextToken();  // 跳过左括号
        auto expr = parseExpression();
        if (hasError()) return nullptr;
        if (!expect(TokenType::RPAREN)) return nullptr;
        return expr;
    }

    setError("Expected expression");
    return nullptr;
}

// ==================== 辅助方法 ====================

const Token& Parser::currentToken() const {
    if (current_ >= tokens_.size()) {
        static Token eof_token(TokenType::EOF_TOKEN, "", 0, 0);
        return eof_token;
    }
    return tokens_[current_];
}

const Token& Parser::nextToken() {
    if (current_ < tokens_.size() - 1) {
        current_++;
    }
    return currentToken();
}

bool Parser::check(TokenType type) const {
    return currentToken().type == type;
}

bool Parser::match(TokenType type) {
    if (check(type)) {
        nextToken();
        return true;
    }
    return false;
}

bool Parser::expect(TokenType type) {
    if (check(type)) {
        nextToken();
        return true;
    }

    std::stringstream ss;
    ss << "Expected " << static_cast<int>(type)
       << ", got " << currentToken().value
       << " at line " << currentToken().line
       << ", column " << currentToken().column;
    setError(ss.str());
    return false;
}

bool Parser::isAtEnd() const {
    return current_ >= tokens_.size() ||
           currentToken().type == TokenType::EOF_TOKEN;
}

void Parser::setError(const std::string& message) {
    error_ = message;
}

ColumnDefinition Parser::parseColumnDefinition() {
    ColumnDefinition col;

    // 列名
    const Token& name_token = currentToken();
    if (!expect(TokenType::IDENTIFIER)) return col;
    col.name = name_token.value;

    // 数据类型
    col.type = parseDataType(&col.max_length);
    if (hasError()) return col;

    // 可选的 PRIMARY KEY
    if (check(TokenType::PRIMARY)) {
        nextToken();
        if (!expect(TokenType::KEY)) return col;
        col.is_primary_key = true;
        col.is_nullable = false;
    }

    return col;
}

TypeId Parser::parseDataType(size_t* max_length) {
    *max_length = 0;

    if (check(TokenType::INT_TYPE)) {
        nextToken();
        return TypeId::INTEGER;
    }

    if (check(TokenType::FLOAT_TYPE)) {
        nextToken();
        return TypeId::FLOAT;
    }

    if (check(TokenType::VARCHAR_TYPE)) {
        nextToken();
        if (!expect(TokenType::LPAREN)) return TypeId::INVALID;

        const Token& len_token = currentToken();
        if (!expect(TokenType::INTEGER)) return TypeId::INVALID;
        *max_length = std::stoi(len_token.value);

        if (!expect(TokenType::RPAREN)) return TypeId::INVALID;
        return TypeId::VARCHAR;
    }

    setError("Expected data type");
    return TypeId::INVALID;
}

}  // namespace minidb
