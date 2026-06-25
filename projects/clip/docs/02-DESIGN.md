# 02 - 设计文档

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIP Model                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │  Image Encoder  │         │  Text Encoder   │           │
│  │  (ResNet-like)  │         │  (Transformer)  │           │
│  └────────┬────────┘         └────────┬────────┘           │
│           │                           │                     │
│           ▼                           ▼                     │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │  Projection     │         │  Projection     │           │
│  │  Head           │         │  Head           │           │
│  └────────┬────────┘         └────────┬────────┘           │
│           │                           │                     │
│           └───────────┬───────────────┘                     │
│                       ▼                                     │
│              ┌─────────────────┐                            │
│              │ Contrastive Loss│                            │
│              └─────────────────┘                            │
└─────────────────────────────────────────────────────────────┘
```

### 模块划分

```
src/
├── clip_model.py      # 主模型类
├── encoders.py        # 编码器实现
├── contrastive_loss.py # 损失函数
├── trainer.py         # 训练器
└── dataset.py         # 数据集工具
```

## 详细设计

### 1. 图像编码器 (ImageEncoder)

#### 架构选择

采用简化的 ResNet 架构：
- 卷积层提取特征
- 残差连接增强梯度流
- 全局平均池化得到固定大小表示

#### 层结构

```python
ImageEncoder:
├── Conv2d(3, 64, 7, stride=2) + BN + ReLU
├── MaxPool2d(3, stride=2)
├── ResidualBlock(64 → 128)
├── ResidualBlock(128 → 256)
├── ResidualBlock(256 → 512)
├── AdaptiveAvgPool2d(1, 1)
├── Linear(512 → hidden_dim)
├── ReLU
└── Linear(hidden_dim → embed_dim)
```

#### 输出

- 输出维度：`[batch_size, embed_dim]`
- L2 归一化

### 2. 文本编码器 (TextEncoder)

#### 架构选择

采用标准 Transformer 编码器：
- Token 嵌入 + 位置嵌入
- 多头自注意力
- 前馈网络
- 层归一化

#### 层结构

```python
TextEncoder:
├── TokenEmbedding(vocab_size, embed_dim)
├── PositionEmbedding(max_seq_length, embed_dim)
├── TransformerEncoder × num_layers
│   ├── MultiHeadAttention
│   ├── LayerNorm
│   ├── FeedForward
│   └── LayerNorm
├── LayerNorm
├── Linear(embed_dim → hidden_dim)
├── GELU
└── Linear(hidden_dim → embed_dim)
```

#### 输出

- 使用 EOS token 的表示作为句子嵌入
- 输出维度：`[batch_size, embed_dim]`
- L2 归一化

### 3. 对比损失 (ContrastiveLoss)

#### 损失计算

```python
# 1. 计算相似度矩阵
logits_per_image = image_embeds @ text_embeds.T / temperature
logits_per_text = logits_per_image.T

# 2. 创建标签（对角线为正样本）
labels = torch.arange(batch_size)

# 3. 计算交叉熵损失
loss_i2t = cross_entropy(logits_per_image, labels)
loss_t2i = cross_entropy(logits_per_text, labels)

# 4. 对称损失
loss = (loss_i2t + loss_t2i) / 2
```

#### 温度参数

可学习的温度参数：
```python
logit_scale = nn.Parameter(log(1/temperature))
scale = exp(logit_scale)
logits = similarity * scale
```

### 4. CLIP 主模型

#### 接口设计

```python
class CLIP(nn.Module):
    def encode_image(images) -> image_embeddings
    def encode_text(input_ids, attention_mask) -> text_embeddings
    def forward(images, input_ids, attention_mask) -> (loss, metrics)
    def get_similarity(images, input_ids) -> similarity_matrix
    def zero_shot_classify(images, class_descriptions) -> predictions
```

### 5. 训练器 (CLIPTrainer)

#### 训练流程

```python
for epoch in range(num_epochs):
    for batch in train_loader:
        # 前向传播
        loss, metrics = model(images, input_ids)

        # 反向传播
        loss.backward()
        clip_grad_norm_(parameters, max_norm=1.0)
        optimizer.step()
        scheduler.step()

    # 验证
    val_metrics = validate(val_loader)

    # 保存检查点
    if loss < best_loss:
        save_checkpoint()
```

#### 学习率调度

采用余弦退火调度：
```python
scheduler = CosineAnnealingLR(
    optimizer,
    T_max=max_steps,
    eta_min=lr * 0.1,
)
```

### 6. 数据集 (Dataset)

#### 数据格式

```python
{
    "image_path": "path/to/image.jpg",
    "text": "a photo of a cat sitting on a couch"
}
```

#### 数据增强

- 图像：随机裁剪、颜色抖动、归一化
- 文本：截断、填充

## 设计决策

### 1. 为什么使用双编码器？

双编码器的优势：
- 模块化：可以独立更新编码器
- 效率：编码只需要前向传播一次
- 灵活：可以处理不同模态的输入

### 2. 为什么使用对称损失？

对称损失确保：
- 图像到文本的对齐
- 文本到图像的对齐
- 双向一致性

### 3. 为什么使用可学习温度？

可学习温度的优势：
- 自动调整相似度分布的锐度
- 适应不同数据集的特点
- 提高训练稳定性

## 性能考虑

### 计算复杂度

- 图像编码器：O(H × W × C × filters)
- 文本编码器：O(seq_len² × embed_dim)
- 对比损失：O(batch_size² × embed_dim)

### 内存优化

- 梯度检查点
- 混合精度训练
- 梯度累积

### 批大小

CLIP 需要大批次训练：
- 更多负样本
- 更稳定的梯度估计
- 推荐：256-4096
