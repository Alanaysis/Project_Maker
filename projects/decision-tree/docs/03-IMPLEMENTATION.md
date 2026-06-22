# 03 - 决策树实现细节

## 1. 概述

本文档详细描述了决策树分类器的实现细节，包括核心算法、数据结构和关键实现决策。

## 2. 核心算法实现

### 2.1 信息增益计算

信息增益是决策树算法的核心，用于选择最佳分裂特征。

**实现步骤**：
1. 计算当前节点的熵（或基尼指数）
2. 对每个特征，计算所有可能分裂点的信息增益
3. 选择信息增益最大的特征和分裂点

**代码实现**：
```python
def _find_best_split(self, X, y):
    n_samples, n_features = X.shape
    best_gain = -1
    best_feature = None
    best_threshold = None

    # 计算当前节点的纯度
    if self.criterion == 'entropy':
        current_impurity = self._entropy(y)
    else:  # gini
        current_impurity = self._gini(y)

    # 遍历所有特征
    for feature_index in range(n_features):
        thresholds = np.unique(X[:, feature_index])
        
        for threshold in thresholds:
            left_indices = X[:, feature_index] <= threshold
            right_indices = ~left_indices
            
            # 计算信息增益
            left_weight = np.sum(left_indices) / n_samples
            right_weight = np.sum(right_indices) / n_samples
            
            if self.criterion == 'entropy':
                left_impurity = self._entropy(y[left_indices])
                right_impurity = self._entropy(y[right_indices])
            else:
                left_impurity = self._gini(y[left_indices])
                right_impurity = self._gini(y[right_indices])
            
            gain = current_impurity - (left_weight * left_impurity + right_weight * right_impurity)
            
            if gain > best_gain:
                best_gain = gain
                best_feature = feature_index
                best_threshold = threshold

    return best_feature, best_threshold
```

### 2.2 熵计算

熵是信息论中衡量不确定性的指标。

**数学公式**：
$$H(D) = -\sum_{i=1}^{n} p_i \log_2(p_i)$$

**实现细节**：
- 使用`np.unique`计算每个类别的样本数
- 添加小常数`1e-10`避免对数计算中的零值
- 使用`np.log2`计算以2为底的对数

**代码实现**：
```python
def _entropy(self, y):
    _, counts = np.unique(y, return_counts=True)
    probabilities = counts / len(y)
    entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
    return entropy
```

### 2.3 基尼指数计算

基尼指数是另一种衡量数据不纯度的指标。

**数学公式**：
$$Gini(D) = 1 - \sum_{i=1}^{n} p_i^2$$

**实现细节**：
- 计算每个类别的概率
- 计算概率平方和
- 用1减去平方和

**代码实现**：
```python
def _gini(self, y):
    _, counts = np.unique(y, return_counts=True)
    probabilities = counts / len(y)
    gini = 1 - np.sum(probabilities ** 2)
    return gini
```

### 2.4 递归构建决策树

决策树的构建是一个递归过程。

**算法流程**：
1. 检查停止条件
2. 寻找最佳分裂特征
3. 根据最佳特征分裂数据集
4. 递归构建左右子树
5. 返回当前节点

**停止条件**：
- 达到最大深度
- 样本数小于最小分裂样本数
- 所有样本属于同一类别
- 没有有效的分裂特征

**代码实现**：
```python
def _build_tree(self, X, y, depth=0):
    n_samples, n_features = X.shape
    n_classes = len(np.unique(y))

    # 停止条件
    if (self.max_depth is not None and depth >= self.max_depth) or \
       n_samples < self.min_samples_split or \
       n_classes == 1:
        return TreeNode(value=self._most_common_label(y))

    # 寻找最佳分裂特征
    best_feature, best_threshold = self._find_best_split(X, y)

    if best_feature is None:
        return TreeNode(value=self._most_common_label(y))

    # 根据最佳特征和阈值分裂数据集
    left_indices = X[:, best_feature] <= best_threshold
    right_indices = ~left_indices

    # 检查分裂后的样本数是否满足最小叶节点要求
    if np.sum(left_indices) < self.min_samples_leaf or \
       np.sum(right_indices) < self.min_samples_leaf:
        return TreeNode(value=self._most_common_label(y))

    # 递归构建左右子树
    left_subtree = self._build_tree(X[left_indices], y[left_indices], depth + 1)
    right_subtree = self._build_tree(X[right_indices], y[right_indices], depth + 1)

    return TreeNode(feature_index=best_feature, threshold=best_threshold,
                   left=left_subtree, right=right_subtree)
```

