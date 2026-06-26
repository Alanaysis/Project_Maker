# 遗传算法优化框架 / Genetic Algorithm Optimization Framework

## 简介 / Overview

一个教育性的遗传算法（GA）优化框架实现，涵盖进化算法的核心组件。
旨在帮助学习者理解遗传算法的原理和实现细节。

An educational Genetic Algorithm (GA) optimization framework implementation covering the core components of evolutionary algorithms. Designed to help learners understand the principles and implementation details of genetic algorithms.

---

## 学习目标 / Learning Objectives

### 中文
- 理解进化算法的基本原理和生物启发机制
- 掌握选择、交叉、变异三种遗传算子的实现
- 学会针对不同问题设计适应度函数
- 理解种群多样性和收敛检测的重要性
- 掌握实数编码和排列编码的应用场景

### English
- Understand the basic principles of evolutionary algorithms and biological inspiration
- Master the implementation of selection, crossover, and mutation operators
- Learn to design fitness functions for different problems
- Understand the importance of population diversity and convergence detection
- Master the application scenarios of real-valued and permutation encoding

---

## 项目结构 / Project Structure

```
genetic-algorithm/
├── src/                          # 源代码
│   ├── __init__.py               # 包初始化
│   ├── individual.py             # 个体和种群管理
│   ├── selection.py              # 选择方法（锦标赛、轮盘赌、排名、精英）
│   ├── crossover.py              # 交叉算子（单点、多点、均匀、算术、顺序）
│   ├── mutation.py               # 变异算子（位翻转、交换、逆序、高斯）
│   ├── convergence.py            # 收敛检测
│   ├── config.py                 # 参数配置
│   ├── core.py                   # 核心引擎（世代/稳态模式）
│   └── suites.py                 # 标准测试函数库
├── examples/                     # 演示脚本
│   ├── function_optimization.py  # 函数优化演示
│   ├── tsp_solver.py             # TSP 旅行商问题
│   ├── knapsack_problem.py       # 背包问题
│   └── visualization.py          # 可视化演示
├── tests/                        # 单元测试
│   └── test_genetic_algorithm.py
├── requirements.txt              # 依赖
└── README.md                     # 本文件
```

---

## 遗传算法理论背景 / GA Theory Background

### 什么是遗传算法？

遗传算法是一种受自然进化启发的优化算法。它模拟生物进化过程中的"适者生存"机制：

> **Genetic Algorithm** is an optimization algorithm inspired by natural evolution. It simulates the "survival of the fittest" mechanism in biological evolution:

1. **初始化**：随机生成一组解（种群）
2. **评估**：用适应度函数评价每个解的质量
3. **选择**：优质个体更有可能被选中繁殖
4. **交叉**：两个父代交换基因，产生子代
5. **变异**：以低概率随机改变基因，维持多样性
6. **迭代**：重复步骤 2-5，直到满足终止条件

### 核心组件 / Core Components

#### 1. 编码方案 / Encoding

| 编码类型 | 适用问题 | 示例 |
|---------|---------|------|
| 二进制编码 | 离散优化 | [1, 0, 1, 1, 0] |
| 实数编码 | 连续优化 | [1.5, -2.3, 0.7] |
| 排列编码 | 排序/路径问题 | [3, 1, 4, 0, 2] |

#### 2. 选择方法 / Selection Methods

- **锦标赛选择 (Tournament Selection)**：随机选 k 个个体，选最优者
- **轮盘赌选择 (Roulette Wheel)**：按适应度比例选择
- **排名选择 (Rank-Based)**：按排名分配选择概率
- **精英保留 (Elitism)**：直接保留最优个体

#### 3. 交叉算子 / Crossover Operators

- **单点交叉**：随机选一个交叉点交换基因
- **多点交叉**：选多个交叉点交替交换
- **均匀交叉**：每个基因位独立决定是否交换
- **算术交叉**：实数编码的线性组合
- **顺序交叉 (OX)**：TSP 等排列问题的专用交叉

#### 4. 变异算子 / Mutation Operators

- **位翻转**：二进制编码的基因翻转
- **交换变异**：交换排列中的两个位置
- **逆序变异**：反转排列中的一段子序列
- **高斯变异**：实数编码的高斯扰动
- **边界变异**：将基因变异到边界值

### 关键参数 / Key Parameters

| 参数 | 典型范围 | 说明 |
|------|---------|------|
| 种群大小 | 50-200 | 种群个体数量 |
| 交叉概率 | 0.6-0.9 | 执行交叉的概率 |
| 变异概率 | 0.01-0.1 | 每个基因变异的概率 |
| 锦标赛大小 | 2-5 | 锦标赛选择的个体数 |
| 精英数量 | 1-5 | 保留的精英个体数 |
| 最大代数 | 100-1000 | 进化终止条件 |

