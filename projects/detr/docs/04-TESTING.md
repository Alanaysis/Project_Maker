# DETR 目标检测 - 测试文档

## 1. 测试策略

### 1.1 测试层次

1. **单元测试**：测试单个组件的功能
2. **集成测试**：测试组件间的交互
3. **系统测试**：测试完整系统的行为

### 1.2 测试覆盖

- 骨干网络（Backbone）
- Transformer（编码器/解码器）
- 匈牙利匹配（Matcher）
- 损失函数（Loss）
- DETR 主模型
- 数据集（Dataset）

## 2. 测试用例

### 2.1 骨干网络测试 (test_backbone.py)

#### 测试 1: ResNet18 骨干网络
```python
def test_backbone_resnet18():
    """测试ResNet18骨干网络"""
    backbone = Backbone('resnet18', train_backbone=True)
    assert backbone.num_channels == [512]
    
    x = torch.randn(2, 3, 320, 320)
    mask = torch.zeros(2, 320, 320, dtype=torch.bool)
    tensor_list = NestedTensor(x, mask)
    
    output = backbone(tensor_list)
    assert output['0'].tensors.shape == (2, 512, 10, 10)
```

#### 测试 2: 参数可训练性
```python
def test_backbone_trainable_params():
    """测试骨干网络参数可训练性"""
    backbone_train = Backbone('resnet18', train_backbone=True)
    for param in backbone_train.parameters():
        assert param.requires_grad
    
    backbone_frozen = Backbone('resnet18', train_backbone=False)
    for param in backbone_frozen.parameters():
        assert not param.requires_grad
```

### 2.2 Transformer 测试 (test_transformer.py)

#### 测试 1: Transformer 前向传播
```python
def test_transformer_forward():
    """测试Transformer前向传播"""
    model = Transformer(d_model=64, nhead=4, num_encoder_layers=2, num_decoder_layers=2)
    
    src = torch.randn(2, 64, 10, 10)
    mask = torch.zeros(2, 10, 10, dtype=torch.bool)
    query_embed = torch.randn(100, 64)
    pos_embed = torch.randn(2, 64, 10, 10)
    
    hs, memory = model(src, mask, query_embed, pos_embed)
    
    assert hs.shape == (2, 100, 64)
    assert memory.shape == (2, 64, 10, 10)
```

#### 测试 2: 不同尺寸输入
```python
def test_transformer_with_different_sizes():
    """测试不同尺寸的输入"""
    model = Transformer(d_model=64, nhead=4, num_encoder_layers=1, num_decoder_layers=1)
    
    for h, w in [(5, 5), (10, 10), (8, 12)]:
        src = torch.randn(1, 64, h, w)
        mask = torch.zeros(1, h, w, dtype=torch.bool)
        query_embed = torch.randn(50, 64)
        pos_embed = torch.randn(1, 64, h, w)
        
        hs, memory = model(src, mask, query_embed, pos_embed)
        assert hs.shape == (1, 50, 64)
```

### 2.3 匈牙利匹配测试 (test_matcher.py)

#### 测试 1: 基本匹配功能
```python
def test_matcher_basic():
    """测试基本匹配功能"""
    matcher = HungarianMatcher(cost_class=1, cost_bbox=1, cost_giou=1)
    
    outputs = {
        'pred_logits': torch.randn(2, 100, 91),
        'pred_boxes': torch.rand(2, 100, 4) * 0.5 + 0.25
    }
    
    targets = [
        {'labels': torch.tensor([1, 2, 3]), 'boxes': torch.tensor([...])},
        {'labels': torch.tensor([4, 5]), 'boxes': torch.tensor([...])}
    ]
    
    indices = matcher(outputs, targets)
    assert len(indices) == 2
```

