# Linkage Mechanism Analysis / 连杆机构分析

> **Learning project for planar linkage mechanism analysis**
> 平面连杆机构分析学习项目

---

## 简介 / Description

本项目实现四连杆（平面连杆机构）的位置分析、速度分析和加速度分析，
是一个教学性质的学习项目，帮助理解机械原理中的连杆机构理论。

This project implements position, velocity, and acceleration analysis for
four-bar (planar) linkage mechanisms. It is an educational learning project
designed to help understand linkage mechanism theory in mechanical engineering.

**核心分析流程 / Core Analysis Pipeline:**
```
机构参数 → 位置分析 → 速度分析 → 加速度分析
Linkage Parameters → Position → Velocity → Acceleration
```

---

## 学习目标 / Learning Objectives

### 理论知识 / Theoretical Knowledge
- **Grashof条件**：判断连杆机构是否可以完整旋转
- **矢量环法**：使用矢量环方程进行位置分析
- **频率分析**：通过微分位置方程进行速度和加速度分析
- **传动角**：评估机构传力性能
- **连杆曲线**：理解连杆上点的轨迹特性

### Grashof Condition: Determines if at least one link can rotate fully
### Vector Loop Method: Position analysis using vector loop equations
### Frequency Analysis: Velocity and acceleration by differentiating position equations
### Transmission Angle: Evaluate mechanism force transmission quality
### Coupler Curve: Understand trajectory characteristics of points on the coupler

---

## 项目结构 / Project Structure

```
linkage-mechanism/
├── src/                          # Source code
│   ├── __init__.py
│   ├── position_analysis.py      # 位置分析 (Grashof条件、连杆圆、连杆曲线)
│   ├── velocity_analysis.py      # 速度分析 (角速度、线速度、传动角)
│   ├── acceleration_analysis.py  # 加速度分析 (角加速度、线加速度)
│   └── visualization.py          # 可视化 (连杆图、曲线图、相位图)
├── examples/                     # 示例脚本
│   ├── 01_fourbar_simulation.py  # 四连杆仿真
│   ├── 02_coupler_curves.py      # 连杆曲线可视化
│   ├── 03_crank_rocker.py        # 曲柄摇杆机构分析
│   └── 04_slider_crank.py        # 滑块曲柄机构分析
├── tests/                        # 单元测试
│   ├── test_position_analysis.py
│   ├── test_velocity_analysis.py
│   ├── test_acceleration_analysis.py
│   └── test_visualization.py
├── requirements.txt
└── README.md
```

---

## 连杆理论基础 / Linkage Theory Background

### 四连杆机构 / Four-Bar Linkage

四连杆机构由四个刚性杆通过铰链连接组成：
- **机架 (Ground Link)**: 固定不动的杆
- **曲柄 (Crank)**: 可以完整旋转的杆
- **连杆 (Coupler)**: 连接曲柄和摇杆的浮动杆
- **摇杆 (Rocker)**: 只能摆动的杆

### Grashof条件 / Grashof Condition

对于四连杆机构，令：
- s = 最短杆长度
- l = 最长杆长度
- p, q = 其余两杆长度

Grashof条件：**s + l ≤ p + q**

| 条件 | 类型 | 说明 |
|------|------|------|
| s + l < p + q | Grashof | 至少一杆可完整旋转 |
| s + l = p + q | 特殊 (变点) | 机构处于变点位置 |
| s + l > p + q | 非Grashof | 无杆可完整旋转 |

### 机构类型 / Mechanism Types

基于Grashof条件和接地杆的位置：

| 机构类型 | 特征 |
|----------|------|
| 曲柄摇杆 (Crank-Rocker) | 曲柄完整旋转，摇杆摆动 |
| 双曲柄 (Double-Crank) | 两杆均可完整旋转 |
| 双摇杆 (Double-Rocker) | 两杆均只能摆动 |

### 位置分析 / Position Analysis

使用矢量环方程：
```
r₂ + r₃ = r₁ + r₄
```

