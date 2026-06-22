# K-Means 聚类学习笔记

## 1. 聚类原理

### 1.1 什么是聚类

聚类是一种无监督学习方法，目标是将数据集划分为若干个组（簇），使得同一组内的数据点相似度较高，不同组的数据点相似度较低。

### 1.2 聚类类型

- **划分聚类**：K-Means、K-Medoids
- **层次聚类**：凝聚聚类、分裂聚类
- **密度聚类**：DBSCAN
- **模型聚类**：高斯混合模型

### 1.3 K-Means 算法

K-Means 是最常用的划分聚类算法，核心思想是：

1. **初始化**：随机选择 K 个点作为初始簇中心
2. **分配**：将每个数据点分配到距离最近的簇中心
3. **更新**：重新计算每个簇的中心（均值）
4. **收敛**：重复步骤 2-3 直到中心不再变化

## 2. 距离度量

### 2.1 欧氏距离

最常用的距离度量，适用于连续数值特征。

**公式**：
```
d(x, y) = sqrt(Σ(xi - yi)²)
```

**特点**：
- 对异常值敏感
- 各维度权重相同
- 适用于球形簇

**代码实现**：
```python
def euclidean_distance(x, y):
    return np.sqrt(np.sum((x - y) ** 2))
```

### 2.2 曼哈顿距离

也称为城市街区距离，适用于网格状数据。

**公式**：
```
d(x, y) = Σ|xi - yi|
```

**特点**：
- 对异常值不敏感
- 计算简单
- 适用于高维数据

**代码实现**：
```python
def manhattan_distance(x, y):
    return np.sum(np.abs(x - y))
```

### 2.3 余弦距离

衡量向量方向的差异，适用于文本数据。

**公式**：
```
cosine_similarity = (x·y) / (||x|| * ||y||)
cosine_distance = 1 - cosine_similarity
```

**特点**：
- 忽略向量大小
- 适用于高维稀疏数据
- 对尺度不敏感

**代码实现**：
```python
def cosine_distance(x, y):
    dot_product = np.dot(x, y)
    norm_x = np.linalg.norm(x)
    norm_y = np.linalg.norm(y)
    return 1 - dot_product / (norm_x * norm_y)
```

## 3. 肘部法则

### 3.1 原理

肘部法则用于选择最优的 K 值。核心思想是：

1. 计算不同 K 值对应的 WCSS（簇内平方和）
2. 绘制 K-WCSS 曲线
3. 选择曲线的"肘部"作为最优 K

### 3.2 WCSS 计算

**公式**：
```
WCSS = Σ Σ ||x - μi||²
       i x∈Ci
```

其中：
- Ci 是第 i 个簇
- μi 是第 i 个簇的中心

**代码实现**：
```python
def compute_wcss(X, labels, centroids):
    wcss = 0.0
    for k in range(n_clusters):
        cluster_points = X[labels == k]
        distances = np.sqrt(np.sum((cluster_points - centroids[k]) ** 2, axis=1))
        wcss += np.sum(distances ** 2)
    return wcss
```

### 3.3 最优 K 选择

**肘部法则步骤**：
1. 计算 K=1 到 K=max_k 的 WCSS
2. 绘制 K-WCSS 曲线
3. 找到曲线的拐点（肘部）

**代码实现**：
```python
def find_optimal_k_elbow(X, max_k=10):
    wcss_list = []
    for k in range(1, max_k + 1):
        kmeans = KMeans(n_clusters=k)
        kmeans.fit(X)
        wcss_list.append(kmeans.inertia_)

    # 使用二阶差分找拐点
    first_diff = np.diff(wcss_list)
    second_diff = np.diff(first_diff)
    optimal_k = np.argmax(second_diff) + 2

    return optimal_k, wcss_list
```

## 4. K-Means++ 初始化

### 4.1 问题

随机初始化可能导致：
- 收敛到局部最优
- 迭代次数增加
- 结果不稳定

### 4.2 解决方案

K-Means++ 初始化策略：

1. 随机选择第一个中心点
2. 对于每个后续中心点：
   - 计算每个点到最近中心的距离
   - 距离越大的点被选为新中心的概率越大
