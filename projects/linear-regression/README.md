# 线性回归 (Linear Regression)

从零实现线性回归，涵盖基础回归、正则化、优化算法、特征工程等核心技术。

## 项目简介

这是一个教学型的线性回归实现项目，旨在帮助学习者深入理解：
- 线性回归的数学原理与实现
- 多种优化算法（梯度下降变体）
- 正则化技术（L1/L2/Elastic Net）
- 特征工程（缩放、多项式、选择、交叉验证）
- 模型评估指标（MSE/RMSE/MAE/R2）
- 实际应用场景（房价/股票/销量预测）

## 核心循环

```
数据 -> 特征工程 -> 前向传播 -> 损失计算 -> 反向传播 -> 参数更新
```

## 项目结构

```
linear-regression/
├── src/
│   ├── __init__.py              # 模块初始化
│   ├── model.py                 # 回归模型（LR/Ridge/Lasso/ElasticNet）
│   ├── losses.py                # 损失函数（MSE/RMSE/MAE）
│   ├── optimizers.py            # 优化算法（BGD/SGD/MiniBatch/调度器）
│   ├── evaluation.py            # 评估指标（MSE/RMSE/MAE/R2）
│   ├── feature_engineering.py   # 特征工程（缩放/多项式/选择/CV）
│   └── utils.py                 # 工具函数
├── tests/
│   ├── test_model.py            # 模型测试
│   ├── test_losses.py           # 损失函数测试
│   ├── test_utils.py            # 工具函数测试
│   ├── test_evaluation.py       # 评估指标测试
│   └── test_feature_engineering.py  # 特征工程测试
├── examples/
│   ├── basic_example.py         # 基础示例
│   ├── regularization_example.py    # 正则化示例
│   ├── optimization_example.py      # 优化算法示例
│   ├── feature_engineering_example.py  # 特征工程示例
│   ├── house_price_prediction.py    # 房价预测
│   ├── stock_prediction.py          # 股票预测
│   └── sales_prediction.py          # 销量预测
├── docs/                        # 文档
├── requirements.txt             # 依赖
└── README.md                    # 说明文档
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行示例

```bash
# 基础示例
python examples/basic_example.py

# 正则化示例
python examples/regularization_example.py

# 优化算法示例
python examples/optimization_example.py

# 特征工程示例
python examples/feature_engineering_example.py

# 房价预测
python examples/house_price_prediction.py

# 股票预测
python examples/stock_prediction.py

# 销量预测
python examples/sales_prediction.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 算法分类

### 1. 基础线性回归

| 算法 | 说明 | 求解方法 |
|------|------|----------|
| 简单线性回归 | 单特征线性回归 | 梯度下降 / 正规方程 |
| 多元线性回归 | 多特征线性回归 | 梯度下降 / 正规方程 |

### 2. 正则化回归

| 算法 | 正则化类型 | 特点 |
|------|-----------|------|
| Ridge (岭回归) | L2 | 权重收缩，保留所有特征 |
| Lasso | L1 | 稀疏解，自动特征选择 |
| Elastic Net | L1+L2 | 结合两者优点 |

### 3. 优化算法

| 算法 | 特点 |
|------|------|
| 批量梯度下降 (BGD) | 使用全部数据，收敛稳定 |
| 随机梯度下降 (SGD) | 单样本更新，速度快但噪声大 |
| 小批量梯度下降 (Mini-Batch) | 平衡效率和稳定性 |
| 学习率调度 | 动态调整学习率 |

### 4. 特征工程

| 技术 | 说明 |
|------|------|
| 标准化 (StandardScaler) | 均值 0，标准差 1 |
| 归一化 (MinMaxScaler) | 缩放到 [0, 1] |
| 多项式特征 | 处理非线性关系 |
| 特征选择 | 方差/相关性/RFE |
| 交叉验证 | K 折交叉验证 |

### 5. 模型评估

