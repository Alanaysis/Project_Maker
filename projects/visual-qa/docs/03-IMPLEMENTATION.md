# 视觉问答实现文档

## 1. 实现概述

本文档详细描述 VQA 系统的实现细节，包括各模块的代码实现和关键算法。

## 2. 图像编码器实现

### 2.1 ResNet 骨干网络

```python
class ImageEncoder(nn.Module):
    def __init__(self, backbone='resnet18', pretrained=False, feature_dim=512):
        super().__init__()

        # 创建骨干网络
        if backbone == 'resnet18':
            model = models.resnet18(pretrained=pretrained)
            backbone_out_dim = model.fc.in_features
            # 移除最后的全连接层
            self.backbone = nn.Sequential(*list(model.children())[:-1])

        # 特征投影层
        self.projection = nn.Sequential(
            nn.Linear(backbone_out_dim, feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.1),
        )

    def forward(self, images):
        # 提取特征
        features = self.backbone(images)

        # 展平特征
        if len(features.shape) > 2:
            features = features.view(features.size(0), -1)

        # 投影到指定维度
        features = self.projection(features)

        return features
```

### 2.2 关键实现细节

1. **预训练权重**: 使用 ImageNet 预训练权重
2. **参数冻结**: 可选择冻结骨干网络参数
3. **特征投影**: 将 CNN 特征投影到统一维度

## 3. 文本编码器实现

### 3.1 LSTM 编码器

```python
class TextEncoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, feature_dim):
        super().__init__()

        # 词嵌入层
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)

        # 双向 LSTM
        self.rnn = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
        )

        # 特征投影
        self.projection = nn.Linear(hidden_dim * 2, feature_dim)

    def forward(self, input_ids):
        # 词嵌入
        embedded = self.embedding(input_ids)

        # LSTM 编码
        output, (hidden, cell) = self.rnn(embedded)

        # 拼接双向最后隐藏状态
        hidden = torch.cat([hidden[-2], hidden[-1]], dim=1)

        # 投影
        features = self.projection(hidden)

        return features
```

### 3.2 Transformer 编码器

```python
class TransformerTextEncoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_heads, num_layers):
        super().__init__()

        # 词嵌入
        self.embedding = nn.Embedding(vocab_size, embed_dim)

        # 位置编码
        self.position_embedding = nn.Embedding(max_seq_len, embed_dim)

        # Transformer
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)

    def forward(self, input_ids):
        # 位置编码
        positions = torch.arange(seq_len).unsqueeze(0)

        # 嵌入
        embedded = self.embedding(input_ids) + self.position_embedding(positions)

        # Transformer 编码
        output = self.transformer(embedded)

        # 平均池化
        features = output.mean(dim=1)

        return features
```

## 4. 融合模块实现

### 4.1 拼接融合

```python
class ConcatFusion(nn.Module):
    def __init__(self, image_dim, text_dim, output_dim):
        super().__init__()

        self.fc = nn.Sequential(
            nn.Linear(image_dim + text_dim, output_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(output_dim, output_dim),
            nn.ReLU(),
        )

    def forward(self, image_features, text_features):
        # 拼接特征
        combined = torch.cat([image_features, text_features], dim=1)

        # 全连接层
        fused = self.fc(combined)

        return fused
```

### 4.2 双线性融合

```python
class BilinearFusion(nn.Module):
    def __init__(self, image_dim, text_dim, output_dim):
        super().__init__()

        # 双线性层
        self.bilinear = nn.Bilinear(image_dim, text_dim, output_dim)

    def forward(self, image_features, text_features):
        # 双线性融合
        fused = self.bilinear(image_features, text_features)

        return fused
```

### 4.3 注意力融合

```python
class AttentionFusion(nn.Module):
    def __init__(self, image_dim, text_dim, output_dim):
        super().__init__()

        # 投影层
        self.image_proj = nn.Linear(image_dim, output_dim)
        self.text_proj = nn.Linear(text_dim, output_dim)

        # 交叉注意力
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=output_dim,
            num_heads=8,
            batch_first=True,
        )

    def forward(self, image_features, text_features):
        # 投影
        image_proj = self.image_proj(image_features).unsqueeze(1)
        text_proj = self.text_proj(text_features).unsqueeze(1)

        # 拼接作为 key/value
        kv = torch.cat([image_proj, text_proj], dim=1)

        # 交叉注意力
        attended, _ = self.cross_attention(
            query=image_proj,
            key=kv,
            value=kv,
        )

        # 残差连接
        fused = attended.squeeze(1) + image_proj.squeeze(1)

        return fused
```

