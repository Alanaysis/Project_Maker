# 流体力学基础 (Fluid Mechanics Basics)

一个用于学习流体力学原理的交互式Python项目。通过数值模拟和可视化，帮助理解管道流动和伯努利方程。

## 项目简介 / Project Description

本项目实现了一系列流体力学计算工具，涵盖管道流动分析、伯努利方程求解、Reynolds数计算、水头损失分析等核心内容。每个模块都包含详细的中文注释和公式推导，适合工程类专业学生学习参考。

This project implements a set of fluid mechanics calculation tools covering pipe flow analysis, Bernoulli equation solving, Reynolds number computation, head loss analysis, and more. Each module includes detailed Chinese comments and formula derivations, suitable for engineering students.

## 学习目标 / Learning Objectives

### 流体力学原理
- [x] 理解质量守恒（连续性方程）
- [x] 理解能量守恒（伯努利方程）
- [x] 理解动量守恒在管道流动中的应用

### 伯努利方程
- [x] 掌握伯努利方程的推导和应用
- [x] 理解压力头、速度头、高程头的物理意义
- [x] 能够解决变径管道、高度变化等问题

### 管道流动计算
- [x] 掌握Darcy-Weisbach方程
- [x] 理解摩擦系数与Reynolds数的关系
- [x] 能够计算串联/并联管道网络

### 流动状态分析
- [x] 理解Reynolds数的物理意义
- [x] 掌握层流/过渡流/湍流的判据
- [x] 能够判断不同条件下的流动状态

## 项目结构 / Project Structure

```
fluid-mechanics/
├── src/                          # 源代码模块
│   ├── bernoulli.py              # 伯努利方程求解器
│   ├── pipe_flow.py              # Darcy-Weisbach管道流动计算
│   ├── reynolds.py               # Reynolds数与流动状态分类
│   ├── head_loss.py              # 水头损失计算（沿程+局部）
│   ├── continuity.py             # 连续性方程
│   └── pressure_drop.py          # 压力降分析
├── examples/                     # 演示脚本
│   ├── bernoulli_demo.py         # 伯努利方程演示
│   ├── pipe_network.py           # 管道网络分析
│   ├── flow_regime_viz.py        # 流动状态可视化
│   └── pressure_drop_calc.py     # 压力降计算
├── tests/                        # 单元测试
│   └── test_fluid_mechanics.py
├── requirements.txt              # 依赖列表
└── README.md                     # 本文件
```

## 安装 / Installation

```bash
pip install -r requirements.txt
```

## 运行示例 / Running Examples

### 1. 伯努利方程演示
```bash
python examples/bernoulli_demo.py
```
展示伯努利方程在不同场景下的应用，包括水平管道、文丘里管、高度变化等。

### 2. 管道网络分析
```bash
python examples/pipe_network.py
```
分析串联和并联管道网络，展示流量分配和压力损失计算。

### 3. 流动状态可视化
```bash
python examples/flow_regime_viz.py
```
可视化不同条件下的流动状态，包括Reynolds数范围、临界速度、速度剖面等。

### 4. 压力降计算
```bash
python examples/pressure_drop_calc.py
```
计算各种场景下的压力降，包括沿程损失、局部损失和高程影响。

### 5. 运行单元测试
```bash
python -m pytest tests/test_fluid_mechanics.py -v
# 或
python tests/test_fluid_mechanics.py
```

## 流体力学理论基础 / Theory Background

### 伯努利方程 (Bernoulli Equation)

沿流线的能量守恒方程：

$$\frac{P}{\rho g} + \frac{v^2}{2g} + z = \text{constant}$$

- **压力头** P/ρg：单位重量流体的压力能
- **速度头** v²/2g：单位重量流体的动能
- **高程头** z：单位重量流体的势能

### Reynolds 数 (Reynolds Number)

判断流动状态的无量纲数：

$$Re = \frac{\rho v D}{\mu} = \frac{v D}{\nu}$$

流动状态判据：
- Re < 2300：层流 (Laminar)
- 2300 ≤ Re < 4000：过渡流 (Transitional)
- Re ≥ 4000：湍流 (Turbulent)

### Darcy-Weisbach 方程

计算沿程水头损失：

$$h_f = f \cdot \frac{L}{D} \cdot \frac{v^2}{2g}$$

摩擦系数 f 的确定：
- 层流：f = 64/Re
- 湍流：Colebrook 方程或 Swamee-Jain 近似

### 连续性方程 (Continuity Equation)

质量守恒的数学表达（不可压缩流体）：

$$A_1 v_1 = A_2 v_2 = Q = \text{constant}$$

### 水头损失 (Head Loss)

总水头损失 = 沿程损失 + 局部损失

$$h_{total} = h_f + h_m = f\frac{L}{D}\frac{v^2}{2g} + \sum K\frac{v^2}{2g}$$

## 管道材料粗糙度参考 / Pipe Roughness Reference

| 管道材料 | 粗糙度 ε (mm) |
|---------|--------------|
| 拉制管 | 0.0015 |
| 商用钢管 | 0.046 |
| 镀锌铁管 | 0.15 |
| 铸铁管 | 0.26 |
| 混凝土管 | 3.0 |

## 常用流体物性 / Fluid Properties (20°C)

| 流体 | 密度 (kg/m³) | 动力粘度 (Pa·s) |
|-----|-------------|----------------|
| 水 | 998.2 | 1.002×10⁻³ |
| 空气 | 1.204 | 1.825×10⁻⁵ |
| SAE 30机油 | 891.0 | 0.29 |
| 甘油 | 1261.0 | 1.49 |

## 许可证 / License

MIT License

## 贡献 / Contributing

欢迎提交 Issue 和 Pull Request！
