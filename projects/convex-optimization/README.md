# 凸优化

实现凸优化的核心算法，包括凸函数判断、优化算法、约束优化和实际应用。

## 项目概述

本项目是一个学习型项目，旨在深入理解和实现凸优化的核心概念和算法。通过实际代码实现，掌握凸优化的理论基础和实际应用。

### 学习目标

- 理解凸函数的定义和性质
- 掌握凸性判断方法（定义法、海森矩阵法）
- 理解强凸性和次梯度
- 掌握梯度下降、牛顿法、拟牛顿法等优化算法
- 理解拉格朗日对偶和 KKT 条件
- 掌握内点法等约束优化方法
- 应用凸优化解决实际问题（最小二乘、SVM、投资组合）

### 技术栈

- **主语言**: Python
- **框架**: 无（纯 NumPy 实现）
- **其他**: NumPy

### 核心概念

```
凸函数 → 优化算法 → 约束优化 → 实际应用
   ↓          ↓          ↓          ↓
凸性判断   梯度下降   拉格朗日    最小二乘
强凸性     牛顿法     KKT条件    SVM求解
次梯度     BFGS       内点法     投资组合
```

## 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd convex-optimization

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行示例

```bash
# 基础优化示例
python examples/basic_optimization.py

# 约束优化示例
python examples/constrained_optimization.py

# 最小二乘示例
python examples/least_squares_example.py

# 投资组合优化示例
python examples/portfolio_example.py
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_functions.py
pytest tests/test_optimizers.py
pytest tests/test_constrained.py
pytest tests/test_applications.py
```

## 项目结构

```
convex-optimization/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── functions/                # 凸函数模块
│   │   ├── __init__.py
│   │   ├── convex_function.py   # 凸函数基类
│   │   └── test_functions.py    # 测试函数
│   ├── optimizers/              # 优化算法模块
│   │   ├── __init__.py
│   │   ├── base_optimizer.py    # 优化器基类
│   │   ├── gradient_descent.py  # 梯度下降
│   │   ├── newton_method.py     # 牛顿法
│   │   └── bfgs.py              # BFGS/L-BFGS
│   ├── constrained/             # 约束优化模块
│   │   ├── __init__.py
│   │   ├── lagrangian.py        # 拉格朗日对偶
│   │   ├── kkt.py               # KKT 条件
│   │   └── interior_point.py    # 内点法
│   └── applications/            # 实际应用模块
│       ├── __init__.py
│       ├── least_squares.py     # 最小二乘
│       ├── svm.py               # SVM 求解
│       └── portfolio.py         # 投资组合优化
├── tests/                       # 测试代码
│   ├── __init__.py
│   ├── test_functions.py
│   ├── test_optimizers.py
│   ├── test_constrained.py
│   └── test_applications.py
├── examples/                    # 示例代码
│   ├── basic_optimization.py
│   ├── constrained_optimization.py
│   ├── least_squares_example.py
│   └── portfolio_example.py
├── docs/                        # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_DESIGN.md
│   ├── 03_IMPLEMENTATION.md
│   ├── 04_TESTING.md
│   └── 05_DEVELOPMENT.md
├── README.md
└── requirements.txt
```

## 核心模块

### 1. 凸函数 (src/functions/)

- **ConvexFunction**: 凸函数基类，提供凸性判断、强凸性检验、次梯度计算
- **QuadraticFunction**: 二次函数 f(x) = 0.5 x^T A x + b^T x + c
- **RosenbrockFunction**: Rosenbrock 函数（非凸测试函数）
- **LogisticLoss**: 逻辑损失函数（凸）
- **HuberLoss**: Huber 损失函数（凸，非光滑）
- **L1Norm**: L1 范数（凸，非光滑）
- **ElasticNet**: 弹性网络（凸）

### 2. 优化算法 (src/optimizers/)

- **GradientDescent**: 梯度下降（支持动量和 Nesterov 加速）
- **NewtonMethod**: 牛顿法（支持阻尼和正则化）
- **BFGS**: BFGS 拟牛顿法
- **LBFGS**: L-BFGS 有限内存拟牛顿法
- **Adam**: Adam 自适应学习率算法

### 3. 约束优化 (src/constrained/)

- **Lagrangian**: 拉格朗日函数
- **DualProblem**: 对偶问题
- **AugmentedLagrangian**: 增广拉格朗日方法
- **KKTChecker**: KKT 条件检验器
- **BarrierMethod**: 障碍函数法（内点法）
- **PrimalDualInteriorPoint**: 原始-对偶内点法

### 4. 实际应用 (src/applications/)

- **LeastSquares**: 普通最小二乘
- **RidgeRegression**: 岭回归（L2 正则化）
- **LassoRegression**: Lasso 回归（L1 正则化）
- **SVM**: 支持向量机
- **PortfolioOptimizer**: 投资组合优化

## 算法详解

### 凸性判断

1. **定义法**: f(αx + (1-α)y) ≤ αf(x) + (1-α)f(y)
2. **海森矩阵法**: ∇²f(x) 半正定（所有特征值 ≥ 0）

### 优化算法

1. **梯度下降**: x_{k+1} = x_k - α∇f(x_k)
2. **牛顿法**: x_{k+1} = x_k - [∇²f(x_k)]^{-1} ∇f(x_k)
3. **BFGS**: 通过迭代更新海森矩阵的近似

### 约束优化

1. **拉格朗日对偶**: 将约束问题转化为无约束问题
2. **KKT 条件**: 最优解的必要条件
3. **内点法**: 通过障碍函数处理约束

## 应用场景

### 最小二乘

- 数据拟合
- 回归分析
- 信号处理

### SVM

- 分类问题
- 模式识别
- 文本分类

### 投资组合

- 资产配置
- 风险管理
- 量化交易

## 参考资料

- Boyd, S., & Vandenberghe, L. (2004). *Convex Optimization*. Cambridge University Press.
- Nocedal, J., & Wright, S. J. (2006). *Numerical Optimization*. Springer.
- Bertsekas, D. P. (2015). *Convex Optimization Algorithms*. Athena Scientific.

## 许可证

MIT License
