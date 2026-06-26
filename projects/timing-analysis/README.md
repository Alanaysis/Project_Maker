# Timing Analysis / 时序分析

> 实现静态时序分析 (Static Timing Analysis, STA) 学习项目

## Description / 项目描述

**English**: A learning project implementing Static Timing Analysis (STA) for digital circuits. STA verifies that all timing constraints in a digital circuit are met without running dynamic simulation.

**中文**: 实现数字电路的静态时序分析学习项目。STA 在不运行动态仿真的情况下验证数字电路中的所有时序约束是否满足。

## Learning Objectives / 学习目标

- **理解时序分析**: Understand how signals propagate through gates and interconnects
  - 理解信号如何在门电路和互连中传播
- **掌握建立/保持时间**: Master setup and hold time concepts and calculations
  - 掌握建立时间和保持时间的概念与计算
- **学会时序优化**: Learn critical path identification and slack optimization techniques
  - 学会关键路径识别和时序优化技术

## Theory / 时序分析理论基础

### What is Static Timing Analysis?

Static Timing Analysis (STA) checks all possible paths in a digital circuit to ensure signals arrive at flip-flops in time. Unlike dynamic simulation, STA does not require test vectors.

**静态时序分析 (STA)** 检查数字电路中的所有可能路径，确保信号按时到达触发器。与动态仿真不同，STA 不需要测试向量。

### Key Concepts / 关键概念

#### Setup Time / 建立时间

The minimum time before the clock edge that data must be stable at the flip-flop input.

```
T_ccq + T_comb + T_setup <= T_clock
Slack_setup = T_clock - (T_ccq + T_comb + T_setup)
```

If Slack_setup < 0, there is a **setup violation**.

#### Hold Time / 保持时间

The minimum time after the clock edge that data must remain stable at the flip-flop input.

```
T_ccq_min + T_comb_min >= T_hold
Slack_hold = (T_ccq_min + T_comb_min) - T_hold
```

If Slack_hold < 0, there is a **hold violation**.

#### Critical Path / 关键路径

The path with the worst (minimum) slack. This path determines the maximum operating frequency of the circuit.

**最坏情况路径**，具有最差（最小）的 slack。该路径决定电路的最高工作频率。

### Timing Graph / 时序图

STA represents the circuit as a **Directed Acyclic Graph (DAG)**:
- **Nodes**: Registers (flip-flops), primary inputs, primary outputs, and interconnects
- **Edges**: Gates/interconnects with timing delays
- **Clock edges**: Define the timing context for each register

STA uses **topological sort** on the DAG to compute:
- **Early arrival time (ear)**: Earliest time a signal can arrive
- **Late arrival time (lar)**: Latest time a signal can arrive
- **Required time (req)**: Latest time a signal must arrive

### Slack Calculation / Slack 计算

```
Slack = Required Time - Arrival Time
```

- **Positive slack**: Timing is met (good)
- **Negative slack**: Timing violation (bad)
- **Zero slack**: Just meets timing (marginal)

## Project Structure / 项目结构

```
timing-analysis/
├── src/                      # Core library
│   ├── timing_analysis.h    # Main header with all type definitions
│   ├── netlist_parser.c     # Circuit netlist parser
│   ├── timing_graph.c       # Timing graph (DAG) construction
│   ├── clock_tree.c         # Clock tree modeling
│   ├── setup_analysis.c     # Setup time analysis
│   ├── hold_analysis.c      # Hold time analysis
│   ├── path_analysis.c      # Critical path analysis
│   ├── slack_calc.c         # Slack calculation
│   └── timing_report.c      # Timing report generation
├── examples/                 # Demo programs
│   ├── demo_basic.c         # Basic timing analysis demo
│   ├── demo_setup_hold.c    # Setup/hold violation detection
│   ├── demo_critical_path.c # Critical path identification
│   └── demo_timing_report.c # Timing report demo
├── tests/                    # Unit tests
│   └── test_timing.c        # Comprehensive test suite
├── README.md                 # This file
└── Makefile                  # Build system
```

## How to Build / 如何构建

```bash
# Build all targets
make

# Build specific target
make demo-basic
make demo-setup-hold
make demo-critical-path
make demo-timing-report

# Run tests
make test

# Run a specific demo
make run-demo-basic
make run-demo-setup-hold
make run-demo-critical-path
make run-demo-timing-report

# Clean
make clean
```

## Examples / 示例

### 1. Basic Timing Analysis / 基础时序分析

Demonstrates parsing a simple circuit netlist and computing basic timing parameters.

```bash
make run-demo-basic
```

### 2. Setup/Hold Violation Detection / 建立/保持违例检测

Shows how to detect setup and hold violations in a circuit.

```bash
make run-demo-setup-hold
```

### 3. Critical Path Identification / 关键路径识别

Finds the critical path (worst-case path) in a circuit.

```bash
make run-demo-critical-path
```

### 4. Timing Report / 时序报告

Generates a comprehensive timing report showing all paths, slacks, and violations.

```bash
make run-demo-timing-report
```

## Static Timing Analysis Theory / 静态时序分析理论

### STA Flow / STA 流程

```
1. Netlist Parsing    →  Parse circuit description into internal representation
2. Graph Construction →  Build timing graph (DAG) from netlist
3. Clock Modeling     →  Define clock trees and timing constraints
4. Graph Analysis     →  Topological sort, compute arrival/required times
5. Slack Calculation  →  Compute slack for all paths
6. Report Generation  →  Output timing summary, violations, critical paths
```

### Timing Closure / 时序收敛

**Timing closure** means all setup and hold constraints are satisfied:
- **Setup**: Data arrives early enough before the next clock edge
- **Hold**: Data remains stable long enough after the current clock edge

Common optimization techniques:
1. **Upsizing**: Increase gate drive strength to reduce delay
2. **Buffer insertion**: Add buffers to break long paths
3. **Sizing**: Optimize transistor sizes for timing
4. **Clock tree synthesis**: Balance clock skew across the chip
5. **Retiming**: Move registers across combinational logic

### Delay Models / 延迟模型

- **Wireload model**: Statistical interconnect delay estimation
- **Elmore delay**: RC tree delay calculation
- **Liberty (.lib)**: Standard cell timing library format

## References / 参考

- "Static Timing Analysis for Nanometer Designs" by J. Bhasker and R. Chadha
- "Digital Integrated Circuits" by J. M. Rabaey
- Synopsys Design Constraints (SDC) Format Reference

## License / 许可证

MIT License
