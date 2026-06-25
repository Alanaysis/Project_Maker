# 02 - 设计文档：Vision Transformer

## 1. 架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Vision Transformer                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  输入图像 (B, C, H, W)                                  │
│       │                                                  │
│       ▼                                                  │
│  ┌─────────────────────────────┐                        │
│  │    Patch Embedding          │                        │
│  │  - Conv2d 投影              │                        │
│  │  - CLS Token 拼接           │                        │
│  │  - 位置编码相加              │                        │
│  │  输出: (B, N+1, D)          │                        │
│  └──────────────┬──────────────┘                        │
│                 │                                        │
│                 ▼                                        │
│  ┌─────────────────────────────┐                        │
│  │    Transformer Encoder      │ x L layers             │
│  │  ┌─────────────────────┐    │                        │
│  │  │ Layer Norm          │    │                        │
│  │  │ Multi-Head Attn     │    │                        │
│  │  │ + Residual          │    │                        │
│  │  ├─────────────────────┤    │                        │
│  │  │ Layer Norm          │    │                        │
│  │  │ Feed-Forward        │    │                        │
│  │  │ + Residual          │    │                        │
│  │  └─────────────────────┘    │                        │
│  │  输出: (B, N+1, D)          │                        │
│  └──────────────┬──────────────┘                        │
│                 │                                        │
│                 ▼                                        │
│  ┌─────────────────────────────┐                        │
│  │    取 [CLS] token           │                        │
│  │  (B, N+1, D) -> (B, D)      │                        │
│  └──────────────┬──────────────┘                        │
│                 │                                        │
│                 ▼                                        │
│  ┌─────────────────────────────┐                        │
│  │    Classification Head      │                        │
│  │  Linear -> Tanh -> Linear   │                        │
│  │  输出: (B, num_classes)     │                        │
│  └─────────────────────────────┘                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

| 模块 | 文件 | 职责 |
|------|------|------|
| `PatchEmbedding` | `patch_embedding.py` | 图像 -> patch 序列 |
| `MultiHeadSelfAttention` | `attention.py` | 多头自注意力机制 |
| `TransformerBlock` | `transformer.py` | 单个 Transformer 层 |
| `TransformerEncoder` | `transformer.py` | 多层 Transformer 编码器 |
| `VisionTransformer` | `vit.py` | 完整 ViT 模型 |
| `ViTTrainer` | `trainer.py` | 训练器 |
| `visualization` | `visualization.py` | 可视化工具 |

## 2. 核心数据流

### 2.1 Patch Embedding 数据流

```
输入: (B, 3, 224, 224)
    │
    ▼ Conv2d(kernel=16, stride=16, out=768)
(B, 768, 14, 14)
    │
    ▼ flatten(2)
(B, 768, 196)
    │
    ▼ transpose(1, 2)
(B, 196, 768)
    │
    ▼ cat([CLS], patches)
(B, 197, 768)
    │
    ▼ + position_embedding
输出: (B, 197, 768)
```

### 2.2 Multi-Head Self-Attention 数据流

```
输入: (B, N, D)
    │
    ▼ QKV projection
(B, N, 3*D)
    │
    ▼ reshape + permute
Q, K, V: (B, H, N, d_k)  其中 d_k = D/H
    │
    ▼ Q @ K^T / sqrt(d_k)
(B, H, N, N)  注意力分数
    │
    ▼ softmax
(B, H, N, N)  注意力权重
    │
    ▼ @ V
(B, H, N, d_k)
    │
    ▼ reshape + projection
输出: (B, N, D)
```

### 2.3 Transformer Block 数据流

```
输入: (B, N, D)
    │
    ├─► LN ─► MHSA ─► + residual
    │                      │
    ▼                      ▼
    ├─► LN ─► FFN  ─► + residual
    │
输出: (B, N, D)
```

## 3. 设计决策

### 3.1 Patch Embedding 实现方式

**选择**：使用 `nn.Conv2d` 实现

**替代方案**：
- 手动分割 + `nn.Linear`：先用 `unfold` 分割 patches，再线性投影
- `einops` 重排：使用 einops 库进行张量重排

**理由**：
- Conv2d 的 kernel_size=stride=patch_size 等价于分割 + 投影
- PyTorch 对 Conv2d 有优化，效率更高
- 代码更简洁

### 3.2 Pre-LN vs Post-LN

**选择**：Pre-LN（Layer Normalization 放在注意力/FFN 之前）

**替代方案**：Post-LN（Layer Normalization 放在注意力/FFN 之后）

**理由**：
- Pre-LN 训练更稳定，不需要 warmup
- 梯度流更顺畅
- 是大多数现代 ViT 实现的默认选择

### 3.3 位置编码

**选择**：可学习的绝对位置编码

**替代方案**：
- 正弦位置编码
- 相对位置编码
- 旋转位置编码（RoPE）

**理由**：
- 实现简单
- 性能与复杂方法相当
- 原论文使用此方案

### 3.4 CLS Token vs 全局平均池化

**选择**：CLS Token

**替代方案**：对所有 patch 输出做全局平均池化

**理由**：
- CLS Token 是原论文的标准做法
- 通过自注意力聚合全局信息
- 便于注意力可视化

### 3.5 MLP Head 设计

**选择**：Linear -> Tanh -> Linear（原论文设计）

**替代方案**：单层 Linear

**理由**：
- 原论文使用此设计
- 提供非线性变换能力
- 但在实际中，简单线性头通常效果也不错

## 4. 关键参数

### 4.1 模型配置

| 配置 | Embed Dim | Depth | Heads | MLP Ratio | Params |
|------|-----------|-------|-------|-----------|--------|
| ViT-Ti | 192 | 4 | 3 | 4.0 | ~5.7M |
| ViT-S | 384 | 8 | 6 | 4.0 | ~22M |
| ViT-B | 768 | 12 | 12 | 4.0 | ~86M |
| ViT-L | 1024 | 24 | 16 | 4.0 | ~307M |
| ViT-H | 1280 | 32 | 16 | 4.0 | ~632M |

### 4.2 训练超参数

| 参数 | MNIST | CIFAR-10 | ImageNet |
|------|-------|----------|----------|
| Learning Rate | 3e-4 | 3e-4 | 1e-3 |
| Weight Decay | 0.01 | 0.01 | 0.01 |
| Batch Size | 64 | 128 | 512 |
| Epochs | 10 | 100 | 300 |
| Optimizer | AdamW | AdamW | AdamW |
| LR Schedule | Cosine | Cosine | Cosine |
| Label Smoothing | 0.1 | 0.1 | 0.1 |

## 5. 内存与计算分析

### 5.1 参数量计算

```
Patch Embedding:
  - Projection: in_channels * embed_dim * patch_size^2
  - CLS Token: embed_dim
  - Position Embedding: (num_patches + 1) * embed_dim

Transformer Block (per layer):
  - QKV: 3 * embed_dim^2
  - Output Proj: embed_dim^2
  - FFN: 2 * embed_dim * (embed_dim * mlp_ratio)
  - LayerNorm: 2 * embed_dim * 2

Classification Head:
  - embed_dim * num_classes
```

### 5.2 计算复杂度

```
Self-Attention: O(N^2 * D)
FFN: O(N * D^2)
Total per layer: O(N^2 * D + N * D^2)

其中 N = num_patches + 1, D = embed_dim
```

### 5.3 内存估算（ViT-B/16, 224x224）

```
参数: 86M * 4 bytes = ~344 MB
激活值: ~1-2 GB (取决于 batch size)
梯度: ~344 MB
优化器状态: ~688 MB (Adam)
总计: ~2-3 GB (batch_size=32)
```
