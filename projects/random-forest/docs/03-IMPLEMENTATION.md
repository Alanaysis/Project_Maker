# 03 - 实现文档：随机森林

## 1. 实现概述

本文档详细说明随机森林的实现细节，包括决策树和随机森林的核心代码。

## 2. 决策树实现

### 2.1 节点类 (Node)

```python
class Node:
    """决策树节点"""

    def __init__(self, feature_index=None, threshold=None,
                 left=None, right=None, value=None,
                 samples=0, impurity=0.0):
        self.feature_index = feature_index  # 分裂特征索引
        self.threshold = threshold          # 分裂阈值
        self.left = left                    # 左子树
        self.right = right                  # 右子树
        self.value = value                  # 叶节点预测值
        self.samples = samples              # 样本数
        self.impurity = impurity            # 不纯度

    @property
    def is_leaf(self):
        return self.value is not None
```

**设计要点**：
- 使用链表结构存储树
- 叶节点只设置 `value`，内部节点设置 `feature_index` 和 `threshold`
- 记录 `samples` 和 `impurity` 用于计算特征重要性

### 2.2 不纯度计算

#### Gini 不纯度

```python
def _gini(self, y):
    """
    Gini = 1 - sum(p_i^2)

    例如：二分类 [0, 0, 1, 1]
    p0 = 0.5, p1 = 0.5
    Gini = 1 - (0.5^2 + 0.5^2) = 0.5
    """
    counts = np.bincount(y.astype(int))
    probabilities = counts / len(y)
    return 1.0 - np.sum(probabilities ** 2)
```

#### 信息熵

```python
def _entropy(self, y):
    """
    Entropy = -sum(p_i * log2(p_i))

    例如：二分类 [0, 0, 1, 1]
    Entropy = -(0.5 * log2(0.5) + 0.5 * log2(0.5)) = 1.0
    """
    counts = np.bincount(y.astype(int))
    probabilities = counts / len(y)
    probabilities = probabilities[probabilities > 0]
    return -np.sum(probabilities * np.log2(probabilities))
```

### 2.3 信息增益

```python
def _information_gain(self, y, left_y, right_y):
    """
    IG = impurity(parent) - weighted_avg(impurity(left), impurity(right))
    """
    n = len(y)
    parent_impurity = self._impurity(y)
    left_weight = len(left_y) / n
    right_weight = len(right_y) / n
    child_impurity = (left_weight * self._impurity(left_y) +
                      right_weight * self._impurity(right_y))
    return parent_impurity - child_impurity
```

### 2.4 最佳分裂查找

```python
def _find_best_split(self, X, y, feature_indices):
    """
    对每个特征：
    1. 获取所有唯一值
    2. 计算相邻值的中点作为候选阈值
    3. 对每个阈值计算信息增益
    4. 返回最佳分裂
    """
    best_gain = 0.0
    best_feature = None
    best_threshold = None

    for feature_idx in feature_indices:
        values = np.unique(X[:, feature_idx])
        thresholds = (values[:-1] + values[1:]) / 2.0

        for threshold in thresholds:
            left_mask = X[:, feature_idx] <= threshold
            right_mask = ~left_mask

            # 检查最小样本约束
            if (np.sum(left_mask) < self.min_samples_leaf or
                np.sum(right_mask) < self.min_samples_leaf):
                continue

            gain = self._information_gain(y, y[left_mask], y[right_mask])

            if gain > best_gain:
                best_gain = gain
                best_feature = feature_idx
                best_threshold = threshold

    return best_feature, best_threshold, best_gain
```

**实现细节**：
- 使用中点作为阈值可以减少计算量
- 检查 `min_samples_leaf` 约束
- 使用向量化操作提高效率

### 2.5 树构建

