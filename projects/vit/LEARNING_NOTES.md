# 学习笔记

## 基本信息

- **项目名称**：Vision Transformer (ViT)
- **开始日期**：2026-06-22
- **完成日期**：2026-06-22
- **学习时长**：8 小时

## 1. 核心概念

### 概念1：Patch Embedding

**定义**：将 2D 图像分割为固定大小的 patches，每个 patch 通过线性投影映射为一个 D 维向量，形成一个序列供 Transformer 处理。

**关键点**：
- 图像 (H, W, C) 被分割为 N = (H/P) * (W/P) 个 patches，每个 patch 大小为 (P, P, C)
- 使用 Conv2d(kernel_size=P, stride=P) 等价于手动分割 + 线性投影
- 在序列开头添加可学习的 [CLS] token 用于分类
- 添加可学习的位置编码，让模型感知 patch 的空间位置

**个人理解**：
Patch Embedding 是 ViT 的核心创新之一。它将图像从 2D 网格结构转换为 1D 序列结构，使得 Transformer 可以处理图像。关键洞察是：一个 16x16 的 patch 可以看作一个"视觉单词"，就像 NLP 中的 token 一样。使用 Conv2d 实现这个操作非常巧妙，因为它同时完成了分割和线性投影两个步骤。

### 概念2：Multi-Head Self-Attention

**定义**：自注意力机制让序列中的每个位置都能关注所有其他位置，多头机制让模型在不同子空间中并行计算多种注意力模式。

**关键点**：
- Q (查询)、K (键)、V (值) 通过线性投影从输入得到
- 注意力分数 = softmax(Q @ K^T / sqrt(d_k))
- 多头将嵌入维度分成 H 个子空间，每个头独立计算注意力
- 缩放因子 1/sqrt(d_k) 防止点积过大导致 softmax 饱和

**个人理解**：
自注意力是 Transformer 的核心。在 ViT 中，每个 patch 可以通过注意力机制"看到"图像中的所有其他 patches，从而捕获全局依赖关系。这比 CNN 的局部感受野更强大。多头机制类似于 CNN 中的多个卷积核，让模型能同时关注不同类型的特征（如纹理、颜色、形状）。

### 概念3：Transformer Encoder

**定义**：由多个 Transformer Block 堆叠而成，每个 Block 包含自注意力层和前馈网络，使用残差连接和层归一化。

**关键点**：
- Pre-LN 架构：Layer Normalization 放在注意力/FFN 之前（训练更稳定）
- 残差连接：x = x + SubLayer(x)，缓解深层网络的梯度消失
- FFN：两层全连接网络，隐藏层维度通常是嵌入维度的 4 倍
- 使用 GELU 激活函数（比 ReLU 更平滑）

**个人理解**：
Transformer Encoder 是特征提取的核心。每一层都通过自注意力聚合全局信息，然后通过 FFN 进行非线性变换。残差连接让信息能直接流过深层网络，这是 ViT 能堆叠到 12 层甚至更多层的关键。Pre-LN 架构比 Post-LN 训练更稳定，是现代 Transformer 的标准做法。

## 2. 重点难点

### 难点1：Patch Embedding 的 Conv2d 实现

**问题**：为什么不直接手动分割 patches 再做矩阵乘法？

**解决过程**：
1. 尝试1：使用 `unfold` 分割 patches，再用 `nn.Linear` 投影
2. 尝试2：使用 einops 库重排张量
3. 最终方案：使用 `nn.Conv2d(kernel_size=P, stride=P)`

**关键收获**：
- Conv2d 的 stride=kernel_size 等价于不重叠地提取 patches
- 每个卷积核的权重就是线性投影矩阵的一行
- PyTorch 对 Conv2d 有底层优化，比手动实现更高效
- 这个技巧在很多 ViT 实现中被使用

### 难点2：注意力权重的多维张量变换

**问题**：Q, K, V 的分头操作涉及复杂的张量形状变换。

**解决过程**：
1. 尝试1：分别计算 Q, K, V 再 reshape
2. 最终方案：合并计算后通过 reshape + permute + unbind 拆分

```python
qkv = self.qkv(x)  # (B, N, 3*D)
qkv = qkv.reshape(B, N, 3, H, d_k)  # (B, N, 3, H, d_k)
qkv = qkv.permute(2, 0, 3, 1, 4)    # (3, B, H, N, d_k)
q, k, v = qkv.unbind(0)              # each (B, H, N, d_k)
```

**关键收获**：
- `reshape` 改变张量形状但不改变数据顺序
- `permute` 重新排列维度
- `unbind` 沿指定维度拆分张量
- 合并计算 QKV 比分别计算更高效

### 难点3：CLS Token 的作用机制

**问题**：为什么需要 CLS Token？为什么不用全局平均池化？

**解决过程**：
1. 尝试1：使用全局平均池化替代 CLS Token
2. 最终方案：使用 CLS Token（原论文方案）

**关键收获**：
- CLS Token 通过自注意力聚合所有 patches 的信息
- 它是一个可学习的"查询"，学习应该关注哪些 patches
- 相比全局平均池化，CLS Token 更灵活，能学到非均匀的注意力分布
- 但实验表明，全局平均池化在某些情况下效果也不错

## 3. 设计决策思考

### 决策1：Pre-LN vs Post-LN

**背景**：Transformer 中 Layer Normalization 的位置会影响训练稳定性。

**我的思考**：
- Post-LN（原论文）：LN 放在子层之后，需要 warmup
- Pre-LN（现代做法）：LN 放在子层之前，训练更稳定
- Pre-LN 让梯度能直接通过残差连接流回，不需要 warmup

