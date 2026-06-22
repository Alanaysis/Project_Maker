# 测试文档

## 1. 测试策略

### 1.1 测试类型

1. **单元测试**：测试单个函数/方法的正确性
2. **集成测试**：测试完整流程的正确性
3. **回归测试**：确保修改不会破坏现有功能

### 1.2 测试覆盖目标

- 核心函数：100%覆盖
- 边界条件：重点测试
- 数值稳定性：特殊处理

## 2. 测试用例设计

### 2.1 Sigmoid函数测试

```python
def test_sigmoid_basic():
    """测试Sigmoid基本值"""
    # sigmoid(0) = 0.5
    # sigmoid(1) > 0.5
    # sigmoid(-1) < 0.5

def test_sigmoid_range():
    """测试输出范围"""
    # 所有输出应在(0, 1)之间

def test_sigmoid_extreme():
    """测试极端值"""
    # sigmoid(100) ≈ 1
    # sigmoid(-100) ≈ 0
```

### 2.2 损失函数测试

```python
def test_loss_perfect_prediction():
    """完美预测损失接近0"""

def test_loss_wrong_prediction():
    """错误预测损失很大"""

def test_loss_with_regularization():
    """正则化损失大于无正则化损失"""
```

### 2.3 训练过程测试

```python
def test_convergence():
    """损失应该逐渐减小"""

def test_weight_update():
    """权重应该被正确更新"""

def test_regularization_effect():
    """正则化应该限制权重大小"""
```

### 2.4 预测功能测试

```python
def test_predict_output():
    """预测结果应该是0或1"""

def test_predict_proba_range():
    """概率应该在(0,1)之间"""

def test_threshold_effect():
    """不同阈值应该产生不同结果"""
```

## 3. 测试数据

### 3.1 简单数据集

```python
# 线性可分数据
X_simple = np.array([[1, 1], [2, 2], [-1, -1], [-2, -2]])
y_simple = np.array([1, 1, 0, 0])
```

### 3.2 随机数据集

```python
# 高斯分布数据
np.random.seed(42)
X_pos = np.random.randn(50, 2) + [2, 2]
X_neg = np.random.randn(50, 2) + [-2, -2]
```

### 3.3 边界条件数据

```python
# 单一类别的数据
y_all_positive = np.array([1, 1, 1])
y_all_negative = np.array([0, 0, 0])

# 不平衡数据
y_imbalanced = np.array([1, 1, 1, 0, 0])
```

## 4. 运行测试

### 4.1 运行所有测试

```bash
# 在项目根目录
pytest tests/ -v
```

### 4.2 运行特定测试

```bash
# 运行模型测试
pytest tests/test_logistic_regression.py -v

# 运行指标测试
pytest tests/test_metrics.py -v
```

### 4.3 查看测试覆盖率

```bash
# 安装coverage
pip install pytest-cov

# 运行带覆盖率的测试
pytest tests/ --cov=src --cov-report=html
```

## 5. 测试结果示例

```
tests/test_logistic_regression.py::TestLogisticRegression::test_sigmoid PASSED
tests/test_logistic_regression.py::TestLogisticRegression::test_loss_computation PASSED
tests/test_logistic_regression.py::TestLogisticRegression::test_fit_simple PASSED
tests/test_logistic_regression.py::TestLogisticRegression::test_predict PASSED
tests/test_logistic_regression.py::TestLogisticRegression::test_accuracy PASSED
tests/test_logistic_regression.py::TestLogisticRegression::test_regularization PASSED
tests/test_logistic_regression.py::TestLogisticRegression::test_threshold PASSED

tests/test_metrics.py::TestMetrics::test_confusion_matrix PASSED
tests/test_metrics.py::TestMetrics::test_accuracy PASSED
tests/test_metrics.py::TestMetrics::test_precision PASSED
tests/test_metrics.py::TestMetrics::test_recall PASSED
tests/test_metrics.py::TestMetrics::test_f1_score PASSED

========================= 12 passed in 0.5s =========================
```

## 6. 常见问题

### 6.1 测试失败排查

1. **导入错误**：检查sys.path设置
2. **数值精度**：使用`assert abs(a-b) < epsilon`而非`assert a == b`
3. **随机性**：设置random_state确保可重复性

### 6.2 性能测试

```python
import time

def test_training_speed():
    """测试训练速度"""
    X, y = generate_large_dataset(10000)

    start = time.time()
    model = LogisticRegression(n_iterations=100)
    model.fit(X, y)
    duration = time.time() - start

    assert duration < 5.0  # 应在5秒内完成
```

## 7. 持续集成

### 7.1 GitHub Actions配置

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install numpy pytest
      - name: Run tests
        run: pytest tests/ -v
```

## 8. 测试最佳实践

1. **测试独立性**：每个测试应独立运行
2. **测试可重复**：使用固定随机种子
3. **测试清晰**：测试名称应描述测试内容
4. **测试全面**：覆盖正常、边界、异常情况