| 指标 | 公式 | 特点 |
|------|------|------|
| MSE | (1/n) * sum((y-y')^2) | 对大误差敏感 |
| RMSE | sqrt(MSE) | 与目标同量纲 |
| MAE | (1/n) * sum(|y-y'|) | 对异常值鲁棒 |
| R2 | 1 - SS_res/SS_tot | 解释方差比例 |

## 学习路径

### 阶段 1：基础
1. 理解线性回归数学原理
2. 实现简单线性回归（单特征）
3. 理解损失函数（MSE）
4. 实现梯度下降

### 阶段 2：进阶
5. 多元线性回归
6. 正规方程法
7. 特征缩放的重要性
8. 模型评估指标

### 阶段 3：正则化
9. Ridge 回归（L2）
10. Lasso 回归（L1）
11. Elastic Net
12. 正则化强度选择

### 阶段 4：优化
13. 批量/随机/小批量梯度下降
14. 学习率调度
15. 多项式特征
16. 特征选择与交叉验证

### 阶段 5：应用
17. 房价预测
18. 股票预测
19. 销量预测

## 使用示例

### 基础使用

```python
import numpy as np
from src.model import LinearRegression
from src.utils import generate_linear_data, train_test_split

# 生成数据
X, y = generate_linear_data(n_samples=100, n_features=1, noise=0.5,
                             true_weights=np.array([3.0]), true_bias=4.0)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 梯度下降法
model = LinearRegression(learning_rate=0.1, n_iterations=500)
model.fit(X_train, y_train)
print(f"R2 Score: {model.score(X_test, y_test):.4f}")

# 正规方程法
model_ne = LinearRegression(method="normal_equation")
model_ne.fit(X_train, y_train)
print(f"R2 Score: {model_ne.score(X_test, y_test):.4f}")
```

### 正则化

```python
from src.model import RidgeRegression, LassoRegression, ElasticNet

# Ridge 回归
ridge = RidgeRegression(alpha=1.0, learning_rate=0.01, n_iterations=1000)
ridge.fit(X_train, y_train)

# Lasso 回归（特征选择）
lasso = LassoRegression(alpha=0.1, learning_rate=0.01, n_iterations=1000)
lasso.fit(X_train, y_train)
print(f"Non-zero weights: {lasso.get_params()['n_nonzero_weights']}")

# Elastic Net
enet = ElasticNet(alpha=0.5, l1_ratio=0.5)
enet.fit(X_train, y_train)
```

### 特征工程

```python
from src.feature_engineering import StandardScaler, PolynomialFeatures, cross_validation

# 标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 多项式特征
poly = PolynomialFeatures(degree=2)
X_train_poly = poly.fit_transform(X_train_scaled)

# 交叉验证
result = cross_validation(X, y, LinearRegression,
                          {"learning_rate": 0.01, "n_iterations": 500},
                          n_folds=5, metric="r2")
print(f"CV R2: {result['mean']:.4f} +/- {result['std']:.4f}")
```

## API 参考

### LinearRegression

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| learning_rate | float | 0.01 | 学习率 |
| n_iterations | int | 1000 | 迭代次数 |
| method | str | 'gradient_descent' | 求解方法 |
| verbose | bool | False | 打印训练过程 |

### RidgeRegression

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| alpha | float | 1.0 | L2 正则化强度 |
| method | str | 'gradient_descent' | 求解方法 |

### LassoRegression

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| alpha | float | 1.0 | L1 正则化强度 |

### ElasticNet

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| alpha | float | 1.0 | 总正则化强度 |
| l1_ratio | float | 0.5 | L1 占比 |

## 参考资源

- [scikit-learn LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)
- [Andrew Ng - Machine Learning](https://www.coursera.org/learn/machine-learning)
- [homemade-machine-learning](https://github.com/trekhleb/homemade-machine-learning)

## 许可证

MIT License
