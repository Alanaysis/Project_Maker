# 测试文档 - 点云处理

## 1. 测试策略

### 1.1 测试层次

| 层次 | 测试内容 | 工具 |
|------|----------|------|
| 单元测试 | 模型组件、工具函数 | pytest |
| 集成测试 | 完整流程 | pytest |
| 性能测试 | 计算效率 | 自定义 |

### 1.2 测试覆盖

- **模型测试**: 输出形状、梯度流、参数数量
- **数据测试**: 数据生成、增强、加载
- **工具测试**: 归一化、采样、距离计算

## 2. 单元测试

### 2.1 TNet 测试

```python
class TestTNet:
    def test_output_shape(self):
        """测试输出形状"""
        tnet = TNet(k=3)
        x = torch.randn(4, 3, 1024)
        output = tnet(x)
        assert output.shape == (4, 3, 3)

    def test_different_k(self):
        """测试不同的 k 值"""
        for k in [3, 64]:
            tnet = TNet(k=k)
            x = torch.randn(4, k, 512)
            output = tnet(x)
            assert output.shape == (4, k, k)
```

### 2.2 PointNet 分类器测试

```python
class TestPointNetClassifier:
    def test_output_shape(self):
        """测试输出形状"""
        model = PointNetClassifier(num_classes=10)
        x = torch.randn(4, 3, 1024)
        logits, _, _ = model(x)
        assert logits.shape == (4, 10)

    def test_parameter_count(self):
        """测试参数数量"""
        model = PointNetClassifier(num_classes=10)
        param_count = sum(p.numel() for p in model.parameters())
        assert 1_000_000 < param_count < 10_000_000
```

### 2.3 梯度流测试

```python
class TestGradientFlow:
    def test_classifier_gradients(self):
        """测试分类器梯度流"""
        model = PointNetClassifier(num_classes=10)
        x = torch.randn(2, 3, 256)
        targets = torch.randint(0, 10, (2,))

        logits, _, trans_feat = model(x)
        loss = pointnet_loss(logits, targets, trans_feat)
        loss.backward()

        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None
```

## 3. 数据测试

### 3.1 数据生成测试

```python
class TestGenerateRandomPointcloud:
    def test_shape(self):
        """测试生成形状"""
        points, labels = generate_random_pointcloud(
            num_points=512, num_classes=10, num_samples=100
        )
        assert points.shape == (100, 512, 3)
        assert labels.shape == (100,)

    def test_label_range(self):
        """测试标签范围"""
        _, labels = generate_random_pointcloud(num_classes=5)
        assert labels.min() >= 0
        assert labels.max() < 5
```

### 3.2 数据增强测试

```python
class TestPointCloudAugmentation:
    def test_preserves_shape(self):
        """测试保持形状"""
        augmentation = PointCloudAugmentation()
        points = torch.randn(100, 3)
        augmented = augmentation(points)
        assert augmented.shape == points.shape
```

## 4. 工具函数测试

### 4.1 归一化测试

```python
class TestNormalizePointcloud:
    def test_numpy_input(self):
        """测试 NumPy 输入"""
        points = np.random.randn(100, 3)
        normalized = normalize_pointcloud(points)

        centroid = np.mean(normalized, axis=0)
        np.testing.assert_allclose(centroid, 0, atol=1e-6)
```

### 4.2 最远点采样测试

```python
class TestFarthestPointSample:
    def test_output_shape(self):
        """测试输出形状"""
        points = torch.randn(4, 1024, 3)
        indices = farthest_point_sample(points, 128)
        assert indices.shape == (4, 128)

    def test_unique_indices(self):
        """测试索引唯一性"""
        points = torch.randn(2, 512, 3)
        indices = farthest_point_sample(points, 64)

        for i in range(2):
            unique_indices = torch.unique(indices[i])
            assert len(unique_indices) == 64
```

## 5. 集成测试

### 5.1 训练流程测试

```python
def test_training_pipeline():
    """测试完整训练流程"""
    # 生成数据
    points, labels = generate_random_pointcloud(num_samples=100)
    dataset = PointCloudDataset(points, labels)

    # 创建训练器
    trainer = PointCloudTrainer.create_classifier(num_classes=10)

    # 训练 1 个 epoch
    history = trainer.train(dataset, epochs=1)

    assert len(history["train_loss"]) == 1
```

### 5.2 预测流程测试

```python
def test_prediction_pipeline():
    """测试预测流程"""
    model = PointNetClassifier(num_classes=10)
    trainer = PointCloudTrainer(model, task="classification")

    points = torch.randn(3, 1024)  # (3, N)
    predictions = trainer.predict(points)

    assert predictions.shape == (1,)
    assert 0 <= predictions.item() < 10
```

## 6. 性能测试

### 6.1 推理速度

```python
def test_inference_speed():
    """测试推理速度"""
    import time

    model = PointNetClassifier(num_classes=10)
    model.eval()

    x = torch.randn(32, 3, 1024)

    # 预热
    with torch.no_grad():
        for _ in range(10):
            model(x)

    # 测试
    start = time.time()
    with torch.no_grad():
        for _ in range(100):
            model(x)
    elapsed = time.time() - start

    print(f"推理速度: {elapsed/100*1000:.2f} ms/batch")
```

### 6.2 内存占用

```python
def test_memory_usage():
    """测试内存占用"""
    model = PointNetClassifier(num_classes=10)

    # 计算模型大小
    param_size = sum(p.nelement() * p.element_size() for p in model.parameters())
    buffer_size = sum(b.nelement() * b.element_size() for b in model.buffers())

    total_size = param_size + buffer_size
    print(f"模型大小: {total_size / 1024 / 1024:.2f} MB")
```

## 7. 运行测试

### 7.1 运行所有测试

```bash
pytest tests/ -v
```

### 7.2 运行特定测试

```bash
# 运行模型测试
pytest tests/test_pointnet.py -v

# 运行数据测试
pytest tests/test_dataset.py -v

# 运行工具测试
pytest tests/test_utils.py -v
```

### 7.3 生成覆盖率报告

```bash
pytest tests/ --cov=src --cov-report=html
```

## 8. 测试结果

### 8.1 预期结果

- 所有单元测试通过
- 梯度流正常
- 输出形状正确
- 训练损失下降

### 8.2 性能基准

| 指标 | 目标 | 实际 |
|------|------|------|
| 推理速度 | < 50ms/batch | - |
| 模型大小 | < 50MB | - |
| 训练收敛 | < 50 epochs | - |