#### 测试 2: IoU 计算
```python
def test_box_iou():
    """测试IoU计算"""
    boxes1 = torch.tensor([[0.0, 0.0, 1.0, 1.0]])
    boxes2 = torch.tensor([[0.5, 0.5, 1.5, 1.5]])
    
    iou, inter = box_iou(boxes1, boxes2)
    
    assert iou.shape == (1, 1)
    assert 0 < iou.item() < 1
```

### 2.4 损失函数测试 (test_loss.py)

#### 测试 1: 集合预测损失
```python
def test_set_criterion_forward():
    """测试集合预测损失"""
    num_classes = 5
    matcher = build_matcher()
    weight_dict = {'loss_ce': 1, 'loss_bbox': 5, 'loss_giou': 2}
    criterion = SetCriterion(num_classes, matcher, weight_dict, eos_coef=0.1, losses=['labels', 'boxes'])
    
    outputs = {
        'pred_logits': torch.randn(2, 100, num_classes + 1),
        'pred_boxes': torch.rand(2, 100, 4)
    }
    
    targets = [{'labels': torch.tensor([1, 2, 3]), 'boxes': torch.tensor([...])}]
    
    losses = criterion(outputs, targets)
    assert 'loss_ce' in losses
    assert 'loss_bbox' in losses
    assert 'loss_giou' in losses
```

#### 测试 2: 梯度流动
```python
def test_loss_gradient():
    """测试损失函数梯度"""
    outputs = {
        'pred_logits': torch.randn(1, 10, 6, requires_grad=True),
        'pred_boxes': torch.rand(1, 10, 4, requires_grad=True)
    }
    
    targets = [{'labels': torch.tensor([1, 2]), 'boxes': torch.tensor([...])}]
    
    losses = criterion(outputs, targets)
    total_loss = sum(losses.values())
    total_loss.backward()
    
    assert outputs['pred_logits'].grad is not None
    assert outputs['pred_boxes'].grad is not None
```

### 2.5 DETR 模型测试 (test_detr.py)

#### 测试 1: 模型前向传播
```python
def test_detr_forward():
    """测试DETR前向传播"""
    model = build_detr(num_classes=5, num_queries=50, hidden_dim=128, 
                      nhead=4, num_encoder_layers=2, num_decoder_layers=2)
    
    images = torch.randn(2, 3, 320, 320)
    outputs = model(images)
    
    assert outputs['pred_logits'].shape == (2, 50, 6)
    assert outputs['pred_boxes'].shape == (2, 50, 4)
```

#### 测试 2: 与损失函数集成
```python
def test_detr_loss_integration():
    """测试DETR与损失函数的集成"""
    model = build_detr(num_classes=5, num_queries=50, ...)
    criterion = SetCriterion(5, matcher, weight_dict, ...)
    
    images = torch.randn(2, 3, 320, 320)
    targets = [{'labels': torch.tensor([1, 2]), 'boxes': torch.tensor([...])}]
    
    outputs = model(images)
    losses = criterion(outputs, targets)
    
    assert all(v.item() > 0 for v in losses.values())
```

### 2.6 数据集测试 (test_dataset.py)

#### 测试 1: 数据集创建
```python
def test_simple_dataset_creation():
    """测试简单数据集创建"""
    dataset = SimpleDetectionDataset(num_samples=100, image_size=320, num_classes=5)
    assert len(dataset) == 100
```

#### 测试 2: 批处理函数
```python
def test_collate_fn():
    """测试批处理函数"""
    dataset = SimpleDetectionDataset(num_samples=4)
    batch = [dataset[i] for i in range(4)]
    
    images, targets = collate_fn(batch)
    
    assert images.shape == (4, 3, 320, 320)
    assert len(targets) == 4
```

## 3. 测试运行

### 3.1 运行所有测试

```bash
cd projects/detr
python -m pytest tests/ -v
```

### 3.2 运行特定测试

```bash
# 运行骨干网络测试
python -m pytest tests/test_backbone.py -v

# 运行Transformer测试
python -m pytest tests/test_transformer.py -v

# 运行匹配器测试
python -m pytest tests/test_matcher.py -v
```

