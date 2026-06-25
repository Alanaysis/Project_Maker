# 视觉问答测试文档

## 1. 测试策略

### 1.1 测试层次

```
单元测试
├── 图像编码器测试
├── 文本编码器测试
├── 融合模块测试
├── 答案预测器测试
└── 数据集测试

集成测试
├── 模型前向传播测试
├── 训练流程测试
└── 推理流程测试
```

### 1.2 测试目标

1. **功能正确性**: 验证各模块功能正确
2. **形状一致性**: 验证输入输出形状正确
3. **梯度流**: 验证梯度正确传播
4. **数值稳定**: 验证无数值异常

## 2. 单元测试

### 2.1 图像编码器测试

```python
class TestImageEncoder:
    def test_resnet18_encoder(self):
        """测试 ResNet18 编码器"""
        encoder = ImageEncoder(backbone='resnet18', feature_dim=512)
        x = torch.randn(2, 3, 224, 224)
        output = encoder(x)

        # 检查输出形状
        assert output.shape == (2, 512)

        # 检查无数值异常
        assert not torch.isnan(output).any()
        assert not torch.isinf(output).any()

    def test_different_feature_dims(self):
        """测试不同特征维度"""
        for dim in [128, 256, 512, 1024]:
            encoder = ImageEncoder(backbone='resnet18', feature_dim=dim)
            assert encoder.get_output_dim() == dim

    def test_output_range(self):
        """测试输出范围"""
        encoder = ImageEncoder(backbone='resnet18', feature_dim=512)
        x = torch.randn(2, 3, 224, 224)
        output = encoder(x)

        # ReLU 后应该非负
        assert (output >= 0).all()
```

### 2.2 文本编码器测试

```python
class TestTextEncoder:
    def test_lstm_encoder(self):
        """测试 LSTM 编码器"""
        encoder = TextEncoder(
            vocab_size=1000,
            embed_dim=128,
            hidden_dim=256,
            feature_dim=512,
            rnn_type='lstm',
        )
        x = torch.randint(0, 1000, (2, 10))
        output = encoder(x)

        assert output.shape == (2, 512)
        assert not torch.isnan(output).any()

    def test_gru_encoder(self):
        """测试 GRU 编码器"""
        encoder = TextEncoder(
            vocab_size=1000,
            embed_dim=128,
            hidden_dim=256,
            feature_dim=256,
            rnn_type='gru',
        )
        x = torch.randint(0, 1000, (2, 10))
        output = encoder(x)

        assert output.shape == (2, 256)

    def test_padding(self):
        """测试 padding 处理"""
        encoder = TextEncoder(vocab_size=1000, feature_dim=512)

        # 带 padding 的输入
        x = torch.tensor([
            [5, 3, 7, 0, 0],  # 有效长度 3
            [2, 4, 6, 8, 1],  # 有效长度 5
        ])
        output = encoder(x)

        assert output.shape == (2, 512)
```

### 2.3 融合模块测试

```python
class TestFusionModule:
    def test_concat_fusion(self):
        """测试拼接融合"""
        fusion = FusionModule(
            fusion_type='concat',
            image_dim=512,
            text_dim=512,
            output_dim=1024,
        )
        img_feat = torch.randn(2, 512)
        txt_feat = torch.randn(2, 512)
        output = fusion(img_feat, txt_feat)

        assert output.shape == (2, 1024)

    def test_bilinear_fusion(self):
        """测试双线性融合"""
        fusion = FusionModule(
            fusion_type='bilinear',
            image_dim=512,
            text_dim=512,
            output_dim=1024,
        )
        img_feat = torch.randn(2, 512)
        txt_feat = torch.randn(2, 512)
        output = fusion(img_feat, txt_feat)

        assert output.shape == (2, 1024)

    def test_attention_fusion(self):
        """测试注意力融合"""
        fusion = FusionModule(
            fusion_type='attention',
            image_dim=512,
            text_dim=512,
            output_dim=1024,
        )
        img_feat = torch.randn(2, 512)
        txt_feat = torch.randn(2, 512)
        output = fusion(img_feat, txt_feat)

        assert output.shape == (2, 1024)

    def test_different_input_dims(self):
        """测试不同输入维度"""
        fusion = FusionModule(
            fusion_type='concat',
            image_dim=256,
            text_dim=512,
            output_dim=512,
        )
        img_feat = torch.randn(2, 256)
        txt_feat = torch.randn(2, 512)
        output = fusion(img_feat, txt_feat)

        assert output.shape == (2, 512)
```

### 2.4 答案预测器测试

