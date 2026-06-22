# 实现细节

## 核心实现

### 1. 基类设计

基类 `NaiveBayesClassifier` 定义了所有朴素贝叶斯变体的通用接口:

```python
class NaiveBayesClassifier(ABC):
    def __init__(self, alpha=1.0):
        self.alpha = alpha  # 平滑参数
        self.class_priors = {}  # 先验概率
        self.classes = []  # 类别列表
        self.is_fitted = False

    @abstractmethod
    def fit(self, X, y):
        """训练模型"""

    @abstractmethod
    def _calculate_likelihood(self, x, class_label):
        """计算似然"""

    def predict(self, X):
        """预测类别"""

    def predict_proba(self, X):
        """预测概率"""
```

### 2. 高斯朴素贝叶斯

**关键步骤**:
1. 按类别分组计算均值和方差
2. 使用高斯概率密度函数计算似然
3. 应用方差平滑防止除零

**公式推导**:
```
P(xi|C) = 1/sqrt(2πσ²) * exp(-(xi-μ)²/(2σ²))

log P(xi|C) = -0.5*log(2πσ²) - (xi-μ)²/(2σ²)
```

### 3. 多项式朴素贝叶斯

**关键步骤**:
1. 统计每个类别下每个特征的计数
2. 应用Laplace平滑
3. 计算对数概率

**公式推导**:
```
P(xi|C) = (Nxi + α) / (Nc + α*n_features)

log P(xi|C) = log(Nxi + α) - log(Nc + α*n_features)
```

### 4. 伯努利朴素贝叶斯

**关键步骤**:
1. 统计每个类别下每个特征为1的计数
2. 应用Laplace平滑
3. 根据特征值选择对应的对数概率

**公式推导**:
```
P(xi=1|C) = (count + α) / (n_class + 2α)
P(xi=0|C) = 1 - P(xi=1|C)

log P(xi|C) = xi * log P(xi=1|C) + (1-xi) * log P(xi=0|C)
```

## 技术要点

### 1. 对数空间计算

**问题**: 连乘小概率会导致数值下溢
**解决**: 使用对数概率，将乘法转换为加法

```python
# 错误方式
prob = P(C) * P(x1|C) * P(x2|C) * ...  # 可能下溢为0

# 正确方式
log_prob = log P(C) + log P(x1|C) + log P(x2|C) + ...
```

### 2. Laplace平滑

**问题**: 某个特征在某类别中未出现，导致概率为0
**解决**: 给每个计数加上平滑参数α

```python
# 未平滑
prob = count / total  # 如果count=0，prob=0

# 平滑后
prob = (count + alpha) / (total + alpha * n_features)
```

### 3. 概率归一化

使用log-sum-exp技巧将对数概率转换为概率:

```python
# 计算对数概率
scores = {cls: log_likelihood + log_prior for cls in classes}

# log-sum-exp技巧
max_score = max(scores.values())
exp_scores = {k: exp(v - max_score) for k, v in scores.items()}
total = sum(exp_scores.values())
proba = {k: v / total for k, v in exp_scores.items()}
```

## 性能优化

1. **向量化计算**: 使用列表推导式
2. **提前计算**: 训练时预计算所有参数
3. **对数空间**: 避免数值问题

## 代码质量

1. **类型注解**: 所有函数都有类型提示
2. **文档字符串**: 详细的函数说明
3. **错误处理**: 输入验证和异常处理
4. **代码风格**: 遵循PEP 8
