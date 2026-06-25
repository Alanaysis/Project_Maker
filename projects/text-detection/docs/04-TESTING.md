# 04 - 测试文档

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────┐
│        Integration Tests            │
│   (完整推理流程、端到端测试)         │
├─────────────────────────────────────┤
│        Module Tests                 │
│   (各模块单独测试)                  │
├─────────────────────────────────────┤
│        Unit Tests                   │
│   (函数级别测试)                    │
└─────────────────────────────────────┘
```

### 1.2 测试覆盖目标

| 模块 | 测试文件 | 测试项数 | 覆盖率目标 |
|------|----------|----------|------------|
| Backbone | test_model.py | 8 | >90% |
| Neck | test_model.py | 5 | >90% |
| Head | test_model.py | 8 | >90% |
| Loss | test_loss.py | 10 | >95% |
| NMS | test_nms.py | 15 | >95% |
| Dataset | test_dataset.py | 10 | >90% |

## 2. 单元测试

### 2.1 Backbone 测试

```python
class TestVGGBackbone:
    def test_output_shapes(self):
        """测试多尺度输出形状"""
        backbone = VGGBackbone()
        x = torch.randn(1, 3, 256, 256)
        f1, f2, f3, f4, f5 = backbone(x)

        assert f1.shape == (1, 64, 128, 128)   # /2
        assert f2.shape == (1, 128, 64, 64)    # /4
        assert f3.shape == (1, 256, 32, 32)    # /8
        assert f4.shape == (1, 512, 16, 16)    # /16
        assert f5.shape == (1, 512, 8, 8)      # /32

    def test_batch_size(self):
        """测试不同 batch size"""
        backbone = VGGBackbone()
        for bs in [1, 2, 4]:
            x = torch.randn(bs, 3, 128, 128)
            f1, f2, f3, f4, f5 = backbone(x)
            assert f1.shape[0] == bs

    def test_gradient_flow(self):
        """测试梯度流"""
        backbone = VGGBackbone()
        x = torch.randn(1, 3, 64, 64, requires_grad=True)
        f1, f2, f3, f4, f5 = backbone(x)
        loss = f5.sum()
        loss.backward()
        assert x.grad is not None
```

### 2.2 Loss 测试

```python
class TestEASTLoss:
    def test_loss_computation(self):
        """测试损失计算"""
        loss_fn = EASTLoss()

        pred_score = torch.sigmoid(torch.randn(2, 1, 16, 16))
        pred_geo = torch.sigmoid(torch.randn(2, 5, 16, 16))
        gt_score = torch.randint(0, 2, (2, 1, 16, 16)).float()
        gt_geo = torch.rand(2, 5, 16, 16) * 100
        mask = torch.ones(2, 1, 16, 16)

        total, score_loss, geo_loss = loss_fn(
            pred_score, pred_geo, gt_score, gt_geo, mask
        )

        assert total.dim() == 0  # 标量
        assert total.item() >= 0

    def test_empty_mask(self):
        """测试空 mask"""
        loss_fn = EASTLoss()

        pred_score = torch.sigmoid(torch.randn(2, 1, 16, 16))
        pred_geo = torch.sigmoid(torch.randn(2, 5, 16, 16))
        gt_score = torch.zeros(2, 1, 16, 16)
        gt_geo = torch.zeros(2, 5, 16, 16)
        mask = torch.zeros(2, 1, 16, 16)

        total, _, _ = loss_fn(pred_score, pred_geo, gt_score, gt_geo, mask)
        assert total.item() >= 0
        assert not torch.isnan(total)

    def test_gradient_flow(self):
        """测试梯度流"""
        loss_fn = EASTLoss()

        pred_score = torch.sigmoid(torch.randn(1, 1, 8, 8, requires_grad=True))
        pred_geo = torch.sigmoid(torch.randn(1, 5, 8, 8, requires_grad=True))
        gt_score = torch.randint(0, 2, (1, 1, 8, 8)).float()
        gt_geo = torch.rand(1, 5, 8, 8) * 100
        mask = torch.ones(1, 1, 8, 8)

        total, _, _ = loss_fn(pred_score, pred_geo, gt_score, gt_geo, mask)
        total.backward()

        assert pred_score.grad is not None
        assert pred_geo.grad is not None
```

### 2.3 NMS 测试

```python
class TestNMS:
    def test_empty_boxes(self):
        """测试空输入"""
        boxes = np.array([]).reshape(0, 4)
        scores = np.array([])
        result = nms(boxes, scores, 0.5)
        assert result == []

    def test_single_box(self):
        """测试单个框"""
        boxes = np.array([[10, 10, 50, 50]])
        scores = np.array([0.9])
        result = nms(boxes, scores, 0.5)
        assert result == [0]

    def test_no_overlap(self):
        """测试无重叠"""
        boxes = np.array([
            [10, 10, 50, 50],
            [100, 100, 150, 150],
            [200, 200, 250, 250],
        ])
        scores = np.array([0.9, 0.8, 0.7])
        result = nms(boxes, scores, 0.5)
        assert len(result) == 3

    def test_full_overlap(self):
        """测试完全重叠"""
        boxes = np.array([
            [10, 10, 50, 50],
            [10, 10, 50, 50],
        ])
        scores = np.array([0.9, 0.8])
        result = nms(boxes, scores, 0.5)
        assert len(result) == 1
        assert result[0] == 0  # 保留最高分
