# Cam Mechanism Learning Project / 凸轮机构学习项目

> 实现凸轮设计和运动分析的交互式学习项目

## English

A comprehensive learning project for cam mechanism design and motion analysis.
This project implements core concepts of cam-follower systems including profile
generation, motion law analysis, pressure angle evaluation, curvature analysis,
and dynamic simulation.

## 中文

凸轮机构设计与运动分析的综合学习项目。本项目实现了凸轮-从动件系统的核心概念，
包括轮廓生成、运动规律分析、压力角评估、曲率分析和动力学仿真。

---

## Learning Objectives / 学习目标

### 理解凸轮原理 / Understand Cam Principles
- 凸轮机构的基本组成和工作原理
- 从动件的运动规律及其特性
- 压力角的定义和影响

### 掌握凸轮轮廓设计 / Master Cam Profile Design
- 不同从动件类型的轮廓生成方法
- 基圆半径对性能的影响
- 避免轮廓失真的曲率分析

### 学会运动分析 / Learn Motion Analysis
- 压力角计算与校核
- 接触应力估算（赫兹接触理论）
- 动力学分析（惯性力、固有频率、共振）

---

## Theory Background / 理论基础

### Cam Mechanism / 凸轮机构

A cam mechanism converts rotary motion into linear or oscillating motion.
It consists of three main components:

1. **Cam (凸轮)**: Rotating or translating element with a curved profile
2. **Follower (从动件)**: Element that follows the cam profile
3. **Frame (机架)**: Supports the cam and guides the follower

### Follower Types / 从动件类型

| Type / 类型 | Description / 说明 | Application / 应用 |
|---|---|---|
| Roller (滚子) | Low friction, wear resistant | General purpose |
| Flat-foot (平底) | Simple, compact | Valves, automation |
| Pin (尖顶) | Simple geometry | Low load applications |

### Motion Laws / 运动规律

| Law / 规律 | Smoothness / 平滑度 | Speed / 速度 | Peak Accel / 峰值加速度 |
|---|---|---|---|
| Uniform (等速) | Low - rigid impact | Low speed | Infinite at boundaries |
| Parabolic (等加速) | Medium - soft impact | Medium | 8h/phi² |
| Cycloidal (摆线) | High - no impact | Medium-high | 6.28h/phi² |
| Polynomial 5th (五次多项式) | Very high | High | 13.6h/phi² |
| Modified Sine (改良正弦) | Very high | High | 5.5h/phi² |
| Modified Trapezoidal (改良梯形) | Very high | High | 5.5h/phi² |

### Pressure Angle / 压力角

The pressure angle is the angle between the follower velocity direction
and the normal to the cam profile at the contact point.

- **Smaller** pressure angle = better force transmission
- **Maximum allowable**: typically 30° for translating followers
- If pressure angle approaches 90°, the mechanism jams (自锁)

### Curvature & Undercutting / 曲率与失真

For roller followers, the curvature radius must be greater than the roller radius:
- **rho_min > r_roller** to avoid undercutting (轮廓失真)
- Undercutting occurs when the cam profile becomes self-intersecting

---

## Project Structure / 项目结构

```
cam-mechanism/
├── src/                      # Source code / 源代码
│   ├── __init__.py
│   ├── motion_laws.py        # Follower motion laws / 从动件运动规律
│   ├── cam_profile.py        # Cam profile generation & curvature / 凸轮轮廓生成与曲率分析
│   ├── pressure_angle.py     # Pressure angle analysis / 压力角分析
│   ├── contact_stress.py     # Hertz contact stress / 赫兹接触应力
│   ├── dynamic_analysis.py   # Dynamic analysis / 动力学分析
│   └── visualization.py      # Plotting tools / 可视化工具
├── examples/                 # Demo scripts / 演示脚本
│   ├── example1_cam_profile.py
│   ├── example2_motion_law_comparison.py
│   ├── example3_pressure_angle.py
│   └── example4_dynamic_simulation.py
├── tests/                    # Unit tests / 单元测试
│   ├── test_motion_laws.py
│   ├── test_cam_profile.py
│   ├── test_dynamic_analysis.py
│   └── test_contact_stress.py
├── requirements.txt          # Dependencies / 依赖
└── README.md                 # This file
```

---

## Quick Start / 快速开始

### Prerequisites / 前置条件

- Python 3.8+
- matplotlib
- numpy

### Installation / 安装

```bash
cd cam-mechanism
pip install -r requirements.txt
```

### Running Examples / 运行示例

```bash
# Example 1: Cam profile generation for different followers
python examples/example1_cam_profile.py

# Example 2: Motion law comparison
python examples/example2_motion_law_comparison.py

# Example 3: Pressure angle analysis
python examples/example3_pressure_angle.py

# Example 4: Dynamic simulation
python examples/example4_dynamic_simulation.py
```

All examples generate figures in the `examples/output/` directory.

### Running Tests / 运行测试

```bash
pip install pytest
pytest tests/ -v
```

---

## Cam Design Workflow / 凸轮设计流程

```
1. Motion Law Selection    →  2. Profile Generation    →  3. Pressure Angle Check
   选择运动规律               生成凸轮轮廓                  压力角校核
       │                           │                              │
       ▼                           ▼                              ▼
   Select smooth law      Calculate profile       Check: max PA <= 30°
   for speed range        for follower type       (or 35-40° for oscillating)
                        ┌─────────────────────────────────────────────┐
                        │                                             │
                        ▼                                             ▼
               4. Curvature Analysis              5. Dynamic Analysis
                  曲率分析                         动力学分析
                        │                              │
                        ▼                              ▼
               Check: rho > r_roller          Check: no contact loss
               Avoid undercutting             Check: F_spring > F_inertia
```

---

## Key Formulas / 核心公式

### Kinematics / 运动学

- **Displacement**: s = f(theta) - 位移函数
- **Velocity**: v = ds/dt = (ds/dtheta) * omega
- **Acceleration**: a = d²s/dt² = (d²s/dtheta²) * omega²
- **Jerk**: j = d³s/dt³ = (d³s/dtheta³) * omega³

### Pressure Angle / 压力角

- **Translating roller**: mu = arctan((ds/dtheta - e) / sqrt((rb + s)² - e²))
- **Oscillating roller**: mu = arctan(ds/dtheta / (L - rb))

### Dynamics / 动力学

- **Inertia force**: F_i = m * a
- **Natural frequency**: f_n = (1/2pi) * sqrt(k/m)
- **Dynamic amplification**: D = 1 / sqrt((1-r²)² + (2*zeta*r)²)
- **Hertz contact stress**: p_max = (F * E² / (pi² * L² * R_eq²))^(1/3)

---

## Learning Resources / 学习资源

1. **Cam Design Fundamentals** - Shigley's Mechanical Engineering Design
2. **Theory of Cam Profiles** - Norton, Design of Machinery
3. **Hertz Contact Theory** - Johnson, Contact Mechanics
4. **Dynamic Cam Systems** - Erdman, Sandor & Kota, Mechanism Design

---

## License / 许可证

MIT License - Educational use only.

---

## Contributing / 参与贡献

Contributions welcome! Please feel free to submit issues and pull requests.

欢迎贡献！欢迎提交问题和拉取请求。
