# 04 - 测试文档

## 测试策略

### 测试层次

1. **单元测试**：测试单个组件
2. **集成测试**：测试组件交互
3. **端到端测试**：测试完整流程

### 测试覆盖

- 模型前向传播
- 损失函数计算
- 训练流程
- 推理流程
- 边界情况

## 单元测试

### 1. 图像编码器测试

```python
class TestImageEncoder:
    def test_output_shape(self):
        """测试输出形状正确"""
        encoder = ImageEncoder(embed_dim=512)
        x = torch.randn(2, 3, 224, 224)
        output = encoder(x)
        assert output.shape == (2, 512)

    def test_output_normalized(self):
        """测试输出已归一化"""
        encoder = ImageEncoder(embed_dim=256)
        x = torch.randn(4, 3, 224, 224)
        output = encoder(x)
        norms = torch.norm(output, dim=1)
        assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    def test_gradient_flow(self):
        """测试梯度可以流过模型"""
        encoder = ImageEncoder(embed_dim=256)
        x = torch.randn(2, 3, 224, 224)
        output = encoder(x)
        loss = output.sum()
        loss.backward()
        for param in encoder.parameters():
            assert param.grad is not None
```

### 2. 文本编码器测试

```python
class TestTextEncoder:
    def test_output_shape(self):
        """测试输出形状正确"""
        encoder = TextEncoder(vocab_size=10000, embed_dim=512)
        input_ids = torch.randint(0, 10000, (2, 77))
        output = encoder(input_ids)
        assert output.shape == (2, 512)

    def test_with_attention_mask(self):
        """测试带注意力掩码的编码"""
        encoder = TextEncoder(vocab_size=10000, embed_dim=256)
        input_ids = torch.randint(0, 10000, (2, 77))
        attention_mask = torch.ones(2, 77)
        attention_mask[:, 50:] = 0
        output = encoder(input_ids, attention_mask)
        assert output.shape == (2, 256)
```

### 3. 对比损失测试

```python
class TestContrastiveLoss:
    def test_loss_shape(self):
        """测试损失是标量"""
        criterion = ContrastiveLoss(temperature=0.07)
        image_embeds = torch.randn(4, 256)
        text_embeds = torch.randn(4, 256)
        loss, _, _ = criterion(image_embeds, text_embeds)
        assert loss.shape == ()

    def test_loss_positive(self):
        """测试损失为正数"""
        criterion = ContrastiveLoss(temperature=0.07)
        image_embeds = torch.randn(8, 256)
        text_embeds = torch.randn(8, 256)
        loss, _, _ = criterion(image_embeds, text_embeds)
        assert loss.item() > 0

    def test_perfect_alignment(self):
        """测试完美对齐时损失较低"""
        criterion = ContrastiveLoss(temperature=0.07)
        embeds = torch.randn(4, 256)
        embeds = F.normalize(embeds, dim=-1)
        loss, _, _ = criterion(embeds, embeds)
        assert loss.item() < 1.0
```

### 4. CLIP 模型测试

```python
class TestCLIPModel:
    def test_forward_pass(self):
        """测试前向传播"""
        model = CLIP(embed_dim=256, vocab_size=10000)
        images = torch.randn(2, 3, 224, 224)
        input_ids = torch.randint(0, 10000, (2, 77))
        loss, metrics = model(images, input_ids)
        assert loss.shape == ()
        assert "loss" in metrics

    def test_similarity(self):
        """测试相似度计算"""
        model = CLIP(embed_dim=256, vocab_size=10000)
        images = torch.randn(4, 3, 224, 224)
        input_ids = torch.randint(0, 10000, (4, 77))
        similarity = model.get_similarity(images, input_ids)
        assert similarity.shape == (4, 4)
```

## 集成测试

### 1. 训练流程测试

```python
class TestTrainingPipeline:
    def test_single_training_step(self):
        """测试单步训练"""
        model = CLIP(embed_dim=128, vocab_size=5000)
        trainer = CLIPTrainer(model=model, device="cpu")
        dataset = SyntheticDataset(num_samples=16, vocab_size=5000)
        dataloader = DataLoader(dataset, batch_size=4)

        batch = next(iter(dataloader))
        metrics = trainer.train_step(
            images=batch["images"],
            input_ids=batch["input_ids"],
        )
        assert metrics["loss"] > 0
        assert trainer.global_step == 1

    def test_full_training_loop(self):
        """测试完整训练循环"""
        model = CLIP(embed_dim=128, vocab_size=5000)
        trainer = CLIPTrainer(model=model, device="cpu")
        dataset = SyntheticDataset(num_samples=32, vocab_size=5000)
        dataloader = DataLoader(dataset, batch_size=8)

        history = trainer.train(
            train_loader=dataloader,
            num_epochs=2,
            log_interval=10,
        )
        assert len(history["history"]) == 2
```

