#pragma once

#include "token.hpp"
#include <memory>
#include <vector>
#include <string>
#include <variant>
#include <iostream>
#include <sstream>

namespace compiler {

// 前向声明
struct Expr;
struct Stmt;
struct Type;

using ExprPtr = std::unique_ptr<Expr>;
using StmtPtr = std::unique_ptr<Stmt>;
using TypePtr = std::shared_ptr<Type>;

/**
 * 类型系统
 * 支持基本类型和复合类型
 */
enum class TypeKind {
    INT,
    FLOAT,
    STRING,
    BOOL,
    VOID,
    ARRAY,
    FUNCTION,
    CLASS,
    AUTO,       // 自动推导类型
};

struct Type {
    TypeKind kind;

    explicit Type(TypeKind kind) : kind(kind) {}
    virtual ~Type() = default;

    virtual std::string toString() const {
        switch (kind) {
            case TypeKind::INT: return "int";
            case TypeKind::FLOAT: return "float";
            case TypeKind::STRING: return "string";
            case TypeKind::BOOL: return "bool";
            case TypeKind::VOID: return "void";
            case TypeKind::AUTO: return "auto";
            default: return "unknown";
        }
    }

    virtual bool operator==(const Type& other) const {
        return kind == other.kind;
    }
};

/**
 * 数组类型
 */
struct ArrayType : public Type {
    TypePtr elementType;
    size_t size;  // 0表示动态大小

    ArrayType(TypePtr elementType, size_t size = 0)
        : Type(TypeKind::ARRAY), elementType(std::move(elementType)), size(size) {}

    std::string toString() const override {
        return elementType->toString() + "[]";
    }
};

/**
 * 函数类型
 */
struct FunctionType : public Type {
    std::vector<TypePtr> paramTypes;
    TypePtr returnType;

    FunctionType(std::vector<TypePtr> paramTypes, TypePtr returnType)
        : Type(TypeKind::FUNCTION),
          paramTypes(std::move(paramTypes)),
          returnType(std::move(returnType)) {}

    std::string toString() const override {
        std::string result = "fn(";
        for (size_t i = 0; i < paramTypes.size(); ++i) {
            if (i > 0) result += ", ";
            result += paramTypes[i]->toString();
        }
        result += ") -> " + returnType->toString();
        return result;
    }
};

/**
 * AST节点基类
 */
struct ASTNode {
    int line;
    int column;

    ASTNode(int line = 0, int column = 0) : line(line), column(column) {}
    virtual ~ASTNode() = default;

    virtual std::string toString() const = 0;
    virtual void print(int indent = 0) const = 0;

protected:
    void printIndent(int indent) const {
        for (int i = 0; i < indent; ++i) {
            std::cout << "  ";
        }
    }
};

// ==================== 表达式节点 ====================

/**
 * 表达式类型枚举
 */
enum class ExprType {
    LITERAL,
    BINARY,
    UNARY,
    VARIABLE,
    ASSIGN,
    CALL,
    INDEX,
    MEMBER,
    ARRAY_LITERAL,
    TERNARY,
    CAST,
    LOGICAL,
};

/**
 * 表达式基类
 */
struct Expr : public ASTNode {
    ExprType exprType;
    TypePtr type;  // 表达式的类型（语义分析后填充）

    Expr(ExprType exprType, int line = 0, int column = 0)
        : ASTNode(line, column), exprType(exprType) {}
};

/**
 * 字面量表达式
 * 支持整数、浮点数、字符串、布尔值
 */
struct LiteralExpr : public Expr {
    TokenValue value;

    LiteralExpr(TokenValue value, int line = 0, int column = 0)
        : Expr(ExprType::LITERAL, line, column), value(std::move(value)) {}

    std::string toString() const override {
        if (std::holds_alternative<int64_t>(value)) {
            return std::to_string(std::get<int64_t>(value));
        } else if (std::holds_alternative<double>(value)) {
            return std::to_string(std::get<double>(value));
        } else if (std::holds_alternative<std::string>(value)) {
            return "\"" + std::get<std::string>(value) + "\"";
        }
        return "null";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "LiteralExpr: " << toString() << std::endl;
    }
};

/**
 * 二元表达式
 * 如: a + b, x * y
 */
struct BinaryExpr : public Expr {
    ExprPtr left;
    Token op;
    ExprPtr right;

