# 03 - 实现细节

## 距离度量实现

### 1. 欧氏距离 (Euclidean Distance)

```python
@staticmethod
def euclidean(x1, x2):
    """
    计算欧氏距离

    公式: d(x, y) = sqrt(Σ(xi - yi)²)

    Args:
        x1, x2: 输入向量

    Returns:
        欧氏距离值
    """
    return np.sqrt(np.sum((x1 - x2) ** 2))
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

    Args:
        x1, x2: 输入向量

    Returns:
        曼哈顿距离值
    """
    return np.sum(np.abs(x1 - x2))
```

**实现要点**：
- `np.abs` 计算绝对值
- 适用于网格状路径

### 3. 闵可夫斯基距离 (Minkowski Distance)

```python
@staticmethod
def minkowski(x1, x2, p=2):
    """
    计算闵可夫斯基距离

    公式: d(x, y) = (Σ|xi - yi|^p)^(1/p)

    Args:
        x1, x2: 输入向量
        p: 距离参数 (p=1: 曼哈顿, p=2: 欧氏)

    Returns:
        闵可夫斯基距离值
    """
    return np.sum(np.abs(x1 - x2) ** p) ** (1 / p)
```

**实现要点**：
- 参数 `p` 控制距离类型
- `p=1` 时等价于曼哈顿距离
- `p=2` 时等价于欧氏距离

### 4. 余弦相似度 (Cosine Similarity)

```python
@staticmethod
def cosine(x1, x2):
    """
    计算余弦相似度

    公式: similarity = (x·y) / (||x|| * ||y||)

    Args:
        x1, x2: 输入向量

    Returns:
        余弦相似度值 (0 到 1)
    """
    dot_product = np.dot(x1, x2)
    norm_x1 = np.linalg.norm(x1)
    norm_x2 = np.linalg.norm(x2)

    # 避免除零
    if norm_x1 == 0 or norm_x2 == 0:
        return 0.0

    return dot_product / (norm_x1 * norm_x2)
```

**实现要点**：
- `np.dot` 计算点积
- `np.linalg.norm` 计算范数
- 处理零向量的边界情况

## KNN 分类器实现

### 初始化

```python
class KNNClassifier:
    """KNN 分类器"""

    def __init__(self, k=3, metric='euclidean'):
        """
        初始化分类器

        Args:
            k: 近邻数量 (默认: 3)
            metric: 距离度量方式 (默认: 'euclidean')
        """
        self.k = k
        self.metric = metric
        self.X_train = None
        self.y_train = None
        self.classes_ = None
```

**设计考虑**：
- K 默认值为 3（常用值）
- 支持多种距离度量
- 存储训练数据供预测使用

### 训练方法

```python
def fit(self, X, y):
    """
    训练模型（存储训练数据）

    Args:
        X: 训练特征矩阵 (n_samples, n_features)
        y: 训练标签 (n_samples,)

    Returns:
        self: 返回自身，支持链式调用
    """
    # 输入验证
    X = np.array(X)
    y = np.array(y)

    if X.ndim != 2:
        raise ValueError("X must be a 2D array")

    if y.ndim != 1:
        raise ValueError("y must be a 1D array")

    if X.shape[0] != y.shape[0]:
        raise ValueError("X and y must have the same number of samples")

    if self.k <= 0:
        raise ValueError("k must be positive")

    if self.k > X.shape[0]:
        raise ValueError("k must be less than or equal to number of training samples")

    # 存储训练数据
    self.X_train = X
    self.y_train = y
    self.classes_ = np.unique(y)

    return self
```

**实现要点**：
- 输入验证确保数据格式正确
- 存储训练数据供预测使用
- 记录所有类别用于概率计算

### 预测方法

```python
def predict(self, X):
    """
    预测新样本

    Args:
        X: 测试特征矩阵 (n_samples, n_features)

    Returns:
        predictions: 预测标签 (n_samples,)
    """
    # 检查是否已训练
    if self.X_train is None:
        raise RuntimeError("Model must be fitted before prediction")

    # 输入验证
    X = np.array(X)

    if X.ndim == 1:
        X = X.reshape(1, -1)

    if X.shape[1] != self.X_train.shape[1]:
        raise ValueError("Number of features must match training data")

    # 批量预测
    predictions = np.array([self._predict_single(x) for x in X])

    return predictions
```

**实现要点**：
- 检查模型是否已训练
- 支持单个样本和批量样本
- 使用列表推导式简化代码

### 单样本预测

```python
def _predict_single(self, x):
    """
    预测单个样本

    Args:
        x: 单个样本 (n_features,)

    Returns:
        prediction: 预测标签
    """
    # 计算距离
    distances = self._compute_distances(x)

    # 选择 K 个近邻
    k_nearest_indices = np.argsort(distances)[:self.k]
    k_nearest_labels = self.y_train[k_nearest_indices]

    # 投票分类
    prediction = self._vote(k_nearest_labels)

    return prediction
```

**实现要点**：
- `np.argsort` 返回排序后的索引
- 取前 K 个索引对应的标签
- 调用投票方法确定最终预测

### 距离计算

```python
def _compute_distances(self, x):
    """
    计算与所有训练样本的距离

    Args:
        x: 单个样本 (n_features,)

    Returns:
        distances: 距离数组 (n_samples,)
    """
    # 获取距离函数
    distance_func = DistanceMetrics.get_metric(self.metric)

    # 向量化计算
    if self.metric == 'minkowski':
        # 闵可夫斯基距离需要额外参数
        distances = np.array([
            distance_func(x, x_train, p=2)
            for x_train in self.X_train
        ])
    else:
        distances = np.array([
            distance_func(x, x_train)
            for x_train in self.X_train
        ])

    return distances
```