### 2. 检查点测试

```python
class TestCheckpoint:
    def test_save_and_load(self, tmp_path):
        """测试检查点保存和加载"""
        model = CLIP(embed_dim=128, vocab_size=5000)
        trainer = CLIPTrainer(model=model, device="cpu")

        # 训练一步
        dataset = SyntheticDataset(num_samples=4, vocab_size=5000)
        dataloader = DataLoader(dataset, batch_size=4)
        batch = next(iter(dataloader))
        trainer.train_step(batch["images"], batch["input_ids"])

        # 保存
        checkpoint_path = tmp_path / "checkpoint.pt"
        trainer.save_checkpoint(str(checkpoint_path))
        assert checkpoint_path.exists()

        # 加载
        new_trainer = CLIPTrainer(
            model=CLIP(embed_dim=128, vocab_size=5000),
            device="cpu",
        )
        new_trainer.load_checkpoint(str(checkpoint_path))
        assert new_trainer.global_step == 1
```

## 端到端测试

### 1. 零样本分类测试

```python
class TestZeroShot:
    def test_zero_shot_classification(self):
        """测试零样本分类流程"""
        model = CLIP(embed_dim=128, vocab_size=5000)
        model.eval()

        # 创建测试数据
        images = torch.randn(5, 3, 224, 224)
        class_descriptions = ["cat", "dog", "bird", "car", "plane"]

        # 简化版零样本分类
        with torch.no_grad():
            image_embeds = model.encode_image(images)
            text_embeds = torch.randn(5, 128)
            text_embeds = F.normalize(text_embeds, dim=-1)

            similarity = torch.matmul(image_embeds, text_embeds.t())
            predictions = similarity.argmax(dim=-1)

        assert predictions.shape == (5,)
        assert all(0 <= p < 5 for p in predictions)
```

## 边界情况测试

### 1. 批大小测试

```python
def test_different_batch_sizes():
    """测试不同批大小"""
    model = CLIP(embed_dim=128, vocab_size=5000)
    for batch_size in [1, 2, 4, 8, 16]:
        images = torch.randn(batch_size, 3, 224, 224)
        input_ids = torch.randint(0, 5000, (batch_size, 77))
        loss, _ = model(images, input_ids)
        assert loss.shape == ()
```

### 2. 序列长度测试

```python
def test_different_seq_lengths():
    """测试不同序列长度"""
    encoder = TextEncoder(vocab_size=5000, embed_dim=128, max_seq_length=100)
    for seq_len in [10, 50, 100]:
        input_ids = torch.randint(0, 5000, (2, seq_len))
        output = encoder(input_ids)
        assert output.shape == (2, 128)
```

## 运行测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

```bash
pytest tests/test_clip.py::TestCLIPModel -v
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=src --cov-report=html
```

## 测试数据

### 合成数据集

```python
class SyntheticDataset(Dataset):
    def __init__(self, num_samples=1000, vocab_size=10000):
        self.num_samples = num_samples
        self.vocab_size = vocab_size

    def __getitem__(self, idx):
        return {
            "images": torch.randn(3, 224, 224),
            "input_ids": torch.randint(1, self.vocab_size, (77,)),
            "attention_mask": torch.ones(77),
        }
```

## 性能测试

### 推理速度测试

```python
def test_inference_speed():
    """测试推理速度"""
    model = CLIP(embed_dim=512, vocab_size=10000)
    model.eval()

    images = torch.randn(32, 3, 224, 224)
    input_ids = torch.randint(0, 10000, (32, 77))

    # 预热
    for _ in range(5):
        with torch.no_grad():
            model.get_similarity(images, input_ids)

    # 计时
    start = time.time()
    for _ in range(100):
        with torch.no_grad():
            model.get_similarity(images, input_ids)
    elapsed = time.time() - start

    print(f"Average inference time: {elapsed/100*1000:.2f} ms")
```
