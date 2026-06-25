# 产品文档：基本电路模拟

## 1. 产品概述

### 1.1 产品定位

基本电路模拟是一个用于学习和验证电路设计的Python库，支持：
- 基本电路元件建模
- 直流电路分析
- 交流电路分析
- 实际应用电路设计

### 1.2 目标用户

| 用户类型 | 需求 | 使用场景 |
|----------|------|----------|
| 学生 | 学习电路原理 | 课程作业、实验验证 |
| 工程师 | 快速验证设计 | 原型设计、参数计算 |
| 爱好者 | 探索电路特性 | 个人项目、兴趣学习 |

### 1.3 核心价值

- **易用性**：简洁的API设计
- **准确性**：基于标准电路分析方法
- **可扩展性**：模块化设计，易于扩展
- **教育性**：清晰的代码和文档

## 2. 功能特性

### 2.1 电路元件

#### 电阻

```python
r = Resistor("R1", node1=0, node2=1, resistance=1000)
z = r.impedance(1000)  # 1000+0j Ω
g = r.conductance()    # 0.001 S
```

**特性**：
- 阻抗与频率无关
- 消耗电能
- 单位：欧姆 (Ω)

#### 电容

```python
c = Capacitor("C1", node1=0, node2=1, capacitance=1e-6)
z = c.impedance(1000)  # -159.15j Ω
x_c = c.reactance(1000) # -159.15 Ω
```

**特性**：
- 阻抗与频率成反比
- 储存电场能
- 直流开路，交流短路
- 单位：法拉 (F)

#### 电感

```python
l = Inductor("L1", node1=0, node2=1, inductance=1e-3)
z = l.impedance(1000)  # 6.28j Ω
x_l = l.reactance(1000) # 6.28 Ω
```

**特性**：
- 阻抗与频率成正比
- 储存磁场能
- 直流短路，交流开路
- 单位：亨利 (H)

#### 电压源

```python
v = VoltageSource("V1", node1=0, node2=1, voltage=10, frequency=1000, phase=0)
phasor = v.phasor()      # 10+0j
v_t = v.time_value(0.001) # 瞬时值
```

**特性**：
- 提供恒定电压
- 支持直流和交流
- 可设置频率和相位

#### 电流源

```python
i = CurrentSource("I1", node1=0, node2=1, current=0.01, frequency=1000, phase=0)
phasor = i.phasor()      # 0.01+0j
i_t = i.time_value(0.001) # 瞬时值
```

**特性**：
- 提供恒定电流
- 支持直流和交流
- 可设置频率和相位

### 2.2 电路分析

#### 欧姆定律

```python
from src.components import ohms_law, power

# 已知V和R，求I
result = ohms_law(voltage=12, resistance=1000)
print(result['current'])  # 0.012 A

# 功率计算
p = power(voltage=12, current=0.012)
print(p)  # 0.144 W
```

#### 分压器

```python
from src.applications import VoltageDivider

divider = VoltageDivider(v_in=12, r1=1000, r2=2000)
v_out = divider.output_voltage()  # 8.0 V
ratio = divider.transfer_ratio()  # 0.667
```

#### 串并联

```python
from src.dc_analysis import series_resistance, parallel_resistance

r_series = series_resistance(1000, 2000, 3000)    # 6000 Ω
r_parallel = parallel_resistance(1000, 2000, 3000) # 545.45 Ω
```

### 2.3 直流分析

```python
from src.circuit import Circuit
from src.dc_analysis import DCAnalyzer

# 创建电路
circuit = Circuit("Voltage Divider")
n0 = circuit.add_node("GND")
n1 = circuit.add_node("VCC")
n2 = circuit.add_node("OUT")
circuit.set_ground(n0)

circuit.add_voltage_source("V1", n0, n1, 12)
circuit.add_resistor("R1", n1, n2, 1000)
circuit.add_resistor("R2", n2, n0, 2000)

# 分析
analyzer = DCAnalyzer(circuit)
result = analyzer.solve()

# 结果
print(result.node_voltages)      # {0: 0, 1: 12, 2: 8.0}
print(result.branch_currents)    # {'V1': 0.004, 'R1': 0.004, 'R2': 0.004}
print(result.power_dissipation)  # {'V1': -0.048, 'R1': 0.016, 'R2': 0.032}
```

### 2.4 交流分析

```python
from src.circuit import Circuit
from src.ac_analysis import ACAnalyzer

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
result = analyzer.solve(1000)

print(result.impedances)        # {'R1': 1000+0j, 'C1': 0-159.15j}
print(result.total_impedance)   # 1000-159.15j
```

### 2.5 频率响应

```python
from src.applications import RCFilter

# RC低通滤波器
lpf = RCFilter(r=1000, c=1e-6, filter_type='low')

# 截止频率
f_c = lpf.cutoff_frequency()  # 159.15 Hz

# 传输函数
h = lpf.transfer_function(1000)  # 0.157 - 0.988j

# 增益
gain = lpf.gain_dB(1000)  # -16.0 dB

# 相位
phase = lpf.phase(1000)  # -81.0°

# 频率响应
fr = lpf.frequency_response(10, 1e6, 1000)
```

### 2.6 放大器

```python
from src.applications import Amplifier

# 反相放大器
inv_amp = Amplifier(r_in=10000, r_f=100000, config='inverting')
gain = inv_amp.gain()           # -10.0
v_out = inv_amp.output_voltage(0.5)  # -5.0 V

# 同相放大器
non_inv_amp = Amplifier(r_in=10000, r_f=100000, config='non_inverting')
gain = non_inv_amp.gain()       # 11.0
v_out = non_inv_amp.output_voltage(0.5)  # 5.5 V
```