```python
def _build_tree(self, X, y, depth=0):
    """
    递归构建决策树：

    1. 检查停止条件：
       - 达到最大深度
       - 节点纯度为 0
       - 样本数小于 min_samples_split

    2. 选择特征子集

    3. 查找最佳分裂

    4. 如果找不到有效分裂，创建叶节点

    5. 分裂数据，递归构建左右子树
    """
    n_samples, n_features = X.shape
    impurity = self._impurity(y)
    class_counts = Counter(y)
    majority_class = class_counts.most_common(1)[0][0]

    # 停止条件
    is_pure = len(class_counts) == 1
    max_depth_reached = self.max_depth is not None and depth >= self.max_depth
    too_few_samples = n_samples < self.min_samples_split

    if is_pure or max_depth_reached or too_few_samples:
        return Node(value=majority_class, samples=n_samples, impurity=impurity)

    # 随机特征选择
    selected_features = self._select_features(n_features)

    # 查找最佳分裂
    best_feature, best_threshold, best_gain = self._find_best_split(
        X, y, selected_features
    )

    if best_feature is None or best_gain <= 0:
        return Node(value=majority_class, samples=n_samples, impurity=impurity)

    # 分裂
    left_mask = X[:, best_feature] <= best_threshold
    right_mask = ~left_mask

    left_subtree = self._build_tree(X[left_mask], y[left_mask], depth + 1)
    right_subtree = self._build_tree(X[right_mask], y[right_mask], depth + 1)

    return Node(
        feature_index=best_feature,
        threshold=best_threshold,
        left=left_subtree,
        right=right_subtree,
        samples=n_samples,
        impurity=impurity,
    )
```

### 2.6 特征重要性

```python
def _compute_feature_importances(self, node, importances):
    """
    递归计算特征重要性：

    importance[feature] += n_samples * (parent_impurity - child_impurity)
    """
    if node.is_leaf or node.feature_index is None:
        return

    n = node.samples
    left_n = node.left.samples if node.left else 0
    right_n = node.right.samples if node.right else 0

    weighted_child_impurity = (
        (left_n / n) * (node.left.impurity if node.left else 0) +
        (right_n / n) * (node.right.impurity if node.right else 0)
    )

    importance = n * (node.impurity - weighted_child_impurity)
    importances[node.feature_index] += importance

    self._compute_feature_importances(node.left, importances)
    self._compute_feature_importances(node.right, importances)
```

## 3. 随机森林实现

### 3.1 Bagging 采样

```python
def _bootstrap_sample(self, X, y):
    """
    Bagging 采样：

    1. 生成 n_samples 个随机索引 (有放回)
    2. 计算 OOB 索引
    3. 返回采样数据和 OOB 索引
    """
    n_samples = len(X)
    indices = self._rng.choice(n_samples, size=n_samples, replace=True)

    # 计算 OOB 索引
    all_indices = set(range(n_samples))
    selected_indices = set(indices)
    oob_indices = np.array(sorted(all_indices - selected_indices))

    return X[indices], y[indices], oob_indices
```

**关键点**：
- 使用 `replace=True` 实现有放回采样
- OOB 约占 36.8% 的样本
- 使用 `self._rng` 确保可重复性

### 3.2 训练流程

```python
def fit(self, X, y):
    """
    训练随机森林：

    1. 验证输入
    2. 初始化 OOB 预测容器
    3. 对每棵树：
       a. 生成不同的随机种子
       b. 创建 bootstrap 样本
       c. 创建决策树
       d. 训练决策树
       e. 累积 OOB 预测
    4. 计算特征重要性
    5. 计算 OOB 分数
    """
    # 初始化
    self.trees_ = []
    oob_predictions = np.zeros((len(X), self.n_classes_))
    oob_counts = np.zeros(len(X))

    for i in range(self.n_estimators):
        # 每棵树使用不同的随机种子
        tree_seed = self._rng.randint(0, 2**31)

        # Bagging 采样
        if self.bootstrap:
            X_sample, y_sample, oob_indices = self._bootstrap_sample(X, y)
        else:
            X_sample, y_sample = X, y
            oob_indices = np.array([])

        # 创建并训练决策树
        tree = DecisionTreeClassifier(
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            criterion=self.criterion,
            max_features=self.max_features,
            random_state=tree_seed,
        )
        tree.fit(X_sample, y_sample)
        self.trees_.append(tree)

        # 累积 OOB 预测
        if self.bootstrap and len(oob_indices) > 0:
            oob_preds = tree.predict(X[oob_indices])
            for idx, pred in zip(oob_indices, oob_preds):
                class_idx = np.searchsorted(self.classes_, pred)
                oob_predictions[idx, class_idx] += 1
                oob_counts[idx] += 1

    # 计算特征重要性 (平均)
    self.feature_importances_ = np.zeros(self.n_features_)
    for tree in self.trees_:
        if tree.feature_importances_ is not None:
            self.feature_importances_ += tree.feature_importances_
    self.feature_importances_ /= self.n_estimators

    # 计算 OOB 分数
    oob_mask = oob_counts > 0
    if np.any(oob_mask):
        oob_pred_classes = self.classes_[
            np.argmax(oob_predictions[oob_mask], axis=1)
        ]
        self.oob_score_ = np.mean(oob_pred_classes == y[oob_mask])
```

