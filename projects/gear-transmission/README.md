# Gear Transmission System - Learning Project
# 齿轮传动系统 - 学习项目

---

## English

### Overview

A comprehensive learning project for understanding gear transmission mechanics,
including spur gear geometry, gear ratio calculations, torque and speed
transmission analysis, efficiency evaluation, and three types of gear trains
(simple, compound, and planetary).

### Learning Objectives

1. **Understand Gear Transmission Principles**
   - Learn about spur gear geometry and standard parameters
   - Understand the involute tooth profile
   - Master gear meshing conditions

2. **Master Gear Ratio Calculations**
   - Calculate single-stage and multi-stage gear ratios
   - Understand the role of idler gears
   - Design gear trains for specific ratios

3. **Transmission Analysis**
   - Calculate torque and speed through gear systems
   - Analyze power flow and losses
   - Understand efficiency factors

4. **Efficiency Evaluation**
   - Analyze mesh efficiency for different gear types
   - Calculate power loss breakdown
   - Compare efficiency across configurations

5. **Gear Train Types**
   - Simple gear trains with idlers
   - Compound gear trains for high reduction
   - Planetary (epicyclic) gear systems

### Project Structure

```
gear-transmission/
├── src/                          # Source modules
│   ├── __init__.py
│   ├── spur_gear.py              # Spur gear geometry
│   ├── gear_ratio.py             # Gear ratio calculations
│   ├── transmission.py           # Torque/speed transmission
│   ├── efficiency.py             # Efficiency analysis
│   ├── gear_train.py             # Simple, compound, planetary trains
│   └── contact_ratio.py          # Contact ratio calculations
├── examples/                     # Demo scripts
│   ├── 01_single_gear_pair.py    # Single gear pair simulation
│   ├── 02_compound_gear_train.py # Compound gear train
│   ├── 03_planetary_gear_system.py # Planetary gear system
│   └── 04_efficiency_comparison.py # Efficiency comparison
├── tests/                        # Unit tests
│   └── test_gear_transmission.py
├── requirements.txt
└── README.md
```

### How to Run Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run each example
python examples/01_single_gear_pair.py
python examples/02_compound_gear_train.py
python examples/03_planetary_gear_system.py
python examples/04_efficiency_comparison.py

