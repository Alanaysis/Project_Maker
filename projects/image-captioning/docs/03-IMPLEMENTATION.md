# 03 - 实现细节

## 编码器实现 (`encoder.py`)

### ResNet 骨干网络
```python
# 加载预训练 ResNet 并移除最后两层
resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
self.backbone = nn.Sequential(*list(resnet.children())[:-2])
```

**关键点**：
- 移除 `avgpool` 和 `fc` 层，保留卷积特征图
- ResNet-50 输出特征图维度：`(batch, 2048, 7, 7)`
- 展平为序列：`(batch, 49, 2048)`

### 特征投影
```python
self.projection = nn.Linear(self.feature_dim, embed_dim)
self.bn = nn.BatchNorm1d(embed_dim)
```

**作用**：
- 将高维特征映射到统一维度
- BatchNorm 稳定特征分布

### 输出格式
- 输入：`(batch, 3, 224, 224)`
- 输出：`(batch, 49, embed_dim)`
- 每个像素位置对应图像的一个区域

## 注意力机制实现 (`attention.py`)

### Bahdanau 注意力
```python
# 特征映射到注意力空间
att_encoder = self.encoder_att(encoder_out)  # (B, N, att_dim)
att_decoder = self.decoder_att(decoder_hidden)  # (B, att_dim)

# 计算注意力分数
attention_scores = self.full_att(
    self.relu(att_encoder + att_decoder.unsqueeze(1))
).squeeze(-1)

# 归一化
attention_weights = self.softmax(attention_scores)

# 加权求和
context = torch.sum(encoder_out * attention_weights.unsqueeze(-1), dim=1)
```

**维度变化**：
- `encoder_out`: (B, 49, 256)
- `att_encoder`: (B, 49, 256) -- 线性投影
- `att_decoder`: (B, 256) -- 线性投影
- `att_encoder + att_decoder.unsqueeze(1)`: (B, 49, 256) -- 广播
- `attention_scores`: (B, 49) -- 压缩最后一维
- `attention_weights`: (B, 49) -- softmax
- `context`: (B, 256) -- 加权求和

### Scaled Dot-Product 注意力
```python
Q = self.query(decoder_hidden).unsqueeze(1)  # (B, 1, att_dim)
K = self.key(encoder_out)  # (B, N, att_dim)
V = self.value(encoder_out)  # (B, N, att_dim)

scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
attention_weights = self.softmax(scores.squeeze(1))
context = torch.sum(V * attention_weights.unsqueeze(-1), dim=1)
```

## 解码器实现 (`decoder.py`)

### LSTM 初始化
```python
# 从编码器特征初始化隐藏状态
mean_encoder_out = encoder_out.mean(dim=1)  # (B, encoder_dim)
h = self.relu(self.init_h(mean_encoder_out))  # (B, hidden_dim)
c = self.relu(self.init_c(mean_encoder_out))  # (B, hidden_dim)
```

**设计意图**：
- 使用编码器特征的平均值作为初始状态
- 让解码器从一开始就"了解"图像内容
- ReLU 激活确保非负

### Teacher Forcing 训练
```python
for t in range(max(decode_lengths)):
    # 当前时间步处理的样本数（长度过滤）
    batch_size_t = sum([l > t for l in decode_lengths])

    # 词嵌入
    embeddings = self.embedding(captions[:batch_size_t, t])

    # 拼接嵌入和上下文
    lstm_input = torch.cat([embeddings, context], dim=1)

    # LSTM 更新
    h, c = self.lstm(lstm_input, (h[:batch_size_t], c[:batch_size_t]))

    # 注意力计算
    context, attn_weights = self.attention(encoder_out[:batch_size_t], h)

    # 门控机制
    gate = self.sigmoid(self.f_beta(h))
    context = gate * context

    # 预测
    preds = self.fc_out(torch.cat([h, context], dim=1))
```

**关键点**：
- 使用真实词作为下一步输入（Teacher Forcing）
- 动态批量大小：只处理未结束的序列
- 门控机制控制上下文信息使用

### 贪心搜索
```python
for _ in range(max_length):
    embeddings = self.embedding(input_word)
    lstm_input = torch.cat([embeddings, context], dim=1)
    h, c = self.lstm(lstm_input, (h, c))
    context, _ = self.attention(encoder_out, h)

    gate = self.sigmoid(self.f_beta(h))
    context = gate * context

    preds = self.fc_out(torch.cat([h, context], dim=1))
    predicted = preds.argmax(dim=-1)
```

