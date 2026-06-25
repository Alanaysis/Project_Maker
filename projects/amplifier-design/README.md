# 放大器设计 (Amplifier Design)

从零实现模拟放大器设计，深入理解BJT放大器、运算放大器电路和频率响应分析。

## 项目概述

本项目实现了完整的模拟放大器设计库，包括 BJT 基本放大器（共射、共集、共基）、运算放大器电路（反相、同相、差分、仪表放大器）、频率响应分析和实际应用（信号调理、传感器放大、音频放大）。

### 核心循环

```
信号源 → 放大器拓扑 → 增益/带宽设计 → 频率补偿 → 实际应用
```

### 学习目标

- 理解 BJT 三种基本放大器配置的工作原理
- 掌握运算放大器电路的设计方法
- 学会频率响应分析和相位补偿技术
- 理解放大器在传感器、音频等领域的实际应用

## 项目结构

```
amplifier-design/
├── README.md                 # 项目说明
├── docs/                     # 文档目录
│   ├── 01_RESEARCH.md        # 调研报告
│   ├── 02_REQUIREMENTS.md    # 需求文档
│   ├── 03_DESIGN.md          # 设计文档
│   ├── 04_PRODUCT.md         # 产品文档
│   └── 05_DEVELOPMENT.md     # 开发日志
├── src/                      # 源代码
│   ├── __init__.py
│   ├── bjt.py                # BJT 基本放大器
│   ├── opamp.py              # 运算放大器电路
│   ├── frequency.py          # 频率响应分析
│   └── applications.py       # 实际应用
├── tests/                    # 测试代码
│   ├── test_bjt.py
│   ├── test_opamp.py
│   ├── test_frequency.py
│   └── test_applications.py
├── examples/                 # 示例代码
│   ├── basic_amplifiers.py   # BJT 放大器演示
│   ├── opamp_circuits.py     # 运放电路演示
│   ├── frequency_response.py # 频率响应演示
│   └── applications_demo.py  # 应用演示
└── requirements.txt
```

## 快速开始

### 环境要求

- Python 3.8+
- NumPy
- Matplotlib (可选，用于可视化)

### 安装依赖

```bash
pip install numpy matplotlib pytest
```

### 运行示例

```bash
cd projects/amplifier-design

# BJT 放大器演示
python examples/basic_amplifiers.py

# 运放电路演示
python examples/opamp_circuits.py

# 频率响应演示
python examples/frequency_response.py

# 应用演示
python examples/applications_demo.py
```

### 运行测试

```bash
cd projects/amplifier-design
python -m pytest tests/ -v
```

## 核心模块

### 1. BJT 基本放大器

三种经典 BJT 放大器配置：

```python
from src.bjt import BJTParams, CommonEmitter, CommonCollector, CommonBase

bjt = BJTParams(beta=100, V_A=100, V_BE=0.7)

# 共射放大器: 高增益，反相
ce = CommonEmitter(R_B1=47e3, R_B2=10e3, R_C=4.7e3, R_E=2.2e3, V_CC=12, bjt=bjt)
print(f"电压增益: {ce.voltage_gain():.1f}")       # 约 -50
print(f"输入阻抗: {ce.input_impedance():.0f} Ohm")

# 共集放大器: 增益≈1，高输入阻抗
cc = CommonCollector(R_B1=47e3, R_B2=10e3, R_E=2.2e3, V_CC=12, bjt=bjt)
print(f"电压增益: {cc.voltage_gain():.4f}")        # 约 0.99

# 共基放大器: 高增益，同相
cb = CommonBase(R_E=2.2e3, R_C=4.7e3, V_CC=12, I_C_bias=1e-3, bjt=bjt)
print(f"电压增益: {cb.voltage_gain():.1f}")        # 约 180
```

### 2. 运算放大器电路

