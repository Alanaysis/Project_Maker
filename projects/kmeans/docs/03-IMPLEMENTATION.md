# K-Means 聚类实现细节

## 1. 核心算法实现

### 1.1 算法流程

K-Means 聚类算法的核心流程如下：

```
1. 初始化：随机选择 K 个数据点作为初始簇中心
2. 分配：将每个数据点分配到距离最近的簇中心
3. 更新：重新计算每个簇的中心（均值）
4. 收敛判断：重复步骤 2-3 直到中心不再变化或达到最大迭代次数
```

### 1.2 代码实现

```python
def fit(self, X):
    """
    训练模型
    """
    # 验证输入
    X = self._validate_input(X)

    # 初始化簇中心
    centroids = self._init_centroids(X)

    # 迭代优化
    for iteration in range(self.max_iter):
        # 保存旧的中心点用于收敛判断
        old_centroids = centroids.copy()

        # 分配簇
        labels = self._assign_clusters(X, centroids)

        # 更新中心
        centroids = self._update_centroids(X, labels)

        # 收敛判断
        centroid_shift = np.max(np.linalg.norm(centroids - old_centroids, axis=1))

        if centroid_shift < self.tol:
            self.n_iter_ = iteration + 1
            break

    # 保存结果
    self.cluster_centers_ = centroids
    self.labels_ = labels
    self.inertia_ = self._compute_wcss(X, labels, centroids)

    return self
```

## 2. 距离度量实现

### 2.1 欧氏距离

```python
def euclidean_distance(x, y):
    """
    计算欧氏距离
    d(x, y) = sqrt(Σ(xi - yi)²)
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    # 处理单个向量
    if x.ndim == 1 and y.ndim == 1:
        return np.sqrt(np.sum((x - y) ** 2))

    # 处理矩阵（批量计算）
    if x.ndim == 2 and y.ndim == 1:
        return np.sqrt(np.sum((x - y) ** 2, axis=1))

    # ... 其他情况
```

### 2.2 曼哈顿距离

```python
def manhattan_distance(x, y):
    """
    计算曼哈顿距离
    d(x, y) = Σ|xi - yi|
    """
    # ... 实现类似欧氏距离
```

### 2.3 余弦距离

```python
def cosine_distance(x, y):
    """
    计算余弦距离
    d(x, y) = 1 - (x·y)/(||x|| * ||y||)
    """
    # ... 实现
```

## 3. 初始化方法

### 3.1 随机初始化

```python
def _init_centroids_random(self, X):
    """随机初始化簇中心"""
    n_samples = X.shape[0]
    rng = np.random.RandomState(self.random_state)
    indices = rng.choice(n_samples, self.n_clusters, replace=False)
    return X[indices].copy()
```

### 3.2 K-Means++ 初始化

```python
def _init_centroids_kmeans_plus_plus(self, X):
    """
    K-Means++ 初始化

    算法步骤:
    1. 随机选择第一个中心点
    2. 对于每个后续中心点，选择距离现有中心最远的点
    3. 使用概率分布选择，距离越远概率越大
    """
    n_samples, n_features = X.shape
    rng = np.random.RandomState(self.random_state)

    # 初始化中心数组
    centroids = np.empty((self.n_clusters, n_features))

    # 1. 随机选择第一个中心点
    first_idx = rng.randint(0, n_samples)
    centroids[0] = X[first_idx]

    # 2. 选择剩余中心点
    for k in range(1, self.n_clusters):
        # 计算每个点到最近中心的距离
        distances = np.min([self._distance_func(X, centroids[i])
                           for i in range(k)], axis=0)

        # 计算概率分布（距离越大，概率越大）
        probabilities = distances ** 2
        probabilities /= probabilities.sum()

        # 根据概率分布选择下一个中心点
        next_idx = rng.choice(n_samples, p=probabilities)
        centroids[k] = X[next_idx]

    return centroids
```

## 4. 簇分配实现

