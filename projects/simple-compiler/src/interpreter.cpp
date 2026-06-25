#include "interpreter.hpp"
#include <cmath>
#include <sstream>
#include <stdexcept>

namespace compiler {

// ==================== Environment ====================

void Environment::define(const std::string& name, const Variable& variable) {
    variables_[name] = variable;
}

Variable* Environment::get(const std::string& name) {
    auto it = variables_.find(name);
    if (it != variables_.end()) {
        return &it->second;
    }

    if (parent_) {
        return parent_->get(name);
    }

    return nullptr;
}

void Environment::set(const std::string& name, const RuntimeValue& value) {
    auto it = variables_.find(name);
    if (it != variables_.end()) {
        if (it->second.isConst) {
            throw std::runtime_error("Cannot assign to constant '" + name + "'");
        }
        it->second.value = value;
        return;
    }

    if (parent_) {
        parent_->set(name, value);
        return;
    }

    throw std::runtime_error("Undefined variable '" + name + "'");
}

void Environment::setAt(int distance, const std::string& name, const RuntimeValue& value) {
    Environment* env = ancestor(distance);
    if (env) {
        auto it = env->variables_.find(name);
        if (it != env->variables_.end()) {
            it->second.value = value;
        }
    }
}

Environment* Environment::ancestor(int distance) {
    Environment* env = this;
    for (int i = 0; i < distance; ++i) {
        if (env->parent_) {
            env = env->parent_.get();
        } else {
            return nullptr;
        }
    }
    return env;
}

// ==================== Interpreter ====================

Interpreter::Interpreter() : outputStream_(&std::cout) {
    globalEnv_ = std::make_shared<Environment>();
    currentEnv_ = globalEnv_;
    registerBuiltins();
}

bool Interpreter::interpret(Program& program) {
    try {
        for (auto& stmt : program.statements) {
            if (stmt) {
                execute(*stmt);
            }
        }
        return errors_.empty();
    } catch (const std::runtime_error& e) {
        error(0, e.what());
        return false;
    } catch (const ReturnException& e) {
        error(0, "Unexpected return statement");
        return false;
    }
}

void Interpreter::error(int line, const std::string& message) {
    std::string errorMsg = "Runtime error";
    if (line > 0) {
        errorMsg += " at line " + std::to_string(line);
    }
    errorMsg += ": " + message;
    errors_.push_back(errorMsg);
    if (outputStream_) {
        *outputStream_ << errorMsg << std::endl;
    }
}

void Interpreter::execute(Stmt& stmt) {
    switch (stmt.stmtType) {
        case StmtType::EXPR_STMT:
            evaluate(*static_cast<ExprStmt&>(stmt).expression);
            break;

        case StmtType::VAR_DECL:
            executeVarDecl(static_cast<VarDeclStmt&>(stmt));
            break;

        case StmtType::FUNCTION:
            executeFunction(static_cast<FunctionStmt&>(stmt));
            break;

        case StmtType::CLASS:
            executeClass(static_cast<ClassStmt&>(stmt));
            break;

        case StmtType::BLOCK:
            executeBlock(static_cast<BlockStmt&>(stmt).statements,
                        std::make_shared<Environment>(currentEnv_));
            break;

        case StmtType::IF:
            executeIf(static_cast<IfStmt&>(stmt));
            break;

        case StmtType::WHILE:
            executeWhile(static_cast<WhileStmt&>(stmt));
            break;

        case StmtType::FOR:
            executeFor(static_cast<ForStmt&>(stmt));
            break;

        case StmtType::RETURN:
            executeReturn(static_cast<ReturnStmt&>(stmt));
            break;

        case StmtType::PRINT:
            executePrint(static_cast<PrintStmt&>(stmt));
            break;

        case StmtType::BREAK:
            throw BreakException();

        case StmtType::CONTINUE:
            throw ContinueException();

        default:
            break;
    }
}

void Interpreter::executeBlock(const std::vector<StmtPtr>& statements,
                                std::shared_ptr<Environment> env) {
    auto previous = currentEnv_;
    currentEnv_ = env;

    try {
        for (const auto& stmt : statements) {
            if (stmt) {
                execute(*stmt);
            }
        }
    } catch (...) {
        currentEnv_ = previous;
        throw;
    }

    currentEnv_ = previous;
}

RuntimeValue Interpreter::evaluate(Expr& expr) {
    switch (expr.exprType) {
        case ExprType::LITERAL:
            return evaluateLiteral(static_cast<LiteralExpr&>(expr));

        case ExprType::BINARY:
            return evaluateBinary(static_cast<BinaryExpr&>(expr));

        case ExprType::UNARY:
            return evaluateUnary(static_cast<UnaryExpr&>(expr));

        case ExprType::VARIABLE:
            return evaluateVariable(static_cast<VariableExpr&>(expr));

        case ExprType::ASSIGN:
            return evaluateAssign(static_cast<AssignExpr&>(expr));

        case ExprType::CALL:
            return evaluateCall(static_cast<CallExpr&>(expr));

        case ExprType::LOGICAL:
            return evaluateLogical(static_cast<LogicalExpr&>(expr));

        case ExprType::INDEX:
            return evaluateIndex(static_cast<IndexExpr&>(expr));

        case ExprType::MEMBER:
            return evaluateMember(static_cast<MemberExpr&>(expr));

        default:
            return std::monostate{};
    }
}

void Interpreter::executeVarDecl(VarDeclStmt& stmt) {
    RuntimeValue value = std::monostate{};

    if (stmt.initializer) {
        value = evaluate(*stmt.initializer);
    }

    Variable var;
    var.value = value;
    var.isConst = stmt.isConst;
    var.type = stmt.type ? std::make_shared<Type>(stmt.type->kind) : nullptr;

    currentEnv_->define(stmt.name, var);
}

void Interpreter::executeFunction(FunctionStmt& stmt) {
    auto closure = std::make_shared<std::unordered_map<std::string, Variable>>();

    // 捕获当前环境中的变量
    auto env = currentEnv_;
    while (env) {
        for (const auto& [name, var] : env->getVariables()) {
            (*closure)[name] = var;
        }
        env = env->getParent();
    }

    FunctionObject func;
    func.name = stmt.name;
    func.params = stmt.params;
    func.body = stmt.body.get();  // 存储原始指针，不复制
    func.closure = closure;

    Variable var;
    var.value = std::monostate{}; // 函数对象不直接存储在值中
    var.isConst = true;

    currentEnv_->define(stmt.name, var);

    // 存储函数对象
    functionTable_[stmt.name] = std::move(func);
}

void Interpreter::executeClass(ClassStmt& stmt) {
    // 注册类（简化处理）
    Variable var;
    var.value = std::monostate{};
    var.isConst = true;
    currentEnv_->define(stmt.name, var);
}

void Interpreter::executeIf(IfStmt& stmt) {
    RuntimeValue condition = evaluate(*stmt.condition);

    if (isTruthy(condition)) {
        execute(*stmt.thenBranch);
    } else if (stmt.elseBranch) {
        execute(*stmt.elseBranch);
    }
}

void Interpreter::executeWhile(WhileStmt& stmt) {
    while (true) {
        RuntimeValue condition = evaluate(*stmt.condition);
        if (!isTruthy(condition)) break;

        try {
            execute(*stmt.body);
        } catch (const BreakException&) {
            break;
        } catch (const ContinueException&) {
            continue;
        }
    }
}

void Interpreter::executeFor(ForStmt& stmt) {
    auto env = std::make_shared<Environment>(currentEnv_);
    auto previous = currentEnv_;
    currentEnv_ = env;

    try {
        // 初始化
        if (stmt.initializer) {
            execute(*stmt.initializer);
        }

        while (true) {
            // 条件
            if (stmt.condition) {
                RuntimeValue condition = evaluate(*stmt.condition);
                if (!isTruthy(condition)) break;
            }

            // 循环体
            try {
                execute(*stmt.body);
            } catch (const BreakException&) {
                break;
            } catch (const ContinueException&) {
                // 继续到递增部分
            }

            // 递增
            if (stmt.increment) {
                evaluate(*stmt.increment);
            }
        }
    } catch (...) {
        currentEnv_ = previous;
        throw;
    }

    currentEnv_ = previous;
}

void Interpreter::executeReturn(ReturnStmt& stmt) {
    RuntimeValue value = std::monostate{};
    if (stmt.value) {
        value = evaluate(*stmt.value);
    }
    throw ReturnException(value);
}

void Interpreter::executePrint(PrintStmt& stmt) {
    for (const auto& arg : stmt.arguments) {
        RuntimeValue value = evaluate(*arg);
        std::string str = valueToString(value);
        if (outputStream_) {
            *outputStream_ << str << " ";
        }
        output_.push_back(str);
    }
    if (outputStream_) {
        *outputStream_ << std::endl;
    }
}

RuntimeValue Interpreter::evaluateLiteral(LiteralExpr& expr) {
    if (std::holds_alternative<int64_t>(expr.value)) {
        return std::get<int64_t>(expr.value);
    } else if (std::holds_alternative<double>(expr.value)) {
        return std::get<double>(expr.value);
    } else if (std::holds_alternative<std::string>(expr.value)) {
        return std::get<std::string>(expr.value);
    } else if (std::holds_alternative<bool>(expr.value)) {
        return std::get<bool>(expr.value);
    }
    return std::monostate{};
}

RuntimeValue Interpreter::evaluateBinary(BinaryExpr& expr) {
    RuntimeValue left = evaluate(*expr.left);
    RuntimeValue right = evaluate(*expr.right);

    // 字符串连接
    if (expr.op.type == TokenType::PLUS) {
        if (std::holds_alternative<std::string>(left) ||
            std::holds_alternative<std::string>(right)) {
            return valueToString(left) + valueToString(right);
        }
    }

    // 数字运算
    double leftNum = valueToNumber(left);
    double rightNum = valueToNumber(right);

    bool isInt = std::holds_alternative<int64_t>(left) &&
                 std::holds_alternative<int64_t>(right);

    switch (expr.op.type) {
        case TokenType::PLUS:
            return isInt ? RuntimeValue(static_cast<int64_t>(leftNum + rightNum))
                        : RuntimeValue(leftNum + rightNum);

        case TokenType::MINUS:
            return isInt ? RuntimeValue(static_cast<int64_t>(leftNum - rightNum))
                        : RuntimeValue(leftNum - rightNum);

        case TokenType::MULTIPLY:
            return isInt ? RuntimeValue(static_cast<int64_t>(leftNum * rightNum))
                        : RuntimeValue(leftNum * rightNum);

        case TokenType::DIVIDE:
            if (rightNum == 0) {
                error(expr.line, "Division by zero");
                return std::monostate{};
            }
            return isInt ? RuntimeValue(static_cast<int64_t>(leftNum / rightNum))
                        : RuntimeValue(leftNum / rightNum);

        case TokenType::MODULO:
            if (rightNum == 0) {
                error(expr.line, "Division by zero");
                return std::monostate{};
            }
            return isInt ? RuntimeValue(static_cast<int64_t>(static_cast<int64_t>(leftNum) %
                                                              static_cast<int64_t>(rightNum)))
                        : RuntimeValue(std::fmod(leftNum, rightNum));

        case TokenType::EQUAL:
            return leftNum == rightNum;

        case TokenType::NOT_EQUAL:
            return leftNum != rightNum;

        case TokenType::LESS:
            return leftNum < rightNum;

        case TokenType::LESS_EQUAL:
            return leftNum <= rightNum;

        case TokenType::GREATER:
            return leftNum > rightNum;

        case TokenType::GREATER_EQUAL:
            return leftNum >= rightNum;

        default:
            error(expr.line, "Unknown binary operator");
            return std::monostate{};
    }
}

RuntimeValue Interpreter::evaluateUnary(UnaryExpr& expr) {
    RuntimeValue operand = evaluate(*expr.operand);

    switch (expr.op.type) {
        case TokenType::MINUS:
            return -valueToNumber(operand);

        case TokenType::NOT:
            return !isTruthy(operand);

        case TokenType::INCREMENT: {
            if (expr.operand->exprType == ExprType::VARIABLE) {
                auto& varExpr = static_cast<VariableExpr&>(*expr.operand);
                double val = valueToNumber(operand) + 1;
                currentEnv_->set(varExpr.name, val);
                return expr.isPrefix ? RuntimeValue(val) : operand;
            }
            break;
        }

        case TokenType::DECREMENT: {
            if (expr.operand->exprType == ExprType::VARIABLE) {
                auto& varExpr = static_cast<VariableExpr&>(*expr.operand);
                double val = valueToNumber(operand) - 1;
                currentEnv_->set(varExpr.name, val);
                return expr.isPrefix ? RuntimeValue(val) : operand;
            }
            break;
        }

        default:
            break;
    }

    return operand;
}

RuntimeValue Interpreter::evaluateVariable(VariableExpr& expr) {
    Variable* var = currentEnv_->get(expr.name);
    if (!var) {
        error(expr.line, "Undefined variable '" + expr.name + "'");
        return std::monostate{};
    }
    return var->value;
}

RuntimeValue Interpreter::evaluateAssign(AssignExpr& expr) {
    RuntimeValue value = evaluate(*expr.value);

    if (expr.target->exprType == ExprType::VARIABLE) {
        auto& varExpr = static_cast<VariableExpr&>(*expr.target);

        // 处理复合赋值
        Variable* var = currentEnv_->get(varExpr.name);
        if (var && (expr.op.type == TokenType::PLUS_ASSIGN ||
                    expr.op.type == TokenType::MINUS_ASSIGN ||
                    expr.op.type == TokenType::MUL_ASSIGN ||
                    expr.op.type == TokenType::DIV_ASSIGN)) {
            double current = valueToNumber(var->value);
            double newVal = valueToNumber(value);

            switch (expr.op.type) {
                case TokenType::PLUS_ASSIGN: value = current + newVal; break;
                case TokenType::MINUS_ASSIGN: value = current - newVal; break;
                case TokenType::MUL_ASSIGN: value = current * newVal; break;
                case TokenType::DIV_ASSIGN:
                    if (newVal == 0) {
                        error(expr.line, "Division by zero");
                        return std::monostate{};
                    }
                    value = current / newVal;
                    break;
                default:
                    break;
            }
        }

        currentEnv_->set(varExpr.name, value);
        return value;
    }

    return value;
}

RuntimeValue Interpreter::evaluateCall(CallExpr& expr) {
    // 获取函数名
    std::string funcName;
    if (expr.callee->exprType == ExprType::VARIABLE) {
        funcName = static_cast<VariableExpr&>(*expr.callee).name;
    } else {
        error(expr.line, "Invalid function call");
        return std::monostate{};
    }

    // 求值参数
    std::vector<RuntimeValue> args;
    for (const auto& arg : expr.arguments) {
        args.push_back(evaluate(*arg));
    }

    // 尝试内置函数
    RuntimeValue result = callBuiltin(funcName, args);
    if (!std::holds_alternative<std::monostate>(result)) {
        return result;
    }

    // 查找用户定义的函数
    auto it = functionTable_.find(funcName);
    if (it != functionTable_.end()) {
        return callFunction(it->second, args);
    }

    error(expr.line, "Undefined function '" + funcName + "'");
    return std::monostate{};
}

RuntimeValue Interpreter::evaluateLogical(LogicalExpr& expr) {
    RuntimeValue left = evaluate(*expr.left);

    if (expr.op.type == TokenType::OR) {
        if (isTruthy(left)) return left;
    } else if (expr.op.type == TokenType::AND) {
        if (!isTruthy(left)) return left;
    }

    return evaluate(*expr.right);
}

RuntimeValue Interpreter::evaluateIndex(IndexExpr& expr) {
    RuntimeValue object = evaluate(*expr.object);
    RuntimeValue index = evaluate(*expr.index);

    if (std::holds_alternative<std::shared_ptr<RuntimeArray>>(object)) {
        const auto& arr = std::get<std::shared_ptr<RuntimeArray>>(object);
        if (std::holds_alternative<int64_t>(index)) {
            int64_t i = std::get<int64_t>(index);
            if (i >= 0 && i < static_cast<int64_t>(arr->elements.size())) {
                return arr->elements[i];
            }
            error(expr.line, "Array index out of bounds");
        }
    } else if (std::holds_alternative<std::string>(object)) {
        const auto& str = std::get<std::string>(object);
        if (std::holds_alternative<int64_t>(index)) {
            int64_t i = std::get<int64_t>(index);
            if (i >= 0 && i < static_cast<int64_t>(str.size())) {
                return std::string(1, str[i]);
            }
            error(expr.line, "String index out of bounds");
        }
    }

    return std::monostate{};
}

RuntimeValue Interpreter::evaluateMember(MemberExpr& expr) {
    RuntimeValue object = evaluate(*expr.object);

    // 简化处理：假设是数组的length属性
    if (expr.member == "length") {
        if (std::holds_alternative<std::shared_ptr<RuntimeArray>>(object)) {
            return static_cast<int64_t>(std::get<std::shared_ptr<RuntimeArray>>(object)->elements.size());
        }
        if (std::holds_alternative<std::string>(object)) {
            return static_cast<int64_t>(std::get<std::string>(object).size());
        }
    }

    return std::monostate{};
}

RuntimeValue Interpreter::callFunction(const FunctionObject& func,
                                        const std::vector<RuntimeValue>& args) {
    // 创建新环境
    auto env = std::make_shared<Environment>();

    // 绑定参数
    for (size_t i = 0; i < func.params.size(); ++i) {
        Variable var;
        if (i < args.size()) {
            var.value = args[i];
        } else if (func.params[i].defaultValue) {
            var.value = evaluate(*func.params[i].defaultValue);
        }
        var.type = std::make_shared<Type>(func.params[i].type->kind);
        env->define(func.params[i].name, var);
    }

    // 执行函数体
    try {
        executeBlock(static_cast<BlockStmt*>(func.body)->statements, env);
    } catch (const ReturnException& e) {
        return e.value;
    }

    return std::monostate{};
}

RuntimeValue Interpreter::callBuiltin(const std::string& name,
                                       const std::vector<RuntimeValue>& args) {
    if (name == "print") {
        for (const auto& arg : args) {
            std::string str = valueToString(arg);
            if (outputStream_) {
                *outputStream_ << str << " ";
            }
            output_.push_back(str);
        }
        if (outputStream_) {
            *outputStream_ << std::endl;
        }
        return std::monostate{};
    }

    if (name == "len") {
        if (args.size() == 1) {
            if (std::holds_alternative<std::string>(args[0])) {
                return static_cast<int64_t>(std::get<std::string>(args[0]).size());
            }
            if (std::holds_alternative<std::shared_ptr<RuntimeArray>>(args[0])) {
                return static_cast<int64_t>(std::get<std::shared_ptr<RuntimeArray>>(args[0])->elements.size());
            }
        }
        return std::monostate{};
    }

    if (name == "str") {
        if (args.size() == 1) {
            return valueToString(args[0]);
        }
        return std::monostate{};
    }

    if (name == "int") {
        if (args.size() == 1) {
            return static_cast<int64_t>(valueToNumber(args[0]));
        }
        return std::monostate{};
    }

    if (name == "float") {
        if (args.size() == 1) {
            return valueToNumber(args[0]);
        }
        return std::monostate{};
    }

    if (name == "abs") {
        if (args.size() == 1) {
            return std::abs(valueToNumber(args[0]));
        }
        return std::monostate{};
    }

    if (name == "sqrt") {
        if (args.size() == 1) {
            return std::sqrt(valueToNumber(args[0]));
        }
        return std::monostate{};
    }

    if (name == "pow") {
        if (args.size() == 2) {
            return std::pow(valueToNumber(args[0]), valueToNumber(args[1]));
        }
        return std::monostate{};
    }

    return std::monostate{};
}

bool Interpreter::isTruthy(const RuntimeValue& value) const {
    if (std::holds_alternative<std::monostate>(value)) return false;
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value);
    if (std::holds_alternative<int64_t>(value)) return std::get<int64_t>(value) != 0;
    if (std::holds_alternative<double>(value)) return std::get<double>(value) != 0.0;
    if (std::holds_alternative<std::string>(value)) return !std::get<std::string>(value).empty();
    return true;
}

