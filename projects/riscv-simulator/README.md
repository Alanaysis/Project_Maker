# RISC-V Simulator - RISC-V 指令集模拟器

## 项目简介

RISC-V Simulator 是一个用 C 语言实现的 RISC-V 指令集模拟器，支持 RV32I 基本整数指令集。包含汇编器，可以直接运行 RISC-V 汇编源代码。

## 学习目标

- **RISC-V 指令集理解**: 掌握 RV32I 的 6 种指令格式和 40+ 条指令
- **指令解码和执行**: 学习如何从二进制编码中提取操作码、寄存器、立即数
- **寄存器管理**: 理解 32 个通用寄存器和 x0 硬连线零的设计
- **内存模型**: 掌握字节寻址、小端序、对齐访问

## 技术栈

| 技术 | 说明 | 学习难度 |
|------|------|----------|
| C (C11) | 实现语言 | ⭐⭐ |
| RISC-V ISA | 目标指令集架构 | ⭐⭐⭐ |
| 汇编器 | 两遍汇编、标签解析 | ⭐⭐⭐ |

## 核心架构

```
指令读取 → 指令解码 → 执行 → 寄存器更新 → PC 更新
  (Fetch)   (Decode)  (Execute)  (Writeback)  (PC+4)
```

## 项目结构

```
riscv-simulator/
├── README.md              # 本文件
├── LEARNING_NOTES.md      # 学习笔记
├── Makefile               # 构建脚本
├── verify.sh              # 验证脚本
├── include/               # 头文件
│   ├── riscv.h            # 公共类型和常量
│   ├── memory.h           # 内存模型接口
│   ├── cpu.h              # CPU 模型接口
│   ├── decoder.h          # 指令解码器接口
│   ├── executor.h         # 指令执行器接口
│   └── assembler.h        # 汇编器接口
├── src/                   # 源代码
│   ├── main.c             # 主程序 (CLI)
│   ├── memory.c           # 内存实现
│   ├── decoder.c          # 解码器实现
│   ├── executor.c         # 执行器实现
│   ├── cpu.c              # CPU 实现
│   └── assembler.c        # 汇编器实现
├── tests/                 # 测试代码
│   ├── test_memory.c      # 内存测试 (7 个)
│   ├── test_decoder.c     # 解码器测试 (11 个)
│   ├── test_assembler.c   # 汇编器测试 (10 个)
│   └── test_integration.c # 集成测试 (11 个)
├── examples/              # 示例程序
│   ├── sum_1_to_10.s      # 求和 1+2+...+10
│   ├── fibonacci.s        # 斐波那契数列
│   ├── factorial.s        # 阶乘计算
│   └── bubble_sort.s      # 冒泡排序
└── docs/                  # 文档
    ├── 01-RESEARCH.md     # 市场调研
    ├── 02-REQUIREMENTS.md # 需求分析
    ├── 03-DESIGN.md       # 架构设计
    ├── 04-PRODUCT.md      # 产品说明
    └── 05-DEVELOPMENT.md  # 开发记录
```

## 快速开始

### 编译
```bash
make
```

### 运行示例
```bash
./riscv-sim -a examples/sum_1_to_10.s
```

### 运行内置测试
```bash
./riscv-sim --test
```

### 运行所有测试
```bash
make test
```

### 完整验证
```bash
make verify
```

## 支持的指令

### RV32I 基本整数指令集

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

## 命令行选项

```
用法: riscv-sim [选项] <程序>

选项:
  -h          显示帮助
  -d <level>  调试级别 (0=无, 1=错误, 2=警告, 3=信息, 4=跟踪)
  -s          单步执行模式
  -a          汇编模式 (输入为汇编文本文件)
  -n <cycles> 最大执行周期数
  --test      运行内置测试程序
```

## 重点难点

### 重点
1. **指令格式**: 理解 R/I/S/B/U/J 六种格式的编码方式
2. **立即数解码**: 不同格式的立即数位置和符号扩展
3. **分支指令**: B-type 格式的立即数编码比较特殊
4. **两遍汇编**: 标签解析需要两遍扫描

### 难点
1. **B-type 立即数编码**: 位的排列不连续 (imm[12|10:5|4:1|11])
2. **符号扩展**: 12 位/13 位/20 位立即数的正确扩展
3. **标签相对偏移**: 分支和跳转指令使用相对于当前 PC 的偏移

### 值得思考
1. 为什么 RISC-V 选择固定指令宽度 (32 位)?
2. x0 硬连线为零的设计有什么好处?
3. 为什么需要 6 种不同的指令格式?
4. 小端序 vs 大端序的选择对模拟器有什么影响?
