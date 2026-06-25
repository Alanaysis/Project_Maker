# 03 - 设计文档

## 系统架构

```
linear-regression/
├── src/
│   ├── __init__.py              # 模块导出
│   ├── model.py                 # 回归模型层
│   ├── losses.py                # 损失函数层
│   ├── optimizers.py            # 优化算法层
│   ├── evaluation.py            # 评估指标层
│   ├── feature_engineering.py   # 特征工程层
│   └── utils.py                 # 工具函数层
├── tests/                       # 测试层
├── examples/                    # 应用层
└── docs/                        # 文档层
```

## 分层设计

### 第 1 层：基础组件
- losses.py: 损失函数
- optimizers.py: 优化算法
- evaluation.py: 评估指标

### 第 2 层：特征工程
- feature_engineering.py: 特征处理

### 第 3 层：模型
- model.py: 回归模型（依赖第 1、2 层）

### 第 4 层：应用
- examples/: 实际应用示例

## 核心类设计

### 1. LinearRegression 类

```python
class LinearRegression:
    def __init__(self, learning_rate=0.01, n_iterations=1000,
                 method='gradient_descent', verbose=False):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.method = method
        self.verbose = verbose
        self.weights = None
        self.bias = 0.0
        self.losses = []

    def fit(self, X, y):
        """训练模型（支持梯度下降和正规方程）"""
        if self.method == 'normal_equation':
            self._fit_normal_equation(X, y)
        else:
            self._fit_gradient_descent(X, y)

    def predict(self, X):
        """预测"""
        return X @ self.weights + self.bias

    def score(self, X, y):
        """计算 R2 分数"""
        ...
```

### 2. RidgeRegression 类

```python
class RidgeRegression:
    def __init__(self, alpha=1.0, learning_rate=0.01, n_iterations=1000):
        self.alpha = alpha  # L2 正则化强度
        ...

    def fit(self, X, y):
        """损失 = MSE + alpha * ||w||^2"""
        ...
```

### 3. LassoRegression 类

```python
class LassoRegression:
    def __init__(self, alpha=1.0, learning_rate=0.01, n_iterations=1000):
        self.alpha = alpha  # L1 正则化强度
        ...

    def fit(self, X, y):
        """损失 = MSE + alpha * ||w||_1"""
        ...
```

### 4. ElasticNet 类

```python
class ElasticNet:
    def __init__(self, alpha=1.0, l1_ratio=0.5, ...):
        self.alpha = alpha
        self.l1_ratio = l1_ratio  # L1 占比
        ...
```

## 数据流

```
输入数据 X, y
    |
    v
特征工程 (缩放/多项式/选择)
    |
    v
初始化参数 w, b
    |
    v
+---------------------+
| 前向传播            |
| y_pred = X @ w + b  |
+---------------------+
    |
    v
+---------------------+
| 计算损失            |
| Loss = MSE + 正则项 |
+---------------------+
    |
    v
+---------------------+
| 计算梯度            |
| dw, db (含正则项)   |
+---------------------+
    |
    v
+---------------------+
| 参数更新            |
| w = w - lr * dw     |
| b = b - lr * db     |
+---------------------+
    |
    v
重复以上步骤 n_iterations 次
    |
    v
评估模型 (MSE/RMSE/MAE/R2)
```

## 正则化设计

### L2 正则化 (Ridge)

```
Loss = MSE + alpha * sum(w^2)
梯度: dw = (2/n) * X.T @ error + 2 * alpha * w
```

效果：权重趋向于小值，但不会为零。

### L1 正则化 (Lasso)

```
Loss = MSE + alpha * sum(|w|)
梯度: dw = (2/n) * X.T @ error + alpha * sign(w)
```

效果：可以将权重压缩到零（稀疏解），实现特征选择。

### Elastic Net

```
Loss = MSE + alpha * l1_ratio * sum(|w|)
     + alpha * (1-l1_ratio) * 0.5 * sum(w^2)
```

效果：结合 L1 和 L2 的优点。

## 优化算法设计

### 批量梯度下降
```
每次使用全部 n 个样本:
  dw = (2/n) * X.T @ (y_pred - y)
  db = (2/n) * sum(y_pred - y)
```

### 随机梯度下降
```
每次使用 1 个样本 i:
  dw = 2 * x_i * (y_pred_i - y_i)
  db = 2 * (y_pred_i - y_i)
```

### 小批量梯度下降
```
每次使用 batch_size 个样本:
  dw = (2/batch_size) * X_batch.T @ (y_pred_batch - y_batch)
  db = (2/batch_size) * sum(y_pred_batch - y_batch)
```

## 特征工程设计

### 标准化
```
x_scaled = (x - mean) / std
```

### 归一化
```
x_scaled = (x - min) / (max - min)
```

### 多项式特征
```
对于 [x1, x2]，degree=2:
输出: [x1, x2, x1^2, x2^2, x1*x2]
```

## 错误处理

1. **输入验证**：检查数据维度匹配
2. **数值稳定性**：避免除以零
3. **矩阵求逆**：使用伪逆 (pinv) 代替逆矩阵
4. **收敛检测**：监控损失变化
