# Sequential Logic Circuit Simulator / 时序逻辑电路模拟器

> **Learning Project / 学习项目** — Understand sequential logic through implementation

---

## 📖 Project Description / 项目描述

**English**: A Python-based learning project that simulates sequential logic circuits, including flip-flops, counters, registers, and finite state machines. Each component is implemented from scratch with detailed comments explaining the underlying digital logic theory.

**中文**: 基于Python的时序逻辑电路学习项目，模拟触发器、计数器、寄存器和有限状态机。每个组件都从零实现，配有详细的注释解释底层数字逻辑理论。

---

## 🎯 Learning Objectives / 学习目标

### English
- Understand the difference between combinational and sequential logic
- Master the operation of SR latches, JK/D/T flip-flops
- Build and analyze counters (asynchronous, synchronous, up/down)
- Implement register types (SIPO, PISO, PIPO, bidirectional shift)
- Design and simulate finite state machines (Moore and Mealy)
- Generate timing diagrams for circuit analysis

### 中文
- 理解组合逻辑与时序逻辑的区别
- 掌握SR锁存器、JK/D/T触发器的工作原理
- 构建和分析计数器（异步、同步、加减）
- 实现寄存器类型（SIPO、PISO、PIPO、双向移位）
- 设计和模拟有限状态机（摩尔型和米利型）
- 生成时序图进行电路分析

---

## 🏗️ Project Structure / 项目结构

```
sequential-logic/
├── src/                          # Source code / 源代码
│   ├── __init__.py
│   ├── flip_flops.py             # SR Latch, JK Flip-Flop
│   ├── d_and_t_ff.py            # D Flip-Flop, T Flip-Flop
│   ├── counter.py               # Ripple/Sync/UpDown counters
│   ├── register.py              # SIPO, PISO, PIPO, shift registers
│   ├── fsm.py                   # Finite State Machines
│   └── timing_diagram.py        # Timing diagram generation
├── examples/                     # Demo scripts / 演示脚本
│   ├── 01_flip_flop_simulation.py
│   ├── 02_counter_simulation.py
│   ├── 04_register_operations.py
│   ├── 05_fsm_demo.py
│   └── output/                  # Generated diagrams
├── tests/                        # Unit tests / 单元测试
│   └── test_sequential_logic.py
├── main.py                       # Entry point / 入口
├── requirements.txt              # Dependencies / 依赖
└── README.md                     # This file
```

---

## 📚 Sequential Logic Theory Background / 时序逻辑理论基础

### What is Sequential Logic? / 什么是时序逻辑？

Sequential logic circuits have **memory** — their output depends not only on current inputs but also on past inputs. This is achieved through **feedback** paths that store state information.

时序逻辑电路具有**记忆**功能——输出不仅取决于当前输入，还取决于过去的输入。通过存储状态信息的**反馈**路径实现。

### Key Concepts / 关键概念

#### 1. Latches and Flip-Flops / 锁存器和触发器

| Type | Name | Description |
|------|------|-------------|
| SR | Set-Reset Latch | Basic memory element with set/reset inputs |
| JK | JK Flip-Flop | Enhanced SR latch with toggle mode |
| D | Data Flip-Flop | Stores one bit of data on clock edge |
| T | Toggle Flip-Flop | Toggles output when T=1 |

#### 2. Counters / 计数器

- **Asynchronous (Ripple) Counter**: Clock cascades through flip-flops. Simple but has propagation delay.
- **Synchronous Counter**: All flip-flops share the same clock. Faster, no ripple delay.
- **Up/Down Counter**: Can count in both directions.

#### 3. Registers / 寄存器

| Type | Data In | Data Out | Use Case |
|------|---------|----------|----------|
| SIPO | Serial | Parallel | Serial-to-parallel conversion |
| PISO | Parallel | Serial | Parallel-to-serial conversion |
| PIPO | Parallel | Parallel | Data storage |
| Shift | Serial | Serial | Data delay/manipulation |

#### 4. Finite State Machines / 有限状态机

- **Moore Machine**: Output depends only on current state
- **Mealy Machine**: Output depends on current state AND inputs

### Core Loop / 核心循环

```
Clock Signal → State Update → Output Calculation
时钟信号 → 状态更新 → 输出计算
```

---

## 🚀 How to Run Examples / 如何运行示例

### 1. Install Dependencies / 安装依赖

```bash
pip install -r requirements.txt
```

### 2. Run Individual Demos / 运行单个演示

```bash
# Flip-flop simulation
python examples/01_flip_flop_simulation.py

# Counter simulation
python examples/02_counter_simulation.py

# Register operations
python examples/04_register_operations.py

# Finite state machine demo
python examples/05_fsm_demo.py
```

### 3. Run via Main Entry / 通过主入口运行

```bash
python main.py flip-flop
python main.py counter
python main.py register
python main.py fsm
python main.py all        # Run all demos
```

### 4. Run Tests / 运行测试

```bash
pytest tests/ -v
```

---

## 📖 Learning Resources / 学习资源

### English
- **Digital Fundamentals** by Thomas L. Floyd — Comprehensive digital logic textbook
- **Digital Design** by Morris Mano — Classic digital design reference
- **Nand2Tetris** (Coursera) — Build a computer from logic gates

### 中文
- **数字逻辑设计** — 数字逻辑基础教材
- **数字设计** — 经典数字设计参考书
- **数字电路与系统** — 数字电路理论与实践

---

## 🧠 Key Takeaways / 关键要点

1. **Sequential = Memory**: Unlike combinational circuits, sequential circuits remember their past.
2. **Clock is King**: The clock signal synchronizes state changes, making circuits predictable.
3. **Flip-Flops are Building Blocks**: All sequential circuits are built from flip-flops.
4. **FSMs Model Behavior**: Finite state machines are the foundation of digital system design.
5. **Timing Matters**: Understanding timing diagrams is essential for circuit analysis.

---

## 📝 Notes / 说明

- This is a **learning project**, not a production tool.
- All implementations are simplified for educational purposes.
- Timing diagram generation requires `matplotlib`.
- For advanced simulation, consider tools like Logisim, ModelSim, or Vivado.

---

## License / 许可

MIT License — Free for educational use.
