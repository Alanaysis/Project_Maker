# 测试策略 - 人体姿态估计

## 测试目标

1. **单元测试**: 验证每个模块的功能正确性
2. **集成测试**: 验证模块间的协作
3. **数值测试**: 验证数学计算的正确性
4. **边界测试**: 验证边界条件的处理

## 测试结构

```
tests/
├── test_model.py      # 模型测试
├── test_heatmap.py    # 热力图测试
├── test_loss.py       # 损失函数测试
├── test_keypoints.py  # 关键点测试
├── test_dataset.py    # 数据集测试
└── test_utils.py      # 工具函数测试
```

## 测试用例

### 1. 模型测试 (`test_model.py`)

#### ConvBlock 测试

```python
def test_output_shape():
    """测试输出形状"""
    block = ConvBlock(3, 64)
    x = torch.randn(2, 3, 32, 32)
    out = block(x)
    assert out.shape == (2, 64, 32, 32)

def test_stride():
    """测试步长"""
    block = ConvBlock(3, 64, stride=2)
    x = torch.randn(2, 3, 64, 64)
    out = block(x)
    assert out.shape == (2, 64, 32, 32)
```

#### PoseEstimationNet 测试

```python
def test_output_shape():
    """测试输出形状"""
    model = PoseEstimationNet(num_keypoints=17, input_size=256, heatmap_size=64)
    x = torch.randn(2, 3, 256, 256)
    out = model(x)
    assert out.shape == (2, 17, 64, 64)

def test_predict_keypoints():
    """测试关键点预测"""
    model = PoseEstimationNet(num_keypoints=17, input_size=128, heatmap_size=32)
    x = torch.randn(2, 3, 128, 128)
    keypoints, confidence = model.predict_keypoints(x)
    assert keypoints.shape == (2, 17, 2)
    assert confidence.shape == (2, 17)

def test_gradient_flow():
    """测试梯度流"""
    model = PoseEstimationNet(num_keypoints=17, input_size=128, heatmap_size=32)
    x = torch.randn(1, 3, 128, 128, requires_grad=True)
    out = model(x)
    loss = out.sum()
    loss.backward()
    assert x.grad is not None
```

### 2. 热力图测试 (`test_heatmap.py`)

#### 高斯热力图生成测试

```python
def test_output_shape():
    """测试输出形状"""
    keypoints = torch.rand(4, 17, 2)
    weights = torch.ones(4, 17)
    heatmaps = generate_heatmaps(keypoints, weights, (64, 64))
    assert heatmaps.shape == (4, 17, 64, 64)

def test_peak_location():
    """测试峰值位置"""
    keypoints = torch.tensor([[[0.5, 0.5]]])
    heatmaps = generate_heatmaps(keypoints, torch.ones(1, 1), (64, 64))
    flat = heatmaps.view(1, 1, -1)
    _, max_idx = flat.max(dim=2)
    y = max_idx.item() // 64
    x = max_idx.item() % 64
    assert abs(y - 32) <= 1
    assert abs(x - 32) <= 1

def test_invisible_keypoint():
    """测试不可见关键点"""
    keypoints = torch.tensor([[[0.5, 0.5]]])
    weights = torch.tensor([[0.0]])
    heatmaps = generate_heatmaps(keypoints, weights, (32, 32))
    assert heatmaps.sum() == 0.0
```

#### Soft-Argmax 测试

```python
def test_differentiable():
    """测试可微性"""
    heatmaps = torch.rand(1, 5, 32, 32, requires_grad=True)
    keypoints, _ = soft_argmax(heatmaps)
    loss = keypoints.sum()
    loss.backward()
    assert heatmaps.grad is not None

def test_roundtrip():
    """测试往返精度"""
    original_kp = torch.tensor([[[0.3, 0.6]]])
    heatmaps = generate_heatmaps(original_kp, torch.ones(1, 1), (128, 128), sigma=2.0)
    extracted_kp, _ = heatmaps_to_keypoints(heatmaps)
    error = (original_kp - extracted_kp).abs().max()
    assert error < 0.05
```

### 3. 损失函数测试 (`test_loss.py`)

