# 03 - 实现文档

## CRF 实现详解

### 参数初始化

```python
# 转移矩阵: transitions[i][j] = score(j -> i)
self.transitions = nn.Parameter(torch.randn(num_tags, num_tags))

# 起始和结束转移
self.start_transitions = nn.Parameter(torch.randn(num_tags))
self.end_transitions = nn.Parameter(torch.randn(num_tags))
```

使用均匀分布初始化 (-0.1, 0.1)，避免初始值过大导致数值问题。

### 前向算法 (计算配分函数)

```python
def _compute_log_partition(self, emissions, mask):
    # 初始化
    alpha = self.start_transitions + emissions[:, 0]

    for i in range(1, seq_len):
        # alpha[b, j] = logsumexp(alpha[b, k] + transitions[j, k] + emissions[b, j])
        emit_score = emissions[:, i].unsqueeze(2)     # (batch, T, 1)
        trans_score = self.transitions.unsqueeze(0)    # (1, T, T)
        alpha_expand = alpha.unsqueeze(1)              # (batch, 1, T)

        scores = alpha_expand + trans_score + emit_score
        new_alpha = torch.logsumexp(scores, dim=2)     # (batch, T)

        # 掩码处理
        mask_i = mask[:, i].unsqueeze(1)
        alpha = new_alpha * mask_i + alpha * (1 - mask_i)

    alpha += self.end_transitions
    return torch.logsumexp(alpha, dim=1)
```

关键点:
1. 使用 log-sum-exp 避免数值溢出
2. 掩码确保只计算有效位置

### 维特比算法

```python
def _viterbi_decode(self, emissions, mask):
    # 初始化
    score = self.start_transitions + emissions[:, 0]
    history = []

    for i in range(1, seq_len):
        # score[b, k] + transitions[j, k] + emissions[b, j]
        broadcast_score = score.unsqueeze(2)
        broadcast_emit = emissions[:, i].unsqueeze(1)
        next_score = broadcast_score + self.transitions + broadcast_emit

        next_score, indices = next_score.max(dim=1)  # 取最优前驱

        mask_i = mask[:, i].unsqueeze(1)
        score = next_score * mask_i + score * (1 - mask_i)
        history.append(indices)

    # 回溯
    seq_lengths = mask.sum(dim=1).long() - 1
    # ...
```

关键点:
1. 维护分数矩阵和历史矩阵
2. 最后回溯得到最优路径

### 路径分数计算

```python
def _compute_score(self, emissions, tags, mask):
    # 起始分数
    score = self.start_transitions[tags[:, 0]]
    score += emissions[torch.arange(batch_size), 0, tags[:, 0]]

    for i in range(1, seq_len):
        # 发射分数
        score += emissions[torch.arange(batch_size), i, tags[:, i]] * mask[:, i]
        # 转移分数
        score += self.transitions[tags[:, i], tags[:, i-1]] * mask[:, i]

    # 结束分数
    seq_lengths = mask.sum(dim=1).long() - 1
    last_tags = tags[torch.arange(batch_size), seq_lengths]
    score += self.end_transitions[last_tags]

    return score
```

## BiLSTM-CRF 实现详解

### 嵌入层

```python
self.embedding = nn.Embedding(
    num_embeddings=vocab_size,
    embedding_dim=embedding_dim,
    padding_idx=pad_idx
)
```

padding_idx=0 确保填充向量始终为零。

### 双向 LSTM

```python
self.lstm = nn.LSTM(
    input_size=embedding_dim,
    hidden_size=hidden_dim,
    num_layers=num_layers,
    batch_first=True,
    bidirectional=True,
    dropout=dropout if num_layers > 1 else 0
)
```

输出维度: hidden_dim * 2 (前向 + 后向拼接)

### 线性映射

```python
self.hidden2tag = nn.Linear(hidden_dim * 2, num_tags)
```

将 BiLSTM 输出映射到标签空间，得到发射分数。

### 变长序列处理