```python
def _assign_clusters(self, X, centroids):
    """
    分配簇

    将每个数据点分配到距离最近的簇中心
    """
    # 计算每个点到每个中心的距离
    if self.distance == 'euclidean':
        # 使用高效的向量化计算
        distances = pairwise_distances(X, centroids, metric='euclidean')
    else:
        distances = self._distance_func(X, centroids)

    # 分配到最近的中心
    labels = np.argmin(distances, axis=1)

    return labels
```

## 5. 中心更新实现

```python
def _update_centroids(self, X, labels):
    """
    更新簇中心

    计算每个簇的均值作为新的中心点
    """
    n_features = X.shape[1]
    centroids = np.empty((self.n_clusters, n_features))

    for k in range(self.n_clusters):
        # 获取属于当前簇的数据点
        cluster_points = X[labels == k]

        if len(cluster_points) > 0:
            # 计算均值作为新中心
            centroids[k] = np.mean(cluster_points, axis=0)
        else:
            # 如果簇为空，随机选择一个点作为中心
            rng = np.random.RandomState(self.random_state)
            centroids[k] = X[rng.randint(0, X.shape[0])]
            warnings.warn(f"簇 {k} 为空，随机重新初始化中心")

    return centroids
```

## 6. 收敛判断

```python
# 收敛判断
centroid_shift = np.max(np.linalg.norm(centroids - old_centroids, axis=1))

if centroid_shift < self.tol:
    self.n_iter_ = iteration + 1
    break
```

## 7. WCSS 计算

```python
def _compute_wcss(self, X, labels, centroids):
    """
    计算簇内平方和 (Within-Cluster Sum of Squares)
    """
    wcss = 0.0

    for k in range(self.n_clusters):
        # 获取属于当前簇的数据点
        cluster_points = X[labels == k]

        if len(cluster_points) > 0:
            # 计算每个点到中心的距离平方
            distances = self._distance_func(cluster_points, centroids[k])
            wcss += np.sum(distances ** 2)

    return wcss
```

## 8. 性能优化

### 8.1 向量化计算

使用 NumPy 的向量化操作避免显式循环：

```python
# 使用广播机制计算距离矩阵
distances = np.sqrt(np.sum((X[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2, axis=2))
```

### 8.2 高效距离计算

对于欧氏距离，使用以下优化：

```python
# 计算 ||x - y||^2 = ||x||^2 + ||y||^2 - 2 * x·y
XX = np.sum(X ** 2, axis=1)[:, np.newaxis]
YY = np.sum(Y ** 2, axis=1)[np.newaxis, :]
distances = np.sqrt(np.maximum(XX + YY - 2 * np.dot(X, Y.T), 0))
```

## 9. 错误处理

### 9.1 输入验证

```python
def _validate_input(self, X):
    """验证输入数据"""
    X = np.asarray(X, dtype=np.float64)

    if X.ndim == 1:
        X = X.reshape(-1, 1)

    if X.ndim != 2:
        raise ValueError("输入数据必须是 2D 数组")

    if np.any(np.isnan(X)):
        raise ValueError("输入数据包含 NaN")

    if np.any(np.isinf(X)):
        raise ValueError("输入数据包含 Inf")

    return X
```

### 9.2 参数验证

```python
# 验证 K 值
if self.n_clusters <= 0:
    raise ValueError("n_clusters 必须大于 0")
if self.n_clusters > n_samples:
    raise ValueError(f"n_clusters ({self.n_clusters}) 不能大于样本数 ({n_samples})")
```

## 10. 测试策略

### 10.1 单元测试

- 测试每个距离函数的正确性
- 测试初始化方法的随机性
- 测试簇分配的准确性
- 测试中心更新的正确性
- 测试收敛判断的准确性

### 10.2 集成测试

- 测试完整的聚类流程
- 测试不同参数组合
- 测试边界情况

### 10.3 性能测试

- 测试大数据集的处理能力
- 测试不同距离函数的性能
- 测试内存使用情况