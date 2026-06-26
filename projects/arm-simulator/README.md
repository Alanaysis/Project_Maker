# arm-simulator

# ARM 指令集模拟器

> 一个教育目的的 ARM 指令集模拟器，用于理解 ARM 架构的核心概念。
> An educational ARM instruction set simulator for understanding core ARM architecture concepts.

---

## 项目描述 / Project Description

本项目实现了一个简化的 ARM 指令集模拟器，支持 ARM 状态和 Thumb 模式下的常见指令执行。
This project implements a simplified ARM instruction set simulator supporting common instructions in both ARM and Thumb modes.

## 学习目标 / Learning Objectives

### 中文
- 理解 ARM 指令集的 CISC/RISC 混合特性
- 掌握 ARM 的 32 个通用寄存器架构
- 学会 CPSR/SPSR 状态寄存器的作用
- 理解 ARM 的条件执行机制
- 掌握 ARM/Thumb 双模式切换
- 理解 Load/Store 架构

### English
- Understand the CISC/RISC hybrid nature of the ARM instruction set
- Master ARM's 32 general-purpose register architecture
- Learn the role of CPSR/SPSR status registers
- Understand ARM's conditional execution mechanism
- Master ARM/Thumb dual-mode switching
- Understand Load/Store architecture

## 支持的指令集 / Supported Instructions

### 数据处理指令 / Data Processing Instructions
| 指令 | 描述 |
|------|------|
| ADD | 加法 |
| SUB | 减法 |
| MOV | 数据移动 |
| MVN | 数据取反移动 |
| AND | 按位与 |
| ORR | 按位或 |
| EOR | 按位异或 |
| BIC | 位清除 |
| LSL | 逻辑左移 |
| LSR | 逻辑右移 |
| ASR | 算术右移 |
| ROR | 循环右移 |
| CMP | 比较 (内部执行 SUB) |
| CMN | 比较负数 (内部执行 ADD) |
| TST | 测试位 (内部执行 AND) |
| TEQ | 测试相等 (内部执行 EOR) |

### 乘法和单数据交换 / Multiplication & Single Data Exchange
| 指令 | 描述 |
|------|------|
| MUL | 乘法 |
| MLA | 乘累加 |
| UMULL | 无符号长乘法 |
| UMLAL | 无符号长乘累加 |

### 加载/存储指令 / Load/Store Instructions
| 指令 | 描述 |
|------|------|
| STR | 存储字 |
| LDR | 加载字 |
| STRB | 存储字节 |
| LDRB | 加载字节 |
| STMIA | 存储多寄存器，递增后 |
| LDMIA | 加载多寄存器，递增后 |
| STMDB | 存储多寄存器，递减后 |
| LDMDB | 加载多寄存器，递减后 |
| LDR/STR (PC相对) | PC相对加载/存储 |

### 分支指令 / Branch Instructions
| 指令 | 描述 |
|------|------|
| B | 无条件分支 |
| BL | 带链接的分支 (保存返回地址) |
| BX | 分支并切换指令集状态 |
| BLX | 带链接并切换指令集状态 |

### Thumb 指令 / Thumb Instructions (subset)
| 指令 | 描述 |
|------|------|
| ADD (Thumb) | Thumb 加法 |
| SUB (Thumb) | Thumb 减法 |
| MOV (Thumb) | Thumb 数据移动 |
| CMP (Thumb) | Thumb 比较 |
| PUSH/POP | 栈操作 |
| TBB/THB | 查表分支 |

## 架构背景 / ARM Architecture Background

### ARM 寄存器文件
ARM 架构有 37 个寄存器：
- **32 个通用寄存器 (R0-R31)**: R0-R12 是通用寄存器，R13 是栈指针 (SP)，R14 是链接寄存器 (LR)，R15 是程序计数器 (PC)
- **CPSR (当前程序状态寄存器)**: 包含条件标志位 (N, Z, C, V) 和控制位
- **SPSR (保存的程序状态寄存器)**: 在异常模式下保存 CPSR

### 条件执行 / Conditional Execution
ARM 的独特特性：大多数 ARM 指令可以附加条件码前缀，在满足条件时才执行：
- EQ (==), NE (!=), GT (>), GE (>=), LT (<), LE (<=), HI (无符号大于), LS (无符号小于)
- 格式: `CMP R1, R2` 后跟 `MOVEQ R3, #0` (如果相等则移动)

### ARM/Thumb 双模式 / ARM/Thumb Dual Mode
- **ARM 状态**: 32 位定长指令，支持条件执行
- **Thumb 状态**: 16 位压缩指令，节省内存，不支持条件执行（但支持 IT 块）
- **切换**: 使用 BX/BLX 指令，通过目标地址 LSB 决定模式

### Load/Store 架构 / Load/Store Architecture
- 只有 LDR/STR 指令可以访问内存
- 所有算术运算在寄存器之间进行
- 偏移寻址模式: 偏移在地址计算之前/之后应用

## 运行示例 / How to Run Examples

```bash
# 运行示例程序
python examples/arithmetic_demo.py
python examples/loop_demo.py
python examples/function_call_demo.py
python examples/trace_demo.py

# 运行测试
python -m pytest tests/ -v
```

## 项目结构 / Project Structure

```
arm-simulator/
├── src/
│   ├── __init__.py
│   ├── cpu.py          # ARM CPU 模拟器核心
│   ├── registers.py    # 寄存器文件 (R0-R15, CPSR, SPSR)
│   ├── decoder.py      # 指令解码器
│   ├── alu.py          # ALU (算术逻辑单元)
│   ├── memory.py       # 内存模拟器
│   ├── thumb.py        # Thumb 模式支持
│   └── exception.py    # 异常处理基础
├── examples/
│   ├── arithmetic_demo.py   # 算术运算演示
│   ├── loop_demo.py         # 循环示例
│   ├── function_call_demo.py # 函数调用示例
│   └── trace_demo.py        # 执行追踪演示
├── tests/
│   ├── __init__.py
│   ├── test_registers.py
│   ├── test_alu.py
│   ├── test_decoder.py
│   └── test_cpu.py
├── README.md
└── requirements.txt
```

## 许可证 / License

MIT License

---

## English Version

### Project Description

This project implements a simplified ARM instruction set simulator supporting common instructions in both ARM and Thumb modes.

### How to Run Examples

```bash
# Run example programs
python examples/arithmetic_demo.py
python examples/loop_demo.py
python examples/function_call_demo.py
python examples/trace_demo.py

# Run tests
python -m pytest tests/ -v
```