---

## 快速开始 / Quick Start

### 安装依赖 / Install Dependencies

```bash
pip install -r requirements.txt
```

### 运行示例 / Run Examples

#### 1. 函数优化 / Function Optimization

```bash
python examples/function_optimization.py
```

优化 Sphere、Rosenbrock、Rastrigin、Ackley 四个经典测试函数。

#### 2. TSP 旅行商问题 / TSP

```bash
python examples/tsp_solver.py
```

求解 20 和 50 城市 TSP 问题。

#### 3. 背包问题 / Knapsack Problem

```bash
python examples/knapsack_problem.py
```

求解 0/1 背包问题。

#### 4. 可视化 / Visualization

```bash
python examples/visualization.py
```

生成适应度进化曲线、选择方法对比图等。

### 运行测试 / Run Tests

```bash
python -m pytest tests/ -v
```

---

## API 使用示例 / API Usage Example

### 基本用法 / Basic Usage

```python
from src.core import GeneticAlgorithm
from src.individual import Individual, Population
import random

# 定义适应度函数（最大化）
def fitness(gene):
    return sum(g ** 2 for g in gene)  # Sphere 函数

# 创建初始种群
def init_population():
    individuals = []
    for _ in range(100):
        gene = [random.uniform(-5.12, 5.12) for _ in range(10)]
        individuals.append(Individual(gene=gene, fitness=0.0))
    return Population(size=100, individuals=individuals)

# 创建并运行遗传算法
ga = GeneticAlgorithm(
    population_size=100,
    fitness_func=fitness,
    max_generations=300,
    selection_method='tournament',
    tournament_size=3,
    crossover_operator='arithmetic',
    mutation_operator='gaussian',
    crossover_rate=0.8,
    mutation_rate=0.05,
    elite_count=2,
    seed=42,
    verbose=True,
)

result = ga.optimize(fitness_func=fitness, initial_population=init_population())

print(f"最佳适应度: {result.best_fitness}")
print(f"最佳基因: {result.best_individual.gene}")
```

### 比较不同选择方法 / Compare Selection Methods

```python
from src.selection import get_selection_method

# 创建不同的选择方法
tournament = get_selection_method('tournament', tournament_size=3)
roulette = get_selection_method('roulette')
rank = get_selection_method('rank')
elitism = get_selection_method('elitism', elite_count=5)
```

### 比较不同交叉算子 / Compare Crossover Operators

```python
from src.crossover import get_crossover_operator

single_point = get_crossover_operator('single_point')
arithmetic = get_crossover_operator('arithmetic')
order = get_crossover_operator('order')
```

---

## 测试函数库 / Test Function Suite

框架内置了多个经典优化测试函数：

| 函数 | 维度 | 特点 | 全局最优 |
|------|------|------|---------|
| Sphere | n | 单峰、可分离 | [0,...,0], f=0 |
| Rosenbrock | n | 峡谷地形 | [1,...,1], f=0 |
| Rastrigin | n | 多峰 | [0,...,0], f=0 |
| Ackley | n | 多峰、平坦最优区 | [0,...,0], f=0 |
| Griewank | n | 多峰、大搜索空间 | [0,...,0], f=0 |

---

## 进化模式 / Evolution Modes

### 世代模式 (Generational Mode)

- 每代完全替换旧种群
- 适合并行化
- 探索性强

### 稳态模式 (Steady-State Mode)

- 每次只替换少量个体
- 种群变化更平滑
- 探索更充分

---

## 收敛检测 / Convergence Detection

| 检测器 | 原理 | 适用场景 |
|--------|------|---------|
| Diversity | 种群多样性低于阈值 | 通用 |
| Fitness Gain | 适应度提升低于阈值 | 通用 |
| Combined | 结合以上两种 | 鲁棒性要求高 |
| Generation Limit | 达到最大代数 | 基本终止条件 |

---

## 常见问题 / FAQ

### Q: 如何选择交叉/变异算子？

**A**: 根据编码类型选择：
- 二进制编码 → 单点交叉 + 位翻转变异
- 实数编码 → 算术交叉 + 高斯变异
- 排列编码 → 顺序交叉 + 逆序变异

### Q: 种群大小怎么设置？

**A**: 根据问题维度：
- 低维问题（<10）：50-100
- 中维问题（10-50）：100-200
- 高维问题（>50）：200-500

### Q: 如何防止早熟收敛？

**A**:
1. 增大种群大小
2. 提高变异率
3. 使用排名选择代替轮盘赌
4. 使用组合收敛检测器
5. 增加精英保留数量

---

## 许可证 / License

MIT License
