# 03 - 设计文档

## 系统架构

```
linear-regression/
├── src/
│   ├── __init__.py
│   ├── model.py          # 线性回归模型
│   ├── losses.py         # 损失函数
│   ├── optimizers.py     # 优化器
│   └── utils.py          # 工具函数
├── tests/
│   ├── test_model.py     # 模型测试
│   ├── test_losses.py    # 损失函数测试
│   └── test_utils.py     # 工具函数测试
├── examples/
│   └── basic_example.py  # 基础示例
└── docs/
    └── ...               # 文档
```

## 核心类设计

### 1. LinearRegression 类

```python
class LinearRegression:
    def __init__(self, learning_rate=0.01, n_iterations=1000):
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.weights = None
        self.bias = None
        self.losses = []  # 记录损失历史

    def fit(self, X, y):
        """训练模型"""
        # 初始化参数
        # 迭代训练
        # 记录损失
        pass

    def predict(self, X):
        """预测"""
        return X @ self.weights + self.bias

    def _compute_gradients(self, X, y, y_pred):
        """计算梯度"""
        n = len(y)
        dw = (2/n) * X.T @ (y_pred - y)
        db = (2/n) * np.sum(y_pred - y)
        return dw, db

    def _update_parameters(self, dw, db):
        """更新参数"""
        self.weights -= self.learning_rate * dw
        self.bias -= self.learning_rate * db
```

### 2. Loss 类

```python
class MSELoss:
    @staticmethod
    def compute(y_true, y_pred):
        """计算 MSE 损失"""
        return np.mean((y_true - y_pred) ** 2)

    @staticmethod
    def gradient(y_true, y_pred):
        """计算梯度"""
        n = len(y_true)
        return (2/n) * (y_pred - y_true)
```

### 3. Visualizer 类

```python
class Visualizer:
    @staticmethod
    def plot_loss_curve(losses):
        """绘制损失曲线"""
        pass

    @staticmethod
    def plot_regression_line(X, y, model):
        """绘制回归线"""
        pass

    @staticmethod
    def plot_training_process(X, y, model):
        """展示训练过程"""
        pass
```

## 数据流

```
输入数据 X, y
    ↓
初始化参数 w, b
    ↓
┌─────────────────────┐
│ 前向传播            │
│ y_pred = X * w + b  │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 计算损失            │
│ Loss = MSE(y, y_pred)│
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 反向传播            │
│ 计算梯度 dw, db     │
└─────────────────────┘
    ↓
┌─────────────────────┐
│ 参数更新            │
│ w = w - lr * dw     │
│ b = b - lr * db     │
└─────────────────────┘
    ↓
重复以上步骤 n_iterations 次
```

## 算法细节

### 梯度下降公式推导

对于线性回归：
```
y_pred = w * x + b
Loss = (1/n) * Σ(y_pred - y_true)²
```

对 w 求偏导：
```
∂Loss/∂w = (2/n) * Σ(y_pred - y_true) * x
         = (2/n) * X.T @ (y_pred - y_true)
```

对 b 求偏导：
```
∂Loss/∂b = (2/n) * Σ(y_pred - y_true)
         = (2/n) * np.sum(y_pred - y_true)
```

## 扩展性设计

1. **支持多特征**：通过矩阵运算支持多个特征
2. **可扩展损失函数**：添加其他损失函数（如 MAE）
3. **可扩展优化器**：添加其他优化算法（如 Adam）
4. **批量梯度下降**：支持 mini-batch 训练

## 错误处理

1. **输入验证**：检查输入数据维度
2. **数值稳定性**：处理 NaN 和 Inf
3. **收敛检测**：检测损失是否收敛
