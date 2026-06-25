# 测试策略 - 深度估计

## 1. 测试概述

### 1.1 测试目标

- 验证模型架构正确性
- 验证损失函数计算正确性
- 验证数据集生成正确性
- 验证工具函数功能正确性
- 验证训练流程完整性

### 1.2 测试类型

- **单元测试**: 测试单个函数/类
- **集成测试**: 测试模块间交互
- **功能测试**: 测试完整功能流程

## 2. 模型测试

### 2.1 ConvBlock 测试

```python
class TestConvBlock:
    def test_output_shape(self):
        """测试输出形状"""
        block = ConvBlock(3, 64)
        x = torch.randn(2, 3, 32, 32)
        out = block(x)
        assert out.shape == (2, 64, 32, 32)

    def test_stride(self):
        """测试步长"""
        block = ConvBlock(3, 64, stride=2)
        x = torch.randn(2, 3, 32, 32)
        out = block(x)
        assert out.shape == (2, 64, 16, 16)
```

### 2.2 ResidualBlock 测试

```python
class TestResidualBlock:
    def test_output_shape(self):
        """测试输出形状"""
        block = ResidualBlock(64)
        x = torch.randn(2, 64, 32, 32)
        out = block(x)
        assert out.shape == (2, 64, 32, 32)

    def test_residual_connection(self):
        """测试残差连接"""
        block = ResidualBlock(64)
        x = torch.randn(1, 64, 16, 16)
        out = block(x)
        assert out.abs().sum() > 0
```

### 2.3 DepthEncoder 测试

```python
class TestDepthEncoder:
    def test_output_shapes(self):
        """测试各层输出形状"""
        encoder = DepthEncoder(in_channels=3, base_channels=32)
        x = torch.randn(2, 3, 128, 128)
        features = encoder(x)

        assert len(features) == 5
        assert features[0].shape == (2, 32, 32, 32)
        assert features[1].shape == (2, 64, 16, 16)
        assert features[2].shape == (2, 128, 8, 8)
        assert features[3].shape == (2, 256, 4, 4)
        assert features[4].shape == (2, 512, 2, 2)
```

### 2.4 DepthEstimationNet 测试

```python
class TestDepthEstimationNet:
    def test_forward(self):
        """测试前向传播"""
        model = DepthEstimationNet(in_channels=3, base_channels=32)
        x = torch.randn(2, 3, 128, 128)
        depth = model(x)
        assert depth.shape == (2, 1, 128, 128)

    def test_output_range(self):
        """测试输出范围 [0, 1]"""
        model = DepthEstimationNet(in_channels=3, base_channels=32)
        x = torch.randn(2, 3, 128, 128)
        depth = model(x)
        assert depth.min() >= 0
        assert depth.max() <= 1

    def test_gradient_flow(self):
        """测试梯度流"""
        model = DepthEstimationNet(in_channels=3, base_channels=32)
        x = torch.randn(2, 3, 128, 128)
        depth = model(x)
        loss = depth.mean()
        loss.backward()

        for param in model.encoder.parameters():
            if param.requires_grad:
                assert param.grad is not None

        for param in model.decoder.parameters():
            if param.requires_grad:
                assert param.grad is not None
```

## 3. 损失函数测试

### 3.1 MSE Loss 测试

```python
class TestDepthMSELoss:
    def test_basic(self):
        """测试基本功能"""
        criterion = DepthMSELoss()
        pred = torch.ones(2, 1, 8, 8)
        target = torch.zeros(2, 1, 8, 8)
        loss = criterion(pred, target)
        assert loss.item() == pytest.approx(1.0)

    def test_zero_loss(self):
        """测试相同输入"""
        criterion = DepthMSELoss()
        x = torch.rand(2, 1, 8, 8)
        loss = criterion(x, x)
        assert loss.item() == pytest.approx(0.0)

    def test_with_mask(self):
        """测试带掩码"""
        criterion = DepthMSELoss()
        pred = torch.ones(2, 1, 8, 8)
        target = torch.zeros(2, 1, 8, 8)
        mask = torch.zeros(2, 1, 8, 8)
        mask[:, :, :4, :] = 1
        loss = criterion(pred, target, mask)
        assert loss.item() == pytest.approx(1.0)
```

### 3.2 SILog Loss 测试

```python
class TestSILogLoss:
    def test_basic(self):
        """测试基本功能"""
        criterion = SILogLoss()
        pred = torch.rand(2, 1, 8, 8) * 10 + 0.1
        target = torch.rand(2, 1, 8, 8) * 10 + 0.1
        loss = criterion(pred, target)
        assert loss.item() > 0

    def test_scale_invariance(self):
        """测试尺度不变性"""
        criterion = SILogLoss(lambda_weight=0.0)
        pred = torch.rand(1, 1, 8, 8) * 10 + 1
        target = pred * 2
        loss = criterion(pred, target)
        assert loss.item() < 1.0
```

### 3.3 Gradient Loss 测试

