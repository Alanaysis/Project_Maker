# 02 - 设计文档

## 项目架构

### 整体结构

```
knn/
├── src/
│   ├── __init__.py
│   ├── knn_classifier.py      # KNN 分类器实现
│   ├── knn_regressor.py       # KNN 回归器实现
│   ├── distance_metrics.py    # 距离度量模块
│   ├── kd_tree.py             # KD-Tree 加速结构
│   ├── ball_tree.py           # Ball Tree 加速结构
│   └── model_selection.py     # 模型选择工具
├── tests/
│   ├── __init__.py
│   └── test_*.py              # 测试用例
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

    @staticmethod
    def manhattan(x1, x2) -> float:
        """计算曼哈顿距离"""

    @staticmethod
    def minkowski(x1, x2, p=2) -> float:
        """计算闵可夫斯基距离"""

    @staticmethod
    def cosine(x1, x2) -> float:
        """计算余弦相似度"""

    @staticmethod
    def cosine_distance(x1, x2) -> float:
        """计算余弦距离"""

    @staticmethod
    def get_metric(name: str):
        """根据名称获取距离函数"""
```

**设计考虑**：
- 使用静态方法，无需实例化
- 输入验证和错误处理
- 支持 NumPy 数组和列表输入

#### 2. KNNClassifier (KNN 分类器)

**职责**：
- 实现 KNN 分类算法
- 支持 fit/predict 接口
- 支持多数投票和距离加权投票
- 提供概率预测

**接口设计**：

```python
class KNNClassifier:
    """KNN 分类器"""

    def __init__(self, k=3, metric='euclidean', weights='uniform'):
        """
        初始化分类器

        Args:
            k: 近邻数量
            metric: 距离度量方式
            weights: 权重策略 ('uniform' 或 'distance')
        """

    def fit(self, X, y):
        """训练模型（存储训练数据）"""

    def predict(self, X):
        """预测新样本"""

    def predict_proba(self, X):
        """预测概率"""

    def _vote(self, neighbor_labels):
        """多数投票"""

    def _weighted_vote(self, neighbor_labels, distances):
        """距离加权投票"""
```

**核心算法流程**：

```
输入: 待分类样本 x, 训练集 (X_train, y_train), K 值, 权重策略

1. 计算距离:
   distances = [distance(x, x_i) for x_i in X_train]

2. 选择 K 个近邻:
   k_nearest_indices = argsort(distances)[:k]
   k_nearest_labels = y_train[k_nearest_indices]
   k_nearest_distances = distances[k_nearest_indices]

3. 投票分类:
   IF weights == 'uniform':
       prediction = mode(k_nearest_labels)
   ELSE:  # distance
       weights = 1 / distances
       prediction = argmax(Σ weight_i * I(y_i == c))

输出: 预测类别
```

#### 3. KNNRegressor (KNN 回归器)

**职责**：
- 实现 KNN 回归算法
- 支持简单平均和距离加权平均
- 提供 R² 评分

**接口设计**：

```python
class KNNRegressor:
    """KNN 回归器"""

    def __init__(self, k=5, metric='euclidean', weights='uniform'):
        """
        初始化回归器

        Args:
            k: 近邻数量
            metric: 距离度量方式
            weights: 权重策略 ('uniform' 或 'distance')
        """

    def fit(self, X, y):
        """训练模型"""

    def predict(self, X):
        """预测新样本"""

    def _simple_average(self, values):
        """简单平均"""

    def _weighted_average(self, values, distances):
        """距离加权平均"""
```

**回归预测公式**：

```
简单平均: y_pred = (1/K) * Σ y_i

距离加权平均: y_pred = Σ(w_i * y_i) / Σ w_i
    其中 w_i = 1 / d(x, x_i)
```

#### 4. KDTree (KD-Tree)

**职责**：
- 构建 KD-Tree 数据结构
- 提供高效的最近邻搜索
- 支持半径搜索

**接口设计**：

```python
class KDTree:
    """KD-Tree 数据结构"""

    def __init__(self, metric='euclidean'):
        """初始化 KD-Tree"""

    def build(self, X, y):
        """构建树"""

    def query(self, point, k=1):
        """查询 K 个最近邻"""

    def query_radius(self, point, radius):
        """查询半径内的所有点"""
```

**建树算法**：

```
BUILD(point_list, depth):
    IF point_list 为空:
        RETURN NULL

    axis = depth MOD k  // 选择分割维度
    sorted_list = SORT point_list BY axis
    median = LENGTH(sorted_list) / 2

    node = NEW Node(sorted_list[median])
    node.left = BUILD(sorted_list[0:median], depth + 1)
    node.right = BUILD(sorted_list[median+1:], depth + 1)

    RETURN node
```

**搜索算法**：

```
SEARCH(node, target, k, best_list):
    IF node 为空:
        RETURN

    dist = DISTANCE(target, node.point)
    ADD (dist, node) TO best_list
    KEEP ONLY k CLOSEST IN best_list

    IF target[axis] < node.point[axis]:
        first, second = node.left, node.right
    ELSE:
        first, second = node.right, node.left

    SEARCH(first, target, k, best_list)

    IF |target[axis] - node.point[axis]| < max_dist IN best_list:
        SEARCH(second, target, k, best_list)
```

#### 5. BallTree (Ball Tree)

**职责**：
- 构建 Ball Tree 数据结构
- 支持任意距离度量
- 提供高效的最近邻搜索

**接口设计**：

```python
class BallTree:
    """Ball Tree 数据结构"""

    def __init__(self, metric='euclidean', leaf_size=10):
        """初始化 Ball Tree"""

    def build(self, X, y):
        """构建树"""

    def query(self, point, k=1):
        """查询 K 个最近邻"""

    def query_radius(self, point, radius):
        """查询半径内的所有点"""
```

