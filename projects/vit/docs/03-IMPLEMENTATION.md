# 03 - 实现文档：Vision Transformer

## 1. 实现概览

### 1.1 文件结构

```
src/
├── __init__.py          # 包初始化，导出公共接口
├── patch_embedding.py   # Patch Embedding 实现
├── attention.py         # Multi-Head Self-Attention
├── transformer.py       # Transformer Encoder
├── vit.py              # 完整 ViT 模型
├── trainer.py          # 训练器
└── visualization.py    # 可视化工具
```

### 1.2 实现顺序

1. `patch_embedding.py` - 基础组件
2. `attention.py` - 核心机制
3. `transformer.py` - 编码器
4. `vit.py` - 完整模型
5. `trainer.py` - 训练支持
6. `visualization.py` - 可视化

## 2. 核心实现细节

### 2.1 Patch Embedding

**关键实现**：使用 `nn.Conv2d` 实现 patch 分割 + 线性投影

```python
# kernel_size = patch_size, stride = patch_size
# 效果：不重叠地提取 patches，同时进行线性投影
self.projection = nn.Conv2d(
    in_channels=in_channels,
    out_channels=embed_dim,
    kernel_size=patch_size,
    stride=patch_size,
)
```

**为什么这样实现**：
- Conv2d 的 stride=kernel_size 确保 patches 不重叠
- 每个 kernel 对应一个 patch 的线性投影
- PyTorch 对 Conv2d 有底层优化

**CLS Token 拼接**：
```python
# CLS token 形状: (1, 1, D)
# 扩展到 batch 维度: (B, 1, D)
cls_tokens = self.cls_token.expand(B, -1, -1)
# 在序列维度拼接: (B, N, D) + (B, 1, D) -> (B, N+1, D)
x = torch.cat([cls_tokens, x], dim=1)
```

### 2.2 Multi-Head Self-Attention

**核心公式**：
```
Attention(Q, K, V) = softmax(Q @ K^T / sqrt(d_k)) @ V
```

**高效实现**：使用单个线性层计算 Q, K, V

```python
# 一次性计算 Q, K, V，比三个独立线性层更高效
self.qkv = nn.Linear(embed_dim, embed_dim * 3)

# 拆分并分头
qkv = qkv.reshape(B, N, 3, H, d_k)
qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, H, N, d_k)
q, k, v = qkv.unbind(0)
```

**缩放因子**：
```python
# 防止点积过大导致 softmax 梯度消失
self.scale = self.head_dim ** -0.5  # 1/sqrt(d_k)
attn = (q @ k.transpose(-2, -1)) * self.scale
```

### 2.3 Transformer Block

**Pre-LN 架构**：
```python
# 子层 1: Self-Attention
residual = x
x_norm = self.norm1(x)  # Layer Norm 在前
attn_out, attn_weights = self.attn(x_norm)
x = residual + attn_out  # 残差连接

# 子层 2: Feed-Forward
residual = x
x_norm = self.norm2(x)  # Layer Norm 在前
ffn_out = self.ffn(x_norm)
x = residual + ffn_out  # 残差连接
```

**为什么用 Pre-LN**：
- 训练更稳定，不需要 learning rate warmup
- 梯度流更顺畅
- 是现代 Transformer 的标准做法

### 2.4 Feed-Forward Network

```python
# 两层全连接，中间使用 GELU 激活
self.fc1 = nn.Linear(in_features, hidden_features)  # 通常 4x
self.act = nn.GELU()
self.fc2 = nn.Linear(hidden_features, in_features)
```

**GELU vs ReLU**：
- GELU 是平滑的，ReLU 在 0 点有拐点
- GELU 在 Transformer 中效果更好
- ViT 论文使用 GELU

## 3. 权重初始化

### 3.1 Patch Embedding 初始化

```python
# Conv2d: Xavier 均匀分布
nn.init.xavier_uniform_(self.projection.weight.view(embed_dim, -1))

# CLS Token 和位置编码: 截断正态分布
nn.init.trunc_normal_(self.cls_token, std=0.02)
nn.init.trunc_normal_(self.position_embedding, std=0.02)
```

### 3.2 Transformer 初始化

```python
# Linear 层: Xavier 均匀分布
nn.init.xavier_uniform_(m.weight)

# LayerNorm: 权重为 1，偏置为 0
nn.init.ones_(m.weight)
nn.init.zeros_(m.bias)
```

## 4. 训练技巧

### 4.1 AdamW 优化器

```python
# AdamW 相比 Adam 的权重衰减实现更正确
optimizer = optim.AdamW(
    model.parameters(),
    lr=3e-4,
    weight_decay=0.01,
    betas=(0.9, 0.999),
)
```

### 4.2 Cosine Annealing

```python
# 学习率按余弦函数衰减
scheduler = optim.lr_scheduler.CosineAnnealingLR(
    optimizer,
    T_max=epochs,
)
```

### 4.3 Label Smoothing

```python
# 防止模型过度自信
criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
```

### 4.4 梯度裁剪

```python
# 防止梯度爆炸
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
```

## 5. 关键难点攻克

### 5.1 Patch Embedding 的等价性

**难点**：理解 Conv2d 为何等价于手动分割 + 线性投影

**解决**：
- Conv2d 的 kernel_size=patch_size, stride=patch_size 意味着每次提取一个不重叠的 patch
- 每个卷积核的权重就是线性投影矩阵的一行
- 这种实现方式更高效，因为 PyTorch 对卷积有底层优化

### 5.2 注意力权重的形状变换

**难点**：Q, K, V 的分头操作涉及多维张量变换

**解决**：
```
(B, N, 3*D) -> reshape -> (B, N, 3, H, d_k)
           -> permute -> (3, B, H, N, d_k)
           -> unbind  -> Q, K, V each (B, H, N, d_k)
```

### 5.3 CLS Token 的广播机制

**难点**：CLS Token 需要扩展到 batch 维度

**解决**：
```python
# CLS token: (1, 1, D)
# expand 不复制数据，只是改变 view
cls_tokens = self.cls_token.expand(B, -1, -1)  # (B, 1, D)
```

## 6. 性能优化

### 6.1 内存优化

- 使用 `torch.no_grad()` 禁用梯度计算（推理时）
- 使用 `pin_memory=True` 加速数据传输
- 使用梯度累积减少内存占用

### 6.2 计算优化

- 使用 Conv2d 代替手动 patch 分割
- QKV 合并计算
- 使用 `torch.cuda.amp` 混合精度训练

## 7. 测试策略

### 7.1 单元测试

- 形状测试：验证每层的输入输出形状
- 梯度测试：验证梯度能正确传播
- 数值测试：验证注意力权重归一化

### 7.2 集成测试

- 端到端训练：验证模型能正常训练
- 参数量测试：验证参数量符合预期
- 批次独立性：验证批次中的样本独立
