# Chip Placement & Routing / 芯片布局布线

> **基础 EDA 布局布线算法学习项目** - Implementing basic EDA placement and routing algorithms

---

## English

### Overview

A learning project implementing fundamental Electronic Design Automation (EDA) algorithms for chip placement and routing. This project covers the core flow of digital IC/FPGA design: **Netlist → Placement → Routing → Timing Verification → Output**.

### Learning Objectives

- **Understand placement and routing**: Learn how circuits go from logical netlists to physical layouts
- **Master routing algorithms**: Implement maze routing (BFS) and A* pathfinding
- **Learn timing optimization**: Static timing analysis, critical path analysis, slack computation

### EDA Theory Background

#### Placement (布局)
Placement assigns physical coordinates to each cell (logic element) in a circuit. Good placement minimizes wire length and congestion while meeting timing constraints.

**Two main approaches:**
1. **Analytical Placement**: Formulates placement as a quadratic optimization problem. Solves linear equations iteratively to minimize HPWL (Half Perimeter Wire Length). Fast but may get stuck in local minima.
2. **Simulated Annealing**: A stochastic optimization inspired by metallurgy annealing. Accepts worse solutions with decreasing probability as "temperature" drops, allowing escape from local minima.

**Key metric: HPWL (Half Perimeter Wire Length)**
```
HPWL(net) = (max_x - min_x) + (max_y - min_y)
Total HPWL = sum of HPWL over all nets
```

#### Routing (布线)
Routing finds physical wire paths to connect all pins of each net.

**Two stages:**
1. **Global Routing**: Coarse channel assignment across the chip. Determines how many routing tracks each net needs in each region.
2. **Detailed Routing**: Exact track assignment for each wire segment. Uses maze routing (BFS) and A* search to find shortest paths avoiding obstacles.

**Key concepts:**
- **Track**: A single wire position within a routing channel
- **Via**: Connection between different metal layers
- **Congestion**: When more nets need tracks than are available (congestion > 1.0 = problem)

#### Timing Analysis (时序分析)
Static Timing Analysis (STA) checks that all signals arrive at their destinations within the required time window.

**Key concepts:**
- **Setup time**: Minimum time before clock edge that data must be stable
- **Hold time**: Minimum time after clock edge that data must remain stable
- **Slack**: `slack = required_time - arrival_time`
  - Positive slack = timing met
  - Negative slack = timing violation
- **Critical path**: The longest delay path (determines maximum clock frequency)

**Elmore Delay Model:**
```
Wire delay = R_driver × C_wire + (R_wire × C_wire) / 2
Cell delay = intrinsic_delay + (load_capacitance / drive_strength)
```

### How to Run Examples

```bash
# 1. Build all demos
make

# 2. Run all demos
make run-all

# 3. Run unit tests
make test

# 4. Clean build artifacts
make clean

# Individual demos:
./build/placement_demo      # Placement algorithms demo
./build/routing_demo        # Routing algorithms demo
./build/timing_demo         # Timing analysis demo
./build/wire_length_demo    # Wire length optimization demo
```

### Project Structure

```
chip-placement/
├── include/           # Header files
│   ├── netlist.h      # Netlist data structures
│   ├── placement.h    # Placement algorithm interfaces
│   ├── routing.h      # Routing algorithm interfaces
│   ├── timing.h       # Timing analysis interfaces
│   └── analysis.h     # Wire length & congestion analysis
├── src/               # Implementation files
│   ├── netlist.cpp    # Netlist parser
│   ├── placement.cpp  # Analytical + SA placement
│   ├── routing.cpp    # Global + detailed routing
│   ├── timing.cpp     # STA implementation
│   └── analysis.cpp   # Wire length & congestion
├── examples/          # Demo programs
│   ├── placement_demo.cpp
│   ├── routing_demo.cpp
│   ├── timing_demo.cpp
│   └── wire_length_demo.cpp
├── tests/             # Unit tests
│   └── test_chip_placement.cpp
├── netlists/          # Sample netlist files
│   ├── simple.net
│   └── larger_circuit.net
├── Makefile
└── README.md
```

### Netlist Format

```
NETLIST <design_name>

CELL <instance_name> <cell_type> <area> <intrinsic_delay> [pins...]
NET <net_name> { <cell>:<pin> ... }
CONSTRAINT <name> <period_ps> <input_delay> <output_delay>

END
```

Supported cell types: `IO_PAD`, `FF`, `LUT`, `BUFFER`, `DSP`, `BRAM`, `CLB`, `HARD_MACRO`

---

## 中文

### 项目概述

本项目实现基础的电子设计自动化（EDA）芯片布局布线算法，涵盖数字集成电路/FPGA设计的核心流程：**网表输入 → 布局 → 布线 → 时序验证 → 输出**。

### 学习目标

- **理解布局布线**：学习电路如何从逻辑网表转化为物理布局
- **掌握布线算法**：实现迷宫布线（BFS）和A*寻路算法
- **学会时序优化**：静态时序分析、关键路径分析、建立时间裕量计算

