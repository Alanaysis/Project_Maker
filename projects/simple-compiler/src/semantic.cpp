#include "semantic.hpp"
#include <algorithm>

namespace compiler {

// ==================== Scope ====================

bool Scope::define(const std::string& name, const Symbol& symbol) {
    if (symbols_.find(name) != symbols_.end()) {
        return false; // 重复定义
    }
    symbols_[name] = symbol;
    symbols_[name].scopeLevel = level_;
    return true;
}

Symbol* Scope::resolve(const std::string& name) {
    auto it = symbols_.find(name);
    if (it != symbols_.end()) {
        return &it->second;
    }

    if (parent_) {
        return parent_->resolve(name);
    }

    return nullptr;
}

Symbol* Scope::resolveLocal(const std::string& name) {
    auto it = symbols_.find(name);
    if (it != symbols_.end()) {
        return &it->second;
    }
    return nullptr;
}

// ==================== SemanticAnalyzer ====================

SemanticAnalyzer::SemanticAnalyzer()
    : currentScope_(nullptr), scopeLevel_(0),
      currentFunction_(nullptr), currentClass_(nullptr), loopDepth_(0) {}

bool SemanticAnalyzer::analyze(Program& program) {
    // 创建全局作用域
    enterScope();

    // 注册内置函数
    Symbol printSym;
    printSym.name = "print";
    printSym.isFunction = true;
    printSym.returnType = std::make_unique<Type>(TypeKind::VOID);
    currentScope_->define("print", printSym);

    Symbol lenSym;
    lenSym.name = "len";
    lenSym.isFunction = true;
    lenSym.returnType = std::make_unique<Type>(TypeKind::INT);
    currentScope_->define("len", lenSym);

    Symbol strSym;
    strSym.name = "str";
    strSym.isFunction = true;
    strSym.returnType = std::make_unique<Type>(TypeKind::STRING);
    currentScope_->define("str", strSym);

    // 分析所有语句
    for (auto& stmt : program.statements) {
        if (stmt) {
            analyzeStmt(*stmt);
        }
    }

    leaveScope();

    return errors_.empty();
}

void SemanticAnalyzer::enterScope() {
    scopeLevel_++;
    currentScope_ = std::make_shared<Scope>(currentScope_, scopeLevel_);
}

void SemanticAnalyzer::leaveScope() {
    scopeLevel_--;
    currentScope_ = currentScope_->getParent();
}

void SemanticAnalyzer::error(int line, int column, const std::string& message) {
    errors_.push_back("Semantic error at line " + std::to_string(line) +
                      ", column " + std::to_string(column) + ": " + message);
}

void SemanticAnalyzer::warning(int line, int column, const std::string& message) {
    warnings_.push_back("Warning at line " + std::to_string(line) +
                        ", column " + std::to_string(column) + ": " + message);
}

bool SemanticAnalyzer::isCompatible(const Type& left, const Type& right) const {
    // 相同类型
    if (left.kind == right.kind) {
        return true;
    }

    // 数字类型兼容
    if ((left.kind == TypeKind::INT || left.kind == TypeKind::FLOAT) &&
        (right.kind == TypeKind::INT || right.kind == TypeKind::FLOAT)) {
        return true;
    }

    // AUTO类型与任何类型兼容
    if (left.kind == TypeKind::AUTO || right.kind == TypeKind::AUTO) {
        return true;
    }

    return false;
}

void SemanticAnalyzer::analyzeStmt(Stmt& stmt) {
    switch (stmt.stmtType) {
        case StmtType::VAR_DECL:
            analyzeVarDecl(static_cast<VarDeclStmt&>(stmt));
            break;
        case StmtType::FUNCTION:
            analyzeFunction(static_cast<FunctionStmt&>(stmt));
            break;
        case StmtType::CLASS:
            analyzeClass(static_cast<ClassStmt&>(stmt));
            break;
        case StmtType::BLOCK:
            analyzeBlock(static_cast<BlockStmt&>(stmt));
            break;
        case StmtType::IF:
            analyzeIf(static_cast<IfStmt&>(stmt));
            break;
        case StmtType::WHILE:
            analyzeWhile(static_cast<WhileStmt&>(stmt));
            break;
        case StmtType::FOR:
            analyzeFor(static_cast<ForStmt&>(stmt));
            break;
        case StmtType::RETURN:
            analyzeReturn(static_cast<ReturnStmt&>(stmt));
            break;
        case StmtType::PRINT:
            analyzePrint(static_cast<PrintStmt&>(stmt));
            break;
        case StmtType::EXPR_STMT:
            analyzeExprStmt(static_cast<ExprStmt&>(stmt));
            break;
        case StmtType::BREAK:
            if (loopDepth_ == 0) {
                error(stmt.line, stmt.column, "'break' outside of loop");
            }
            break;
        case StmtType::CONTINUE:
            if (loopDepth_ == 0) {
                error(stmt.line, stmt.column, "'continue' outside of loop");
            }
            break;
        default:
            break;
    }
}

void SemanticAnalyzer::analyzeVarDecl(VarDeclStmt& stmt) {
    // 检查重复定义
    if (currentScope_->resolveLocal(stmt.name)) {
        error(stmt.line, stmt.column,
              "Variable '" + stmt.name + "' already defined in this scope");
        return;
    }

    // 分析初始化器
    TypePtr initType = nullptr;
    if (stmt.initializer) {
        initType = analyzeExpr(*stmt.initializer);
    }

    // 类型检查
    if (stmt.type && initType) {
        if (!isCompatible(*stmt.type, *initType)) {
            error(stmt.line, stmt.column,
                  "Type mismatch: cannot initialize '" + stmt.name + "' of type '" +
                  stmt.type->toString() + "' with value of type '" +
                  initType->toString() + "'");
        }
    }

    // 确定变量类型
    TypePtr varType = stmt.type ? std::move(stmt.type) : std::move(initType);
    if (!varType) {
        varType = std::make_unique<Type>(TypeKind::AUTO);
    }

    // 注册到符号表
    Symbol symbol;
    symbol.name = stmt.name;
    symbol.type = std::move(varType);
    symbol.isConst = stmt.isConst;
    symbol.isVar = stmt.isVar;

    if (!currentScope_->define(stmt.name, symbol)) {
        error(stmt.line, stmt.column,
              "Failed to define variable '" + stmt.name + "'");
    }
}

void SemanticAnalyzer::analyzeFunction(FunctionStmt& stmt) {
    // 检查重复定义
    if (currentScope_->resolveLocal(stmt.name)) {
        error(stmt.line, stmt.column,
              "Function '" + stmt.name + "' already defined in this scope");
        return;
    }

    // 注册函数到当前作用域（允许递归调用）
    Symbol funcSym;
    funcSym.name = stmt.name;
    funcSym.isFunction = true;
    funcSym.returnType = stmt.returnType ?
        std::make_unique<Type>(stmt.returnType->kind) :
        std::make_unique<Type>(TypeKind::VOID);

    for (const auto& param : stmt.params) {
        funcSym.paramTypes.push_back(std::make_unique<Type>(param.type->kind));
    }

    currentScope_->define(stmt.name, funcSym);

    // 分析函数体
    FunctionStmt* prevFunction = currentFunction_;
    currentFunction_ = &stmt;

    enterScope();

    // 注册参数
    for (const auto& param : stmt.params) {
        Symbol paramSym;
        paramSym.name = param.name;
        paramSym.type = std::make_unique<Type>(param.type->kind);
        paramSym.isParameter = true;

        if (!currentScope_->define(param.name, paramSym)) {
            error(stmt.line, stmt.column,
                  "Duplicate parameter name '" + param.name + "'");
        }
    }

    // 分析函数体
    if (stmt.body) {
        analyzeStmt(*stmt.body);
    }

    leaveScope();
    currentFunction_ = prevFunction;
}

void SemanticAnalyzer::analyzeClass(ClassStmt& stmt) {
    // 检查重复定义
    if (currentScope_->resolveLocal(stmt.name)) {
        error(stmt.line, stmt.column,
              "Class '" + stmt.name + "' already defined in this scope");
        return;
    }

    // 注册类到当前作用域
    Symbol classSym;
    classSym.name = stmt.name;
    classSym.isClass = true;
    classSym.type = std::make_unique<Type>(TypeKind::CLASS);

    currentScope_->define(stmt.name, classSym);

    // 分析类成员
    ClassStmt* prevClass = currentClass_;
    currentClass_ = &stmt;

    enterScope();

    // 注册this
    Symbol thisSym;
    thisSym.name = "this";
    thisSym.type = std::make_unique<Type>(TypeKind::CLASS);
    currentScope_->define("this", thisSym);

    for (auto& member : stmt.members) {
        if (member.isMethod) {
            if (member.method) {
                analyzeFunction(*member.method);
            }
        } else {
            // 字段声明
            if (member.initializer) {
                analyzeExpr(*member.initializer);
            }

            Symbol fieldSym;
            fieldSym.name = member.name;
            fieldSym.type = std::make_unique<Type>(member.type->kind);
            currentScope_->define(member.name, fieldSym);
        }
    }

    leaveScope();
    currentClass_ = prevClass;
}

void SemanticAnalyzer::analyzeBlock(BlockStmt& stmt) {
    enterScope();
    for (auto& s : stmt.statements) {
        if (s) {
            analyzeStmt(*s);
        }
    }
    leaveScope();
}

void SemanticAnalyzer::analyzeIf(IfStmt& stmt) {
    // 分析条件
    TypePtr condType = analyzeExpr(*stmt.condition);
    if (condType && condType->kind != TypeKind::BOOL &&
        condType->kind != TypeKind::INT) {
        warning(stmt.condition->line, stmt.condition->column,
                "Condition should be boolean or integer");
    }

    // 分析分支
    analyzeStmt(*stmt.thenBranch);
    if (stmt.elseBranch) {
        analyzeStmt(*stmt.elseBranch);
    }
}

void SemanticAnalyzer::analyzeWhile(WhileStmt& stmt) {
    TypePtr condType = analyzeExpr(*stmt.condition);

    loopDepth_++;
    analyzeStmt(*stmt.body);
    loopDepth_--;
}

void SemanticAnalyzer::analyzeFor(ForStmt& stmt) {
    enterScope();

    if (stmt.initializer) {
        analyzeStmt(*stmt.initializer);
    }

    if (stmt.condition) {
        analyzeExpr(*stmt.condition);
    }

    if (stmt.increment) {
        analyzeExpr(*stmt.increment);
    }

    loopDepth_++;
    analyzeStmt(*stmt.body);
    loopDepth_--;

    leaveScope();
}

void SemanticAnalyzer::analyzeReturn(ReturnStmt& stmt) {
    if (!currentFunction_) {
        error(stmt.line, stmt.column, "'return' outside of function");
        return;
    }

    if (stmt.value) {
        TypePtr returnType = analyzeExpr(*stmt.value);

        if (currentFunction_->returnType &&
            currentFunction_->returnType->kind != TypeKind::VOID) {
            if (returnType && !isCompatible(*currentFunction_->returnType, *returnType)) {
                error(stmt.line, stmt.column,
                      "Return type mismatch: expected '" +
                      currentFunction_->returnType->toString() +
                      "', got '" + returnType->toString() + "'");
            }
        }
    } else if (currentFunction_->returnType &&
               currentFunction_->returnType->kind != TypeKind::VOID) {
        error(stmt.line, stmt.column,
              "Function '" + currentFunction_->name + "' must return a value");
    }
}

void SemanticAnalyzer::analyzePrint(PrintStmt& stmt) {
    for (auto& arg : stmt.arguments) {
        analyzeExpr(*arg);
    }
}

void SemanticAnalyzer::analyzeExprStmt(ExprStmt& stmt) {
    analyzeExpr(*stmt.expression);
}

TypePtr SemanticAnalyzer::analyzeExpr(Expr& expr) {
    TypePtr type;

    switch (expr.exprType) {
        case ExprType::LITERAL:
            type = analyzeLiteral(static_cast<LiteralExpr&>(expr));
            break;
        case ExprType::BINARY:
            type = analyzeBinary(static_cast<BinaryExpr&>(expr));
            break;
        case ExprType::UNARY:
            type = analyzeUnary(static_cast<UnaryExpr&>(expr));
            break;
        case ExprType::VARIABLE:
            type = analyzeVariable(static_cast<VariableExpr&>(expr));
            break;
        case ExprType::ASSIGN:
            type = analyzeAssign(static_cast<AssignExpr&>(expr));
            break;
        case ExprType::CALL:
            type = analyzeCall(static_cast<CallExpr&>(expr));
            break;
        case ExprType::INDEX:
            type = analyzeIndex(static_cast<IndexExpr&>(expr));
            break;
        case ExprType::MEMBER:
            type = analyzeMember(static_cast<MemberExpr&>(expr));
            break;
        case ExprType::LOGICAL:
            type = analyzeLogical(static_cast<LogicalExpr&>(expr));
            break;
        case ExprType::TERNARY:
            type = analyzeTernary(static_cast<TernaryExpr&>(expr));
            break;
        case ExprType::CAST:
            type = analyzeCast(static_cast<CastExpr&>(expr));
            break;
        default:
            type = std::make_unique<Type>(TypeKind::AUTO);
            break;
    }

    expr.type = std::make_unique<Type>(type->kind);
    return type;
}

TypePtr SemanticAnalyzer::analyzeLiteral(LiteralExpr& expr) {
    if (std::holds_alternative<int64_t>(expr.value)) {
        return std::make_unique<Type>(TypeKind::INT);
    } else if (std::holds_alternative<double>(expr.value)) {
        return std::make_unique<Type>(TypeKind::FLOAT);
    } else if (std::holds_alternative<std::string>(expr.value)) {
        return std::make_unique<Type>(TypeKind::STRING);
    } else if (std::holds_alternative<bool>(expr.value)) {
        return std::make_unique<Type>(TypeKind::BOOL);
    }
    return std::make_unique<Type>(TypeKind::AUTO);
}

TypePtr SemanticAnalyzer::analyzeBinary(BinaryExpr& expr) {
    TypePtr leftType = analyzeExpr(*expr.left);
    TypePtr rightType = analyzeExpr(*expr.right);

    // 比较运算符返回布尔值
    if (expr.op.type == TokenType::EQUAL || expr.op.type == TokenType::NOT_EQUAL ||
        expr.op.type == TokenType::LESS || expr.op.type == TokenType::LESS_EQUAL ||
        expr.op.type == TokenType::GREATER || expr.op.type == TokenType::GREATER_EQUAL) {
        return std::make_unique<Type>(TypeKind::BOOL);
    }

    // 算术运算符
    if (leftType && rightType) {
        if (leftType->kind == TypeKind::STRING || rightType->kind == TypeKind::STRING) {
            if (expr.op.type == TokenType::PLUS) {
                return std::make_unique<Type>(TypeKind::STRING);
            }
        }

        if (leftType->kind == TypeKind::FLOAT || rightType->kind == TypeKind::FLOAT) {
            return std::make_unique<Type>(TypeKind::FLOAT);
        }

        if (leftType->kind == TypeKind::INT && rightType->kind == TypeKind::INT) {
            return std::make_unique<Type>(TypeKind::INT);
        }
    }

    return std::make_unique<Type>(TypeKind::AUTO);
}

TypePtr SemanticAnalyzer::analyzeUnary(UnaryExpr& expr) {
    TypePtr operandType = analyzeExpr(*expr.operand);

    if (expr.op.type == TokenType::NOT) {
        return std::make_unique<Type>(TypeKind::BOOL);
    }

    if (expr.op.type == TokenType::MINUS) {
        if (operandType && (operandType->kind == TypeKind::INT ||
                           operandType->kind == TypeKind::FLOAT)) {
            return std::make_unique<Type>(operandType->kind);
        }
    }

    return operandType ? std::make_unique<Type>(operandType->kind) :
                        std::make_unique<Type>(TypeKind::AUTO);
}

TypePtr SemanticAnalyzer::analyzeVariable(VariableExpr& expr) {
    Symbol* symbol = currentScope_->resolve(expr.name);
    if (!symbol) {
        error(expr.line, expr.column,
              "Undefined variable '" + expr.name + "'");
        return std::make_unique<Type>(TypeKind::AUTO);
    }

    return symbol->type ? std::make_unique<Type>(symbol->type->kind) :
                          std::make_unique<Type>(TypeKind::AUTO);
}

TypePtr SemanticAnalyzer::analyzeAssign(AssignExpr& expr) {
    TypePtr valueType = analyzeExpr(*expr.value);

    // 检查左值
    if (expr.target->exprType == ExprType::VARIABLE) {
        auto& varExpr = static_cast<VariableExpr&>(*expr.target);
        Symbol* symbol = currentScope_->resolve(varExpr.name);

        if (symbol) {
            if (symbol->isConst) {
                error(expr.line, expr.column,
                      "Cannot assign to constant '" + varExpr.name + "'");
            }

            if (symbol->type && valueType &&
                !isCompatible(*symbol->type, *valueType)) {
                error(expr.line, expr.column,
                      "Type mismatch in assignment to '" + varExpr.name + "'");
            }
        }

        analyzeExpr(*expr.target);
    } else if (expr.target->exprType == ExprType::INDEX ||
               expr.target->exprType == ExprType::MEMBER) {
        analyzeExpr(*expr.target);
    } else {
        error(expr.line, expr.column, "Invalid assignment target");
    }

    return valueType;
}

TypePtr SemanticAnalyzer::analyzeCall(CallExpr& expr) {
    // 分析callee
    if (expr.callee->exprType == ExprType::VARIABLE) {
        auto& varExpr = static_cast<VariableExpr&>(*expr.callee);
        Symbol* symbol = currentScope_->resolve(varExpr.name);

        if (symbol && symbol->isFunction) {
            // 分析参数
            for (auto& arg : expr.arguments) {
                analyzeExpr(*arg);
            }

            return symbol->returnType ?
                std::make_unique<Type>(symbol->returnType->kind) :
                std::make_unique<Type>(TypeKind::VOID);
        } else if (symbol && !symbol->isFunction) {
            error(expr.line, expr.column,
                  "'" + varExpr.name + "' is not a function");
        }
    }

    // 分析参数
    for (auto& arg : expr.arguments) {
        analyzeExpr(*arg);
    }

    analyzeExpr(*expr.callee);
    return std::make_unique<Type>(TypeKind::AUTO);
}

TypePtr SemanticAnalyzer::analyzeIndex(IndexExpr& expr) {
    TypePtr objType = analyzeExpr(*expr.object);
    TypePtr indexType = analyzeExpr(*expr.index);

    if (indexType && indexType->kind != TypeKind::INT) {
        error(expr.line, expr.column, "Array index must be integer");
    }

    // 返回元素类型（简化处理）
    return std::make_unique<Type>(TypeKind::AUTO);
}

TypePtr SemanticAnalyzer::analyzeMember(MemberExpr& expr) {
    TypePtr objType = analyzeExpr(*expr.object);

    // 简化处理：假设成员访问有效
    return std::make_unique<Type>(TypeKind::AUTO);
}

TypePtr SemanticAnalyzer::analyzeLogical(LogicalExpr& expr) {
    TypePtr leftType = analyzeExpr(*expr.left);
    TypePtr rightType = analyzeExpr(*expr.right);

    return std::make_unique<Type>(TypeKind::BOOL);
}

TypePtr SemanticAnalyzer::analyzeTernary(TernaryExpr& expr) {
    TypePtr condType = analyzeExpr(*expr.condition);
    TypePtr trueType = analyzeExpr(*expr.trueExpr);
    TypePtr falseType = analyzeExpr(*expr.falseExpr);

    if (trueType && falseType && isCompatible(*trueType, *falseType)) {
        return std::make_unique<Type>(trueType->kind);
    }

    return std::make_unique<Type>(TypeKind::AUTO);
}

TypePtr SemanticAnalyzer::analyzeCast(CastExpr& expr) {
    TypePtr exprType = analyzeExpr(*expr.expr);
    return std::make_unique<Type>(expr.targetType->kind);
}

} // namespace compiler