```python
class TestAnswerPredictor:
    def test_forward(self):
        """测试前向传播"""
        predictor = AnswerPredictor(input_dim=1024, num_answers=100)
        x = torch.randn(2, 1024)
        targets = torch.randint(0, 100, (2,))

        outputs = predictor(x, targets)

        assert 'logits' in outputs
        assert 'loss' in outputs
        assert 'accuracy' in outputs
        assert outputs['logits'].shape == (2, 100)

    def test_predict(self):
        """测试预测"""
        predictor = AnswerPredictor(input_dim=1024, num_answers=100)
        x = torch.randn(2, 1024)

        predictions, confidence = predictor.predict(x)

        assert predictions.shape == (2,)
        assert confidence.shape == (2,)
        assert (predictions >= 0).all() and (predictions < 100).all()
        assert (confidence >= 0).all() and (confidence <= 1).all()

    def test_predict_top_k(self):
        """测试 top-k 预测"""
        predictor = AnswerPredictor(input_dim=1024, num_answers=100)
        x = torch.randn(2, 1024)

        predictions, confidence = predictor.predict_top_k(x, k=5)

        assert predictions.shape == (2, 5)
        assert confidence.shape == (2, 5)
```

### 2.5 数据集测试

```python
class TestVQADataset:
    def test_sample_data_creation(self):
        """测试示例数据创建"""
        questions, image_ids, answers, vocab = create_sample_data(num_samples=50)

        assert len(questions) == 50
        assert len(image_ids) == 50
        assert len(answers) == 50
        assert len(vocab) > 4

    def test_dataset_getitem(self):
        """测试数据集获取样本"""
        questions, image_ids, answers, vocab = create_sample_data(num_samples=10)
        dataset = VQADataset(questions, image_ids, answers, vocab)

        item = dataset[0]
        assert 'question_ids' in item
        assert 'image_features' in item
        assert 'answer_idx' in item

    def test_vocab_encode_decode(self):
        """测试词汇表编码解码"""
        vocab = Vocab()
        text = "what color is the cat"
        for word in text.split():
            vocab.add_word(word)

        encoded = vocab.encode(text, max_len=10)
        decoded = vocab.decode(encoded)

        assert len(encoded) == 10
        assert 'what' in decoded
```

## 3. 集成测试

### 3.1 模型前向传播测试

```python
class TestVQAModel:
    def test_model_creation(self):
        """测试模型创建"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )
        info = model.get_model_info()

        assert info['vocab_size'] == 1000
        assert info['num_answers'] == 100

    def test_forward_with_images(self):
        """测试使用图像输入的前向传播"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        images = torch.randn(2, 3, 224, 224)
        question_ids = torch.randint(0, 1000, (2, 10))
        targets = torch.randint(0, 100, (2,))

        outputs = model(images=images, question_ids=question_ids, targets=targets)

        assert 'logits' in outputs
        assert 'loss' in outputs
        assert 'image_features' in outputs
        assert 'text_features' in outputs
        assert 'fused_features' in outputs

    def test_forward_with_features(self):
        """测试使用预提取特征的前向传播"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        image_features = torch.randn(2, 256)
        question_ids = torch.randint(0, 1000, (2, 10))

        outputs = model(image_features=image_features, question_ids=question_ids)

        assert 'logits' in outputs
        assert outputs['logits'].shape == (2, 100)

    def test_different_fusion_types(self):
        """测试不同融合类型"""
        for fusion_type in ['concat', 'bilinear', 'attention']:
            model = VQAModel(
                vocab_size=1000,
                num_answers=100,
                image_feature_dim=256,
                text_feature_dim=256,
                fusion_dim=512,
                fusion_type=fusion_type,
            )

            image_features = torch.randn(2, 256)
            question_ids = torch.randint(0, 1000, (2, 10))

            outputs = model(image_features=image_features, question_ids=question_ids)
            assert outputs['logits'].shape == (2, 100)
```

### 3.2 梯度流测试

```python
class TestGradientFlow:
    def test_gradient_flow(self):
        """测试梯度流"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=50,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        image_features = torch.randn(2, 256)
        question_ids = torch.randint(0, 1000, (2, 10))
        targets = torch.randint(0, 50, (2,))

        outputs = model(
            image_features=image_features,
            question_ids=question_ids,
            targets=targets,
        )

        # 反向传播
        outputs['loss'].backward()

        # 检查梯度
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"{name} 没有梯度"
                assert not torch.isnan(param.grad).any(), f"{name} 梯度包含 NaN"
```

### 3.3 训练流程测试

