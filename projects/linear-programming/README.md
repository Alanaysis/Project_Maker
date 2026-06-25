# 线性规划 (Linear Programming)

基于 NumPy 实现的线性规划求解库，支持单纯形法、对偶理论、敏感性分析及经典应用问题求解。

## 项目概述

线性规划是运筹学中最基础、应用最广泛的优化方法。本项目从零实现完整的线性规划求解框架，涵盖：

1. **单纯形法** - 三种变体：标准形式、大M法、两阶段法
2. **对偶理论** - 对偶问题构造、强/弱对偶定理、互补松弛条件
3. **对偶单纯形法** - 适用于右端项变化后的重新优化
4. **敏感性分析** - 目标函数系数和右端项的变化范围
5. **实际应用** - 生产计划、运输问题、指派问题

### 数学基础

标准形式：
```
max  c^T x
s.t. Ax <= b
      x >= 0
```

对偶形式：
```
min  b^T y
s.t. A^T y >= c
      y >= 0
```

强对偶定理：若原问题有最优解 x*，则对偶也有最优解 y*，且 c^T x* = b^T y*。

## 项目结构

```
linear-programming/
├── src/                        # 源代码
│   ├── __init__.py
│   ├── linear_program.py      # LP 问题表示与标准形式转换
│   ├── simplex.py             # 单纯形法（标准、大M、两阶段）
│   ├── duality.py             # 对偶理论与对偶单纯形法
│   ├── sensitivity.py         # 敏感性分析
│   └── applications.py        # 实际应用（生产、运输、指派）
├── tests/                      # 测试文件
│   ├── test_simplex.py        # 单纯形法测试
│   ├── test_duality.py        # 对偶理论测试
│   ├── test_sensitivity.py    # 敏感性分析测试
│   └── test_applications.py   # 应用问题测试
├── examples/                   # 使用示例
│   └── basic_usage.py         # 完整使用示例
├── docs/                       # 文档
│   ├── 01_RESEARCH.md         # 研究文档
│   ├── 02_REQUIREMENTS.md     # 需求文档
│   ├── 03_DESIGN.md           # 设计文档
│   ├── 04_TESTING.md          # 测试文档
│   └── 05_DEVELOPMENT.md      # 开发文档
├── requirements.txt
└── setup.py
```

## 快速开始

### 安装

```bash
cd projects/linear-programming
pip install -e .
```

### 基本使用

```python
from src.linear_program import LinearProgram, ConstraintType, ObjectiveType
from src.simplex import SimplexSolver

# 问题: max 3x1 + 5x2, s.t. x1<=4, 2x2<=12, 3x1+5x2<=25
lp = LinearProgram(ObjectiveType.MAX)
lp.set_objective([3, 5])
lp.add_constraint([1, 0], 4, ConstraintType.LE)
lp.add_constraint([0, 2], 12, ConstraintType.LE)
lp.add_constraint([3, 5], 25, ConstraintType.LE)

solver = SimplexSolver(method="standard")
result = solver.solve(lp)
print(result)
# LP Result: optimal
#   Optimal Value: 33.000000
#   Solution: [2. 5.]
```

### 大M法处理混合约束

```python
lp = LinearProgram(ObjectiveType.MAX)
lp.set_objective([5, 4])
lp.add_constraint([6, 4], 24, ConstraintType.LE)
lp.add_constraint([1, 2], 6, ConstraintType.GE)  # >= 约束

solver = SimplexSolver(method="big_m", M=1e6)
result = solver.solve(lp)
```

### 对偶问题

```python
from src.duality import DualProblem

dual = DualProblem.construct_dual(primal_lp)
print(dual)  # 打印对偶问题

# 验证强对偶定理
is_strong = DualProblem.verify_strong_duality(primal_result, dual_result)
```

### 敏感性分析

```python
from src.sensitivity import SensitivityAnalyzer

analyzer = SensitivityAnalyzer()
report = analyzer.analyze(lp, result)
print(report)
# === Sensitivity Report ===
# Objective Coefficient Ranges: ...
# Right-Hand Side Ranges: ...
# Shadow Prices: ...
```

### 生产计划

```python
from src.applications import ProductionPlanner

planner = ProductionPlanner()
planner.add_resource("工时", 120)
planner.add_resource("原料", 80)
planner.add_product("A", profit=20, cost=5, usage=[4, 1], max_demand=20)
planner.add_product("B", profit=30, cost=8, usage=[2, 3], max_demand=15)

result = planner.optimize()
print(planner.report(result))
```

### 运输问题

```python
from src.applications import TransportationSolver

solver = TransportationSolver()
cost = [[2, 3, 1], [4, 1, 5], [3, 2, 4]]
supply = [30, 40, 20]
demand = [25, 35, 30]

result = solver.solve(cost, supply, demand)
```

### 指派问题

```python
from src.applications import AssignmentSolver

solver = AssignmentSolver()
cost = [[9, 2, 7], [6, 4, 3], [5, 8, 1]]
result = solver.solve(cost)
```

## 核心模块

### 1. 单纯形法 (simplex.py)

| 方法 | 适用场景 | 复杂度 |
|------|----------|--------|
| 标准形式 | 仅 <= 约束, b >= 0 | O(n^3) |
| 大M法 | 任意约束类型 | O(n^3) |
| 两阶段法 | 任意约束类型 | O(n^3) |

### 2. 对偶理论 (duality.py)

- **对偶问题构造** - 自动将原问题转为对偶问题
- **强对偶验证** - 验证 c^T x* = b^T y*
- **互补松弛检查** - y_i*(b_i - A_i x*) = 0
- **对偶单纯形法** - 保持对偶可行，恢复原始可行

### 3. 敏感性分析 (sensitivity.py)

- **目标函数系数范围** - c_j 的允许变化范围
- **右端项范围** - b_i 的允许变化范围
- **影子价格** - 资源的边际价值
- **约简成本** - 非基变量进入基的门槛

### 4. 实际应用 (applications.py)

- **生产计划** - 多产品、多资源的最优生产安排
- **运输问题** - 供需平衡的最小成本运输
- **指派问题** - 最优任务分配 (含匈牙利算法)

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_simplex.py -v
pytest tests/test_duality.py -v
pytest tests/test_sensitivity.py -v
pytest tests/test_applications.py -v
```

## 依赖

- Python >= 3.8
- NumPy >= 1.20.0

## 学习价值

1. **数学基础** - 线性代数、凸优化、对偶理论
2. **算法设计** - 迭代算法、枢轴运算、基变换
3. **建模能力** - 将实际问题转化为数学模型
4. **数值计算** - 浮点精度、退化处理、循环避免