### EDA理论基础

#### 布局（Placement）
布局为电路中的每个单元（逻辑元件）分配物理坐标。好的布局最小化线长和拥塞，同时满足时序约束。

**两种主要方法：**
1. **解析布局**：将布局建模为二次优化问题。通过迭代求解线性方程组来最小化HPWL（半周长线长）。速度快但可能陷入局部最优。
2. **模拟退火布局**：受冶金退火启发的随机优化算法。随着"温度"降低，以递减的概率接受更差的解，从而逃离局部最优。

**关键指标：HPWL（半周长线长）**
```
HPWL(网) = (max_x - min_x) + (max_y - min_y)
总HPWL = 所有网HPWL之和
```

#### 布线（Routing）
布线为每个网的所有引脚找到物理连线路径。

**两个阶段：**
1. **全局布线**：在芯片上粗粒度分配布线通道。确定每个网在每个区域需要多少布线轨道。
2. **详细布线**：为每个线段分配精确的轨道。使用迷宫布线（BFS）和A*搜索寻找避开障碍物的最短路径。

**关键概念：**
- **轨道（Track）**：布线通道内的单个导线位置
- **过孔（Via）**：不同金属层之间的连接
- **拥塞**：当需要的轨道数超过可用数时（拥塞 > 1.0 = 问题）

#### 时序分析（Timing Analysis）
静态时序分析（STA）检查所有信号是否在要求的时间内到达目的地。

**关键概念：**
- **建立时间**：数据必须在时钟沿之前稳定的最小时间
- **保持时间**：数据必须在时钟沿之后保持稳定的最小时间
- **建立时间裕量（Slack）**：`slack = required_time - arrival_time`
  - 正裕量 = 时序满足
  - 负裕量 = 时序违规
- **关键路径**：最长延迟路径（决定最高时钟频率）

**Elmore延迟模型：**
```
导线延迟 = R_driver × C_wire + (R_wire × C_wire) / 2
单元延迟 = intrinsic_delay + (负载电容 / 驱动能力)
```

### 如何运行示例

```bash
# 1. 编译所有示例
make

# 2. 运行所有示例
make run-all

# 3. 运行单元测试
make test

# 4. 清理构建产物
make clean

# 单独运行示例：
./build/placement_demo      # 布局算法演示
./build/routing_demo        # 布线算法演示
./build/timing_demo         # 时序分析演示
./build/wire_length_demo    # 线长优化演示
```

### 项目结构

```
chip-placement/
├── include/           # 头文件
│   ├── netlist.h      # 网表数据结构
│   ├── placement.h    # 布局算法接口
│   ├── routing.h      # 布线算法接口
│   ├── timing.h       # 时序分析接口
│   └── analysis.h     # 线长和拥塞分析
├── src/               # 实现文件
│   ├── netlist.cpp    # 网表解析器
│   ├── placement.cpp  # 解析布局 + 模拟退火
│   ├── routing.cpp    # 全局 + 详细布线
│   ├── timing.cpp     # STA实现
│   └── analysis.cpp   # 线长和拥塞分析
├── examples/          # 示例程序
│   ├── placement_demo.cpp
│   ├── routing_demo.cpp
│   ├── timing_demo.cpp
│   └── wire_length_demo.cpp
├── tests/             # 单元测试
│   └── test_chip_placement.cpp
├── netlists/          # 示例网表文件
│   ├── simple.net
│   └── larger_circuit.net
├── Makefile
└── README.md
```

### 网表格式

```
NETLIST <设计名称>

CELL <实例名> <单元类型> <面积> <本征延迟> [引脚...]
NET <网名> { <单元>:<引脚> ... }
CONSTRAINT <约束名> <周期_ps> <输入延迟> <输出延迟>

END
```

支持的单元类型：`IO_PAD`, `FF`, `LUT`, `BUFFER`, `DSP`, `BRAM`, `CLB`, `HARD_MACRO`

---

## Tech Stack

| Item | Value |
|------|-------|
| Language | C++17 |
| Framework | None |
| Libraries | Standard library only |
| Build | Make |

## Learning Path

1. **Start**: Read the netlist format and data structures (`include/netlist.h`)
2. **Placement**: Run `placement_demo` and study `src/placement.cpp`
3. **Routing**: Run `routing_demo` and study `src/routing.cpp`
4. **Timing**: Run `timing_demo` and study `src/timing.cpp`
5. **Analysis**: Run `wire_length_demo` and study `src/analysis.cpp`
6. **Test**: Run `make test` to verify all components

## References

- *Physical Design Automation of VLSI Systems* by Chiang-Kuan Cheng
- *Logic Synthesis and Verification Algorithms* by Hachtel & Somenzi
- *Static Timing Analysis for Nanometer Designs* by J. Bhasker
- *Introduction to VLSI Systems* by C. Mead & L. Conway
