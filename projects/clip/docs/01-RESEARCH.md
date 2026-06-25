# 01 - 调研报告

## CLIP 概述

CLIP (Contrastive Language-Image Pre-training) 是 OpenAI 于 2021 年提出的多模态预训练模型。它通过从互联网收集的 4 亿个图文对进行训练，学习将图像和文本映射到同一嵌入空间。

## 核心思想

### 对比学习

对比学习是一种自监督学习方法，核心思想是：
- **正样本对**：匹配的样本对应该在嵌入空间中靠近
- **负样本对**：不匹配的样本对应该在嵌入空间中远离

在 CLIP 中：
- 正样本对：匹配的图像-文本对
- 负样本对：同一批次中不匹配的图像-文本对

### 多模态对齐

CLIP 的目标是学习一个共享的嵌入空间，使得：
- 相似语义的图像和文本在嵌入空间中接近
- 不同语义的图像和文本在嵌入空间中远离

## 技术架构

### 双编码器

CLIP 使用两个独立的编码器：

1. **图像编码器**：基于 ResNet 或 ViT
   - 输入：图像 (H, W, C)
   - 输出：图像嵌向量

2. **文本编码器**：基于 Transformer
   - 输入：文本 token 序列
   - 输出：文本嵌入向量

### 对比损失

CLIP 使用对称交叉熵损失：

```
L = (L_image_to_text + L_text_to_image) / 2
```

其中：
- `L_image_to_text`：图像查询文本的交叉熵损失
- `L_text_to_image`：文本查询图像的交叉熵损失

### 温度参数

CLIP 引入可学习的温度参数 τ，用于控制 softmax 的锐度：

```
similarity = (image_embed · text_embed) / τ
```

## 应用场景

### 零样本分类

CLIP 可以用于零样本分类：
1. 将类别名称转换为文本描述
2. 编码图像和文本描述
3. 计算相似度，选择最匹配的类别

### 图像检索

给定文本查询，检索最相关的图像：
1. 编码查询文本
2. 编码数据库中的图像
3. 按相似度排序返回结果

### 图像生成

CLIP 可以指导图像生成：
1. 使用 CLIP 计算文本与生成图像的相似度
2. 优化生成图像以最大化相似度

## 相关工作

### SimCLR

SimCLR 是一种视觉对比学习方法：
- 使用数据增强创建正样本对
- 使用 NT-Xent 损失进行训练

### MoCo

MoCo 使用动量编码器和队列来维护大量负样本。

### ALIGN

ALIGN 是 Google 提出的类似方法，使用更大的数据集（18 亿图文对）。

## 关键论文

1. **CLIP**: Learning Transferable Visual Models From Natural Language Supervision (Radford et al., 2021)
2. **SimCLR**: A Simple Framework for Contrastive Learning of Visual Representations (Chen et al., 2020)
3. **MoCo**: Momentum Contrast for Unsupervised Visual Representation Learning (He et al., 2020)

## 总结

CLIP 的核心创新在于：
1. 使用自然语言监督进行视觉表示学习
2. 大规模预训练实现强大的零样本能力
3. 对称对比损失实现双向对齐
