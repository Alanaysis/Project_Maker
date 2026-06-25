# 遗传算法 (Genetic Algorithm)

## 项目概述

实现一个完整的遗传算法优化框架，支持多种编码方式、选择算子、交叉算子和变异算子。框架包含函数优化、TSP 旅行商问题、背包问题等经典应用场景，并支持多目标优化（NSGA-II）和自适应参数调整。

## 学习目标

- 理解进化算法的基本原理和生物学背景
- 掌握遗传算法的核心算子：选择、交叉、变异
- 学会设计有效的适应度函数
- 实践遗传算法在组合优化和连续优化问题中的应用
- 了解多目标优化和自适应策略

## 技术栈

- **主语言**: Python 3.8+
- **可视化**: matplotlib
- **依赖**: numpy, matplotlib, pytest

## 项目结构

```
genetic-algorithm/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md           # 学习笔记
├── requirements.txt            # 依赖
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-ARCHITECTURE.md      # 架构设计
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试策略
│   └── 05-DEVELOPMENT.md       # 开发计划
├── src/                         # 源代码
│   ├── __init__.py
│   ├── core/                   # 核心算法
│   │   ├── __init__.py
│   │   ├── individual.py       # 个体表示
│   │   ├── population.py       # 种群管理
│   │   ├── ga_engine.py        # GA 引擎
│   │   └── multi_objective.py  # NSGA-II 多目标优化
│   ├── operators/              # 遗传算子
│   │   ├── __init__.py
│   │   ├── selection.py        # 选择算子
│   │   ├── crossover.py        # 交叉算子
│   │   └── mutation.py         # 变异算子
│   └── problems/               # 优化问题
│       ├── __init__.py
│       ├── base.py             # 基类
│       ├── tsp.py              # TSP 问题
│       ├── function_opt.py     # 函数优化问题
│       └── knapsack.py         # 背包问题
├── tests/                       # 测试文件
│   ├── __init__.py
│   ├── test_individual.py
│   ├── test_population.py
│   ├── test_operators.py
│   ├── test_new_operators.py   # 新算子测试
│   ├── test_tsp.py
│   ├── test_function_opt.py    # 函数优化测试
│   ├── test_knapsack.py        # 背包问题测试
│   ├── test_multi_objective.py # 多目标优化测试
│   └── test_integration.py
└── examples/                    # 示例代码
    ├── basic_ga.py             # 基础示例
    ├── tsp_solver.py           # TSP 求解
    ├── knapsack_solver.py      # 背包问题求解
    ├── multi_objective_example.py # 多目标优化示例
    ├── adaptive_ga.py          # 自适应 GA 示例
    └── visualization.py        # 可视化
```

## 核心循环

```
初始种群 → 适应度评估 → 精英保留 → 选择 → 交叉 → 变异 → 新种群
```

## 快速开始

### 1. 安装依赖

```bash
pip install numpy matplotlib pytest
```

### 2. 运行基础示例

```bash
python examples/basic_ga.py
```

### 3. 求解 TSP 问题

```bash
python examples/tsp_solver.py
```

### 4. 求解背包问题

```bash
python examples/knapsack_solver.py
```

### 5. 多目标优化

```bash
python examples/multi_objective_example.py
```

### 6. 运行测试

```bash
pytest tests/ -v
```

## 算法特性

### 编码方式
- **二进制编码**: 适用于离散问题
- **实数编码**: 适用于连续优化
- **排列编码**: 适用于 TSP 等组合问题

### 选择算子
- **轮盘赌选择 (Roulette Wheel)**: 适应度越高，被选中概率越大
- **锦标赛选择 (Tournament)**: 随机选择 k 个个体，取最优
- **精英保留 (Elitism)**: 保留适应度最高的 n 个个体

### 交叉算子
- **单点交叉 (Single Point)**: 随机选择一个切点，交换后半部分
- **两点交叉 (Two Point)**: 随机选择两个切点，交换中间部分
- **均匀交叉 (Uniform)**: 每个基因以相同概率从两个父代中随机选择
- **算术交叉 (Arithmetic)**: 对实数编码的父代进行线性组合
- **顺序交叉 (OX)**: 保持城市访问的相对顺序，专用于 TSP

### 变异算子
- **位翻转变异 (Bit Flip)**: 随机翻转染色体上的位，适用于二进制编码
- **交换变异 (Swap)**: 随机交换两个位置的值，适用于排列编码
- **逆序变异 (Inversion)**: 随机选择一段子序列并反转，适用于排列编码
- **高斯变异 (Gaussian)**: 对实数编码的基因添加高斯噪声
- **自适应变异 (Adaptive)**: 根据种群适应度自动调整变异率

### 高级特性
- **精英保留策略**: 确保最优个体不丢失
- **自适应变异**: 根据进化状态动态调整变异率
- **多目标优化 (NSGA-II)**: 非支配排序和拥挤度距离选择

## 实际应用

### 1. 函数优化
- Sphere 函数（单模态）
- Rastrigin 函数（多模态）
- Rosenbrock 函数（香蕉函数）
- Ackley 函数
- Griewank 函数

### 2. TSP 旅行商问题
- 给定一组城市，找到访问每个城市一次并返回起点的最短路径
- 使用排列编码和顺序交叉 (OX)

### 3. 背包问题
- 0/1 背包问题：在容量限制下最大化总价值
- 多重背包问题：将物品分配到多个背包中

### 4. 多目标优化
- ZDT1/ZDT2 测试问题
- Pareto 最优解集
- NSGA-II 算法

## 参考资源

- [遗传算法 Wikipedia](https://zh.wikipedia.org/wiki/遗传算法)
- [DEAP 框架文档](https://deap.readthedocs.io/)
- [NSGA-II 论文](https://ieeexplore.ieee.org/document/996017)
- 书籍: 《Introduction to Evolutionary Computing》
- 书籍: 《Genetic Algorithms in Search, Optimization, and Machine Learning》

## 许可证

MIT License