## 5. 答案预测器实现

### 5.1 分类预测器

```python
class AnswerPredictor(nn.Module):
    def __init__(self, input_dim, num_answers):
        super().__init__()

        # MLP 分类器
        self.classifier = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, num_answers),
        )

    def forward(self, fused_features, targets=None):
        # 预测
        logits = self.classifier(fused_features)

        outputs = {'logits': logits}

        # 计算损失
        if targets is not None:
            loss = F.cross_entropy(logits, targets)
            outputs['loss'] = loss

            # 计算准确率
            predictions = logits.argmax(dim=1)
            accuracy = (predictions == targets).float().mean()
            outputs['accuracy'] = accuracy

        return outputs

    def predict(self, fused_features):
        logits = self.classifier(fused_features)
        probabilities = F.softmax(logits, dim=1)
        confidence, predictions = probabilities.max(dim=1)
        return predictions, confidence
```

## 6. VQA 模型实现

### 6.1 模型整合

```python
class VQAModel(nn.Module):
    def __init__(self, config):
        super().__init__()

        # 图像编码器
        self.image_encoder = ImageEncoder(
            backbone=config['image_backbone'],
            feature_dim=config['image_feature_dim'],
        )

        # 文本编码器
        self.text_encoder = TextEncoder(
            vocab_size=config['vocab_size'],
            feature_dim=config['text_feature_dim'],
        )

        # 融合模块
        self.fusion = FusionModule(
            fusion_type=config['fusion_type'],
            image_dim=config['image_feature_dim'],
            text_dim=config['text_feature_dim'],
            output_dim=config['fusion_dim'],
        )

        # 答案预测器
        self.predictor = AnswerPredictor(
            input_dim=config['fusion_dim'],
            num_answers=config['num_answers'],
        )

    def forward(self, images=None, question_ids=None,
                image_features=None, targets=None):
        # 编码图像
        if image_features is None:
            image_features = self.image_encoder(images)

        # 编码文本
        text_features = self.text_encoder(question_ids)

        # 融合
        fused_features = self.fusion(image_features, text_features)

        # 预测
        outputs = self.predictor(fused_features, targets)

        # 保存中间特征
        outputs['image_features'] = image_features
        outputs['text_features'] = text_features
        outputs['fused_features'] = fused_features

        return outputs
```

## 7. 训练器实现

### 7.1 训练循环

```python
class VQATrainer:
    def __init__(self, model, learning_rate=1e-3):
        self.model = model
        self.optimizer = Adam(model.parameters(), lr=learning_rate)
        self.scheduler = StepLR(self.optimizer, step_size=10, gamma=0.5)

    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0
        total_correct = 0

        for batch in dataloader:
            # 前向传播
            outputs = self.model(
                question_ids=batch['question_ids'],
                image_features=batch['image_features'],
                targets=batch['answer_idx'],
            )

            # 计算损失
            loss = outputs['loss']

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()

            # 梯度裁剪
            nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)

            # 更新参数
            self.optimizer.step()

            # 统计
            total_loss += loss.item()
            total_correct += outputs['accuracy'].item()

        # 更新学习率
        self.scheduler.step()

        return {
            'loss': total_loss / len(dataloader),
            'accuracy': total_correct / len(dataloader),
        }

    def train(self, train_loader, val_loader, num_epochs):
        for epoch in range(num_epochs):
            # 训练
            train_metrics = self.train_epoch(train_loader)

            # 验证
            val_metrics = self.evaluate(val_loader)

            print(f"Epoch {epoch+1}: "
                  f"Train Loss={train_metrics['loss']:.4f}, "
                  f"Val Acc={val_metrics['accuracy']:.2%}")
```

## 8. 数据处理实现

