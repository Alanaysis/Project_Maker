#include "codegen.hpp"
#include <iomanip>
#include <algorithm>

namespace compiler {

// 前向声明
std::string getRegisterName(Register reg);

// ==================== Register Name ====================

std::string getRegisterName(Register reg) {
    switch (reg) {
        case Register::RAX: return "rax";
        case Register::RBX: return "rbx";
        case Register::RCX: return "rcx";
        case Register::RDX: return "rdx";
        case Register::RSI: return "rsi";
        case Register::RDI: return "rdi";
        case Register::RBP: return "rbp";
        case Register::RSP: return "rsp";
        case Register::R8: return "r8";
        case Register::R9: return "r9";
        case Register::R10: return "r10";
        case Register::R11: return "r11";
        case Register::R12: return "r12";
        case Register::R13: return "r13";
        case Register::R14: return "r14";
        case Register::R15: return "r15";
        case Register::XMM0: return "xmm0";
        case Register::XMM1: return "xmm1";
        case Register::XMM2: return "xmm2";
        case Register::XMM3: return "xmm3";
        case Register::XMM4: return "xmm4";
        case Register::XMM5: return "xmm5";
        case Register::XMM6: return "xmm6";
        case Register::XMM7: return "xmm7";
        case Register::RIP: return "rip";
        default: return "???";
    }
}

// ==================== Operand ====================

std::string Operand::toString() const {
    switch (type) {
        case OperandType::REGISTER:
            if (reg == Register::VIRTUAL) {
                return "v" + std::to_string(virtualReg);
            }
            return getRegisterName(reg);

        case OperandType::IMMEDIATE:
            return "$" + std::to_string(immediate);

        case OperandType::MEMORY:
            return "[" + getRegisterName(reg) + " + " + std::to_string(stackOffset) + "]";

        case OperandType::LABEL:
            return label;

        case OperandType::STACK:
            return "[rbp - " + std::to_string(stackOffset) + "]";

        default:
            return "???";
    }
}

// ==================== AsmInstruction ====================

std::string AsmInstruction::toString() const {
    std::stringstream ss;

    // 标签
    if (opcode == AsmOpcode::LABEL) {
        ss << label << ":";
        if (!comment.empty()) {
            ss << " ; " << comment;
        }
        return ss.str();
    }

    // 注释
    if (opcode == AsmOpcode::COMMENT) {
        ss << "; " << comment;
        return ss.str();
    }

    // 指令助记符
    std::string mnemonic;
    switch (opcode) {
        case AsmOpcode::MOV: mnemonic = "mov"; break;
        case AsmOpcode::MOVZX: mnemonic = "movzx"; break;
        case AsmOpcode::MOVSX: mnemonic = "movsx"; break;
        case AsmOpcode::LEA: mnemonic = "lea"; break;
        case AsmOpcode::PUSH: mnemonic = "push"; break;
        case AsmOpcode::POP: mnemonic = "pop"; break;
        case AsmOpcode::ADD: mnemonic = "add"; break;
        case AsmOpcode::SUB: mnemonic = "sub"; break;
        case AsmOpcode::IMUL: mnemonic = "imul"; break;
        case AsmOpcode::IDIV: mnemonic = "idiv"; break;
        case AsmOpcode::INC: mnemonic = "inc"; break;
        case AsmOpcode::DEC: mnemonic = "dec"; break;
        case AsmOpcode::NEG: mnemonic = "neg"; break;
        case AsmOpcode::AND: mnemonic = "and"; break;
        case AsmOpcode::OR: mnemonic = "or"; break;
        case AsmOpcode::XOR: mnemonic = "xor"; break;
        case AsmOpcode::NOT: mnemonic = "not"; break;
        case AsmOpcode::SHL: mnemonic = "shl"; break;
        case AsmOpcode::SHR: mnemonic = "shr"; break;
        case AsmOpcode::SAR: mnemonic = "sar"; break;
        case AsmOpcode::CMP: mnemonic = "cmp"; break;
        case AsmOpcode::TEST: mnemonic = "test"; break;
        case AsmOpcode::JMP: mnemonic = "jmp"; break;
        case AsmOpcode::JE: mnemonic = "je"; break;
        case AsmOpcode::JNE: mnemonic = "jne"; break;
        case AsmOpcode::JL: mnemonic = "jl"; break;
        case AsmOpcode::JLE: mnemonic = "jle"; break;
        case AsmOpcode::JG: mnemonic = "jg"; break;
        case AsmOpcode::JGE: mnemonic = "jge"; break;
        case AsmOpcode::JB: mnemonic = "jb"; break;
        case AsmOpcode::JBE: mnemonic = "jbe"; break;
        case AsmOpcode::JA: mnemonic = "ja"; break;
        case AsmOpcode::JAE: mnemonic = "jae"; break;
        case AsmOpcode::JZ: mnemonic = "jz"; break;
        case AsmOpcode::JNZ: mnemonic = "jnz"; break;
        case AsmOpcode::CALL: mnemonic = "call"; break;
        case AsmOpcode::RET: mnemonic = "ret"; break;
        case AsmOpcode::ENTER: mnemonic = "enter"; break;
        case AsmOpcode::LEAVE: mnemonic = "leave"; break;
        case AsmOpcode::ADDSD: mnemonic = "addsd"; break;
        case AsmOpcode::SUBSD: mnemonic = "subsd"; break;
        case AsmOpcode::MULSD: mnemonic = "mulsd"; break;
        case AsmOpcode::DIVSD: mnemonic = "divsd"; break;
        case AsmOpcode::MOVSD: mnemonic = "movsd"; break;
        case AsmOpcode::UCOMISD: mnemonic = "ucomisd"; break;
        case AsmOpcode::CVTSI2SD: mnemonic = "cvtsi2sd"; break;
        case AsmOpcode::CVTSD2SI: mnemonic = "cvtsd2si"; break;
        case AsmOpcode::NOP: mnemonic = "nop"; break;
        case AsmOpcode::SYSCALL: mnemonic = "syscall"; break;
        default: mnemonic = "???"; break;
    }

    ss << std::setw(8) << std::left << mnemonic;

    // 操作数
    if (dest.type != OperandType::REGISTER || dest.reg != Register::RAX || dest.virtualReg != -1) {
        ss << " " << dest.toString();
        if (src.type != OperandType::REGISTER || src.reg != Register::RAX || src.virtualReg != -1) {
            ss << ", " << src.toString();
        }
    }

    // 注释
    if (!comment.empty()) {
        ss << "  ; " << comment;
    }

    return ss.str();
}

// ==================== RegisterAllocator ====================

std::unordered_map<int, Register> RegisterAllocator::allocate(const IRFunction& function) {
    auto intervals = computeLiveIntervals(function);
    return linearScan(intervals);
}

std::vector<RegisterAllocator::LiveInterval>
RegisterAllocator::computeLiveIntervals(const IRFunction& function) {
    std::vector<LiveInterval> intervals;
    std::unordered_map<int, int> firstDef;
    std::unordered_map<int, int> lastUse;

    int pos = 0;
    for (const auto& block : function.basicBlocks) {
        for (const auto& instr : block.instructions) {
            // 记录定义
            if (instr.result.isTemporary) {
                if (firstDef.find(instr.result.version) == firstDef.end()) {
                    firstDef[instr.result.version] = pos;
                }
                lastUse[instr.result.version] = pos;
            }

            // 记录使用
            for (const auto& operand : instr.operands) {
                if (operand.isTemporary) {
                    lastUse[operand.version] = pos;
                }
            }

            pos++;
        }
    }

    // 创建活跃区间
    for (const auto& [vreg, start] : firstDef) {
        LiveInterval interval;
        interval.vreg = vreg;
        interval.start = start;
        interval.end = lastUse[vreg];
        interval.isFloat = false; // 简化处理
        intervals.push_back(interval);
    }

    // 按开始位置排序
    std::sort(intervals.begin(), intervals.end(),
              [](const LiveInterval& a, const LiveInterval& b) {
                  return a.start < b.start;
              });

    return intervals;
}

std::unordered_map<int, Register>
RegisterAllocator::linearScan(const std::vector<LiveInterval>& intervals) {
    std::unordered_map<int, Register> allocation;

    // 可用寄存器列表
    std::vector<Register> freeRegs = {
        Register::RAX, Register::RBX, Register::RCX, Register::RDX,
        Register::RSI, Register::RDI, Register::R8, Register::R9,
        Register::R10, Register::R11, Register::R12, Register::R13,
        Register::R14, Register::R15
    };

    // 活跃区间列表
    struct ActiveInterval {
        LiveInterval interval;
        Register reg;
    };
    std::vector<ActiveInterval> active;

    for (const auto& interval : intervals) {
        // 移除过期的活跃区间
        active.erase(
            std::remove_if(active.begin(), active.end(),
                           [interval](const ActiveInterval& a) {
                               return a.interval.end < interval.start;
                           }),
            active.end());

        // 尝试分配寄存器
        if (!freeRegs.empty()) {
            Register reg = freeRegs.back();
            freeRegs.pop_back();
            allocation[interval.vreg] = reg;
            active.push_back({interval, reg});
        } else {
            // 溢出到栈
            allocation[interval.vreg] = Register::RAX; // 简化处理
        }
    }

    return allocation;
}

// ==================== CodeGenerator ====================

CodeGenerator::CodeGenerator() {}

std::string CodeGenerator::generate(const IRModule& module) {
    output_.str("");
    output_.clear();

    // 数据段
    output_ << "section .data" << std::endl;
    output_ << "    fmt_int db \"%ld\", 10, 0" << std::endl;
    output_ << "    fmt_float db \"%f\", 10, 0" << std::endl;
    output_ << "    fmt_string db \"%s\", 10, 0" << std::endl;
    output_ << "    fmt_true db \"true\", 10, 0" << std::endl;
    output_ << "    fmt_false db \"false\", 10, 0" << std::endl;
    output_ << std::endl;

    // BSS段
    output_ << "section .bss" << std::endl;
    output_ << "    buffer resb 256" << std::endl;
    output_ << std::endl;

    // 代码段
    output_ << "section .text" << std::endl;
    output_ << "    global main" << std::endl;
    output_ << "    extern printf" << std::endl;
    output_ << std::endl;

    // 生成每个函数
    for (const auto& [name, func] : module.functions) {
        output_ << generateFunction(func) << std::endl;
    }

    // 如果没有main函数，创建一个默认的
    if (module.functions.find("main") == module.functions.end()) {
        output_ << "main:" << std::endl;
        output_ << "    push rbp" << std::endl;
        output_ << "    mov rbp, rsp" << std::endl;
        output_ << "    xor eax, eax" << std::endl;
        output_ << "    pop rbp" << std::endl;
        output_ << "    ret" << std::endl;
    }

    return output_.str();
}

std::string CodeGenerator::generateFunction(const IRFunction& function) {
    std::ostringstream funcOutput;

    // 寄存器分配
    registerMap_ = allocator_.allocate(function);

    // 计算栈帧
    computeStackFrame(function);

    // 函数标签
    funcOutput << function.name << ":" << std::endl;

    // 函数序言
    funcOutput << "    push rbp" << std::endl;
    funcOutput << "    mov rbp, rsp" << std::endl;

    if (frame_.totalSize > 0) {
        funcOutput << "    sub rsp, " << frame_.totalSize << std::endl;
    }

    // 保存被调用者保存的寄存器
    funcOutput << "    push rbx" << std::endl;
    funcOutput << "    push r12" << std::endl;
    funcOutput << "    push r13" << std::endl;
    funcOutput << "    push r14" << std::endl;
    funcOutput << "    push r15" << std::endl;

    // 加载参数到寄存器/栈
    for (size_t i = 0; i < function.parameters.size(); ++i) {
        const auto& param = function.parameters[i];
        if (i < 6) {
            // 前6个参数通过寄存器传递
            Register paramRegs[] = {Register::RDI, Register::RSI, Register::RDX,
                                   Register::RCX, Register::R8, Register::R9};
            funcOutput << "    mov [rbp - " << frame_.varOffsets[param.name]
                       << "], " << getRegisterName(paramRegs[i]) << std::endl;
        } else {
            // 其他参数通过栈传递
            int stackOffset = 16 + (i - 6) * 8;
            funcOutput << "    mov rax, [rbp + " << stackOffset << "]" << std::endl;
            funcOutput << "    mov [rbp - " << frame_.varOffsets[param.name]
                       << "], rax" << std::endl;
        }
    }

    // 生成基本块
    for (const auto& block : function.basicBlocks) {
        // 标签
        if (!block.label.empty()) {
            funcOutput << "." << block.label << ":" << std::endl;
        }

        // 指令
        for (const auto& instr : block.instructions) {
            funcOutput << "    ";

            switch (instr.opcode) {
                case IROpcode::LOAD: {
                    if (instr.result.isConstant) {
                        funcOutput << "mov rax, " << instr.result.constant.intValue;
                    }
                    break;
                }

                case IROpcode::ADD: {
                    funcOutput << "mov rax, " << irValueToOperand(instr.operands[0]).toString() << std::endl;
                    funcOutput << "    add rax, " << irValueToOperand(instr.operands[1]).toString();
                    break;
                }

                case IROpcode::SUB: {
                    funcOutput << "mov rax, " << irValueToOperand(instr.operands[0]).toString() << std::endl;
                    funcOutput << "    sub rax, " << irValueToOperand(instr.operands[1]).toString();
                    break;
                }

                case IROpcode::MUL: {
                    funcOutput << "mov rax, " << irValueToOperand(instr.operands[0]).toString() << std::endl;
                    funcOutput << "    imul rax, " << irValueToOperand(instr.operands[1]).toString();
                    break;
                }

                case IROpcode::DIV: {
                    funcOutput << "mov rax, " << irValueToOperand(instr.operands[0]).toString() << std::endl;
                    funcOutput << "    cqo" << std::endl;
                    funcOutput << "    idiv " << irValueToOperand(instr.operands[1]).toString();
                    break;
                }

                case IROpcode::CMP_EQ: {
                    funcOutput << "mov rax, " << irValueToOperand(instr.operands[0]).toString() << std::endl;
                    funcOutput << "    cmp rax, " << irValueToOperand(instr.operands[1]).toString() << std::endl;
                    funcOutput << "    sete al" << std::endl;
                    funcOutput << "    movzx eax, al";
                    break;
                }

                case IROpcode::CMP_LT: {
                    funcOutput << "mov rax, " << irValueToOperand(instr.operands[0]).toString() << std::endl;
                    funcOutput << "    cmp rax, " << irValueToOperand(instr.operands[1]).toString() << std::endl;
                    funcOutput << "    setl al" << std::endl;
                    funcOutput << "    movzx eax, al";
                    break;
                }

                case IROpcode::JUMP: {
                    funcOutput << "jmp ." << instr.operands[0].name;
                    break;
                }

                case IROpcode::BRANCH: {
                    funcOutput << "test rax, rax" << std::endl;
                    funcOutput << "    jnz ." << instr.operands[1].name << std::endl;
                    funcOutput << "    jmp ." << instr.operands[2].name;
                    break;
                }

                case IROpcode::RETURN: {
                    if (!instr.operands.empty()) {
                        funcOutput << "mov rax, " << irValueToOperand(instr.operands[0]).toString() << std::endl;
                    }
                    funcOutput << "    jmp .epilogue";
                    break;
                }

                case IROpcode::CALL: {
                    // 简化处理
                    funcOutput << "call " << instr.operands[0].name;
                    break;
                }

                case IROpcode::PRINT: {
                    funcOutput << "mov rdi, fmt_int" << std::endl;
                    funcOutput << "    mov rsi, " << irValueToOperand(instr.operands[0]).toString() << std::endl;
                    funcOutput << "    xor eax, eax" << std::endl;
                    funcOutput << "    call printf";
                    break;
                }

                case IROpcode::STORE_VAR: {
                    funcOutput << "mov rax, " << irValueToOperand(instr.operands[1]).toString() << std::endl;
                    funcOutput << "    mov [rbp - " << frame_.varOffsets[instr.operands[0].name]
                               << "], rax";
                    break;
                }

                case IROpcode::LOAD_VAR: {
                    funcOutput << "mov rax, [rbp - " << frame_.varOffsets[instr.operands[0].name]
                               << "]";
                    break;
                }

                default:
                    funcOutput << "nop";
                    break;
            }

            funcOutput << std::endl;
        }
    }

    // 函数尾声
    funcOutput << ".epilogue:" << std::endl;
    funcOutput << "    pop r15" << std::endl;
    funcOutput << "    pop r14" << std::endl;
    funcOutput << "    pop r13" << std::endl;
    funcOutput << "    pop r12" << std::endl;
    funcOutput << "    pop rbx" << std::endl;

    if (frame_.totalSize > 0) {
        funcOutput << "    add rsp, " << frame_.totalSize << std::endl;
    }

    funcOutput << "    pop rbp" << std::endl;
    funcOutput << "    ret" << std::endl;

    return funcOutput.str();
}

Operand CodeGenerator::irValueToOperand(const IRValue& value) {
    if (value.isConstant) {
        switch (value.type) {
            case IRValueType::INT:
                return Operand::immOp(value.constant.intValue);
            case IRValueType::BOOL:
                return Operand::immOp(value.constant.boolValue ? 1 : 0);
            default:
                break;
        }
    }

    // 查找变量在栈上的位置
    auto it = frame_.varOffsets.find(value.name);
    if (it != frame_.varOffsets.end()) {
        return Operand::stackOp(it->second);
    }

    // 临时变量使用寄存器
    if (value.isTemporary) {
        auto regIt = registerMap_.find(value.version);
        if (regIt != registerMap_.end()) {
            return Operand::regOp(regIt->second);
        }
    }

    // 默认返回rax
    return Operand::regOp(Register::RAX);
}

void CodeGenerator::computeStackFrame(const IRFunction& function) {
    frame_ = StackFrame();
    int offset = 0;

    // 为每个变量分配栈空间
    for (const auto& param : function.parameters) {
        offset += 8;
        frame_.varOffsets[param.name] = offset;
    }

    // 为临时变量分配栈空间
    for (const auto& block : function.basicBlocks) {
        for (const auto& instr : block.instructions) {
            if (instr.result.isTemporary &&
                frame_.varOffsets.find(instr.result.name) == frame_.varOffsets.end()) {
                offset += 8;
                frame_.varOffsets[instr.result.name] = offset;
            }
        }
    }

    frame_.localVarsSize = offset;
    frame_.savedRegsSize = 5 * 8; // rbx, r12-r15
    frame_.totalSize = frame_.localVarsSize + frame_.savedRegsSize;

    // 对齐到16字节
    if (frame_.totalSize % 16 != 0) {
        frame_.totalSize += 16 - (frame_.totalSize % 16);
    }
}

} // namespace compiler