3. 重复直到选择 K 个中心点

### 4.3 优势

- 降低对初始值的敏感性
- 加速收敛
- 提高聚类质量

**代码实现**：
```python
def _init_centroids_kmeans_plus_plus(self, X):
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

## 5. 收敛判断

### 5.1 收敛条件

1. **中心点变化小于阈值**：
   ```python
   centroid_shift = np.max(np.linalg.norm(centroids - old_centroids, axis=1))
   if centroid_shift < self.tol:
       break
   ```

2. **达到最大迭代次数**：
   ```python
   if iteration >= self.max_iter - 1:
       break
   ```

3. **簇分配不再变化**：
   ```python
   if np.array_equal(labels, old_labels):
       break
   ```

### 5.2 参数选择

- **tol**：收敛阈值，通常设为 1e-4
- **max_iter**：最大迭代次数，通常设为 100-300

## 6. 性能优化

### 6.1 向量化计算

使用 NumPy 向量化操作避免显式循环：

```python
# 低效写法
for i in range(n_samples):
    for j in range(n_clusters):
        distances[i, j] = np.sqrt(np.sum((X[i] - centroids[j]) ** 2))

# 高效写法
distances = np.sqrt(np.sum((X[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2, axis=2))
```

### 6.2 广播机制

利用 NumPy 广播机制计算距离矩阵：

```python
# X 形状: (n_samples, n_features)
# centroids 形状: (n_clusters, n_features)

# 使用广播计算距离
XX = np.sum(X ** 2, axis=1)[:, np.newaxis]  # (n_samples, 1)
YY = np.sum(centroids ** 2, axis=1)[np.newaxis, :]  # (1, n_clusters)
distances = np.sqrt(np.maximum(XX + YY - 2 * np.dot(X, centroids.T), 0))
```

### 6.3 提前收敛判断

在每次迭代中检查收敛条件，避免不必要的计算。

## 7. 常见问题

### 7.1 如何选择 K 值？

- **肘部法则**：绘制 K-WCSS 曲线，选择拐点
- **轮廓系数**：评估簇的紧密度和分离度
- **Gap Statistic**：比较实际数据与随机数据的 WCSS
- **业务需求**：根据实际需求确定 K 值

### 7.2 如何处理异常值？

- 使用曼哈顿距离代替欧氏距离
- 在聚类前进行异常值检测和处理
- 使用 K-Medoids 算法（对异常值更鲁棒）

### 7.3 如何评估聚类效果？

- **轮廓系数**：衡量簇的紧密度和分离度
- **Calinski-Harabasz 指数**：衡量簇间分离度和簇内紧密度
- **Davies-Bouldin 指数**：衡量簇的相似度

### 7.4 K-Means 的局限性

- 需要预先指定 K 值
- 对初始值敏感
- 假设簇是球形的
- 对异常值敏感
- 只能发现凸形簇

## 8. 实践建议

### 8.1 数据预处理

- 标准化数据（Z-score）
- 处理缺失值
- 处理异常值

### 8.2 参数调优

- 尝试不同的 K 值
- 使用不同的距离度量
- 尝试不同的初始化方法

### 8.3 结果验证

- 可视化聚类结果
- 计算评估指标
- 业务专家验证

## 9. 学习资源

### 9.1 书籍

- 《机器学习》周志华
- 《Pattern Recognition and Machine Learning》
- 《Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow》

### 9.2 在线课程

- Coursera: Machine Learning (Andrew Ng)
- edX: Introduction to Machine Learning

### 9.3 实践平台

- Kaggle
- UCI Machine Learning Repository

## 10. 总结

通过本项目，我深入学习了 K-Means 聚类算法的原理和实现。关键收获包括：

1. **算法理解**：掌握了 K-Means 的核心思想和实现步骤
2. **距离度量**：学习了多种距离计算方法及其适用场景
3. **肘部法则**：掌握了选择最优 K 值的方法
4. **编程技能**：提高了 NumPy 向量化编程能力
5. **工程实践**：学习了项目结构设计和测试编写

这些知识和技能为后续的机器学习学习和应用奠定了坚实基础。