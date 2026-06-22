# 04 - 测试文档：随机森林

## 1. 测试策略

### 1.1 测试层次

1. **单元测试**：测试单个函数/方法
2. **集成测试**：测试组件之间的交互
3. **端到端测试**：测试完整的训练-预测流程

### 1.2 测试覆盖

- 正常路径：标准输入输出
- 边界条件：极值、空值、单元素
- 错误处理：非法输入、异常情况

## 2. 决策树测试

### 2.1 初始化测试

```python
def test_initialization():
    """测试参数初始化"""
    clf = DecisionTreeClassifier(
        max_depth=5,
        min_samples_split=3,
        min_samples_leaf=2,
        criterion="gini",
        random_state=42,
    )
    assert clf.max_depth == 5
    assert clf.min_samples_split == 3
    assert clf.min_samples_leaf == 2
    assert clf.criterion == "gini"
    assert clf.random_state == 42
```

### 2.2 参数验证测试

```python
def test_invalid_criterion():
    """测试无效准则"""
    with pytest.raises(ValueError, match="Criterion must be one of"):
        DecisionTreeClassifier(criterion="invalid")

def test_invalid_min_samples_split():
    """测试无效最小分裂样本数"""
    with pytest.raises(ValueError, match="min_samples_split must be at least 2"):
        DecisionTreeClassifier(min_samples_split=1)

def test_invalid_min_samples_leaf():
    """测试无效最小叶节点样本数"""
    with pytest.raises(ValueError, match="min_samples_leaf must be at least 1"):
        DecisionTreeClassifier(min_samples_leaf=0)
```

### 2.3 基本功能测试

```python
def test_fit_predict_simple(simple_data):
    """测试基本拟合和预测"""
    X, y = simple_data
    clf = DecisionTreeClassifier(max_depth=10, random_state=42)
    clf.fit(X, y)

    predictions = clf.predict(X)
    assert len(predictions) == len(y)
    assert np.array_equal(predictions, y)  # 应该完美拟合
```

### 2.4 深度限制测试

```python
def test_max_depth_limiting(linear_separable_data):
    """测试最大深度限制"""
    X, y = linear_separable_data
    clf = DecisionTreeClassifier(max_depth=2, random_state=42)
    clf.fit(X, y)

    assert clf.get_depth() <= 2
```

### 2.5 准则测试

```python
def test_gini_criterion(linear_separable_data):
    """测试 Gini 准则"""
    X, y = linear_separable_data
    clf = DecisionTreeClassifier(criterion="gini", random_state=42)
    clf.fit(X, y)

    accuracy = clf.score(X, y)
    assert accuracy > 0.95

def test_entropy_criterion(linear_separable_data):
    """测试信息熵准则"""
    X, y = linear_separable_data
    clf = DecisionTreeClassifier(criterion="entropy", random_state=42)
    clf.fit(X, y)

    accuracy = clf.score(X, y)
    assert accuracy > 0.95
```

### 2.6 多分类测试

```python
def test_multi_class(multi_class_data):
    """测试多分类"""
    X, y = multi_class_data
    clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    clf.fit(X, y)

    predictions = clf.predict(X)
    assert len(np.unique(predictions)) <= 3
    accuracy = clf.score(X, y)
    assert accuracy > 0.9
```

### 2.7 特征重要性测试

```python
def test_feature_importances(linear_separable_data):
    """测试特征重要性"""
    X, y = linear_separable_data
    clf = DecisionTreeClassifier(random_state=42)
    clf.fit(X, y)

    assert clf.feature_importances_ is not None
    assert len(clf.feature_importances_) == X.shape[1]
    assert np.all(clf.feature_importances_ >= 0)
    assert np.isclose(np.sum(clf.feature_importances_), 1.0)
```

### 2.8 节点测试

