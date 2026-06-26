# Simple CPU Design / 简易 CPU 设计

> **A learning project implementing a simplified CPU with fetch-decode-execute cycle**
> 实现简易 CPU 取指-译码-执行周期的学习项目

---

## 📖 Project Description / 项目描述

This project implements a simplified CPU simulator in C++ to help understand core computer architecture concepts. It demonstrates the fundamental operations of a real CPU through software simulation.

本项目使用 C++ 实现了一个简化的 CPU 模拟器，帮助理解核心计算机体系结构概念。通过软件模拟展示了真实 CPU 的基本操作。

### Learning Objectives / 学习目标

1. **CPU Architecture / CPU 架构** - Understand the Von Neumann architecture and data paths
2. **Instruction Cycle / 指令周期** - Master the fetch-decode-execute cycle
3. **Data Path / 数据通路** - Learn how data flows through CPU components
4. **Register File / 寄存器文件** - Manage general-purpose registers
5. **Memory Interface / 内存接口** - Handle memory read/write operations
6. **ALU Design / ALU 设计** - Implement arithmetic and logic operations

---

## 🏗️ CPU Architecture / CPU 架构

```
                    +------------------+
                    |  Program Counter |
                    |  (PC)            |
                    +------------------+
                           |
                           v
+-----------+    +------------------+    +------------------+
| Clock --> |    |  Instruction     |    |  Instruction     |
| Signal    |    |  Register (IR)   |--> |  Decoder         |
+-----------+    +------------------+    +------------------+
                                    |            |
                                    v            v
                            +------------------+    +------------------+
                            |  Register File   |<--> |  ALU             |
                            |  (16 registers)  |     |  (Arithmetic     |
                            +------------------+     |   Logic Unit)    |
                                    |                +------------------+
                                    v                         |
                            +------------------+              v
                            |  Memory Interface |    +------------------+
                            |  (RAM)            |    |  Status Flags    |
                            +------------------+    |  (Zero, Negative)  |
                                                    +------------------+
```

### Instruction Pipeline / 指令流水线

```
1. FETCH (取指):  PC -> Memory -> IR
2. DECODE (译码): IR -> Decoder -> Control Signals
3. EXECUTE (执行): ALU performs computation
4. MEMORY (访存): Load/Store access RAM
5. WRITEBACK (写回): Result -> Register File
```

---

## 📋 Supported Instructions / 支持的指令

### Data Movement / 数据传送
| Instruction / 指令 | Format / 格式 | Description / 描述 |
|---|---|---|
| LOAD | `LOAD rd, offset(rs1)` | `rd = mem[rs1 + offset]` |
| STORE | `STORE rd, offset(rs1)` | `mem[rs1 + offset] = rd` |
| LUI | `LUI rd, imm` | `rd = imm << 12` |
| ADDI | `ADDI rd, rs1, imm` | `rd = rs1 + imm` |

### Arithmetic / 算术运算
| Instruction / 指令 | Format / 格式 | Description / 描述 |
|---|---|---|
| ADD | `ADD rd, rs1, rs2` | `rd = rs1 + rs2` |
| SUB | `SUB rd, rs1, rs2` | `rd = rs1 - rs2` |
| MUL | `MUL rd, rs1, rs2` | `rd = rs1 * rs2` |
| DIV | `DIV rd, rs1, rs2` | `rd = rs1 / rs2` |

### Logic Operations / 逻辑运算
| Instruction / 指令 | Format / 格式 | Description / 描述 |
|---|---|---|
| AND | `AND rd, rs1, rs2` | `rd = rs1 & rs2` |
| OR | `OR rd, rs1, rs2` | `rd = rs1 | rs2` |
| XOR | `XOR rd, rs1, rs2` | `rd = rs1 ^ rs2` |
| NOT | `NOT rd, rs1` | `rd = ~rs1` |
| SLL | `SLL rd, rs1, rs2` | `rd = rs1 << rs2` |
| SRL | `SRL rd, rs1, rs2` | `rd = rs1 >> rs2` |
| SLT | `SLT rd, rs1, rs2` | `rd = (rs1 < rs2) ? 1 : 0` |

### Control Flow / 流程控制
| Instruction / 指令 | Format / 格式 | Description / 描述 |
|---|---|---|
| JUMP | `JUMP rs1` | `PC = rs1` |
| JAL | `JAL rd, rs1` | `rd = PC+4, PC = rs1` |
| BEQ | `BEQ rs1, rs2, offset` | `if (rs1 == rs2) PC += offset` |
| BNE | `BNE rs1, rs2, offset` | `if (rs1 != rs2) PC += offset` |

### Special / 特殊指令
| Instruction / 指令 | Description / 描述 |
|---|---|
| NOP | No operation |
| HALT | Stop execution |

---

## 🚀 How to Build and Run / 如何构建和运行