### 8.1 词汇表

```python
class Vocab:
    def __init__(self):
        self.word2idx = {'<pad>': 0, '<unk>': 1}
        self.idx2word = {0: '<pad>', 1: '<unk>'}
        self.next_idx = 2

    def add_word(self, word):
        if word not in self.word2idx:
            self.word2idx[word] = self.next_idx
            self.idx2word[self.next_idx] = word
            self.next_idx += 1

    def encode(self, text, max_len=20):
        tokens = text.lower().split()
        ids = [self.word2idx.get(t, 1) for t in tokens[:max_len]]
        ids += [0] * (max_len - len(ids))
        return ids

    def decode(self, ids):
        tokens = [self.idx2word.get(i, '<unk>') for i in ids if i != 0]
        return ' '.join(tokens)
```

### 8.2 数据集

```python
class VQADataset(Dataset):
    def __init__(self, questions, image_ids, answers, vocab):
        self.questions = questions
        self.image_ids = image_ids
        self.answers = answers
        self.vocab = vocab

        # 答案到索引映射
        unique_answers = sorted(set(answers))
        self.answer2idx = {a: i for i, a in enumerate(unique_answers)}

    def __getitem__(self, idx):
        return {
            'question_ids': torch.tensor(
                self.vocab.encode(self.questions[idx]),
                dtype=torch.long,
            ),
            'image_features': torch.randn(512),  # 模拟特征
            'answer_idx': torch.tensor(
                self.answer2idx[self.answers[idx]],
                dtype=torch.long,
            ),
        }
```

## 9. 关键算法

### 9.1 注意力机制

```python
def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    缩放点积注意力

    Args:
        Q: 查询 [batch, seq_len, dim]
        K: 键 [batch, seq_len, dim]
        V: 值 [batch, seq_len, dim]
        mask: 掩码

    Returns:
        注意力输出
    """
    # 计算注意力分数
    scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(dim)

    # 应用掩码
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)

    # Softmax
    attention_weights = F.softmax(scores, dim=-1)

    # 加权求和
    output = torch.matmul(attention_weights, V)

    return output, attention_weights
```

### 9.2 双线性池化

```python
def bilinear_pooling(x, y):
    """
    双线性池化

    Args:
        x: 特征1 [batch, dim1]
        y: 特征2 [batch, dim2]

    Returns:
        双线性特征 [batch, dim1 * dim2]
    """
    # 外积
    outer = torch.einsum('bi,bj->bij', x, y)

    # 展平
    output = outer.view(outer.size(0), -1)

    return output
```

## 10. 性能优化

### 10.1 混合精度训练

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    with autocast():
        outputs = model(batch)
        loss = outputs['loss']

    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### 10.2 预提取特征

```python
# 预提取图像特征
def precompute_features(image_encoder, dataloader):
    features = {}
    for images, image_ids in dataloader:
        with torch.no_grad():
            feats = image_encoder(images)
        for id, feat in zip(image_ids, feats):
            features[id] = feat
    return features
```

## 11. 测试实现

### 11.1 单元测试

```python
def test_image_encoder():
    encoder = ImageEncoder(backbone='resnet18', feature_dim=512)
    x = torch.randn(2, 3, 224, 224)
    output = encoder(x)
    assert output.shape == (2, 512)

def test_text_encoder():
    encoder = TextEncoder(vocab_size=1000, feature_dim=512)
    x = torch.randint(0, 1000, (2, 10))
    output = encoder(x)
    assert output.shape == (2, 512)

def test_fusion():
    fusion = FusionModule(fusion_type='concat', image_dim=512, text_dim=512)
    img = torch.randn(2, 512)
    txt = torch.randn(2, 512)
    output = fusion(img, txt)
    assert output.shape == (2, 1024)
```

### 11.2 集成测试

```python
def test_full_pipeline():
    model = VQAModel(config)
    batch = create_sample_batch()

    outputs = model(
        question_ids=batch['question_ids'],
        image_features=batch['image_features'],
        targets=batch['answer_idx'],
    )

    assert 'logits' in outputs
    assert 'loss' in outputs
    assert outputs['loss'].item() > 0
```