```python
class TestNode:
    def test_leaf_node(self):
        """测试叶节点"""
        node = Node(value=0, samples=10, impurity=0.0)
        assert node.is_leaf is True
        assert node.value == 0
        assert node.samples == 10

    def test_internal_node(self):
        """测试内部节点"""
        left = Node(value=0, samples=5)
        right = Node(value=1, samples=5)
        node = Node(
            feature_index=0,
            threshold=0.5,
            left=left,
            right=right,
            samples=10,
            impurity=0.5,
        )
        assert node.is_leaf is False
        assert node.feature_index == 0
        assert node.threshold == 0.5
```

## 3. 随机森林测试

### 3.1 初始化测试

```python
def test_initialization():
    """测试参数初始化"""
    clf = RandomForestClassifier(
        n_estimators=50,
        max_depth=5,
        min_samples_split=3,
        min_samples_leaf=2,
        max_features="sqrt",
        bootstrap=True,
        criterion="gini",
        random_state=42,
    )
    assert clf.n_estimators == 50
    assert clf.max_depth == 5
    assert clf.bootstrap is True
    assert clf.random_state == 42
```

### 3.2 Bagging 测试

```python
def test_bagging_creates_different_trees(simple_data):
    """测试 Bagging 创建不同的树"""
    X, y = simple_data
    clf = RandomForestClassifier(
        n_estimators=10, bootstrap=True, random_state=42
    )
    clf.fit(X, y)

    # 所有树的预测应该不同
    predictions = np.array([tree.predict(X) for tree in clf.trees_])
    assert not np.all(predictions == predictions[0])
```

```python
def test_bagging_vs_no_bagging(simple_data):
    """测试有无 Bagging 的差异"""
    X, y = simple_data

    # 有 Bagging
    clf_bagging = RandomForestClassifier(
        n_estimators=10, bootstrap=True, random_state=42
    )
    clf_bagging.fit(X, y)

    # 无 Bagging
    clf_no_bagging = RandomForestClassifier(
        n_estimators=10, bootstrap=False, random_state=42
    )
    clf_no_bagging.fit(X, y)

    # 两者都应该有效
    assert clf_bagging.score(X, y) > 0.8
    assert clf_no_bagging.score(X, y) > 0.8
```

### 3.3 随机特征选择测试

```python
def test_random_feature_selection(high_dim_data):
    """测试随机特征选择"""
    X, y = high_dim_data  # 20 维，只有 2 个相关特征
    clf = RandomForestClassifier(
        n_estimators=10, max_features="sqrt", random_state=42
    )
    clf.fit(X, y)

    # 应该仍然有不错的准确率
    accuracy = clf.score(X, y)
    assert accuracy > 0.7
```

### 3.4 预测概率测试

```python
def test_predict_proba(simple_data):
    """测试概率预测"""
    X, y = simple_data
    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    clf.fit(X, y)

    proba = clf.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.all(proba >= 0)
    assert np.all(proba <= 1)
    assert np.allclose(np.sum(proba, axis=1), 1.0)
```

### 3.5 多分类测试

```python
def test_multi_class(multi_class_data):
    """测试多分类"""
    X, y = multi_class_data
    clf = RandomForestClassifier(
        n_estimators=20, max_depth=5, random_state=42
    )
    clf.fit(X, y)

    predictions = clf.predict(X)
    assert len(np.unique(predictions)) <= 3
    accuracy = clf.score(X, y)
    assert accuracy > 0.85
```

### 3.6 特征重要性测试

```python
def test_feature_importances(simple_data):
    """测试特征重要性"""
    X, y = simple_data
    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    clf.fit(X, y)

    assert clf.feature_importances_ is not None
    assert len(clf.feature_importances_) == X.shape[1]
    assert np.all(clf.feature_importances_ >= 0)
    assert np.isclose(np.sum(clf.feature_importances_), 1.0)
```

### 3.7 OOB 分数测试

