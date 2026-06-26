# Vibration Analysis System / 振动分析系统

> 实现机械振动分析和模态分析 | Implement mechanical vibration analysis and modal analysis

---

## 📖 项目描述 / Project Description

### 中文

本项目是一个振动分析学习系统，实现了单自由度和多自由度系统的振动分析功能。通过数值模拟和可视化，帮助理解振动原理、模态分析和频响分析。

**核心功能:**
- 自由振动分析（无阻尼和有阻尼）
- 强迫振动响应（简谐、阶跃、脉冲激励）
- 模态分析（固有频率、模态振型、模态叠加法）
- 频响函数分析（FRF、Bode图、Nyquist图）
- 多自由度系统分析
- 共振检测与避免设计

### English

This project is a vibration analysis learning system that implements vibration analysis for single-degree-of-freedom (SDOF) and multi-degree-of-freedom (MDOF) systems. Through numerical simulation and visualization, it helps understand vibration principles, modal analysis, and frequency response analysis.

**Core Features:**
- Free vibration analysis (undamped and damped)
- Forced vibration response (harmonic, step, impulse excitation)
- Modal analysis (natural frequencies, mode shapes, modal superposition)
- Frequency Response Function (FRF) analysis (Bode plots, Nyquist plots)
- Multi-degree-of-freedom system analysis
- Resonance detection and avoidance design

---

## 🎯 学习目标 / Learning Objectives

### 中文

1. **理解振动原理**
   - 掌握自由振动和强迫振动的基本理论
   - 理解阻尼对振动的影响
   - 掌握对数衰减率测量阻尼的方法

2. **掌握模态分析**
   - 理解固有频率和模态振型的物理意义
   - 掌握模态正交性原理
   - 理解模态叠加法求解多自由度系统响应

3. **学会频响分析**
   - 理解频响函数的定义和物理意义
   - 掌握Bode图和Nyquist图的绘制
   - 学会共振检测和避免设计

### English

1. **Understand Vibration Principles**
   - Master basic theory of free and forced vibration
   - Understand the effect of damping on vibration
   - Learn logarithmic decrement method for damping measurement

2. **Master Modal Analysis**
   - Understand physical meaning of natural frequencies and mode shapes
   - Master modal orthogonality principle
   - Understand modal superposition for MDOF system response

3. **Learn Frequency Response Analysis**
   - Understand definition and physical meaning of FRF
   - Master Bode and Nyquist plot plotting
   - Learn resonance detection and avoidance design

---

## 📁 项目结构 / Project Structure

```
vibration-analysis/
├── src/                          # 源代码 / Source code
│   ├── __init__.py
│   ├── free_vibration.py         # 自由振动分析 (Free vibration analysis)
│   ├── forced_vibration.py       # 强迫振动响应 (Forced vibration response)
│   ├── modal_analysis.py         # 模态分析 (Modal analysis)
│   ├── frequency_response.py     # 频响函数 (Frequency response function)
│   ├── multi_dof.py             # 多自由度系统 (MDOF systems)
│   └── resonance.py             # 共振检测 (Resonance detection)
├── examples/                     # 示例 / Examples
│   ├── 01_spring_mass_simulation.py    # 弹簧-质量系统仿真
│   ├── 02_modal_analysis_demo.py       # 模态分析演示
│   ├── 03_forced_vibration_response.py # 强迫振动响应
│   └── 04_resonance_analysis.py        # 共振分析
├── tests/                      # 测试 / Tests
│   ├── __init__.py
│   ├── test_free_vibration.py
│   ├── test_forced_vibration.py
│   ├── test_modal_analysis.py
│   └── test_resonance.py
├── README.md
├── requirements.txt
└── tests/
```

---

## 🚀 快速开始 / Quick Start

### 1. 安装依赖 / Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. 运行示例 / Run Examples

```bash
# 弹簧-质量系统仿真
python examples/01_spring_mass_simulation.py

# 模态分析演示
python examples/02_modal_analysis_demo.py

# 强迫振动响应
python examples/03_forced_vibration_response.py

# 共振分析
python examples/04_resonance_analysis.py
```

### 3. 运行测试 / Run Tests

```bash
pytest tests/ -v
```

---

## 📚 振动理论基础 / Vibration Theory Background

### 1. 自由振动 / Free Vibration

**运动方程 / Equation of Motion:**

```
m*x'' + c*x' + k*x = 0
```

其中:
- `m`: 质量 (mass) [kg]
- `c`: 阻尼系数 (damping coefficient) [N*s/m]
- `k`: 刚度系数 (stiffness coefficient) [N/m]
- `x`: 位移 (displacement) [m]

**固有频率 / Natural Frequency:**

```
omega_n = sqrt(k/m) [rad/s]
f_n = omega_n / (2*pi) [Hz]
```

**阻尼比 / Damping Ratio:**

```
zeta = c / (2 * m * omega_n)
```

阻尼分类 / Damping Classification:
- `zeta = 0`: 无阻尼 (Undamped) - 持续振荡
- `0 < zeta < 1`: 欠阻尼 (Underdamped) - 衰减振荡
- `zeta = 1`: 临界阻尼 (Critically damped) - 最快回到平衡
- `zeta > 1`: 过阻尼 (Overdamped) - 缓慢回到平衡

### 2. 强迫振动 / Forced Vibration

**运动方程 / Equation of Motion:**

```
m*x'' + c*x' + k*x = F(t)
```