    BinaryExpr(ExprPtr left, Token op, ExprPtr right, int line = 0, int column = 0)
        : Expr(ExprType::BINARY, line, column),
          left(std::move(left)), op(std::move(op)), right(std::move(right)) {}

    std::string toString() const override {
        return "(" + left->toString() + " " + op.lexeme + " " + right->toString() + ")";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "BinaryExpr: " << op.lexeme << std::endl;
        left->print(indent + 1);
        right->print(indent + 1);
    }
};

/**
 * 一元表达式
 * 如: -x, !flag
 */
struct UnaryExpr : public Expr {
    Token op;
    ExprPtr operand;
    bool isPrefix;  // true表示前缀，false表示后缀

    UnaryExpr(Token op, ExprPtr operand, bool isPrefix, int line = 0, int column = 0)
        : Expr(ExprType::UNARY, line, column),
          op(std::move(op)), operand(std::move(operand)), isPrefix(isPrefix) {}

    std::string toString() const override {
        if (isPrefix) {
            return "(" + op.lexeme + operand->toString() + ")";
        }
        return "(" + operand->toString() + op.lexeme + ")";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "UnaryExpr: " << op.lexeme
                  << (isPrefix ? " (prefix)" : " (postfix)") << std::endl;
        operand->print(indent + 1);
    }
};

/**
 * 变量引用表达式
 */
struct VariableExpr : public Expr {
    std::string name;

    VariableExpr(const std::string& name, int line = 0, int column = 0)
        : Expr(ExprType::VARIABLE, line, column), name(name) {}

    std::string toString() const override {
        return name;
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "VariableExpr: " << name << std::endl;
    }
};

/**
 * 赋值表达式
 * 如: x = 10, arr[i] = value
 */
struct AssignExpr : public Expr {
    ExprPtr target;
    Token op;
    ExprPtr value;

    AssignExpr(ExprPtr target, Token op, ExprPtr value, int line = 0, int column = 0)
        : Expr(ExprType::ASSIGN, line, column),
          target(std::move(target)), op(std::move(op)), value(std::move(value)) {}

    std::string toString() const override {
        return target->toString() + " " + op.lexeme + " " + value->toString();
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "AssignExpr: " << op.lexeme << std::endl;
        target->print(indent + 1);
        value->print(indent + 1);
    }
};

/**
 * 函数调用表达式
 * 如: foo(1, 2), obj.method()
 */
struct CallExpr : public Expr {
    ExprPtr callee;
    std::vector<ExprPtr> arguments;

    CallExpr(ExprPtr callee, std::vector<ExprPtr> arguments, int line = 0, int column = 0)
        : Expr(ExprType::CALL, line, column),
          callee(std::move(callee)), arguments(std::move(arguments)) {}

    std::string toString() const override {
        std::string result = callee->toString() + "(";
        for (size_t i = 0; i < arguments.size(); ++i) {
            if (i > 0) result += ", ";
            result += arguments[i]->toString();
        }
        result += ")";
        return result;
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "CallExpr" << std::endl;
        printIndent(indent + 1);
        std::cout << "Callee:" << std::endl;
        callee->print(indent + 2);
        if (!arguments.empty()) {
            printIndent(indent + 1);
            std::cout << "Arguments:" << std::endl;
            for (const auto& arg : arguments) {
                arg->print(indent + 2);
            }
        }
    }
};

/**
 * 数组索引表达式
 * 如: arr[i], matrix[j][k]
 */
struct IndexExpr : public Expr {
    ExprPtr object;
    ExprPtr index;

    IndexExpr(ExprPtr object, ExprPtr index, int line = 0, int column = 0)
        : Expr(ExprType::INDEX, line, column),
          object(std::move(object)), index(std::move(index)) {}