std::string Interpreter::valueToString(const RuntimeValue& value) const {
    if (std::holds_alternative<std::monostate>(value)) return "null";
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value) ? "true" : "false";
    if (std::holds_alternative<int64_t>(value)) return std::to_string(std::get<int64_t>(value));
    if (std::holds_alternative<double>(value)) {
        std::ostringstream oss;
        oss << std::get<double>(value);
        return oss.str();
    }
    if (std::holds_alternative<std::string>(value)) return std::get<std::string>(value);
    if (std::holds_alternative<std::shared_ptr<RuntimeArray>>(value)) {
        std::string result = "[";
        const auto& arr = std::get<std::shared_ptr<RuntimeArray>>(value);
        for (size_t i = 0; i < arr->elements.size(); ++i) {
            if (i > 0) result += ", ";
            result += valueToString(arr->elements[i]);
        }
        return result + "]";
    }
    return "object";
}

double Interpreter::valueToNumber(const RuntimeValue& value) const {
    if (std::holds_alternative<int64_t>(value)) return static_cast<double>(std::get<int64_t>(value));
    if (std::holds_alternative<double>(value)) return std::get<double>(value);
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value) ? 1.0 : 0.0;
    if (std::holds_alternative<std::string>(value)) {
        try {
            return std::stod(std::get<std::string>(value));
        } catch (...) {
            return 0.0;
        }
    }
    return 0.0;
}

