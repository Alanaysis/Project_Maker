# 03 - 实现细节

## 距离度量实现

### 1. 欧氏距离 (Euclidean Distance)

```python
@staticmethod
def euclidean(x1, x2):
    """
    计算欧氏距离

    公式: d(x, y) = sqrt(Σ(xi - yi)²)
    """
    x1 = np.asarray(x1, dtype=float)
    x2 = np.asarray(x2, dtype=float)
    return float(np.sqrt(np.sum((x1 - x2) ** 2)))
```

**实现要点**：
- 使用 NumPy 向量化计算
- `np.sum` 按指定轴求和
- `np.sqrt` 计算平方根

### 2. 曼哈顿距离 (Manhattan Distance)

```python
@staticmethod
def manhattan(x1, x2):
    """
    计算曼哈顿距离

    公式: d(x, y) = Σ|xi - yi|
    """
    return float(np.sum(np.abs(x1 - x2)))
```

### 3. 闵可夫斯基距离 (Minkowski Distance)

```python
@staticmethod
def minkowski(x1, x2, p=2):
    """
    计算闵可夫斯基距离

    公式: d(x, y) = (Σ|xi - yi|^p)^(1/p)

    p=1: 曼哈顿距离
    p=2: 欧氏距离
    p=inf: 切比雪夫距离
    """
    if p == float('inf'):
        return float(np.max(np.abs(x1 - x2)))
    return float(np.sum(np.abs(x1 - x2) ** p) ** (1 / p))
```

### 4. 余弦距离 (Cosine Distance)

```python
@staticmethod
def cosine(x1, x2):
    """
    计算余弦相似度

    公式: similarity = (x·y) / (||x|| * ||y||)
    余弦距离 = 1 - similarity
    """
    dot_product = np.dot(x1, x2)
    norm_x1 = np.linalg.norm(x1)
    norm_x2 = np.linalg.norm(x2)

    if norm_x1 == 0 or norm_x2 == 0:
        return 0.0

    return float(dot_product / (norm_x1 * norm_x2))

@staticmethod
def cosine_distance(x1, x2):
    """余弦距离 = 1 - 余弦相似度"""
    return 1 - DistanceMetrics.cosine(x1, x2)
```

## KNN 分类器实现

### 初始化

```python
class KNNClassifier:
    def __init__(self, k=3, metric='euclidean', weights='uniform'):
        """
        初始化分类器

        Args:
            k: 近邻数量
            metric: 距离度量方式
            weights: 权重策略
                - 'uniform': 等权投票（多数投票）
                - 'distance': 距离加权投票
        """
        self.k = k
        self.metric = metric
        self.weights = weights
```

### 投票机制

#### 多数投票

```python
def _vote(self, neighbor_labels):
    """
    多数投票

    统计 K 个近邻中各类别出现次数，返回出现次数最多的类别。
    """
    unique_labels, counts = np.unique(neighbor_labels, return_counts=True)
    return unique_labels[np.argmax(counts)]
```

#### 距离加权投票

```python
def _weighted_vote(self, neighbor_labels, distances):
    """
    距离加权投票

    权重 = 1 / distance，距离越近权重越大。
    计算各类别的加权得分，返回得分最高的类别。
    """
    # 避免除零
    weights = np.where(distances == 0, 1e10, 1.0 / distances)

    # 计算各类别的加权得分
    weighted_scores = {}
    for label, weight in zip(neighbor_labels, weights):
        if label in weighted_scores:
            weighted_scores[label] += weight
        else:
            weighted_scores[label] = weight

    return max(weighted_scores, key=weighted_scores.get)
```

### 概率预测

```python
def _predict_proba_single(self, x):
    """
    预测单个样本的概率

    对于 'uniform' 权重：
        P(class) = count(class in K neighbors) / K

    对于 'distance' 权重：
        P(class) = Σ(1/d_i for neighbor i with class) / Σ(1/d_i)
    """
    distances = self._compute_distances(x)
    k_nearest_indices = np.argsort(distances)[:self.k]
    k_nearest_labels = self.y_train[k_nearest_indices]
    k_nearest_distances = distances[k_nearest_indices]

    probabilities = np.zeros(len(self.classes_))

    if self.weights == 'distance':
        weights = np.where(k_nearest_distances == 0, 1e10,
                           1.0 / k_nearest_distances)
        total_weight = np.sum(weights)
        for i, cls in enumerate(self.classes_):
            mask = k_nearest_labels == cls
            probabilities[i] = np.sum(weights[mask]) / total_weight
    else:
        for i, cls in enumerate(self.classes_):
            probabilities[i] = np.sum(k_nearest_labels == cls) / self.k

    return probabilities
```

