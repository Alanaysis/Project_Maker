# Bayesian Optimization / 贝叶斯优化

> 从零实现贝叶斯优化超参数调优框架，包含高斯过程、采集函数和完整的优化循环。

**中文**: 实现贝叶斯优化超参数调优 | **English**: Implement Bayesian Optimization for hyperparameter tuning

---

## 📖 项目描述 / Project Description

本项目从零实现了一个完整的贝叶斯优化框架，用于黑盒函数优化和超参数调优。贝叶斯优化是一种高效的序列优化方法，通过构建目标函数的概率代理模型（高斯过程）和使用采集函数来指导搜索，在较少的函数评估次数下找到全局最优解。

This project implements a complete Bayesian Optimization framework from scratch for black-box function optimization and hyperparameter tuning. BO uses a probabilistic surrogate model (Gaussian Process) and acquisition functions to guide search efficiently with minimal function evaluations.

---

## 🎯 学习目标 / Learning Objectives

### 核心理论 / Core Theory

1. **理解贝叶斯优化原理** - 掌握先验、似然、后验的更新机制
2. **掌握高斯过程** - 实现 GP 回归、Cholesky 分解、预测推导
3. **学会采集函数设计** - 实现 EI、UCB、PI 三种采集函数

### 具体技能 / Specific Skills

- [x] 高斯过程回归实现（含 RBF/Matern 核）
- [x] 协方差矩阵计算与 Cholesky 分解
- [x] Expected Improvement (EI) 采集函数
- [x] Upper Confidence Bound (UCB) 采集函数
- [x] Probability of Improvement (PI) 采集函数
- [x] 贝叶斯优化主循环
- [x] 超参数优化（边际似然最大化）
- [x] 噪声建模

---

## 🏗️ 项目结构 / Project Structure

```
bayesian-optimization/
├── src/                          # 核心源码
│   ├── __init__.py
│   ├── kernel.py                 # 核函数（RBF, Matern, 组合核）
│   ├── gaussian_process.py       # 高斯过程回归
│   ├── acquisition.py            # 采集函数（EI, UCB, PI）
│   ├── optimization.py           # 超参数优化 & LHS
│   ├── noise_model.py            # 噪声模型
│   ├── benchmarks.py             # 基准测试函数
│   └── bo_loop.py                # 贝叶斯优化主循环
├── examples/                     # 示例脚本
│   ├── optimize_branin.py        # Branin 函数优化
│   ├── optimize_hartmann.py      # Hartmann 函数优化
│   ├── compare_acquisitions.py   # 采集函数对比
│   ├── hparam_tuning.py          # 超参数调优
│   └── visualize_bo.py           # 优化过程可视化
├── tests/                        # 单元测试
│   ├── test_kernel.py
│   ├── test_gaussian_process.py
│   ├── test_acquisition.py
│   ├── test_benchmarks.py
│   ├── test_noise_model.py
│   └── test_optimization.py
├── requirements.txt
└── README.md
```

---

## 🚀 快速开始 / Quick Start

### 安装 / Installation

```bash
cd projects/bayesian-optimization
pip install -r requirements.txt
```

### 运行示例 / Run Examples

```bash
# Branin 函数优化（2D，可视化）
python examples/optimize_branin.py

# Hartmann 函数优化（6D）
python examples/optimize_hartmann.py

# 采集函数对比
python examples/compare_acquisitions.py

# 超参数调优
python examples/hparam_tuning.py

# 1D 优化过程可视化
python examples/visualize_bo.py
```

### 运行测试 / Run Tests

```bash
pytest tests/ -v
```

---

## 📐 理论基础 / Theory Background

### 贝叶斯优化流程 / BO Workflow

```
初始采样 → 高斯过程建模 → 采集函数 → 新采样点 → 更新模型
```

### 高斯过程 / Gaussian Process

GP 作为先验分布 over functions:

```
f(x) ~ GP(m(x), k(x, x'))
```

观测数据 D = {(x_i, y_i)} 后的后验分布:

```
p(f* | D, x*) = N(mu*, sigma*^2)

mu*   = k_*^T (K + sigma_n^2 * I)^{-1} y
sigma*^2 = k** - k_*^T (K + sigma_n^2 * I)^{-1} k_*
```

其中 K = k(X, X) 是协方差矩阵，使用 Cholesky 分解 K = L*L^T 求解。

### 核函数 / Kernels

**RBF 核（平方指数核）**:
```
K(x, x') = sigma_f^2 * exp(-||x - x'||^2 / (2 * l^2))
```
- 无限可微，产生非常平滑的函数
- 最常用的 BO 核函数