**最终方案**：选择 Pre-LN

**反思**：
Pre-LN 是正确的选择。它让训练更简单，不需要精心调整 warmup 步数。虽然有研究表明 Post-LN 的最终性能可能略好，但 Pre-LN 的易用性优势更明显。

### 决策2：使用 Conv2d 实现 Patch Embedding

**背景**：Patch Embedding 可以用多种方式实现。

**我的思考**：
- 方案A：手动分割 + nn.Linear
- 方案B：使用 einops 库
- 方案C：使用 nn.Conv2d

**最终方案**：选择 Conv2d

**反思**：
Conv2d 方案最简洁，且有底层优化。虽然手动实现更直观，但 Conv2d 是工业界的标准做法。理解等价性是关键：stride=P 的卷积等价于不重叠分割。

## 4. 代码片段收藏

### 片段1：Patch Embedding 的 Conv2d 实现

```python
# 使用 Conv2d 实现 patch 分割 + 线性投影
# kernel_size = stride = patch_size -> 不重叠地提取 patches
self.projection = nn.Conv2d(
    in_channels=in_channels,
    out_channels=embed_dim,
    kernel_size=patch_size,
    stride=patch_size,
)
```

**为什么收藏**：这是 ViT 的核心技巧，将复杂的分割+投影操作简化为一个卷积层。

**使用场景**：任何需要将图像分割为 patches 的场景。

### 片段2：高效 QKV 计算

```python
# 一次性计算 Q, K, V，比三个独立线性层更高效
self.qkv = nn.Linear(embed_dim, embed_dim * 3)

# 拆分并分头
qkv = self.qkv(x).reshape(B, N, 3, H, d_k)
qkv = qkv.permute(2, 0, 3, 1, 4)
q, k, v = qkv.unbind(0)
```

**为什么收藏**：展示了如何高效地计算多头注意力的 Q, K, V。

**使用场景**：实现任何 Transformer 注意力层。

### 片段3：Pre-LN Transformer Block

```python
# Pre-LN 架构：Layer Norm 在子层之前
residual = x
x = residual + self.attn(self.norm1(x))
residual = x
x = residual + self.ffn(self.norm2(x))
```

**为什么收藏**：简洁地展示了 Pre-LN Transformer Block 的结构。

**使用场景**：实现任何 Transformer 编码器。

## 5. 延伸学习

### 想深入了解的主题

1. **DeiT（数据高效 ViT）**：如何用更少的数据训练 ViT？
2. **Swin Transformer**：如何引入层级结构和窗口注意力？
3. **ViT 的自监督预训练**：如 MAE（Masked Autoencoder）

### 推荐资源

- [An Image is Worth 16x16 Words](https://arxiv.org/abs/2010.11929)：ViT 原始论文
- [Training Data-Efficient Image Transformers](https://arxiv.org/abs/2012.12877)：DeiT 论文
- [Swin Transformer](https://arxiv.org/abs/2103.14030)：Swin Transformer 论文
- [Masked Autoencoders](https://arxiv.org/abs/2111.06377)：MAE 自监督学习

## 6. 自我评估

### 掌握程度

| 知识点 | 掌握程度 | 证据 |
|--------|----------|------|
| Patch Embedding | ⭐⭐⭐⭐⭐ | 能独立实现，理解 Conv2d 等价性 |
| Multi-Head Self-Attention | ⭐⭐⭐⭐⭐ | 能独立实现，理解 QKV 计算 |
| Transformer Encoder | ⭐⭐⭐⭐⭐ | 能独立实现，理解 Pre-LN 架构 |
| ViT 模型 | ⭐⭐⭐⭐⭐ | 能独立实现完整模型 |
| 训练技巧 | ⭐⭐⭐⭐ | 理解 AdamW、Cosine Annealing 等 |
| 注意力可视化 | ⭐⭐⭐ | 能实现基本可视化 |

### 改进计划

1. 深入研究 DeiT 的训练策略（蒸馏、数据增强）
2. 实现 Swin Transformer 的窗口注意力
3. 探索 ViT 的自监督预训练方法

## 7. 练习任务

- [ ] 实现 DeiT 的蒸馏 token 机制
- [ ] 实现 Swin Transformer 的窗口注意力
- [ ] 在 CIFAR-10 上训练 ViT-Small 达到 90%+ 准确率
- [ ] 实现 MAE（Masked Autoencoder）自监督预训练
- [ ] 对比 ViT 和 ResNet 在小数据集上的表现

## 8. 学习心得

### 最大的收获

理解了 Transformer 如何应用于视觉任务。核心洞察是：图像可以被分解为 patch 序列，每个 patch 是一个"视觉 token"。自注意力机制让每个 patch 能关注所有其他 patches，从而捕获全局依赖关系。这比 CNN 的局部感受野更强大，但代价是需要更多数据。

### 最大的挑战

理解 Patch Embedding 的 Conv2d 等价性。最初很难理解为什么 stride=P 的卷积等价于手动分割 patches。后来通过画图和计算输出形状，终于理解了：stride=P 意味着每次滑动 P 个像素，正好不重叠地提取 patches。

### 给其他学习者的建议

1. 先理解 Transformer 的基本原理（NLP 中的 Transformer），再学习 ViT
2. 画图！画出 Patch Embedding 的数据流，理解每一步的形状变化
3. 从小模型开始（ViT-Tiny），验证代码正确后再扩大规模
4. 注意力可视化是理解 ViT 的好工具，一定要尝试
