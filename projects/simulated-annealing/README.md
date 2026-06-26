# 模拟退火优化算法 (Simulated Annealing Optimization)

> 实现模拟退火优化算法，理解温度调度、接受准则和邻域搜索策略

---

## 📖 项目简介 / Project Description

**中文**：
本项目实现了一个完整的模拟退火 (Simulated Annealing, SA) 优化算法库，
包含多种温度调度策略、接受准则、邻域生成方法和重启机制。
通过 TSP 求解、函数优化和可视化等示例，帮助学习者深入理解模拟退火算法的原理和应用。

**English**:
This project implements a complete Simulated Annealing (SA) optimization algorithm library,
including multiple temperature scheduling strategies, acceptance criteria, neighborhood generation methods,
and restart mechanisms. Through TSP solving, function optimization, and visualization examples,
it helps learners deeply understand the principles and applications of simulated annealing.

---

## 🎯 学习目标 / Learning Objectives

### 核心概念 / Core Concepts

1. **模拟退火原理**
   - 受金属退火过程启发的概率优化算法
   - 通过接受差解的概率避免陷入局部最优
   - Metropolis 准则：P = exp(-ΔE/T)

2. **温度调度**
   - 指数冷却：T(k+1) = α × T(k)
   - 线性冷却：T(k+1) = T(k) - δ
   - 对数冷却：T(k) = T₀ / log(1+k)
   - 自适应冷却：根据接受率动态调整

3. **接受准则**
   - Metropolis 准则：以概率 exp(-ΔE/T) 接受差解
   - ΔE < 0 时总是接受（贪心）
   - ΔE > 0 时以概率接受（探索）

4. **邻域搜索**
   - 交换、插入、反转（排列问题）
   - 高斯扰动（连续问题）
   - 自适应策略混合

### 掌握的技能 / Skills Gained

- [x] 理解模拟退火算法的数学基础
- [x] 掌握不同温度调度策略的特点和适用场景
- [x] 学会设计合适的邻域搜索策略
- [x] 理解接受准则在算法中的作用
- [x] 实现收敛检测和重启机制

---

## 📁 项目结构 / Project Structure

```
simulated-annealing/
├── src/                          # 源代码
│   ├── __init__.py               # 包初始化
│   ├── core.py                   # 核心算法
│   ├── temperature.py            # 温度调度
│   ├── acceptance.py             # 接受准则
│   ├── neighborhood.py           # 邻域生成
│   ├── cooling.py                # 冷却方案
│   ├── convergence.py            # 收敛检测
│   └── restart.py                # 重启机制
├── examples/                     # 示例
│   ├── tsp_solver.py             # TSP 求解器
│   ├── function_optimization.py  # 函数优化
│   ├── visualization.py          # 2D 可视化
│   └── sa_vs_ga.py              # 与遗传算法对比
├── tests/                        # 测试
│   └── test_simulated_annealing.py
├── requirements.txt              # 依赖
└── README.md                     # 本文件
```

---

## 🚀 快速开始 / Quick Start

### 安装依赖 / Install Dependencies

```bash
pip install -r requirements.txt
```

### 运行示例 / Run Examples

```bash
# TSP 求解器
python examples/tsp_solver.py

# 函数优化
python examples/function_optimization.py

# 2D 可视化（需要 matplotlib）
python examples/visualization.py

# SA vs GA 对比
python examples/sa_vs_ga.py
```

### 运行测试 / Run Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 📚 理论基础 / Theory Background

### 模拟退火算法 / Simulated Annealing Algorithm

模拟退火算法 (Simulated Annealing, SA) 由 Kirkpatrick 等人在 1983 年提出，
灵感来自固体退火过程：

1. **高温阶段**：粒子运动自由，系统处于高能量状态（广泛探索）
2. **降温阶段**：温度逐渐降低，粒子能量降低（探索→利用平衡）
3. **低温阶段**：粒子趋于稳定，达到低能量状态（精细利用）

### 算法流程 / Algorithm Flow

```
1. 初始化: S = S₀, T = T₀
2. While T > T_min:
    a. 生成邻域解: S_new = Neighbor(S)
    b. 计算能量差: ΔE = E(S_new) - E(S)
    c. 接受判断:
       - 如果 ΔE < 0: 接受 S_new
       - 如果 ΔE ≥ 0: 以概率 exp(-ΔE/T) 接受
    d. 降低温度: T = α × T
3. 返回最优解
```

### 关键参数 / Key Parameters

| 参数 | 说明 | 典型值 |
|------|------|--------|
| T₀ (初始温度) | 决定初期接受差解的概率 | 100-10000 |
| T_min (终止温度) | 算法终止的温度下限 | 1e-10 |
| α (冷却系数) | 控制降温速度 | 0.8-0.999 |
| L (每个温度的迭代次数) | 平衡计算精度和速度 | 50-200 |

### 冷却方案对比 / Cooling Schedule Comparison

| 方案 | 公式 | 特点 |
|------|------|------|
| 指数冷却 | T(k) = T₀ × α^k | 最常用，实现简单 |
| 线性冷却 | T(k) = T₀ × (1-k/K) | 简单直观 |
| 对数冷却 | T(k) = T₀/log(1+k) | 理论收敛保证 |
| 自适应冷却 | 动态调整 α | 自动适应问题 |

---

## 🔧 使用示例 / Usage Examples

### 基本用法 / Basic Usage

```python
from src.core import SimulatedAnnealing
from src.temperature import ExponentialScheduler
from src.neighborhood import continuous_neighbor
import random

# 创建 SA 求解器
sa = SimulatedAnnealing(
    initial_temp=1000.0,
    cooling_rate=0.99,
    iterations_per_temp=100,
)

# 执行优化
result = sa.optimize(
    objective=lambda x: sum(xi**2 for xi in x),  # Sphere 函数
    initial_solution=[5.0, 5.0],
    neighbor_generator=lambda sol: [
        sol[0] + random.gauss(0, 1),
        sol[1] + random.gauss(0, 1),
    ],
)

print(f"最优值: {result.best_energy}")
print(f"最优解: {result.best_solution}")
```

### TSP 求解 / TSP Solving

```python
from examples.tsp_solver import TSPSolver, generate_random_cities

# 生成城市
cities = generate_random_cities(30)

# 求解
solver = TSPSolver(cities)
result = solver.solve(
    initial_temp=10000.0,
    cooling_rate=0.995,
    strategy="swap",
)

print(f"最短路径: {result.best_energy:.4f}")
```

---

## 📊 算法对比 / Algorithm Comparison

| 特性 | 模拟退火 (SA) | 遗传算法 (GA) |
|------|---------------|---------------|
| 搜索方式 | 单点搜索 | 种群搜索 |
| 全局搜索 | 通过温度控制 | 通过种群多样性 |
| 参数数量 | 较少 (3-5个) | 较多 (5-10个) |
| 实现复杂度 | 简单 | 中等 |
| 适用场景 | 连续/离散优化 | 组合优化 |
| 收敛速度 | 中等 | 中等 |

---

## 📝 参考 / References

1. Kirkpatrick, S., Gelatt, C. D., & Vecchi, M. P. (1983). Optimization by Simulated Annealing. *Science*.
2. Geman, S., & Geman, D. (1984). Stochastic relaxation, Gibbs distributions, and the Bayesian restoration of images.
3. Černý, V. (1985). Thermodynamic approach to the traveling salesman problem. *Czechoslovak Mathematical Journal*.

---

## 📄 许可证 / License

MIT License
