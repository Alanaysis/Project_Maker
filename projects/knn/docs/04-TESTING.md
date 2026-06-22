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

## 距离度量测试

### 欧氏距离测试

```python
def test_euclidean_distance():
    """测试欧氏距离计算"""
    # 测试相同点
    assert DistanceMetrics.euclidean([0, 0], [0, 0]) == 0.0

    # 测试单位距离
    assert DistanceMetrics.euclidean([0, 0], [1, 0]) == 1.0
    assert DistanceMetrics.euclidean([0, 0], [0, 1]) == 1.0

    # 测试二维距离
    assert abs(DistanceMetrics.euclidean([0, 0], [3, 4]) - 5.0) < 1e-10

    # 测试三维距离
    x1 = np.array([1, 2, 3])
    x2 = np.array([4, 5, 6])
    expected = np.sqrt(27)
    assert abs(DistanceMetrics.euclidean(x1, x2) - expected) < 1e-10
```

### 曼哈顿距离测试

```python
def test_manhattan_distance():
    """测试曼哈顿距离计算"""
    # 测试相同点
    assert DistanceMetrics.manhattan([0, 0], [0, 0]) == 0

    # 测试单位距离
    assert DistanceMetrics.manhattan([0, 0], [1, 0]) == 1
    assert DistanceMetrics.manhattan([0, 0], [0, 1]) == 1

    # 测试网格路径
    assert DistanceMetrics.manhattan([0, 0], [3, 4]) == 7

    # 测试三维
    x1 = np.array([1, 2, 3])
    x2 = np.array([4, 5, 6])
    assert DistanceMetrics.manhattan(x1, x2) == 9
```

### 闵可夫斯基距离测试

```python
def test_minkowski_distance():
    """测试闵可夫斯基距离计算"""
    x1 = np.array([0, 0])
    x2 = np.array([3, 4])

    # p=1 时等于曼哈顿距离
    assert DistanceMetrics.minkowski(x1, x2, p=1) == 7

    # p=2 时等于欧氏距离
    assert abs(DistanceMetrics.minkowski(x1, x2, p=2) - 5.0) < 1e-10

    # p=inf 时为切比雪夫距离
    # 距离 = max(|3-0|, |4-0|) = 4
    assert abs(DistanceMetrics.minkowski(x1, x2, p=float('inf')) - 4.0) < 1e-10
```

### 余弦相似度测试

```python
def test_cosine_similarity():
    """测试余弦相似度计算"""
    # 测试相同向量
    assert abs(DistanceMetrics.cosine([1, 0], [1, 0]) - 1.0) < 1e-10

    # 测试正交向量
    assert abs(DistanceMetrics.cosine([1, 0], [0, 1]) - 0.0) < 1e-10

    # 测试相反向量
    assert abs(DistanceMetrics.cosine([1, 0], [-1, 0]) - (-1.0)) < 1e-10

    # 测试零向量
    assert DistanceMetrics.cosine([0, 0], [1, 1]) == 0.0
```

## KNN 分类器测试

### 初始化测试

```python
def test_knn_initialization():
    """测试分类器初始化"""
    # 默认参数
    knn = KNNClassifier()
    assert knn.k == 3
    assert knn.metric == 'euclidean'

    # 自定义参数
    knn = KNNClassifier(k=5, metric='manhattan')
    assert knn.k == 5
    assert knn.metric == 'manhattan'
```

### 训练测试

```python
def test_knn_fit():
    """测试分类器训练"""
    X_train = np.array([[1, 2], [3, 4], [5, 6]])
    y_train = np.array([0, 1, 0])

    knn = KNNClassifier(k=2)
    knn.fit(X_train, y_train)

    # 验证训练数据已存储
    assert knn.X_train is not None
    assert knn.y_train is not None
    np.testing.assert_array_equal(knn.X_train, X_train)
    np.testing.assert_array_equal(knn.y_train, y_train)
```

### 预测测试

```python
def test_knn_predict():
    """测试分类器预测"""
    # 创建简单数据集
    X_train = np.array([
        [1, 2], [1, 3], [2, 2],  # 类别 0
        [5, 5], [5, 6], [6, 5]   # 类别 1
    ])
    y_train = np.array([0, 0, 0, 1, 1, 1])

    knn = KNNClassifier(k=3)
    knn.fit(X_train, y_train)

    # 测试预测
    X_test = np.array([[2, 3], [4, 4]])
    predictions = knn.predict(X_test)

    assert len(predictions) == 2
    assert predictions[0] == 0  # 应该属于类别 0
    assert predictions[1] == 1  # 应该属于类别 1
```

### 概率预测测试

```python
def test_knn_predict_proba():
    """测试概率预测"""
    X_train = np.array([[1, 2], [3, 4], [5, 6]])
    y_train = np.array([0, 1, 0])

    knn = KNNClassifier(k=2)
    knn.fit(X_train, y_train)

    X_test = np.array([[2, 3]])
    proba = knn.predict_proba(X_test)

    # 验证概率形状
    assert proba.shape == (1, 2)

    # 验证概率和为 1
    assert abs(np.sum(proba) - 1.0) < 1e-10
```