### 束搜索 (Beam Search)
```python
# 扩展为 beam_size 个候选
h = h.expand(beam_size, -1)
c = c.expand(beam_size, -1)
context = context.expand(beam_size, -1)
encoder_out = encoder_out.expand(beam_size, -1, -1)

for _ in range(max_length):
    all_candidates = []
    for seq_idx, (seq, score, done) in enumerate(sequences):
        if done:
            all_candidates.append((seq, score, True))
            continue

        # 计算新候选
        embeddings = self.embedding(torch.tensor([seq[-1]]))
        # ... LSTM + Attention ...

        # Top-K 选择
        topk_scores, topk_indices = preds.topk(beam_size)
        for k in range(beam_size):
            all_candidates.append((seq + [word_idx], new_score, new_done))

    # 保留最佳候选
    sequences = sorted(all_candidates, reverse=True)[:beam_size]
```

## 词汇表实现 (`vocabulary.py`)

### 特殊标记
```python
PAD_TOKEN = "<pad>"    # 0 - 填充
START_TOKEN = "<start>" # 1 - 序列开始
END_TOKEN = "<end>"     # 2 - 序列结束
UNK_TOKEN = "<unk>"    # 3 - 未知词
```

### 编码过程
```python
def encode(self, sentence, max_length=None):
    tokens = [self.START_TOKEN]
    for word in sentence.lower().split():
        idx = self.word2idx.get(word, self.word2idx[self.UNK_TOKEN])
        tokens.append(self.idx2word.get(idx, self.UNK_TOKEN))
    tokens.append(self.END_TOKEN)

    indices = [self.word2idx[t] for t in tokens]
    if max_length is not None:
        indices = indices[:max_length]
    return indices
```

### 解码过程
```python
def decode(self, indices, skip_special=True):
    special_indices = {self.word2idx[self.PAD_TOKEN],
                       self.word2idx[self.START_TOKEN],
                       self.word2idx[self.END_TOKEN]}

    words = []
    for idx in indices:
        word = self.idx2word.get(idx, self.UNK_TOKEN)
        if skip_special and idx in special_indices:
            continue
        words.append(word)
    return " ".join(words)
```

## 训练器实现 (`trainer.py`)

### 训练循环
```python
def train_epoch(self):
    self.model.train()
    for images, captions, lengths in self.train_loader:
        # 前向传播
        predictions, _ = self.model(images, captions, lengths)

        # 计算损失
        targets = captions[:, 1:]  # 去掉 <start>
        loss = self.criterion(predictions, targets)

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)
        self.optimizer.step()
```

### 学习率调度
```python
self.scheduler = torch.optim.lr_scheduler.StepLR(
    self.optimizer, step_size=5, gamma=0.8
)
```

### 检查点保存
```python
checkpoint = {
    "model_state_dict": self.model.state_dict(),
    "optimizer_state_dict": self.optimizer.state_dict(),
    "scheduler_state_dict": self.scheduler.state_dict(),
    "history": self.history,
}
torch.save(checkpoint, filepath)
```

## 数据集实现 (`dataset.py`)

### 图像预处理
```python
self.transform = transforms.Compose([
    transforms.Resize((image_size, image_size)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])
```

### 批量整理
```python
def collate_fn(batch):
    # 按长度降序排列
    batch.sort(key=lambda x: x[2], reverse=True)
    images, captions, lengths = zip(*batch)

    # 堆叠图像
    images = torch.stack(images)

    # 填充描述序列
    max_length = max(lengths)
    padded_captions = torch.zeros(len(captions), max_length, dtype=torch.long)
    for i, cap in enumerate(captions):
        padded_captions[i, :lengths[i]] = cap[:lengths[i]]

    return images, padded_captions, torch.tensor(lengths)
```

## 调试技巧

### 1. 维度检查
```python
print(f"encoder_out shape: {encoder_out.shape}")
print(f"h shape: {h.shape}")
print(f"context shape: {context.shape}")
```

### 2. 梯度检查
```python
loss.backward()
for name, param in model.named_parameters():
    if param.grad is None:
        print(f"警告: {name} 没有梯度")
```

### 3. 数值稳定性
```python
# 使用 log_softmax 防止数值溢出
log_probs = F.log_softmax(logits, dim=-1)

# 梯度裁剪
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
```
