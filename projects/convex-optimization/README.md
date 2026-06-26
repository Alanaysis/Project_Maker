# Convex Optimization Learning Project (凸优化学习项目)

> Understanding convex optimization through implementation.

---

## English

A hands-on learning project implementing core convex optimization algorithms from scratch. This project helps you understand the mathematical foundations and practical implementation of convex optimization solvers.

### Learning Objectives

1. **Understand Convex Optimization Principles**
   - Convex sets and convex functions
   - Local vs. global optimality
   - Duality theory

2. **Master KKT Conditions**
   - Karush-Kuhn-Tucker optimality conditions
   - Complementary slackness
   - Primal-dual methods

3. **Learn Interior Point Methods**
   - Log barrier functions
   - Central path
   - Primal-dual algorithms

### Project Structure

```
convex-optimization/
├── src/                          # Core modules
│   ├── __init__.py
│   ├── convexity_checker.py      # Convexity verification tools
│   ├── gradient_descent.py       # Gradient descent variants
│   ├── newton_method.py          # Newton's method optimizers
│   ├── interior_point.py         # Interior point method
│   ├── lagrangian.py             # Lagrangian multiplier method
│   ├── kkt_solver.py             # KKT conditions solver
│   ├── line_search.py            # Damped line search
│   └── convergence.py            # Convergence detection
├── examples/                     # Demo scripts
│   ├── 01_linear_programming.py
│   ├── 02_quadratic_programming.py
│   ├── 03_svm_convex.py
│   ├── 04_portfolio_optimization.py
│   └── 05_visualization.py
├── tests/                        # Unit tests
│   ├── test_convexity.py
│   ├── test_gradient_descent.py
│   ├── test_newton_method.py
│   ├── test_interior_point.py
│   ├── test_lagrangian.py
│   ├── test_kkt_solver.py
│   ├── test_line_search.py
│   └── test_convergence.py
├── requirements.txt
└── README.md
```

### How to Run Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run examples
python examples/01_linear_programming.py
python examples/02_quadratic_programming.py
python examples/03_svm_convex.py
python examples/04_portfolio_optimization.py
python examples/05_visualization.py

# Run tests
python -m pytest tests/
# or
python -m unittest discover tests/
```

### Core Optimization Loop

```
Problem Modeling → Feasibility Check → Optimization Iteration → Optimal Solution
问题建模 → 可行性检查 → 优化迭代 → 最优解
```

---

## 中文

通过从零实现，学习核心凸优化算法的手把手项目。本项目帮助你理解凸优化求解器的数学基础和实际实现。

### 学习目标

1. **理解凸优化原理**
   - 凸集与凸函数
   - 局部最优与全局最优
   - 对偶理论

2. **掌握 KKT 条件**
   - Karush-Kuhn-Tucker 最优性条件
   - 互补松弛条件
   - 原对偶方法

3. **学会内点法**
   - 对数障碍函数
   - 中心路径
   - 原对偶算法

### 项目结构

```
convex-optimization/
├── src/                          # 核心模块
│   ├── __init__.py
│   ├── convexity_checker.py      # 凸性检测工具
│   ├── gradient_descent.py       # 梯度下降变体
│   ├── newton_method.py          # 牛顿法优化器
│   ├── interior_point.py         # 内点法
│   ├── lagrangian.py             # 拉格朗日乘子法
│   ├── kkt_solver.py             # KKT 条件求解器
│   ├── line_search.py            # 阻尼线搜索
│   └── convergence.py            # 收敛检测
├── examples/                     # 演示脚本
│   ├── 01_linear_programming.py
│   ├── 02_quadratic_programming.py
│   ├── 03_svm_convex.py
│   ├── 04_portfolio_optimization.py
│   └── 05_visualization.py
├── tests/                        # 单元测试
│   ├── test_convexity.py
│   ├── test_gradient_descent.py
│   ├── test_newton_method.py
│   ├── test_interior_point.py
│   ├── test_lagrangian.py
│   ├── test_kkt_solver.py
│   ├── test_line_search.py
│   └── test_convergence.py
├── requirements.txt
└── README.md
```

### 如何运行示例

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/01_linear_programming.py
python examples/02_quadratic_programming.py
python examples/03_svm_convex.py
python examples/04_portfolio_optimization.py
python examples/05_visualization.py

# 运行测试
python -m pytest tests/
# 或
python -m unittest discover tests/
```