```

## 3. 集成测试

### 3.1 完整推理流程测试

```python
class TestFullPipeline:
    def test_end_to_end(self):
        """测试完整推理流程"""
        # 创建模型
        model = EASTNet(backbone_type='light', neck_type='unet')

        # 创建检测器
        detector = TextDetector(model, score_thresh=0.5, nms_thresh=0.4)

        # 生成测试图像
        generator = SyntheticTextGenerator(img_size=512)
        image, gt_boxes = generator.generate_sample(num_texts=5)

        # 预处理
        img_tensor = preprocess(image)

        # 推理
        results = detector.detect(img_tensor)

        # 验证输出
        assert 'boxes' in results[0]
        assert 'scores' in results[0]
```

### 3.2 训练流程测试

```python
class TestTraining:
    def test_training_loop(self):
        """测试训练循环"""
        model = EASTNet(backbone_type='light')
        dataset = TextDetectionDataset(num_samples=10, img_size=128)
        dataloader = DataLoader(dataset, batch_size=2)
        criterion = EASTLoss()
        optimizer = torch.optim.Adam(model.parameters())

        # 训练一个 batch
        model.train()
        images, score_maps, geo_maps, masks = next(iter(dataloader))
        output = model(images)
        loss, _, _ = criterion(output['score'], output['geo'],
                               score_maps, geo_maps, masks)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        assert loss.item() > 0
```

## 4. 性能测试

### 4.1 推理速度测试

```python
class TestPerformance:
    def test_inference_speed(self):
        """测试推理速度"""
        import time

        model = EASTNet(backbone_type='light')
        model.eval()

        x = torch.randn(1, 3, 512, 512)

        # Warmup
        for _ in range(10):
            with torch.no_grad():
                model(x)

        # 测速
        start = time.time()
        for _ in range(100):
            with torch.no_grad():
                model(x)
        elapsed = time.time() - start

        fps = 100 / elapsed
        print(f"FPS: {fps:.1f}")
        assert fps > 10  # 至少 10 FPS
```

### 4.2 显存测试

```python
def test_memory_usage():
    """测试显存占用"""
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")

    model = EASTNet(backbone_type='vgg').cuda()
    x = torch.randn(1, 3, 512, 512).cuda()

    torch.cuda.reset_peak_memory_stats()
    with torch.no_grad():
        model(x)

    memory_mb = torch.cuda.max_memory_allocated() / 1024 / 1024
    print(f"Peak memory: {memory_mb:.1f} MB")
    assert memory_mb < 1000  # 小于 1GB
```

## 5. 边界情况测试

### 5.1 极小输入

```python
def test_tiny_input():
    """测试极小输入"""
    model = EASTNet(backbone_type='light')
    x = torch.randn(1, 3, 32, 32)
    output = model(x)
    assert output['score'].shape[2] == 8  # 32/4
```

### 5.2 大输入

```python
def test_large_input():
    """测试大输入"""
    model = EASTNet(backbone_type='light')
    x = torch.randn(1, 3, 1024, 1024)
    output = model(x)
    assert output['score'].shape[2] == 256  # 1024/4
```

### 5.3 空图像

```python
def test_empty_image():
    """测试空图像（全黑）"""
    model = EASTNet(backbone_type='light')
    x = torch.zeros(1, 3, 256, 256)
    output = model(x)
    assert output['score'].max() < 0.5  # 应该检测不到文字
```

## 6. 测试运行

### 6.1 运行所有测试

```bash
cd text-detection
pytest tests/ -v
```

### 6.2 运行特定测试

```bash
# 运行模型测试
pytest tests/test_model.py -v

# 运行损失测试
pytest tests/test_loss.py -v

# 运行 NMS 测试
pytest tests/test_nms.py -v
```

### 6.3 生成覆盖率报告

```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html
```

## 7. 测试数据

### 7.1 合成数据生成

```python
def generate_test_data():
    """生成测试数据"""
    generator = SyntheticTextGenerator(img_size=256)
    images, boxes = generator.generate_batch(batch_size=10, num_texts=5)
    return images, boxes
```

### 7.2 固定种子

```python
def test_deterministic():
    """测试确定性输出"""
    torch.manual_seed(42)
    np.random.seed(42)

    dataset = TextDetectionDataset(num_samples=10)
    img1, _, _, _ = dataset[0]

    torch.manual_seed(42)
    np.random.seed(42)

    dataset = TextDetectionDataset(num_samples=10)
    img2, _, _, _ = dataset[0]

    assert torch.allclose(img1, img2)
```
