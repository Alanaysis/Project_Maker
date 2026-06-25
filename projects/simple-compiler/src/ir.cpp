#include "ir.hpp"
#include <iomanip>

namespace compiler {

// ==================== IRInstruction ====================

std::string IRInstruction::toString() const {
    std::stringstream ss;

    // 结果
    if (!result.name.empty()) {
        ss << result.name << " = ";
    }

    // 操作码
    switch (opcode) {
        case IROpcode::ADD: ss << "add"; break;
        case IROpcode::SUB: ss << "sub"; break;
        case IROpcode::MUL: ss << "mul"; break;
        case IROpcode::DIV: ss << "div"; break;
        case IROpcode::MOD: ss << "mod"; break;
        case IROpcode::NEG: ss << "neg"; break;
        case IROpcode::CMP_EQ: ss << "cmp_eq"; break;
        case IROpcode::CMP_NE: ss << "cmp_ne"; break;
        case IROpcode::CMP_LT: ss << "cmp_lt"; break;
        case IROpcode::CMP_LE: ss << "cmp_le"; break;
        case IROpcode::CMP_GT: ss << "cmp_gt"; break;
        case IROpcode::CMP_GE: ss << "cmp_ge"; break;
        case IROpcode::AND: ss << "and"; break;
        case IROpcode::OR: ss << "or"; break;
        case IROpcode::NOT: ss << "not"; break;
        case IROpcode::BIT_AND: ss << "bit_and"; break;
        case IROpcode::BIT_OR: ss << "bit_or"; break;
        case IROpcode::BIT_XOR: ss << "bit_xor"; break;
        case IROpcode::BIT_NOT: ss << "bit_not"; break;
        case IROpcode::SHL: ss << "shl"; break;
        case IROpcode::SHR: ss << "shr"; break;
        case IROpcode::LOAD: ss << "load"; break;
        case IROpcode::MOVE: ss << "move"; break;
        case IROpcode::LOAD_VAR: ss << "load_var"; break;
        case IROpcode::STORE_VAR: ss << "store_var"; break;
        case IROpcode::ALLOCA: ss << "alloca"; break;
        case IROpcode::LOAD_MEM: ss << "load_mem"; break;
        case IROpcode::STORE_MEM: ss << "store_mem"; break;
        case IROpcode::GEP: ss << "gep"; break;
        case IROpcode::LABEL: ss << "label"; break;
        case IROpcode::JUMP: ss << "jump"; break;
        case IROpcode::BRANCH: ss << "branch"; break;
        case IROpcode::CALL: ss << "call"; break;
        case IROpcode::RETURN: ss << "return"; break;
        case IROpcode::FUNC_BEGIN: ss << "func_begin"; break;
        case IROpcode::FUNC_END: ss << "func_end"; break;
        case IROpcode::PARAM: ss << "param"; break;
        case IROpcode::ARG: ss << "arg"; break;
        case IROpcode::ARRAY_NEW: ss << "array_new"; break;
        case IROpcode::ARRAY_LOAD: ss << "array_load"; break;
        case IROpcode::ARRAY_STORE: ss << "array_store"; break;
        case IROpcode::NOP: ss << "nop"; break;
        case IROpcode::PHI: ss << "phi"; break;
        case IROpcode::CAST: ss << "cast"; break;
        case IROpcode::PRINT: ss << "print"; break;
        case IROpcode::CONST_FOLD: ss << "const_fold"; break;
        case IROpcode::DEAD_CODE: ss << "dead_code"; break;
    }

    // 操作数
    if (!operands.empty()) {
        ss << " ";
        for (size_t i = 0; i < operands.size(); ++i) {
            if (i > 0) ss << ", ";
            ss << operands[i].name;

            if (operands[i].isConstant) {
                switch (operands[i].type) {
                    case IRValueType::INT:
                        ss << "(" << operands[i].constant.intValue << ")";
                        break;
                    case IRValueType::FLOAT:
                        ss << "(" << operands[i].constant.floatValue << ")";
                        break;
                    case IRValueType::BOOL:
                        ss << "(" << (operands[i].constant.boolValue ? "true" : "false") << ")";
                        break;
                    default:
                        break;
                }
            }
        }
    }

    return ss.str();
}

// ==================== IRModule ====================

void IRModule::print(std::ostream& out) const {
    out << "; Module: " << name << std::endl;
    out << std::endl;

    // 打印全局变量
    if (!globals.empty()) {
        out << "; Global variables:" << std::endl;
        for (const auto& [name, value] : globals) {
            out << ";   " << name << ": ";
            switch (value.type) {
                case IRValueType::INT: out << "int"; break;
                case IRValueType::FLOAT: out << "float"; break;
                case IRValueType::STRING: out << "string"; break;
                case IRValueType::BOOL: out << "bool"; break;
                default: out << "unknown"; break;
            }
            out << std::endl;
        }
        out << std::endl;
    }

    // 打印全局指令
    if (!globalInstructions.empty()) {
        out << "; Global instructions:" << std::endl;
        for (const auto& instr : globalInstructions) {
            out << "  " << instr.toString() << std::endl;
        }
        out << std::endl;
    }

    // 打印函数
    for (const auto& [name, func] : functions) {
        printFunction(name, out);
        out << std::endl;
    }
}

void IRModule::printFunction(const std::string& name, std::ostream& out) const {
    auto it = functions.find(name);
    if (it == functions.end()) return;

    const auto& func = it->second;

    out << "; Function: " << func.name << std::endl;

    // 函数签名
    out << "define ";
    switch (func.returnType) {
        case IRValueType::VOID: out << "void"; break;
        case IRValueType::INT: out << "i64"; break;
        case IRValueType::FLOAT: out << "f64"; break;
        case IRValueType::STRING: out << "string"; break;
        case IRValueType::BOOL: out << "i1"; break;
        default: out << "unknown"; break;
    }
    out << " @" << func.name << "(";

    for (size_t i = 0; i < func.parameters.size(); ++i) {
        if (i > 0) out << ", ";
        switch (func.parameters[i].type) {
            case IRValueType::INT: out << "i64"; break;
            case IRValueType::FLOAT: out << "f64"; break;
            case IRValueType::STRING: out << "string"; break;
            case IRValueType::BOOL: out << "i1"; break;
            default: out << "unknown"; break;
        }
        out << " " << func.parameters[i].name;
    }

    out << ") {" << std::endl;

    // 基本块
    for (const auto& block : func.basicBlocks) {
        // 标签
        if (!block.label.empty()) {
            out << block.label << ":" << std::endl;
        }

        // 指令
        for (const auto& instr : block.instructions) {
            out << "  " << instr.toString() << std::endl;
        }
    }

    out << "}" << std::endl;
}

// ==================== IRGenerator ====================

IRGenerator::IRGenerator()
    : currentFunction_(nullptr), currentBlock_(nullptr) {}

std::unique_ptr<IRModule> IRGenerator::generate(const Program& program) {
    module_ = std::make_unique<IRModule>("main");

    // 生成全局指令
    for (const auto& stmt : program.statements) {
        if (stmt) {
            generateStmt(*stmt);
        }
    }

    return std::move(module_);
}

void IRGenerator::emit(const IRInstruction& instruction) {
    if (currentBlock_) {
        currentBlock_->instructions.push_back(instruction);
    }
}

BasicBlock* IRGenerator::createBasicBlock(const std::string& label) {
    if (!currentFunction_) return nullptr;

    int id = currentFunction_->basicBlocks.size();
    std::string blockLabel = label.empty() ?
        currentFunction_->newLabel("BB") : label;

    currentFunction_->basicBlocks.emplace_back(id, blockLabel);
    return &currentFunction_->basicBlocks.back();
}

void IRGenerator::switchToBlock(BasicBlock* block) {
    currentBlock_ = block;
}

IRValue IRGenerator::generateExpr(const Expr& expr) {
    switch (expr.exprType) {
        case ExprType::LITERAL: {
            const auto& literal = static_cast<const LiteralExpr&>(expr);
            IRValue value;

            if (std::holds_alternative<int64_t>(literal.value)) {
                value = IRValue("$" + std::to_string(std::get<int64_t>(literal.value)),
                               IRValueType::INT);
                value.isConstant = true;
                value.constant.intValue = std::get<int64_t>(literal.value);
            } else if (std::holds_alternative<double>(literal.value)) {
                value = IRValue("$" + std::to_string(std::get<double>(literal.value)),
                               IRValueType::FLOAT);
                value.isConstant = true;
                value.constant.floatValue = std::get<double>(literal.value);
            } else if (std::holds_alternative<bool>(literal.value)) {
                value = IRValue(std::get<bool>(literal.value) ? "$true" : "$false",
                               IRValueType::BOOL);
                value.isConstant = true;
                value.constant.boolValue = std::get<bool>(literal.value);
            } else if (std::holds_alternative<std::string>(literal.value)) {
                value = IRValue("\"" + std::get<std::string>(literal.value) + "\"",
                               IRValueType::STRING);
                value.isConstant = true;
            }

            return value;
        }

        case ExprType::BINARY: {
            return generateBinary(static_cast<const BinaryExpr&>(expr));
        }

        case ExprType::UNARY: {
            return generateUnary(static_cast<const UnaryExpr&>(expr));
        }

        case ExprType::VARIABLE: {
            const auto& varExpr = static_cast<const VariableExpr&>(expr);
            auto it = variableMap_.find(varExpr.name);
            if (it != variableMap_.end()) {
                return it->second;
            }
            // 变量未找到，返回一个占位符
            IRValue var(varExpr.name, IRValueType::INT);
            return var;
        }

        case ExprType::CALL: {
            return generateCall(static_cast<const CallExpr&>(expr));
        }

        default: {
            // 默认返回临时变量
            if (currentFunction_) {
                return currentFunction_->newTemp(IRValueType::INT);
            }
            IRValue temp("%t_unknown", IRValueType::INT);
            return temp;
        }
    }
}

void IRGenerator::generateStmt(const Stmt& stmt) {
    switch (stmt.stmtType) {
        case StmtType::EXPR_STMT: {
            const auto& exprStmt = static_cast<const ExprStmt&>(stmt);
            generateExpr(*exprStmt.expression);
            break;
        }

        case StmtType::VAR_DECL: {
            const auto& varDecl = static_cast<const VarDeclStmt&>(stmt);
            IRValue var(varDecl.name, IRValueType::INT);

            if (varDecl.initializer) {
                IRValue initValue = generateExpr(*varDecl.initializer);
                emit(IRInstruction(IROpcode::STORE_VAR, IRValue(), {var, initValue}));
            }

            variableMap_[varDecl.name] = var;
            break;
        }

        case StmtType::IF: {
            generateIf(static_cast<const IfStmt&>(stmt));
            break;
        }

        case StmtType::WHILE: {
            generateWhile(static_cast<const WhileStmt&>(stmt));
            break;
        }

        case StmtType::FOR: {
            generateFor(static_cast<const ForStmt&>(stmt));
            break;
        }

        case StmtType::FUNCTION: {
            generateFunction(static_cast<const FunctionStmt&>(stmt));
            break;
        }

        case StmtType::RETURN: {
            generateReturn(static_cast<const ReturnStmt&>(stmt));
            break;
        }

        case StmtType::PRINT: {
            const auto& printStmt = static_cast<const PrintStmt&>(stmt);
            for (const auto& arg : printStmt.arguments) {
                IRValue value = generateExpr(*arg);
                emit(IRInstruction(IROpcode::PRINT, IRValue(), {value}));
            }
            break;
        }

        case StmtType::BLOCK: {
            const auto& blockStmt = static_cast<const BlockStmt&>(stmt);
            for (const auto& s : blockStmt.statements) {
                if (s) {
                    generateStmt(*s);
                }
            }
            break;
        }

        default:
            break;
    }
}

IRValue IRGenerator::generateBinary(const BinaryExpr& expr) {
    IRValue left = generateExpr(*expr.left);
    IRValue right = generateExpr(*expr.right);

    IROpcode opcode;
    IRValueType resultType = IRValueType::INT;

    switch (expr.op.type) {
        case TokenType::PLUS: opcode = IROpcode::ADD; break;
        case TokenType::MINUS: opcode = IROpcode::SUB; break;
        case TokenType::MULTIPLY: opcode = IROpcode::MUL; break;
        case TokenType::DIVIDE: opcode = IROpcode::DIV; break;
        case TokenType::MODULO: opcode = IROpcode::MOD; break;
        case TokenType::EQUAL: opcode = IROpcode::CMP_EQ; resultType = IRValueType::BOOL; break;
        case TokenType::NOT_EQUAL: opcode = IROpcode::CMP_NE; resultType = IRValueType::BOOL; break;
        case TokenType::LESS: opcode = IROpcode::CMP_LT; resultType = IRValueType::BOOL; break;
        case TokenType::LESS_EQUAL: opcode = IROpcode::CMP_LE; resultType = IRValueType::BOOL; break;
        case TokenType::GREATER: opcode = IROpcode::CMP_GT; resultType = IRValueType::BOOL; break;
        case TokenType::GREATER_EQUAL: opcode = IROpcode::CMP_GE; resultType = IRValueType::BOOL; break;
        case TokenType::AND: opcode = IROpcode::AND; resultType = IRValueType::BOOL; break;
        case TokenType::OR: opcode = IROpcode::OR; resultType = IRValueType::BOOL; break;
        case TokenType::BIT_AND: opcode = IROpcode::BIT_AND; break;
        case TokenType::BIT_OR: opcode = IROpcode::BIT_OR; break;
        case TokenType::BIT_XOR: opcode = IROpcode::BIT_XOR; break;
        case TokenType::SHIFT_LEFT: opcode = IROpcode::SHL; break;
        case TokenType::SHIFT_RIGHT: opcode = IROpcode::SHR; break;
        default: opcode = IROpcode::ADD; break;
    }

    IRValue result = currentFunction_ ?
        currentFunction_->newTemp(resultType) :
        IRValue("%t", resultType);

    emit(IRInstruction(opcode, result, {left, right}));
    return result;
}

IRValue IRGenerator::generateUnary(const UnaryExpr& expr) {
    IRValue operand = generateExpr(*expr.operand);
    IRValue result;

    switch (expr.op.type) {
        case TokenType::MINUS: {
            result = currentFunction_ ?
                currentFunction_->newTemp(IRValueType::INT) :
                IRValue("%t", IRValueType::INT);
            emit(IRInstruction(IROpcode::NEG, result, {operand}));
            break;
        }
        case TokenType::NOT: {
            result = currentFunction_ ?
                currentFunction_->newTemp(IRValueType::BOOL) :
                IRValue("%t", IRValueType::BOOL);
            emit(IRInstruction(IROpcode::NOT, result, {operand}));
            break;
        }
        case TokenType::BIT_NOT: {
            result = currentFunction_ ?
                currentFunction_->newTemp(IRValueType::INT) :
                IRValue("%t", IRValueType::INT);
            emit(IRInstruction(IROpcode::BIT_NOT, result, {operand}));
            break;
        }
        default:
            result = operand;
            break;
    }

    return result;
}

IRValue IRGenerator::generateCall(const CallExpr& expr) {
    // 生成参数
    std::vector<IRValue> args;
    for (const auto& arg : expr.arguments) {
        args.push_back(generateExpr(*arg));
    }

    // 获取函数名
    std::string funcName;
    if (expr.callee->exprType == ExprType::VARIABLE) {
        funcName = static_cast<const VariableExpr&>(*expr.callee).name;
    }

    // 调用指令
    IRValue result = currentFunction_ ?
        currentFunction_->newTemp(IRValueType::INT) :
        IRValue("%t", IRValueType::INT);

    std::vector<IRValue> operands;
    operands.push_back(IRValue(funcName, IRValueType::FUNCTION));
    operands.insert(operands.end(), args.begin(), args.end());

    emit(IRInstruction(IROpcode::CALL, result, operands));
    return result;
}

void IRGenerator::generateIf(const IfStmt& stmt) {
    // 生成条件
    IRValue cond = generateExpr(*stmt.condition);

    // 创建基本块
    std::string thenLabel = currentFunction_->newLabel("then");
    std::string elseLabel = currentFunction_->newLabel("else");
    std::string endLabel = currentFunction_->newLabel("end");

    // 条件跳转
    emit(IRInstruction(IROpcode::BRANCH, IRValue(),
                       {cond, IRValue(thenLabel, IRValueType::LABEL),
                        IRValue(stmt.elseBranch ? elseLabel : endLabel, IRValueType::LABEL)}));

    // then分支
    BasicBlock* thenBlock = createBasicBlock(thenLabel);
    switchToBlock(thenBlock);
    generateStmt(*stmt.thenBranch);
    emit(IRInstruction(IROpcode::JUMP, IRValue(),
                       {IRValue(endLabel, IRValueType::LABEL)}));

    // else分支
    if (stmt.elseBranch) {
        BasicBlock* elseBlock = createBasicBlock(elseLabel);
        switchToBlock(elseBlock);
        generateStmt(*stmt.elseBranch);
        emit(IRInstruction(IROpcode::JUMP, IRValue(),
                           {IRValue(endLabel, IRValueType::LABEL)}));
    }

    // 结束块
    BasicBlock* endBlock = createBasicBlock(endLabel);
    switchToBlock(endBlock);
}

void IRGenerator::generateWhile(const WhileStmt& stmt) {
    std::string condLabel = currentFunction_->newLabel("while_cond");
    std::string bodyLabel = currentFunction_->newLabel("while_body");
    std::string endLabel = currentFunction_->newLabel("while_end");

    // 跳转到条件检查
    emit(IRInstruction(IROpcode::JUMP, IRValue(),
                       {IRValue(condLabel, IRValueType::LABEL)}));

    // 条件检查块
    BasicBlock* condBlock = createBasicBlock(condLabel);
    switchToBlock(condBlock);
    IRValue cond = generateExpr(*stmt.condition);
    emit(IRInstruction(IROpcode::BRANCH, IRValue(),
                       {cond, IRValue(bodyLabel, IRValueType::LABEL),
                        IRValue(endLabel, IRValueType::LABEL)}));

    // 循环体块
    BasicBlock* bodyBlock = createBasicBlock(bodyLabel);
    switchToBlock(bodyBlock);
    generateStmt(*stmt.body);
    emit(IRInstruction(IROpcode::JUMP, IRValue(),
                       {IRValue(condLabel, IRValueType::LABEL)}));

    // 结束块
    BasicBlock* endBlock = createBasicBlock(endLabel);
    switchToBlock(endBlock);
}

void IRGenerator::generateFor(const ForStmt& stmt) {
    // 初始化
    if (stmt.initializer) {
        generateStmt(*stmt.initializer);
    }

    // 转换为while循环
    std::string condLabel = currentFunction_->newLabel("for_cond");
    std::string bodyLabel = currentFunction_->newLabel("for_body");
    std::string endLabel = currentFunction_->newLabel("for_end");

    // 跳转到条件检查
    emit(IRInstruction(IROpcode::JUMP, IRValue(),
                       {IRValue(condLabel, IRValueType::LABEL)}));

    // 条件检查块
    BasicBlock* condBlock = createBasicBlock(condLabel);
    switchToBlock(condBlock);

    if (stmt.condition) {
        IRValue cond = generateExpr(*stmt.condition);
        emit(IRInstruction(IROpcode::BRANCH, IRValue(),
                           {cond, IRValue(bodyLabel, IRValueType::LABEL),
                            IRValue(endLabel, IRValueType::LABEL)}));
    } else {
        // 无条件循环
        emit(IRInstruction(IROpcode::JUMP, IRValue(),
                           {IRValue(bodyLabel, IRValueType::LABEL)}));
    }

    // 循环体块
    BasicBlock* bodyBlock = createBasicBlock(bodyLabel);
    switchToBlock(bodyBlock);
    generateStmt(*stmt.body);

    // 递增
    if (stmt.increment) {
        generateExpr(*stmt.increment);
    }

    emit(IRInstruction(IROpcode::JUMP, IRValue(),
                       {IRValue(condLabel, IRValueType::LABEL)}));

    // 结束块
    BasicBlock* endBlock = createBasicBlock(endLabel);
    switchToBlock(endBlock);
}

void IRGenerator::generateFunction(const FunctionStmt& stmt) {
    // 创建新函数
    IRFunction func(stmt.name);

    // 设置返回类型
    if (stmt.returnType) {
        switch (stmt.returnType->kind) {
            case TypeKind::INT: func.returnType = IRValueType::INT; break;
            case TypeKind::FLOAT: func.returnType = IRValueType::FLOAT; break;
            case TypeKind::STRING: func.returnType = IRValueType::STRING; break;
            case TypeKind::BOOL: func.returnType = IRValueType::BOOL; break;
            default: func.returnType = IRValueType::VOID; break;
        }
    }

    // 参数
    for (const auto& param : stmt.params) {
        IRValue paramValue(param.name, IRValueType::INT);
        func.parameters.push_back(paramValue);
    }

    // 保存当前函数上下文
    IRFunction* prevFunction = currentFunction_;
    BasicBlock* prevBlock = currentBlock_;

    // 切换到新函数
    currentFunction_ = &module_->functions[stmt.name];
    *currentFunction_ = func;

    // 创建入口基本块
    BasicBlock* entryBlock = createBasicBlock("entry");
    switchToBlock(entryBlock);

    // 注册参数到变量映射
    variableMap_.clear();
    for (const auto& param : currentFunction_->parameters) {
        variableMap_[param.name] = param;
    }

    // 生成函数体
    if (stmt.body) {
        generateStmt(*stmt.body);
    }

    // 如果没有return语句，添加默认return
    if (currentBlock_->instructions.empty() ||
        currentBlock_->instructions.back().opcode != IROpcode::RETURN) {
        if (func.returnType == IRValueType::VOID) {
            emit(IRInstruction(IROpcode::RETURN, IRValue(), {}));
        }
    }

    // 恢复上下文
    currentFunction_ = prevFunction;
    currentBlock_ = prevBlock;
    variableMap_.clear();
}

void IRGenerator::generateReturn(const ReturnStmt& stmt) {
    if (stmt.value) {
        IRValue value = generateExpr(*stmt.value);
        emit(IRInstruction(IROpcode::RETURN, IRValue(), {value}));
    } else {
        emit(IRInstruction(IROpcode::RETURN, IRValue(), {}));
    }
}

IROpcode IRGenerator::getCompareOpcode(const Token& op) const {
    switch (op.type) {
        case TokenType::EQUAL: return IROpcode::CMP_EQ;
        case TokenType::NOT_EQUAL: return IROpcode::CMP_NE;
        case TokenType::LESS: return IROpcode::CMP_LT;
        case TokenType::LESS_EQUAL: return IROpcode::CMP_LE;
        case TokenType::GREATER: return IROpcode::CMP_GT;
        case TokenType::GREATER_EQUAL: return IROpcode::CMP_GE;
        default: return IROpcode::CMP_EQ;
    }
}

} // namespace compiler
