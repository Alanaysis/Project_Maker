# 学习笔记

## KNN 算法核心概念

### 1. 算法原理

KNN (K-Nearest Neighbors) 是一种基于实例的学习算法，核心思想是：

**"近朱者赤，近墨者黑"**

- 如果一个样本在特征空间中的 K 个最近邻居大多数属于某个类别，则该样本也属于这个类别

### 2. 工作流程

```
输入: 待分类样本 x
  ↓
计算距离: d(x, x_i) for all x_i in training set
  ↓
选择 K 近邻: 找到距离最小的 K 个样本
  ↓
投票分类: 统计 K 个近邻的类别，选择出现次数最多的
  ↓
输出: 预测类别
```

### 3. 关键要素

#### K 值选择

**K 太小 (如 K=1)**：
- 模型复杂
- 容易过拟合
- 对噪声敏感

**K 太大 (如 K=N)**：
- 模型简单
- 容易欠拟合
- 预测偏向多数类

**最佳实践**：
- 使用交叉验证选择 K
- 通常取奇数（避免平票）
- K 通常在 3-10 之间

#### 距离度量

**欧氏距离**：
```
d(x, y) = sqrt(Σ(xi - yi)²)
```
- 最常用
- 适用于连续数值
- 对异常值敏感

**曼哈顿距离**：
```
d(x, y) = Σ|xi - yi|
```
- 网格状路径
- 对异常值不敏感
- 适用于高维数据

**余弦相似度**：
```
similarity = (x·y) / (||x|| * ||y||)
```
- 衡量方向相似性
- 适用于文本分类
- 不受向量长度影响

## 实现要点

### 1. 输入验证

```python
# 验证输入格式
if X.ndim != 2:
    raise ValueError("X must be a 2D array")

if y.ndim != 1:
    raise ValueError("y must be a 1D array")

if X.shape[0] != y.shape[0]:
    raise ValueError("X and y must have the same number of samples")
```

**为什么重要**：
- 避免运行时错误
- 提供清晰的错误信息
- 确保数据格式正确

### 2. 向量化计算

```python
# 低效实现（Python 循环）
distances = []
for x_train in self.X_train:
    dist = np.sqrt(np.sum((x - x_train) ** 2))
    distances.append(dist)

# 高效实现（NumPy 向量化）
distances = np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))
```

**为什么高效**：
- 利用 NumPy 底层 C 实现
- 减少 Python 解释器开销
- 内存访问优化

### 3. 投票机制

```python
def _vote(self, neighbor_labels):
    # 统计各类别出现次数
    unique_labels, counts = np.unique(neighbor_labels, return_counts=True)

    # 返回出现次数最多的类别
    return unique_labels[np.argmax(counts)]
```

**平票处理**：
- 返回第一个出现的类别
- 可以使用距离加权避免平票

### 4. 概率预测

```python
def predict_proba(self, X):
    # 计算每个类别的概率
    proba = np.zeros(len(self.classes_))
    for i, cls in enumerate(self.classes_):
        proba[i] = np.sum(k_nearest_labels == cls) / self.k

    return proba
```

**概率意义**：
- 概率 = 该类别近邻数 / K
- 概率和为 1
- 可用于评估预测置信度

## 常见问题

### 1. 维度灾难

**问题**：高维数据中，距离计算变得不准确

**原因**：高维空间中，所有点之间的距离趋于相等

**解决方案**：
- 特征选择
- 降维处理（PCA、t-SNE）
- 使用其他算法

### 2. 计算效率

**问题**：预测时需要计算与所有样本的距离

**时间复杂度**：O(n * d * k)

**优化方法**：
- KD 树：O(d * n * log n)
- Ball 树：适用于高维数据
- LSH：近似最近邻搜索

### 3. 特征缩放

**问题**：不同特征的尺度不同，距离计算会被大尺度特征主导

**解决方案**：
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

### 4. 不平衡数据

**问题**：多数类样本数量远大于少数类，预测偏向多数类

**解决方案**：
- 距离加权投票
- 过采样/欠采样
- 调整类别权重

## 实际应用

### 1. 手写数字识别

```python
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

# 加载数据
digits = load_digits()
X, y = digits.data, digits.target

# 划分数据集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)

# 训练 KNN
knn = KNNClassifier(k=5, metric='euclidean')
knn.fit(X_train, y_train)

# 预测
predictions = knn.predict(X_test)
accuracy = np.mean(predictions == y_test)
print(f"准确率: {accuracy:.2%}")
```

### 2. 推荐系统

```python
# 基于用户相似度的推荐
def recommend_items(user_id, k=5):
    # 计算用户之间的相似度
    user_features = get_user_features(user_id)
    similarities = compute_similarities(user_features, all_user_features)

    # 找到最相似的 K 个用户
    k_nearest_users = get_k_nearest(similarities, k)

    # 推荐这些用户喜欢的物品
    recommended_items = get_popular_items(k_nearest_users)

    return recommended_items
```

### 3. 异常检测

```python
def detect_anomalies(data, k=5, threshold=0.8):
    # 计算每个点的 K 近邻平均距离
    avg_distances = []
    for point in data:
        distances = compute_distances(point, data)
        k_nearest_distances = np.sort(distances)[:k]
        avg_distances.append(np.mean(k_nearest_distances))

    # 标记异常点
    anomalies = avg_distances > np.percentile(avg_distances, threshold * 100)

    return anomalies
```

## 学习资源

### 书籍

1. **《机器学习实战》** - Peter Harrington
   - 第 2 章：KNN 算法详解
   - 包含实际代码示例

2. **《统计学习方法》** - 李航
   - 第 3 章：K 近邻法
   - 理论推导详细

### 在线资源

1. **scikit-learn 官方文档**
   - https://scikit-learn.org/stable/modules/neighbors.html
   - 包含完整 API 和示例

2. **Khan Academy - 机器学习**
   - 适合初学者
   - 概念讲解清晰

### 实践项目

1. **Kaggle 竞赛**
   - 手写数字识别
   - 房价预测

2. **个人项目**
   - 图像分类器
   - 推荐系统原型

## 总结

### 关键学习点

1. **KNN 原理**：基于距离的分类方法
2. **距离度量**：欧氏、曼哈顿、余弦等
3. **K 值选择**：交叉验证、奇数原则
4. **性能优化**：向量化、KD 树
5. **实际应用**：分类、推荐、异常检测

### 实践建议

1. **先理解原理**：不要急于实现，先理解算法思想
2. **逐步实现**：从简单功能开始，逐步完善
3. **测试驱动**：先写测试，再写实现
4. **文档记录**：记录学习过程和遇到的问题
5. **持续优化**：不断优化代码和算法

### 下一步学习

1. **深入学习**：KD 树、Ball 树实现
2. **扩展应用**：回归任务、多输出任务
3. **比较学习**：与其他分类算法对比
4. **实际项目**：应用到真实数据集