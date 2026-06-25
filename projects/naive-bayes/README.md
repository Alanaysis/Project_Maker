# 朴素贝叶斯分类器

从零实现朴素贝叶斯分类器，深入理解贝叶斯定理和概率分类。

## 学习目标

- 理解贝叶斯定理
- 掌握条件独立假设
- 学会概率计算
- 实现三种朴素贝叶斯变体
- 掌握模型评估指标

## 项目结构

```
naive-bayes/
├── src/
│   ├── __init__.py
│   ├── naive_bayes.py              # 基类
│   ├── gaussian_naive_bayes.py     # 高斯朴素贝叶斯
│   ├── multinomial_naive_bayes.py  # 多项式朴素贝叶斯
│   ├── bernoulli_naive_bayes.py    # 伯努利朴素贝叶斯
│   └── evaluation.py              # 模型评估模块
├── tests/
│   ├── test_gaussian_naive_bayes.py
│   ├── test_multinomial_naive_bayes.py
│   ├── test_bernoulli_naive_bayes.py
│   └── test_evaluation.py
├── examples/
│   ├── spam_classification.py      # 垃圾邮件分类
│   ├── sentiment_analysis.py       # 文本情感分析
│   └── news_classification.py      # 新闻分类
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

#### 模型评估

```python
from src import GaussianNaiveBayes, evaluate_model, classification_report

# 训练模型
clf = GaussianNaiveBayes()
clf.fit(X_train, y_train)

# 预测
y_pred = clf.predict(X_test)

# 综合评估
results = evaluate_model(y_test, y_pred)
print(f"准确率: {results['accuracy']:.4f}")
print(f"F1分数: {results['f1_macro']:.4f}")

# 分类报告
print(classification_report(y_test, y_pred))

# 混淆矩阵
from src import confusion_matrix
matrix = confusion_matrix(y_test, y_pred)
```

## 运行测试

```bash
cd projects/naive-bayes

# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_evaluation.py -v
```

## 运行示例

```bash
cd projects/naive-bayes

# 垃圾邮件分类
python examples/spam_classification.py

# 文本情感分析
python examples/sentiment_analysis.py

# 新闻分类
python examples/news_classification.py
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
| 高斯 | 连续特征 | 数值分类、鸢尾花分类 |
| 多项式 | 计数特征 | 文本分类、情感分析 |
| 伯努利 | 二值特征 | 垃圾邮件检测、关键词匹配 |

### 模型评估指标

| 指标 | 公式 | 说明 |
|------|------|------|
| 准确率 | (TP+TN) / (TP+TN+FP+FN) | 正确预测比例 |
| 精确率 | TP / (TP+FP) | 预测为正的样本中真正为正的比例 |
| 召回率 | TP / (TP+FN) | 实际为正的样本中被正确预测的比例 |
| F1分数 | 2*P*R / (P+R) | 精确率和召回率的调和平均 |

## 技术要点

1. **对数空间计算**: 避免数值下溢
2. **Laplace平滑**: 处理零概率
3. **log-sum-exp技巧**: 概率归一化

## 应用场景

1. **垃圾邮件分类**: 伯努利朴素贝叶斯，检测邮件是否包含垃圾邮件关键词
2. **文本情感分析**: 多项式朴素贝叶斯，分析评论是正面还是负面
3. **新闻分类**: 多项式朴素贝叶斯，将新闻文章分类到不同主题

## 参考资料

- 《机器学习》周志华
- 《统计学习方法》李航
- [scikit-learn Naive Bayes](https://scikit-learn.org/stable/modules/naive_bayes.html)