    std::string toString() const override {
        return object->toString() + "[" + index->toString() + "]";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "IndexExpr" << std::endl;
        object->print(indent + 1);
        index->print(indent + 1);
    }
};

/**
 * 成员访问表达式
 * 如: obj.field, this.value
 */
struct MemberExpr : public Expr {
    ExprPtr object;
    std::string member;

    MemberExpr(ExprPtr object, const std::string& member, int line = 0, int column = 0)
        : Expr(ExprType::MEMBER, line, column),
          object(std::move(object)), member(member) {}

    std::string toString() const override {
        return object->toString() + "." + member;
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "MemberExpr: ." << member << std::endl;
        object->print(indent + 1);
    }
};

/**
 * 数组字面量表达式
 * 如: [1, 2, 3], ["a", "b"]
 */
struct ArrayLiteralExpr : public Expr {
    std::vector<ExprPtr> elements;

    ArrayLiteralExpr(std::vector<ExprPtr> elements, int line = 0, int column = 0)
        : Expr(ExprType::ARRAY_LITERAL, line, column),
          elements(std::move(elements)) {}

    std::string toString() const override {
        std::string result = "[";
        for (size_t i = 0; i < elements.size(); ++i) {
            if (i > 0) result += ", ";
            result += elements[i]->toString();
        }
        result += "]";
        return result;
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "ArrayLiteralExpr" << std::endl;
        for (const auto& elem : elements) {
            elem->print(indent + 1);
        }
    }
};

/**
 * 三元表达式
 * 如: condition ? true_expr : false_expr
 */
struct TernaryExpr : public Expr {
    ExprPtr condition;
    ExprPtr trueExpr;
    ExprPtr falseExpr;

    TernaryExpr(ExprPtr condition, ExprPtr trueExpr, ExprPtr falseExpr,
                int line = 0, int column = 0)
        : Expr(ExprType::TERNARY, line, column),
          condition(std::move(condition)),
          trueExpr(std::move(trueExpr)),
          falseExpr(std::move(falseExpr)) {}

    std::string toString() const override {
        return "(" + condition->toString() + " ? " +
               trueExpr->toString() + " : " + falseExpr->toString() + ")";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "TernaryExpr" << std::endl;
        condition->print(indent + 1);
        trueExpr->print(indent + 1);
        falseExpr->print(indent + 1);
    }
};

/**
 * 类型转换表达式
 * 如: x as int, value as float
 */
struct CastExpr : public Expr {
    ExprPtr expr;
    TypePtr targetType;

    CastExpr(ExprPtr expr, TypePtr targetType, int line = 0, int column = 0)
        : Expr(ExprType::CAST, line, column),
          expr(std::move(expr)), targetType(std::move(targetType)) {}

    std::string toString() const override {
        return "(" + expr->toString() + " as " + targetType->toString() + ")";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "CastExpr: as " << targetType->toString() << std::endl;
        expr->print(indent + 1);
    }
};

/**
 * 逻辑表达式
 * 如: a && b, x || y
 */
struct LogicalExpr : public Expr {
    ExprPtr left;
    Token op;
    ExprPtr right;

    LogicalExpr(ExprPtr left, Token op, ExprPtr right, int line = 0, int column = 0)
        : Expr(ExprType::LOGICAL, line, column),
          left(std::move(left)), op(std::move(op)), right(std::move(right)) {}

    std::string toString() const override {
        return "(" + left->toString() + " " + op.lexeme + " " + right->toString() + ")";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "LogicalExpr: " << op.lexeme << std::endl;
        left->print(indent + 1);
        right->print(indent + 1);
    }
};

// ==================== 语句节点 ====================

/**
 * 语句类型枚举
 */
enum class StmtType {
    EXPR_STMT,
    VAR_DECL,
    BLOCK,
    IF,
    WHILE,
    FOR,
    RETURN,
    FUNCTION,
    CLASS,
    PRINT,
    BREAK,
    CONTINUE,
    IMPORT,
};

/**
 * 语句基类
 */
struct Stmt : public ASTNode {
    StmtType stmtType;