```python
if mask is not None:
    seq_lengths = mask.sum(dim=1).long()
    packed = pack_padded_sequence(
        embeds, seq_lengths.cpu(), batch_first=True, enforce_sorted=False
    )
    lstm_out, _ = self.lstm(packed)
    lstm_out, _ = pad_packed_sequence(lstm_out, batch_first=True)
```

使用 pack_padded_sequence 避免在填充位置计算。

## 数据处理实现

### 词表构建

```python
class Vocabulary:
    def build(self, sentences):
        # 统计词频
        for sentence in sentences:
            for token in sentence:
                self.token_counts[token] += 1

        # 添加满足最小频率的词
        for token, count in self.token_counts.items():
            if count >= self.min_freq:
                self.token2idx[token] = len(self.token2idx)
```

特殊标记:
- `<PAD>`: 索引 0，用于填充
- `<UNK>`: 索引 1，用于未知词

### 数据集实现

```python
class NERDataset(Dataset):
    def __getitem__(self, idx):
        # 转换为索引
        token_ids = [self.vocab[token] for token in sentence]
        tag_ids = [self.tag_vocab[tag] for tag in tag_seq]

        # 填充到固定长度
        token_ids = token_ids + [self.vocab.pad_idx] * pad_len
        tag_ids = tag_ids + [0] * pad_len
        mask = [1] * seq_len + [0] * pad_len

        return tokens, tag_ids, mask
```

### CoNLL 文件读取

```python
def read_conll_file(filepath):
    for line in f:
        line = line.strip()
        if not line:
            # 空行表示句子结束
            if current_tokens:
                sentences.append(current_tokens)
                tags.append(current_tags)
        else:
            parts = line.split()
            current_tokens.append(parts[0])
            current_tags.append(parts[1])
```

## 评估实现

### 实体提取

```python
def _extract_entities(self, tag_sequences):
    for i, tag in enumerate(tag_seq):
        if tag.startswith("B-"):
            # 保存之前的实体
            if current_entity:
                entities.append((current_entity, current_start, i-1))
            # 开始新实体
            current_entity = tag[2:]
            current_start = i

        elif tag.startswith("I-"):
            if current_entity == tag[2:]:
                continue  # 继续当前实体
            else:
                # 类型不匹配
                entities.append((current_entity, current_start, i-1))

        else:  # O
            if current_entity:
                entities.append((current_entity, current_start, i-1))
```

### 指标计算

```python
def _count_matches(self, true_entities, pred_entities, entity_type):
    true_set = {(t, s, e) for t, s, e in true_entities if t == entity_type}
    pred_set = {(t, s, e) for t, s, e in pred_entities if t == entity_type}

    correct = len(true_set & pred_set)
    pred_count = len(pred_set)
    true_count = len(true_set)

    return correct, pred_count, true_count
```

## 训练实现

### 训练循环

```python
def train_epoch(self, dataloader):
    for tokens, tags, mask in dataloader:
        # 前向传播
        loss = self.model(tokens, tags, mask)

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()

        # 梯度裁剪
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)

        self.optimizer.step()
```

### 早停机制

```python
def train(self, train_loader, val_loader, num_epochs, early_stopping):
    for epoch in range(num_epochs):
        avg_loss = self.train_epoch(train_loader)
        val_results = self.evaluate(val_loader)
        val_f1 = val_results["overall"]["f1"]

        if val_f1 > best_f1:
            best_f1 = val_f1
            patience_counter = 0
            best_state = model.state_dict()
        else:
            patience_counter += 1
            if patience_counter >= early_stopping:
                break

    # 恢复最佳模型
    model.load_state_dict(best_state)
```

## 性能优化

### 数值稳定性

```python
# 使用 log-sum-exp 避免指数溢出
torch.logsumexp(scores, dim=2)

# 使用 pack_padded_sequence 避免无效计算
packed = pack_padded_sequence(embeds, seq_lengths, ...)
```

### 内存优化

```python
# 使用梯度累积
loss = loss / accumulation_steps
loss.backward()
if (step + 1) % accumulation_steps == 0:
    optimizer.step()
    optimizer.zero_grad()
```

### 计算优化

```python
# 使用 GPU 加速
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
```
