# 02 - 架构设计

## 整体架构

### 系统架构图
```
┌─────────────────────────────────────────────────────────┐
│                  ImageCaptioningModel                   │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  CNNEncoder   │───▶│   Attention   │◀──│LSTMDecoder│ │
│  │  (ResNet)     │    │  (Bahdanau)   │    │           │ │
│  └──────────────┘    └──────────────┘    └───────────┘ │
│         │                    │                   ▲      │
│         ▼                    ▼                   │      │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  特征提取     │    │  上下文向量   │    │ 词概率分布│ │
│  └──────────────┘    └──────────────┘    └───────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 数据流
```
输入图像 (B, 3, 224, 224)
        │
        ▼
┌─────────────────┐
│   CNNEncoder    │  ResNet-18/50 + BatchNorm
│  (预训练权重)   │
└────────┬────────┘
         │
         ▼
特征序列 (B, 49, 256)  ──┐
         │                │
         ▼                │
┌─────────────────┐       │
│   Attention     │◀──────┤
│  (Bahdanau)     │       │
└────────┬────────┘       │
         │                │
    上下文向量 (B, 256)   │
         │                │
         ▼                │
┌─────────────────┐       │
│  LSTMDecoder    │       │
│  (LSTMCell)     │       │
└────────┬────────┘       │
         │                │
         ▼                │
词概率分布 (B, seq_len, vocab_size)
```

## 模块设计

### 1. CNNEncoder（编码器）

**职责**：将输入图像转换为特征序列

**设计决策**：
- 使用预训练 ResNet 作为骨干网络
- 移除最后的全连接层和平均池化层
- 通过线性投影层统一特征维度
- 使用 BatchNorm 稳定特征分布

**输入/输出**：
- 输入：`(batch_size, 3, H, W)` 图像张量
- 输出：`(batch_size, num_pixels, embed_dim)` 特征序列

**配置选项**：
- `backbone`: resnet18/34/50（精度 vs 速度权衡）
- `embed_dim`: 输出特征维度
- `pretrained`: 是否使用预训练权重

### 2. Attention（注意力机制）

**职责**：计算解码器隐藏状态与图像特征的注意力权重

**设计决策**：
- 实现两种注意力机制：Bahdanau 和 Scaled Dot-Product
- 使用可学习的线性层进行特征映射
- 输出归一化的注意力权重

**Bahdanau 注意力**：
```python
# 特征映射
att_encoder = W_encoder * encoder_out    # (B, N, att_dim)
att_decoder = W_decoder * decoder_hidden # (B, att_dim)

# 注意力分数
score = V * tanh(att_encoder + att_decoder)  # (B, N, 1)

# 归一化
weights = softmax(score)  # (B, N)

# 上下文向量
context = sum(weights * encoder_out)  # (B, encoder_dim)
```

**Scaled Dot-Product 注意力**：
```python
Q = W_q * decoder_hidden  # (B, 1, att_dim)
K = W_k * encoder_out     # (B, N, att_dim)
V = W_v * encoder_out     # (B, N, att_dim)

score = Q * K^T / sqrt(d_k)  # (B, 1, N)
weights = softmax(score)
context = weights * V
```

### 3. LSTMDecoder（解码器）

**职责**：在注意力机制辅助下逐词生成描述

**设计决策**：
- 使用 LSTMCell 而非 LSTM（更灵活的控制）
- 从编码器特征初始化隐藏状态
- 使用门控机制选择性使用上下文信息
- 支持贪心搜索和束搜索

**前向传播流程**：
```python
# 初始化
h, c = init_from_encoder(encoder_out)

# 每个时间步
for t in range(max_length):
    # 1. 词嵌入 + 上下文
    input = concat(embedding(word_t), context_prev)

    # 2. LSTM 更新
    h, c = LSTMCell(input, (h, c))

    # 3. 注意力计算
    context, weights = attention(encoder_out, h)

    # 4. 门控机制
    gate = sigmoid(W_gate * h)
    context = gate * context

    # 5. 预测
    prediction = fc_out(concat(h, context))
```

**初始化策略**：
- 使用编码器特征的平均值初始化 h_0 和 c_0
- 通过线性层映射到 LSTM 隐藏状态维度

### 4. ImageCaptioningModel（完整模型）

**职责**：整合编码器和解码器，提供统一接口

**设计决策**：
- 编码器和解码器共享嵌入维度
- 支持训练和推理两种模式
- 提供参数统计功能

**训练模式**：
```python
predictions, attention_weights = model(images, captions, lengths)
loss = CrossEntropyLoss(predictions, targets)
```

**推理模式**：
```python
captions = model.generate(images, vocabulary, max_length=50)
```

## 关键设计选择

### 1. 为什么用 LSTMCell 而非 LSTM？
- LSTMCell 允许在每个时间步更灵活地控制
- 可以在时间步之间插入其他操作（如注意力）
- 更容易实现自定义的解码逻辑

### 2. 为什么用门控机制？
- 控制上下文信息的使用程度
- 防止无关信息干扰预测
- 类似于 LSTM 的门控思想

### 3. 为什么用编码器特征初始化隐藏状态？
- 让解码器从一开始就"了解"图像内容
- 比随机初始化更有效
- 建立编码器和解码器的语义联系

### 4. 批量处理中的序列长度对齐
- 使用填充（padding）对齐不同长度的序列
- 按长度降序排列便于处理
- 使用 mask 忽略填充位置的损失
