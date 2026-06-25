#pragma once

#include "ast.hpp"
#include <memory>
#include <unordered_map>
#include <vector>
#include <variant>
#include <functional>
#include <iostream>

namespace compiler {

/**
 * 运行时值类型
 */
struct RuntimeArray;  // 前向声明

using RuntimeValue = std::variant<
    std::monostate,         // void/null
    int64_t,                // 整数
    double,                 // 浮点数
    bool,                   // 布尔值
    std::string,            // 字符串
    std::shared_ptr<RuntimeArray>,  // 数组
    void*                   // 对象指针
>;

/**
 * 运行时数组
 */
struct RuntimeArray {
    std::vector<RuntimeValue> elements;
};

/**
 * 变量信息
 */
struct Variable {
    RuntimeValue value;
    bool isConst;
    std::shared_ptr<Type> type;

    Variable() : isConst(false) {}
    Variable(RuntimeValue value, bool isConst, std::shared_ptr<Type> type = nullptr)
        : value(std::move(value)), isConst(isConst), type(std::move(type)) {}
};

/**
 * 函数对象
 */
struct FunctionObject {
    std::string name;
    std::vector<Parameter> params;
    Stmt* body;  // 原始指针，不拥有所有权
    std::shared_ptr<std::unordered_map<std::string, Variable>> closure;

    FunctionObject() : body(nullptr) {}
    FunctionObject(const std::string& name, std::vector<Parameter> params,
                   Stmt* body, std::shared_ptr<std::unordered_map<std::string, Variable>> closure)
        : name(name), params(std::move(params)), body(body),
          closure(std::move(closure)) {}
};

/**
 * 类实例
 */
struct ClassInstance {
    std::string className;
    std::unordered_map<std::string, Variable> fields;
    std::unordered_map<std::string, FunctionObject> methods;

    ClassInstance() = default;
    ClassInstance(const std::string& className) : className(className) {}
};

/**
 * 环境（作用域）
 */
class Environment {
public:
    /**
     * 构造函数
     * @param parent 父环境
     */
    explicit Environment(std::shared_ptr<Environment> parent = nullptr)
        : parent_(parent) {}

    /**
     * 定义变量
     */
    void define(const std::string& name, const Variable& variable);

    /**
     * 获取变量
     */
    Variable* get(const std::string& name);

    /**
     * 设置变量值
     */
    void set(const std::string& name, const RuntimeValue& value);

    /**
     * 在指定距离的环境中设置变量
     */
    void setAt(int distance, const std::string& name, const RuntimeValue& value);

    /**
     * 获取指定距离的环境
     */
    Environment* ancestor(int distance);

    /**
     * 获取父环境
     */
    std::shared_ptr<Environment> getParent() const { return parent_; }

    /**
     * 获取所有变量（用于闭包捕获）
     */
    const std::unordered_map<std::string, Variable>& getVariables() const { return variables_; }

private:
    std::unordered_map<std::string, Variable> variables_;
    std::shared_ptr<Environment> parent_;
};

/**
 * 返回值异常（用于实现return语句）
 */
struct ReturnException {
    RuntimeValue value;

    ReturnException(RuntimeValue value) : value(std::move(value)) {}
};

/**
 * break异常（用于实现break语句）
 */
struct BreakException {};

/**
 * continue异常（用于实现continue语句）
 */
struct ContinueException {};

/**
 * 解释器
 *
 * 职责：
 * 1. 直接解释执行AST
 * 2. 管理运行时环境
 * 3. 处理函数调用
 * 4. 处理类和对象
 */
class Interpreter {
public:
    Interpreter();

    /**
     * 解释执行程序
     * @param program AST根节点
     * @return 是否成功执行
     */
    bool interpret(Program& program);

    /**
     * 获取错误信息
     */
    const std::vector<std::string>& getErrors() const { return errors_; }

    /**
     * 获取输出
     */
    const std::vector<std::string>& getOutput() const { return output_; }

    /**
     * 设置标准输出流
     */
    void setOutputStream(std::ostream* os) { outputStream_ = os; }

private:
    // 全局环境
    std::shared_ptr<Environment> globalEnv_;

    // 当前环境
    std::shared_ptr<Environment> currentEnv_;

    // 函数表
    std::unordered_map<std::string, FunctionObject> functionTable_;

    // 错误信息
    std::vector<std::string> errors_;

    // 输出
    std::vector<std::string> output_;
    std::ostream* outputStream_;

    // 辅助方法

