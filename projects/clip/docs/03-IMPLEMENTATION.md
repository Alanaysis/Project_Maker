# 03 - 实现文档

## 实现概述

本文档详细说明 CLIP 模型的实现细节，包括各个组件的代码实现和关键算法。

## 核心组件实现

### 1. 图像编码器

```python
class ImageEncoder(nn.Module):
    def __init__(self, embed_dim=512, hidden_dim=256):
        super().__init__()
        # 卷积特征提取
        self.conv_layers = nn.Sequential(
            nn.Conv2d(3, 64, 7, stride=2, padding=3),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(3, stride=2, padding=1),
            # 残差块
            self._make_residual_block(64, 128, stride=2),
            self._make_residual_block(128, 256, stride=2),
            self._make_residual_block(256, 512, stride=2),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        # 投影头
        self.projection = nn.Sequential(
            nn.Linear(512, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, embed_dim),
        )

    def forward(self, x):
        features = self.conv_layers(x)
        features = features.flatten(start_dim=1)
        embeddings = self.projection(features)
        return F.normalize(embeddings, dim=-1)
```

**关键实现点：**

1. **残差块**：增强梯度流动
2. **全局平均池化**：将特征图转换为向量
3. **投影头**：将特征映射到嵌入空间
4. **L2 归一化**：确保嵌入在单位球面上

### 2. 文本编码器

```python
class TextEncoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_heads, num_layers):
        super().__init__()
        # 嵌入层
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = nn.Embedding(max_seq_length, embed_dim)

        # Transformer 编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim * 4,
            dropout=0.1,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer, num_layers=num_layers
        )

        # 投影头
        self.projection = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, embed_dim),
        )

    def forward(self, input_ids, attention_mask=None):
        # 嵌入
        position_ids = torch.arange(seq_length)
        token_embeds = self.token_embedding(input_ids)
        position_embeds = self.position_embedding(position_ids)
        hidden_states = token_embeds + position_embeds

        # Transformer 编码
        hidden_states = self.transformer(hidden_states, mask=attention_mask)
        hidden_states = self.ln_final(hidden_states)

        # 使用 EOS token
        eos_indices = input_ids.ne(0).sum(dim=1) - 1
        hidden_states = hidden_states[torch.arange(batch_size), eos_indices]

        # 投影
        embeddings = self.projection(hidden_states)
        return F.normalize(embeddings, dim=-1)
```

**关键实现点：**

1. **位置编码**：学习位置嵌入
2. **Transformer**：标准编码器架构
3. **EOS token**：使用序列末尾作为句子表示
4. **注意力掩码**：处理变长序列

### 3. 对比损失

```python
class CLIPLoss(nn.Module):
    def __init__(self, temperature=0.07, learnable_temperature=True):
        super().__init__()
        if learnable_temperature:
            self.logit_scale = nn.Parameter(
                torch.ones([]) * torch.log(torch.tensor(1.0 / temperature))
            )
        else:
            self.register_buffer("logit_scale", torch.tensor(1.0 / temperature))

    def forward(self, image_embeddings, text_embeddings):
        # 归一化
        image_embeddings = F.normalize(image_embeddings, dim=-1)
        text_embeddings = F.normalize(text_embeddings, dim=-1)

        # 计算相似度
        logit_scale = self.logit_scale.exp()
        logits_per_image = logit_scale * torch.matmul(
            image_embeddings, text_embeddings.t()
        )
        logits_per_text = logits_per_image.t()

        # 标签
        labels = torch.arange(batch_size)

        # 交叉熵损失
        image_to_text_loss = F.cross_entropy(logits_per_image, labels)
        text_to_image_loss = F.cross_entropy(logits_per_text, labels)
        loss = (image_to_text_loss + text_to_image_loss) / 2

        return loss, metrics
```

**关键实现点：**

1. **可学习温度**：自动调整相似度锐度
2. **对称损失**：双向对齐
3. **指标计算**：准确率、温度等

### 4. CLIP 主模型

```python
class CLIP(nn.Module):
    def __init__(self, embed_dim, vocab_size, **kwargs):
        super().__init__()
        self.image_encoder = ImageEncoder(embed_dim=embed_dim)
        self.text_encoder = TextEncoder(vocab_size=vocab_size, embed_dim=embed_dim)
        self.loss_fn = CLIPLoss(temperature=0.07)

    def forward(self, images, input_ids, attention_mask=None):
        image_embeddings = self.encode_image(images)
        text_embeddings = self.encode_text(input_ids, attention_mask)
        loss, metrics = self.loss_fn(image_embeddings, text_embeddings)
        return loss, metrics

    def zero_shot_classify(self, images, class_descriptions, tokenizer):
        image_embeddings = self.encode_image(images)
        text_embeddings = self.encode_text(tokenizer(class_descriptions))
        similarity = torch.matmul(image_embeddings, text_embeddings.t())
        predictions = similarity.argmax(dim=-1)
        return predictions
```

## 训练实现

### 训练循环

```python
class CLIPTrainer:
    def train_step(self, images, input_ids, attention_mask):
        self.model.train()
        loss, metrics = self.model(images, input_ids, attention_mask)
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()
        self.scheduler.step()
        return metrics
```

### 学习率调度

```python
# 余弦退火
scheduler = CosineAnnealingLR(
    optimizer,
    T_max=max_steps,
    eta_min=learning_rate * 0.1,
)

# 线性预热
def warmup_lr(step):
    if step < warmup_steps:
        return step / warmup_steps
    return 1.0
```

### 梯度裁剪

```python
nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

## 数据处理

### 图像预处理

```python
image_transform = transforms.Compose([
    transforms.RandomResizedCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(0.4, 0.4, 0.4),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])
```

### 文本预处理

```python
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

def tokenize_text(text):
    return tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=77,
        return_tensors="pt",
    )
```

## 性能优化

### 混合精度训练

```python
scaler = torch.cuda.amp.GradScaler()

with torch.cuda.amp.autocast():
    loss, metrics = model(images, input_ids)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

### 梯度累积

```python
accumulation_steps = 4

for i, batch in enumerate(dataloader):
    loss, _ = model(batch)
    loss = loss / accumulation_steps
    loss.backward()

    if (i + 1) % accumulation_steps == 0:
        optimizer.step()
        optimizer.zero_grad()
```

## 调试技巧

### 1. 检查嵌入归一化

```python
embeddings = model.encode_image(images)
norms = torch.norm(embeddings, dim=1)
assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)
```

### 2. 检查相似度矩阵

```python
similarity = model.get_similarity(images, input_ids)
print(f"Similarity range: [{similarity.min():.3f}, {similarity.max():.3f}]")
print(f"Diagonal (should be high): {similarity.diag().mean():.3f}")
```

### 3. 监控训练指标

```python
metrics = {
    "loss": loss.item(),
    "i2t_acc": i2t_acc,
    "t2i_acc": t2i_acc,
    "temperature": 1.0 / logit_scale.item(),
}
```

## 常见问题

### Q: 训练不稳定

**解决方案：**
- 降低学习率
- 增加预热步数
- 使用梯度裁剪
- 减小批次大小

### Q: 过拟合

**解决方案：**
- 增加数据增强
- 使用 dropout
- 增加权重衰减
- 减少模型复杂度

### Q: 内存溢出

**解决方案：**
- 减小批次大小
- 使用梯度累积
- 使用混合精度训练
- 使用梯度检查点
