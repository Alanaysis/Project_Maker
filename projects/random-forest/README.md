# 随机森林 (Random Forest)

从零实现随机森林分类器和回归器，深入理解集成学习的核心原理。

## 学习目标

- **理解 Bagging 原理**：Bootstrap Aggregating 如何通过有放回采样减少方差
- **掌握随机特征选择**：每次分裂时只考虑特征子集，增加树的多样性
- **学会集成学习**：通过多数投票/平均将多个弱学习器组合成强学习器
- **回归与分类**：理解两种任务下随机森林的不同机制
- **特征重要性**：基于不纯度和基于排列两种方法的原理与对比
- **模型评估**：掌握分类和回归的各项评估指标

## 核心循环

```
数据采样 → 决策树训练 → 集成 → 投票/平均
```

1. **数据采样 (Bagging)**：从训练集中有放回地随机采样，生成多个不同的子数据集
2. **决策树训练**：在每个子数据集上训练一棵决策树，每次分裂时随机选择特征子集
3. **集成**：收集所有训练好的决策树
4. **投票/平均**：对新样本，每棵树独立预测，最终结果通过多数投票（分类）或平均（回归）决定

## 项目结构

```
random-forest/
├── README.md                           # 项目说明
├── LEARNING_NOTES.md                   # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md                 # 调研文档
│   ├── 02-DESIGN.md                   # 设计文档
│   ├── 03-IMPLEMENTATION.md           # 实现文档
│   ├── 04-TESTING.md                  # 测试文档
│   └── 05-DEVELOPMENT.md              # 开发文档
├── src/
│   ├── __init__.py
│   ├── decision_tree.py               # 决策树分类器
│   ├── random_forest.py               # 随机森林分类器
│   ├── random_forest_regressor.py     # 决策树回归器 + 随机森林回归器
│   └── evaluation.py                  # 评估指标模块
├── tests/
│   ├── __init__.py
│   ├── test_decision_tree.py          # 决策树测试 (21 tests)
│   ├── test_random_forest.py          # 随机森林分类器测试 (19 tests)
│   ├── test_random_forest_regressor.py # 回归器测试 (21 tests)
│   └── test_evaluation.py             # 评估指标测试 (42 tests)
└── examples/
    ├── iris_classification.py          # 鸢尾花分类实战
    ├── house_price_prediction.py       # 房价预测实战
    └── feature_importance_analysis.py  # 特征重要性分析
```

## 快速开始

### 随机森林分类

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

### 随机森林回归

```python
import numpy as np
from src.random_forest_regressor import RandomForestRegressor

# 创建回归数据集
np.random.seed(42)
X = np.random.randn(200, 3)
y = 3 * X[:, 0] + 2 * X[:, 1] + np.random.randn(200) * 0.2

# 创建随机森林回归器
rf_reg = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    max_features="sqrt",
    bootstrap=True,
    random_state=42,
)

rf_reg.fit(X, y)

# 预测
predictions = rf_reg.predict(X[:5])
print(f"预测值: {predictions}")
print(f"真实值: {y[:5]}")

# OOB R-squared
print(f"OOB R-squared: {rf_reg.oob_score_:.4f}")
```

### 模型评估

```python
from src.evaluation import (
    accuracy, precision_score, recall_score, f1_score,
    mean_squared_error, r2_score, permutation_importance,
    train_test_split, classification_report,
)

# 分类评估
y_true = np.array([0, 1, 1, 0, 1])
y_pred = np.array([0, 1, 0, 0, 1])

print(f"Accuracy:  {accuracy(y_true, y_pred):.4f}")
print(f"Precision: {precision_score(y_true, y_pred):.4f}")
print(f"Recall:    {recall_score(y_true, y_pred):.4f}")
print(f"F1-Score:  {f1_score(y_true, y_pred):.4f}")

# 回归评估
y_true_reg = np.array([100, 200, 300, 400, 500])
y_pred_reg = np.array([110, 190, 310, 380, 520])

print(f"MSE:  {mean_squared_error(y_true_reg, y_pred_reg):.2f}")
print(f"R2:   {r2_score(y_true_reg, y_pred_reg):.4f}")

# 排列重要性
perm_imp = permutation_importance(rf, X_test, y_test, n_repeats=20, random_state=42)
```

## 核心算法

### 1. Bagging (Bootstrap Aggregating)

```python
def bootstrap_sample(X, y):
    n_samples = len(X)
    # 有放回采样
    indices = np.random.choice(n_samples, size=n_samples, replace=True)
    # 约 37% 的数据未被选中 (OOB)
    oob_indices = set(range(n_samples)) - set(indices)
    return X[indices], y[indices], oob_indices
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

### 3. 集成投票/平均

```python
# 分类：多数投票
from collections import Counter
votes = Counter(predictions)
result = votes.most_common(1)[0][0]

# 回归：平均值
result = np.mean(predictions)
```

### 4. 特征重要性

```python
# 基于不纯度 (Impurity-based)
importance[feature] += n_samples * (parent_impurity - child_impurity)

# 基于排列 (Permutation-based)
baseline_score = score(model, X, y)
for feature in features:
    X_shuffled = shuffle_column(X, feature)
    importance[feature] = baseline_score - score(model, X_shuffled, y)
```

## 关键概念

### 偏差-方差权衡

- **单棵决策树**：低偏差、高方差（容易过拟合）
- **随机森林**：通过集成多棵树，保持低偏差的同时显著降低方差

### 袋外数据 (Out-of-Bag)

- 每次 Bagging 采样约有 37% 的数据未被选中
- 这些数据可以用来评估模型性能，无需额外的验证集
- OOB 分数是泛化误差的无偏估计

### 特征重要性

| 方法 | 优点 | 缺点 |
|------|------|------|
| 基于不纯度 | 计算快，训练时自动获得 | 偏向高基数特征 |
| 基于排列 | 模型无关，更可靠 | 计算慢，需要多次预测 |

## 运行测试

```bash
# 运行所有测试 (103 个测试)
pytest tests/ -v

# 运行决策树测试
pytest tests/test_decision_tree.py -v

# 运行随机森林分类器测试
pytest tests/test_random_forest.py -v

# 运行回归器测试
pytest tests/test_random_forest_regressor.py -v

# 运行评估指标测试
pytest tests/test_evaluation.py -v
```

## 运行示例

```bash
# 鸢尾花分类
python examples/iris_classification.py

# 房价预测
python examples/house_price_prediction.py

# 特征重要性分析
python examples/feature_importance_analysis.py
```

## 参考资料

- [Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.](https://link.springer.com/article/10.1023/A:1010933404324)
- [scikit-learn RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- [Understanding Random Forests - Towards Data Science](https://towardsdatascience.com/understanding-random-forest-58381e0602d2)

## License

This project is for educational purposes.

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