    /**
     * 报告错误
     */
    void error(int line, const std::string& message);

    /**
     * 执行语句
     */
    void execute(Stmt& stmt);

    /**
     * 执行块语句
     */
    void executeBlock(const std::vector<StmtPtr>& statements,
                      std::shared_ptr<Environment> env);

    /**
     * 求值表达式
     */
    RuntimeValue evaluate(Expr& expr);

    /**
     * 执行变量声明
     */
    void executeVarDecl(VarDeclStmt& stmt);

    /**
     * 执行函数声明
     */
    void executeFunction(FunctionStmt& stmt);

    /**
     * 执行类声明
     */
    void executeClass(ClassStmt& stmt);

    /**
     * 执行if语句
     */
    void executeIf(IfStmt& stmt);

    /**
     * 执行while循环
     */
    void executeWhile(WhileStmt& stmt);

    /**
     * 执行for循环
     */
    void executeFor(ForStmt& stmt);

    /**
     * 执行return语句
     */
    void executeReturn(ReturnStmt& stmt);

    /**
     * 执行print语句
     */
    void executePrint(PrintStmt& stmt);

    /**
     * 求值字面量
     */
    RuntimeValue evaluateLiteral(LiteralExpr& expr);

    /**
     * 求值二元表达式
     */
    RuntimeValue evaluateBinary(BinaryExpr& expr);

    /**
     * 求值一元表达式
     */
    RuntimeValue evaluateUnary(UnaryExpr& expr);

    /**
     * 求值变量
     */
    RuntimeValue evaluateVariable(VariableExpr& expr);

    /**
     * 求值赋值
     */
    RuntimeValue evaluateAssign(AssignExpr& expr);

    /**
     * 求值函数调用
     */
    RuntimeValue evaluateCall(CallExpr& expr);

    /**
     * 求值逻辑表达式
     */
    RuntimeValue evaluateLogical(LogicalExpr& expr);

    /**
     * 求值索引表达式
     */
    RuntimeValue evaluateIndex(IndexExpr& expr);

    /**
     * 求值成员访问
     */
    RuntimeValue evaluateMember(MemberExpr& expr);

    /**
     * 调用函数
     */
    RuntimeValue callFunction(const FunctionObject& func,
                              const std::vector<RuntimeValue>& args);

    /**
     * 调用内置函数
     */
    RuntimeValue callBuiltin(const std::string& name,
                             const std::vector<RuntimeValue>& args);

    /**
     * 检查值是否为真
     */
    bool isTruthy(const RuntimeValue& value) const;

    /**
     * 值转字符串
     */
    std::string valueToString(const RuntimeValue& value) const;

    /**
     * 值转数字
     */
    double valueToNumber(const RuntimeValue& value) const;

    /**
     * 注册内置函数
     */
    void registerBuiltins();
};

/**
 * 栈式虚拟机
 * 基于栈的字节码虚拟机
 */
class StackVM {
public:
    /**
     * 字节码操作码
     */
    enum class Opcode : uint8_t {
        NOP = 0,

        // 常量加载
        LOAD_CONST,         // 加载常量
        LOAD_TRUE,          // 加载true
        LOAD_FALSE,         // 加载false
        LOAD_NULL,          // 加载null

        // 变量操作
        LOAD_VAR,           // 加载变量
        STORE_VAR,          // 存储变量
        LOAD_GLOBAL,        // 加载全局变量
        STORE_GLOBAL,       // 存储全局变量

        // 栈操作
        POP,                // 弹出栈顶
        DUP,                // 复制栈顶
        SWAP,               // 交换栈顶两个值

        // 算术运算
        ADD,
        SUB,
        MUL,
        DIV,
        MOD,
        NEG,

        // 比较运算
        CMP_EQ,
        CMP_NE,
        CMP_LT,
        CMP_LE,
        CMP_GT,
        CMP_GE,

        // 逻辑运算
        AND,
        OR,
        NOT,

        // 控制流
        JUMP,               // 无条件跳转
        JUMP_IF_TRUE,       // 条件为真跳转
        JUMP_IF_FALSE,      // 条件为假跳转

        // 函数调用
        CALL,               // 调用函数
        RETURN,             // 返回
        BUILD_ARGS,         // 构建参数列表

        // 数组操作
        BUILD_ARRAY,        // 构建数组
        ARRAY_GET,          // 获取数组元素
        ARRAY_SET,          // 设置数组元素

        // 输出
        PRINT,

        // 特殊
        HALT,               // 停止执行
    };

