# 05 - 开发文档

## 开发环境

### 依赖

```
Python >= 3.8
PyTorch >= 1.9
```

### 安装

```bash
pip install torch
```

## 运行指南

### 运行测试

```bash
cd projects/ner
python -m pytest tests/ -v
```

### 运行训练示例

```bash
cd projects/ner
python examples/train.py
```

## 核心算法实现细节

### CRF 前向算法实现

#### 数值稳定性

使用 log-sum-exp 技巧避免数值溢出:

```python
# 直接计算 (数值不稳定)
exp_score = torch.exp(scores)
sum_exp = exp_score.sum(dim=2)
log_sum = torch.log(sum_exp)

# log-sum-exp (数值稳定)
log_sum = torch.logsumexp(scores, dim=2)
```

#### 复杂度分析

```
时间复杂度: O(T * n^2)
空间复杂度: O(T * n)

T: 序列长度
n: 标签数量
```

### 维特比算法实现

#### 向量化优化

```python
# 非向量化 (慢)
for i in range(seq_len):
    for j in range(num_tags):
        for k in range(num_tags):
            score = delta[i-1][k] + transitions[j][k] + emissions[i][j]

# 向量化 (快)
broadcast_score = score.unsqueeze(2)  # (batch, n, 1)
broadcast_emit = emissions[:, i].unsqueeze(1)  # (batch, 1, n)
next_score = broadcast_score + self.transitions + broadcast_emit
```

#### 回溯实现

```python
# 保存每一步的最优前驱
history.append(indices)

# 从后向前回溯
for hist in reversed(history):
    best_last_tag = hist[b][best_last_tag]
    best_tags.append(best_last_tag.item())

best_tags.reverse()
```

### BiLSTM 实现

#### 双向 LSTM

```python
# 前向 LSTM
h_t_forward = LSTM_forward(x_t, h_{t-1}_forward)

# 后向 LSTM
h_t_backward = LSTM_backward(x_t, h_{t+1}_backward)

# 拼接
h_t = [h_t_forward; h_t_backward]
```

#### Dropout 使用

```python
# 嵌入后 Dropout
embeds = self.dropout(self.embedding(tokens))

# LSTM 后 Dropout
lstm_out = self.dropout(lstm_out)

# 多层 LSTM 的层间 Dropout
self.lstm = nn.LSTM(..., dropout=dropout if num_layers > 1 else 0)
```

### 梯度裁剪

```python
nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
```

作用:
- 防止梯度爆炸
- 稳定训练
- 允许使用更大的学习率

## 调试技巧

### 检查 CRF 损失

```python
# 损失应该为正数
loss = model(tokens, tags)
assert loss.item() > 0, f"Loss should be positive, got {loss.item()}"

# 损失应该随着训练下降
for epoch in range(10):
    loss = train_epoch(model, data)
    print(f"Epoch {epoch}: {loss:.4f}")
```

### 检查维特比解码

```python
# 解码结果应该在合法范围内
best_tags = model.decode(tokens)
for tags in best_tags:
    for tag in tags:
        assert 0 <= tag < num_tags
```

### 检查梯度

```python
loss = model(tokens, tags)
loss.backward()

for name, param in model.named_parameters():
    if param.requires_grad:
        assert param.grad is not None, f"No gradient for {name}"
        if torch.isnan(param.grad).any():
            print(f"NaN gradient in {name}")
```

## 常见问题

### 1. 损失不下降

可能原因:
- 学习率过大或过小
- 梯度爆炸 (需要梯度裁剪)
- 数据预处理错误

解决方案:
```python
# 调整学习率
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# 添加梯度裁剪
nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)

# 检查数据
print(tokens.min(), tokens.max())
print(tags.min(), tags.max())
```

### 2. 预测全为 O

可能原因:
- 标签分布不均衡
- 训练不充分
- 模型容量不足

解决方案:
```python
# 增加训练轮数
trainer.train(..., num_epochs=100)

# 增加模型容量
model = BiLSTM_CRF(..., hidden_dim=256, num_layers=2)

# 使用类别权重
class_weights = compute_class_weights(tags)
loss = loss * class_weights
```

### 3. 内存溢出

可能原因:
- 序列太长
- 批次太大
- 模型太大

解决方案:
```python
# 减少最大长度
max_len = 64  # 而非 512

# 减少批次大小
batch_size = 16  # 而非 64

# 使用梯度累积
loss = loss / accumulation_steps
loss.backward()
if (step + 1) % accumulation_steps == 0:
    optimizer.step()
```

### 4. 训练速度慢

可能原因:
- 没有使用 GPU
- 没有使用 pack_padded_sequence
- 数据加载瓶颈

解决方案:
```python
# 使用 GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# 使用 pack_padded_sequence
packed = pack_padded_sequence(embeds, seq_lengths, ...)

# 使用多进程数据加载
DataLoader(dataset, num_workers=4)
```

## 扩展方向

### 1. 字符级特征

```python
class CharCNN(nn.Module):
    def __init__(self, char_vocab_size, char_emb_dim, num_filters):
        self.char_embedding = nn.Embedding(char_vocab_size, char_emb_dim)
        self.conv = nn.Conv1d(char_emb_dim, num_filters, kernel_size=3)

    def forward(self, chars):
        # chars: (batch, seq_len, max_word_len)
        char_embeds = self.char_embedding(chars)
        char_features = self.conv(char_embeds)
        return char_features
```

### 2. 预训练模型

```python
from transformers import BertModel

class BertCRF(nn.Module):
    def __init__(self, num_tags):
        self.bert = BertModel.from_pretrained('bert-base-chinese')
        self.crf = CRF(num_tags)

    def forward(self, input_ids, tags, mask):
        outputs = self.bert(input_ids, attention_mask=mask)
        emissions = self.classifier(outputs.last_hidden_state)
        return self.crf(emissions, tags, mask)
```

### 3. 多任务学习

```python
class MultiTaskModel(nn.Module):
    def __init__(self, vocab_size, num_ner_tags, num_pos_tags):
        self.embedding = nn.Embedding(vocab_size, 128)
        self.lstm = nn.LSTM(128, 256, bidirectional=True)
        self.ner_crf = CRF(num_ner_tags)
        self.pos_crf = CRF(num_pos_tags)

    def forward(self, tokens, ner_tags, pos_tags, mask):
        embeds = self.embedding(tokens)
        lstm_out, _ = self.lstm(embeds)

        ner_loss = self.ner_crf(self.ner_classifier(lstm_out), ner_tags, mask)
        pos_loss = self.pos_crf(self.pos_classifier(lstm_out), pos_tags, mask)

        return ner_loss + pos_loss
```

## 性能基准

### CoNLL-2003 数据集

| 模型 | F1 |
|------|-----|
| BiLSTM | 88.17 |
| BiLSTM-CRF | 90.10 |
| BERT-CRF | 93.50 |

### 模型大小

| 配置 | 参数量 | 训练速度 |
|------|--------|---------|
| emb=64, hidden=128 | ~200K | 100 sent/s |
| emb=128, hidden=256 | ~800K | 50 sent/s |
| emb=256, hidden=512 | ~3.2M | 20 sent/s |