### 距离计算优化

```python
def _compute_distances(self, x):
    """
    计算与所有训练样本的距离

    对欧氏距离和曼哈顿距离使用向量化计算，提高性能。
    """
    if self.metric == 'euclidean':
        # 向量化欧氏距离
        distances = np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))
    elif self.metric == 'manhattan':
        # 向量化曼哈顿距离
        distances = np.sum(np.abs(self.X_train - x), axis=1)
    elif self.metric == 'minkowski':
        distance_func = DistanceMetrics.get_metric('minkowski')
        distances = np.array([
            distance_func(x, x_train, p=2)
            for x_train in self.X_train
        ])
    else:
        distance_func = DistanceMetrics.get_metric(self.metric)
        distances = np.array([
            distance_func(x, x_train)
            for x_train in self.X_train
        ])

    return distances
```

## KNN 回归器实现

### 预测机制

#### 简单平均

```python
def _simple_average(self, values):
    """简单平均"""
    return float(np.mean(values))
```

#### 距离加权平均

```python
def _weighted_average(self, values, distances):
    """
    距离加权平均

    权重 = 1 / distance
    预测值 = Σ(w_i * y_i) / Σ(w_i)
    """
    # 避免除零
    weights = np.where(distances == 0, 1e10, 1.0 / distances)

    weighted_sum = np.sum(weights * values)
    weight_total = np.sum(weights)

    return float(weighted_sum / weight_total)
```

### R² 评分

```python
def score(self, X, y):
    """
    计算 R² 决定系数

    R² = 1 - SS_res / SS_tot
    其中:
        SS_res = Σ(y_true - y_pred)²
        SS_tot = Σ(y_true - mean(y_true))²
    """
    predictions = self.predict(X)
    ss_res = np.sum((y - predictions) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    if ss_tot == 0:
        return 0.0

    return float(1 - ss_res / ss_tot)
```

## KD-Tree 实现

### 建树算法

```python
def _build_recursive(self, X, y, indices, depth):
    """
    递归构建 KD-Tree

    1. 选择分割维度（循环选择）
    2. 按分割维度排序
    3. 选择中位数作为分割点
    4. 递归构建左右子树
    """
    if len(indices) == 0:
        return None

    # 选择分割维度
    axis = depth % self.n_features

    # 按分割维度排序
    sorted_idx = indices[np.argsort(X[indices, axis])]

    # 选择中位数
    median_idx = len(sorted_idx) // 2

    # 创建节点
    node = KDNode(
        point=X[sorted_idx[median_idx]].copy(),
        label=y[sorted_idx[median_idx]],
        axis=axis,
        depth=depth
    )

    # 递归构建子树
    node.left = self._build_recursive(X, y, sorted_idx[:median_idx], depth + 1)
    node.right = self._build_recursive(X, y, sorted_idx[median_idx + 1:], depth + 1)

    return node
```

### 搜索算法

```python
def _search_recursive(self, node, point, k, neighbors):
    """
    递归搜索最近邻

    1. 计算当前节点与查询点的距离
    2. 更新近邻列表
    3. 先搜索近侧子树
    4. 检查远侧子树是否可能包含更近的点
    """
    if node is None:
        return

    # 计算距离
    dist = self._distance(point, node.point)

    # 更新近邻列表
    neighbors.append((-dist, id(node), node.label))
    if len(neighbors) > k:
        neighbors.sort(key=lambda x: x[0])
        neighbors.pop()

    # 计算到分割超平面的距离
    plane_dist = abs(point[node.axis] - node.point[node.axis])

    # 确定搜索顺序
    if point[node.axis] < node.point[node.axis]:
        first, second = node.left, node.right
    else:
        first, second = node.right, node.left

    # 先搜索近侧
    self._search_recursive(first, point, k, neighbors)

    # 检查远侧
    max_dist = -neighbors[-1][0] if len(neighbors) >= k else float('inf')
    if len(neighbors) < k or plane_dist < max_dist:
        self._search_recursive(second, point, k, neighbors)
```

## Ball Tree 实现

### 建树算法

