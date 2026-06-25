# 贝叶斯优化 (Bayesian Optimization)

基于高斯过程的贝叶斯优化库，用于高效的黑盒函数优化。

## 项目概述

贝叶斯优化是一种序列化的全局优化策略，特别适用于：
- 目标函数评估代价高昂（如深度学习模型训练）
- 目标函数是黑盒函数（无梯度信息）
- 搜索空间维度不高（通常 < 20 维）

### 核心组件

1. **高斯过程 (Gaussian Process)**
   - 核函数：RBF、Matérn
   - 预测：均值、方差、采样
   - 超参数优化

2. **采集函数 (Acquisition Functions)**
   - 期望改进 (Expected Improvement, EI)
   - 置信上界 (Upper Confidence Bound, UCB)
   - 概率改进 (Probability of Improvement, PI)
   - Thompson 采样

3. **优化器 (Optimizer)**
   - 初始采样
   - 迭代优化
   - 结果分析与可视化

## 项目结构

```
bayesian-optimization/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── kernels.py         # 核函数实现
│   ├── gaussian_process.py # 高斯过程回归
│   ├── acquisition.py     # 采集函数
│   └── optimizer.py       # 贝叶斯优化器
├── tests/                  # 测试文件
│   ├── test_gaussian_process.py
│   ├── test_acquisition.py
│   └── test_optimizer.py
├── examples/               # 示例代码
│   ├── branin_function.py
│   └── hyperparameter_tuning.py
├── docs/                   # 文档
├── requirements.txt
└── README.md
```

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd bayesian-optimization

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 基本使用

```python
from src.optimizer import BayesianOptimizer
from src.acquisition import ExpectedImprovement

# 定义目标函数
def objective(x):
    return -x[0]**2  # 最大化 -x^2

# 创建优化器
optimizer = BayesianOptimizer(
    objective_function=objective,
    bounds=[(-5, 5)],  # 搜索空间
    acquisition=ExpectedImprovement(xi=0.01),
    kernel='rbf',
    n_initial=5,
    maximize=True
)

# 运行优化
result = optimizer.optimize(n_iterations=20, verbose=True)

print(f"最优解: {result['best_x']}")
print(f"最优值: {result['best_y']}")
```

### 超参数调优

```python
from src.optimizer import BayesianOptimizer
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score

def svm_objective(params):
    C = np.exp(params[0])
    gamma = np.exp(params[1])
    svm = SVC(C=C, gamma=gamma, kernel='rbf')
    scores = cross_val_score(svm, X, y, cv=5)
    return scores.mean()

optimizer = BayesianOptimizer(
    objective_function=svm_objective,
    bounds=[(-3, 3), (-5, 1)],  # log_C, log_gamma
    maximize=True
)

result = optimizer.optimize(n_iterations=20)
```

## 核心算法

### 贝叶斯优化流程

1. **初始化**: 使用拉丁超立方采样选择初始点
2. **循环**:
   - 拟合高斯过程模型
   - 优化采集函数选择下一个点
   - 评估目标函数
   - 更新模型
3. **返回**: 最优解

### 采集函数

#### 期望改进 (EI)

$$EI(x) = E[\max(f(x) - f_{best}, 0)]$$

$$= (\mu(x) - f_{best}) \Phi(Z) + \sigma(x) \phi(Z)$$

其中 $Z = \frac{\mu(x) - f_{best} - \xi}{\sigma(x)}$

#### 置信上界 (UCB)

$$UCB(x) = \mu(x) + \kappa \sigma(x)$$

#### 概率改进 (PI)

$$PI(x) = P(f(x) > f_{best} + \xi) = \Phi(Z)$$

## 应用场景

1. **机器学习超参数调优**
   - 学习率、正则化参数
   - 神经网络架构搜索

2. **实验设计**
   - 化学实验条件优化
   - 材料配方优化

3. **工程优化**
   - 控制器参数调优
   - 结构设计优化

## 参考文献

1. Shahriari, B., et al. (2016). "Taking the Human Out of the Loop: A Review of Bayesian Optimization." *Proceedings of the IEEE*.
2. Rasmussen, C. E., & Williams, C. K. (2006). *Gaussian Processes for Machine Learning*. MIT Press.
3. Brochu, E., Cora, V. M., & De Freitas, N. (2010). "A Tutorial on Bayesian Optimization of Expensive Cost Functions."

## 许可证

MIT License