### 3.3 多数投票预测

```python
def predict(self, X):
    """
    多数投票预测：

    1. 收集所有树的预测
    2. 对每个样本，统计每个类别的票数
    3. 返回票数最多的类别
    """
    # 收集所有树的预测
    all_predictions = np.array([tree.predict(X) for tree in self.trees_])
    # shape: (n_estimators, n_samples)

    # 多数投票
    predictions = np.empty(n_samples, dtype=self.classes_.dtype)
    for i in range(n_samples):
        votes = all_predictions[:, i]
        vote_counts = Counter(votes)
        predictions[i] = vote_counts.most_common(1)[0][0]

    return predictions
```

### 3.4 概率预测

```python
def predict_proba(self, X):
    """
    概率预测：

    返回每个类别的得票比例
    """
    all_predictions = np.array([tree.predict(X) for tree in self.trees_])

    proba = np.zeros((n_samples, self.n_classes_))
    for i in range(n_samples):
        votes = all_predictions[:, i]
        for j, cls in enumerate(self.classes_):
            proba[i, j] = np.sum(votes == cls) / self.n_estimators

    return proba
```

## 4. 关键实现细节

### 4.1 随机种子管理

```python
# 总体随机种子
self._rng = np.random.RandomState(random_state)

# 每棵树的随机种子
tree_seed = self._rng.randint(0, 2**31)
```

这确保了：
- 整体可重复性
- 每棵树有不同的随机性

### 4.2 OOB 分数计算

```python
# 使用 OOB 预测计算泛化误差估计
oob_mask = oob_counts > 0
oob_pred_classes = self.classes_[np.argmax(oob_predictions[oob_mask], axis=1)]
self.oob_score_ = np.mean(oob_pred_classes == y[oob_mask])
```

OOB 分数是随机森林特有的验证方法，无需单独的验证集。

### 4.3 特征重要性平均

```python
# 每棵树的特征重要性相加后取平均
self.feature_importances_ = np.zeros(self.n_features_)
for tree in self.trees_:
    self.feature_importances_ += tree.feature_importances_
self.feature_importances_ /= self.n_estimators
```

## 5. 性能优化

### 5.1 NumPy 向量化

- 使用 `np.bincount` 计算类别分布
- 使用 `np.unique` 获取唯一值
- 使用布尔索引进行数据分裂

### 5.2 避免不必要的复制

- 使用视图而非复制
- 在可能的情况下使用原地操作

### 5.3 提前停止

- 检查纯度、深度、样本数等停止条件
- 避免不必要的分裂尝试

## 6. 测试策略

### 6.1 单元测试

- 测试不纯度计算的正确性
- 测试信息增益的计算
- 测试最佳分裂的查找
- 测试树的构建和预测

### 6.2 集成测试

- 测试 Bagging 采样的正确性
- 测试 OOB 分数的计算
- 测试特征重要性的计算
- 测试多数投票的正确性

### 6.3 边界测试

- 测试空数据
- 测试单类别数据
- 测试极端参数
