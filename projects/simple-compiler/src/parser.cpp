#include "parser.hpp"
#include <stdexcept>

namespace compiler {

Parser::Parser(std::vector<Token> tokens)
    : tokens_(std::move(tokens)), current_(0), panicMode_(false) {}

std::unique_ptr<Program> Parser::parse() {
    auto program = std::make_unique<Program>();

    while (!isAtEnd()) {
        try {
            auto decl = declaration();
            if (decl) {
                program->statements.push_back(std::move(decl));
            }
        } catch (const std::runtime_error& e) {
            // 错误恢复
            synchronize();
        }
    }

    return program;
}

// ==================== 辅助方法 ====================

const Token& Parser::peek() const {
    return tokens_[current_];
}

const Token& Parser::previous() const {
    return tokens_[current_ - 1];
}

Token Parser::advance() {
    if (!isAtEnd()) current_++;
    return tokens_[current_ - 1];
}

bool Parser::check(TokenType type) const {
    if (isAtEnd()) return false;
    return peek().type == type;
}

bool Parser::match(std::initializer_list<TokenType> types) {
    for (TokenType type : types) {
        if (check(type)) {
            advance();
            return true;
        }
    }
    return false;
}

Token Parser::expect(TokenType type, const std::string& message) {
    if (check(type)) return advance();
    error(peek(), message);
    return Token(); // 不会执行到这里
}

bool Parser::isAtEnd() const {
    return peek().type == TokenType::EOF_TOKEN;
}

void Parser::error(const Token& token, const std::string& message) {
    std::string errorMsg = "Parse error at line " + std::to_string(token.line) +
                          ", column " + std::to_string(token.column) + ": " + message;

    if (token.type == TokenType::EOF_TOKEN) {
        errorMsg += " (at end of file)";
    } else {
        errorMsg += " (found '" + token.lexeme + "')";
    }

    errors_.push_back(errorMsg);
    panicMode_ = true;
    throw std::runtime_error(errorMsg);
}

void Parser::synchronize() {
    panicMode_ = false;

    while (!isAtEnd()) {
        // 跳到下一个语句边界
        if (previous().type == TokenType::SEMICOLON) return;

        switch (peek().type) {
            case TokenType::LET:
            case TokenType::VAR:
            case TokenType::CONST:
            case TokenType::FUNCTION:
            case TokenType::CLASS:
            case TokenType::IF:
            case TokenType::WHILE:
            case TokenType::FOR:
            case TokenType::RETURN:
            case TokenType::PRINT:
            case TokenType::BREAK:
            case TokenType::CONTINUE:
                return;
            default:
                break;
        }

        advance();
    }
}

// ==================== 声明解析 ====================

StmtPtr Parser::declaration() {
    try {
        // 变量声明
        if (match({TokenType::LET, TokenType::VAR, TokenType::CONST})) {
            return varDeclaration();
        }

        // 函数声明
        if (check(TokenType::FUNCTION)) {
            return functionDeclaration();
        }

        // 类声明
        if (check(TokenType::CLASS)) {
            return classDeclaration();
        }

        return statement();
    } catch (const std::runtime_error& e) {
        synchronize();
        return nullptr;
    }
}

StmtPtr Parser::varDeclaration() {
    Token keyword = previous();
    bool isConst = (keyword.type == TokenType::CONST);
    bool isVar = (keyword.type == TokenType::VAR);

    Token name = expect(TokenType::IDENTIFIER, "Expected variable name");

    // 可选的类型注解
    std::shared_ptr<Type> type = nullptr;
    if (match({TokenType::COLON})) {
        type = typeAnnotation();
    }

    // 可选的初始化器
    ExprPtr initializer = nullptr;
    if (match({TokenType::ASSIGN})) {
        initializer = expression();
    } else if (isConst) {
        error(previous(), "Constants must be initialized");
    }

    expect(TokenType::SEMICOLON, "Expected ';' after variable declaration");

    return std::make_unique<VarDeclStmt>(
        name.lexeme, std::move(type), std::move(initializer),
        isConst, isVar, name.line, name.column
    );
}

StmtPtr Parser::functionDeclaration() {
    Token keyword = advance(); // 消耗 fn

    Token name = expect(TokenType::IDENTIFIER, "Expected function name");

    expect(TokenType::LEFT_PAREN, "Expected '(' after function name");

    // 参数列表
    std::vector<Parameter> params;
    if (!check(TokenType::RIGHT_PAREN)) {
        do {
            Token paramName = expect(TokenType::IDENTIFIER, "Expected parameter name");

            expect(TokenType::COLON, "Expected ':' after parameter name");
            TypePtr paramType = typeAnnotation();

            ExprPtr defaultValue = nullptr;
            if (match({TokenType::ASSIGN})) {
                defaultValue = expression();
            }

            params.emplace_back(paramName.lexeme, std::move(paramType),
                               std::move(defaultValue));
        } while (match({TokenType::COMMA}));
    }

    expect(TokenType::RIGHT_PAREN, "Expected ')' after parameters");

    // 返回类型
    std::shared_ptr<Type> returnType = nullptr;
    if (match({TokenType::COLON})) {
        returnType = typeAnnotation();
    }

    // 函数体
    StmtPtr body = block();

    return std::make_unique<FunctionStmt>(
        name.lexeme, std::move(params), std::move(returnType),
        std::move(body), name.line, name.column
    );
}

StmtPtr Parser::classDeclaration() {
    Token keyword = advance(); // 消耗 class

    Token name = expect(TokenType::IDENTIFIER, "Expected class name");

    // 可选的父类
    std::string parent;
    if (match({TokenType::LESS})) {
        Token parentName = expect(TokenType::IDENTIFIER, "Expected parent class name");
        parent = parentName.lexeme;
    }

    expect(TokenType::LEFT_BRACE, "Expected '{' after class name");

    // 类成员
    std::vector<ClassMember> members;
    while (!check(TokenType::RIGHT_BRACE) && !isAtEnd()) {
        members.push_back(classMember());
    }

    expect(TokenType::RIGHT_BRACE, "Expected '}' after class body");

    return std::make_unique<ClassStmt>(
        name.lexeme, parent, std::move(members), name.line, name.column
    );
}

ClassMember Parser::classMember() {
    Token name = expect(TokenType::IDENTIFIER, "Expected member name");

    // 检查是否是方法
    if (check(TokenType::LEFT_PAREN)) {
        // 方法声明
        auto func = functionDeclaration();
        auto* funcStmt = dynamic_cast<FunctionStmt*>(func.release());
        return ClassMember(name.lexeme, funcStmt);
    }

    // 字段声明
    expect(TokenType::COLON, "Expected ':' after field name");
    TypePtr type = typeAnnotation();

    ExprPtr initializer = nullptr;
    if (match({TokenType::ASSIGN})) {
        initializer = expression();
    }

    expect(TokenType::SEMICOLON, "Expected ';' after field declaration");

    return ClassMember(name.lexeme, std::move(type), std::move(initializer));
}

// ==================== 语句解析 ====================

StmtPtr Parser::statement() {
    // if语句
    if (check(TokenType::IF)) {
        return ifStatement();
    }

    // while循环
    if (check(TokenType::WHILE)) {
        return whileStatement();
    }

    // for循环
    if (check(TokenType::FOR)) {
        return forStatement();
    }

    // return语句
    if (check(TokenType::RETURN)) {
        return returnStatement();
    }

    // print语句
    if (check(TokenType::PRINT)) {
        return printStatement();
    }

    // break语句
    if (check(TokenType::BREAK)) {
        return breakStatement();
    }

    // continue语句
    if (check(TokenType::CONTINUE)) {
        return continueStatement();
    }

    // 块语句
    if (check(TokenType::LEFT_BRACE)) {
        return block();
    }

    // 表达式语句
    return expressionStatement();
}

StmtPtr Parser::expressionStatement() {
    int line = peek().line;
    int column = peek().column;

    ExprPtr expr = expression();

    // 可选的分号
    if (match({TokenType::SEMICOLON})) {
        // 消耗了分号
    }

    return std::make_unique<ExprStmt>(std::move(expr), line, column);
}

StmtPtr Parser::ifStatement() {
    Token keyword = advance(); // 消耗 if

    expect(TokenType::LEFT_PAREN, "Expected '(' after 'if'");
    ExprPtr condition = expression();
    expect(TokenType::RIGHT_PAREN, "Expected ')' after if condition");

    StmtPtr thenBranch = statement();

    StmtPtr elseBranch = nullptr;
    if (match({TokenType::ELSE})) {
        elseBranch = statement();
    }

    return std::make_unique<IfStmt>(
        std::move(condition), std::move(thenBranch),
        std::move(elseBranch), keyword.line, keyword.column
    );
}

StmtPtr Parser::whileStatement() {
    Token keyword = advance(); // 消耗 while

    expect(TokenType::LEFT_PAREN, "Expected '(' after 'while'");
    ExprPtr condition = expression();
    expect(TokenType::RIGHT_PAREN, "Expected ')' after while condition");

    StmtPtr body = statement();

    return std::make_unique<WhileStmt>(
        std::move(condition), std::move(body), keyword.line, keyword.column
    );
}

StmtPtr Parser::forStatement() {
    Token keyword = advance(); // 消耗 for

    expect(TokenType::LEFT_PAREN, "Expected '(' after 'for'");

    // 初始化器
    StmtPtr initializer = nullptr;
    if (match({TokenType::SEMICOLON})) {
        // 无初始化器
    } else if (match({TokenType::LET, TokenType::VAR})) {
        initializer = varDeclaration();
    } else {
        initializer = expressionStatement();
    }

    // 条件
    ExprPtr condition = nullptr;
    if (!check(TokenType::SEMICOLON)) {
        condition = expression();
    }
    expect(TokenType::SEMICOLON, "Expected ';' after for condition");

    // 递增
    ExprPtr increment = nullptr;
    if (!check(TokenType::RIGHT_PAREN)) {
        increment = expression();
    }
    expect(TokenType::RIGHT_PAREN, "Expected ')' after for clauses");

    // 循环体
    StmtPtr body = statement();

    // 转换为while循环
    // for (init; cond; incr) body => { init; while (cond) { body; incr; } }
    std::vector<StmtPtr> stmts;

    if (initializer) {
        stmts.push_back(std::move(initializer));
    }

    // 创建包含body和increment的块
    std::vector<StmtPtr> bodyStmts;
    bodyStmts.push_back(std::move(body));
    if (increment) {
        bodyStmts.push_back(std::make_unique<ExprStmt>(std::move(increment)));
    }
    auto bodyBlock = std::make_unique<BlockStmt>(std::move(bodyStmts));

    // 如果没有条件，默认为true
    if (!condition) {
        condition = std::make_unique<LiteralExpr>(true, keyword.line, keyword.column);
    }

    auto whileStmt = std::make_unique<WhileStmt>(
        std::move(condition), std::move(bodyBlock), keyword.line, keyword.column
    );
    stmts.push_back(std::move(whileStmt));

    return std::make_unique<BlockStmt>(std::move(stmts), keyword.line, keyword.column);
}

StmtPtr Parser::returnStatement() {
    Token keyword = advance(); // 消耗 return

    ExprPtr value = nullptr;
    if (!check(TokenType::SEMICOLON) && !check(TokenType::RIGHT_BRACE)) {
        value = expression();
    }

    expect(TokenType::SEMICOLON, "Expected ';' after return value");

    return std::make_unique<ReturnStmt>(std::move(value), keyword.line, keyword.column);
}

StmtPtr Parser::printStatement() {
    Token keyword = advance(); // 消耗 print

    expect(TokenType::LEFT_PAREN, "Expected '(' after 'print'");

    std::vector<ExprPtr> arguments;
    if (!check(TokenType::RIGHT_PAREN)) {
        do {
            arguments.push_back(expression());
        } while (match({TokenType::COMMA}));
    }

    expect(TokenType::RIGHT_PAREN, "Expected ')' after print arguments");
    expect(TokenType::SEMICOLON, "Expected ';' after print statement");

    return std::make_unique<PrintStmt>(std::move(arguments), keyword.line, keyword.column);
}

StmtPtr Parser::breakStatement() {
    Token keyword = advance(); // 消耗 break
    expect(TokenType::SEMICOLON, "Expected ';' after 'break'");
    return std::make_unique<BreakStmt>(keyword.line, keyword.column);
}

StmtPtr Parser::continueStatement() {
    Token keyword = advance(); // 消耗 continue
    expect(TokenType::SEMICOLON, "Expected ';' after 'continue'");
    return std::make_unique<ContinueStmt>(keyword.line, keyword.column);
}

std::unique_ptr<BlockStmt> Parser::block() {
    expect(TokenType::LEFT_BRACE, "Expected '{'");

    std::vector<StmtPtr> statements;
    while (!check(TokenType::RIGHT_BRACE) && !isAtEnd()) {
        auto decl = declaration();
        if (decl) {
            statements.push_back(std::move(decl));
        }
    }

    expect(TokenType::RIGHT_BRACE, "Expected '}'");

    return std::make_unique<BlockStmt>(std::move(statements));
}

// ==================== 表达式解析 ====================

ExprPtr Parser::expression() {
    return assignment();
}

ExprPtr Parser::assignment() {
    ExprPtr expr = logicOr();

    if (match({TokenType::ASSIGN, TokenType::PLUS_ASSIGN, TokenType::MINUS_ASSIGN,
               TokenType::MUL_ASSIGN, TokenType::DIV_ASSIGN})) {
        Token op = previous();
        ExprPtr value = assignment(); // 右结合

        // 检查左值
        if (expr->exprType == ExprType::VARIABLE ||
            expr->exprType == ExprType::INDEX ||
            expr->exprType == ExprType::MEMBER) {
            return std::make_unique<AssignExpr>(
                std::move(expr), op, std::move(value), op.line, op.column
            );
        }

        error(op, "Invalid assignment target");
    }

    return expr;
}

ExprPtr Parser::logicOr() {
    ExprPtr expr = logicAnd();

    while (match({TokenType::OR})) {
        Token op = previous();
        ExprPtr right = logicAnd();
        expr = std::make_unique<LogicalExpr>(
            std::move(expr), op, std::move(right), op.line, op.column
        );
    }

    return expr;
}

ExprPtr Parser::logicAnd() {
    ExprPtr expr = equality();

    while (match({TokenType::AND})) {
        Token op = previous();
        ExprPtr right = equality();
        expr = std::make_unique<LogicalExpr>(
            std::move(expr), op, std::move(right), op.line, op.column
        );
    }

    return expr;
}

ExprPtr Parser::equality() {
    ExprPtr expr = comparison();

    while (match({TokenType::EQUAL, TokenType::NOT_EQUAL})) {
        Token op = previous();
        ExprPtr right = comparison();
        expr = std::make_unique<BinaryExpr>(
            std::move(expr), op, std::move(right), op.line, op.column
        );
    }

    return expr;
}

ExprPtr Parser::comparison() {
    ExprPtr expr = addition();

    while (match({TokenType::LESS, TokenType::LESS_EQUAL,
                  TokenType::GREATER, TokenType::GREATER_EQUAL})) {
        Token op = previous();
        ExprPtr right = addition();
        expr = std::make_unique<BinaryExpr>(
            std::move(expr), op, std::move(right), op.line, op.column
        );
    }

    return expr;
}

ExprPtr Parser::addition() {
    ExprPtr expr = multiplication();

    while (match({TokenType::PLUS, TokenType::MINUS})) {
        Token op = previous();
        ExprPtr right = multiplication();
        expr = std::make_unique<BinaryExpr>(
            std::move(expr), op, std::move(right), op.line, op.column
        );
    }

    return expr;
}

ExprPtr Parser::multiplication() {
    ExprPtr expr = unary();

    while (match({TokenType::MULTIPLY, TokenType::DIVIDE, TokenType::MODULO})) {
        Token op = previous();
        ExprPtr right = unary();
        expr = std::make_unique<BinaryExpr>(
            std::move(expr), op, std::move(right), op.line, op.column
        );
    }

    return expr;
}

ExprPtr Parser::unary() {
    if (match({TokenType::NOT, TokenType::MINUS, TokenType::INCREMENT, TokenType::DECREMENT})) {
        Token op = previous();
        ExprPtr operand = unary();
        return std::make_unique<UnaryExpr>(
            op, std::move(operand), true, op.line, op.column
        );
    }

    return postfix();
}

ExprPtr Parser::postfix() {
    ExprPtr expr = call();

    if (match({TokenType::INCREMENT, TokenType::DECREMENT})) {
        Token op = previous();
        return std::make_unique<UnaryExpr>(
            op, std::move(expr), false, op.line, op.column
        );
    }

    return expr;
}

ExprPtr Parser::call() {
    ExprPtr expr = primary();

    while (true) {
        if (match({TokenType::LEFT_PAREN})) {
            expr = finishCall(std::move(expr));
        } else if (match({TokenType::DOT})) {
            Token name = expect(TokenType::IDENTIFIER, "Expected property name after '.'");
            expr = std::make_unique<MemberExpr>(
                std::move(expr), name.lexeme, name.line, name.column
            );
        } else if (match({TokenType::LEFT_BRACKET})) {
            ExprPtr index = expression();
            expect(TokenType::RIGHT_BRACKET, "Expected ']'");
            expr = std::make_unique<IndexExpr>(
                std::move(expr), std::move(index), peek().line, peek().column
            );
        } else {
            break;
        }
    }

    return expr;
}

ExprPtr Parser::primary() {
    // 数字字面量
    if (match({TokenType::INTEGER})) {
        Token token = previous();
        return std::make_unique<LiteralExpr>(
            std::get<int64_t>(token.value), token.line, token.column
        );
    }

    if (match({TokenType::FLOAT})) {
        Token token = previous();
        return std::make_unique<LiteralExpr>(
            std::get<double>(token.value), token.line, token.column
        );
    }

    // 字符串字面量
    if (match({TokenType::STRING})) {
        Token token = previous();
        return std::make_unique<LiteralExpr>(
            std::get<std::string>(token.value), token.line, token.column
        );
    }

    // 布尔字面量
    if (match({TokenType::TRUE})) {
        Token token = previous();
        return std::make_unique<LiteralExpr>(true, token.line, token.column);
    }

    if (match({TokenType::FALSE})) {
        Token token = previous();
        return std::make_unique<LiteralExpr>(false, token.line, token.column);
    }

    // 标识符
    if (match({TokenType::IDENTIFIER})) {
        Token token = previous();
        return std::make_unique<VariableExpr>(token.lexeme, token.line, token.column);
    }

    // 括号表达式
    if (match({TokenType::LEFT_PAREN})) {
        ExprPtr expr = expression();
        expect(TokenType::RIGHT_PAREN, "Expected ')' after expression");
        return expr;
    }

    // 数组字面量
    if (match({TokenType::LEFT_BRACKET})) {
        std::vector<ExprPtr> elements;
        if (!check(TokenType::RIGHT_BRACKET)) {
            do {
                elements.push_back(expression());
            } while (match({TokenType::COMMA}));
        }
        expect(TokenType::RIGHT_BRACKET, "Expected ']'");
        return std::make_unique<ArrayLiteralExpr>(std::move(elements));
    }

    // new表达式
    if (match({TokenType::NEW})) {
        Token className = expect(TokenType::IDENTIFIER, "Expected class name after 'new'");
        expect(TokenType::LEFT_PAREN, "Expected '(' after class name");

        std::vector<ExprPtr> arguments;
        if (!check(TokenType::RIGHT_PAREN)) {
            do {
                arguments.push_back(expression());
            } while (match({TokenType::COMMA}));
        }
        expect(TokenType::RIGHT_PAREN, "Expected ')' after arguments");

        auto callee = std::make_unique<VariableExpr>(className.lexeme, className.line, className.column);
        return std::make_unique<CallExpr>(
            std::move(callee), std::move(arguments), className.line, className.column
        );
    }

    error(peek(), "Expected expression");
    return nullptr; // 不会执行到这里
}

// ==================== 辅助解析 ====================

std::shared_ptr<Type> Parser::typeAnnotation() {
    // 基本类型
    if (match({TokenType::INT_TYPE})) {
        return std::make_shared<Type>(TypeKind::INT);
    }
    if (match({TokenType::FLOAT_TYPE})) {
        return std::make_shared<Type>(TypeKind::FLOAT);
    }
    if (match({TokenType::STRING_TYPE})) {
        return std::make_shared<Type>(TypeKind::STRING);
    }
    if (match({TokenType::BOOL_TYPE})) {
        return std::make_shared<Type>(TypeKind::BOOL);
    }
    if (match({TokenType::VOID_TYPE})) {
        return std::make_shared<Type>(TypeKind::VOID);
    }

    // 自定义类型（类名）
    if (check(TokenType::IDENTIFIER)) {
        Token name = advance();
        // 这里简化处理，实际应该创建自定义类型
        return std::make_shared<Type>(TypeKind::CLASS);
    }

    error(peek(), "Expected type name");
    return nullptr;
}

std::vector<Parameter> Parser::parameters() {
    std::vector<Parameter> params;

    if (!check(TokenType::RIGHT_PAREN)) {
        do {
            Token name = expect(TokenType::IDENTIFIER, "Expected parameter name");
            expect(TokenType::COLON, "Expected ':' after parameter name");
            TypePtr type = typeAnnotation();

            ExprPtr defaultValue = nullptr;
            if (match({TokenType::ASSIGN})) {
                defaultValue = expression();
            }

            params.emplace_back(name.lexeme, std::move(type), std::move(defaultValue));
        } while (match({TokenType::COMMA}));
    }

    return params;
}

std::vector<ExprPtr> Parser::arguments() {
    std::vector<ExprPtr> args;

    if (!check(TokenType::RIGHT_PAREN)) {
        do {
            args.push_back(expression());
        } while (match({TokenType::COMMA}));
    }

    return args;
}

ExprPtr Parser::finishCall(ExprPtr callee) {
    std::vector<ExprPtr> args;
    if (!check(TokenType::RIGHT_PAREN)) {
        do {
            args.push_back(expression());
        } while (match({TokenType::COMMA}));
    }

    expect(TokenType::RIGHT_PAREN, "Expected ')' after arguments");

    return std::make_unique<CallExpr>(
        std::move(callee), std::move(args), peek().line, peek().column
    );
}

ExprPtr Parser::finishIndex(ExprPtr object) {
    ExprPtr index = expression();
    expect(TokenType::RIGHT_BRACKET, "Expected ']'");

    return std::make_unique<IndexExpr>(
        std::move(object), std::move(index), peek().line, peek().column
    );
}

} // namespace compiler
