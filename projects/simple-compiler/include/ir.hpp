#pragma once

#include "ast.hpp"
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <variant>
#include <iostream>

namespace compiler {

/**
 * IR值类型
 * 表示中间代码中的值
 */
enum class IRValueType {
    VOID,
    INT,
    FLOAT,
    STRING,
    BOOL,
    POINTER,
    LABEL,
    FUNCTION,
};

/**
 * IR操作码
 * 定义所有中间代码操作
 */
enum class IROpcode {
    // 算术运算
    ADD,            // a = b + c
    SUB,            // a = b - c
    MUL,            // a = b * c
    DIV,            // a = b / c
    MOD,            // a = b % c
    NEG,            // a = -b

    // 比较运算
    CMP_EQ,         // a = (b == c)
    CMP_NE,         // a = (b != c)
    CMP_LT,         // a = (b < c)
    CMP_LE,         // a = (b <= c)
    CMP_GT,         // a = (b > c)
    CMP_GE,         // a = (b >= c)

    // 逻辑运算
    AND,            // a = b && c
    OR,             // a = b || c
    NOT,            // a = !b

    // 位运算
    BIT_AND,        // a = b & c
    BIT_OR,         // a = b | c
    BIT_XOR,        // a = b ^ c
    BIT_NOT,        // a = ~b
    SHL,            // a = b << c
    SHR,            // a = b >> c

    // 赋值
    LOAD,           // a = constant
    MOVE,           // a = b
    LOAD_VAR,       // a = [var_name]
    STORE_VAR,      // [var_name] = a

    // 内存操作
    ALLOCA,         // a = alloca size
    LOAD_MEM,       // a = [b]
    STORE_MEM,      // [a] = b
    GEP,            // a = b + offset (Get Element Pointer)

    // 控制流
    LABEL,          // label:
    JUMP,           // goto label
    BRANCH,         // if (cond) goto label1 else goto label2
    CALL,           // a = call func(args...)
    RETURN,         // return a

    // 函数定义
    FUNC_BEGIN,     // func_name:
    FUNC_END,       // end func_name
    PARAM,          // 参数声明
    ARG,            // 函数调用参数

    // 数组操作
    ARRAY_NEW,      // a = new array[size]
    ARRAY_LOAD,     // a = array[index]
    ARRAY_STORE,    // array[index] = value

    // 特殊操作
    NOP,            // 空操作
    PHI,            // SSA phi函数
    CAST,           // 类型转换
    PRINT,          // 打印值

    // 优化相关
    CONST_FOLD,     // 常量折叠标记
    DEAD_CODE,      // 死代码标记
};

/**
 * IR值
 * 表示中间代码中的一个值（变量、常量、临时变量）
 */
struct IRValue {
    std::string name;           // 值名称
    IRValueType type;           // 值类型
    bool isConstant;            // 是否是常量
    bool isTemporary;           // 是否是临时变量

    // 常量值
    union {
        int64_t intValue;
        double floatValue;
        bool boolValue;
    } constant;

    // SSA相关
    int version;                // SSA版本号
    std::vector<int> uses;     // 使用列表

    IRValue() : type(IRValueType::VOID), isConstant(false),
                isTemporary(false), version(0) {
        constant.intValue = 0;
    }

    IRValue(const std::string& name, IRValueType type)
        : name(name), type(type), isConstant(false),
          isTemporary(false), version(0) {
        constant.intValue = 0;
    }
};

/**
 * IR指令
 * 表示一条中间代码指令
 */
struct IRInstruction {
    IROpcode opcode;                    // 操作码
    IRValue result;                     // 结果
    std::vector<IRValue> operands;      // 操作数
    int line;                           // 源代码行号（用于调试）

    // SSA相关
    int basicBlockId;                   // 所属基本块ID

    // 优化相关
    bool isDead;                        // 是否被标记为死代码
    bool isConstFolded;                 // 是否已常量折叠

    IRInstruction() : opcode(IROpcode::NOP), line(0),
                      basicBlockId(-1), isDead(false), isConstFolded(false) {}

    IRInstruction(IROpcode opcode, const IRValue& result,
                  std::vector<IRValue> operands, int line = 0)
        : opcode(opcode), result(result), operands(std::move(operands)),
          line(line), basicBlockId(-1), isDead(false), isConstFolded(false) {}

    /**
     * 获取指令的字符串表示
     */
    std::string toString() const;
};

/**
 * 基本块
 * 一系列顺序执行的指令，只有一个入口和一个出口
 */
struct BasicBlock {
    int id;                                 // 基本块ID
    std::string label;                      // 标签名称
    std::vector<IRInstruction> instructions; // 指令列表