**建树算法**：

```
BUILD(point_list):
    center = MEAN(point_list)
    radius = MAX(DISTANCE(p, center) FOR p IN point_list)

    IF LENGTH(point_list) <= leaf_size:
        RETURN LeafNode(center, radius, point_list)

    seed1, seed2 = SELECT_SEEDS(point_list)  // 选择两个最远点
    left_points, right_points = PARTITION(point_list, seed1, seed2)

    node = BallNode(center, radius)
    node.left = BUILD(left_points)
    node.right = BUILD(right_points)

    RETURN node
```

#### 6. ModelSelection (模型选择)

**职责**：
- K-Fold 交叉验证
- K 值选择
- 训练/测试划分
- 评分函数

**接口设计**：

```python
class KFold:
    """K 折交叉验证"""

    def __init__(self, n_splits=5, shuffle=True, random_state=None):
        """初始化"""

    def split(self, X):
        """生成训练/验证索引对"""


class CrossValidator:
    """交叉验证器"""

    def cross_val_score(self, estimator, X, y, scoring=None):
        """交叉验证评分"""

    def select_k(self, X, y, k_range, metric, task):
        """选择最优 K 值"""


def train_test_split(X, y, test_size=0.2, random_state=None):
    """划分训练集和测试集"""

def accuracy_score(y_true, y_pred):
    """计算准确率"""

def mean_squared_error(y_true, y_pred):
    """计算均方误差"""

def r2_score(y_true, y_pred):
    """计算 R² 决定系数"""
```

### 类关系图

```
+---------------------+       +-------------------+
|   KNNClassifier     |------>|  DistanceMetrics  |
+---------------------+       +-------------------+
| - k: int            |       | + euclidean()     |
| - metric: str       |       | + manhattan()     |
| - weights: str      |       | + minkowski()     |
| - X_train: ndarray  |       | + cosine()        |
| - y_train: ndarray  |       +-------------------+
+---------------------+
| + fit()             |
| + predict()         |
| + predict_proba()   |
+---------------------+

+---------------------+       +-------------------+
|   KNNRegressor      |------>|  DistanceMetrics  |
+---------------------+       +-------------------+
| - k: int            |
| - metric: str       |
| - weights: str      |
+---------------------+
| + fit()             |
| + predict()         |
| + score()           |
+---------------------+

+---------------------+       +-------------------+
|   KNNClassifier     |------>|  KDTree / BallTree|
+---------------------+       +-------------------+
| (可选使用加速结构)    |       | + build()         |
|                     |       | + query()         |
+---------------------+       +-------------------+

+---------------------+
|   CrossValidator    |
+---------------------+
| - n_folds: int      |
| - shuffle: bool     |
+---------------------+
| + cross_val_score() |
| + select_k()        |
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
[可选] 构建加速结构 (KD-Tree / Ball Tree)
     ↓
训练完成
```

### 预测阶段

```
测试样本 X_test
     ↓
循环处理每个样本:
  ├── 计算与所有训练样本的距离（或使用加速结构）
  ├── 选择 K 个最近邻
  ├── 投票/平均确定预测值
  │   ├── uniform: 多数投票 / 简单平均
  │   └── distance: 距离加权投票 / 距离加权平均
  └── 记录预测结果
     ↓
返回预测结果
```

### 交叉验证流程

```
数据集 (X, y)
     ↓
K-Fold 划分
     ↓
For each fold:
  ├── 训练集 → 训练模型
  ├── 验证集 → 评估模型
  └── 记录分数
     ↓
汇总结果（均值、标准差）
     ↓
返回评估结果
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

5. **权重策略验证**：
   - 确保是 'uniform' 或 'distance'

### 异常处理

```python
# 输入验证示例
if X.ndim != 2:
    raise ValueError("X must be a 2D array")

if X.shape[0] != y.shape[0]:
    raise ValueError("X and y must have the same number of samples")

if self.k > len(self.X_train):
    raise ValueError("k must be less than or equal to number of training samples")

if weights not in ['uniform', 'distance']:
    raise ValueError("weights must be 'uniform' or 'distance'")
```

## 性能优化考虑

### 1. 向量化计算

使用 NumPy 广播机制计算距离：

```python
# 向量化欧氏距离
distances = np.sqrt(np.sum((self.X_train - x) ** 2, axis=1))

# 向量化曼哈顿距离
distances = np.sum(np.abs(self.X_train - x), axis=1)
```

### 2. 加速结构

- **KD-Tree**：适合低维数据（d < 20）
- **Ball Tree**：适合高维数据和非欧氏距离

### 3. 内存效率

- 避免不必要的数据复制
- 使用视图而非副本

### 4. 计算效率

- 预计算距离矩阵（批量预测时）
- 使用 `np.argpartition` 替代 `np.argsort`（仅需 K 个最近邻）

## 扩展性设计

### 1. 新增距离度量

在 `DistanceMetrics` 类中添加新方法，并更新 `get_metric` 方法。

### 2. 新增权重策略

支持自定义权重函数：

```python
def _weighted_vote(self, neighbor_labels, distances, weight_func=None):
    """自定义权重投票"""
    if weight_func is None:
        weights = 1 / (distances + 1e-8)
    else:
        weights = weight_func(distances)
    # ... 加权投票逻辑
```

### 3. 新增搜索算法

支持 LSH（局部敏感哈希）等近似搜索算法。

## 测试策略

### 单元测试

- 距离计算准确性
- 输入验证
- 边界情况处理
- 加权投票正确性

### 集成测试

- 完整分类/回归流程
- 不同参数组合
- 真实数据集测试

### 性能测试

- 大规模数据性能
- 加速结构效果对比

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
5. **性能优先**：使用向量化计算和加速结构
