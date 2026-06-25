# 模拟滤波器 (Analog Filter)

从零实现模拟滤波器，深入理解滤波器原理、频率响应和实际应用。

## 项目概述

本项目实现了常见的模拟滤波器，包括 RC/RL 低通、高通滤波器，以及 RLC 带通、带阻滤波器。通过纯 Python 实现，不依赖信号处理库，帮助深入理解模拟电路和滤波器的工作原理。

### 核心循环

```
电路元件 → 传递函数 → 频率响应 → 实际应用
```

### 学习目标

- 理解 RC/RL/RLC 电路的工作原理
- 掌握传递函数的推导和计算
- 学会频率响应分析 (幅频响应、相频响应)
- 理解波特图的含义和应用
- 掌握滤波器在音频处理和信号调理中的应用

## 项目结构

```
analog-filter/
├── README.md                 # 项目说明
├── LEARNING_NOTES.md         # 学习笔记
├── docs/                     # 文档目录
│   ├── 01_RESEARCH.md        # 调研报告
│   ├── 02_REQUIREMENTS.md    # 需求文档
│   ├── 03_DESIGN.md          # 设计文档
│   ├── 04_PRODUCT.md         # 产品文档
│   └── 05_DEVELOPMENT.md     # 开发日志
├── src/                      # 源代码
│   ├── __init__.py
│   ├── lowpass.py            # 低通滤波器 (RC/RL)
│   ├── highpass.py           # 高通滤波器 (RC/RL)
│   ├── bandpass.py           # 带通滤波器 (RLC)
│   ├── bandstop.py           # 带阻滤波器 (RLC)
│   ├── frequency_response.py # 频率响应分析
│   ├── visualization.py      # 可视化工具
│   └── applications.py       # 实际应用
├── tests/                    # 测试代码
│   ├── test_lowpass.py
│   ├── test_highpass.py
│   ├── test_bandpass.py
│   ├── test_bandstop.py
│   └── test_frequency_response.py
└── examples/                 # 示例代码
    ├── basic_filters.py      # 基本滤波器演示
    ├── audio_processing.py   # 音频处理应用
    └── signal_conditioning.py # 信号调理应用
```

## 快速开始

### 环境要求

- Python 3.8+
- NumPy
- Matplotlib (可选，用于可视化)

### 安装依赖

```bash
pip install numpy matplotlib
```

### 运行示例

```bash
cd projects/analog-filter

# 基本滤波器演示
python examples/basic_filters.py

# 音频处理应用
python examples/audio_processing.py

# 信号调理应用
python examples/signal_conditioning.py
```

### 运行测试

```bash
cd projects/analog-filter
python -m pytest tests/ -v
```

## 核心模块

### 1. 低通滤波器

允许低频信号通过，衰减高频信号。

```python
from src.lowpass import RCLowPass, RLLowPass

# RC 低通: R=1kΩ, C=1μF
rc_lp = RCLowPass(R=1000, C=1e-6)
print(f"截止频率: {rc_lp.fc:.2f} Hz")

# RL 低通: R=100Ω, L=0.1H
rl_lp = RLLowPass(R=100, L=0.1)
print(f"截止频率: {rl_lp.fc:.2f} Hz")

# 计算频率响应
import numpy as np
f = np.logspace(1, 5, 100)
mag_db = rc_lp.magnitude_db(f)
phase = rc_lp.phase(f)
```

### 2. 高通滤波器

允许高频信号通过，衰减低频信号。

```python
from src.highpass import RCHighPass, RLHighPass

# RC 高通: R=1kΩ, C=1μF
rc_hp = RCHighPass(R=1000, C=1e-6)
print(f"截止频率: {rc_hp.fc:.2f} Hz")
```

### 3. 带通滤波器

允许特定频率范围内的信号通过。

```python
from src.bandpass import RLCBandPass

# RLC 带通: R=100Ω, L=10mH, C=1μF
bp = RLCBandPass(R=100, L=0.01, C=1e-6)
print(f"中心频率: {bp.f0:.2f} Hz")
print(f"带宽: {bp.bw:.2f} Hz")
print(f"品质因数: {bp.Q:.2f}")
```

### 4. 带阻滤波器 (陷波滤波器)

衰减特定频率范围内的信号。

```python
from src.bandstop import RLCBandStop

# RLC 带阻: R=100Ω, L=10mH, C=1μF
bs = RLCBandStop(R=100, L=0.01, C=1e-6)
print(f"中心频率: {bs.f0:.2f} Hz")
```

### 5. 频率响应分析

```python
from src.frequency_response import generate_log_freq, analyze_filter

# 生成频率数组
f = generate_log_freq(1, 1e6, 1000)

# 分析滤波器
result = analyze_filter(rc_lp, f)
print(f"截止频率: {result['cutoff_frequency']:.2f} Hz")
```

### 6. 实际应用

```python
from src.applications import AudioCrossover, NotchFilter, SignalConditioner

# 音频分频器
crossover = AudioCrossover(crossover_freq=1000)
low_out = crossover.process(signal, t, 'low')
high_out = crossover.process(signal, t, 'high')

# 陷波滤波器 (消除 50Hz 工频干扰)
notch = NotchFilter(notch_freq=50.0, Q=30)
cleaned = notch.process(noisy_signal, t)

# 信号调理器
conditioner = SignalConditioner(fs=1000)
signal = conditioner.remove_dc_offset(signal, t)
signal = conditioner.remove_powerline_hum(signal, t)
```

## 滤波器特性总结

| 滤波器类型 | 传递函数 | 截止频率 | 相位范围 |
|-----------|---------|---------|---------|
| RC 低通 | 1/(1+sRC) | 1/(2πRC) | 0° ~ -90° |
| RL 低通 | (R/L)/(s+R/L) | R/(2πL) | 0° ~ -90° |
| RC 高通 | sRC/(1+sRC) | 1/(2πRC) | +90° ~ 0° |
| RL 高通 | s/(s+R/L) | R/(2πL) | +90° ~ 0° |
| RLC 带通 | (s/RC)/(s²+s/RC+1/LC) | 1/(2π√LC) | +90° ~ -90° |
| RLC 带阻 | (s²+1/LC)/(s²+s/RC+1/LC) | 1/(2π√LC) | 0° ~ ±180° ~ 0° |

## 可视化

使用 matplotlib 绘制波特图：

```python
from src.visualization import plot_bode, plot_comparison

# 单个滤波器波特图
plot_bode(rc_lp, f, title="RC 低通滤波器波特图")

# 多滤波器对比
plot_comparison([rc_lp, rl_lp], f, labels=["RC", "RL"])
```

## 参考资源

- 《模拟电子技术基础》- 童诗白
- 《电路》- 邱关源
- 《信号与系统》- 奥本海姆
- [MIT OpenCourseWare - Circuits and Electronics](https://ocw.mit.edu/courses/6-002-circuits-and-electronics-spring-2007/)