```python
class TestTraining:
    def test_training_step(self):
        """测试单步训练"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=50,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        trainer = VQATrainer(model, learning_rate=1e-3)

        # 创建模拟数据
        batch = {
            'question_ids': torch.randint(0, 1000, (4, 10)),
            'image_features': torch.randn(4, 256),
            'answer_idx': torch.randint(0, 50, (4,)),
        }

        # 记录初始参数
        initial_params = {
            name: param.clone()
            for name, param in model.named_parameters()
        }

        # 训练一步
        outputs = model(
            question_ids=batch['question_ids'],
            image_features=batch['image_features'],
            targets=batch['answer_idx'],
        )

        trainer.optimizer.zero_grad()
        outputs['loss'].backward()
        trainer.optimizer.step()

        # 检查参数更新
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert not torch.equal(param, initial_params[name])
```

## 4. 边界测试

### 4.1 边界输入测试

```python
class TestEdgeCases:
    def test_single_sample(self):
        """测试单样本"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        image_features = torch.randn(1, 256)
        question_ids = torch.randint(0, 1000, (1, 10))

        outputs = model(image_features=image_features, question_ids=question_ids)
        assert outputs['logits'].shape == (1, 100)

    def test_large_batch(self):
        """测试大批次"""
        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )

        image_features = torch.randn(64, 256)
        question_ids = torch.randint(0, 1000, (64, 10))

        outputs = model(image_features=image_features, question_ids=question_ids)
        assert outputs['logits'].shape == (64, 100)

    def test_zero_padding(self):
        """测试全 padding 输入"""
        encoder = TextEncoder(vocab_size=1000, feature_dim=512)

        # 全 padding 输入
        x = torch.zeros(2, 10, dtype=torch.long)
        output = encoder(x)

        assert output.shape == (2, 512)
        assert not torch.isnan(output).any()
```

## 5. 性能测试

### 5.1 推理速度测试

```python
class TestPerformance:
    def test_inference_speed(self):
        """测试推理速度"""
        import time

        model = VQAModel(
            vocab_size=1000,
            num_answers=100,
            image_feature_dim=256,
            text_feature_dim=256,
            fusion_dim=512,
        )
        model.eval()

        image_features = torch.randn(32, 256)
        question_ids = torch.randint(0, 1000, (32, 10))

        # 预热
        for _ in range(10):
            with torch.no_grad():
                model(image_features=image_features, question_ids=question_ids)

        # 测速
        start = time.time()
        for _ in range(100):
            with torch.no_grad():
                model(image_features=image_features, question_ids=question_ids)
        elapsed = time.time() - start

        print(f"平均推理时间: {elapsed/100*1000:.2f} ms")
        assert elapsed / 100 < 0.1  # 每次推理应小于 100ms
```

### 5.2 内存使用测试

```python
    def test_memory_usage(self):
        """测试内存使用"""
        import tracemalloc

        tracemalloc.start()

        model = VQAModel(
            vocab_size=10000,
            num_answers=1000,
            image_feature_dim=512,
            text_feature_dim=512,
            fusion_dim=1024,
        )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"当前内存: {current / 1024 / 1024:.2f} MB")
        print(f"峰值内存: {peak / 1024 / 1024:.2f} MB")

        # 模型大小应在合理范围内
        assert peak / 1024 / 1024 < 500  # 小于 500MB
```

## 6. 测试运行

### 6.1 运行所有测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_vqa.py -v

# 运行特定测试类
pytest tests/test_vqa.py::TestImageEncoder -v

# 运行特定测试方法
pytest tests/test_vqa.py::TestImageEncoder::test_resnet18_encoder -v
```

### 6.2 测试覆盖率

```bash
# 安装覆盖率工具
pip install pytest-cov

# 运行带覆盖率的测试
pytest tests/ --cov=src --cov-report=html
```

### 6.3 持续集成

```yaml
# .github/workflows/test.yml
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
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ -v
```

## 7. 测试最佳实践

### 7.1 测试命名规范

- 使用 `test_` 前缀
- 描述测试的功能
- 使用下划线分隔单词

### 7.2 测试结构

```python
def test_feature():
    # 1. 准备
    model = create_model()
    input_data = create_input()

    # 2. 执行
    output = model(input_data)

    # 3. 断言
    assert output.shape == expected_shape
    assert not torch.isnan(output).any()
```

### 7.3 测试隔离

- 每个测试独立运行
- 不依赖外部状态
- 使用 mock 外部依赖

## 8. 常见问题

### 8.1 测试失败

- 检查输入形状
- 检查数据类型
- 检查设备（CPU/GPU）

### 8.2 数值异常

- 检查 NaN/Inf
- 检查数值范围
- 检查梯度爆炸

### 8.3 性能问题

- 使用小数据集测试
- 减少模型大小
- 使用 CPU 测试