---

## Convex Optimization Theory Background / 凸优化理论基础

### What is Convex Optimization? / 什么是凸优化?

A **convex optimization problem** has the form:

```
minimize    f₀(x)
subject to  fᵢ(x) ≤ 0,  i = 1, ..., m
            Ax = b
```

where f₀, ..., fₘ are **convex functions**.

**凸优化问题**的形式为：

```
最小化    f₀(x)
约束条件   fᵢ(x) ≤ 0,  i = 1, ..., m
           Ax = b
```

其中 f₀, ..., fₘ 是**凸函数**。

### Key Properties / 关键性质

1. **Local = Global**: Any local minimum is a global minimum.
   **局部=全局**：任何局部最小值都是全局最小值。

2. **First-order condition**: x* is optimal iff grad(f)(x*) = 0 (unconstrained).
   **一阶条件**：x* 最优当且仅当 grad(f)(x*) = 0（无约束情况）。

3. **Second-order condition**: x* is optimal iff grad(f)(x*) = 0 and Hessian(f)(x*) ⪰ 0.
   **二阶条件**：x* 最优当且仅当 grad(f)(x*) = 0 且 Hessian(f)(x*) ⪰ 0。

### Common Convex Functions / 常见凸函数

| Function | Formula | Condition |
|----------|---------|-----------|
| Linear | aᵀx | Always convex |
| Quadratic | xᵀPx + qᵀx | P ⪰ 0 |
| Exponential | exp(aᵀx) | Always convex |
| Log-sum-exp | log(Σexp(xᵢ)) | Always convex |
| Negative entropy | Σxᵢlog(xᵢ) | x > 0 |
| Norm | ‖x‖ₚ | p ≥ 1 |
| Log barrier | -Σlog(xᵢ) | x > 0 |

### KKT Conditions / KKT 条件

For the problem with equality and inequality constraints:

```
minimize    f₀(x)
subject to  hᵢ(x) = 0,  i = 1, ..., p
            gⱼ(x) ≤ 0,  j = 1, ..., q
```

The **Lagrangian** is:

```
L(x, λ, ν) = f₀(x) + Σλⱼgⱼ(x) + Σνᵢhᵢ(x)
```

The **KKT conditions** (necessary for optimality):

1. **Stationarity**: ∇f₀(x*) + Σλⱼ∇gⱼ(x*) + Σνᵢ∇hᵢ(x*) = 0
2. **Primal feasibility**: hᵢ(x*) = 0, gⱼ(x*) ≤ 0
3. **Dual feasibility**: λⱼ ≥ 0
4. **Complementary slackness**: λⱼgⱼ(x*) = 0

### Algorithms Implemented / 实现的算法

| Algorithm | Convergence Rate | Complexity | Best For |
|-----------|-----------------|------------|----------|
| Gradient Descent | O(1/k) | O(n²) per iter | Large-scale problems |
| Momentum GD | O(1/k) | O(n²) per iter | Ill-conditioned problems |
| AdaGrad | Adaptive | O(n²) per iter | Sparse problems |
| Newton's Method | Quadratic | O(n³) per iter | Small/medium problems |
| Damped Newton | Global + quadratic | O(n³) per iter | Reliable convergence |
| Interior Point | Polynomial | Varies | Constrained problems |

---

## License

This project is for educational purposes only.

本项目仅用于教育目的。