    Stmt(StmtType stmtType, int line = 0, int column = 0)
        : ASTNode(line, column), stmtType(stmtType) {}
};

/**
 * 表达式语句
 * 如: foo(); x = 10;
 */
struct ExprStmt : public Stmt {
    ExprPtr expression;

    ExprStmt(ExprPtr expression, int line = 0, int column = 0)
        : Stmt(StmtType::EXPR_STMT, line, column),
          expression(std::move(expression)) {}

    std::string toString() const override {
        return expression->toString() + ";";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "ExprStmt" << std::endl;
        expression->print(indent + 1);
    }
};

/**
 * 变量声明语句
 * 如: let x: int = 10; var y = "hello";
 */
struct VarDeclStmt : public Stmt {
    std::string name;
    std::shared_ptr<Type> type;
    ExprPtr initializer;
    bool isConst;
    bool isVar;  // true表示var，false表示let

    VarDeclStmt(const std::string& name, std::shared_ptr<Type> type, ExprPtr initializer,
                bool isConst, bool isVar, int line = 0, int column = 0)
        : Stmt(StmtType::VAR_DECL, line, column),
          name(name), type(std::move(type)),
          initializer(std::move(initializer)),
          isConst(isConst), isVar(isVar) {}

    std::string toString() const override {
        std::string result = isConst ? "const " : (isVar ? "var " : "let ");
        result += name;
        if (type) {
            result += ": " + type->toString();
        }
        if (initializer) {
            result += " = " + initializer->toString();
        }
        return result + ";";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "VarDeclStmt: " << name
                  << (isConst ? " (const)" : "")
                  << (isVar ? " (var)" : " (let)") << std::endl;
        if (type) {
            printIndent(indent + 1);
            std::cout << "Type: " << type->toString() << std::endl;
        }
        if (initializer) {
            printIndent(indent + 1);
            std::cout << "Initializer:" << std::endl;
            initializer->print(indent + 2);
        }
    }
};

/**
 * 块语句
 * 如: { stmt1; stmt2; }
 */
struct BlockStmt : public Stmt {
    std::vector<StmtPtr> statements;

    BlockStmt(std::vector<StmtPtr> statements, int line = 0, int column = 0)
        : Stmt(StmtType::BLOCK, line, column),
          statements(std::move(statements)) {}

    std::string toString() const override {
        return "{ ... }";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "BlockStmt" << std::endl;
        for (const auto& stmt : statements) {
            stmt->print(indent + 1);
        }
    }
};

/**
 * if语句
 * 如: if (cond) { ... } else { ... }
 */
struct IfStmt : public Stmt {
    ExprPtr condition;
    StmtPtr thenBranch;
    StmtPtr elseBranch;  // 可选

    IfStmt(ExprPtr condition, StmtPtr thenBranch, StmtPtr elseBranch,
           int line = 0, int column = 0)
        : Stmt(StmtType::IF, line, column),
          condition(std::move(condition)),
          thenBranch(std::move(thenBranch)),
          elseBranch(std::move(elseBranch)) {}

    std::string toString() const override {
        std::string result = "if (" + condition->toString() + ") { ... }";
        if (elseBranch) {
            result += " else { ... }";
        }
        return result;
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "IfStmt" << std::endl;
        printIndent(indent + 1);
        std::cout << "Condition:" << std::endl;
        condition->print(indent + 2);
        printIndent(indent + 1);
        std::cout << "Then:" << std::endl;
        thenBranch->print(indent + 2);
        if (elseBranch) {
            printIndent(indent + 1);
            std::cout << "Else:" << std::endl;
            elseBranch->print(indent + 2);
        }
    }
};

/**
 * while循环语句
 * 如: while (cond) { ... }
 */
struct WhileStmt : public Stmt {
    ExprPtr condition;
    StmtPtr body;

    WhileStmt(ExprPtr condition, StmtPtr body, int line = 0, int column = 0)
        : Stmt(StmtType::WHILE, line, column),
          condition(std::move(condition)), body(std::move(body)) {}

