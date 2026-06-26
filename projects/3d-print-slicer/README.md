# 3D Printing Slicer / 3D 打印切片器

> **Learning Project**: Implement core 3D printing slicer algorithms from scratch.
> **学习项目**: 从零实现核心 3D 打印切片算法。

---

## English

### Overview

A learning project that implements the core algorithms of a 3D printing slicer.
A slicer converts a 3D mesh model (STL) into G-code instructions that a 3D printer
can execute. This project covers each step of the slicing pipeline.

### Learning Objectives / 学习目标

- **Understand slicing theory**: How 3D meshes are converted to 2D cross-sections
- **Master toolpath planning**: Perimeter-first strategy, infill patterns, travel optimization
- **Learn G-code generation**: FDM printer instruction format, extrusion calculations
- **Explore support structures**: Overhang detection and support generation

### Core Pipeline / 核心流程

```
3D Model (STL) → Slicing → Layer Generation → Infill Patterns → Toolpath → G-code
```

### Architecture / 架构

```
src/
├── stl_parser.py          # Binary & ASCII STL file loader
├── mesh_slicer.py         # Triangle-plane intersection & layer extraction
├── layer_generator.py     # Layer geometry processing (perimeters, infill regions)
├── infill_generator.py    # Grid, honeycomb, gyroid, concentric patterns
├── toolpath_planner.py    # Perimeter-first toolpath generation
├── gcode_generator.py     # G-code output with extrusion calculations
└── support_generator.py   # Basic overhang detection & support generation
```

### Infill Patterns / 填充图案

| Pattern | Description | Strength | Speed |
|---------|-------------|----------|-------|
| Grid | Cross-hatch (90° lines) | Good X/Y | Medium |
| Honeycomb | Hexagonal cells | Best strength/weight | Medium |
| Gyroid | Continuous minimal surface | Isotropic | Slow |
| Concentric | Nested perimeter copies | Fastest | Fast |

### How to Run Examples / 如何运行示例

```bash
# Install dependencies
pip install -r requirements.txt

# 1. STL file loading and visualization
python examples/01_stl_loading.py

# 2. Slicing demo with layer visualization
python examples/02_slicing_demo.py

# 3. G-code generation demo
python examples/03_gcode_generation.py

# 4. Infill pattern comparison
python examples/04_infill_comparison.py

# Run tests
python tests/test_stl_parser.py
python tests/test_mesh_slicer.py
python tests/test_infill_generator.py
python tests/test_gcode_generator.py
```

### Slicing Theory Background / 切片理论基础

#### Triangle-Plane Intersection

When a horizontal slicing plane at height Z intersects a triangle, the result is:
- **No intersection**: All vertices on same side of plane
- **Line segment**: Two edges cross the plane (standard case)
- **Point**: One vertex touches the plane (degenerate)
- **Full triangle**: All three vertices on the plane (coplanar)

The intersection point on an edge is found by linear interpolation:

```
P = V1 + (Z - V1.z) / (V2.z - V1.z) * (V2 - V1)
```

#### Layer Processing

Each layer's segments are processed to:
1. **Extract perimeters**: Connect segments into closed loops
2. **Generate infill**: Fill the interior with patterned paths
3. **Plan toolpath**: Order segments to minimize travel distance

#### Extrusion Calculation

The amount of filament to extrude is calculated from the cross-sectional area:

```
Volume = MoveLength × NozzleWidth × LayerHeight
ExtrusionLength = Volume / (FilamentDiameter² × π / 4)
```

For standard 1.75mm filament and 0.4mm nozzle:
- Cross-section area ≈ 0.16 mm²
- Filament area ≈ 2.405 mm²
- Ratio ≈ 0.0665 (extrusion ≈ 6.65% of move length)

---

## 中文

### 项目概述

本项目从零实现 3D 打印切片器的核心算法。切片器将 3D 网格模型（STL 格式）
转换为 3D 打印机可以执行的 G-code 指令。项目覆盖切片管道的每个步骤。

### 学习目标

- **理解切片原理**: 3D 网格如何转换为 2D 截面
- **掌握路径规划**: 先轮廓后填充策略、填充图案、路径优化
- **学会 G-code 生成**: FDM 打印机指令格式、挤出量计算
- **探索支撑结构**: 悬垂检测和支撑生成

### 核心流程

```
3D 模型 (STL) → 切片 → 层生成 → 填充图案 → 路径规划 → G-code
```

### 运行示例

```bash
# 安装依赖
pip install -r requirements.txt

# 1. STL 文件加载和可视化
python examples/01_stl_loading.py

# 2. 切片演示（含层可视化）
python examples/02_slicing_demo.py

# 3. G-code 生成演示
python examples/03_gcode_generation.py

# 4. 填充图案对比
python examples/04_infill_comparison.py

# 运行测试
python tests/test_stl_parser.py
python tests/test_mesh_slicer.py
python tests/test_infill_generator.py
python tests/test_gcode_generator.py
```

### 切片理论基础

#### 三角形-平面相交

当高度为 Z 的水平切片平面与三角形相交时，结果为：
- **无相交**: 所有顶点在平面同侧
- **线段**: 两条边穿过平面（标准情况）
- **点**: 一个顶点接触平面（退化情况）
- **完整三角形**: 三个顶点都在平面上（共面）

边上的交点通过线性插值计算：

```
P = V1 + (Z - V1.z) / (V2.z - V1.z) * (V2 - V1)
```

#### 挤出量计算

挤出 filament 量通过横截面积计算：

```
体积 = 移动长度 × 喷嘴宽度 × 层高
挤出长度 = 体积 / (线径² × π / 4)
```

对于标准 1.75mm 线径和 0.4mm 喷嘴：
- 横截面积 ≈ 0.16 mm²
- 线径面积 ≈ 2.405 mm²
- 比率 ≈ 0.0665（挤出量 ≈ 移动长度的 6.65%）

---

## Project Structure / 项目结构

```
3d-print-slicer/
├── src/                          # Source modules
│   ├── stl_parser.py            # STL 文件解析器
│   ├── mesh_slicer.py           # 网格切片算法
│   ├── layer_generator.py       # 层生成
│   ├── infill_generator.py      # 填充图案生成
│   ├── toolpath_planner.py      # 路径规划
│   ├── gcode_generator.py       # G-code 生成
│   └── support_generator.py     # 支撑结构生成
├── examples/                     # Demo scripts
│   ├── 01_stl_loading.py        # STL 加载演示
│   ├── 02_slicing_demo.py       # 切片演示
│   ├── 03_gcode_generation.py   # G-code 生成演示
│   └── 04_infill_comparison.py  # 填充图案对比
├── tests/                        # Unit tests
│   ├── test_stl_parser.py
│   ├── test_mesh_slicer.py
│   ├── test_infill_generator.py
│   └── test_gcode_generator.py
├── README.md                     # This file
└── requirements.txt              # Dependencies
```

## License / 许可证

MIT
