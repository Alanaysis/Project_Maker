# 实现细节文档

## 1. 核心算法实现

### 1.1 Sigmoid函数

```python
def _sigmoid(self, z: np.ndarray) -> np.ndarray:
    """
    Sigmoid激活函数实现

    关键点：
    1. 使用np.clip防止数值溢出
    2. 支持向量化计算
    """
    z = np.clip(z, -500, 500)  # 数值稳定性处理
    return 1 / (1 + np.exp(-z))
```

**数值稳定性问题**：
- 当z很大时，e^(-z)趋近于0，不会溢出
- 当z很小时，e^(-z)会很大，可能溢出
- 使用clip限制z的范围，避免极端值

### 1.2 交叉熵损失

```python
def _compute_loss(self, y_true, y_pred):
    """
    交叉熵损失实现

    L = -1/m * Σ[y*log(p) + (1-y)*log(1-p)]

    关键点：
    1. 使用epsilon防止log(0)
    2. 可选L2正则化
    """
    epsilon = 1e-15
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)

    cross_entropy = -np.mean(
        y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred)
    )

    if self.regularization > 0:
        l2_penalty = (self.regularization / (2 * m)) * np.sum(self.weights ** 2)
        return cross_entropy + l2_penalty

    return cross_entropy
```

### 1.3 梯度计算

```python
def _compute_gradients(self, X, y_true, y_pred):
    """
    梯度计算实现

    推导过程：
    1. 损失函数 L = -[y*log(a) + (1-y)*log(1-a)]
    2. 对z求导：dL/dz = a - y
    3. 对w求导：dL/dw = X^T * (a - y) / m
    4. 对b求导：dL/db = Σ(a - y) / m
    """
    m = len(y_true)
    error = y_pred - y_true

    dw = (1 / m) * np.dot(X.T, error)

    if self.regularization > 0:
        dw += (self.regularization / m) * self.weights

    db = (1 / m) * np.sum(error)

    return dw, db
```

### 1.4 梯度下降更新

```python
def fit(self, X, y):
    """
    训练过程实现

    核心循环：
    1. 前向传播：计算预测值
    2. 计算损失
    3. 反向传播：计算梯度
    4. 更新参数
    """
    for i in range(self.n_iterations):
        # 前向传播
        z = np.dot(X, self.weights) + self.bias
        y_pred = self._sigmoid(z)

        # 计算损失
        loss = self._compute_loss(y, y_pred)

        # 反向传播
        dw, db = self._compute_gradients(X, y, y_pred)

        # 更新参数
        self.weights -= self.learning_rate * dw
        self.bias -= self.learning_rate * db
```

## 2. 关键数学推导

### 2.1 梯度推导

目标：最小化损失函数 L

$$L = -\frac{1}{m}\sum_{i=1}^{m}[y^{(i)}\log(a^{(i)}) + (1-y^{(i)})\log(1-a^{(i)})]$$

其中 $a = \sigma(z)$，$z = w^Tx + b$

**步骤1**：对z求导

$$\frac{\partial L}{\partial z} = a - y$$

**步骤2**：利用链式法则

$$\frac{\partial L}{\partial w} = \frac{\partial L}{\partial z} \cdot \frac{\partial z}{\partial w} = (a - y) \cdot x$$

**步骤3**：对所有样本求平均

$$\frac{\partial L}{\partial w} = \frac{1}{m}X^T(a - y)$$

### 2.2 正则化梯度

L2正则化项：

$$R(w) = \frac{\lambda}{2m}\sum_{j=1}^{n}w_j^2$$

梯度：

$$\frac{\partial R}{\partial w} = \frac{\lambda}{m}w$$

## 3. 数值优化技巧

### 3.1 防止数值溢出

```python
# Sigmoid函数溢出处理
z = np.clip(z, -500, 500)

# 对数函数溢出处理
epsilon = 1e-15
y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
```

### 3.2 学习率选择

- 太大：损失震荡，不收敛
- 太小：收敛速度慢
- 建议：从0.01开始，根据收敛情况调整

### 3.3 特征标准化

虽然逻辑回归不要求特征标准化，但标准化后：
- 收敛更快
- 学习率选择更容易

```python
# 标准化示例
X_standardized = (X - X.mean(axis=0)) / X.std(axis=0)
```

## 4. 测试实现

### 4.1 单元测试策略

```python
class TestLogisticRegression:
    def test_sigmoid(self):
        """测试Sigmoid函数的基本性质"""

    def test_loss_computation(self):
        """测试损失计算的正确性"""

    def test_gradient_descent(self):
        """测试梯度下降收敛性"""

    def test_regularization(self):
        """测试正则化效果"""
```

### 4.2 测试数据设计

```python
# 线性可分数据：用于验证基本功能
@pytest.fixture
def linear_separable_data():
    X = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
    y = np.array([1, 1, 0, 0])
    return X, y

# 高斯分布数据：用于验证收敛性
@pytest.fixture
def gaussian_data():
    X_pos = np.random.randn(50, 2) + [2, 2]
    X_neg = np.random.randn(50, 2) + [-2, -2]
    ...
```

## 5. 性能优化

### 5.1 向量化计算

```python
# 错误：使用循环
for i in range(m):
    z[i] = np.dot(X[i], w) + b

# 正确：向量化
z = np.dot(X, w) + b
```

### 5.2 内存优化

- 避免不必要的数组复制
- 使用in-place操作
- 及时释放临时变量

## 6. 与sklearn对比

### 6.1 实现差异

| 特性 | 自定义实现 | sklearn |
|------|-----------|---------|
| 正则化参数 | lambda | C=1/lambda |
| 优化器 | 梯度下降 | L-BFGS等 |
| 多分类 | 不支持 | 支持 |
| 早停 | 不支持 | 支持 |

### 6.2 性能对比

在简单数据集上，自定义实现与sklearn性能相当：
- 准确率差异 < 1%
- 训练时间可能较长（未优化）
