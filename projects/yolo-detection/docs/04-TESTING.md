# 04 - 测试策略

## 测试架构

### 测试文件组织

```
tests/
├── test_utils.py     # 工具函数测试
├── test_model.py     # 模型架构测试
├── test_loss.py      # 损失函数测试
├── test_nms.py       # NMS 测试
└── test_dataset.py   # 数据集测试
```

### 测试类型

1. **单元测试**：测试单个函数/模块
2. **集成测试**：测试模块间交互
3. **数值测试**：验证数学计算正确性

## 工具函数测试

### IoU 测试

```python
class TestIoU:
    def test_identical_boxes(self):
        """相同框的 IoU 应为 1.0"""

    def test_no_overlap(self):
        """不重叠框的 IoU 应为 0.0"""

    def test_partial_overlap(self):
        """部分重叠框的 IoU 应为正确值"""

    def test_contained_boxes(self):
        """一个框包含另一个框的情况"""
```

### 坐标转换测试

```python
class TestBoxConversions:
    def test_xywh_to_xyxy(self):
        """测试中心格式到角格式转换"""

    def test_xyxy_to_xywh(self):
        """测试角格式到中心格式转换"""

    def test_roundtrip(self):
        """测试来回转换是否保持一致"""

    def test_zero_size(self):
        """测试零大小框的处理"""
```

### 批量计算测试

```python
def test_batch_iou():
    """测试批量 IoU 计算的正确性和效率"""

def test_vectorized_conversion():
    """测试向量化坐标转换"""
```

## 模型测试

### 基本功能测试

```python
class TestModel:
    def test_model_creation(self):
        """测试模型能否正常创建"""

    def test_output_shape(self):
        """测试输出形状是否正确"""

    def test_batch_processing(self):
        """测试批量处理能力"""

    def test_different_input_sizes(self):
        """测试不同输入尺寸"""
```

### 数值正确性测试

```python
def test_gradient_flow():
    """测试梯度能否正常传播"""

def test_deterministic_output():
    """测试相同输入产生相同输出"""

def test_model_modes():
    """测试训练/评估模式切换"""
```

### 性能测试

```python
def test_inference_speed():
    """测试推理速度"""

def test_memory_usage():
    """测试内存使用"""
```

## 损失函数测试

### 基本功能测试

```python
class TestYOLOLoss:
    def test_loss_computation(self):
        """测试损失能否正常计算"""

    def test_loss_non_negative(self):
        """测试损失值非负"""

    def test_loss_with_zeros(self):
        """测试全零输入"""
```

### 数值正确性测试

```python
def test_perfect_predictions():
    """测试完美预测的损失应接近 0"""

def test_gradient_flow():
    """测试梯度能否正常传播"""

def test_custom_weights():
    """测试自定义权重的效果"""
```

### 边界情况测试

```python
def test_empty_targets():
    """测试空目标"""

def test_full_grid():
    """测试所有单元格都有目标"""

def test_extreme_coordinates():
    """测试极端坐标值"""
```

## NMS 测试

### 标准 NMS 测试

```python
class TestNMS:
    def test_empty_input(self):
        """测试空输入"""

    def test_single_box(self):
        """测试单个框"""

    def test_no_overlap(self):
        """测试不重叠框"""

    def test_high_overlap(self):
        """测试高度重叠框"""

    def test_score_threshold(self):
        """测试置信度阈值"""

    def test_max_detections(self):
        """测试最大检测数限制"""
```

### 批量 NMS 测试

```python
class TestBatchedNMS:
    def test_different_classes(self):
        """测试不同类别的框不相互抑制"""

    def test_same_class(self):
        """测试同类别框的抑制"""
```

### Soft NMS 测试

```python
class TestSoftNMS:
    def test_score_decay(self):
        """测试分数衰减是否正确"""

    def test_gaussian_method(self):
        """测试高斯衰减方法"""

    def test_linear_method(self):
        """测试线性衰减方法"""
```

## 数据集测试

### 数据集创建测试

```python
class TestDataset:
    def test_creation(self):
        """测试数据集能否正常创建"""

    def test_length(self):
        """测试数据集长度"""

    def test_getitem(self):
        """测试数据获取"""
```

### 数据格式测试

```python
def test_image_range():
    """测试图像值范围 [0, 1]"""

def test_target_shape():
    """测试目标张量形状"""

def test_target_values():
    """测试目标值的合理性"""
```

### 数据加载测试

```python
def test_collate_function():
    """测试批处理函数"""

def test_dataloader():
    """测试数据加载器"""

def test_reproducibility():
    """测试数据可重现性"""
```

## 集成测试

### 训练流程测试

```python
def test_training_loop():
    """测试完整训练流程能否运行"""

def test_loss_convergence():
    """测试损失是否下降"""

def test_checkpoint_save_load():
    """测试检查点保存和加载"""
```

### 推理流程测试

```python
def test_end_to_end_detection():
    """测试端到端检测流程"""

def test_batch_inference():
    """测试批量推理"""

def test_visualization():
    """测试结果可视化"""
```

## 运行测试

### 使用 pytest

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_nms.py -v

# 运行特定测试类
pytest tests/test_model.py::TestTinyYOLOv1 -v

# 运行带标记的测试
pytest tests/ -m "slow" -v
```

### 测试覆盖率

```bash
# 安装 coverage
pip install pytest-cov

# 运行带覆盖率的测试
pytest tests/ --cov=src --cov-report=html
```

### 持续集成

```yaml
# GitHub Actions 示例
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

## 测试最佳实践

### 1. 测试命名

- 使用描述性的测试名称
- 遵循 `test_<功能>_<场景>` 格式

### 2. 测试独立性

- 每个测试应该独立运行
- 不依赖外部状态

### 3. 测试覆盖

- 覆盖正常路径
- 覆盖边界情况
- 覆盖错误情况

### 4. 测试速度

- 单元测试应该快速
- 使用 mock 避免慢速操作
