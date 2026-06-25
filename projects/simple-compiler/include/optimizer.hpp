#pragma once

#include "ir.hpp"
#include <memory>
#include <vector>
#include <unordered_set>

namespace compiler {

/**
 * 优化Pass基类
 */
class OptimizationPass {
public:
    virtual ~OptimizationPass() = default;

    /**
     * 执行优化
     * @param module IR模块
     * @return 是否有修改
     */
    virtual bool run(IRModule& module) = 0;

    /**
     * 获取pass名称
     */
    virtual std::string getName() const = 0;
};

/**
 * 常量折叠优化
 * 在编译时计算常量表达式
 *
 * 示例：
 *   x = 2 + 3  =>  x = 5
 *   y = x * 0  =>  y = 0
 */
class ConstantFoldingPass : public OptimizationPass {
public:
    bool run(IRModule& module) override;
    std::string getName() const override { return "ConstantFolding"; }

private:
    /**
     * 检查值是否是常量
     */
    bool isConstant(const IRValue& value) const;

    /**
     * 执行常量运算
     */
    IRValue foldConstants(IROpcode opcode, const IRValue& left, const IRValue& right);

    /**
     * 处理单条指令
     */
    bool processInstruction(IRInstruction& instruction);
};

/**
 * 死代码消除优化
 * 移除不会被执行或结果未被使用的代码
 *
 * 示例：
 *   x = 10    (x未被使用)
 *   y = 20
 *   return y
 *   =>
 *   y = 20
 *   return y
 */
class DeadCodeEliminationPass : public OptimizationPass {
public:
    bool run(IRModule& module) override;
    std::string getName() const override { return "DeadCodeElimination"; }

private:
    /**
     * 标记活跃变量
     */
    void markLiveVariables(BasicBlock& block, std::unordered_set<std::string>& liveVars);

    /**
     * 检查指令是否有副作用
     */
    bool hasSideEffects(const IRInstruction& instruction) const;
};

/**
 * 公共子表达式消除优化
 * 识别并消除重复计算的表达式
 *
 * 示例：
 *   a = b + c
 *   d = b + c
 *   =>
 *   a = b + c
 *   d = a
 */
class CommonSubexpressionEliminationPass : public OptimizationPass {
public:
    bool run(IRModule& module) override;
    std::string getName() const override { return "CommonSubexpressionElimination"; }

private:
    /**
     * 表达式签名
     */
    struct ExprSignature {
        IROpcode opcode;
        std::string operand1;
        std::string operand2;

        bool operator==(const ExprSignature& other) const {
            return opcode == other.opcode &&
                   operand1 == other.operand1 &&
                   operand2 == other.operand2;
        }
    };

    /**
     * 表达式签名哈希
     */
    struct ExprHash {
        size_t operator()(const ExprSignature& expr) const {
            size_t h1 = std::hash<int>()(static_cast<int>(expr.opcode));
            size_t h2 = std::hash<std::string>()(expr.operand1);
            size_t h3 = std::hash<std::string>()(expr.operand2);
            return h1 ^ (h2 << 1) ^ (h3 << 2);
        }
    };

    /**
     * 处理单个基本块
     */
    bool processBlock(BasicBlock& block);

    /**
     * 检查签名是否包含指定操作数
     */
    bool sigContainsOperand(const ExprSignature& sig, const std::string& name) const {
        return sig.operand1 == name || sig.operand2 == name;
    }
};

/**
 * 循环优化
 * 包括循环不变量外提、循环展开等
 *
 * 示例（循环不变量外提）：
 *   while (i < 10) {
 *     x = a + b  // a和b在循环中不变
 *     i = i + 1
 *   }
 *   =>
 *   t = a + b
 *   while (i < 10) {
 *     x = t
 *     i = i + 1
 *   }
 */
class LoopOptimizationPass : public OptimizationPass {
public:
    bool run(IRModule& module) override;
    std::string getName() const override { return "LoopOptimization"; }

private:
    /**
     * 循环信息
     */
    struct LoopInfo {
        int headerBlock;                // 循环头基本块
        std::vector<int> bodyBlocks;    // 循环体基本块
        int exitBlock;                  // 循环出口基本块
    };

    /**
     * 识别循环
     */
    std::vector<LoopInfo> identifyLoops(const IRFunction& function);

    /**
     * 循环不变量外提
     */
    bool hoistLoopInvariants(IRFunction& function, const LoopInfo& loop);

    /**
     * 检查值是否在循环中不变
     */
    bool isLoopInvariant(const IRValue& value, const LoopInfo& loop,
                         const IRFunction& function) const;

    /**
     * 检查指令是否有副作用
     */
    bool hasSideEffects(const IRInstruction& instruction) const;
};

/**
 * 内联优化
 * 将小函数调用替换为函数体
 *
 * 示例：
 *   fn add(a, b) { return a + b; }
 *   x = add(1, 2)
 *   =>
 *   x = 1 + 2
 */
class InliningPass : public OptimizationPass {
public:
    bool run(IRModule& module) override;
    std::string getName() const override { return "Inlining"; }

    /**
     * 设置内联阈值（函数最大指令数）
     */
    void setThreshold(int threshold) { threshold_ = threshold; }

private:
    int threshold_ = 20;  // 默认阈值

    /**
     * 检查函数是否可以内联
     */
    bool canInline(const IRFunction& function) const;

    /**
     * 内联函数调用
     */
    bool inlineCall(IRFunction& caller, IRInstruction& callInstr,
                    const IRFunction& callee);
};

/**
 * 强度削减优化
 * 将昂贵的操作替换为等价的便宜操作
 *
 * 示例：
 *   x = y * 2  =>  x = y << 1
 *   x = y * 8  =>  x = y << 3
 *   x = y / 2  =>  x = y >> 1
 */
class StrengthReductionPass : public OptimizationPass {
public:
    bool run(IRModule& module) override;
    std::string getName() const override { return "StrengthReduction"; }

private:
    /**
     * 检查值是否是2的幂
     */
    bool isPowerOfTwo(int64_t value) const;

    /**
     * 获取2的幂的指数
     */
    int getPowerOfTwoExponent(int64_t value) const;

    /**
     * 处理单条指令
     */
    bool processInstruction(IRInstruction& instruction);
};

/**
 * 优化器
 * 管理和执行所有优化Pass
 */
class Optimizer {
public:
    Optimizer();

    /**
     * 添加优化Pass
     */
    void addPass(std::unique_ptr<OptimizationPass> pass);

    /**
     * 执行所有优化
     * @param module IR模块
     * @param maxIterations 最大迭代次数
     */
    void optimize(IRModule& module, int maxIterations = 10);

    /**
     * 获取优化统计信息
     */
    struct Stats {
        int totalPasses;
        int totalModifications;
        std::vector<std::pair<std::string, int>> passStats;
    };

    Stats getStats() const { return stats_; }

private:
    std::vector<std::unique_ptr<OptimizationPass>> passes_;
    Stats stats_;
};

} // namespace compiler
