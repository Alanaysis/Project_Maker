# 05 - 开发文档

## 开发环境

### 依赖

```
Python >= 3.8
NumPy >= 1.19
PyTorch >= 1.9 (深度学习模型)
```

### 安装

```bash
pip install numpy torch
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

### CRF 前向算法

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

### 维特比算法

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

### HMM 训练

#### 极大似然估计

```python
# 初始概率
pi_counts[tag_idx] += 1
pi = (pi_counts + smooth) / (pi_counts.sum() + smooth * num_tags)

# 转移概率
A_counts[prev_tag][curr_tag] += 1
A = (A_counts + smooth) / (A_counts.sum(axis=1, keepdims=True) + smooth * num_tags)

# 发射概率
B_counts[tag_idx][word_idx] += 1
B = (B_counts + smooth) / (B_counts.sum(axis=1, keepdims=True) + smooth * vocab_size)
```

### 词典匹配

#### Trie 树

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.entity_type = None

# 插入
def add_entity(entity, entity_type):
    node = root
    for char in entity:
        if char not in node.children:
            node.children[char] = TrieNode()
        node = node.children[char]
    node.is_end = True
    node.entity_type = entity_type

# 正向最大匹配
def forward_match(text):
    i = 0
    while i < len(text):
        node = root
        j = i
        best_match = None
        while j < len(text) and text[j] in node.children:
            node = node.children[text[j]]
            j += 1
            if node.is_end:
                best_match = text[i:j]
        if best_match:
            # 找到匹配
            i += len(best_match)
        else:
            i += 1
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

#### 变长序列处理

```python
# 使用 pack_padded_sequence
seq_lengths = mask.sum(dim=1).long()
packed = pack_padded_sequence(embeds, seq_lengths.cpu(),
                               batch_first=True, enforce_sorted=False)
lstm_out, _ = self.lstm(packed)
lstm_out, _ = pad_packed_sequence(lstm_out, batch_first=True)
```

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
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
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
```

### 3. 内存溢出

解决方案:
```python
# 减少最大长度
max_len = 64

# 减少批次大小
batch_size = 16

# 使用梯度累积
loss = loss / accumulation_steps
loss.backward()
if (step + 1) % accumulation_steps == 0:
    optimizer.step()
    optimizer.zero_grad()
```
