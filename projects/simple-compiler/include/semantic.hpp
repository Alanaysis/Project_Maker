#pragma once

#include "ast.hpp"
#include <memory>
#include <unordered_map>
#include <vector>
#include <string>

namespace compiler {

/**
 * 符号信息
 */
struct Symbol {
    std::string name;
    std::shared_ptr<Type> type;
    bool isConst;
    bool isVar;
    bool isFunction;
    bool isClass;
    bool isParameter;
    int scopeLevel;

    // 函数特有
    std::vector<std::shared_ptr<Type>> paramTypes;
    std::shared_ptr<Type> returnType;

    Symbol() : isConst(false), isVar(false), isFunction(false),
               isClass(false), isParameter(false), scopeLevel(0) {}
};

/**
 * 作用域
 * 管理变量的可见性和生命周期
 */
class Scope {
public:
    /**
     * 构造函数
     * @param parent 父作用域
     * @param level 作用域层级
     */
    explicit Scope(std::shared_ptr<Scope> parent = nullptr, int level = 0)
        : parent_(parent), level_(level) {}

    /**
     * 在当前作用域定义符号
     */
    bool define(const std::string& name, const Symbol& symbol);

    /**
     * 在当前作用域及父作用域中查找符号
     */
    Symbol* resolve(const std::string& name);

    /**
     * 仅在当前作用域查找符号
     */
    Symbol* resolveLocal(const std::string& name);

    /**
     * 获取父作用域
     */
    std::shared_ptr<Scope> getParent() const { return parent_; }

    /**
     * 获取作用域层级
     */
    int getLevel() const { return level_; }

private:
    std::unordered_map<std::string, Symbol> symbols_;
    std::shared_ptr<Scope> parent_;
    int level_;
};

/**
 * 语义分析器
 *
 * 职责：
 * 1. 类型检查
 * 2. 作用域分析
 * 3. 名称解析
 * 4. 类型推导
 * 5. 语义错误报告
 */
class SemanticAnalyzer {
public:
    SemanticAnalyzer();

    /**
     * 分析AST
     * @param program AST根节点
     * @return 是否有错误
     */
    bool analyze(Program& program);

    /**
     * 获取错误信息
     */
    const std::vector<std::string>& getErrors() const { return errors_; }

    /**
     * 获取警告信息
     */
    const std::vector<std::string>& getWarnings() const { return warnings_; }

private:
    // 作用域栈
    std::shared_ptr<Scope> currentScope_;
    int scopeLevel_;

    // 当前函数（用于return语句检查）
    FunctionStmt* currentFunction_;

    // 当前类（用于this引用检查）
    ClassStmt* currentClass_;

    // 循环深度（用于break/continue检查）
    int loopDepth_;

    // 错误和警告
    std::vector<std::string> errors_;
    std::vector<std::string> warnings_;

    // 辅助方法

    /**
     * 进入新作用域
     */
    void enterScope();

    /**
     * 离开当前作用域
     */
    void leaveScope();

    /**
     * 报告错误
     */
    void error(int line, int column, const std::string& message);

    /**
     * 报告警告
     */
    void warning(int line, int column, const std::string& message);

    /**
     * 检查类型是否兼容
     */
    bool isCompatible(const Type& left, const Type& right) const;

    /**
     * 获取表达式的类型
     */
    TypePtr getType(const Expr& expr);

    /**
     * 推导表达式的类型
     */
    TypePtr inferType(const Expr& expr);

    /**
     * 检查类型并填充表达式的type字段
     */
    TypePtr checkExpr(Expr& expr);

    // 语句分析
    void analyzeStmt(Stmt& stmt);
    void analyzeVarDecl(VarDeclStmt& stmt);
    void analyzeFunction(FunctionStmt& stmt);
    void analyzeClass(ClassStmt& stmt);
    void analyzeBlock(BlockStmt& stmt);
    void analyzeIf(IfStmt& stmt);
    void analyzeWhile(WhileStmt& stmt);
    void analyzeFor(ForStmt& stmt);
    void analyzeReturn(ReturnStmt& stmt);
    void analyzePrint(PrintStmt& stmt);
    void analyzeExprStmt(ExprStmt& stmt);

    // 表达式分析
    TypePtr analyzeExpr(Expr& expr);
    TypePtr analyzeLiteral(LiteralExpr& expr);
    TypePtr analyzeBinary(BinaryExpr& expr);
    TypePtr analyzeUnary(UnaryExpr& expr);
    TypePtr analyzeVariable(VariableExpr& expr);
    TypePtr analyzeAssign(AssignExpr& expr);
    TypePtr analyzeCall(CallExpr& expr);
    TypePtr analyzeIndex(IndexExpr& expr);
    TypePtr analyzeMember(MemberExpr& expr);
    TypePtr analyzeLogical(LogicalExpr& expr);
    TypePtr analyzeTernary(TernaryExpr& expr);
    TypePtr analyzeCast(CastExpr& expr);
};

} // namespace compiler
