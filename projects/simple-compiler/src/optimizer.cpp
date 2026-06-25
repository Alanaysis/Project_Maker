#include "optimizer.hpp"
#include <algorithm>
#include <cmath>

namespace compiler {

// ==================== ConstantFoldingPass ====================

bool ConstantFoldingPass::run(IRModule& module) {
    bool modified = false;

    for (auto& [name, func] : module.functions) {
        for (auto& block : func.basicBlocks) {
            for (auto& instr : block.instructions) {
                if (processInstruction(instr)) {
                    modified = true;
                }
            }
        }
    }

    return modified;
}

bool ConstantFoldingPass::isConstant(const IRValue& value) const {
    return value.isConstant;
}

IRValue ConstantFoldingPass::foldConstants(IROpcode opcode,
                                            const IRValue& left,
                                            const IRValue& right) {
    IRValue result;
    result.isConstant = true;

    // 整数运算
    if (left.type == IRValueType::INT && right.type == IRValueType::INT) {
        int64_t l = left.constant.intValue;
        int64_t r = right.constant.intValue;
        result.type = IRValueType::INT;

        switch (opcode) {
            case IROpcode::ADD: result.constant.intValue = l + r; break;
            case IROpcode::SUB: result.constant.intValue = l - r; break;
            case IROpcode::MUL: result.constant.intValue = l * r; break;
            case IROpcode::DIV:
                if (r != 0) result.constant.intValue = l / r;
                else result.isConstant = false;
                break;
            case IROpcode::MOD:
                if (r != 0) result.constant.intValue = l % r;
                else result.isConstant = false;
                break;
            case IROpcode::CMP_EQ: result.type = IRValueType::BOOL; result.constant.boolValue = (l == r); break;
            case IROpcode::CMP_NE: result.type = IRValueType::BOOL; result.constant.boolValue = (l != r); break;
            case IROpcode::CMP_LT: result.type = IRValueType::BOOL; result.constant.boolValue = (l < r); break;
            case IROpcode::CMP_LE: result.type = IRValueType::BOOL; result.constant.boolValue = (l <= r); break;
            case IROpcode::CMP_GT: result.type = IRValueType::BOOL; result.constant.boolValue = (l > r); break;
            case IROpcode::CMP_GE: result.type = IRValueType::BOOL; result.constant.boolValue = (l >= r); break;
            case IROpcode::BIT_AND: result.constant.intValue = l & r; break;
            case IROpcode::BIT_OR: result.constant.intValue = l | r; break;
            case IROpcode::BIT_XOR: result.constant.intValue = l ^ r; break;
            case IROpcode::SHL: result.constant.intValue = l << r; break;
            case IROpcode::SHR: result.constant.intValue = l >> r; break;
            default: result.isConstant = false; break;
        }
    }
    // 浮点数运算
    else if (left.type == IRValueType::FLOAT && right.type == IRValueType::FLOAT) {
        double l = left.constant.floatValue;
        double r = right.constant.floatValue;
        result.type = IRValueType::FLOAT;

        switch (opcode) {
            case IROpcode::ADD: result.constant.floatValue = l + r; break;
            case IROpcode::SUB: result.constant.floatValue = l - r; break;
            case IROpcode::MUL: result.constant.floatValue = l * r; break;
            case IROpcode::DIV:
                if (r != 0.0) result.constant.floatValue = l / r;
                else result.isConstant = false;
                break;
            case IROpcode::CMP_EQ: result.type = IRValueType::BOOL; result.constant.boolValue = (l == r); break;
            case IROpcode::CMP_NE: result.type = IRValueType::BOOL; result.constant.boolValue = (l != r); break;
            case IROpcode::CMP_LT: result.type = IRValueType::BOOL; result.constant.boolValue = (l < r); break;
            case IROpcode::CMP_LE: result.type = IRValueType::BOOL; result.constant.boolValue = (l <= r); break;
            case IROpcode::CMP_GT: result.type = IRValueType::BOOL; result.constant.boolValue = (l > r); break;
            case IROpcode::CMP_GE: result.type = IRValueType::BOOL; result.constant.boolValue = (l >= r); break;
            default: result.isConstant = false; break;
        }
    }
    // 布尔运算
    else if (left.type == IRValueType::BOOL && right.type == IRValueType::BOOL) {
        bool l = left.constant.boolValue;
        bool r = right.constant.boolValue;
        result.type = IRValueType::BOOL;

        switch (opcode) {
            case IROpcode::AND: result.constant.boolValue = l && r; break;
            case IROpcode::OR: result.constant.boolValue = l || r; break;
            case IROpcode::CMP_EQ: result.constant.boolValue = (l == r); break;
            case IROpcode::CMP_NE: result.constant.boolValue = (l != r); break;
            default: result.isConstant = false; break;
        }
    }
    else {
        result.isConstant = false;
    }

    return result;
}

bool ConstantFoldingPass::processInstruction(IRInstruction& instruction) {
    // 一元运算
    if (instruction.opcode == IROpcode::NEG && instruction.operands.size() == 1) {
        const auto& operand = instruction.operands[0];
        if (operand.isConstant && operand.type == IRValueType::INT) {
            IRValue result;
            result.isConstant = true;
            result.type = IRValueType::INT;
            result.constant.intValue = -operand.constant.intValue;
            instruction.result = result;
            instruction.isConstFolded = true;
            return true;
        }
        if (operand.isConstant && operand.type == IRValueType::FLOAT) {
            IRValue result;
            result.isConstant = true;
            result.type = IRValueType::FLOAT;
            result.constant.floatValue = -operand.constant.floatValue;
            instruction.result = result;
            instruction.isConstFolded = true;
            return true;
        }
    }

    if (instruction.opcode == IROpcode::NOT && instruction.operands.size() == 1) {
        const auto& operand = instruction.operands[0];
        if (operand.isConstant && operand.type == IRValueType::BOOL) {
            IRValue result;
            result.isConstant = true;
            result.type = IRValueType::BOOL;
            result.constant.boolValue = !operand.constant.boolValue;
            instruction.result = result;
            instruction.isConstFolded = true;
            return true;
        }
    }

    // 二元运算
    if (instruction.operands.size() == 2) {
        const auto& left = instruction.operands[0];
        const auto& right = instruction.operands[1];

        if (left.isConstant && right.isConstant) {
            IRValue folded = foldConstants(instruction.opcode, left, right);
            if (folded.isConstant) {
                instruction.result = folded;
                instruction.isConstFolded = true;
                return true;
            }
        }

        // 特殊情况：x * 0 = 0, x * 1 = x, x + 0 = x
        if (instruction.opcode == IROpcode::MUL) {
            if (right.isConstant && right.type == IRValueType::INT) {
                if (right.constant.intValue == 0) {
                    instruction.result = right;
                    instruction.isConstFolded = true;
                    return true;
                }
                if (right.constant.intValue == 1) {
                    instruction.result = left;
                    instruction.isConstFolded = true;
                    return true;
                }
            }
            if (left.isConstant && left.type == IRValueType::INT) {
                if (left.constant.intValue == 0) {
                    instruction.result = left;
                    instruction.isConstFolded = true;
                    return true;
                }
                if (left.constant.intValue == 1) {
                    instruction.result = right;
                    instruction.isConstFolded = true;
                    return true;
                }
            }
        }

        if (instruction.opcode == IROpcode::ADD) {
            if (right.isConstant && right.type == IRValueType::INT &&
                right.constant.intValue == 0) {
                instruction.result = left;
                instruction.isConstFolded = true;
                return true;
            }
            if (left.isConstant && left.type == IRValueType::INT &&
                left.constant.intValue == 0) {
                instruction.result = right;
                instruction.isConstFolded = true;
                return true;
            }
        }

        if (instruction.opcode == IROpcode::SUB) {
            if (right.isConstant && right.type == IRValueType::INT &&
                right.constant.intValue == 0) {
                instruction.result = left;
                instruction.isConstFolded = true;
                return true;
            }
        }
    }

    return false;
}

// ==================== DeadCodeEliminationPass ====================

bool DeadCodeEliminationPass::run(IRModule& module) {
    bool modified = false;

    for (auto& [name, func] : module.functions) {
        // 标记活跃变量
        std::unordered_set<std::string> liveVars;

        // 从后往前遍历基本块
        for (auto it = func.basicBlocks.rbegin(); it != func.basicBlocks.rend(); ++it) {
            markLiveVariables(*it, liveVars);
        }

        // 删除死代码
        for (auto& block : func.basicBlocks) {
            auto newEnd = std::remove_if(block.instructions.begin(),
                                          block.instructions.end(),
                [&liveVars, this](const IRInstruction& instr) {
                    // 如果结果未被使用且没有副作用，标记为死代码
                    if (!instr.result.name.empty() &&
                        liveVars.find(instr.result.name) == liveVars.end() &&
                        !hasSideEffects(instr)) {
                        return true;
                    }
                    return false;
                });

            if (newEnd != block.instructions.end()) {
                block.instructions.erase(newEnd, block.instructions.end());
                modified = true;
            }
        }
    }

    return modified;
}

void DeadCodeEliminationPass::markLiveVariables(BasicBlock& block,
                                                  std::unordered_set<std::string>& liveVars) {
    // 从后往前遍历指令
    for (auto it = block.instructions.rbegin(); it != block.instructions.rend(); ++it) {
        const auto& instr = *it;

        // 如果结果在活跃集合中，移除它并添加操作数
        if (!instr.result.name.empty()) {
            if (liveVars.find(instr.result.name) != liveVars.end()) {
                liveVars.erase(instr.result.name);
            } else if (!hasSideEffects(instr)) {
                // 死代码
                continue;
            }
        }

        // 添加操作数到活跃集合
        for (const auto& operand : instr.operands) {
            if (!operand.isConstant) {
                liveVars.insert(operand.name);
            }
        }
    }
}

bool DeadCodeEliminationPass::hasSideEffects(const IRInstruction& instruction) const {
    // 这些指令有副作用，不能删除
    switch (instruction.opcode) {
        case IROpcode::STORE_VAR:
        case IROpcode::STORE_MEM:
        case IROpcode::CALL:
        case IROpcode::RETURN:
        case IROpcode::JUMP:
        case IROpcode::BRANCH:
        case IROpcode::PRINT:
        case IROpcode::ARRAY_STORE:
            return true;
        default:
            return false;
    }
}

// ==================== CommonSubexpressionEliminationPass ====================

bool CommonSubexpressionEliminationPass::run(IRModule& module) {
    bool modified = false;

    for (auto& [name, func] : module.functions) {
        for (auto& block : func.basicBlocks) {
            if (processBlock(block)) {
                modified = true;
            }
        }
    }

    return modified;
}

bool CommonSubexpressionEliminationPass::processBlock(BasicBlock& block) {
    bool modified = false;
    std::unordered_map<ExprSignature, std::string, ExprHash> availableExprs;

    for (auto& instr : block.instructions) {
        // 只处理二元运算
        if (instr.operands.size() == 2 && !instr.result.name.empty()) {
            ExprSignature sig;
            sig.opcode = instr.opcode;
            sig.operand1 = instr.operands[0].name;
            sig.operand2 = instr.operands[1].name;

            auto it = availableExprs.find(sig);
            if (it != availableExprs.end()) {
                // 找到公共子表达式，替换为之前的值
                IRValue replacement(it->second, instr.result.type);
                instr.result = replacement;
                instr.opcode = IROpcode::MOVE;
                instr.operands.clear();
                modified = true;
            } else {
                // 记录新表达式
                availableExprs[sig] = instr.result.name;
            }
        }

        // 如果操作数被重新定义，清除相关表达式
        if (!instr.result.name.empty()) {
            for (auto it = availableExprs.begin(); it != availableExprs.end();) {
                if (it->second == instr.result.name ||
                    this->sigContainsOperand(it->first, instr.result.name)) {
                    it = availableExprs.erase(it);
                } else {
                    ++it;
                }
            }
        }
    }

    return modified;
}

// ==================== LoopOptimizationPass ====================

bool LoopOptimizationPass::run(IRModule& module) {
    bool modified = false;

    for (auto& [name, func] : module.functions) {
        auto loops = identifyLoops(func);
        for (const auto& loop : loops) {
            if (hoistLoopInvariants(func, loop)) {
                modified = true;
            }
        }
    }

    return modified;
}

std::vector<LoopOptimizationPass::LoopInfo>
LoopOptimizationPass::identifyLoops(const IRFunction& function) {
    std::vector<LoopInfo> loops;

    // 简单实现：识别向后跳转形成的循环
    for (size_t i = 0; i < function.basicBlocks.size(); ++i) {
        const auto& block = function.basicBlocks[i];

        for (const auto& instr : block.instructions) {
            if (instr.opcode == IROpcode::JUMP && !instr.operands.empty()) {
                // 查找目标块
                for (size_t j = 0; j < i; ++j) {
                    if (function.basicBlocks[j].label == instr.operands[0].name) {
                        // 找到循环
                        LoopInfo loop;
                        loop.headerBlock = j;
                        loop.exitBlock = i + 1;

                        for (size_t k = j; k <= i; ++k) {
                            loop.bodyBlocks.push_back(k);
                        }

                        loops.push_back(loop);
                        break;
                    }
                }
            }
        }
    }

    return loops;
}

bool LoopOptimizationPass::hoistLoopInvariants(IRFunction& function,
                                                 const LoopInfo& loop) {
    bool modified = false;

    // 收集循环中定义的变量
    std::unordered_set<std::string> loopDefs;
    for (int blockId : loop.bodyBlocks) {
        for (const auto& instr : function.basicBlocks[blockId].instructions) {
            if (!instr.result.name.empty()) {
                loopDefs.insert(instr.result.name);
            }
        }
    }

    // 查找循环不变量
    std::vector<IRInstruction> invariantInstrs;
    for (int blockId : loop.bodyBlocks) {
        auto& block = function.basicBlocks[blockId];
        for (auto it = block.instructions.begin(); it != block.instructions.end();) {
            bool isInvariant = true;

            // 检查操作数是否在循环中定义
            for (const auto& operand : it->operands) {
                if (!operand.isConstant && loopDefs.find(operand.name) != loopDefs.end()) {
                    isInvariant = false;
                    break;
                }
            }

            // 检查是否有副作用
            if (this->hasSideEffects(*it)) {
                isInvariant = false;
            }

            if (isInvariant && !it->operands.empty()) {
                invariantInstrs.push_back(*it);
                it = block.instructions.erase(it);
                modified = true;
            } else {
                ++it;
            }
        }
    }

    // 将不变量外提到循环头之前
    if (!invariantInstrs.empty() && loop.headerBlock > 0) {
        auto& preheader = function.basicBlocks[loop.headerBlock - 1];
        for (const auto& instr : invariantInstrs) {
            preheader.instructions.push_back(instr);
        }
    }

    return modified;
}

bool LoopOptimizationPass::hasSideEffects(const IRInstruction& instruction) const {
    switch (instruction.opcode) {
        case IROpcode::STORE_VAR:
        case IROpcode::STORE_MEM:
        case IROpcode::CALL:
        case IROpcode::RETURN:
        case IROpcode::PRINT:
        case IROpcode::ARRAY_STORE:
            return true;
        default:
            return false;
    }
}

// ==================== InliningPass ====================

bool InliningPass::run(IRModule& module) {
    bool modified = false;

    for (auto& [name, func] : module.functions) {
        for (auto& block : func.basicBlocks) {
            for (auto& instr : block.instructions) {
                if (instr.opcode == IROpcode::CALL && !instr.operands.empty()) {
                    std::string calleeName = instr.operands[0].name;
                    auto it = module.functions.find(calleeName);
                    if (it != module.functions.end() && canInline(it->second)) {
                        if (inlineCall(func, instr, it->second)) {
                            modified = true;
                        }
                    }
                }
            }
        }
    }

    return modified;
}

bool InliningPass::canInline(const IRFunction& function) const {
    // 计算指令数
    int instrCount = 0;
    for (const auto& block : function.basicBlocks) {
        instrCount += block.instructions.size();
    }

    return instrCount <= threshold_;
}

bool InliningPass::inlineCall(IRFunction& caller, IRInstruction& callInstr,
                               const IRFunction& callee) {
    // 简化实现：将callee的指令复制到caller中
    // 实际实现需要更复杂的变量重命名和控制流处理

    // 这里只做标记，实际内联需要更复杂的实现
    return false;
}

// ==================== StrengthReductionPass ====================

bool StrengthReductionPass::run(IRModule& module) {
    bool modified = false;

    for (auto& [name, func] : module.functions) {
        for (auto& block : func.basicBlocks) {
            for (auto& instr : block.instructions) {
                if (processInstruction(instr)) {
                    modified = true;
                }
            }
        }
    }

    return modified;
}

bool StrengthReductionPass::isPowerOfTwo(int64_t value) const {
    return value > 0 && (value & (value - 1)) == 0;
}

int StrengthReductionPass::getPowerOfTwoExponent(int64_t value) const {
    int exp = 0;
    while (value > 1) {
        value >>= 1;
        exp++;
    }
    return exp;
}

bool StrengthReductionPass::processInstruction(IRInstruction& instruction) {
    if (instruction.operands.size() != 2) return false;

    const auto& left = instruction.operands[0];
    const auto& right = instruction.operands[1];

    // 乘法优化：x * 2^n => x << n
    if (instruction.opcode == IROpcode::MUL) {
        if (right.isConstant && right.type == IRValueType::INT &&
            isPowerOfTwo(right.constant.intValue)) {
            int exp = getPowerOfTwoExponent(right.constant.intValue);
            instruction.opcode = IROpcode::SHL;
            instruction.operands[1] = IRValue("$" + std::to_string(exp), IRValueType::INT);
            instruction.operands[1].isConstant = true;
            instruction.operands[1].constant.intValue = exp;
            return true;
        }
        if (left.isConstant && left.type == IRValueType::INT &&
            isPowerOfTwo(left.constant.intValue)) {
            int exp = getPowerOfTwoExponent(left.constant.intValue);
            instruction.opcode = IROpcode::SHL;
            instruction.operands[0] = instruction.operands[1];
            instruction.operands[1] = IRValue("$" + std::to_string(exp), IRValueType::INT);
            instruction.operands[1].isConstant = true;
            instruction.operands[1].constant.intValue = exp;
            return true;
        }
    }

    // 除法优化：x / 2^n => x >> n
    if (instruction.opcode == IROpcode::DIV) {
        if (right.isConstant && right.type == IRValueType::INT &&
            isPowerOfTwo(right.constant.intValue)) {
            int exp = getPowerOfTwoExponent(right.constant.intValue);
            instruction.opcode = IROpcode::SHR;
            instruction.operands[1] = IRValue("$" + std::to_string(exp), IRValueType::INT);
            instruction.operands[1].isConstant = true;
            instruction.operands[1].constant.intValue = exp;
            return true;
        }
    }

    // 模运算优化：x % 2^n => x & (2^n - 1)
    if (instruction.opcode == IROpcode::MOD) {
        if (right.isConstant && right.type == IRValueType::INT &&
            isPowerOfTwo(right.constant.intValue)) {
            int64_t mask = right.constant.intValue - 1;
            instruction.opcode = IROpcode::BIT_AND;
            instruction.operands[1] = IRValue("$" + std::to_string(mask), IRValueType::INT);
            instruction.operands[1].isConstant = true;
            instruction.operands[1].constant.intValue = mask;
            return true;
        }
    }

    return false;
}

// ==================== Optimizer ====================

Optimizer::Optimizer() {
    stats_.totalPasses = 0;
    stats_.totalModifications = 0;
}

void Optimizer::addPass(std::unique_ptr<OptimizationPass> pass) {
    passes_.push_back(std::move(pass));
}

void Optimizer::optimize(IRModule& module, int maxIterations) {
    bool changed = true;
    int iteration = 0;

    while (changed && iteration < maxIterations) {
        changed = false;
        iteration++;

        for (auto& pass : passes_) {
            bool passChanged = pass->run(module);
            if (passChanged) {
                changed = true;
                stats_.totalModifications++;
            }

            stats_.passStats.emplace_back(pass->getName(), passChanged ? 1 : 0);
        }

        stats_.totalPasses++;
    }
}

} // namespace compiler
