# 项目设计

## 架构设计

### 模块结构

```
naive-bayes/
├── src/
│   ├── __init__.py
│   ├── naive_bayes.py          # 基类
│   ├── gaussian_naive_bayes.py # 高斯变体
│   ├── multinomial_naive_bayes.py # 多项式变体
│   └── bernoulli_naive_bayes.py # 伯努利变体
├── tests/
│   └── test_*.py               # 测试文件
├── docs/                       # 文档
└── README.md
```

### 类设计

```
NaiveBayesClassifier (ABC)
├── fit(X, y) -> self
├── predict(X) -> list
├── predict_proba(X) -> list[dict]
├── score(X, y) -> float
└── _calculate_likelihood(x, class) -> float (abstract)

GaussianNaiveBayes
├── 继承 NaiveBayesClassifier
├── 存储: means, variances
└── 似然: 高斯概率密度函数

MultinomialNaiveBayes
├── 继承 NaiveBayesClassifier
├── 存储: feature_log_prob
└── 似然: 多项式分布

BernoulliNaiveBayes
├── 继承 NaiveBayesClassifier
├── 存储: feature_log_prob
└── 似然: 伯努利分布
```

### 数据流

```
训练阶段:
X, y -> fit() -> 计算先验概率 P(C)
              -> 计算似然参数 (均值/方差 或 特征概率)
              -> 存储模型参数

预测阶段:
X -> predict() -> 对每个样本:
               -> 对每个类别:
               -> 计算后验概率 P(C|X) = P(X|C) * P(C)
               -> 选择最大后验概率的类别
               -> 返回预测结果
```

### 关键算法

#### 1. 贝叶斯计算

```python
# 对数空间计算避免下溢
log P(C|X) = log P(X|C) + log P(C) - log P(X)

# 由于 log P(X) 对所有类别相同，简化为:
log P(C|X) ∝ log P(X|C) + log P(C)
```

#### 2. 概率估计

**高斯分布**:
```
log P(xi|C) = -0.5 * log(2πσ²) - (xi-μ)² / (2σ²)
```

**多项式分布**:
```
log P(xi|C) = log(Nxi + α) - log(Nc + α*n_features)
```

**伯努利分布**:
```
log P(xi|C) = xi * log(p) + (1-xi) * log(1-p)
```

### 设计决策

1. **使用对数概率**: 避免连乘导致的下溢问题
2. **Laplace平滑**: 处理零概率问题
3. **抽象基类**: 统一接口，便于扩展
4. **类型注解**: 提高代码可读性