## 3. 使用示例

### 3.1 基础示例

```python
from src.circuit import Circuit
from src.dc_analysis import DCAnalyzer

# 欧姆定律
from src.components import ohms_law
result = ohms_law(voltage=12, resistance=1000)
print(f"电流: {result['current']*1000:.2f} mA")

# 分压器
from src.applications import VoltageDivider
divider = VoltageDivider(v_in=12, r1=1000, r2=2000)
print(f"输出电压: {divider.output_voltage():.2f} V")
```

### 3.2 滤波器设计

```python
from src.applications import RCFilter, RLCFilter

# RC低通滤波器
lpf = RCFilter(r=1000, c=1e-6, filter_type='low')
print(f"截止频率: {lpf.cutoff_frequency():.2f} Hz")

# RLC带通滤波器
bpf = RLCFilter(r=100, l=1e-3, c=1e-6, filter_type='bandpass')
print(f"谐振频率: {bpf.resonance_freq():.2f} Hz")
print(f"品质因数: {bpf.quality_factor():.2f}")
```

### 3.3 频率响应绘制

```python
import matplotlib.pyplot as plt
from src.applications import RCFilter

lpf = RCFilter(r=1000, c=1e-6, filter_type='low')
fr = lpf.frequency_response(10, 1e6, 1000)

plt.figure(figsize=(10, 6))
plt.semilogx(fr.frequencies, 20 * np.log10(fr.magnitude))
plt.xlabel('频率 (Hz)')
plt.ylabel('增益 (dB)')
plt.title('RC低通滤波器频率响应')
plt.grid(True)
plt.savefig('frequency_response.png')
```

## 4. API参考

### 4.1 元件模块

| 类/函数 | 说明 |
|---------|------|
| `Resistor` | 电阻元件 |
| `Capacitor` | 电容元件 |
| `Inductor` | 电感元件 |
| `VoltageSource` | 电压源 |
| `CurrentSource` | 电流源 |
| `ohms_law()` | 欧姆定律计算 |
| `power()` | 功率计算 |

### 4.2 电路模块

| 类/函数 | 说明 |
|---------|------|
| `Circuit` | 电路网络 |
| `Node` | 电路节点 |

### 4.3 分析模块

| 类/函数 | 说明 |
|---------|------|
| `DCAnalyzer` | 直流分析器 |
| `ACAnalyzer` | 交流分析器 |
| `voltage_divider()` | 分压器计算 |
| `current_divider()` | 分流器计算 |
| `series_resistance()` | 串联电阻计算 |
| `parallel_resistance()` | 并联电阻计算 |
| `resonance_frequency()` | 谐振频率计算 |
| `quality_factor()` | 品质因数计算 |

### 4.4 应用模块

| 类/函数 | 说明 |
|---------|------|
| `VoltageDivider` | 分压器 |
| `RCFilter` | RC滤波器 |
| `RLCFilter` | RLC滤波器 |
| `Amplifier` | 放大器 |
| `Integrator` | 积分器 |
| `Differentiator` | 微分器 |

## 5. 最佳实践

### 5.1 电路构建

```python
# 1. 创建电路
circuit = Circuit("My Circuit")

# 2. 添加节点
n0 = circuit.add_node("GND")
n1 = circuit.add_node("VCC")

# 3. 设置接地点
circuit.set_ground(n0)

# 4. 添加元件
circuit.add_voltage_source("V1", n0, n1, 10)
circuit.add_resistor("R1", n1, n0, 1000)
```

### 5.2 分析流程

```python
# 1. 创建分析器
analyzer = DCAnalyzer(circuit)

# 2. 求解
result = analyzer.solve()

# 3. 查看结果
print(result.node_voltages)
print(result.branch_currents)

# 4. 验证定律
print(result.kcl_violations)
print(result.kvl_violations)
```

### 5.3 可视化

```python
import matplotlib.pyplot as plt

# 计算频率响应
fr = analyzer.frequency_response(10, 1e6, 1000)

# 绘制幅频响应
plt.semilogx(fr.frequencies, 20 * np.log10(fr.magnitude))
plt.xlabel('频率 (Hz)')
plt.ylabel('增益 (dB)')
plt.grid(True)
plt.show()
```

## 6. 限制与注意事项

### 6.1 当前限制

- 仅支持线性电路
- 不支持非线性元件（二极管、晶体管）
- 不支持瞬态分析
- 不支持分布式参数电路

### 6.2 数值精度

- 使用双精度浮点数
- 矩阵求解可能有数值误差
- 极端参数值可能导致数值不稳定

### 6.3 性能考虑

- 大规模电路分析可能较慢
- 频率响应计算需要多次求解
- 建议使用适当的频率点数

## 7. 常见问题

### Q1: 如何设置接地点？

```python
circuit = Circuit()
n0 = circuit.add_node("GND")
circuit.set_ground(n0)  # 必须设置接地点
```

### Q2: 如何处理多个电压源？

使用MNA方法自动处理：
```python
circuit.add_voltage_source("V1", n0, n1, 10)
circuit.add_voltage_source("V2", n0, n2, 5)
```

### Q3: 如何计算截止频率？

```python
from src.applications import RCFilter
lpf = RCFilter(r=1000, c=1e-6, filter_type='low')
f_c = lpf.cutoff_frequency()  # 159.15 Hz
```

### Q4: 如何绘制频率响应？

```python
fr = lpf.frequency_response(10, 1e6, 1000)
plt.semilogx(fr.frequencies, 20 * np.log10(fr.magnitude))
plt.show()
```
