# 02 - 设计文档

## 项目架构

### 整体结构

```
knn/
├── src/
│   ├── __init__.py
│   ├── knn_classifier.py      # KNN 分类器实现
│   └── distance_metrics.py    # 距离度量模块
├── tests/
│   ├── __init__.py
│   └── test_knn.py            # 测试用例
└── docs/
    └── ...                    # 文档
```

### 模块设计

#### 1. DistanceMetrics (距离度量模块)

**职责**：
- 实现各种距离计算方法
- 提供统一接口
- 处理边界情况

**接口设计**：

```python
class DistanceMetrics:
    """距离度量工具类"""

    @staticmethod
    def euclidean(x1, x2) -> float:
        """计算欧氏距离"""
        pass

    @staticmethod
    def manhattan(x1, x2) -> float:
        """计算曼哈顿距离"""
        pass

    @staticmethod
    def minkowski(x1, x2, p=2) -> float:
        """计算闵可夫斯基距离"""
        pass

    @staticmethod
    def cosine(x1, x2) -> float:
        """计算余弦相似度"""
        pass

    @staticmethod
    def get_metric(name: str):
        """根据名称获取距离函数"""
        pass
```

**设计考虑**：
- 使用静态方法，无需实例化
- 输入验证和错误处理
- 支持 NumPy 数组和列表输入

#### 2. KNNClassifier (KNN 分类器)

**职责**：
- 实现 KNN 分类算法
- 支持 fit/predict 接口
- 提供 K 值选择功能

**接口设计**：

```python
class KNNClassifier:
    """KNN 分类器"""

    def __init__(self, k=3, metric='euclidean'):
        """
        初始化分类器

        Args:
            k: 近邻数量
            metric: 距离度量方式
        """
        pass

    def fit(self, X, y):
        """
        训练模型（存储训练数据）

        Args:
            X: 训练特征矩阵 (n_samples, n_features)
            y: 训练标签 (n_samples,)
        """
        pass

    def predict(self, X):
        """
        预测新样本

        Args:
            X: 测试特征矩阵 (n_samples, n_features)

        Returns:
            predictions: 预测标签 (n_samples,)
        """
        pass

    def predict_proba(self, X):
        """
        预测概率

        Args:
            X: 测试特征矩阵 (n_samples, n_features)

        Returns:
            probabilities: 各类别的概率 (n_samples, n_classes)
        """
        pass

    def _vote(self, neighbor_labels):
        """
        投票机制

        Args:
            neighbor_labels: 近邻标签列表

        Returns:
            最终预测类别
        """
        pass

    def _compute_distances(self, x):
        """
        计算与所有训练样本的距离

        Args:
            x: 单个样本

        Returns:
            distances: 距离数组
        """
        pass
```

**核心算法流程**：

```
输入: 待分类样本 x, 训练集 (X_train, y_train), K 值

1. 计算距离:
   distances = [distance(x, x_i) for x_i in X_train]

2. 选择 K 个近邻:
   k_nearest_indices = argsort(distances)[:k]
   k_nearest_labels = y_train[k_nearest_indices]

3. 投票分类:
   prediction = mode(k_nearest_labels)

输出: 预测类别
```

### 类关系图

```
+---------------------+       +-------------------+
|   KNNClassifier     |------>|  DistanceMetrics  |
+---------------------+       +-------------------+
| - k: int            |       | + euclidean()     |
| - metric: str       |       | + manhattan()     |
| - X_train: ndarray  |       | + minkowski()     |
| - y_train: ndarray  |       | + cosine()        |
+---------------------+       +-------------------+
| + fit()             |
| + predict()         |
| + predict_proba()   |
+---------------------+
```

## 数据流设计

### 训练阶段

```
输入数据 (X, y)
     ↓
验证输入格式
     ↓
存储训练数据
     ↓
训练完成
```

### 预测阶段

```
测试样本 X_test
     ↓
循环处理每个样本:
  ├── 计算与所有训练样本的距离
  ├── 选择 K 个最近邻
  ├── 投票确定类别
  └── 记录预测结果
     ↓
返回预测结果
```

## 错误处理策略

### 输入验证

1. **X 格式验证**：
   - 确保是二维数组
   - 检查特征数量一致性

2. **y 格式验证**：
   - 确保是一维数组
   - 检查样本数量匹配

3. **K 值验证**：
   - 确保 K > 0
   - 确保 K <= 训练样本数量

4. **距离度量验证**：
   - 确保是支持的度量方式

### 异常处理

```python
# 输入验证示例
if X.ndim != 2:
    raise ValueError("X must be a 2D array")

if X.shape[0] != y.shape[0]:
    raise ValueError("X and y must have the same number of samples")

if self.k > len(self.X_train):
    raise ValueError("k must be less than or equal to number of training samples")
```

## 性能优化考虑

### 1. 向量化计算

使用 NumPy 广播机制计算距离：

```python
# 向量化欧氏距离
distances = np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))
```

### 2. 内存效率

- 避免不必要的数据复制
- 使用视图而非副本

### 3. 计算效率

- 预计算距离矩阵（批量预测时）
- 使用 `np.argpartition` 替代 `np.argsort`

## 扩展性设计

### 1. 新增距离度量

在 `DistanceMetrics` 类中添加新方法，并更新 `get_metric` 方法。

### 2. 新增权重策略

支持距离加权投票：

```python
def _weighted_vote(self, neighbor_labels, distances):
    """距离加权投票"""
    weights = 1 / (distances + 1e-8)  # 避免除零
    # ... 加权投票逻辑
```

### 3. 新增搜索算法

支持 KD 树等高效搜索算法。

## 测试策略

### 单元测试

- 距离计算准确性
- 输入验证
- 边界情况处理

### 集成测试

- 完整分类流程
- 不同参数组合
- 真实数据集测试

### 性能测试

- 大规模数据性能
- 内存使用情况

## 依赖管理

### 必需依赖

- `numpy`: 数值计算

### 可选依赖

- `pytest`: 测试框架
- `matplotlib`: 可视化（演示用）

## 总结

本设计遵循以下原则：

1. **单一职责**：每个模块专注于一个功能
2. **接口清晰**：提供直观的 API
3. **可扩展性**：易于添加新功能
4. **健壮性**：完善的错误处理
5. **性能优先**：使用向量化计算