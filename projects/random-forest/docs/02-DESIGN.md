# 02 - 设计文档：随机森林

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                  RandomForestClassifier                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Tree 1    │  │   Tree 2    │  │   Tree N    │         │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │         │
│  │ │  Root   │ │  │ │  Root   │ │  │ │  Root   │ │         │
│  │ │ ┌──┬──┐ │ │  │ │ ┌──┬──┐ │ │  │ │ ┌──┬──┐ │ │         │
│  │ │ L  R  │ │  │ │ │ L  R  │ │  │ │ │ L  R  │ │         │
│  │ └──┴──┴──┘ │  │ └──┴──┴──┘ │  │ └──┴──┴──┘ │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│                   ┌─────────────┐                          │
│                   │  Majority   │                          │
│                   │    Vote     │                          │
│                   └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## 2. 类设计

### 2.1 DecisionTreeClassifier

```python
class DecisionTreeClassifier:
    """CART 决策树分类器"""

    # 属性
    max_depth: int              # 最大深度
    min_samples_split: int      # 最小分裂样本数
    min_samples_leaf: int       # 最小叶节点样本数
    criterion: str              # 分裂准则 ('gini' | 'entropy')
    max_features: Any           # 每次分裂考虑的特征数
    random_state: int           # 随机种子

    # 训练后属性
    root_: Node                 # 根节点
    n_features_: int            # 特征数
    n_classes_: int             # 类别数
    classes_: np.ndarray        # 类别标签
    feature_importances_: np.ndarray  # 特征重要性

    # 方法
    fit(X, y) -> self           # 训练
    predict(X) -> np.ndarray    # 预测
    score(X, y) -> float        # 准确率
    get_depth() -> int          # 树深度
    get_n_leaves() -> int       # 叶节点数
```

### 2.2 Node

```python
class Node:
    """决策树节点"""

    feature_index: int          # 分裂特征索引 (叶节点为 None)
    threshold: float            # 分裂阈值 (叶节点为 None)
    left: Node                  # 左子树 (samples <= threshold)
    right: Node                 # 右子树 (samples > threshold)
    value: Any                  # 预测值 (仅叶节点)
    samples: int                # 经过的样本数
    impurity: float             # 不纯度

    @property
    def is_leaf(self) -> bool   # 是否为叶节点
```

### 2.3 RandomForestClassifier

```python
class RandomForestClassifier:
    """随机森林分类器"""

    # 属性
    n_estimators: int           # 树的数量
    max_depth: int              # 每棵树的最大深度
    min_samples_split: int      # 最小分裂样本数
    min_samples_leaf: int       # 最小叶节点样本数
    max_features: Any           # 每次分裂考虑的特征数
    bootstrap: bool             # 是否使用 Bagging
    criterion: str              # 分裂准则
    random_state: int           # 随机种子

    # 训练后属性
    trees_: List[DecisionTreeClassifier]  # 所有树
    classes_: np.ndarray        # 类别标签
    n_classes_: int             # 类别数
    n_features_: int            # 特征数
    feature_importances_: np.ndarray  # 特征重要性
    oob_score_: float           # 袋外分数

    # 方法
    fit(X, y) -> self           # 训练
    predict(X) -> np.ndarray    # 预测 (多数投票)
    predict_proba(X) -> np.ndarray  # 预测概率
    score(X, y) -> float        # 准确率
```

## 3. 核心算法设计

### 3.1 训练流程

```python
def fit(X, y):
    """
    训练流程：
    1. 验证输入数据
    2. 初始化随机数生成器
    3. 对每棵树：
       a. 创建 bootstrap 样本 (如果 bootstrap=True)
       b. 创建决策树
       c. 训练决策树
    4. 计算特征重要性
    5. 计算 OOB 分数 (如果 bootstrap=True)
    """
```

### 3.2 预测流程