```python
def _build_recursive(self, indices):
    """
    递归构建 Ball Tree

    1. 计算质心和半径
    2. 如果数据量小于叶节点大小，创建叶节点
    3. 选择两个最远的点作为分裂种子
    4. 将数据点分配到最近的种子
    5. 递归构建左右子树
    """
    X_subset = self.X_train[indices]

    # 计算质心和半径
    center = np.mean(X_subset, axis=0)
    radius = np.max(self._batch_distances(X_subset, center))

    node = BallNode(center=center, radius=radius)

    # 叶节点
    if len(indices) <= self.leaf_size:
        node.is_leaf = True
        node.indices = indices.copy()
        return node

    # 选择分裂种子
    seed1, seed2 = self._select_seeds(X_subset)

    # 分配数据点
    dist_to_seed1 = self._batch_distances(X_subset, X_subset[seed1])
    dist_to_seed2 = self._batch_distances(X_subset, X_subset[seed2])
    left_mask = dist_to_seed1 <= dist_to_seed2

    # 递归构建
    node.left = self._build_recursive(indices[left_mask])
    node.right = self._build_recursive(indices[~left_mask])

    return node
```

### 种子选择

```python
def _select_seeds(self, X):
    """
    选择分裂种子（两个最远的点）

    使用两遍扫描的贪心算法：
    1. 选择离质心最远的点作为第一个种子
    2. 选择离第一个种子最远的点作为第二个种子
    """
    center = np.mean(X, axis=0)

    # 第一遍：找离质心最远的点
    dists_to_center = self._batch_distances(X, center)
    seed1 = np.argmax(dists_to_center)

    # 第二遍：找离第一个种子最远的点
    dists_to_seed1 = self._batch_distances(X, X[seed1])
    seed2 = np.argmax(dists_to_seed1)

    return int(seed1), int(seed2)
```

## 模型选择实现

### K-Fold 交叉验证

```python
class KFold:
    def split(self, X):
        """
        生成训练/验证索引对

        1. 生成索引数组
        2. 可选打乱
        3. 分成 K 份
        4. 轮流作为验证集
        """
        n_samples = X.shape[0]
        indices = np.arange(n_samples)

        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(indices)

        fold_size = n_samples // self.n_splits
        remainder = n_samples % self.n_splits

        splits = []
        start = 0
        for i in range(self.n_splits):
            current_fold_size = fold_size + (1 if i < remainder else 0)
            end = start + current_fold_size
            val_indices = indices[start:end]
            train_indices = np.concatenate([indices[:start], indices[end:]])
            splits.append((train_indices, val_indices))
            start = end

        return splits
```

### K 值选择

```python
def select_k(self, X, y, k_range, metric, task):
    """
    选择最优 K 值

    1. 对每个 K 值进行交叉验证
    2. 计算平均分数
    3. 返回最优 K 值
    """
    k_scores = {}
    for k in k_range:
        if task == 'classification':
            estimator = KNNClassifier(k=k, metric=metric)
        else:
            estimator = KNNRegressor(k=k, metric=metric, weights=weights)

        results = self.cross_val_score(estimator, X, y)
        k_scores[k] = results['mean_score']

    best_k = max(k_scores, key=k_scores.get)
    return {'best_k': best_k, 'best_score': k_scores[best_k], 'k_scores': k_scores}
```

## 性能优化

### 1. 向量化距离计算

```python
# 欧氏距离
distances = np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))

# 曼哈顿距离
distances = np.sum(np.abs(self.X_train - x), axis=1)
```

### 2. 加速结构选择

| 数据特点 | 推荐结构 | 原因 |
|---------|---------|------|
| 低维 (d < 20) | KD-Tree | 分割效率高 |
| 高维 (d >= 20) | Ball Tree | 对维度不敏感 |
| 非欧氏距离 | Ball Tree | 支持任意距离度量 |
| 大规模数据 | LSH | 近似搜索，速度快 |

### 3. 数值稳定性

```python
# 避免除零
weights = np.where(distances == 0, 1e10, 1.0 / distances)

# 避免数值溢出
log_probs = np.log(probabilities + 1e-10)
```

## 时间复杂度分析

### 暴力搜索

- **训练**: O(1)
- **预测**: O(n * d) per query

### KD-Tree

- **建树**: O(n log n)
- **查询**: O(log n) 平均，O(n) 最坏

### Ball Tree

- **建树**: O(n log n)
- **查询**: O(log n) 平均

## 总结

实现过程中的关键决策：

1. **接口设计**：遵循 scikit-learn 风格的 fit/predict 接口
2. **权重策略**：支持 uniform 和 distance 两种策略
3. **加速结构**：实现 KD-Tree 和 Ball Tree
4. **模型选择**：实现 K-Fold 交叉验证和 K 值选择
5. **数值稳定性**：处理除零、溢出等边界情况