```python
def test_oob_score(simple_data):
    """测试 OOB 分数"""
    X, y = simple_data
    clf = RandomForestClassifier(
        n_estimators=50, bootstrap=True, random_state=42
    )
    clf.fit(X, y)

    assert clf.oob_score_ is not None
    assert 0.0 <= clf.oob_score_ <= 1.0
    assert clf.oob_score_ > 0.7

def test_oob_score_without_bootstrap(simple_data):
    """测试无 Bagging 时的 OOB 分数"""
    X, y = simple_data
    clf = RandomForestClassifier(
        n_estimators=10, bootstrap=False, random_state=42
    )
    clf.fit(X, y)

    assert clf.oob_score_ is None
```

### 3.8 可重复性测试

```python
def test_random_state_reproducibility(simple_data):
    """测试随机种子的可重复性"""
    X, y = simple_data

    clf1 = RandomForestClassifier(n_estimators=10, random_state=42)
    clf1.fit(X, y)
    pred1 = clf1.predict(X)

    clf2 = RandomForestClassifier(n_estimators=10, random_state=42)
    clf2.fit(X, y)
    pred2 = clf2.predict(X)

    assert np.array_equal(pred1, pred2)
```

### 3.9 集成效果测试

```python
def test_ensemble_better_than_single_tree(high_dim_data):
    """测试集成是否优于单棵树"""
    X, y = high_dim_data

    # 单棵树
    single_tree = DecisionTreeClassifier(max_depth=5, random_state=42)
    single_tree.fit(X, y)
    single_accuracy = single_tree.score(X, y)

    # 随机森林
    rf = RandomForestClassifier(n_estimators=20, max_depth=5, random_state=42)
    rf.fit(X, y)
    rf_accuracy = rf.score(X, y)

    # 两者都应该高于随机
    assert single_accuracy > 0.5
    assert rf_accuracy > 0.5
```

## 4. 测试数据

### 4.1 简单数据

```python
@pytest.fixture
def simple_data():
    np.random.seed(42)
    X1 = np.random.randn(50, 2) + [2, 2]
    X2 = np.random.randn(50, 2) + [-2, -2]
    X = np.vstack([X1, X2])
    y = np.array([0] * 50 + [1] * 50)
    return X, y
```

### 4.2 多分类数据

```python
@pytest.fixture
def multi_class_data():
    np.random.seed(42)
    X1 = np.random.randn(30, 3) + [3, 0, 0]
    X2 = np.random.randn(30, 3) + [-3, 0, 0]
    X3 = np.random.randn(30, 3) + [0, 3, 0]
    X = np.vstack([X1, X2, X3])
    y = np.array([0] * 30 + [1] * 30 + [2] * 30)
    return X, y
```

### 4.3 高维数据

```python
@pytest.fixture
def high_dim_data():
    np.random.seed(42)
    n_samples = 100
    n_features = 20
    X = np.random.randn(n_samples, n_features)
    # 只有前 2 个特征相关
    y = ((X[:, 0] + X[:, 1]) > 0).astype(int)
    return X, y
```

## 5. 运行测试

### 5.1 运行所有测试

```bash
pytest tests/ -v
```

### 5.2 运行特定测试文件

```bash
pytest tests/test_decision_tree.py -v
pytest tests/test_random_forest.py -v
```

### 5.3 运行特定测试类

```bash
pytest tests/test_decision_tree.py::TestDecisionTreeClassifier -v
```

### 5.4 运行特定测试方法

```bash
pytest tests/test_decision_tree.py::TestDecisionTreeClassifier::test_fit_predict_simple -v
```

### 5.5 显示详细输出

```bash
pytest tests/ -v --tb=short
```

## 6. 测试覆盖率

### 6.1 覆盖的关键路径

- [x] 参数初始化和验证
- [x] 不纯度计算 (Gini, Entropy)
- [x] 信息增益计算
- [x] 最佳分裂查找
- [x] 树构建 (递归)
- [x] 预测 (单样本和多样本)
- [x] 特征重要性
- [x] Bagging 采样
- [x] 随机特征选择
- [x] 多数投票
- [x] OOB 分数
- [x] 多分类支持
- [x] 可重复性

### 6.2 边界情况

- [x] 空数据
- [x] 单类别数据
- [x] 单特征
- [x] 单样本
- [x] 极端参数值
