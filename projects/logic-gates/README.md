# 逻辑门模拟器 (Logic Gates Simulator)

一个完整的数字电路仿真框架，用于学习和理解数字逻辑电路的工作原理。

## 功能特性

### 1. 基本逻辑门
- **AND** (与门): 所有输入为1时输出1
- **OR** (或门): 任一输入为1时输出1
- **NOT** (非门): 输入取反
- **NAND** (与非门): AND门取反
- **NOR** (或非门): OR门取反
- **XOR** (异或门): 输入不同时输出1
- **XNOR** (同或门): 输入相同时输出1
- **Buffer** (缓冲器): 信号直通

### 2. 组合电路
- **多路选择器 (MUX)**: 根据选择信号从多个输入中选择一个
- **多路分配器 (DEMUX)**: 将输入分配到多个输出中的一个
- **解码器 (Decoder)**: 将二进制输入解码为独热码输出
- **编码器 (Encoder)**: 将独热码输入编码为二进制输出
- **半加器 (Half Adder)**: 计算两个一位二进制数的和
- **全加器 (Full Adder)**: 带进位输入的加法器
- **纹波进位加法器 (Ripple Carry Adder)**: 多位加法器
- **比较器 (Comparator)**: 比较两个二进制数的大小
- **ALU (算术逻辑单元)**: 支持多种算术和逻辑运算

### 3. 时序电路
- **SR锁存器**: 基本存储单元
- **D锁存器**: 数据锁存器
- **D触发器**: 边沿触发的D触发器
- **JK触发器**: 全功能触发器
- **T触发器**: 翻转触发器
- **计数器**: 二进制计数器、十进制计数器、环形计数器
- **寄存器**: 数据寄存器
- **移位寄存器**: 支持左移、右移和并行加载

### 4. 仿真引擎
- **连线 (Wire)**: 支持延迟和信号追踪
- **总线 (Bus)**: 多位连线
- **电路仿真器**: 事件驱动仿真
- **时钟生成器**: 生成周期性时钟信号
- **激励生成器**: 生成测试激励信号
- **信号追踪器**: 记录和显示信号波形

### 5. 实际应用
- **简单CPU**: 4位CPU设计，支持基本指令集
- **存储单元**: RAM、ROM、缓存行

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/logic-gates-simulator.git

# 进入项目目录
cd logic-gates-simulator

# 安装依赖（无外部依赖）
pip install -r requirements.txt
```

## 快速开始

### 基本逻辑门

```python
from src.gates import AndGate, OrGate, NotGate

# 创建AND门
and_gate = AndGate()
print(and_gate.evaluate(1, 1))  # 输出: 1
print(and_gate.evaluate(1, 0))  # 输出: 0

# 生成真值表
print(and_gate.truth_table())
```

### 组合电路

```python
from src.combinational import Multiplexer, HalfAdder

# 4选1多路选择器
mux = Multiplexer(2)
data = [1, 0, 1, 0]
select = [1, 0]  # 选择第2个输入
print(mux.evaluate(data, select))  # 输出: 1

# 半加器
ha = HalfAdder()
sum_val, carry = ha.evaluate(1, 1)
print(f"Sum: {sum_val}, Carry: {carry}")  # Sum: 0, Carry: 1
```

### 时序电路

```python
from src.sequential import DFlipFlop, Counter

# D触发器
ff = DFlipFlop()
ff.set_data(1)
ff.clock(0)  # 低电平
ff.clock(1)  # 上升沿，触发
print(ff.get_state())  # {'Q': 1, 'Q_bar': 0}

# 4位计数器
counter = Counter(4)
for _ in range(5):
    counter.increment()
print(counter.get_count())  # 5
```

### 仿真引擎

```python
from src.simulation import Simulator, ClockGenerator

# 创建仿真器
sim = Simulator()
sim.add_wire("CLK")
sim.add_wire("DATA")

# 创建时钟
clock_gen = ClockGenerator(sim, "CLK", period=4)
clock_gen.start(20)

# 运行仿真
sim.run(20)

# 获取波形
waveform = sim.get_waveform("CLK")
print(waveform)
```

### CPU设计

```python
from src.applications import SimpleCPU

# 创建CPU
cpu = SimpleCPU()

# 编写程序
program = [
    0b00010001,  # LOAD R0, 1
    0b00010101,  # LOAD R1, 1
    0b00100001,  # ADD R0, R1
    0b11110000,  # HALT
]

# 加载并运行
cpu.load_program(program)
cpu.run()

print(cpu.get_register(0))  # 2
```

## 项目结构

```
logic-gates/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── signal.py            # 信号定义
│   ├── gates.py             # 基本逻辑门
│   ├── circuit.py           # 电路类
│   ├── truth_table.py       # 真值表生成器
│   ├── registry.py          # 门注册表
│   ├── utils.py             # 工具函数
│   ├── cli.py               # 命令行接口
│   ├── exceptions.py        # 异常定义
│   ├── combinational/       # 组合电路
│   │   ├── __init__.py
│   │   ├── multiplexer.py
│   │   ├── decoder.py
│   │   ├── adder.py
│   │   ├── comparator.py
│   │   └── alu.py
│   ├── sequential/          # 时序电路
│   │   ├── __init__.py
│   │   ├── latch.py
│   │   ├── flipflop.py
│   │   ├── counter.py
│   │   └── register.py
│   ├── simulation/          # 仿真引擎
│   │   ├── __init__.py
│   │   ├── wire.py
│   │   ├── sim_circuit.py
│   │   ├── simulator.py
│   │   └── trace.py
│   └── applications/        # 实际应用
│       ├── __init__.py
│       ├── cpu.py
│       └── memory.py
├── tests/                   # 测试文件
├── examples/                # 示例代码
├── docs/                    # 文档
└── README.md
```

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_gates.py

# 运行带详细输出的测试
python -m pytest tests/ -v
```

## 使用示例

### 命令行接口

```bash
# 查看帮助
python -m src.cli --help

# 运行AND门示例
python -m src.cli --example and

# 生成真值表
python -m src.cli --truth-table AND

# 模拟电路
python -m src.cli --circuit half_adder --inputs A=1,B=0
```

### 示例文件

- `examples/basic_gates.py`: 基本逻辑门示例
- `examples/circuit_demo.py`: 电路组合示例
- `examples/truth_table_demo.py`: 真值表生成示例

## 学习资源

### 数字电路基础
1. 逻辑门的工作原理
2. 组合逻辑电路设计
3. 时序逻辑电路设计
4. 状态机设计

### 高级主题
1. CPU设计原理
2. 存储系统设计
3. 总线系统设计
4. 时序分析

## 贡献

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- 感谢所有贡献者
- 灵感来自数字电路教材和实际硬件设计