**简谐激励 / Harmonic Excitation:**

```
F(t) = F0 * sin(omega_f * t)
```

**稳态响应幅值 / Steady-State Amplitude:**

```
X = (F0/k) / sqrt((1-r^2)^2 + (2*zeta*r)^2)
```

其中 `r = omega_f / omega_n` 为频率比。

**频响函数 / Frequency Response Function:**

```
H(omega) = X(omega) / F(omega) = 1 / (k - m*omega^2 + i*c*omega)
```

### 3. 模态分析 / Modal Analysis

**广义特征值问题 / Generalized Eigenvalue Problem:**

```
(K - omega^2 * M) * phi = 0
```

其中:
- `K`: 刚度矩阵 (stiffness matrix)
- `M`: 质量矩阵 (mass matrix)
- `omega`: 固有频率 (natural frequency)
- `phi`: 模态振型 (mode shape)

**模态正交性 / Modal Orthogonality:**

```
phi_i^T * M * phi_j = 0  (i != j)
phi_i^T * K * phi_j = 0  (i != j)
```

### 4. 共振 / Resonance

**共振条件 / Resonance Condition:**

```
激励频率 = 固有频率
forcing_freq = natural_freq
```

**品质因数 / Quality Factor:**

```
Q = 1 / (2*zeta)
```

**半功率带宽 / Half-Power Bandwidth:**

```
B = omega_2 - omega_1
zeta = B / (2 * omega_n)
```

---

## 📊 核心公式 / Key Formulas

| 概念 | 公式 | 说明 |
|------|------|------|
| 固有频率 | omega_n = sqrt(k/m) | 无阻尼固有频率 |
| 阻尼比 | zeta = c / (2*m*omega_n) | 无量纲阻尼 |
| 有阻尼频率 | omega_d = omega_n * sqrt(1-zeta^2) | 欠阻尼系统 |
| 共振频率 | omega_r = omega_n * sqrt(1-2*zeta^2) | 振幅最大处 |
| Q因子 | Q = 1 / (2*zeta) | 品质因数 |
| 频响函数 | H(omega) = 1/(k-m*omega^2+i*c*omega) | 位移/力 |
| 放大因子 | AF = 1/sqrt((1-r^2)^2+(2*zeta*r)^2) | 稳态幅值比 |

---

## 🔧 使用示例 / Usage Examples

### 基本振动分析

```python
from src.free_vibration import (
    natural_frequency,
    damping_ratio,
    free_vibration_damped,
)

# 系统参数
mass = 1.0      # kg
stiffness = 100.0  # N/m
damping = 2.0       # N*s/m

# 计算固有频率
omega_n = natural_frequency(stiffness, mass)
print(f"固有频率: {omega_n:.4f} rad/s")

# 计算阻尼比
zeta = damping_ratio(damping, stiffness, mass)
print(f"阻尼比: {zeta:.4f}")

# 有阻尼自由振动
result = free_vibration_damped(stiffness, mass, damping,
                               initial_displacement=1.0,
                               duration=5.0)
```

### 模态分析

```python
from src.modal_analysis import modal_analysis
from src.multi_dof import build_spring_mass_matrices

# 构建两自由度系统矩阵
mass_matrix, stiffness_matrix = build_spring_mass_matrices(
    masses=[1.0, 2.0],
    springs=[(0, 1, 200.0)],
    ground_springs=[(0, 100.0), (1, 150.0)]
)

# 执行模态分析
modal = modal_analysis(mass_matrix, stiffness_matrix)
print(f"固有频率: {modal.natural_freq_hz}")
print(f"模态振型:\n{modal.mode_shapes}")
```

### 频响分析

```python
from src.frequency_response import displacement_frf
import numpy as np

freq_range = np.linspace(0.1, 20, 1000)
frf = displacement_frf(stiffness, mass, damping, freq_range)

print(f"共振频率: {freq_range[np.argmax(frf.magnitude)]:.2f} Hz")
print(f"最大幅值: {np.max(frf.magnitude):.4f}")
```

---

## 📝 振动理论背景补充 / Additional Theory Notes

### 振动分类 / Vibration Classification

1. **自由振动 (Free Vibration)**: 系统受初始扰动后无外力作用的振动
2. **强迫振动 (Forced Vibration)**: 系统受持续外力作用的振动
3. **自激振动 (Self-Excited Vibration)**: 系统从非振荡能源获取能量维持振动
4. **参数振动 (Parametric Vibration)**: 系统参数周期性变化引起的振动

### 阻尼类型 / Damping Types

1. **粘性阻尼 (Viscous Damping)**: 阻尼力与速度成正比
2. **库仑阻尼 (Coulomb Damping)**: 摩擦阻尼，恒定大小
3. **结构阻尼 (Structural Damping)**: 材料内摩擦引起的阻尼
4. **辐射阻尼 (Radiation Damping)**: 能量向周围环境辐射

### 工程应用 / Engineering Applications

- 建筑结构抗震分析
- 机械振动隔离设计
- 旋转机械转子动力学
- 桥梁风振分析
- 汽车悬架系统优化
- 航空航天结构模态测试

---

## 📄 许可证 / License

MIT License

---

## 🙏 致谢 / Acknowledgments

- 振动理论参考: "Mechanical Vibrations" by S.S. Rao
- 模态分析参考: "Modal Analysis" by J. Ewins
- 数值方法参考: scipy 和 numpy 库