```python
from src.opamp import InvertingAmp, NonInvertingAmp, DifferentialAmp, InstrumentationAmp

# 反相放大器: Av = -Rf/Rin
inv = InvertingAmp(R_in=10e3, R_f=100e3)
print(f"增益: {inv.gain()}")                        # -10.0
print(f"带宽: {inv.bandwidth()/1e3:.0f} kHz")       # 100 kHz

# 同相放大器: Av = 1 + Rf/Rin
ni = NonInvertingAmp(R_in=10e3, R_f=100e3)
print(f"增益: {ni.gain()}")                         # 11.0

# 差分放大器
diff = DifferentialAmp(R1=10e3, R_f=100e3)
print(f"差模增益: {diff.differential_gain()}")       # 10.0
print(f"CMRR: {diff.cmrr():.0f} dB")

# 仪表放大器: G = 1 + 2*R1/Rg
inamp = InstrumentationAmp(R1=49.4e3, R_g=1e3)
print(f"增益: {inamp.gain():.1f}")                  # 99.8
inamp.set_gain(200)  # 动态设置增益
```

### 3. 频率响应分析

```python
from src.frequency import GainBandwidthProduct, PhaseCompensation, StabilityAnalyzer

# 增益带宽积
gbw = GainBandwidthProduct(gbw=1e6)
print(f"增益10时带宽: {gbw.bandwidth_at_gain(10)/1e3:.0f} kHz")  # 100 kHz

# 相位补偿
result = PhaseCompensation.dominant_pole_compensation(
    gbw_original=1e6, f_p1=1e3, f_p2=5e5, f_new_pole=100
)
print(f"相位裕度: {result['phase_margin']:.1f}°")

# 稳定性分析
tf = StabilityAnalyzer.loop_gain_tf(gbw=1e6, gain=100)
result = StabilityAnalyzer.phase_margin(tf)
print(f"相位裕度: {result['phase_margin']:.1f}°")
print(f"稳定: {result['stable']}")
```

### 4. 实际应用

```python
from src.applications import SignalConditioner, SensorAmplifier, AudioAmplifier

# 信号调理
sc = SignalConditioner(gain=3.3, offset=1.65, v_ref=0.0)
output = sc.process(sensor_signal)

# 热电偶放大
sa = SensorAmplifier()
tc = sa.thermocouple_amp(R_g=100, R1=49.4e3)
print(f"灵敏度: {tc['sensitivity']*1e3:.2f} mV/°C")

# 应变片放大
sg = sa.strain_gauge_amp(R_gauge=350, R_g=1000, V_excitation=5.0)
print(f"灵敏度: {sg['sensitivity']:.3f} V/strain")

# 音频前置放大
audio = AudioAmplifier(v_supply=15.0)
preamp = audio.preamp(R_in=1e3, R_f=100e3)
print(f"增益: {preamp['gain_dB']:.1f} dB")
```

## 放大器特性总结

### BJT 放大器对比

| 配置 | 增益 | 输入阻抗 | 输出阻抗 | 相移 | 用途 |
|------|------|---------|---------|------|------|
| 共射 (CE) | 高 | 中 | 高 | 180° | 电压放大 |
| 共集 (CC) | ≈1 | 高 | 低 | 0° | 缓冲器 |
| 共基 (CB) | 高 | 低 | 高 | 0° | 高频放大 |

### 运放电路对比

| 电路 | 增益 | 输入阻抗 | 带宽 | 用途 |
|------|------|---------|------|------|
| 反相 | -Rf/Rin | Rin | GBW/\|Av\| | 通用放大 |
| 同相 | 1+Rf/Rin | 很高 | GBW/\|Av\| | 高阻抗源 |
| 差分 | Rf/R1 | ~R1 | GBW/\|Av\| | 共模抑制 |
| 仪表 | 1+2R1/Rg | ~GOhm | GBW/G | 传感器 |

### 关键公式

| 参数 | 公式 |
|------|------|
| 跨导 | g_m = I_C / V_T |
| 增益带宽积 | GBW = \|Av\| x BW |
| 相位裕度 | PM = 180° + angle(H) at \|H\|=1 |
| 转换速率限制 | V_max = SR / (2πf) |

## 参考资源

- 《模拟电子技术基础》- 童诗白、华成英
- 《晶体管电路设计》- 铃木雅臣
- 《运算放大器权威指南》- Ron Mancini
- [MIT OCW - Circuits and Electronics](https://ocw.mit.edu/courses/6-002/)
- [TI Analog Engineer's Pocket Reference](https://www.ti.com/lit/pdf/sboa325)

## 许可证

MIT License
