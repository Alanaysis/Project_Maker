#pragma once

#include "ir.hpp"
#include <string>
#include <vector>
#include <unordered_map>
#include <sstream>

namespace compiler {

/**
 * 寄存器类型
 */
enum class Register {
    // 通用寄存器 (x86-64)
    RAX, RBX, RCX, RDX,
    RSI, RDI, RBP, RSP,
    R8, R9, R10, R11,
    R12, R13, R14, R15,

    // 浮点寄存器
    XMM0, XMM1, XMM2, XMM3,
    XMM4, XMM5, XMM6, XMM7,

    // 特殊寄存器
    RIP,    // 指令指针
    EFLAGS, // 标志寄存器

    // 虚拟寄存器（用于寄存器分配前）
    VIRTUAL,
};

/**
 * 操作数类型
 */
enum class OperandType {
    REGISTER,       // 寄存器
    IMMEDIATE,      // 立即数
    MEMORY,         // 内存地址
    LABEL,          // 标签
    STACK,          // 栈偏移
};

/**
 * 操作数
 */
struct Operand {
    OperandType type;
    Register reg;               // 寄存器
    int64_t immediate;          // 立即数
    std::string label;          // 标签名
    int stackOffset;            // 栈偏移
    int virtualReg;             // 虚拟寄存器号
    bool isFloat;               // 是否是浮点操作

    Operand() : type(OperandType::REGISTER), reg(Register::RAX),
                immediate(0), stackOffset(0), virtualReg(-1), isFloat(false) {}

    static Operand regOp(Register reg) {
        Operand op;
        op.type = OperandType::REGISTER;
        op.reg = reg;
        return op;
    }

    static Operand immOp(int64_t value) {
        Operand op;
        op.type = OperandType::IMMEDIATE;
        op.immediate = value;
        return op;
    }

    static Operand memOp(Register base, int offset) {
        Operand op;
        op.type = OperandType::MEMORY;
        op.reg = base;
        op.stackOffset = offset;
        return op;
    }

    static Operand labelOp(const std::string& label) {
        Operand op;
        op.type = OperandType::LABEL;
        op.label = label;
        return op;
    }

    static Operand stackOp(int offset) {
        Operand op;
        op.type = OperandType::STACK;
        op.stackOffset = offset;
        return op;
    }

    static Operand virtOp(int regNum, bool isFloat = false) {
        Operand op;
        op.type = OperandType::REGISTER;
        op.reg = Register::VIRTUAL;
        op.virtualReg = regNum;
        op.isFloat = isFloat;
        return op;
    }

    /**
     * 获取操作数的字符串表示
     */
    std::string toString() const;
};

/**
 * 汇编指令类型
 */
enum class AsmOpcode {
    // 数据传送
    MOV, MOVZX, MOVSX, LEA,
    PUSH, POP,

    // 算术运算
    ADD, SUB, IMUL, IDIV,
    INC, DEC, NEG,

    // 逻辑运算
    AND, OR, XOR, NOT,
    SHL, SHR, SAR,

    // 比较
    CMP, TEST,

    // 跳转
    JMP, JE, JNE, JL, JLE, JG, JGE,
    JB, JBE, JA, JAE,
    JZ, JNZ,

    // 函数调用
    CALL, RET,

    // 栈帧
    ENTER, LEAVE,

    // 浮点运算
    ADDSD, SUBSD, MULSD, DIVSD,
    MOVSD, UCOMISD,
    CVTSI2SD, CVTSD2SI,

    // 特殊
    NOP, LABEL, COMMENT,
    SYSCALL,
};

/**
 * 汇编指令
 */
struct AsmInstruction {
    AsmOpcode opcode;
    Operand dest;
    Operand src;
    std::string comment;        // 注释
    std::string label;          // 标签（仅用于LABEL指令）

    AsmInstruction() : opcode(AsmOpcode::NOP) {}

    AsmInstruction(AsmOpcode opcode, const Operand& dest = Operand(),
                   const Operand& src = Operand(), const std::string& comment = "")
        : opcode(opcode), dest(dest), src(src), comment(comment) {}

    /**
     * 获取指令的字符串表示
     */
    std::string toString() const;
};

/**
 * 栈帧信息
 */
struct StackFrame {
    int totalSize;              // 总大小
    int localVarsSize;          // 局部变量区大小
    int paramsSize;             // 参数区大小
    int savedRegsSize;          // 保存寄存器区大小
    std::unordered_map<std::string, int> varOffsets;  // 变量栈偏移

    StackFrame() : totalSize(0), localVarsSize(0),
                   paramsSize(0), savedRegsSize(0) {}
};

/**
 * 寄存器分配器
 * 实现简单的线性扫描寄存器分配算法
 */
class RegisterAllocator {
public:
    /**
     * 分配寄存器
     * @param function IR函数
     * @return 虚拟寄存器到物理寄存器的映射
     */
    std::unordered_map<int, Register> allocate(const IRFunction& function);

private:
    /**
     * 活跃区间
     */
    struct LiveInterval {
        int vreg;               // 虚拟寄存器号
        int start;              // 开始位置
        int end;                // 结束位置
        bool isFloat;           // 是否是浮点寄存器
    };

    /**
     * 计算活跃区间
     */
    std::vector<LiveInterval> computeLiveIntervals(const IRFunction& function);

    /**
     * 线性扫描分配
     */
    std::unordered_map<int, Register> linearScan(
        const std::vector<LiveInterval>& intervals);
};

/**
 * x86-64代码生成器
 * 将IR转换为x86-64汇编代码
 */
class CodeGenerator {
public:
    CodeGenerator();

    /**
     * 生成汇编代码
     * @param module IR模块
     * @return 汇编代码字符串
     */
    std::string generate(const IRModule& module);

    /**
     * 生成单个函数的汇编代码
     */
    std::string generateFunction(const IRFunction& function);

    /**
     * 获取错误信息
     */
    const std::vector<std::string>& getErrors() const { return errors_; }

private:
    // 输出流
    std::ostringstream output_;

    // 寄存器分配器
    RegisterAllocator allocator_;

    // 寄存器映射（虚拟寄存器 -> 物理寄存器）
    std::unordered_map<int, Register> registerMap_;

    // 栈帧信息
    StackFrame frame_;

    // 错误信息
    std::vector<std::string> errors_;

    // 辅助方法

    /**
     * 输出汇编指令
     */
    void emit(const AsmInstruction& instruction);

    /**
     * 输出注释
     */
    void emitComment(const std::string& comment);

    /**
     * 输出标签
     */
    void emitLabel(const std::string& label);

    /**
     * 生成函数序言
     */
    void generatePrologue(const IRFunction& function);

    /**
     * 生成函数尾声
     */
    void generateEpilogue();

    /**
     * 将IRValue转换为汇编操作数
     */
    Operand irValueToOperand(const IRValue& value);

    /**
     * 将IROpcode转换为汇编操作码
     */
    AsmOpcode irOpcodeToAsm(IROpcode opcode, bool isFloat = false);

    /**
     * 生成单条IR指令的汇编代码
     */
    void generateInstruction(const IRInstruction& instruction);

    /**
     * 计算栈帧大小
     */
    void computeStackFrame(const IRFunction& function);

    /**
     * 获取操作数大小后缀
     */
    std::string getSizeSuffix(int size) const;
};

/**
 * 获取寄存器名称（自由函数）
 */
std::string getRegisterName(Register reg);

} // namespace compiler
