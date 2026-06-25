# 市场调研

## 1. RISC-V 指令集简介

RISC-V 是一个开源的精简指令集架构 (ISA)，由加州大学伯克利分校于 2010 年发起。与 x86 和 ARM 不同，RISC-V 是完全开源的，任何人都可以自由使用和扩展。

### 核心特点
- **精简设计**: 基础指令集只有约 40 条指令
- **模块化**: 基础整数指令集 (RV32I/RV64I) + 可选扩展 (M/A/F/D/C 等)
- **开源免费**: 无授权费用，适合教学和研究
- **统一编码**: 所有指令固定 32 位宽度 (标准) 或 16 位 (压缩扩展)

## 2. 同类型项目分析

### 2.1 QEMU RISC-V
- **特点**: 功能完整的 RISC-V 系统模拟器
- **代码规模**: 约 200 万行 (整个 QEMU)
- **适用场景**: 运行完整操作系统
- **学习难度**: 极高

### 2.2 Spike (riscv-isa-sim)
- **GitHub**: https://github.com/riscv-software-tools/riscv-isa-sim
- **语言**: C++
- **特点**: RISC-V 官方参考模拟器
- **代码规模**: 约 3 万行
- **适用场景**: ISA 验证、软件开发
- **学习难度**: 高

### 2.3 rv32emu
- **GitHub**: https://github.com/sysprog21/rv32emu
- **语言**: C
- **特点**: 轻量级 RV32I 模拟器，代码简洁
- **代码规模**: 约 5000 行
- **适用场景**: 学习 RISC-V 架构
- **学习难度**: 中

### 2.4 RARS (RISC-V Assembler and Runtime Simulator)
- **语言**: Java
- **特点**: 集成汇编器和模拟器，有图形界面
- **适用场景**: 教学
- **学习难度**: 低

### 2.5 Tiny RISC-V
- **特点**: 极简实现，适合入门
- **代码规模**: 约 1000 行
- **适用场景**: 理解指令执行流程
- **学习难度**: 低

## 3. RISC-V 指令格式

### 3.1 基本格式

RISC-V 有 6 种基本指令格式:

```
R-type: [funct7 | rs2 | rs1 | funct3 | rd | opcode]
I-type: [imm[11:0]       | rs1 | funct3 | rd | opcode]
S-type: [imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode]
B-type: [imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode]
U-type: [imm[31:12]                           | rd | opcode]
J-type: [imm[20|10:1|11|19:12]                | rd | opcode]
```

### 3.2 RV32I 指令分类

| 类型 | 指令 | 说明 |
|------|------|------|
| 算术 | ADD, SUB, ADDI | 加减法 |
| 逻辑 | AND, OR, XOR, ANDI, ORI, XORI | 逻辑运算 |
| 移位 | SLL, SRL, SRA, SLLI, SRLI, SRAI | 移位运算 |
| 比较 | SLT, SLTU, SLTI, SLTIU | 小于比较 |
| 分支 | BEQ, BNE, BLT, BGE, BLTU, BGEU | 条件分支 |
| 跳转 | JAL, JALR | 无条件跳转 |
| 加载 | LB, LH, LW, LBU, LHU | 内存加载 |
| 存储 | SB, SH, SW | 内存存储 |
| 高位 | LUI, AUIPC | 高位立即数 |
| 系统 | ECALL, EBREAK | 系统调用/断点 |

## 4. 关键技术点

### 4.1 指令解码
- 从 32 位原始指令中提取各字段
- 立即数的符号扩展 (不同格式的立即数位置不同)
- 操作码和功能码的组合识别

### 4.2 执行引擎
- ALU 运算 (算术、逻辑、移位、比较)
- 内存访问 (加载/存储，支持字节/半字/字)
- 控制流 (分支、跳转、PC 更新)
- 系统调用模拟

### 4.3 内存模型
- 字节寻址
- 小端序 (Little-Endian)
- 对齐访问 (RISC-V 支持非对齐访问，但模拟器可以选择只支持对齐访问)
