# 朴素贝叶斯分类器

从零实现朴素贝叶斯分类器，深入理解贝叶斯定理和概率分类。

## 学习目标

- 理解贝叶斯定理
- 掌握条件独立假设
- 学会概率计算
- 实现三种朴素贝叶斯变体

## 项目结构

```
naive-bayes/
├── src/
│   ├── __init__.py
│   ├── naive_bayes.py              # 基类
│   ├── gaussian_naive_bayes.py     # 高斯朴素贝叶斯
│   ├── multinomial_naive_bayes.py  # 多项式朴素贝叶斯
│   └── bernoulli_naive_bayes.py    # 伯努利朴素贝叶斯
├── tests/
│   ├── test_gaussian_naive_bayes.py
│   ├── test_multinomial_naive_bayes.py
│   └── test_bernoulli_naive_bayes.py
├── docs/
│   ├── 01-RESEARCH.md              # 市场调研
│   ├── 02-DESIGN.md                # 架构设计
│   ├── 03-IMPLEMENTATION.md        # 实现细节
│   ├── 04-TESTING.md               # 测试策略
│   └── 05-DEVELOPMENT.md           # 开发日志
├── LEARNING_NOTES.md               # 学习笔记
└── README.md
```

## 快速开始

### 安装

无需安装额外依赖，纯Python实现。

### 使用示例

#### 高斯朴素贝叶斯 (连续特征)

```python
from src import GaussianNaiveBayes

# 训练数据
X_train = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0],
           [10.0, 11.0], [11.0, 12.0], [12.0, 13.0]]
y_train = [0, 0, 0, 1, 1, 1]

# 创建并训练模型
clf = GaussianNaiveBayes()
clf.fit(X_train, y_train)

# 预测
predictions = clf.predict([[1.5, 2.5], [11.0, 12.0]])
print(predictions)  # [0, 1]

# 预测概率
probabilities = clf.predict_proba([[1.5, 2.5]])
print(probabilities)  # [{0: 0.99, 1: 0.01}, ...]

# 计算准确率
score = clf.score([[1.5, 2.5], [11.0, 12.0]], [0, 1])
print(score)  # 1.0
```

#### 多项式朴素贝叶斯 (文本分类)

```python
from src import MultinomialNaiveBayes

# 词频数据: [good, bad, great]
X_train = [[3, 0, 2], [2, 0, 3], [0, 3, 0], [0, 4, 0]]
y_train = [0, 0, 1, 1]  # 0: 正面, 1: 负面

clf = MultinomialNaiveBayes()
clf.fit(X_train, y_train)

# 预测
print(clf.predict([[3, 0, 2]]))  # [0] 正面
print(clf.predict([[0, 4, 0]]))  # [1] 负面
```

#### 伯努利朴素贝叶斯 (二值特征)

```python
from src import BernoulliNaiveBayes

# 二值数据: [是否包含word_a, 是否包含word_b]
X_train = [[1, 0], [1, 0], [0, 1], [0, 1]]
y_train = [0, 0, 1, 1]

clf = BernoulliNaiveBayes()
clf.fit(X_train, y_train)

# 预测
print(clf.predict([[1, 0]]))  # [0]
print(clf.predict([[0, 1]]))  # [1]
```

## 运行测试

```bash
cd projects/naive-bayes
python -m pytest tests/ -v
```

## 核心概念

### 贝叶斯定理

```
P(C|X) = P(X|C) * P(C) / P(X)
```

- P(C|X): 后验概率
- P(X|C): 似然
- P(C): 先验概率
- P(X): 证据

### 条件独立假设

```
P(X1, X2, ..., Xn | C) = P(X1|C) * P(X2|C) * ... * P(Xn|C)
```

### 三种变体

| 变体 | 适用数据 | 典型应用 |
|------|---------|---------|
| 高斯 | 连续特征 | 数值分类 |
| 多项式 | 计数特征 | 文本分类 |
| 伯努利 | 二值特征 | 文本分类 |

## 技术要点

1. **对数空间计算**: 避免数值下溢
2. **Laplace平滑**: 处理零概率
3. **log-sum-exp技巧**: 概率归一化

## 应用场景

1. **文本分类**: 垃圾邮件检测、情感分析
2. **推荐系统**: 用户兴趣分类
3. **医学诊断**: 疾病预测

## 参考资料

- 《机器学习》周志华
- 《统计学习方法》李航
- [scikit-learn Naive Bayes](https://scikit-learn.org/stable/modules/naive_bayes.html)
