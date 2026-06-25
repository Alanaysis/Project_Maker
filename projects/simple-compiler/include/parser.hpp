#pragma once

#include "lexer.hpp"
#include "ast.hpp"
#include <memory>
#include <vector>
#include <functional>

namespace compiler {

/**
 * 语法分析器 (Parser)
 *
 * 职责：
 * 1. 将token流转换为抽象语法树(AST)
 * 2. 处理运算符优先级和结合性
 * 3. 实现递归下降解析
 * 4. 错误恢复
 *
 * 语法规则（EBNF）：
 * program     -> declaration* EOF
 * declaration -> varDecl | funDecl | classDecl | statement
 * varDecl     -> (let|var|const) IDENTIFIER (':' type)? ('=' expression)? ';'
 * funDecl     -> 'fn' IDENTIFIER '(' parameters? ')' (':' type)? block
 * classDecl   -> 'class' IDENTIFIER ('extends' IDENTIFIER)? '{' member* '}'
 * statement   -> exprStmt | ifStmt | whileStmt | forStmt | returnStmt | block | printStmt
 * expression  -> assignment
 * assignment  -> (call '.')? IDENTIFIER '=' assignment | logicOr
 * logicOr     -> logicAnd ('||' logicAnd)*
 * logicAnd    -> equality ('&&' equality)*
 * equality    -> comparison (('==' | '!=') comparison)*
 * comparison  -> addition (('<' | '>' | '<=' | '>=') addition)*
 * addition    -> multiplication (('+' | '-') multiplication)*
 * multiplication -> unary (('*' | '/' | '%') unary)*
 * unary       -> ('!' | '-' | '++' | '--') unary | postfix
 * postfix     -> call ('++' | '--')?
 * call        -> primary ('(' arguments? ')' | '.' IDENTIFIER | '[' expression ']')*
 * primary     -> INTEGER | FLOAT | STRING | 'true' | 'false' | 'nil'
 *             | IDENTIFIER | '(' expression ')' | arrayLiteral
 */
class Parser {
public:
    /**
     * 构造函数
     * @param tokens token列表
     */
    explicit Parser(std::vector<Token> tokens);

    /**
     * 解析程序
     * @return AST根节点
     */
    std::unique_ptr<Program> parse();

    /**
     * 获取错误信息
     */
    const std::vector<std::string>& getErrors() const { return errors_; }

private:
    // token列表和当前位置
    std::vector<Token> tokens_;
    size_t current_;

    // 错误信息
    std::vector<std::string> errors_;

    // 错误恢复标志
    bool panicMode_;

    // 辅助方法

    /**
     * 查看当前token
     */
    const Token& peek() const;

    /**
     * 查看前一个token
     */
    const Token& previous() const;

    /**
     * 消耗并返回当前token
     */
    Token advance();

    /**
     * 检查当前token是否匹配预期类型
     */
    bool check(TokenType type) const;

    /**
     * 检查当前token是否匹配多个类型中的一个
     */
    bool match(std::initializer_list<TokenType> types);

    /**
     * 消耗预期类型的token，否则报错
     */
    Token expect(TokenType type, const std::string& message);

    /**
     * 检查是否到达token流末尾
     */
    bool isAtEnd() const;

    /**
     * 报告错误
     */
    void error(const Token& token, const std::string& message);

    /**
     * 错误恢复：跳到下一个语句边界
     */
    void synchronize();

    // ==================== 解析方法 ====================

    // 顶层声明
    StmtPtr declaration();
    StmtPtr varDeclaration();
    StmtPtr functionDeclaration();
    StmtPtr classDeclaration();

    // 语句
    StmtPtr statement();
    StmtPtr expressionStatement();
    StmtPtr ifStatement();
    StmtPtr whileStatement();
    StmtPtr forStatement();
    StmtPtr returnStatement();
    StmtPtr printStatement();
    StmtPtr breakStatement();
    StmtPtr continueStatement();
    std::unique_ptr<BlockStmt> block();

    // 表达式（按优先级从低到高）
    ExprPtr expression();
    ExprPtr assignment();
    ExprPtr logicOr();
    ExprPtr logicAnd();
    ExprPtr equality();
    ExprPtr comparison();
    ExprPtr addition();
    ExprPtr multiplication();
    ExprPtr unary();
    ExprPtr postfix();
    ExprPtr call();
    ExprPtr primary();

    // 辅助解析
    std::shared_ptr<Type> typeAnnotation();
    std::vector<Parameter> parameters();
    std::vector<ExprPtr> arguments();
    ClassMember classMember();

    // 表达式解析辅助
    ExprPtr finishCall(ExprPtr callee);
    ExprPtr finishIndex(ExprPtr object);
};

} // namespace compiler
