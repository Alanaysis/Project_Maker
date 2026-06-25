# 04 - 测试文档

## 测试策略

### 测试类型

1. **单元测试**：测试单个函数/方法
2. **集成测试**：测试完整流程
3. **边界测试**：测试边界情况和异常处理

### 测试覆盖目标

- 代码覆盖率 > 90%
- 核心功能 100% 覆盖
- 边界情况完整测试

## 测试文件结构

```
tests/
├── __init__.py
├── test_knn.py              # 距离度量和 KNN 分类器测试
├── test_regressor.py        # KNN 回归器测试
├── test_kd_tree.py          # KD-Tree 测试
├── test_ball_tree.py        # Ball Tree 测试
└── test_model_selection.py  # 模型选择测试
```

## 距离度量测试

### 欧氏距离测试

```python
class TestDistanceMetrics:
    def test_euclidean_distance_same_point(self):
        """测试相同点的欧氏距离"""
        assert DistanceMetrics.euclidean([0, 0], [0, 0]) == 0.0

    def test_euclidean_distance_unit(self):
        """测试单位距离"""
        assert DistanceMetrics.euclidean([0, 0], [1, 0]) == 1.0

    def test_euclidean_distance_2d(self):
        """测试二维欧氏距离（3-4-5 三角形）"""
        assert abs(DistanceMetrics.euclidean([0, 0], [3, 4]) - 5.0) < 1e-10

    def test_euclidean_distance_symmetry(self):
        """测试对称性"""
        x1, x2 = [1, 2, 3], [4, 5, 6]
        assert DistanceMetrics.euclidean(x1, x2) == DistanceMetrics.euclidean(x2, x1)
```

### 曼哈顿距离测试

```python
def test_manhattan_distance_grid(self):
    """测试网格路径"""
    assert DistanceMetrics.manhattan([0, 0], [3, 4]) == 7

def test_manhattan_distance_3d(self):
    """测试三维曼哈顿距离"""
    assert DistanceMetrics.manhattan([1, 2, 3], [4, 5, 6]) == 9
```

### 闵可夫斯基距离测试

```python
def test_minkowski_distance_p1(self):
    """p=1 时等于曼哈顿距离"""
    assert DistanceMetrics.minkowski([0, 0], [3, 4], p=1) == 7

def test_minkowski_distance_p2(self):
    """p=2 时等于欧氏距离"""
    assert abs(DistanceMetrics.minkowski([0, 0], [3, 4], p=2) - 5.0) < 1e-10

def test_minkowski_distance_pinf(self):
    """p=inf 时为切比雪夫距离"""
    assert abs(DistanceMetrics.minkowski([0, 0], [3, 4], p=float('inf')) - 4.0) < 1e-10
```

### 余弦相似度测试

```python
def test_cosine_similarity_same_direction(self):
    """测试相同方向"""
    assert abs(DistanceMetrics.cosine([1, 0], [1, 0]) - 1.0) < 1e-10

def test_cosine_similarity_orthogonal(self):
    """测试正交向量"""
    assert abs(DistanceMetrics.cosine([1, 0], [0, 1]) - 0.0) < 1e-10

def test_cosine_similarity_opposite(self):
    """测试相反方向"""
    assert abs(DistanceMetrics.cosine([1, 0], [-1, 0]) - (-1.0)) < 1e-10

def test_cosine_similarity_zero_vector(self):
    """测试零向量"""
    assert DistanceMetrics.cosine([0, 0], [1, 1]) == 0.0
```

## KNN 分类器测试

### 初始化测试

```python
def test_initialization_default(self):
    """测试默认参数"""
    knn = KNNClassifier()
    assert knn.k == 3
    assert knn.metric == 'euclidean'
    assert knn.weights == 'uniform'

def test_initialization_custom(self):
    """测试自定义参数"""
    knn = KNNClassifier(k=5, metric='manhattan', weights='distance')
    assert knn.k == 5
    assert knn.metric == 'manhattan'
    assert knn.weights == 'distance'

def test_initialization_invalid_k(self):
    """测试无效 K 值"""
    with pytest.raises(ValueError):
        KNNClassifier(k=0)

def test_initialization_invalid_weights(self):
    """测试无效权重策略"""
    with pytest.raises(ValueError):
        KNNClassifier(weights='invalid')
```

### 训练测试