    /**
     * 字节码指令
     */
    struct Instruction {
        Opcode opcode;
        int operand;        // 操作数（跳转地址、常量索引等）
        int line;           // 源代码行号

        Instruction() : opcode(Opcode::NOP), operand(0), line(0) {}
        Instruction(Opcode opcode, int operand = 0, int line = 0)
            : opcode(opcode), operand(operand), line(line) {}
    };

    /**
     * 字节码程序
     */
    struct Bytecode {
        std::vector<Instruction> instructions;
        std::vector<RuntimeValue> constants;
        std::unordered_map<std::string, int> globals;
    };

    StackVM();

    /**
     * 执行字节码
     */
    bool execute(const Bytecode& bytecode);

    /**
     * 获取输出
     */
    const std::vector<std::string>& getOutput() const { return output_; }

    /**
     * 获取错误
     */
    const std::vector<std::string>& getErrors() const { return errors_; }

private:
    // 当前字节码
    const Bytecode* bytecode_;

    // 运行时栈
    std::vector<RuntimeValue> stack_;

    // 调用栈
    struct CallFrame {
        int returnAddress;
        int basePointer;
        std::unordered_map<std::string, RuntimeValue> locals;
    };
    std::vector<CallFrame> callStack_;

    // 程序计数器
    int pc_;

    // 输出
    std::vector<std::string> output_;
    std::vector<std::string> errors_;

    /**
     * 执行单条指令
     */
    bool executeInstruction(const Instruction& instruction);

    /**
     * 栈操作辅助
     */
    RuntimeValue pop();
    void push(const RuntimeValue& value);
    RuntimeValue peek() const;

    /**
     * 值转换辅助
     */
    bool isTruthy(const RuntimeValue& value) const;
    double valueToNumber(const RuntimeValue& value) const;
    std::string valueToString(const RuntimeValue& value) const;
};

/**
 * 寄存式虚拟机
 * 基于寄存器的字节码虚拟机
 */
class RegisterVM {
public:
    /**
     * 字节码操作码
     */
    enum class Opcode : uint8_t {
        NOP = 0,

        // 数据传送
        LOAD,               // R[dest] = constant
        MOVE,               // R[dest] = R[src]
        LOAD_VAR,           // R[dest] = var[name]
        STORE_VAR,          // var[name] = R[src]

        // 算术运算
        ADD,                // R[dest] = R[src1] + R[src2]
        SUB,
        MUL,
        DIV,
        MOD,
        NEG,                // R[dest] = -R[src]

        // 比较运算
        CMP_EQ,             // R[dest] = R[src1] == R[src2]
        CMP_NE,
        CMP_LT,
        CMP_LE,
        CMP_GT,
        CMP_GE,

        // 逻辑运算
        AND,
        OR,
        NOT,

        // 控制流
        JUMP,
        JUMP_IF_TRUE,
        JUMP_IF_FALSE,

        // 函数调用
        CALL,
        RETURN,

        // 输出
        PRINT,

        // 特殊
        HALT,
    };

    /**
     * 字节码指令
     */
    struct Instruction {
        Opcode opcode;
        int dest;           // 目标寄存器
        int src1;           // 源寄存器1
        int src2;           // 源寄存器2
        int64_t immediate;  // 立即数
        int line;           // 源代码行号

        Instruction() : opcode(Opcode::NOP), dest(0), src1(0),
                        src2(0), immediate(0), line(0) {}
    };

    /**
     * 字节码程序
     */
    struct Bytecode {
        std::vector<Instruction> instructions;
        std::vector<RuntimeValue> constants;
        int numRegisters;
    };

    RegisterVM();

    /**
     * 执行字节码
     */
    bool execute(const Bytecode& bytecode);

    /**
     * 获取输出
     */
    const std::vector<std::string>& getOutput() const { return output_; }

    /**
     * 获取错误
     */
    const std::vector<std::string>& getErrors() const { return errors_; }

private:
    // 当前字节码
    const Bytecode* bytecode_;

    // 寄存器文件
    std::vector<RuntimeValue> registers_;

    // 程序计数器
    int pc_;

    // 输出
    std::vector<std::string> output_;
    std::vector<std::string> errors_;

    /**
     * 执行单条指令
     */
    bool executeInstruction(const Instruction& instruction);

    /**
     * 值转换辅助
     */
    bool isTruthy(const RuntimeValue& value) const;
    double valueToNumber(const RuntimeValue& value) const;
    std::string valueToString(const RuntimeValue& value) const;
};

} // namespace compiler