# Run tests
pytest tests/ -v
```

### Gear Theory Background

#### Spur Gear Geometry

A spur gear is the simplest type of gear with straight teeth parallel to
the rotation axis. Key parameters:

| Parameter | Symbol | Formula | Description |
|-----------|--------|---------|-------------|
| Module | m | - | Tooth size standard |
| Teeth | z | - | Number of teeth |
| Pressure Angle | φ | - | Angle of force transmission (standard: 20°) |
| Pitch Diameter | d | d = m × z | Reference circle diameter |
| Base Circle Diameter | db | db = d × cos(φ) | Circle for involute generation |
| Addendum | ha | ha = m | Tooth height above pitch circle |
| Dedendum | hf | hf = 1.25m | Tooth depth below pitch circle |
| Outside Diameter | da | da = d + 2m | Tip circle diameter |
| Root Diameter | df | df = d - 2.5m | Root circle diameter |
| Circular Pitch | p | p = πm | Distance between teeth on pitch circle |

#### Gear Ratio

The gear ratio determines the relationship between input and output:

```
i = z_driven / z_driver = n_driver / n_driven = T_driven / T_driver
```

- **i > 1**: Reduction (speed decreases, torque increases)
- **i < 1**: Increase (speed increases, torque decreases)
- **i = 1**: Direct drive (same speed and torque)

#### Efficiency

Typical mesh efficiencies:
- Spur gears: 96-98% per mesh
- Helical gears: 97-99% per mesh
- Worm gears: 50-90% per mesh (depends on lead angle)
- Bevel gears: 95-98% per mesh

Total efficiency for N stages: η_total = η_mesh^N

#### Contact Ratio

Contact ratio (ε) is the average number of tooth pairs in contact:
- ε = Path of contact / Base pitch
- Minimum recommended: ε ≥ 1.2 for smooth operation
- Higher contact ratio = smoother operation, better load distribution

#### Planetary Gears

Planetary gear systems use a sun gear, planet gears, and a ring gear:

```
(n_s - n_c) / (n_r - n_c) = -z_r / z_s
```

Where n_s = sun speed, n_r = ring speed, n_c = carrier speed.

---

## 中文

### 项目概述

全面的齿轮传动力学学习项目，包含直齿轮几何、齿轮比计算、扭矩和速度
传递分析、效率评估以及三种齿轮系（简单齿轮系、复合齿轮系和行星齿轮系）。

### 学习目标

1. **理解齿轮传动原理**
   - 学习直齿轮几何和标准参数
   - 理解渐开线齿廓
   - 掌握齿轮啮合条件

2. **掌握齿轮比计算**
   - 计算单级和多级齿轮比
   - 理解惰轮的作用
   - 为特定传动比设计齿轮系

3. **传动分析**
   - 计算齿轮系统中的扭矩和速度
   - 分析功率流和损失
   - 理解效率因素

4. **效率评估**
   - 分析不同类型齿轮的啮合效率
   - 计算功率损失分解
   - 比较不同配置的效率

5. **齿轮系类型**
   - 带惰轮的简单齿轮系
   - 用于高减速比的复合齿轮系
   - 行星（周转）齿轮系统

### 项目结构

```
gear-transmission/
├── src/                          # 源模块
│   ├── __init__.py
│   ├── spur_gear.py              # 直齿轮几何
│   ├── gear_ratio.py             # 齿轮比计算
│   ├── transmission.py           # 扭矩/速度传递
│   ├── efficiency.py             # 效率分析
│   ├── gear_train.py             # 简单、复合、行星齿轮系
│   └── contact_ratio.py          # 重合度计算
├── examples/                     # 演示脚本
│   ├── 01_single_gear_pair.py    # 单级齿轮副仿真
│   ├── 02_compound_gear_train.py # 复合齿轮系
│   ├── 03_planetary_gear_system.py # 行星齿轮系统
│   └── 04_efficiency_comparison.py # 效率对比
├── tests/                        # 单元测试
│   └── test_gear_transmission.py
├── requirements.txt
└── README.md
```

### 如何运行示例

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/01_single_gear_pair.py
python examples/02_compound_gear_train.py
python examples/03_planetary_gear_system.py
python examples/04_efficiency_comparison.py

# 运行测试
pytest tests/ -v
```

### 齿轮理论基础

#### 直齿轮几何

直齿轮是最简单的齿轮类型，齿与旋转轴平行。关键参数：

| 参数 | 符号 | 公式 | 说明 |
|------|------|------|------|
| 模数 | m | - | 齿大小标准 |
| 齿数 | z | - | 齿的数量 |
| 压力角 | φ | - | 力传递角度（标准：20°） |
| 分度圆直径 | d | d = m × z | 参考圆直径 |
| 基圆直径 | db | db = d × cos(φ) | 渐开线生成圆 |
| 齿顶高 | ha | ha = m | 分度圆上方齿高 |
| 齿根高 | hf | hf = 1.25m | 分度圆下方齿深 |
| 齿顶圆直径 | da | da = d + 2m | 齿顶圆直径 |
| 齿根圆直径 | df | df = d - 2.5m | 齿根圆直径 |
| 齿距 | p | p = πm | 分度圆上齿间距 |

#### 齿轮比

齿轮比决定输入和输出的关系：

```
i = 从动轮齿数 / 主动轮齿数 = 主动轮转速 / 从动轮转速 = 从动轮扭矩 / 主动轮扭矩
```

- **i > 1**: 减速（转速降低，扭矩增大）
- **i < 1**: 增速（转速升高，扭矩降低）
- **i = 1**: 直连（相同转速和扭矩）

#### 效率

典型啮合效率：
- 直齿轮：每啮合 96-98%
- 斜齿轮：每啮合 97-99%
- 蜗轮蜗杆：每啮合 50-90%（取决于导程角）
- 锥齿轮：每啮合 95-98%

N 级总效率：η_total = η_mesh^N

#### 重合度

重合度 (ε) 是啮合中齿对平均数量：
- ε = 啮合路径 / 基圆齿距
- 最小推荐值：ε ≥ 1.2 以实现平稳运行
- 更高重合度 = 更平稳运行，更好的载荷分布

#### 行星齿轮

行星齿轮系统使用太阳轮、行星轮和齿圈：

```
(n_s - n_c) / (n_r - n_c) = -z_r / z_s
```

其中 n_s = 太阳轮转速，n_r = 齿圈转速，n_c = 行星架转速。