    std::string toString() const override {
        return "while (" + condition->toString() + ") { ... }";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "WhileStmt" << std::endl;
        printIndent(indent + 1);
        std::cout << "Condition:" << std::endl;
        condition->print(indent + 2);
        printIndent(indent + 1);
        std::cout << "Body:" << std::endl;
        body->print(indent + 2);
    }
};

/**
 * for循环语句
 * 如: for (let i = 0; i < 10; i++) { ... }
 */
struct ForStmt : public Stmt {
    StmtPtr initializer;
    ExprPtr condition;
    ExprPtr increment;
    StmtPtr body;

    ForStmt(StmtPtr initializer, ExprPtr condition, ExprPtr increment,
            StmtPtr body, int line = 0, int column = 0)
        : Stmt(StmtType::FOR, line, column),
          initializer(std::move(initializer)),
          condition(std::move(condition)),
          increment(std::move(increment)),
          body(std::move(body)) {}

    std::string toString() const override {
        return "for (...) { ... }";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "ForStmt" << std::endl;
        if (initializer) {
            printIndent(indent + 1);
            std::cout << "Initializer:" << std::endl;
            initializer->print(indent + 2);
        }
        if (condition) {
            printIndent(indent + 1);
            std::cout << "Condition:" << std::endl;
            condition->print(indent + 2);
        }
        if (increment) {
            printIndent(indent + 1);
            std::cout << "Increment:" << std::endl;
            increment->print(indent + 2);
        }
        printIndent(indent + 1);
        std::cout << "Body:" << std::endl;
        body->print(indent + 2);
    }
};

/**
 * return语句
 * 如: return x; return;
 */
struct ReturnStmt : public Stmt {
    ExprPtr value;  // 可选

    ReturnStmt(ExprPtr value, int line = 0, int column = 0)
        : Stmt(StmtType::RETURN, line, column), value(std::move(value)) {}

    std::string toString() const override {
        if (value) {
            return "return " + value->toString() + ";";
        }
        return "return;";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "ReturnStmt" << std::endl;
        if (value) {
            value->print(indent + 1);
        }
    }
};

/**
 * 函数参数
 */
struct Parameter {
    std::string name;
    std::shared_ptr<Type> type;
    std::shared_ptr<Expr> defaultValue;  // 可选

    Parameter(const std::string& name, std::shared_ptr<Type> type, std::shared_ptr<Expr> defaultValue = nullptr)
        : name(name), type(std::move(type)), defaultValue(std::move(defaultValue)) {}
};

/**
 * 函数声明语句
 * 如: fn add(a: int, b: int): int { return a + b; }
 */
struct FunctionStmt : public Stmt {
    std::string name;
    std::vector<Parameter> params;
    std::shared_ptr<Type> returnType;
    StmtPtr body;

    FunctionStmt(const std::string& name, std::vector<Parameter> params,
                 std::shared_ptr<Type> returnType, StmtPtr body, int line = 0, int column = 0)
        : Stmt(StmtType::FUNCTION, line, column),
          name(name), params(std::move(params)),
          returnType(std::move(returnType)), body(std::move(body)) {}

    std::string toString() const override {
        std::string result = "fn " + name + "(";
        for (size_t i = 0; i < params.size(); ++i) {
            if (i > 0) result += ", ";
            result += params[i].name + ": " + params[i].type->toString();
        }
        result += ")";
        if (returnType) {
            result += ": " + returnType->toString();
        }
        return result + " { ... }";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "FunctionStmt: " << name << std::endl;
        printIndent(indent + 1);
        std::cout << "Parameters:" << std::endl;
        for (const auto& param : params) {
            printIndent(indent + 2);
            std::cout << param.name << ": " << param.type->toString() << std::endl;
        }
        if (returnType) {
            printIndent(indent + 1);
            std::cout << "Return Type: " << returnType->toString() << std::endl;
        }
        printIndent(indent + 1);
        std::cout << "Body:" << std::endl;
        body->print(indent + 2);
    }
};

/**
 * 类成员
 */
struct ClassMember {
    bool isMethod;
    std::string name;
    TypePtr type;           // 字段类型
    FunctionStmt* method;  // 方法（如果isMethod为true）
    ExprPtr initializer;   // 字段初始化器

