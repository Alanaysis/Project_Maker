# 线性回归 (Linear Regression)

从零实现线性回归，理解梯度下降。

## 项目简介

这是一个教学型的线性回归实现项目，旨在帮助学习者深入理解：
- 线性回归的数学原理
- 梯度下降优化算法
- 损失函数的作用和计算
- 模型训练的完整流程

## 核心循环

```
数据 → 前向传播 → 损失计算 → 反向传播 → 参数更新
```

## 项目结构

```
linear-regression/
├── src/
│   ├── __init__.py      # 模块初始化
│   ├── model.py         # 线性回归模型
│   ├── losses.py        # 损失函数
│   └── utils.py         # 工具函数
├── tests/
│   ├── test_model.py    # 模型测试
│   ├── test_losses.py   # 损失函数测试
│   └── test_utils.py    # 工具函数测试
├── examples/
│   └── basic_example.py # 基础示例
├── docs/                # 文档
├── requirements.txt     # 依赖
└── README.md            # 说明文档
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行示例

```bash
python examples/basic_example.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 使用示例

### 基础使用

```python
import numpy as np
from src.model import LinearRegression

# 生成数据
np.random.seed(42)
X = 2 * np.random.rand(100, 1)
y = 4 + 3 * X.flatten() + np.random.randn(100) * 0.1

# 训练模型
model = LinearRegression(learning_rate=0.1, n_iterations=500)
model.fit(X, y)

# 预测
X_new = np.array([[1.0], [2.0]])
y_pred = model.predict(X_new)
print(f"预测结果: {y_pred}")

# 查看参数
print(f"权重: {model.weights[0]:.4f}")
print(f"偏置: {model.bias:.4f}")
```

### 可视化

```python
from src.utils import plot_loss_curve, plot_regression_line

# 绘制损失曲线
plot_loss_curve(model.losses)

# 绘制回归线
plot_regression_line(X, y, model.weights, model.bias)
```

## 核心概念

### 1. 线性回归模型

线性回归试图找到特征与目标之间的线性关系：

```
y = w * x + b
```

其中：
- `y` 是预测值
- `w` 是权重（斜率）
- `x` 是输入特征
- `b` 是偏置（截距）

### 2. 损失函数 (MSE)

均方误差用于衡量预测值与真实值的差异：

```
MSE = (1/n) * Σ(y_pred - y_true)²
```

### 3. 梯度下降

通过计算损失函数的梯度来更新参数：

```
w = w - learning_rate * ∂Loss/∂w
b = b - learning_rate * ∂Loss/∂b
```

## 学习目标

通过本项目，你将学到：

1. **线性回归原理**：理解线性回归的数学基础
2. **梯度下降**：掌握优化算法的工作原理
3. **损失函数**：理解 MSE 的计算和意义
4. **模型训练**：了解完整的训练流程
5. **模型评估**：学会使用 R² 等指标评估模型

## API 参考

### LinearRegression

#### 初始化参数

- `learning_rate` (float): 学习率，默认 0.01
- `n_iterations` (int): 迭代次数，默认 1000
- `verbose` (bool): 是否打印训练过程，默认 False

#### 方法

- `fit(X, y)`: 训练模型
- `predict(X)`: 预测
- `score(X, y)`: 计算 R² 分数
- `get_params()`: 获取模型参数

### MSELoss

- `compute(y_true, y_pred)`: 计算 MSE 损失
- `gradient(y_true, y_pred)`: 计算梯度

## 参考资源

- [scikit-learn LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html)
- [homemade-machine-learning](https://github.com/trekhleb/homemade-machine-learning)

## 许可证

MIT License