void Interpreter::registerBuiltins() {
    // 内置函数在callBuiltin中处理
}

// ==================== StackVM ====================

StackVM::StackVM() : bytecode_(nullptr), pc_(0) {}

bool StackVM::execute(const Bytecode& bytecode) {
    bytecode_ = &bytecode;
    pc_ = 0;
    stack_.clear();
    callStack_.clear();

    // 创建主调用帧
    CallFrame mainFrame;
    mainFrame.returnAddress = -1;
    mainFrame.basePointer = 0;
    callStack_.push_back(mainFrame);

    while (pc_ < static_cast<int>(bytecode_->instructions.size())) {
        const auto& instr = bytecode_->instructions[pc_];

        if (!executeInstruction(instr)) {
            return false;
        }

        // 检查HALT
        if (instr.opcode == Opcode::HALT) {
            break;
        }

        pc_++;
    }

    return errors_.empty();
}

bool StackVM::executeInstruction(const Instruction& instruction) {
    switch (instruction.opcode) {
        case Opcode::NOP:
            break;

        case Opcode::LOAD_CONST:
            push(bytecode_->constants[instruction.operand]);
            break;

        case Opcode::LOAD_TRUE:
            push(true);
            break;

        case Opcode::LOAD_FALSE:
            push(false);
            break;

        case Opcode::LOAD_NULL:
            push(std::monostate{});
            break;

        case Opcode::LOAD_VAR: {
            auto& locals = callStack_.back().locals;
            auto it = locals.find(std::to_string(instruction.operand));
            if (it != locals.end()) {
                push(it->second);
            } else {
                push(std::monostate{});
            }
            break;
        }

        case Opcode::STORE_VAR: {
            RuntimeValue value = pop();
            callStack_.back().locals[std::to_string(instruction.operand)] = value;
            break;
        }

        case Opcode::POP:
            pop();
            break;

        case Opcode::DUP:
            push(peek());
            break;

        case Opcode::SWAP: {
            RuntimeValue a = pop();
            RuntimeValue b = pop();
            push(a);
            push(b);
            break;
        }

        case Opcode::ADD: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            if (std::holds_alternative<int64_t>(left) && std::holds_alternative<int64_t>(right)) {
                push(std::get<int64_t>(left) + std::get<int64_t>(right));
            } else if (std::holds_alternative<double>(left) || std::holds_alternative<double>(right)) {
                push(valueToNumber(left) + valueToNumber(right));
            } else if (std::holds_alternative<std::string>(left) || std::holds_alternative<std::string>(right)) {
                push(valueToString(left) + valueToString(right));
            }
            break;
        }

        case Opcode::SUB: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(valueToNumber(left) - valueToNumber(right));
            break;
        }

        case Opcode::MUL: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(valueToNumber(left) * valueToNumber(right));
            break;
        }

        case Opcode::DIV: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            double r = valueToNumber(right);
            if (r == 0.0) {
                errors_.push_back("Division by zero");
                return false;
            }
            push(valueToNumber(left) / r);
            break;
        }

        case Opcode::MOD: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            double r = valueToNumber(right);
            if (r == 0.0) {
                errors_.push_back("Division by zero");
                return false;
            }
            push(std::fmod(valueToNumber(left), r));
            break;
        }

        case Opcode::NEG: {
            RuntimeValue value = pop();
            push(-valueToNumber(value));
            break;
        }

        case Opcode::CMP_EQ: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(valueToNumber(left) == valueToNumber(right));
            break;
        }

        case Opcode::CMP_NE: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(valueToNumber(left) != valueToNumber(right));
            break;
        }

        case Opcode::CMP_LT: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(valueToNumber(left) < valueToNumber(right));
            break;
        }

        case Opcode::CMP_LE: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(valueToNumber(left) <= valueToNumber(right));
            break;
        }

        case Opcode::CMP_GT: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(valueToNumber(left) > valueToNumber(right));
            break;
        }

        case Opcode::CMP_GE: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(valueToNumber(left) >= valueToNumber(right));
            break;
        }

        case Opcode::AND: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(isTruthy(left) && isTruthy(right));
            break;
        }

        case Opcode::OR: {
            RuntimeValue right = pop();
            RuntimeValue left = pop();
            push(isTruthy(left) || isTruthy(right));
            break;
        }

        case Opcode::NOT: {
            RuntimeValue value = pop();
            push(!isTruthy(value));
            break;
        }

        case Opcode::JUMP:
            pc_ = instruction.operand - 1; // -1因为循环会+1
            break;

        case Opcode::JUMP_IF_TRUE: {
            RuntimeValue condition = pop();
            if (isTruthy(condition)) {
                pc_ = instruction.operand - 1;
            }
            break;
        }

        case Opcode::JUMP_IF_FALSE: {
            RuntimeValue condition = pop();
            if (!isTruthy(condition)) {
                pc_ = instruction.operand - 1;
            }
            break;
        }

        case Opcode::CALL: {
            int numArgs = instruction.operand;
            CallFrame frame;
            frame.returnAddress = pc_ + 1;
            frame.basePointer = stack_.size() - numArgs;
            callStack_.push_back(frame);
            break;
        }

        case Opcode::RETURN: {
            RuntimeValue returnValue = pop();
            CallFrame frame = callStack_.back();
            callStack_.pop_back();

            // 恢复栈
            stack_.resize(frame.basePointer);

            // 推入返回值
            push(returnValue);

            // 跳转回调用点
            pc_ = frame.returnAddress - 1;
            break;
        }

        case Opcode::PRINT: {
            RuntimeValue value = pop();
            std::string str = valueToString(value);
            output_.push_back(str);
            std::cout << str << std::endl;
            break;
        }

        case Opcode::HALT:
            return true;

        default:
            errors_.push_back("Unknown opcode");
            return false;
    }

    return true;
}