```python
def test_fit_basic(self):
    """测试基本训练"""
    X_train = np.array([[1, 2], [3, 4], [5, 6]])
    y_train = np.array([0, 1, 0])

    knn = KNNClassifier(k=2)
    result = knn.fit(X_train, y_train)

    assert result is knn  # 返回自身
    np.testing.assert_array_equal(knn.X_train, X_train)
    np.testing.assert_array_equal(knn.classes_, np.array([0, 1]))
```

### 预测测试

```python
def test_predict_basic(self):
    """测试基本预测"""
    X_train = np.array([
        [1, 2], [1, 3], [2, 2],  # 类别 0
        [5, 5], [5, 6], [6, 5]   # 类别 1
    ])
    y_train = np.array([0, 0, 0, 1, 1, 1])

    knn = KNNClassifier(k=3)
    knn.fit(X_train, y_train)

    predictions = knn.predict(np.array([[2, 3], [4, 4]]))
    assert predictions[0] == 0
    assert predictions[1] == 1
```

### 加权投票测试

```python
def test_weighted_vote(self):
    """测试距离加权投票"""
    X_train = np.array([[0], [1], [10]])
    y_train = np.array([0, 0, 1])

    # 等权投票：2 个类别 0，1 个类别 1 → 预测 0
    knn_uniform = KNNClassifier(k=2, weights='uniform')
    knn_uniform.fit(X_train, y_train)
    assert knn_uniform.predict(np.array([[0.5]]))[0] == 0

    # 距离加权：距离 [0.5, 0.5, 9.5]
    # 类别 0 权重 = 1/0.5 + 1/0.5 = 4
    # 类别 1 权重 = 1/9.5 ≈ 0.105
    # 预测 0
    knn_distance = KNNClassifier(k=2, weights='distance')
    knn_distance.fit(X_train, y_train)
    assert knn_distance.predict(np.array([[0.5]]))[0] == 0
```

### 概率预测测试

```python
def test_predict_proba_basic(self):
    """测试概率预测"""
    X_train = np.array([[1, 2], [3, 4], [5, 6]])
    y_train = np.array([0, 1, 0])

    knn = KNNClassifier(k=2)
    knn.fit(X_train, y_train)

    proba = knn.predict_proba(np.array([[2, 3]]))
    assert proba.shape == (1, 2)
    assert abs(np.sum(proba) - 1.0) < 1e-10

def test_predict_proba_weighted(self):
    """测试距离加权概率预测"""
    X_train = np.array([[0], [1], [10]])
    y_train = np.array([0, 0, 1])

    knn = KNNClassifier(k=2, weights='distance')
    knn.fit(X_train, y_train)

    proba = knn.predict_proba(np.array([[0.5]]))
    # 类别 0 的概率应该远大于类别 1
    assert proba[0][0] > proba[0][1]
```

## KNN 回归器测试

### 基本功能测试

```python
def test_predict_basic(self):
    """测试基本预测"""
    X_train = np.array([[1], [2], [3], [4], [5]])
    y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    reg = KNNRegressor(k=3, weights='uniform')
    reg.fit(X_train, y_train)

    predictions = reg.predict(np.array([[3.5]]))
    # 最近的 3 个是 [3, 4, 5]，平均值 = 4.0
    assert abs(predictions[0] - 4.0) < 0.1
```

### 加权平均测试

```python
def test_predict_weighted(self):
    """测试距离加权平均"""
    X_train = np.array([[0], [1], [10]])
    y_train = np.array([0.0, 1.0, 100.0])

    reg = KNNRegressor(k=2, weights='distance')
    reg.fit(X_train, y_train)

    prediction = reg.predict(np.array([[0.5]]))
    # 距离加权应该更接近近距离的值
    assert prediction[0] < 1.0
```

### R² 评分测试

```python
def test_score_perfect(self):
    """测试完美预测的 R²"""
    X = np.array([[1], [2], [3]])
    y = np.array([1.0, 2.0, 3.0])

    reg = KNNRegressor(k=1)
    reg.fit(X, y)

    score = reg.score(X, y)
    assert abs(score - 1.0) < 1e-10
```

## KD-Tree 测试

### 建树测试

```python
def test_build_basic(self):
    """测试基本建树"""
    X = np.array([[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]])
    y = np.array([0, 0, 1, 0, 1, 1])

    tree = KDTree(metric='euclidean')
    tree.build(X, y)

    assert tree.root is not None
    assert tree.get_size() == 6
```

