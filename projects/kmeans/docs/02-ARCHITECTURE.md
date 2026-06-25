# K-Means 聚类项目架构设计

## 1. 项目结构

```
projects/kmeans/
├── README.md              # 项目说明
├── docs/                  # 文档目录
│   ├── 01-RESEARCH.md     # 调研报告
│   ├── 02-ARCHITECTURE.md # 架构设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md      # 测试说明
│   └── 05-DEVELOPMENT.md  # 开发记录
├── src/                   # 源代码
│   ├── __init__.py
│   ├── kmeans.py          # 核心算法 (KMeans, MiniBatchKMeans)
│   ├── distance.py        # 距离度量
│   ├── visualization.py   # 可视化工具
│   └── utils.py           # 工具函数和评估指标
├── examples/              # 实际应用示例
│   ├── image_color_compression.py  # 图像颜色压缩
│   ├── customer_segmentation.py    # 客户分群
│   └── clustering_visualization.py # 聚类可视化
├── tests/                 # 测试代码
│   ├── __init__.py
│   ├── test_kmeans.py     # 核心算法测试
│   ├── test_distance.py   # 距离度量测试
│   └── test_visualization.py # 可视化测试
└── LEARNING_NOTES.md      # 学习笔记
```

## 2. 模块设计

### 2.1 距离度量模块 (distance.py)

**职责**：提供多种距离计算方法

**接口设计**：
```python
def euclidean_distance(x, y):
    """计算欧氏距离"""

def manhattan_distance(x, y):
    """计算曼哈顿距离"""

def cosine_distance(x, y):
    """计算余弦距离"""
```

**设计原则**：
- 每个函数接受两个向量，返回标量距离
- 使用 NumPy 向量化操作提高性能
- 支持批量计算

### 2.2 核心算法模块 (kmeans.py)

**职责**：实现 K-Means 聚类算法

**类设计**：
```python
class KMeans:
    def __init__(self, n_clusters=3, max_iter=100, tol=1e-4, distance='euclidean',
                 init='random', random_state=None):
        """初始化参数"""

    def fit(self, X):
        """训练模型"""

    def predict(self, X):
        """预测簇标签"""

    def fit_predict(self, X):
        """训练并预测"""

class MiniBatchKMeans:
    def __init__(self, n_clusters=3, batch_size=100, max_iter=100, tol=1e-4,
                 init='random', random_state=None, n_init=1):
        """初始化参数"""

    def fit(self, X):
        """训练模型（使用小批量数据）"""

    def predict(self, X):
        """预测簇标签"""

    def fit_predict(self, X):
        """训练并预测"""
```

**属性**：
- `cluster_centers_`：簇中心坐标
- `labels_`：每个样本的簇标签
- `inertia_`：簇内平方和
- `n_iter_`：实际迭代次数

**方法**：
- `_init_centroids(X)`：初始化簇中心
- `_assign_clusters(X, centroids)`：分配簇
- `_update_centroids(X, labels)`：更新簇中心
- `_compute_wcss(X, labels, centroids)`：计算 WCSS
- `_get_mini_batch(X, rng)`：获取小批量数据（MiniBatchKMeans）

### 2.3 可视化模块 (visualization.py)

**职责**：提供聚类结果可视化

**接口设计**：
```python
def plot_clusters(X, labels, centroids, title="K-Means Clustering"):
    """绘制聚类结果"""

def plot_elbow(wcss_list, title="Elbow Method"):
    """绘制肘部法则图"""

def plot_2d_clusters(X, labels, centroids):
    """2D 聚类可视化"""

def plot_3d_clusters(X, labels, centroids):
    """3D 聚类可视化"""
```

### 2.4 工具模块 (utils.py)

**职责**：提供辅助功能和评估指标

**接口设计**：
```python
def generate_clustered_data(n_samples=300, n_clusters=4, n_features=2, random_state=None):
    """生成聚类测试数据"""

def normalize_data(X):
    """数据标准化"""

def compute_wcss(X, labels, centroids):
    """计算簇内平方和"""

def compute_silhouette_score_fast(X, labels):
    """计算轮廓系数（优化版本）"""

def compute_calinski_harabasz(X, labels):
    """计算 Calinski-Harabasz 指数"""

def evaluate_clustering(X, labels, method='all'):
    """综合评估聚类结果"""

def find_optimal_k_elbow(X, k_range=None, max_k=10, distance='euclidean', random_state=None):
    """使用肘部法则寻找最优 K 值"""
```

## 3. 数据流

```
输入数据 X
    ↓
初始化簇中心 (K-Means++ 或随机)
    ↓
迭代循环:
    ├── 分配簇 (计算距离，分配最近中心)
    ├── 更新中心 (计算簇均值)
    └── 收敛判断 (中心变化 < tol 或 max_iter)
    ↓
输出结果 (labels_, cluster_centers_, inertia_)
```

## 4. 依赖关系

### 4.1 外部依赖
- `numpy`：数值计算
- `matplotlib`：可视化

### 4.2 内部依赖
- `visualization.py` 依赖 `distance.py`
- `kmeans.py` 依赖 `distance.py`
- `utils.py` 独立

## 5. 错误处理

### 5.1 输入验证
- 检查数据维度一致性
- 检查 K 值合理性 (0 < K ≤ n_samples)
- 检查距离函数有效性

### 5.2 异常情况
- K=0 或 K > n_samples：抛出 ValueError
- 数据包含 NaN：抛出 ValueError
- 收敛失败：记录警告，返回当前结果

## 6. 性能考虑

### 6.1 计算复杂度

**标准 K-Means**：
- 时间复杂度：O(n * K * d * max_iter)
- 空间复杂度：O(n * d + K * d)

**Mini-Batch K-Means**：
- 时间复杂度：O(batch_size * K * d * max_iter)
- 空间复杂度：O(batch_size * d + K * d)

### 6.2 优化策略
- 使用 NumPy 向量化
- 提前收敛判断
- 批量处理大数据集
- 增量更新中心点（Mini-Batch）
- 预计算距离矩阵（评估指标）

## 7. 扩展性

### 7.1 可扩展功能
- 支持更多距离度量
- 支持 K-Means++ 初始化
- 支持 Mini-Batch K-Means
- 支持并行计算

### 7.2 接口兼容性
- 遵循 Scikit-learn API 风格
- 支持 fit/predict 模式