    // 控制流图
    std::vector<int> predecessors;          // 前驱基本块
    std::vector<int> successors;            // 后继基本块

    // 优化相关
    bool isDead;                            // 是否不可达
    int executionFrequency;                 // 执行频率估计

    BasicBlock() : id(-1), isDead(false), executionFrequency(0) {}
    BasicBlock(int id, const std::string& label = "")
        : id(id), label(label), isDead(false), executionFrequency(0) {}
};

/**
 * IR函数
 * 表示一个函数的中间代码
 */
struct IRFunction {
    std::string name;                       // 函数名
    std::vector<IRValue> parameters;        // 参数列表
    IRValueType returnType;                 // 返回类型
    std::vector<BasicBlock> basicBlocks;    // 基本块列表
    int nextTempId;                         // 下一个临时变量ID
    int nextLabelId;                        // 下一个标签ID

    IRFunction() : returnType(IRValueType::VOID), nextTempId(0), nextLabelId(0) {}
    IRFunction(const std::string& name) : name(name), returnType(IRValueType::VOID),
                                           nextTempId(0), nextLabelId(0) {}

    /**
     * 创建新的临时变量
     */
    IRValue newTemp(IRValueType type) {
        IRValue temp("%t" + std::to_string(nextTempId++), type);
        temp.isTemporary = true;
        return temp;
    }

    /**
     * 创建新的标签
     */
    std::string newLabel(const std::string& prefix = "L") {
        return prefix + std::to_string(nextLabelId++);
    }
};

/**
 * IR模块
 * 表示整个程序的中间代码
 */
struct IRModule {
    std::string name;                               // 模块名
    std::unordered_map<std::string, IRFunction> functions;  // 函数表
    std::vector<IRInstruction> globalInstructions;  // 全局指令
    std::unordered_map<std::string, IRValue> globals;  // 全局变量

    IRModule() = default;
    IRModule(const std::string& name) : name(name) {}

    /**
     * 打印整个模块的IR
     */
    void print(std::ostream& out = std::cout) const;

    /**
     * 打印单个函数的IR
     */
    void printFunction(const std::string& name, std::ostream& out = std::cout) const;
};

/**
 * IR生成器
 * 将AST转换为中间代码
 */
class IRGenerator {
public:
    IRGenerator();

    /**
     * 生成IR
     * @param program AST根节点
     * @return IR模块
     */
    std::unique_ptr<IRModule> generate(const Program& program);

    /**
     * 获取错误信息
     */
    const std::vector<std::string>& getErrors() const { return errors_; }

private:
    // 当前函数
    IRFunction* currentFunction_;

    // 当前基本块
    BasicBlock* currentBlock_;

    // IR模块
    std::unique_ptr<IRModule> module_;

    // 错误信息
    std::vector<std::string> errors_;

    // 变量映射（变量名 -> IRValue）
    std::unordered_map<std::string, IRValue> variableMap_;

    // 辅助方法

    /**
     * 添加指令到当前基本块
     */
    void emit(const IRInstruction& instruction);

    /**
     * 创建新的基本块
     */
    BasicBlock* createBasicBlock(const std::string& label = "");

    /**
     * 切换到新的基本块
     */
    void switchToBlock(BasicBlock* block);

    /**
     * 生成表达式的IR
     * @return 表达式结果的IRValue
     */
    IRValue generateExpr(const Expr& expr);

    /**
     * 生成语句的IR
     */
    void generateStmt(const Stmt& stmt);

    /**
     * 生成二元表达式的IR
     */
    IRValue generateBinary(const BinaryExpr& expr);

    /**
     * 生成一元表达式的IR
     */
    IRValue generateUnary(const UnaryExpr& expr);

    /**
     * 生成函数调用的IR
     */
    IRValue generateCall(const CallExpr& expr);

    /**
     * 生成if语句的IR
     */
    void generateIf(const IfStmt& stmt);

    /**
     * 生成while循环的IR
     */
    void generateWhile(const WhileStmt& stmt);

    /**
     * 生成for循环的IR
     */
    void generateFor(const ForStmt& stmt);

    /**
     * 生成函数定义的IR
     */
    void generateFunction(const FunctionStmt& stmt);

    /**
     * 生成return语句的IR
     */
    void generateReturn(const ReturnStmt& stmt);

    /**
     * 获取操作码对应的比较类型
     */
    IROpcode getCompareOpcode(const Token& op) const;
};

} // namespace compiler