RuntimeValue StackVM::pop() {
    if (stack_.empty()) {
        errors_.push_back("Stack underflow");
        return std::monostate{};
    }
    RuntimeValue value = stack_.back();
    stack_.pop_back();
    return value;
}

void StackVM::push(const RuntimeValue& value) {
    stack_.push_back(value);
}

RuntimeValue StackVM::peek() const {
    if (stack_.empty()) {
        return std::monostate{};
    }
    return stack_.back();
}

bool StackVM::isTruthy(const RuntimeValue& value) const {
    if (std::holds_alternative<std::monostate>(value)) return false;
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value);
    if (std::holds_alternative<int64_t>(value)) return std::get<int64_t>(value) != 0;
    if (std::holds_alternative<double>(value)) return std::get<double>(value) != 0.0;
    if (std::holds_alternative<std::string>(value)) return !std::get<std::string>(value).empty();
    return true;
}

double StackVM::valueToNumber(const RuntimeValue& value) const {
    if (std::holds_alternative<int64_t>(value)) return static_cast<double>(std::get<int64_t>(value));
    if (std::holds_alternative<double>(value)) return std::get<double>(value);
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value) ? 1.0 : 0.0;
    if (std::holds_alternative<std::string>(value)) {
        try {
            return std::stod(std::get<std::string>(value));
        } catch (...) {
            return 0.0;
        }
    }
    return 0.0;
}