```python
class TestGradientLoss:
    def test_basic(self):
        """测试基本功能"""
        criterion = GradientLoss()
        pred = torch.rand(2, 1, 8, 8)
        target = torch.rand(2, 1, 8, 8)
        loss = criterion(pred, target)
        assert loss.item() >= 0

    def test_same_gradient(self):
        """测试相同梯度"""
        criterion = GradientLoss()
        x = torch.linspace(0, 1, 8).unsqueeze(0).unsqueeze(0).unsqueeze(3)
        pred = x.expand(1, 1, 8, 8)
        target = x.expand(1, 1, 8, 8) * 2
        loss = criterion(pred, target)
        assert loss.item() < 0.1
```

## 4. 数据集测试

### 4.1 SyntheticDepthDataset 测试

```python
class TestSyntheticDepthDataset:
    def test_basic(self):
        """测试基本功能"""
        dataset = SyntheticDepthDataset(num_samples=10, image_size=(64, 64))
        assert len(dataset) == 10

    def test_getitem(self):
        """测试获取样本"""
        dataset = SyntheticDepthDataset(num_samples=10, image_size=(64, 64))
        image, depth, mask = dataset[0]

        assert image.shape == (3, 64, 64)
        assert depth.shape == (1, 64, 64)
        assert mask.shape == (1, 64, 64)

    def test_image_range(self):
        """测试图像值范围"""
        dataset = SyntheticDepthDataset(num_samples=10, image_size=(64, 64))
        image, _, _ = dataset[0]
        assert image.min() >= 0
        assert image.max() <= 1

    def test_different_scenes(self):
        """测试不同场景类型"""
        for scene in ["plane", "slope", "stairs", "sphere"]:
            dataset = SyntheticDepthDataset(
                num_samples=1,
                image_size=(64, 64),
                scene_types=[scene],
            )
            image, depth, mask = dataset[0]
            assert image.shape == (3, 64, 64)
```

### 4.2 DataLoader 测试

```python
class TestCreateDataloader:
    def test_basic(self):
        """测试基本功能"""
        dataset = SyntheticDepthDataset(num_samples=20, image_size=(64, 64))
        loader = create_dataloader(dataset, batch_size=4)

        images, depths, masks = next(iter(loader))
        assert images.shape == (4, 3, 64, 64)
        assert depths.shape == (4, 1, 64, 64)
        assert masks.shape == (4, 1, 64, 64)
```

## 5. 工具函数测试

### 5.1 深度归一化测试

```python
class TestNormalizeDepth:
    def test_basic(self):
        """测试基本功能"""
        depth = torch.tensor([[[[1.0, 2.0], [3.0, 4.0]]]])
        normalized = normalize_depth(depth)
        assert normalized.min() == pytest.approx(0.0)
        assert normalized.max() == pytest.approx(1.0)
```

### 5.2 深度着色测试

```python
class TestColorizeDepth:
    def test_basic(self):
        """测试基本功能"""
        depth = torch.rand(8, 8)
        colored = colorize_depth(depth)
        assert colored.shape == (3, 8, 8)

    def test_range(self):
        """测试输出范围"""
        depth = torch.rand(8, 8)
        colored = colorize_depth(depth)
        assert colored.min() >= 0
        assert colored.max() <= 1
```

### 5.3 评估指标测试

```python
class TestComputeDepthMetrics:
    def test_perfect_prediction(self):
        """测试完美预测"""
        pred = torch.rand(2, 1, 8, 8) * 10 + 0.1
        metrics = compute_depth_metrics(pred, pred)

        assert metrics["abs_rel"] == pytest.approx(0.0, abs=1e-5)
        assert metrics["rmse"] == pytest.approx(0.0, abs=1e-5)
        assert metrics["delta1"] == pytest.approx(1.0)

    def test_metrics_range(self):
        """测试指标范围"""
        pred = torch.rand(2, 1, 8, 8) * 10 + 0.1
        target = torch.rand(2, 1, 8, 8) * 10 + 0.1
        metrics = compute_depth_metrics(pred, target)

        assert metrics["abs_rel"] >= 0
        assert metrics["rmse"] >= 0
        assert 0 <= metrics["delta1"] <= 1
```

## 6. 测试运行

### 6.1 运行所有测试

```bash
cd projects/depth-estimation
pytest tests/ -v
```

### 6.2 运行特定测试

```bash
# 运行模型测试
pytest tests/test_model.py -v

# 运行损失函数测试
pytest tests/test_loss.py -v

# 运行数据集测试
pytest tests/test_dataset.py -v

# 运行工具函数测试
pytest tests/test_utils.py -v
```

### 6.3 测试覆盖率

```bash
pytest tests/ -v --cov=src --cov-report=html
```

## 7. 测试最佳实践

### 7.1 测试命名规范

- 测试文件: `test_<module>.py`
- 测试类: `Test<ClassName>`
- 测试方法: `test_<功能描述>`

### 7.2 测试内容

- **正常输入**: 验证预期输出
- **边界条件**: 验证边界行为
- **异常输入**: 验证错误处理

### 7.3 测试独立性

- 每个测试独立运行
- 不依赖外部状态
- 使用 fixture 共享 setup

### 7.4 测试可读性

- 清晰的测试意图
- 有意义的断言消息
- 适当的注释
