# 测试策略文档 - 手势识别

## 1. 测试层次

### 单元测试

测试各个组件的独立功能：

| 组件 | 测试内容 | 测试文件 |
|------|----------|----------|
| HandDetector | 肤色检测、形态学操作 | `test_hand_detector.py` |
| KeypointExtractor | 模型结构、前向传播 | `test_keypoint_extractor.py` |
| GestureClassifier | 特征提取、规则分类 | `test_gesture_classifier.py` |
| HandDataset | 数据生成、DataLoader | `test_hand_dataset.py` |

### 集成测试

测试组件间的协作：

```python
def test_end_to_end_recognition():
    """测试端到端识别流程"""
    recognizer = GestureRecognizer()
    image = create_test_image()
    results = recognizer.recognize(image)
    assert len(results) > 0
```

## 2. 测试用例设计

### HandDetector测试

```python
class TestHandDetector:
    def test_init_default(self):
        """测试默认参数初始化"""

    def test_detect_skin(self):
        """测试肤色分割"""

    def test_clean_mask(self):
        """测试形态学操作"""

    def test_find_hands_empty(self):
        """测试空图像处理"""

    def test_find_hands_with_region(self):
        """测试正常手部检测"""
```

### KeypointExtractor测试

```python
class TestKeypointNet:
    def test_model_structure(self):
        """测试模型层数和参数"""

    def test_forward_pass(self):
        """测试前向传播形状"""

    def test_output_range(self):
        """测试输出范围[0,1]"""

class TestKeypointExtractor:
    def test_extract_with_bbox(self):
        """测试带边界框提取"""

    def test_extract_without_bbox(self):
        """测试全图提取"""
```

### GestureClassifier测试

```python
class TestKeypointFeatureExtractor:
    def test_finger_states_open_palm(self):
        """测试张开手掌特征"""

    def test_finger_states_fist(self):
        """测试拳头特征"""

class TestGestureClassifier:
    def test_classify_rule_based_open_palm(self):
        """测试规则分类：张开手掌"""

    def test_classify_rule_based_fist(self):
        """测试规则分类：拳头"""

    def test_classify_neural(self):
        """测试神经网络分类"""
```

## 3. 测试数据

### 合成数据生成

```python
# 为每种手势生成基础关键点模板
# 添加随机扰动模拟真实变化
# 确保类别平衡
```

### 测试夹具

```python
@pytest.fixture
def sample_keypoints():
    """张开手掌关键点"""

@pytest.fixture
def fist_keypoints():
    """拳头关键点"""

@pytest.fixture
def sample_image():
    """带手部区域的测试图像"""
```

## 4. 运行测试

### 基本运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_hand_detector.py -v

# 运行特定测试类
pytest tests/test_gesture_classifier.py::TestGestureClassifier -v
```

### 覆盖率报告

```bash
# 生成覆盖率报告
pytest tests/ -v --cov=gesture_recognition --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 性能测试

```bash
# 运行性能测试
pytest tests/ -v -m "performance"
```

## 5. 测试覆盖率目标

| 组件 | 目标覆盖率 | 当前覆盖率 |
|------|------------|------------|
| HandDetector | 80% | - |
| KeypointExtractor | 70% | - |
| GestureClassifier | 80% | - |
| HandDataset | 75% | - |
| Visualization | 60% | - |

## 6. 持续集成

### GitHub Actions配置

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
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov=gesture_recognition
```

## 7. 测试最佳实践

### 命名规范

- 测试文件：`test_<module>.py`
- 测试类：`Test<ClassName>`
- 测试方法：`test_<功能描述>`

### 测试原则

1. **独立性**：每个测试独立运行
2. **可重复**：多次运行结果一致
3. **快速**：单元测试应在秒级完成
4. **清晰**：测试意图明确

### 断言使用

```python
# 值比较
assert result == expected

# 浮点数比较
np.testing.assert_array_almost_equal(a, b, decimal=5)

# 异常测试
with pytest.raises(ValueError):
    function_that_raises()
```
