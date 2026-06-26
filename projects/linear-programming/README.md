"""
线性规划求解器 (Linear Programming Solver)

实现单纯形法及其变体，用于求解线性规划问题。

## 项目简介

本项目是一个教学用的线性规划求解器，实现了单纯形法 (Simplex Method)
及其多种变体，帮助学习者理解线性优化的核心算法。

## 学习目标

1. **理解线性规划原理**
   - 线性规划的标准形式与一般形式
   - 可行域、基本解、基本可行解的概念
   - 最优解的几何意义

2. **掌握单纯形法**
   - 单纯形表的构造与解读
   - 检验数 (Reduced Cost) 的含义
   - 进基变量和出基变量的选择规则
   - 最小比值测试 (Minimum Ratio Test)
   - 主元运算 (Pivot Operation)

3. **学会约束处理**
   - 松弛变量 (Slack Variables)
   - 剩余变量 (Surplus Variables)
   - 人工变量 (Artificial Variables)
   - 两阶段法 (Two-Phase Method)
   - 大M法 (Big-M Method)

4. **深入理解对偶理论**
   - 原问题与对偶问题的关系
   - 强对偶定理
   - 互补松弛条件
   - 影子价格 (Shadow Price)

5. **掌握灵敏度分析**
   - 目标系数变化范围
   - 约束右侧变化范围
   - 100% 规则

## 项目结构

```
linear-programming/
├── src/                          # 源代码
│   ├── __init__.py              # 包初始化
│   ├── problem.py               # 问题建模
│   ├── standard_form.py         # 标准形转换
│   ├── simplex.py               # 单纯形算法
│   ├── big_m.py                 # 大M法
│   ├── dual.py                  # 对偶问题求解
│   ├── sensitivity.py           # 灵敏度分析
│   └── analysis.py              # 解分析 (无界解/多重最优解)
├── examples/                     # 示例脚本
│   ├── 01_production_planning.py # 生产计划问题
│   ├── 02_diet_problem.py       # 饮食问题
│   ├── 03_transportation.py     # 运输问题
│   ├── 04_graphical_method.py   # 图解法可视化
│   └── 05_sensitivity_analysis.py # 灵敏度分析演示
├── tests/                        # 测试
│   └── test_linear_programming.py
├── requirements.txt              # 依赖
└── README.md                     # 项目文档
```

## 安装

```bash
cd linear-programming
pip install -r requirements.txt
```

## 运行示例

```bash
# 示例 1: 生产计划问题
python examples/01_production_planning.py

# 示例 2: 饮食问题
python examples/02_diet_problem.py

# 示例 3: 运输问题
python examples/03_transportation.py

# 示例 4: 图解法可视化 (需要 matplotlib)
python examples/04_graphical_method.py

# 示例 5: 灵敏度分析
python examples/05_sensitivity_analysis.py
```

## 运行测试

```bash
python -m pytest tests/
# 或
python -m unittest discover tests/
```

## 单纯形法详解

### 算法核心思想

单纯形法是一种迭代算法，从可行域的一个顶点移动到相邻顶点，
每次移动都使目标函数值改善，直到无法再改进为止。

### 步骤分解

**步骤 1: 问题建模**
将实际问题转化为线性规划数学模型。

例如，生产计划问题:
```
最大化 z = 3x1 + 2x2
约束:
    x1 + x2 <= 4     (机器时间)
    x1 <= 3          (产能1)
    x2 <= 2          (产能2)
    x1, x2 >= 0
```

**步骤 2: 标准形转换**
添加松弛变量，将不等式约束转为等式:
```
x1 + x2 + s1 = 4
x1 + s2 = 3
x2 + s3 = 2
```

**步骤 3: 构造初始单纯形表**

```
     x1   x2   s1   s2   s3   RHS
s1 |  1    1    1    0    0    4
s2 |  1    0    0    1    0    3
s3 |  0    1    0    0    1    2
z | -3   -2    0    0    0    0   (检验数)
```

**步骤 4: 迭代**

**第 1 次迭代:**
- 进基变量: x1 (检验数 -3 最负)
- 出基变量: s2 (最小比值: 3/1 = 3)
- 主元: 第 2 行 x1 列 = 1

**第 2 次迭代:**
- 进基变量: x2 (检验数仍为负)
- 出基变量: s1 (最小比值测试)
- 更新单纯形表

**步骤 5: 最优解**

当所有检验数 >= 0 时，达到最优:
```
x1 = 2, x2 = 2, z = 10
```

### 终止条件

1. **最优解**: 所有检验数 >= 0 (最小化问题)
2. **无界解**: 存在检验数 < 0 的变量，其列所有系数 <= 0
3. **多重最优解**: 最优表中存在非基变量检验数 = 0

## 算法对比

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 两阶段法 | 无初始可行基 | 数值稳定 | 需要求解两个问题 |
| 大M法 | 人工变量较少 | 一步求解 | M 的选择影响数值稳定性 |

## 数学符号说明

| 符号 | 含义 |
|------|------|
| x | 决策变量向量 |
| c | 目标函数系数向量 |
| A | 约束矩阵 |
| b | 约束右侧向量 |
| z | 目标函数值 |
| y | 对偶变量向量 |
| B | 基矩阵 |
| c_B | 基变量对应的目标系数 |

## License

MIT