## 3. 数据结构设计

### 3.1 TreeNode类

决策树的每个节点都由TreeNode类表示。

**属性**：
- `feature_index`: 分裂特征的索引
- `threshold`: 分裂阈值
- `left`: 左子树
- `right`: 右子树
- `value`: 叶节点的预测值

**方法**：
- `is_leaf_node()`: 判断是否为叶节点

**代码实现**：
```python
class TreeNode:
    def __init__(self, feature_index=None, threshold=None, left=None, right=None, value=None):
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value

    def is_leaf_node(self):
        return self.value is not None
```

### 3.2 DecisionTreeClassifier类

决策树分类器的主类。

**属性**：
- `root`: 树的根节点
- `max_depth`: 最大深度
- `min_samples_split`: 最小分裂样本数
- `min_samples_leaf`: 最小叶节点样本数
- `criterion`: 分裂标准
- `n_features`: 特征数量
- `n_classes`: 类别数量
- `classes`: 类别数组

**方法**：
- `fit(X, y)`: 训练模型
- `predict(X)`: 预测新数据
- `score(X, y)`: 计算准确率
- `get_params()`: 获取参数
- `print_tree()`: 打印树结构

## 4. 关键实现决策

### 4.1 分裂标准选择

支持两种分裂标准：
- **信息增益**（entropy）：ID3算法使用
- **基尼指数**（gini）：CART算法使用

默认使用信息增益，因为它是决策树算法中最经典的标准。

### 4.2 阈值选择策略

对于连续特征，使用以下策略选择阈值：
1. 获取特征的所有唯一值
2. 对每个唯一值作为阈值计算信息增益
3. 选择信息增益最大的阈值

这种方法简单有效，但对于大数据集可能较慢。

### 4.3 停止条件设计

设计了多个停止条件以防止过拟合：
- **最大深度**：限制树的深度
- **最小分裂样本数**：节点样本数少于此值时不再分裂
- **最小叶节点样本数**：叶节点的最小样本数
- **纯节点**：所有样本属于同一类别

### 4.4 预测机制

预测过程是树的遍历过程：
1. 从根节点开始
2. 如果当前节点是叶节点，返回预测值
3. 根据特征值选择左子树或右子树
4. 递归进行预测

## 5. 性能优化

### 5.1 向量化操作

使用NumPy的向量化操作代替循环，提高计算效率。

### 5.2 避免重复计算

在计算信息增益时，缓存当前节点的熵值，避免重复计算。

### 5.3 早期停止

在寻找最佳分裂时，如果找到完美分裂（信息增益为0），提前停止搜索。

## 6. 错误处理

### 6.1 输入验证

在训练和预测前验证输入数据：
- 检查数据类型
- 检查数据维度
- 检查样本数匹配

### 6.2 数值稳定性

- 添加小常数避免对数计算中的零值
- 处理标准差为零的情况

## 7. 扩展性设计

### 7.1 支持多种分裂标准

通过参数化设计，可以轻松添加新的分裂标准。

### 7.2 支持剪枝策略

预留了剪枝接口，可以添加预剪枝和后剪枝策略。

### 7.3 支持回归问题

当前实现仅支持分类问题，但可以通过修改叶节点的预测值（使用平均值）来支持回归问题。

## 8. 测试策略

### 8.1 单元测试

测试每个独立的功能模块，包括：
- TreeNode类
- DecisionTreeClassifier类
- 工具函数

### 8.2 集成测试

测试完整的训练和预测流程，确保各模块协同工作。

### 8.3 边界测试

测试边界条件和异常情况，包括：
- 极小数据集
- 极大数据集
- 高维数据集
- 单类别数据集

## 9. 总结

本文档详细描述了决策树分类器的实现细节，包括核心算法、数据结构、关键实现决策和性能优化。通过这些实现细节，可以深入理解决策树的工作原理，并为后续的优化和扩展提供基础。