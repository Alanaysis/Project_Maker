# Verilog Simulator  Verilog 模拟器

> 实现 Verilog 仿真引擎，学习数字电路设计和硬件描述语言

## English

A learning project that implements a Verilog simulator engine. This project
helps you understand:

- **Verilog syntax**: Module declarations, wires, regs, always blocks, initial blocks
- **Event-driven simulation**: How HDL simulators work under the hood
- **Timing analysis**: Understanding delays, propagation, and clock synchronization
- **Gate-level modeling**: Building circuits from primitive gates
- **Behavioral modeling**: Writing high-level Verilog code
- **Testbench design**: Verifying digital circuits through simulation

## 中文

一个实现 Verilog 仿真引擎的学习项目。通过本项目可以学习：

- **Verilog 语法**：模块声明、线网、寄存器、always 块、initial 块
- **事件驱动仿真**：理解 HDL 仿真器的工作原理
- **时序分析**：理解延迟、传播和时钟同步
- **门级建模**：从基本逻辑门构建电路
- **行为级建模**：编写高级 Verilog 代码
- **测试台设计**：通过仿真验证数字电路

---

## Learning Objectives 学习目标

### Primary 主要目标

1. **理解 Verilog 语法** / Understand Verilog Syntax
   - 掌握模块、端口、线网、寄存器的声明
   - 掌握 always 块和 initial 块的使用方法
   - 掌握连续赋值和过程赋值的区别

2. **掌握事件驱动仿真** / Master Event-Driven Simulation
   - 理解事件队列和调度机制
   - 理解 delta 周期的概念
   - 理解阻塞赋值和非阻塞赋值的区别

3. **学会时序分析** / Learn Timing Analysis
   - 理解传播延迟和时钟延迟
   - 理解建立时间和保持时间
   - 理解时序收敛的概念

### Secondary 次要目标

4. **掌握测试台设计** / Master Testbench Design
   - 编写系统化的测试用例
   - 理解验证覆盖率的概念
   - 学习断言和自动检查

5. **理解数字电路设计流程** / Understand Digital Design Flow
   - 从门级到行为级的设计层次
   - 组合逻辑和时序逻辑的区别
   - 有限状态机的设计方法

---

## Quick Start 快速开始

### Build 构建

```bash
# Compile all examples and tests
make all

# Or compile specific targets
make gate_demo        # Gate-level example
make combinational    # Combinational circuit example
make sequential       # Sequential circuit example
make testbench        # Testbench example
make tests            # Run unit tests
```

### Run Examples 运行示例

```bash
# Run gate-level simulation example
./build/example_01_gate_level

# Run combinational circuit example
./build/example_02_combinational

# Run sequential circuit example
./build/example_03_sequential

# Run testbench example
./build/example_04_testbench

# Run unit tests
./build/tests/test_verilog_simulator
```

### Verilog Files Verilog 文件

The `examples/` directory contains Verilog source files that can be
simulated with this tool:

`examples/` 目录包含可以用此工具仿真的 Verilog 源文件：

- `gate_demo.v` - 基本门级仿真 / Basic gate-level simulation
- `combinational_demo.v` - 组合逻辑电路仿真 / Combinational circuit simulation
- `sequential_demo.v` - 时序逻辑电路仿真 / Sequential circuit simulation
- `testbench_demo.v` - 测试台演示 / Testbench demo

---

## Project Structure 项目结构

```
verilog-simulator/
├── src/
│   ├── verilog_simulator.h    # Core simulator header (核心仿真器头文件)
│   └── main.cc                # CLI entry point (命令行入口)
├── examples/
│   ├── gate_demo.v            # Gate-level Verilog (门级 Verilog)
│   ├── combinational_demo.v   # Combinational circuits (组合电路)
│   ├── sequential_demo.v      # Sequential circuits (时序电路)
│   ├── testbench_demo.v       # Testbench patterns (测试台模式)
│   ├── example_01_gate_level.cc
│   ├── example_02_combinational.cc
│   ├── example_03_sequential.cc
│   └── example_04_testbench.cc
├── tests/
│   └── test_verilog_simulator.cc
├── Makefile
└── README.md
```

---

## Verilog Simulation Theory  Verilog 仿真理论

### Event-Driven Simulation 事件驱动仿真

Verilog simulators use an event-driven approach:

```
Verilog 代码 → 解析 → 事件队列 → 按时间排序 → 执行 → 波形输出
```

1. **Elaboration (展开)**: Parse Verilog source, build module hierarchy
2. **Initialization (初始化)**: Set initial values, run initial blocks
3. **Evaluation (求值)**: Process events in time order
4. **Finalization (完成)**: Close VCD, print statistics

### Delta Cycles Delta 周期

Within a single time step, events are processed in scheduling order:

```
t=0:  Event A (delta 0, seq 0)
t=0:  Event B (delta 0, seq 1)
t=0:  Event C (delta 1, seq 0)    <- next delta cycle
t=10: Event D (delta 0, seq 0)    <- next time step
```

### Time Model 时间模型

