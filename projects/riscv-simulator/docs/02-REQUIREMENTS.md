# 需求分析

## 1. 功能需求

### 1.1 核心功能 (P0)

#### 指令集支持
- [x] RV32I 基本整数指令集 (全部 40+ 条指令)
- [x] R-type: ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND
- [x] I-type: ADDI, SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI
- [x] Load: LB, LH, LW, LBU, LHU
- [x] Store: SB, SH, SW
- [x] Branch: BEQ, BNE, BLT, BGE, BLTU, BGEU
- [x] Jump: JAL, JALR
- [x] Upper: LUI, AUIPC
- [x] System: ECALL, EBREAK

#### CPU 模型
- [x] 32 个通用寄存器 (x0-x31)
- [x] x0 硬连线为零
- [x] 程序计数器 (PC)
- [x] 指令计数器

#### 内存模型
- [x] 1MB 可配置内存
- [x] 字节寻址
- [x] 小端序
- [x] 对齐访问检查
- [x] 越界检查

### 1.2 汇编器功能 (P0)

- [x] 支持所有 RV32I 指令的汇编
- [x] 支持 ABI 寄存器名称 (zero, ra, sp, a0, t0 等)
- [x] 支持数字寄存器名称 (x0-x31)
- [x] 支持标签 (labels)
- [x] 支持注释 (# 和 ;)
- [x] 两遍汇编 (第一遍收集标签，第二遍生成代码)

### 1.3 调试功能 (P1)

- [x] 单步执行模式
- [x] 指令跟踪 (trace)
- [x] 寄存器状态打印
- [x] 内存内容查看
- [x] EBREAK 断点支持

### 1.4 命令行接口 (P0)

- [x] 运行二进制文件
- [x] 汇编并运行汇编源文件
- [x] 调试级别控制
- [x] 单步模式
- [x] 最大周期数限制
- [x] 内置测试程序

## 2. 非功能需求

### 2.1 性能
- 单条指令执行时间 < 1us
- 支持至少 100 万周期的连续运行

### 2.2 可靠性
- 所有指令的正确性验证
- 内存访问的边界检查
- 错误处理和报告

### 2.3 可维护性
- 模块化设计 (CPU/内存/解码器/执行器/汇编器)
- 清晰的代码注释
- 完整的单元测试

## 3. 约束条件

- 语言: C (C11 标准)
- 平台: Linux
- 编译器: GCC
- 无外部依赖

## 4. 测试需求

### 4.1 单元测试
- 内存模块: 创建、读写、对齐、边界
- 解码器模块: 各类型指令解码、立即数符号扩展
- 汇编器模块: 寄存器解析、立即数解析、各类型指令汇编

### 4.2 集成测试
- 算术运算 (ADD, SUB, AND, OR, XOR, SLL, SRL)
- 控制流 (BEQ, BNE, BLT, BGE, JAL, JALR)
- 内存访问 (LUI, Load/Store)
- 比较运算 (SLT, SLTU)
- x0 硬连线零