分解为两个标量方程：
```
a₂·cos(θ₂) + a₃·cos(θ₃) = a₁ + a₄·cos(θ₄)
a₂·sin(θ₂) + a₃·sin(θ₃) = a₄·sin(θ₄)
```

通过Freudenstein方程求解未知角度。

### 速度分析 / Velocity Analysis

对位置方程求导：
```
-dθ₂/dt·a₂·sin(θ₂) - dθ₃/dt·a₃·sin(θ₃) = -dθ₄/dt·a₄·sin(θ₄)
dθ₂/dt·a₂·cos(θ₂) + dθ₃/dt·a₃·cos(θ₃) = dθ₄/dt·a₄·cos(θ₄)
```

求解线性方程组得到 ω₃ 和 ω₄。

### 加速度分析 / Acceleration Analysis

对速度方程求导，得到角加速度 α₃ 和 α₄。

### 传动角 / Transmission Angle

传动角 μ 是连杆与摇杆之间的夹角。
- **理想值**: 90°
- **可接受范围**: 40° ~ 140°
- 传动角过小会导致传力性能下降

---

## 如何运行示例 / How to Run Examples

### 1. 安装依赖 / Install Dependencies

```bash
cd projects/linkage-mechanism
pip install -r requirements.txt
```

### 2. 运行示例 / Run Examples

```bash
# 四连杆仿真
python examples/01_fourbar_simulation.py

# 连杆曲线可视化
python examples/02_coupler_curves.py

# 曲柄摇杆机构分析
python examples/03_crank_rocker.py

# 滑块曲柄机构分析
python examples/04_slider_crank.py
```

每个示例会生成 PNG 图像文件到 `examples/` 目录。

### 3. 运行测试 / Run Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## API 参考 / API Reference

### FourBarParams
```python
from src.position_analysis import FourBarParams

params = FourBarParams(
    a1=4.0,        # 机架长度
    a2=1.5,        # 曲柄长度
    a3=4.5,        # 连杆长度
    a4=3.5,        # 摇杆长度
    o2=(0.0, 0.0), # 曲柄固定铰链位置
    o4=(4.0, 0.0), # 摇杆固定铰链位置
)
```

### 位置分析 / Position Analysis
```python
from src.position_analysis import position_analysis, check_grashof

# 检查Grashof条件
grashof_type = check_grashof(params)

# 位置分析
pos = position_analysis(params, theta2=np.pi/4)
# pos.theta3: 连杆角度
# pos.theta4: 摇杆角度
# pos.coupler_point: 连杆上点的位置
```

### 速度分析 / Velocity Analysis
```python
from src.velocity_analysis import velocity_analysis, compute_transmission_angle

omega3, omega4 = velocity_analysis(params, theta2, omega2)
mu = compute_transmission_angle(params, theta2)  # 传动角
```

### 加速度分析 / Acceleration Analysis
```python
from src.acceleration_analysis import acceleration_analysis

alpha3, alpha4 = acceleration_analysis(params, theta2, omega2, alpha2)
```

### 可视化 / Visualization
```python
from src.visualization import plot_linkage, plot_coupler_curve

plot_linkage(params, theta2)
plot_coupler_curve(params, coupler_point_ratio=(0.5, 0.3))
```

---

## 数学符号说明 / Notation

| 符号 | 含义 |
|------|------|
| a₁, a₂, a₃, a₄ | 各杆长度 |
| θ₂, θ₃, θ₄ | 各杆角度 |
| ω₂, ω₃, ω₄ | 各杆角速度 |
| α₂, α₃, α₄ | 各杆角加速度 |
| μ | 传动角 |
| s, l, p, q | Grashof条件中的杆长 |

---

## 参考资源 / References

- Norton, R. L. "Design of Machinery" - 机械原理经典教材
- Erdman, A. G. et al. "Modern Kinematics" - 运动学现代方法
- Juvinall, R. C. "Fundamentals of Machine Component Design" - 机械元件设计基础

---

## 许可证 / License

MIT License
