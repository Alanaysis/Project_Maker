# 04 - 测试文档

## 测试策略

### 测试层次

```
┌─────────────────────────────────┐
│        集成测试                  │  完整流程测试
├─────────────────────────────────┤
│        模块测试                  │  训练器、评估器
├─────────────────────────────────┤
│        单元测试                  │  CRF、模型、数据
└─────────────────────────────────┘
```

### 测试覆盖

| 模块 | 测试数量 | 覆盖内容 |
|------|---------|---------|
| CRF | 8 | 前向、解码、掩码、梯度 |
| BiLSTM-CRF | 5 | 前向、解码、梯度、掩码 |
| Vocabulary | 3 | 基本操作、构建、过滤 |
| TagVocabulary | 3 | 基本操作、构建、映射 |
| NERDataset | 2 | 创建、获取数据 |
| CoNLL I/O | 1 | 保存和读取 |
| Evaluator | 4 | 完美、部分、无实体、提取 |
| Trainer | 1 | 训练一个 epoch |
| Integration | 2 | 完整流程、预测 |

## 单元测试

### CRF 测试

#### 1. 初始化测试

```python
def test_initialization(self):
    assert self.crf.num_tags == 5
    assert self.crf.transitions.shape == (5, 5)
    assert self.crf.start_transitions.shape == (5,)
    assert self.crf.end_transitions.shape == (5,)
```

验证 CRF 层的参数形状正确。

#### 2. 前向传播测试

```python
def test_forward(self):
    emissions = torch.randn(2, 4, 5)
    tags = torch.randint(0, 5, (2, 4))
    loss = self.crf(emissions, tags)

    assert loss.dim() == 0  # 标量
    assert loss.item() > 0  # 正数
```

验证损失计算正确。

#### 3. 掩码测试

```python
def test_forward_with_mask(self):
    mask = torch.tensor([[1, 1, 1, 0], [1, 1, 0, 0]], dtype=torch.float32)
    loss = self.crf(emissions, tags, mask)

    assert loss.dim() == 0
    assert loss.item() > 0
```

验证掩码处理正确。

#### 4. 解码测试

```python
def test_decode(self):
    best_tags = self.crf.decode(emissions)

    assert len(best_tags) == batch_size
    for tags in best_tags:
        assert len(tags) == seq_len
        for tag in tags:
            assert 0 <= tag < num_tags
```

验证解码输出合法。

#### 5. 分数一致性测试

```python
def test_score_consistency(self):
    score = self.crf._compute_score(emissions, tags, mask)
    log_z = self.crf._compute_log_partition(emissions, mask)

    # 最优路径分数 <= 配分函数
    assert score.item() <= log_z.item() + 1e-5
```

验证数学性质正确。

#### 6. 梯度流动测试

```python
def test_gradient_flow(self):
    loss = self.crf(emissions, tags)
    loss.backward()

    assert emissions.grad is not None
    assert not torch.isnan(emissions.grad).any()
```

验证梯度计算正确。

### BiLSTM-CRF 测试

#### 1. 模型初始化测试

```python
def test_initialization(self):
    assert self.model.embedding.num_embeddings == vocab_size
    assert self.model.lstm.bidirectional
    assert self.model.hidden2tag.out_features == num_tags
```

#### 2. 完整前向传播测试

```python
def test_forward(self):
    tokens = torch.randint(0, 100, (2, 8))
    tags = torch.randint(0, 5, (2, 8))
    loss = self.model(tokens, tags)

    assert loss.dim() == 0
    assert loss.item() > 0
```

#### 3. 变长序列测试

```python
def test_mask_handling(self):
    mask = torch.ones(2, 8)
    mask[0, 5:] = 0  # 第一个序列长度为 5
    mask[1, 3:] = 0  # 第二个序列长度为 3

    best_tags = self.model.decode(tokens, mask)
    assert len(best_tags[0]) == 5
    assert len(best_tags[1]) == 3
```

### 数据处理测试

#### 1. 词表测试

```python
def test_build(self):
    vocab = Vocabulary()
    vocab.build(sentences)

    assert "hello" in vocab
    assert "world" in vocab
    assert len(vocab) > 2
```

#### 2. 标签表测试

```python
def test_build(self):
    tag_vocab = TagVocabulary()
    tag_vocab.build(tags)

    assert "B-PER" in tag_vocab
    assert "I-PER" in tag_vocab
    assert tag_vocab["O"] == 0
```

#### 3. 数据集测试

```python
def test_getitem(self):
    tokens, tag_ids, mask = dataset[0]

    assert tokens.shape == (20,)
    assert tag_ids.shape == (20,)
    assert mask.shape == (20,)
    assert mask.sum().item() == len(sentences[0])
```

## 集成测试

### 完整流程测试

```python
def test_full_pipeline(self):
    # 1. 准备数据
    sentences, tags = create_sample_data()
    vocab = Vocabulary()
    vocab.build(sentences)
    tag_vocab = TagVocabulary()
    tag_vocab.build(tags)

    # 2. 创建数据集
    dataset = NERDataset(sentences, tags, vocab, tag_vocab)
    train_dataset, val_dataset = random_split(dataset, [0.8, 0.2])

    # 3. 创建模型
    model = BiLSTM_CRF(len(vocab), len(tag_vocab))

    # 4. 训练
    trainer = Trainer(model)
    history = trainer.train(train_loader, val_loader, num_epochs=3)

    # 5. 验证
    assert "train_losses" in history
    assert "val_f1_scores" in history
    assert len(history["train_losses"]) > 0
```

### 预测功能测试

```python
def test_prediction(self):
    # 准备输入
    test_sentence = ["John", "lives", "in", "New", "York"]
    token_ids = [vocab[token] for token in test_sentence]

    # 预测
    pred_tags = trainer.predict(tokens, mask_tensor)

    assert len(pred_tags) == 1
    assert len(pred_tags[0]) == 5
```

## 测试运行

### 运行所有测试

```bash
cd projects/ner
python -m pytest tests/ -v
```

### 运行特定测试

```bash
# CRF 测试
python -m pytest tests/test_ner.py::TestCRF -v

# 模型测试
python -m pytest tests/test_ner.py::TestBiLSTMCRF -v

# 集成测试
python -m pytest tests/test_ner.py::TestIntegration -v
```

### 测试覆盖率

```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

## 测试结果示例

```
============================= test session starts ==============================
collecting ... collected 30 items

tests/test_ner.py::TestCRF::test_initialization PASSED                  [  3%]
tests/test_ner.py::TestCRF::test_forward PASSED                         [  6%]
tests/test_ner.py::TestCRF::test_forward_with_mask PASSED               [ 10%]
tests/test_ner.py::TestCRF::test_decode PASSED                          [ 13%]
tests/test_ner.py::TestCRF::test_decode_with_mask PASSED                [ 16%]
tests/test_ner.py::TestCRF::test_score_consistency PASSED               [ 20%]
tests/test_ner.py::TestCRF::test_gradient_flow PASSED                   [ 23%]
tests/test_ner.py::TestBiLSTMCRF::test_initialization PASSED            [ 26%]
tests/test_ner.py::TestBiLSTMCRF::test_forward PASSED                   [ 30%]
tests/test_ner.py::TestBiLSTMCRF::test_decode PASSED                    [ 33%]
tests/test_ner.py::TestBiLSTMCRF::test_gradient_flow PASSED             [ 36%]
tests/test_ner.py::TestBiLSTMCRF::test_mask_handling PASSED             [ 40%]
...

============================== 30 passed in 45.23s ==============================
```