### 3.3 测试覆盖率

```bash
# 安装覆盖率工具
pip install pytest-cov

# 运行测试并生成覆盖率报告
python -m pytest tests/ -v --cov=src --cov-report=html
```

## 4. 测试结果示例

### 4.1 测试输出

```
tests/test_backbone.py::TestBackbone::test_backbone_resnet18 PASSED
tests/test_backbone.py::TestBackbone::test_backbone_resnet50 PASSED
tests/test_backbone.py::TestBackbone::test_build_backbone PASSED
tests/test_backbone.py::TestBackbone::test_frozen_batch_norm PASSED
tests/test_backbone.py::TestBackbone::test_backbone_trainable_params PASSED

tests/test_transformer.py::TestTransformer::test_transformer_forward PASSED
tests/test_transformer.py::TestTransformer::test_encoder_layer PASSED
tests/test_transformer.py::TestTransformer::test_decoder_layer PASSED
tests/test_transformer.py::TestTransformer::test_build_transformer PASSED
tests/test_transformer.py::TestTransformer::test_transformer_with_different_sizes PASSED

tests/test_matcher.py::TestMatcher::test_matcher_basic PASSED
tests/test_matcher.py::TestMatcher::test_box_conversion PASSED
tests/test_matcher.py::TestMatcher::test_box_iou PASSED
tests/test_matcher.py::TestMatcher::test_generalized_box_iou PASSED
tests/test_matcher.py::TestMatcher::test_build_matcher PASSED
tests/test_matcher.py::TestMatcher::test_matcher_perfect_match PASSED

tests/test_loss.py::TestLoss::test_set_criterion_forward PASSED
tests/test_loss.py::TestLoss::test_sigmoid_focal_loss PASSED
tests/test_loss.py::TestLoss::test_loss_gradient PASSED
tests/test_loss.py::TestLoss::test_loss_with_aux_outputs PASSED

tests/test_detr.py::TestDETR::test_detr_forward PASSED
tests/test_detr.py::TestDETR::test_detr_with_nested_tensor PASSED
tests/test_detr.py::TestDETR::test_detr_with_aux_loss PASSED
tests/test_detr.py::TestDETR::test_detr_loss_integration PASSED
tests/test_detr.py::TestDETR::test_build_detr_default PASSED
tests/test_detr.py::TestDETR::test_detr_gradient_flow PASSED

tests/test_dataset.py::TestDataset::test_simple_dataset_creation PASSED
tests/test_dataset.py::TestDataset::test_dataset_getitem PASSED
tests/test_dataset.py::TestDataset::test_dataset_boxes_format PASSED
tests/test_dataset.py::TestDataset::test_create_simple_dataset PASSED
tests/test_dataset.py::TestDataset::test_collate_fn PASSED
tests/test_dataset.py::TestDataset::test_dataset_consistency PASSED

========================= 32 passed in 45.23s =========================
```

### 4.2 覆盖率报告

```
Name                    Stmts   Miss  Cover
-------------------------------------------
src/__init__.py            15      0   100%
src/backbone.py            85     12    86%
src/dataset.py             45      5    89%
src/detr.py                60      8    87%
src/loss.py                95     15    84%
src/matcher.py             70     10    86%
src/transformer.py        120     18    85%
src/utils.py               55      8    85%
-------------------------------------------
TOTAL                     545     76    86%
```

## 5. 持续集成

### 5.1 GitHub Actions 配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

## 6. 测试最佳实践

### 6.1 测试命名规范

- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试方法：`test_*`

### 6.2 测试隔离

- 每个测试独立运行
- 使用 fixtures 设置测试环境
- 测试后清理资源

### 6.3 断言清晰

- 使用描述性的断言消息
- 测试边界条件
- 验证异常情况

### 6.4 测试数据

- 使用随机数据
- 测试不同尺寸
- 测试边界值