```python
def predict(X):
    """
    预测流程：
    1. 验证模型已训练
    2. 对每棵树：
       a. 获取预测结果
    3. 对每个样本：
       a. 收集所有树的预测
       b. 多数投票得到最终预测
    """
```

### 3.3 Bagging 采样

```python
def bootstrap_sample(X, y):
    """
    1. 生成 n_samples 个随机索引 (有放回)
    2. 返回采样后的数据和 OOB 索引
    """
    n_samples = len(X)
    indices = rng.choice(n_samples, size=n_samples, replace=True)
    oob_indices = set(range(n_samples)) - set(indices)
    return X[indices], y[indices], oob_indices
```

### 3.4 随机特征选择

```python
def select_features(n_features, max_features):
    """
    根据 max_features 策略选择特征子集：
    - 'sqrt': sqrt(n_features)
    - 'log2': log2(n_features)
    - int: 直接使用
    - float: 比例
    """
```

### 3.5 最佳分裂

```python
def find_best_split(X, y, feature_indices):
    """
    1. 对每个选定的特征：
       a. 获取所有唯一值作为候选阈值
       b. 对每个阈值：
          - 计算信息增益
          - 更新最佳分裂
    2. 返回最佳特征、阈值、增益
    """
```

## 4. 数据结构设计

### 4.1 树的存储

使用链表结构存储决策树：
- 每个节点包含指向左右子树的指针
- 叶节点存储预测值
- 内部节点存储分裂特征和阈值

### 4.2 特征重要性

```python
# 基于不纯度减少的特征重要性
importance[feature] += n_samples * (parent_impurity - child_impurity)

# 归一化
importances /= sum(importances)
```

### 4.3 OOB 预测

```python
# 使用字典记录每个样本的 OOB 预测
oob_predictions = {i: [] for i in range(n_samples)}

# 对每棵树，预测未被采样的样本
for tree_idx, tree in enumerate(trees):
    oob_indices = get_oob_indices(tree_idx)
    predictions = tree.predict(X[oob_indices])
    for idx, pred in zip(oob_indices, predictions):
        oob_predictions[idx].append(pred)

# 对每个样本，取多数投票
final_oob_predictions = [majority_vote(oob_predictions[i]) for i in range(n_samples)]
```

## 5. 接口设计

### 5.1 输入格式

```python
# X: 特征矩阵
# shape: (n_samples, n_features)
# dtype: float64
X = np.array([[1.0, 2.0], [3.0, 4.0], ...])

# y: 目标标签
# shape: (n_samples,)
# dtype: int 或 float
y = np.array([0, 1, 0, 1, ...])
```

### 5.2 输出格式

```python
# predict: 预测标签
# shape: (n_samples,)
predictions = rf.predict(X)

# predict_proba: 预测概率
# shape: (n_samples, n_classes)
probabilities = rf.predict_proba(X)
```

### 5.3 参数验证

```python
def _validate_params(self):
    if self.n_estimators < 1:
        raise ValueError("n_estimators must be at least 1")
    if self.min_samples_split < 2:
        raise ValueError("min_samples_split must be at least 2")
    # ...
```

## 6. 错误处理

### 6.1 训练前验证

- 检查 X 和 y 的样本数是否一致
- 检查是否至少有 2 个类别
- 检查参数是否合法

### 6.2 预测前验证

- 检查模型是否已训练
- 检查输入特征数是否与训练时一致

## 7. 性能考虑

### 7.1 时间复杂度

- 训练：O(n_estimators * n_samples * n_features * log(n_samples))
- 预测：O(n_estimators * n_samples * tree_depth)

### 7.2 空间复杂度

- O(n_estimators * tree_size)

### 7.3 优化策略

- 使用 NumPy 向量化操作
- 避免不必要的数据复制
- 考虑使用并行训练（未来优化）

## 8. 扩展性设计

### 8.1 未来扩展

- 支持回归任务 (RandomForestRegressor)
- 支持并行训练 (n_jobs)
- 支持更多分裂准则
- 支持增量学习
- 支持特征重要性的置换方法