**实现要点**：
- 根据度量类型选择距离函数
- 使用列表推导式计算所有距离
- 处理需要额外参数的度量方式

### 投票机制

```python
def _vote(self, neighbor_labels):
    """
    投票机制（多数投票）

    Args:
        neighbor_labels: 近邻标签列表

    Returns:
        最终预测类别
    """
    # 统计各类别出现次数
    unique_labels, counts = np.unique(neighbor_labels, return_counts=True)

    # 返回出现次数最多的类别
    return unique_labels[np.argmax(counts)]
```

**实现要点**：
- `np.unique` 统计唯一值和出现次数
- `np.argmax` 返回最大值的索引
- 处理平票情况（取第一个出现的）

### 概率预测

```python
def predict_proba(self, X):
    """
    预测概率

    Args:
        X: 测试特征矩阵 (n_samples, n_features)

    Returns:
        probabilities: 各类别的概率 (n_samples, n_classes)
    """
    # 检查是否已训练
    if self.X_train is None:
        raise RuntimeError("Model must be fitted before prediction")

    # 输入验证
    X = np.array(X)

    if X.ndim == 1:
        X = X.reshape(1, -1)

    if X.shape[1] != self.X_train.shape[1]:
        raise ValueError("Number of features must match training data")

    # 计算概率
    probabilities = []
    for x in X:
        distances = self._compute_distances(x)
        k_nearest_indices = np.argsort(distances)[:self.k]
        k_nearest_labels = self.y_train[k_nearest_indices]

        # 统计各类别出现次数
        proba = np.zeros(len(self.classes_))
        for i, cls in enumerate(self.classes_):
            proba[i] = np.sum(k_nearest_labels == cls) / self.k

        probabilities.append(proba)

    return np.array(probabilities)
```

**实现要点**：
- 计算每个类别的概率
- 概率 = 该类别出现次数 / K
- 返回 (n_samples, n_classes) 形状的数组

## 关键算法优化

### 1. 向量化距离计算

```python
# 原始实现（逐样本计算）
distances = np.array([
    distance_func(x, x_train)
    for x_train in self.X_train
])

# 优化实现（向量化计算）
if self.metric == 'euclidean':
    distances = np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))
```

**优化效果**：
- 减少 Python 循环开销
- 利用 NumPy 底层优化
- 速度提升 10-100 倍

### 2. 高效 K 近邻选择

```python
# 原始实现（完全排序）
k_nearest_indices = np.argsort(distances)[:self.k]

# 优化实现（部分排序）
k_nearest_indices = np.argpartition(distances, self.k)[:self.k]
```

**优化效果**：
- `np.argpartition` 时间复杂度 O(n)
- `np.argsort` 时间复杂度 O(n log n)
- 大数据集时性能提升显著

### 3. 批量预测优化

```python
# 原始实现（逐样本预测）
predictions = np.array([self._predict_single(x) for x in X])

# 优化实现（批量距离计算）
# 一次性计算所有距离矩阵
distances = self._batch_compute_distances(X)
```

## 边界情况处理

### 1. 空数组处理

```python
if len(self.X_train) == 0:
    raise ValueError("Training data cannot be empty")
```

### 2. 零向量处理

```python
# 余弦相似度中的零向量
if norm_x1 == 0 or norm_x2 == 0:
    return 0.0
```

### 3. 平票处理

```python
# 当多个类别票数相同时
unique_labels, counts = np.unique(neighbor_labels, return_counts=True)
max_count = np.max(counts)
max_labels = unique_labels[counts == max_count]

# 返回第一个出现的（默认行为）
return max_labels[0]
```

### 4. 数值稳定性

```python
# 避免除零错误
weights = 1 / (distances + 1e-8)

# 避免数值溢出
log_probs = np.log(probabilities + 1e-10)
```

## 性能考虑

### 时间复杂度

- **训练**：O(1) - 仅存储数据
- **预测**：O(n * d * k) - n: 样本数, d: 特征数, k: 近邻数

### 空间复杂度

- **训练**：O(n * d) - 存储所有训练数据
- **预测**：O(n * k) - 存储距离和近邻索引

### 优化建议

1. **使用 KD 树**：适用于低维数据
2. **使用 Ball 树**：适用于高维数据
3. **使用 LSH**：适用于大规模数据
4. **并行计算**：多进程预测

## 测试策略

### 单元测试覆盖

1. **距离计算测试**
   - 验证各种距离计算正确性
   - 测试边界情况（零向量、相同向量）

2. **分类器测试**
   - 验证 fit/predict 流程
   - 测试不同 K 值
   - 测试不同距离度量

3. **错误处理测试**
   - 测试输入验证
   - 测试异常情况

### 集成测试

1. **鸢尾花数据集测试**
   - 验证分类准确率
   - 测试不同参数组合

2. **自定义数据集测试**
   - 线性可分数据
   - 非线性可分数据
   - 多分类数据

## 总结

实现过程中需要注意：

1. **输入验证**：确保数据格式正确
2. **边界处理**：处理各种特殊情况
3. **性能优化**：使用向量化计算
4. **代码清晰**：保持接口简洁直观
5. **测试覆盖**：确保代码质量