std::string StackVM::valueToString(const RuntimeValue& value) const {
    if (std::holds_alternative<std::monostate>(value)) return "null";
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value) ? "true" : "false";
    if (std::holds_alternative<int64_t>(value)) return std::to_string(std::get<int64_t>(value));
    if (std::holds_alternative<double>(value)) {
        std::ostringstream oss;
        oss << std::get<double>(value);
        return oss.str();
    }
    if (std::holds_alternative<std::string>(value)) return std::get<std::string>(value);
    return "object";
}

// ==================== RegisterVM ====================

RegisterVM::RegisterVM() : bytecode_(nullptr), pc_(0) {
    registers_.resize(256); // 256个寄存器
}

bool RegisterVM::execute(const Bytecode& bytecode) {
    bytecode_ = &bytecode;
    pc_ = 0;

    while (pc_ < static_cast<int>(bytecode_->instructions.size())) {
        const auto& instr = bytecode_->instructions[pc_];

        if (!executeInstruction(instr)) {
            return false;
        }

        if (instr.opcode == Opcode::HALT) {
            break;
        }

        pc_++;
    }

    return errors_.empty();
}

bool RegisterVM::executeInstruction(const Instruction& instruction) {
    switch (instruction.opcode) {
        case Opcode::NOP:
            break;

        case Opcode::LOAD:
            registers_[instruction.dest] = bytecode_->constants[instruction.immediate];
            break;

        case Opcode::MOVE:
            registers_[instruction.dest] = registers_[instruction.src1];
            break;

        case Opcode::ADD:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) +
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::SUB:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) -
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::MUL:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) *
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::DIV: {
            double right = valueToNumber(registers_[instruction.src2]);
            if (right == 0.0) {
                errors_.push_back("Division by zero");
                return false;
            }
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) / right;
            break;
        }

        case Opcode::MOD: {
            double right = valueToNumber(registers_[instruction.src2]);
            if (right == 0.0) {
                errors_.push_back("Division by zero");
                return false;
            }
            registers_[instruction.dest] = std::fmod(
                valueToNumber(registers_[instruction.src1]), right);
            break;
        }

        case Opcode::NEG:
            registers_[instruction.dest] = -valueToNumber(registers_[instruction.src1]);
            break;

        case Opcode::CMP_EQ:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) ==
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::CMP_NE:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) !=
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::CMP_LT:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) <
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::CMP_LE:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) <=
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::CMP_GT:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) >
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::CMP_GE:
            registers_[instruction.dest] = valueToNumber(registers_[instruction.src1]) >=
                                           valueToNumber(registers_[instruction.src2]);
            break;

        case Opcode::AND:
            registers_[instruction.dest] = isTruthy(registers_[instruction.src1]) &&
                                           isTruthy(registers_[instruction.src2]);
            break;

        case Opcode::OR:
            registers_[instruction.dest] = isTruthy(registers_[instruction.src1]) ||
                                           isTruthy(registers_[instruction.src2]);
            break;

        case Opcode::NOT:
            registers_[instruction.dest] = !isTruthy(registers_[instruction.src1]);
            break;

        case Opcode::JUMP:
            pc_ = instruction.immediate - 1;
            break;

        case Opcode::JUMP_IF_TRUE:
            if (isTruthy(registers_[instruction.dest])) {
                pc_ = instruction.immediate - 1;
            }
            break;

        case Opcode::JUMP_IF_FALSE:
            if (!isTruthy(registers_[instruction.dest])) {
                pc_ = instruction.immediate - 1;
            }
            break;

        case Opcode::PRINT: {
            std::string str = valueToString(registers_[instruction.dest]);
            output_.push_back(str);
            std::cout << str << std::endl;
            break;
        }

        case Opcode::HALT:
            return true;

        default:
            errors_.push_back("Unknown opcode");
            return false;
    }

    return true;
}

