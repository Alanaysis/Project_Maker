# Constraint Solver - CAD Geometric Constraint Solver Learning Project

## 约束求解器 - CAD 几何约束求解器学习项目

---

## English

### Description

A learning project implementing a 2D CAD geometric constraint solver from scratch.
The solver takes geometric entities (points, lines, circles) and constraints
(distance, angle, parallel, perpendicular, etc.) as input, and computes the
positions of all entities that satisfy all constraints simultaneously.

**Core loop**: Constraint Definition → Equation Building → Numerical Solving → Geometry Update

### Learning Objectives

- Understand the principles of geometric constraint solving
- Master numerical methods for solving non-linear systems (Newton-Raphson)
- Learn constraint propagation and dependency analysis
- Understand over-constrained and under-constrained system detection

### Supported Constraint Types

| Constraint | Description | Equation |
|------------|-------------|----------|
| **Distance** | Distance between two points | ‖P₁ - P₂‖ - d = 0 |
| **Angle** | Angle between two rays | θ₁₂ - θ = 0 |
| **Parallel** | Two lines are parallel | v₁ × v₂ = 0 |
| **Perpendicular** | Two lines are perpendicular | v₁ · v₂ = 0 |
| **Collinear** | Three+ points on same line | (P₂-P₁) × (P₃-P₁) = 0 |
| **Concentric** | Two circles share center | C₁ - C₂ = 0 |
| **Tangent** | Circle tangent to line/circle | dist = r |
| **Equal Radius** | Two circles have equal radius | r₁ - r₂ = 0 |
| **Midpoint** | Point is midpoint of segment | P - (P₁+P₂)/2 = 0 |
| **Horizontal** | Line is horizontal | y₁ - y₂ = 0 |
| **Vertical** | Line is vertical | x₁ - x₂ = 0 |

### Numerical Methods Background

#### Newton-Raphson Method

The core solver uses the Newton-Raphson method to solve F(x) = 0:

```
x_{k+1} = x_k - J(x_k)⁻¹ · F(x_k)
```

where:
- **F(x)**: Vector of constraint residuals (should be zero when satisfied)
- **J(x)**: Jacobian matrix (partial derivatives dF/dx)
- **x**: Vector of unknown point coordinates

#### Key Implementation Details

1. **Sparse Jacobian**: Uses scipy.sparse for efficient matrix operations
2. **Finite Differences**: Numerical Jacobian computation via perturbation
3. **Damping**: Step size limiting prevents divergence
4. **Convergence**: Residual norm below tolerance indicates solution

#### Constraint Propagation

Before numerical solving, the engine propagates known values through the
constraint network to identify directly solvable constraints, reducing
the size of the numerical system.

### How to Run Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run simple sketch solver (rectangles, triangles)
python examples/simple_sketch_solver.py

# Run geometric construction examples
python examples/geometric_construction.py

# Run visualization (requires matplotlib)
python examples/interactive_solver.py

# Run text-based visualization
python examples/visualization.py

# Run tests
python -m pytest tests/ -v
```

### Project Structure

```
constraint-solver/
├── src/
│   ├── __init__.py          # Package init
│   ├── entities.py          # Point, Line, Circle classes
│   ├── constraints.py       # All constraint types
│   ├── constraint_graph.py  # Graph builder & propagation
│   └── solver.py            # Newton-Raphson solver
├── examples/
│   ├── simple_sketch_solver.py    # Rectangle & triangle examples
│   ├── geometric_construction.py  # Complex geometric constructions
│   ├── interactive_solver.py      # Matplotlib visualization
│   └── visualization.py           # Text-based ASCII visualization
├── tests/
│   ├── test_constraints.py  # Constraint unit tests
│   └── test_solver.py       # Solver integration tests
├── requirements.txt
└── README.md
```

---

## 中文

### 项目描述

从零实现一个 2D CAD 几何约束求解器。求解器接收几何实体（点、线、圆）和约束
（距离、角度、平行、垂直等）作为输入，计算满足所有约束的几何实体位置。

**核心循环**：约束定义 → 方程构建 → 数值求解 → 几何更新

### 学习目标

- 理解几何约束求解原理
- 掌握非线性方程组数值求解方法（牛顿-拉夫森法）
- 学习约束传播和依赖分析
- 理解过约束和欠约束系统检测

### 支持的约束类型

| 约束类型 | 描述 | 方程 |
|----------|------|------|
| **距离** | 两点间距离 | ‖P₁ - P₂‖ - d = 0 |
| **角度** | 两射线间夹角 | θ₁₂ - θ = 0 |
| **平行** | 两线平行 | v₁ × v₂ = 0 |
| **垂直** | 两线垂直 | v₁ · v₂ = 0 |
| **共线** | 三点及以上共线 | (P₂-P₁) × (P₃-P₁) = 0 |
| **同心** | 两圆同心 | C₁ - C₂ = 0 |
| **相切** | 圆与线/圆相切 | dist = r |
| **等半径** | 两圆半径相等 | r₁ - r₂ = 0 |
| **中点** | 点为线段中点 | P - (P₁+P₂)/2 = 0 |
| **水平** | 线为水平 | y₁ - y₂ = 0 |
| **垂直** | 线为垂直 | x₁ - x₂ = 0 |

### 数值方法背景

#### 牛顿-拉夫森法

核心求解器使用牛顿-拉夫森法求解 F(x) = 0：

```
x_{k+1} = x_k - J(x_k)⁻¹ · F(x_k)
```

其中：
- **F(x)**: 约束残差向量（满足时为零）
- **J(x)**: Jacobian 矩阵（dF/dx 偏导数）
- **x**: 未知点坐标向量

#### 实现要点

1. **稀疏 Jacobian**: 使用 scipy.sparse 进行高效矩阵运算
2. **有限差分**: 通过扰动数值计算 Jacobian
3. **阻尼**: 步长限制防止发散
4. **收敛**: 残差范数低于容差即表示收敛

#### 约束传播

在数值求解之前，引擎通过约束网络传播已知值，识别可直接求解的约束，
减少数值系统的大小。

### 运行示例

```bash
# 安装依赖
pip install -r requirements.txt

# 运行简单草图求解器（矩形、三角形）
python examples/simple_sketch_solver.py

# 运行几何构造示例
python examples/geometric_construction.py

# 运行可视化（需要 matplotlib）
python examples/interactive_solver.py

# 运行文本可视化
python examples/visualization.py

# 运行测试
python -m pytest tests/ -v
```

---

## License

MIT License
