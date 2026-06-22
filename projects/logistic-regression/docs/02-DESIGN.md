# 逻辑回归项目设计文档

## 1. 项目架构

```
logistic-regression/
├── src/                        # 源代码目录
│   ├── __init__.py            # 包初始化
│   ├── logistic_regression.py # 核心模型实现
│   └── metrics.py             # 评估指标
├── tests/                      # 测试目录
│   ├── test_logistic_regression.py
│   └── test_metrics.py
├── examples/                   # 示例代码
│   ├── basic_usage.py
│   └── compare_sklearn.py
├── docs/                       # 文档目录
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── main.py                     # 主入口
├── README.md                   # 项目说明
└── LEARNING_NOTES.md           # 学习笔记
```

## 2. 核心类设计

### 2.1 LogisticRegression类

```python
class LogisticRegression:
    """
    逻辑回归分类器

    设计原则：
    1. 接口与scikit-learn保持一致
    2. 支持链式调用（fit返回self）
    3. 参数可配置
    4. 支持模型序列化
    """

    def __init__(self, learning_rate, n_iterations, regularization, threshold, verbose):
        ...

    def fit(self, X, y) -> 'LogisticRegression':
        """训练模型"""

    def predict(self, X) -> np.ndarray:
        """预测类别"""

    def predict_proba(self, X) -> np.ndarray:
        """预测概率"""

    def score(self, X, y) -> float:
        """计算准确率"""
```

### 2.2 模块依赖关系

```
main.py
    └── examples/basic_usage.py
            └── src/__init__.py
                    ├── logistic_regression.py
                    │       └── numpy
                    └── metrics.py
                            └── numpy
```

## 3. 数据流设计

### 3.1 训练流程

```
输入数据 X, y
       │
       ▼
┌─────────────────┐
│  参数初始化       │
│  w = zeros       │
│  b = 0           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  迭代训练        │
│  for i in range  │◄──────┐
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│  前向传播        │       │
│  z = Xw + b     │       │
│  a = sigmoid(z) │       │
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│  计算损失        │       │
│  L = cross_ent  │       │
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│  反向传播        │       │
│  计算梯度 dw, db │       │
└────────┬────────┘       │
         │                │
         ▼                │
┌─────────────────┐       │
│  参数更新        │       │
│  w -= lr * dw   │───────┘
│  b -= lr * db   │
└─────────────────┘
         │
         ▼
    训练完成
```

### 3.2 预测流程

```
输入新样本 X
       │
       ▼
┌─────────────────┐
│  线性变换        │
│  z = Xw + b     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Sigmoid激活    │
│  p = σ(z)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  阈值判断        │
│  if p >= 0.5:   │
│      return 1   │
│  else:          │
│      return 0   │
└─────────────────┘
         │
         ▼
    输出预测结果
```

## 4. 接口设计

### 4.1 与scikit-learn兼容

我们的实现遵循scikit-learn的API设计模式：

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `fit(X, y)` | 训练模型 | self |
| `predict(X)` | 预测类别 | ndarray |
| `predict_proba(X)` | 预测概率 | ndarray |
| `score(X, y)` | 计算准确率 | float |

### 4.2 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| learning_rate | float | 0.01 | 学习率 |
| n_iterations | int | 1000 | 迭代次数 |
| regularization | float | 0.0 | L2正则化强度 |
| threshold | float | 0.5 | 分类阈值 |
| verbose | bool | False | 是否打印训练过程 |

## 5. 评估指标模块

### 5.1 函数接口

```python
def confusion_matrix(y_true, y_pred) -> Tuple[int, int, int, int]
def accuracy_score(y_true, y_pred) -> float
def precision_score(y_true, y_pred) -> float
def recall_score(y_true, y_pred) -> float
def f1_score(y_true, y_pred) -> float
def classification_report(y_true, y_pred) -> str
```

## 6. 扩展性设计

### 6.1 可扩展点

1. **优化器扩展**：可添加SGD、Adam等优化器
2. **多分类支持**：通过One-vs-Rest策略扩展
3. **批量训练**：支持mini-batch梯度下降
4. **早停机制**：根据验证集性能提前停止

### 6.2 预留接口

```python
# 未来可扩展
class LogisticRegression:
    def __init__(self, optimizer='gd', batch_size=None, early_stopping=False):
        ...
```

## 7. 测试策略

### 7.1 单元测试

- Sigmoid函数数值稳定性测试
- 损失计算正确性测试
- 梯度计算正确性测试
- 收敛性测试

### 7.2 集成测试

- 完整训练流程测试
- 与sklearn对比测试
- 边界条件测试

## 8. 性能考虑

### 8.1 数值稳定性

- Sigmoid函数使用`np.clip`防止溢出
- 交叉熵损失使用epsilon防止log(0)

### 8.2 计算效率

- 使用NumPy向量化操作
- 避免显式循环
- 矩阵运算替代逐元素操作
