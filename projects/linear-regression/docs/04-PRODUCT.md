# 04 - 产品文档

## 产品概述

线性回归教学项目是一个从零实现的机器学习学习工具，旨在帮助学习者理解线性回归的核心概念。

## 目标用户

1. **机器学习初学者**：想了解基础算法
2. **学生**：学习机器学习课程
3. **开发者**：想深入理解算法原理

## 使用场景

### 场景 1：学习线性回归原理
```python
# 创建模型
model = LinearRegression(learning_rate=0.01, n_iterations=100)

# 训练模型
model.fit(X_train, y_train)

# 查看损失曲线
model.plot_losses()
```

### 场景 2：观察梯度下降过程
```python
# 训练并记录每一步的参数
model = LinearRegression(learning_rate=0.01, n_iterations=100)
model.fit(X_train, y_train)

# 查看参数更新历史
print(model.weight_history)
print(model.bias_history)
```

### 场景 3：预测新数据
```python
# 预测
predictions = model.predict(X_test)

# 评估
mse = MSELoss.compute(y_test, predictions)
print(f"MSE: {mse}")
```

## 功能列表

### 核心功能
- [x] 线性回归模型实现
- [x] 梯度下降优化
- [x] MSE 损失计算
- [x] 训练过程可视化

### 辅助功能
- [x] 数据生成工具
- [x] 模型评估指标
- [x] 结果可视化

### 扩展功能
- [ ] 多特征支持
- [ ] 批量梯度下降
- [ ] 正则化

## API 参考

### LinearRegression

#### __init__(learning_rate, n_iterations)
- `learning_rate` (float): 学习率，默认 0.01
- `n_iterations` (int): 迭代次数，默认 1000

#### fit(X, y)
训练模型。
- `X` (np.ndarray): 特征矩阵，形状 (n_samples, n_features)
- `y` (np.ndarray): 目标值，形状 (n_samples,)

#### predict(X)
预测。
- `X` (np.ndarray): 特征矩阵
- 返回：预测值

### MSELoss

#### compute(y_true, y_pred)
计算 MSE 损失。
- `y_true` (np.ndarray): 真实值
- `y_pred` (np.ndarray): 预测值
- 返回：损失值

## 示例代码

### 基础示例
```python
import numpy as np
from src.model import LinearRegression

# 生成数据
np.random.seed(42)
X = 2 * np.random.rand(100, 1)
y = 4 + 3 * X + np.random.randn(100, 1)

# 训练模型
model = LinearRegression(learning_rate=0.01, n_iterations=1000)
model.fit(X, y)

# 预测
X_new = np.array([[0], [2]])
y_pred = model.predict(X_new)
print(f"预测结果: {y_pred}")
```

## 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 训练时间 (1000样本) | < 1s | 0.5s |
| 收敛迭代次数 | < 500 | 200 |
| 内存占用 | < 100MB | 50MB |