- **Time unit**: Picoseconds (ps)
- **Delay types**: Inertial delay, Transport delay
- **Precision**: Deterministic scheduling order

### Gate Primitives 门级原语

| Gate | Symbol | Truth Table | Description |
|------|--------|-------------|-------------|
| AND | `&` | 00=0, 01=0, 10=0, 11=1 | All inputs must be 1 |
| OR | `\|` | 00=0, 01=1, 10=1, 11=1 | Any input is 1 |
| NOT | `~` | 0=1, 1=0 | Inverts input |
| XOR | `^` | 00=0, 01=1, 10=1, 11=0 | Inputs differ |
| NAND | `&`+NOT | 00=1, 01=1, 10=1, 11=0 | NOT AND |
| NOR | `\|`+NOT | 00=1, 01=0, 10=0, 11=0 | NOT OR |
| XNOR | `^`+NOT | 00=1, 01=0, 10=0, 11=1 | Inputs equal |

### Flip-Flop Operation 触发器工作原理

```
        ┌──────────┐
D ──────►| D       |───── Q
        |  Flip-Flop|
CLK ─────►|En       |
        └──────────┘

On positive edge of CLK:
  Q <= D  (capture D value)
```

### DFF with Reset 带复位触发器

```
        ┌──────────┐
D ──────►| D       |───── Q
        |  D FF    |
CLK ─────►|En       |
RST ─────►|Reset    |
        └──────────┘

If RST is active:
  Q <= 1'b1  (async reset)
Else on CLK edge:
  Q <= D
```

---

## Examples 示例

### Example 1: Gate-Level Simulation 门级仿真

Demonstrates basic logic gates and their truth tables:

```
a | b | AND | OR | NOT(a) | XOR | NAND | NOR | XNOR
--+---+-----+----+--------+-----+------+-----+------
0 | 0 |  0  | 0  |   1    |  0  |   1  |  1  |   1
0 | 1 |  0  | 1  |   1    |  1  |   1  |  0  |   0
1 | 0 |  0  | 1  |   0    |  1  |   1  |  0  |   0
1 | 1 |  1  | 1  |   0    |  0  |   0  |  0  |   1
```

### Example 2: Combinational Circuits 组合电路

- **4-bit Ripple Carry Adder**: Four full adders chained together
- **4-to-16 Decoder**: One-hot encoding of 4-bit input
- **8-to-1 MUX**: Selects one of 8 inputs based on selector

### Example 3: Sequential Circuits 时序电路

- **D Flip-Flop**: Basic storage element
- **4-bit Counter**: Increments on each clock cycle
- **FSM**: Traffic light controller with 4 states

### Example 4: Testbench 测试台

- Systematic test case selection
- Boundary value testing
- Overflow detection
- Pass/fail reporting

---

## Testbench Patterns 测试台模式

### Pattern 1: Manual Timing 手动时序

```verilog
initial begin
    clk = 0;
    forever #5 clk = ~clk;  // Toggle every 5ns
end
```

### Pattern 2: Stimulus Generation 刺激生成

```verilog
initial begin
    rst = 1;
    #10 rst = 0;
    #20 input_a = 8'hFF;
    #30 input_b = 8'h00;
    #100 $finish;
end
```

### Pattern 3: Response Checking 响应检查

```verilog
task check_result;
    input integer test_num;
    input [31:0] expected;
    input [31:0] actual;
    begin
        if (expected == actual)
            $display("Test %0d: PASS", test_num);
        else
            $display("Test %0d: FAIL (expected=%h, got=%h)", 
                     test_num, expected, actual);
    end
endtask
```

---

## VCD Waveform Format VCD 波形格式

The simulator outputs VCD (Value Change Dump) files, which can be
viewed with waveform viewers like GTKWave:

```
$var wire 1 $1 clk $end
$var wire 8 $2 q $end
$enddefinitions $end
$dumpvars
0
00000000
$end
#100
1
$end
```

View with GTKWave:
```bash
gtkwave output.wcd
```

---

## Learning Path 学习路径

1. **Week 1**: Study Verilog syntax and gate primitives
   - 学习 Verilog 语法和门级原语
   - Run gate_demo example

2. **Week 2**: Understand event-driven simulation
   - 理解事件驱动仿真机制
   - Study the simulator source code

3. **Week 3**: Design combinational circuits
   - 设计组合逻辑电路
   - Run combinational_demo example

4. **Week 4**: Design sequential circuits
   - 设计时序逻辑电路
   - Run sequential_demo example

5. **Week 5**: Write testbenches
   - 编写测试台
   - Run testbench_demo example

---

## References 参考资料

- **IEEE 1800-2017**: SystemVerilog Standard
- **IEEE 1364-2005**: Verilog-2005 Standard
- **Digital Design and Computer Architecture**: Harris & Harris
- **Verilog Digital System Programming**: Kochie
- **CMOS Digital Integrated Circuits**: Kang & Leblebici

---

## License 许可证

This is a learning project. Feel free to use and modify for educational purposes.

这是一个学习项目，可以自由使用和修改用于教育目的。