### 查询测试

```python
def test_query_k_nearest(self):
    """测试 K 近邻查询"""
    X = np.array([[0, 0], [1, 0], [0, 1], [1, 1], [2, 2]])
    y = np.array([0, 0, 0, 1, 1])

    tree = KDTree(metric='euclidean')
    tree.build(X, y)

    indices, distances = tree.query(np.array([0.5, 0.5]), k=3)
    assert len(indices) == 3
    assert distances[0] <= distances[1] <= distances[2]
```

### 与暴力搜索一致性测试

```python
def test_accuracy_vs_brute_force(self):
    """测试与暴力搜索的一致性"""
    np.random.seed(42)
    X = np.random.randn(100, 2)
    y = np.random.randint(0, 3, 100)

    tree = KDTree(metric='euclidean')
    tree.build(X, y)

    query_point = np.array([0.5, 0.5])
    k = 5

    # KD-Tree
    tree_indices, tree_distances = tree.query(query_point, k=k)

    # 暴力搜索
    brute_distances = np.sqrt(np.sum((X - query_point) ** 2, axis=1))
    brute_indices = np.argsort(brute_distances)[:k]

    # 距离应该一致
    np.testing.assert_allclose(
        np.sort(tree_distances),
        brute_distances[brute_indices],
        atol=1e-10
    )
```

### 半径查询测试

```python
def test_query_radius_basic(self):
    """测试半径查询"""
    X = np.array([[0, 0], [1, 0], [0, 1], [1, 1], [2, 2]])
    y = np.array([0, 0, 0, 1, 1])

    tree = KDTree(metric='euclidean')
    tree.build(X, y)

    indices, distances = tree.query_radius(np.array([0, 0]), radius=1.0)
    assert len(indices) == 3  # (0,0), (1,0), (0,1)
```

## Ball Tree 测试

### 建树测试

```python
def test_build_basic(self):
    """测试基本建树"""
    X = np.array([[2, 3], [5, 4], [9, 6], [4, 7], [8, 1], [7, 2]])
    y = np.array([0, 0, 1, 0, 1, 1])

    tree = BallTree(metric='euclidean', leaf_size=2)
    tree.build(X, y)

    assert tree.root is not None
```

### 多距离度量测试

```python
def test_manhattan_metric(self):
    """测试曼哈顿距离"""
    X = np.array([[0, 0], [1, 1], [2, 2]])
    y = np.array([0, 1, 0])

    tree = BallTree(metric='manhattan', leaf_size=2)
    tree.build(X, y)

    indices, distances = tree.query(np.array([1, 0]), k=1)
    assert abs(distances[0] - 1.0) < 1e-10

def test_cosine_metric(self):
    """测试余弦距离"""
    X = np.array([[1, 0], [0, 1], [1, 1]])
    y = np.array([0, 1, 0])

    tree = BallTree(metric='cosine', leaf_size=2)
    tree.build(X, y)

    indices, distances = tree.query(np.array([1, 0]), k=1)
    assert distances[0] < 1e-10
```

### 叶节点大小测试

```python
def test_leaf_size(self):
    """测试叶节点大小的影响"""
    X = np.array([[1], [2], [3], [4], [5], [6], [7], [8]])
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])

    tree_small = BallTree(metric='euclidean', leaf_size=2)
    tree_small.build(X, y)
    size_small = tree_small.get_size()

    tree_large = BallTree(metric='euclidean', leaf_size=4)
    tree_large.build(X, y)
    size_large = tree_large.get_size()

    # 叶节点越小，树越大
    assert size_small >= size_large
```

## 模型选择测试

### K-Fold 测试

```python
def test_split_basic(self):
    """测试基本分割"""
    X = np.arange(10).reshape(-1, 1)
    kfold = KFold(n_splits=5, shuffle=False)

    splits = kfold.split(X)
    assert len(splits) == 5

    for train_idx, val_idx in splits:
        assert len(set(train_idx) & set(val_idx)) == 0
        assert len(train_idx) + len(val_idx) == 10

def test_split_reproducible(self):
    """测试可复现性"""
    X = np.arange(20).reshape(-1, 1)

    kfold1 = KFold(n_splits=5, shuffle=True, random_state=42)
    kfold2 = KFold(n_splits=5, shuffle=True, random_state=42)

    for (train1, val1), (train2, val2) in zip(kfold1.split(X), kfold2.split(X)):
        np.testing.assert_array_equal(train1, train2)
        np.testing.assert_array_equal(val1, val2)
```