    ClassMember(const std::string& name, std::shared_ptr<Type> type, ExprPtr initializer = nullptr)
        : isMethod(false), name(name), type(std::move(type)),
          method(nullptr), initializer(std::move(initializer)) {}

    ClassMember(const std::string& name, FunctionStmt* method)
        : isMethod(true), name(name), method(method) {}
};

/**
 * 类声明语句
 * 如: class Point { x: int; y: int; fn init(x: int, y: int) { ... } }
 */
struct ClassStmt : public Stmt {
    std::string name;
    std::string parent;  // 父类名（可选）
    std::vector<ClassMember> members;

    ClassStmt(const std::string& name, const std::string& parent,
              std::vector<ClassMember> members, int line = 0, int column = 0)
        : Stmt(StmtType::CLASS, line, column),
          name(name), parent(parent), members(std::move(members)) {}

    std::string toString() const override {
        std::string result = "class " + name;
        if (!parent.empty()) {
            result += " extends " + parent;
        }
        return result + " { ... }";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "ClassStmt: " << name;
        if (!parent.empty()) {
            std::cout << " extends " << parent;
        }
        std::cout << std::endl;
        for (const auto& member : members) {
            if (member.isMethod) {
                member.method->print(indent + 1);
            } else {
                printIndent(indent + 1);
                std::cout << "Field: " << member.name << ": "
                          << member.type->toString() << std::endl;
            }
        }
    }
};

/**
 * print语句
 * 如: print("hello", x, y);
 */
struct PrintStmt : public Stmt {
    std::vector<ExprPtr> arguments;

    PrintStmt(std::vector<ExprPtr> arguments, int line = 0, int column = 0)
        : Stmt(StmtType::PRINT, line, column),
          arguments(std::move(arguments)) {}

    std::string toString() const override {
        return "print(...);";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "PrintStmt" << std::endl;
        for (const auto& arg : arguments) {
            arg->print(indent + 1);
        }
    }
};

/**
 * break语句
 */
struct BreakStmt : public Stmt {
    BreakStmt(int line = 0, int column = 0)
        : Stmt(StmtType::BREAK, line, column) {}

    std::string toString() const override {
        return "break;";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "BreakStmt" << std::endl;
    }
};

/**
 * continue语句
 */
struct ContinueStmt : public Stmt {
    ContinueStmt(int line = 0, int column = 0)
        : Stmt(StmtType::CONTINUE, line, column) {}

    std::string toString() const override {
        return "continue;";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "ContinueStmt" << std::endl;
    }
};

/**
 * import语句
 * 如: import "module"; import { foo, bar } from "module";
 */
struct ImportStmt : public Stmt {
    std::string module;
    std::vector<std::string> names;  // 导入的名称列表，空表示导入全部

    ImportStmt(const std::string& module, std::vector<std::string> names,
               int line = 0, int column = 0)
        : Stmt(StmtType::IMPORT, line, column),
          module(module), names(std::move(names)) {}

    std::string toString() const override {
        if (names.empty()) {
            return "import \"" + module + "\";";
        }
        std::string result = "import { ";
        for (size_t i = 0; i < names.size(); ++i) {
            if (i > 0) result += ", ";
            result += names[i];
        }
        return result + " } from \"" + module + "\";";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "ImportStmt: " << module << std::endl;
        if (!names.empty()) {
            for (const auto& name : names) {
                printIndent(indent + 1);
                std::cout << name << std::endl;
            }
        }
    }
};

/**
 * 程序根节点
 * 包含所有顶层声明
 */
struct Program : public ASTNode {
    std::vector<StmtPtr> statements;

    Program() : ASTNode(0, 0) {}

    std::string toString() const override {
        return "Program";
    }

    void print(int indent = 0) const override {
        printIndent(indent);
        std::cout << "Program" << std::endl;
        for (const auto& stmt : statements) {
            stmt->print(indent + 1);
        }
    }
};

} // namespace compiler