### Prerequisites / 前置条件
- C++17 compatible compiler (g++ 7+)
- Make

### Build / 构建
```bash
cd projects/simple-cpu
make
```

### Run Examples / 运行示例

```bash
# Run with all output enabled (推荐)
make run

# Run specific examples
make run-addition    # 加法程序
make run-sorting     # 排序程序
make run-fibonacci   # 斐波那契数列
make run-logic       # 逻辑运算
make run-factorial   # 阶乘计算
make run-trace       # 执行追踪演示

# Run with command line options
./simple-cpu examples/asm/addition.asm --trace --regs --memory --stats
```

### Available Options / 可用选项
| Option / 选项 | Description / 描述 |
|---|---|
| `--trace` | 显示执行追踪 (Show execution trace) |
| `--regs` | 显示寄存器状态 (Show register state) |
| `--memory` | 显示内存转储 (Show memory dump) |
| `--stats` | 显示 CPU 统计信息 (Show CPU statistics) |

### Run Tests / 运行测试
```bash
make test
```

---

## 📁 Project Structure / 项目结构

```
simple-cpu/
├── src/
│   ├── main.cpp          # Main entry point + CPU core
│   ├── cpu.cpp           # CPU core implementation
│   ├── memory.cpp        # Memory interface
│   ├── alu.cpp           # ALU implementation
│   └── asm_parser.cpp    # Assembly parser
├── include/
│   └── cpu_types.h       # Type definitions
├── examples/
│   ├── asm/
│   │   ├── addition.asm      # Addition program
│   │   ├── sorting.asm       # Bubble sort program
│   │   ├── fibonacci.asm     # Fibonacci sequence
│   │   ├── logic_ops.asm     # Logic operations demo
│   │   ├── factorial.asm     # Factorial computation
│   │   └── trace_demo.asm    # Step-by-step trace
│   └── output/
├── tests/
│   └── test_cpu.cpp    # Unit tests
├── Makefile
└── README.md
```

---

## 📚 CPU Architecture Background / CPU 架构背景

### Von Neumann Architecture / 冯·诺依曼架构

The Von Neumann architecture is the foundation of most modern computers. Key components:

- **Program Counter (PC)**: Points to the next instruction to execute
- **Instruction Register (IR)**: Holds the current instruction being executed
- **Arithmetic Logic Unit (ALU)**: Performs arithmetic and logic operations
- **Register File**: Small, fast storage for operands and results
- **Memory**: Stores both program instructions and data

### Instruction Cycle / 指令周期

Every CPU instruction goes through these phases:

1. **Fetch**: Read instruction from memory at PC address
2. **Decode**: Determine what operation to perform
3. **Execute**: Perform the operation (arithmetic, logic, data movement)
4. **Memory**: Access memory if needed (load/store)
5. **Writeback**: Store result back to register file

### Data Path / 数据通路

The data path is the network of wires and components that allow data to flow between CPU elements:

```
Registers <-> ALU <-> Memory
    ^            |
    |            v
    +------ Control Unit
```

---

## 🎓 Learning Path / 学习路径

1. **Start / 开始**: Run `make run-addition` and observe the trace
2. **Understand / 理解**: Read through `examples/asm/trace_demo.asm`
3. **Experiment / 实验**: Modify assembly programs and observe results
4. **Extend / 扩展**: Add new instructions or features

---

## 📝 Assembly Syntax / 汇编语法

```asm
; Comment (注释)
LUI rd, imm       ; Load upper immediate
ADD rd, rs1, rs2  ; rd = rs1 + rs2
LOAD rd, offset(rs1) ; rd = mem[rs1 + offset]
STORE rd, offset(rs1) ; mem[rs1 + offset] = rd
BEQ rs1, rs2, L   ; if (rs1 == rs2) goto L
BNE rs1, rs2, L   ; if (rs1 != rs2) goto L
JUMP target       ; goto target
HALT              ; Stop execution
```

---

## 🔧 Extensions / 扩展方向

- [ ] Add pipeline simulation
- [ ] Implement cache simulation
- [ ] Add interrupt handling
- [ ] Support more instructions (RISC-V subset)
- [ ] Add visual debugger
- [ ] Implement DMA controller
- [ ] Add timer/counter peripherals

---

## 📄 License

This is a learning project for educational purposes.

---

## 🌟 Key Concepts Summary / 核心概念总结

| Concept / 概念 | Description / 描述 |
|---|---|
| Program Counter | Tracks current instruction address |
| Instruction Register | Holds current instruction |
| Register File | 16 general-purpose registers |
| ALU | Performs computation |
| Memory Interface | Handles RAM access |
| Fetch-Decode-Execute | Core CPU operation cycle |
| Branch/Jump | Changes instruction flow |
| Load/Store | Data movement between registers and memory |