### 交叉验证测试

```python
def test_cross_val_score(self):
    """测试交叉验证评分"""
    np.random.seed(42)
    X = np.random.randn(100, 2)
    y = np.random.randint(0, 3, 100)

    cv = CrossValidator(n_folds=5, random_state=42)
    knn = KNNClassifier(k=5)
    results = cv.cross_val_score(knn, X, y)

    assert len(results['scores']) == 5
    assert 0 <= results['mean_score'] <= 1
    assert results['std_score'] >= 0
```

### K 值选择测试

```python
def test_select_k(self):
    """测试 K 值选择"""
    np.random.seed(42)
    X = np.random.randn(100, 2)
    y = np.random.randint(0, 3, 100)

    cv = CrossValidator(n_folds=5, random_state=42)
    results = cv.select_k(X, y, k_range=[1, 3, 5, 7], task='classification')

    assert results['best_k'] in [1, 3, 5, 7]
    assert 0 <= results['best_score'] <= 1
```

## 边界情况测试

### 输入验证测试

```python
def test_fit_validation_x_dimension(self):
    """测试 X 维度验证"""
    knn = KNNClassifier(k=2)
    with pytest.raises(ValueError):
        knn.fit(np.array([1, 2, 3]), np.array([0, 1, 0]))

def test_fit_validation_k_too_large(self):
    """测试 K 值过大"""
    knn = KNNClassifier(k=2)
    with pytest.raises(ValueError):
        knn.fit(np.array([[1]]), np.array([0]))

def test_predict_before_fit(self):
    """测试未训练时预测"""
    knn = KNNClassifier(k=3)
    with pytest.raises(RuntimeError):
        knn.predict(np.array([[1, 2]]))
```

### 边界值测试

```python
def test_single_sample(self):
    """测试单个训练样本"""
    knn = KNNClassifier(k=1)
    knn.fit(np.array([[1, 2]]), np.array([0]))
    predictions = knn.predict(np.array([[1, 2]]))
    assert predictions[0] == 0

def test_all_same_class(self):
    """测试所有样本同一类别"""
    knn = KNNClassifier(k=3)
    knn.fit(np.array([[1], [2], [3]]), np.array([0, 0, 0]))
    predictions = knn.predict(np.array([[2]]))
    assert predictions[0] == 0
```

## 评分函数测试

```python
def test_accuracy_score():
    """测试准确率计算"""
    y_true = np.array([0, 1, 2, 0, 1])
    y_pred = np.array([0, 1, 2, 0, 0])
    assert accuracy_score(y_true, y_pred) == 0.8

def test_mean_squared_error():
    """测试 MSE 计算"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.5, 2.5, 3.5])
    assert abs(mean_squared_error(y_true, y_pred) - 0.25) < 1e-10

def test_r2_score():
    """测试 R² 计算"""
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.0, 3.0])
    assert abs(r2_score(y_true, y_pred) - 1.0) < 1e-10
```

## 测试执行

### 运行所有测试

```bash
cd projects/knn
python -m pytest tests/ -v
```

### 运行特定测试文件

```bash
python -m pytest tests/test_knn.py -v
python -m pytest tests/test_regressor.py -v
python -m pytest tests/test_kd_tree.py -v
python -m pytest tests/test_ball_tree.py -v
python -m pytest tests/test_model_selection.py -v
```

### 运行特定测试类

```bash
python -m pytest tests/test_knn.py::TestDistanceMetrics -v
python -m pytest tests/test_knn.py::TestKNNClassifier -v
```

### 生成覆盖率报告

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## 测试最佳实践

1. **独立性**：每个测试相互独立
2. **可重复**：使用固定随机种子确保结果可重复
3. **清晰性**：测试意图清晰明确
4. **完整性**：覆盖所有边界情况
5. **效率性**：测试执行高效

## 总结

测试文档涵盖了：

1. **单元测试**：距离计算、分类器、回归器功能
2. **数据结构测试**：KD-Tree、Ball Tree
3. **模型选择测试**：K-Fold、交叉验证、K 值选择
4. **边界测试**：异常情况处理
5. **集成测试**：完整工作流程