**Matern 核**:
```
nu = 1/2: 非常粗糙（不可微）
nu = 3/2: 一次可微
nu = 5/2: 二次可微
nu -> inf: 退化为 RBF
```
- 更灵活，可以控制函数的平滑度
- 在 nu=2.5 时提供闭式解

### 采集函数 / Acquisition Functions

**Expected Improvement (EI)**:
```
EI(x) = E[max(0, f_best - f(x))]
      = (f_best - mu + xi) * Phi(z) + sigma * phi(z)
```
- 自然平衡探索与利用
- 最广泛使用的采集函数

**Upper Confidence Bound (UCB)**:
```
UCB(x) = mu(x) + beta * sigma(x)
```
- 理论保证（次线性 regret）
- 不需要知道 f_best

**Probability of Improvement (PI)**:
```
PI(x) = P(f(x) > f_best) = Phi((mu - f_best) / sigma)
```
- 最简单的采集函数
- 倾向于过度利用（greedy）

### 边际似然 / Marginal Likelihood

用于优化核超参数:

```
log p(y|X, theta) = -0.5 * y^T K^{-1} y - 0.5 * log|K| - n/2 * log(2pi)
```

这是自动奥卡姆剃刀：奖励拟合好，惩罚复杂度过高。

---

## 📊 基准函数 / Benchmark Functions

| 函数 | 维度 | 全局最优 | 特点 |
|------|------|----------|------|
| Branin | 2 | 0.3979 | 3个全局最小值，经典测试 |
| Hartmann | d (6) | -3.3224 | 多模态，BO标准基准 |
| Booth | 2 | 0 | 单峰，简单测试 |
| Rastrigin | d | 0 | 高度多模态 |
| Ackley | d | 0 | 平坦外围+深中心 |

---

## 🔧 使用示例 / Usage Examples

### 基本用法

```python
from src.bo_loop import BayesianOptimization
from src.benchmarks import branin, branin_bounds

# 定义搜索空间
bounds = branin_bounds()  # [[-5, 10], [0, 15]]

# 创建 BO 实例
bo = BayesianOptimization(
    bounds=bounds,
    acquisition="ei",      # 使用 EI 采集函数
    xi=0.01,               # 探索参数
    n_initial=10,          # 初始采样数
    random_state=42,
)

# 运行优化
result = bo.run(branin, n_iter=30, verbose=True)

print(f"最佳解: x={result['best_x']}, f(x)={result['best_y']}")
```

### 自定义核函数

```python
from src.kernel import MaternKernel

bo = BayesianOptimization(
    bounds=bounds,
    kernel=MaternKernel(nu=2.5, length_scale=1.0),
)
```

### 切换采集函数

```python
# Expected Improvement
bo = BayesianOptimization(bounds=bounds, acquisition="ei", xi=0.01)

# Upper Confidence Bound
bo = BayesianOptimization(bounds=bounds, acquisition="ucb", beta=2.0)

# Probability of Improvement
bo = BayesianOptimization(bounds=bounds, acquisition="pi", xi=0.01)
```

---

## 📝 核心概念详解

### 探索 vs 利用 / Exploration vs Exploitation

贝叶斯优化的核心挑战是平衡：

- **探索（Exploration）**: 在不确定性高的区域采样
  - 采集函数中的 sigma 项驱动探索
  - 适合发现全局最优

- **利用（Exploitation）**: 在当前最优附近采样
  - 采集函数中的 mu 项驱动利用
  - 适合精细搜索

### 为什么用高斯过程？

1. **提供不确定性估计**: 不仅预测均值，还给出方差
2. **核方法灵活性**: 通过核函数编码领域知识
3. **贝叶斯一致性**: 先验 + 似然 = 后验，理论完备
4. **Cholesky 分解**: 数值稳定的求解方法

### 采样的策略

**Latin Hypercube Sampling (LHS)**:
- 每个维度等间隔采样
- 保证空间填充性
- 比纯随机采样更适合初始化

---

## 📚 参考资源 / References

1. **Shahriari et al. (2015)** - "Taking the Human Out of the Loop: A Review of Bayesian Optimization"
2. **Rasmussen & Williams (2006)** - "Gaussian Processes for Machine Learning"
3. **Snoek et al. (2012)** - "Practical Bayesian Optimization of Machine Learning Algorithms"
4. **Guerrero et al. (2021)** - "A Tutorial on Bayesian Optimization"

---

## ⚙️ 技术栈 / Tech Stack

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.8+ |
| 数值计算 | NumPy, SciPy |
| 可视化 | Matplotlib |
| 测试 | pytest |

---

## 📄 许可证 / License

MIT License

---

## 🙏 致谢 / Acknowledgments

感谢 GPML (Rasmussen & Williams) 提供的理论框架和数学推导。