## 边界情况测试

### 输入验证测试

```python
def test_input_validation():
    """测试输入验证"""
    knn = KNNClassifier(k=3)

    # 测试非二维数组
    with pytest.raises(ValueError):
        knn.fit(np.array([1, 2, 3]), np.array([0, 1, 0]))

    # 测试样本数量不匹配
    with pytest.raises(ValueError):
        knn.fit(np.array([[1, 2], [3, 4]]), np.array([0]))

    # 测试 K 值过大
    with pytest.raises(ValueError):
        knn.fit(np.array([[1, 2]]), np.array([0]))
        knn.k = 10
        knn.predict(np.array([[1, 2]]))
```

### 边界值测试

```python
def test_edge_cases():
    """测试边界情况"""
    # 测试单个训练样本
    X_train = np.array([[1, 2]])
    y_train = np.array([0])

    knn = KNNClassifier(k=1)
    knn.fit(X_train, y_train)

    predictions = knn.predict(np.array([[1, 2]]))
    assert predictions[0] == 0

    # 测试所有样本同一类别
    X_train = np.array([[1, 2], [3, 4], [5, 6]])
    y_train = np.array([0, 0, 0])

    knn = KNNClassifier(k=3)
    knn.fit(X_train, y_train)

    predictions = knn.predict(np.array([[2, 3]]))
    assert predictions[0] == 0
```

## 集成测试

### 鸢尾花数据集测试

```python
def test_iris_dataset():
    """测试鸢尾花数据集"""
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    # 加载数据
    iris = load_iris()
    X, y = iris.data, iris.target

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    # 训练模型
    knn = KNNClassifier(k=5, metric='euclidean')
    knn.fit(X_train, y_train)

    # 预测
    predictions = knn.predict(X_test)

    # 验证准确率
    accuracy = accuracy_score(y_test, predictions)
    assert accuracy > 0.9  # 准确率应该大于 90%
```

### 多距离度量测试

```python
def test_multiple_metrics():
    """测试多种距离度量"""
    X_train = np.array([[1, 2], [3, 4], [5, 6]])
    y_train = np.array([0, 1, 0])

    metrics = ['euclidean', 'manhattan', 'minkowski', 'cosine']

    for metric in metrics:
        knn = KNNClassifier(k=2, metric=metric)
        knn.fit(X_train, y_train)

        predictions = knn.predict(np.array([[2, 3]]))
        assert len(predictions) == 1
```

## 性能测试

### 大规模数据测试

```python
def test_large_dataset():
    """测试大规模数据集性能"""
    import time

    # 生成大数据集
    n_samples = 10000
    n_features = 10
    X_train = np.random.randn(n_samples, n_features)
    y_train = np.random.randint(0, 3, n_samples)

    knn = KNNClassifier(k=5)
    knn.fit(X_train, y_train)

    # 测试预测性能
    X_test = np.random.randn(100, n_features)

    start_time = time.time()
    predictions = knn.predict(X_test)
    end_time = time.time()

    # 验证预测时间合理
    assert (end_time - start_time) < 10  # 应该在 10 秒内完成
```

## 测试数据准备

### 简单数据集

```python
def create_simple_dataset():
    """创建简单测试数据集"""
    X = np.array([
        [1, 2], [1, 3], [2, 2],  # 类别 0
        [5, 5], [5, 6], [6, 5]   # 类别 1
    ])
    y = np.array([0, 0, 0, 1, 1, 1])
    return X, y
```

### 多分类数据集

```python
def create_multiclass_dataset():
    """创建多分类数据集"""
    X = np.array([
        [1, 2], [1, 3], [2, 2],  # 类别 0
        [5, 5], [5, 6], [6, 5],  # 类别 1
        [3, 8], [4, 8], [3, 9]   # 类别 2
    ])
    y = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])
    return X, y
```

## 测试执行

### 运行所有测试

```bash
cd projects/knn
python -m pytest tests/ -v
```

### 运行特定测试

```bash
# 运行距离度量测试
python -m pytest tests/test_knn.py::TestDistanceMetrics -v

# 运行 KNN 分类器测试
python -m pytest tests/test_knn.py::TestKNNClassifier -v
```

### 生成覆盖率报告

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## 测试最佳实践

1. **独立性**：每个测试相互独立
2. **可重复**：测试结果可重复
3. **清晰性**：测试意图清晰明确
4. **完整性**：覆盖所有边界情况
5. **效率性**：测试执行高效

## 总结

测试文档涵盖了：

1. **单元测试**：距离计算、分类器功能
2. **集成测试**：完整分类流程
3. **边界测试**：异常情况处理
4. **性能测试**：大规模数据处理
5. **测试策略**：覆盖率和执行方法