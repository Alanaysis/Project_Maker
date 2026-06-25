# 基本电路模拟

实现基本电路元件（电阻、电容、电感、电压源、电流源）的模拟和分析，包括直流分析、交流分析和实际应用电路。

## 项目概述

本项目是一个电路模拟学习项目，旨在通过Python实现基本电路分析算法，理解电路原理和分析方法。

### 学习目标

- 理解基本电路元件（R、C、L、V、I）的特性
- 掌握欧姆定律和基尔霍夫定律
- 学会节点分析法和网孔分析法
- 理解交流电路的阻抗和频率响应
- 实现分压器、滤波器、放大器等实际应用

### 技术栈

- **主语言**: Python
- **库**: NumPy, Matplotlib, SciPy
- **测试**: pytest

### 核心概念

```
电路元件 → 电路构建 → DC分析/AC分析 → 实际应用
   ↓           ↓           ↓              ↓
 R/C/L/V/I   节点/支路   节点法/网孔法   滤波器/放大器
```

## 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd basic-circuit

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install numpy matplotlib scipy
```

### 运行示例

```bash
# 基础直流电路
python examples/basic_dc_circuit.py

# 交流电路分析
python examples/ac_analysis_demo.py

# 滤波器设计
python examples/filter_design.py
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=src

# 运行特定测试
pytest tests/test_components.py
```

## 项目结构

```
basic-circuit/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── components.py        # 电路元件
│   ├── circuit.py           # 电路网络
│   ├── dc_analysis.py       # 直流分析
│   ├── ac_analysis.py       # 交流分析
│   └── applications.py      # 实际应用
├── tests/
│   ├── __init__.py
│   ├── test_components.py   # 元件测试
│   ├── test_circuit.py      # 电路测试
│   ├── test_dc_analysis.py  # DC分析测试
│   ├── test_ac_analysis.py  # AC分析测试
│   └── test_applications.py # 应用测试
├── examples/
│   ├── basic_dc_circuit.py  # DC电路示例
│   ├── ac_analysis_demo.py  # AC分析示例
│   └── filter_design.py     # 滤波器设计示例
├── docs/
│   ├── 01_RESEARCH.md       # 调研文档
│   ├── 02_REQUIREMENTS.md   # 需求文档
│   ├── 03_DESIGN.md         # 设计文档
│   ├── 04_PRODUCT.md        # 产品文档
│   └── 05_DEVELOPMENT.md    # 开发文档
├── requirements.txt
├── setup.py
└── README.md
```

## 核心模块

### 1. 电路元件 (components.py)

基本电路元件实现：

```python
from src.components import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource

# 电阻
r = Resistor("R1", node1=0, node2=1, resistance=1000)
z = r.impedance(frequency=1000)  # 1000+0j

# 电容
c = Capacitor("C1", node1=0, node2=1, capacitance=1e-6)
z = c.impedance(frequency=1000)  # -159.15j

# 电感
l = Inductor("L1", node1=0, node2=1, inductance=1e-3)
z = l.impedance(frequency=1000)  # 6.28j

# 电压源
v = VoltageSource("V1", node1=0, node2=1, voltage=10, frequency=1000)

# 电流源
i = CurrentSource("I1", node1=0, node2=1, current=0.01)
```

### 2. 电路网络 (circuit.py)

电路构建和管理：

```python
from src.circuit import Circuit

# 创建电路
circuit = Circuit("RC Low Pass")
n0 = circuit.add_node("GND")
n1 = circuit.add_node("IN")
n2 = circuit.add_node("OUT")
circuit.set_ground(n0)

# 添加元件
circuit.add_voltage_source("V1", n0, n1, 10)
circuit.add_resistor("R1", n1, n2, 1000)
circuit.add_capacitor("C1", n2, n0, 1e-6)

# 查看电路信息
print(circuit.summary())
```

### 3. 直流分析 (dc_analysis.py)

节点分析法求解直流电路：

```python
from src.dc_analysis import DCAnalyzer, voltage_divider, series_resistance

# 创建电路
circuit = Circuit("Voltage Divider")
n0 = circuit.add_node("GND")
n1 = circuit.add_node("VCC")
n2 = circuit.add_node("OUT")
circuit.set_ground(n0)

circuit.add_voltage_source("V1", n0, n1, 12)
circuit.add_resistor("R1", n1, n2, 1000)
circuit.add_resistor("R2", n2, n0, 2000)

# 求解
analyzer = DCAnalyzer(circuit)
result = analyzer.solve()

# 查看结果
print(result.node_voltages)  # {0: 0, 1: 12, 2: 8.0}
print(result.branch_currents)  # {'V1': 0.004, 'R1': 0.004, 'R2': 0.004}
```

### 4. 交流分析 (ac_analysis.py)

阻抗计算和频率响应分析：

```python
from src.ac_analysis import ACAnalyzer, resonance_frequency

# 创建RC电路
circuit = Circuit("RC Circuit")
n0 = circuit.add_node("GND")
n1 = circuit.add_node("IN")
circuit.set_ground(n0)

circuit.add_voltage_source("V1", n0, n1, 10, frequency=1000)
circuit.add_resistor("R1", n1, n0, 1000)
circuit.add_capacitor("C1", n1, n0, 1e-6)

# 交流分析
analyzer = ACAnalyzer(circuit)
result = analyzer.solve(frequency=1000)

# 频率响应
fr = analyzer.frequency_response(10, 1e6, 1000)
```

### 5. 实际应用 (applications.py)

分压器、滤波器、放大器：

```python
from src.applications import VoltageDivider, RCFilter, Amplifier

# 分压器
divider = VoltageDivider(v_in=12, r1=1000, r2=2000)
print(divider.output_voltage())  # 8.0V

# RC滤波器
lpf = RCFilter(r=1000, c=1e-6, filter_type='low')
print(lpf.cutoff_frequency())  # 159.15 Hz

# 放大器
amp = Amplifier(r_in=10000, r_f=100000, config='inverting')
print(amp.gain())  # -10.0
```

## 核心公式

### 欧姆定律

```
V = IR
P = VI = I²R = V²/R
```

### 基尔霍夫定律

- **KCL**: 流入节点的电流之和 = 0
- **KVL**: 闭合回路中电压降之和 = 0

### 阻抗

- 电阻: Z_R = R
- 电容: Z_C = 1/(jωC) = -j/(2πfC)
- 电感: Z_L = jωL

### 分压器

```
V_out = V_in × R2 / (R1 + R2)
```

### 截止频率

```
f_c = 1 / (2πRC)
```

### 谐振频率

```
f_r = 1 / (2π√(LC))
```

## 学习资源

- [电路分析基础](https://en.wikipedia.org/wiki/Network_analysis_(electrical))
- [节点分析法](https://en.wikipedia.org/wiki/Nodal_analysis)
- [网孔分析法](https://en.wikipedia.org/wiki/Mesh_analysis)
- [交流电路](https://en.wikipedia.org/wiki/AC_power)

## 许可证

MIT License