bool RegisterVM::isTruthy(const RuntimeValue& value) const {
    if (std::holds_alternative<std::monostate>(value)) return false;
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value);
    if (std::holds_alternative<int64_t>(value)) return std::get<int64_t>(value) != 0;
    if (std::holds_alternative<double>(value)) return std::get<double>(value) != 0.0;
    if (std::holds_alternative<std::string>(value)) return !std::get<std::string>(value).empty();
    return true;
}

double RegisterVM::valueToNumber(const RuntimeValue& value) const {
    if (std::holds_alternative<int64_t>(value)) return static_cast<double>(std::get<int64_t>(value));
    if (std::holds_alternative<double>(value)) return std::get<double>(value);
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value) ? 1.0 : 0.0;
    if (std::holds_alternative<std::string>(value)) {
        try {
            return std::stod(std::get<std::string>(value));
        } catch (...) {
            return 0.0;
        }
    }
    return 0.0;
}

std::string RegisterVM::valueToString(const RuntimeValue& value) const {
    if (std::holds_alternative<std::monostate>(value)) return "null";
    if (std::holds_alternative<bool>(value)) return std::get<bool>(value) ? "true" : "false";
    if (std::holds_alternative<int64_t>(value)) return std::to_string(std::get<int64_t>(value));
    if (std::holds_alternative<double>(value)) {
        std::ostringstream oss;
        oss << std::get<double>(value);
        return oss.str();
    }
    if (std::holds_alternative<std::string>(value)) return std::get<std::string>(value);
    return "object";
}

} // namespace compiler