#### MSE 损失测试

```python
def test_identical_inputs():
    """相同输入损失为零"""
    criterion = KeypointMSELoss(use_target_weight=False)
    heatmaps = torch.rand(2, 17, 32, 32)
    loss = criterion(heatmaps, heatmaps)["loss"]
    assert loss.item() < 1e-6

def test_loss_positive():
    """损失为正数"""
    criterion = KeypointMSELoss(use_target_weight=False)
    pred = torch.rand(2, 17, 32, 32)
    target = torch.rand(2, 17, 32, 32)
    loss = criterion(pred, target)["loss"]
    assert loss.item() > 0

def test_gradient_flow():
    """测试梯度流"""
    criterion = KeypointMSELoss(use_target_weight=False)
    pred = torch.rand(2, 17, 32, 32, requires_grad=True)
    target = torch.rand(2, 17, 32, 32)
    loss = criterion(pred, target)["loss"]
    loss.backward()
    assert pred.grad is not None
```

#### OHKM 损失测试

```python
def test_topk_effect():
    """测试 Top-K 效果"""
    pred = torch.rand(4, 17, 32, 32)
    target = torch.rand(4, 17, 32, 32)
    
    criterion_small = KeypointOHKMLoss(topk=4)
    criterion_large = KeypointOHKMLoss(topk=12)
    
    loss_small = criterion_small(pred, target)["loss"]
    loss_large = criterion_large(pred, target)["loss"]
    
    assert loss_small.item() > 0
    assert loss_large.item() > 0
```

### 4. 关键点测试 (`test_keypoints.py`)

#### 关键点提取测试

```python
def test_output_shape():
    """测试输出形状"""
    heatmaps = torch.rand(4, 17, 64, 64)
    keypoints, confidence = extract_keypoints(heatmaps)
    assert keypoints.shape == (4, 17, 2)
    assert confidence.shape == (4, 17)

def test_threshold_effect():
    """测试阈值效果"""
    heatmaps = torch.rand(2, 17, 32, 32)
    kp_low, _ = extract_keypoints(heatmaps, threshold=0.01)
    kp_high, _ = extract_keypoints(heatmaps, threshold=0.9)
    
    zero_count_high = (kp_high == 0).sum().item()
    zero_count_low = (kp_low == 0).sum().item()
    assert zero_count_high >= zero_count_low
```

#### PCK 评估测试

```python
def test_perfect_prediction():
    """完美预测 PCK 为 1"""
    pred = torch.rand(4, 17, 2) * 0.5 + 0.25
    target = pred.clone()
    pck = compute_pck(pred, target, threshold=0.01)
    assert pck == 1.0

def test_threshold_effect():
    """阈值对 PCK 的影响"""
    pred = torch.rand(4, 17, 2)
    target = torch.rand(4, 17, 2)
    
    pck_tight = compute_pck(pred, target, threshold=0.05)
    pck_loose = compute_pck(pred, target, threshold=0.5)
    
    assert pck_loose >= pck_tight
```

### 5. 数据集测试 (`test_dataset.py`)

```python
def test_sample_keys():
    """测试样本的键"""
    dataset = SyntheticPoseDataset(num_samples=10)
    sample = dataset[0]
    assert "image" in sample
    assert "keypoints" in sample
    assert "weights" in sample
    assert "heatmaps" in sample

def test_keypoints_range():
    """测试关键点范围"""
    dataset = SyntheticPoseDataset(num_samples=20)
    for i in range(len(dataset)):
        kp = dataset[i]["keypoints"]
        assert kp.min() >= 0.0
        assert kp.max() <= 1.0

def test_variety():
    """测试样本多样性"""
    dataset = SyntheticPoseDataset(num_samples=10)
    kp_list = [dataset[i]["keypoints"] for i in range(10)]
    # 不同样本的关键点应该不同
    ...
```

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_model.py -v

# 运行特定测试类
pytest tests/test_model.py::TestPoseEstimationNet -v

# 运行特定测试函数
pytest tests/test_model.py::TestPoseEstimationNet::test_output_shape -v

# 显示详细输出
pytest tests/ -v --tb=long

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```
