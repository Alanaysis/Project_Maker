# 随机森林 (Random Forest)

从零实现随机森林分类器，深入理解集成学习的核心原理。

## 学习目标

- **理解 Bagging 原理**：Bootstrap Aggregating 如何通过有放回采样减少方差
- **掌握随机特征选择**：每次分裂时只考虑特征子集，增加树的多样性
- **学会集成学习**：通过多数投票将多个弱学习器组合成强学习器

## 核心循环

```
数据采样 → 决策树训练 → 集成 → 投票/平均
```

1. **数据采样 (Bagging)**：从训练集中有放回地随机采样，生成多个不同的子数据集
2. **决策树训练**：在每个子数据集上训练一棵决策树，每次分裂时随机选择特征子集
3. **集成**：收集所有训练好的决策树
4. **投票/平均**：对新样本，每棵树独立预测，最终结果通过多数投票决定

## 项目结构

```
random-forest/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py
│   ├── decision_tree.py        # 决策树实现
│   └── random_forest.py        # 随机森林实现
└── tests/
    ├── __init__.py
    ├── test_decision_tree.py    # 决策树测试
    └── test_random_forest.py    # 随机森林测试
```

## 快速开始

### 基本使用

```python
import numpy as np
from src import RandomForestClassifier

# 创建数据集
X = np.array([
    [1, 2], [3, 4], [5, 6], [7, 8],
    [2, 3], [4, 5], [6, 7], [8, 9]
])
y = np.array([0, 0, 1, 1, 0, 0, 1, 1])

# 创建随机森林分类器
rf = RandomForestClassifier(
    n_estimators=100,      # 100 棵树
    max_depth=5,           # 最大深度 5
    max_features="sqrt",   # 每次分裂考虑 sqrt(n_features) 个特征
    bootstrap=True,        # 使用 Bagging
    random_state=42        # 随机种子
)

# 训练
rf.fit(X, y)

# 预测
predictions = rf.predict([[3, 4], [6, 7]])
print(f"预测结果: {predictions}")

# 预测概率
probabilities = rf.predict_proba([[3, 4], [6, 7]])
print(f"预测概率: {probabilities}")

# 准确率
accuracy = rf.score(X, y)
print(f"训练准确率: {accuracy:.2%}")

# 特征重要性
print(f"特征重要性: {rf.feature_importances_}")

# 袋外分数 (OOB Score)
print(f"OOB 分数: {rf.oob_score_:.2%}")
```

### 与 scikit-learn 对比

```python
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier as SklearnRF
from src import RandomForestClassifier

# 生成数据
X, y = make_classification(n_samples=1000, n_features=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 我们的实现
our_rf = RandomForestClassifier(n_estimators=100, random_state=42)
our_rf.fit(X_train, y_train)
our_accuracy = our_rf.score(X_test, y_test)

# scikit-learn 实现
sklearn_rf = SklearnRF(n_estimators=100, random_state=42)
sklearn_rf.fit(X_train, y_train)
sklearn_accuracy = sklearn_rf.score(X_test, y_test)

print(f"我们的实现: {our_accuracy:.2%}")
print(f"scikit-learn: {sklearn_accuracy:.2%}")
```

## 核心算法

### 1. Bagging (Bootstrap Aggregating)

```python
def bootstrap_sample(X, y):
    n_samples = len(X)
    # 有放回采样
    indices = np.random.choice(n_samples, size=n_samples, replace=True)
    return X[indices], y[indices]
```

**原理**：通过有放回采样，每棵树看到的训练数据略有不同，减少了模型的方差。

### 2. 随机特征选择

```python
def select_features(n_features, max_features="sqrt"):
    if max_features == "sqrt":
        n_selected = int(np.sqrt(n_features))
    # 随机选择特征子集
    return np.random.choice(n_features, size=n_selected, replace=False)
```

**原理**：每次分裂时只考虑部分特征，增加了树之间的多样性，减少了过拟合。

### 3. 集成投票

```python
def majority_vote(predictions):
    # predictions: (n_trees, n_samples)
    from collections import Counter
    votes = Counter(predictions)
    return votes.most_common(1)[0][0]
```

**原理**：多数投票可以减少单棵树的错误，提高整体准确率。

## 关键概念

### 偏差-方差权衡

- **单棵决策树**：低偏差、高方差（容易过拟合）
- **随机森林**：通过集成多棵树，保持低偏差的同时显著降低方差

### 袋外数据 (Out-of-Bag)

- 每次 Bagging 采样约有 37% 的数据未被选中
- 这些数据可以用来评估模型性能，无需额外的验证集

### 特征重要性

- 基于每个特征在所有树中被用于分裂的次数
- 可以帮助理解哪些特征对预测最重要

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行决策树测试
pytest tests/test_decision_tree.py -v

# 运行随机森林测试
pytest tests/test_random_forest.py -v

# 运行测试并显示覆盖率
pytest tests/ -v --tb=short
```

## 参考资料

- [Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.](https://link.springer.com/article/10.1023/A:1010933404324)
- [scikit-learn RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- [Understanding Random Forests - Towards Data Science](https://towardsdatascience.com/understanding-random-forest-58381e0602d2)

## License

This project is for educational purposes.
