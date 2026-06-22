# K-Means 聚类测试说明

## 1. 测试概述

本项目采用单元测试和集成测试相结合的方式，确保 K-Means 聚类算法的正确性和可靠性。

## 2. 测试结构

```
tests/
├── __init__.py              # 测试包初始化
├── test_kmeans.py           # 核心算法测试
├── test_distance.py         # 距离度量测试
└── test_visualization.py    # 可视化测试
```

## 3. 核心算法测试 (test_kmeans.py)

### 3.1 测试用例

#### 基本功能测试
- `test_basic_clustering`: 测试基本聚类功能
- `test_fit_predict_consistency`: 测试 fit 和 predict 的一致性
- `test_cluster_centers_shape`: 测试簇中心的形状
- `test_inertia_calculation`: 测试 WCSS 计算
- `test_convergence`: 测试收敛性

#### 参数测试
- `test_different_k_values`: 测试不同的 K 值
- `test_distance_metrics`: 测试不同的距离度量
- `test_init_methods`: 测试不同的初始化方法

#### 边界情况测试
- `test_single_cluster`: 测试单个簇
- `test_two_clusters`: 测试两个簇
- `test_large_k`: 测试较大的 K 值
- `test_high_dimensional_data`: 测试高维数据

#### 错误处理测试
- `test_input_validation`: 测试输入验证
- `test_nan_handling`: 测试 NaN 处理

### 3.2 测试方法

```python
def test_basic_clustering(self):
    """测试基本聚类功能"""
    kmeans = KMeans(n_clusters=4, random_state=42)
    labels = kmeans.fit_predict(self.X)

    # 检查返回的标签形状
    self.assertEqual(labels.shape, (300,))

    # 检查簇的数量
    unique_labels = np.unique(labels)
    self.assertEqual(len(unique_labels), 4)

    # 检查标签范围
    self.assertTrue(all(0 <= label < 4 for label in labels))
```

## 4. 距离度量测试 (test_distance.py)

### 4.1 测试用例

#### 欧氏距离测试
- `test_single_vectors`: 测试单个向量
- `test_zero_distance`: 测试零距离
- `test_2d_to_1d`: 测试矩阵到向量
- `test_1d_to_2d`: 测试向量到矩阵
- `test_2d_to_2d`: 测试矩阵到矩阵
- `test_symmetry`: 测试对称性

#### 曼哈顿距离测试
- `test_single_vectors`: 测试单个向量
- `test_zero_distance`: 测试零距离
- `test_2d_to_1d`: 测试矩阵到向量
- `test_symmetry`: 测试对称性

#### 余弦距离测试
- `test_same_direction`: 测试相同方向
- `test_orthogonal`: 测试正交向量
- `test_opposite_direction`: 测试相反方向
- `test_zero_vector`: 测试零向量
- `test_2d_to_1d`: 测试矩阵到向量

#### 成对距离测试
- `test_euclidean_pairwise`: 测试欧氏成对距离
- `test_symmetric`: 测试对称性
- `test_diagonal_zero`: 测试对角线为零

### 4.2 测试方法

```python
def test_single_vectors(self):
    """测试单个向量"""
    x = np.array([1, 2, 3])
    y = np.array([4, 5, 6])

    distance = euclidean_distance(x, y)
    expected = np.sqrt(9 + 9 + 9)

    self.assertAlmostEqual(distance, expected, places=10)
```

## 5. 可视化测试 (test_visualization.py)

### 5.1 测试用例

#### 基本绘图测试
- `test_plot_clusters_2d`: 测试 2D 聚类绘图
- `test_plot_clusters_3d`: 测试 3D 聚类绘图
- `test_plot_2d_clusters`: 测试 2D 聚类绘图函数
- `test_plot_3d_clusters`: 测试 3D 聚类绘图函数
- `test_plot_elbow`: 测试肘部法则图
- `test_plot_cluster_distribution`: 测试簇分布图
- `test_plot_convergence`: 测试收敛历史图

#### 边界情况测试
- `test_single_cluster`: 测试单个簇
- `test_many_clusters`: 测试多个簇
- `test_custom_figsize`: 测试自定义图表大小

### 5.2 测试方法

```python
def test_plot_clusters_2d(self):
    """测试 2D 聚类绘图"""
    fig = plot_clusters(self.X, self.labels, self.centroids, title="Test 2D")

    # 检查返回的是 Figure 对象
    self.assertIsNotNone(fig)

    # 清理
    import matplotlib.pyplot as plt
    plt.close(fig)
```

## 6. 运行测试

### 6.1 运行所有测试

```bash
# 在项目根目录下运行
cd projects/kmeans
python -m pytest tests/ -v
```

### 6.2 运行特定测试文件

```bash
python -m pytest tests/test_kmeans.py -v
python -m pytest tests/test_distance.py -v
python -m pytest tests/test_visualization.py -v
```

### 6.3 运行特定测试用例

```bash
python -m pytest tests/test_kmeans.py::TestKMeans::test_basic_clustering -v
```

## 7. 测试覆盖率

### 7.1 生成覆盖率报告

```bash
# 安装覆盖率工具
pip install pytest-cov

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html
```

### 7.2 覆盖率目标

- 核心算法覆盖率：95%+
- 距离度量覆盖率：100%
- 可视化覆盖率：90%+

## 8. 持续集成

### 8.1 GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov numpy matplotlib
    - name: Run tests
      run: |
        python -m pytest tests/ --cov=src --cov-report=xml
```

## 9. 测试数据

### 9.1 测试数据生成

使用 `generate_clustered_data` 函数生成测试数据：

```python
def generate_clustered_data(n_samples=300, n_clusters=4, n_features=2,
                            cluster_std=1.0, random_state=None):
    """
    生成聚类测试数据
    """
    rng = np.random.RandomState(random_state)

    # 每个簇的样本数
    samples_per_cluster = n_samples // n_clusters
    remainder = n_samples % n_clusters

    # 生成簇中心
    centers = rng.randn(n_clusters, n_features) * 10

    # 生成数据
    X = []
    y = []

    for i in range(n_clusters):
        # 当前簇的样本数
        n = samples_per_cluster + (1 if i < remainder else 0)

        # 生成当前簇的数据
        cluster_data = rng.randn(n, n_features) * cluster_std + centers[i]

        X.append(cluster_data)
        y.extend([i] * n)

    X = np.vstack(X)
    y = np.array(y)

    # 随机打乱数据
    indices = rng.permutation(n_samples)
    X = X[indices]
    y = y[indices]

    return X, y
```

### 9.2 测试数据特点

- 可控的簇数量和大小
- 可控的簇间距离
- 可控的簇内方差
- 可重复的随机种子

## 10. 测试最佳实践

### 10.1 测试原则

- 每个测试用例只测试一个功能点
- 测试用例应该独立，不依赖其他测试
- 测试数据应该可重复
- 测试应该覆盖正常情况和边界情况

### 10.2 测试命名规范

- 测试文件：`test_<module>.py`
- 测试类：`Test<ClassName>`
- 测试方法：`test_<function_name>_<scenario>`

### 10.3 测试断言

- 使用 `assertEqual` 检查相等性
- 使用 `assertAlmostEqual` 检查浮点数相等性
- 使用 `assertTrue` / `assertFalse` 检查条件
- 使用 `assertRaises` 检查异常