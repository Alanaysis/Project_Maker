# 01 - 研究文档：Vision Transformer

## 1. 问题定义

### 核心问题

如何将 Transformer 架构成功应用于计算机视觉任务，特别是图像分类？

### 背景

- **CNN 时代**：自 2012 年 AlexNet 以来，卷积神经网络（CNN）一直是计算机视觉的主流架构
- **Transformer 的崛起**：2017 年 Transformer 在 NLP 领域取得巨大成功（BERT、GPT）
- **核心挑战**：Transformer 的自注意力机制计算复杂度是序列长度的平方，直接应用于图像会导致极高的计算成本

### 关键研究问题

1. 如何将 2D 图像转换为 Transformer 可以处理的 1D 序列？
2. Transformer 在视觉任务中能否达到或超越 CNN 的性能？
3. Transformer 在视觉任务中的数据效率如何？

## 2. 技术演进

### 2.1 CNN 的发展

| 年份 | 模型 | 关键创新 |
|------|------|----------|
| 1998 | LeNet-5 | 首个成功的 CNN |
| 2012 | AlexNet | ReLU、Dropout、GPU 训练 |
| 2014 | VGGNet | 小卷积核堆叠 |
| 2014 | GoogLeNet | Inception 模块 |
| 2015 | ResNet | 残差连接 |
| 2017 | SENet | 通道注意力 |

### 2.2 Transformer 在视觉中的探索

| 年份 | 模型 | 关键创新 |
|------|------|----------|
| 2020 | ViT | 纯 Transformer 图像分类 |
| 2020 | DETR | Transformer 目标检测 |
| 2021 | DeiT | 数据高效 ViT 训练 |
| 2021 | Swin Transformer | 层级化窗口注意力 |
| 2021 | PVT | 金字塔 Vision Transformer |
| 2022 | BEiT | 自监督视觉 Transformer |

### 2.3 ViT 论文时间线

1. **2020.10**：Dosovitskiy et al. 发布 ViT 原始论文
2. **2021.01**：Touvron et al. 发布 DeiT，改进训练策略
3. **2021.03**：Liu et al. 发布 Swin Transformer，引入层级结构
4. **2021-2022**：大量 ViT 变体和改进工作涌现

## 3. 竞品分析

### 3.1 主要方法对比

| 方法 | 核心思想 | 优点 | 缺点 |
|------|----------|------|------|
| **CNN** | 局部感受野 + 权重共享 | 参数高效、归纳偏置强 | 全局建模能力弱 |
| **ViT** | 全局自注意力 | 全局建模、可扩展性强 | 需要大量数据 |
| **DeiT** | 改进训练策略 | 数据效率更高 | 仍需较多数据 |
| **Swin** | 层级化窗口注意力 | 多尺度特征、高效 | 架构较复杂 |

### 3.2 ViT vs CNN

**ViT 的优势**：
- 全局感受野：每个 patch 可以关注所有其他 patches
- 可扩展性：模型越大、数据越多，性能越好
- 统一架构：同一个架构可用于多种视觉任务

**ViT 的劣势**：
- 缺乏归纳偏置：没有 CNN 的平移不变性和局部性
- 数据效率低：需要大规模数据集（如 JFT-300M）才能超越 CNN
- 计算成本高：自注意力的复杂度是 O(N^2)

## 4. 核心技术原理

### 4.1 Patch Embedding

将图像分割为固定大小的 patches，每个 patch 通过线性投影映射为一个向量。

```
图像 (H x W x C) -> N 个 patches (P x P x C) -> N 个嵌入向量 (D)
其中 N = (H/P) * (W/P)
```

**关键洞察**：这等价于使用 stride=P 的卷积操作。

### 4.2 位置编码

由于 Transformer 没有位置感知能力，需要显式添加位置信息。

- **可学习位置编码**：每个位置一个可学习的向量
- **正弦位置编码**：使用正弦/余弦函数生成（原始 Transformer）
- **相对位置编码**：编码相对距离而非绝对位置

### 4.3 CLS Token

在序列开头添加一个特殊的 [CLS] token，用其最终表示进行分类。

- 类似 BERT 的 [CLS] token
- 通过自注意力聚合全局信息
- 最终通过分类头映射到类别空间

### 4.4 Transformer Encoder

每个层包含：
1. **Multi-Head Self-Attention**：捕获全局依赖
2. **Feed-Forward Network**：非线性变换
3. **Layer Normalization**：稳定训练
4. **Residual Connection**：缓解梯度消失

## 5. 数据集与基准

### 5.1 常用数据集

| 数据集 | 类别数 | 训练集 | 测试集 | 图像尺寸 |
|--------|--------|--------|--------|----------|
| MNIST | 10 | 60K | 10K | 28x28 |
| CIFAR-10 | 10 | 50K | 10K | 32x32 |
| CIFAR-100 | 100 | 50K | 10K | 32x32 |
| ImageNet-1K | 1000 | 1.2M | 50K | 224x224 |
| ImageNet-21K | 21841 | 14M | - | 224x224 |

### 5.2 ViT 性能基准

在 ImageNet-1K 上的 Top-1 准确率：

| 模型 | 参数量 | ImageNet Acc | 预训练数据 |
|------|--------|-------------|-----------|
| ViT-B/16 | 86M | 77.9% | ImageNet-1K |
| ViT-B/16 | 86M | 84.2% | ImageNet-21K |
| ViT-L/16 | 307M | 85.2% | ImageNet-21K |
| ViT-H/14 | 632M | 88.6% | JFT-300M |

## 6. 技术选型

### 6.1 为什么选择实现 ViT

1. **基础架构**：ViT 是所有视觉 Transformer 的基础
2. **学习价值**：理解 Patch Embedding、位置编码、CLS Token 等核心概念
3. **可扩展性**：可以在此基础上扩展到 DeiT、Swin 等变体
4. **社区资源**：大量教程和预训练权重可用

### 6.2 实现范围

- **核心实现**：Patch Embedding、Multi-Head Self-Attention、Transformer Encoder、ViT 模型
- **训练支持**：MNIST / CIFAR-10 数据集训练
- **可视化**：注意力权重可视化
- **不包含**：预训练权重加载、大规模数据集训练

## 7. 参考资料

1. [An Image is Worth 16x16 Words (Dosovitskiy et al., 2020)](https://arxiv.org/abs/2010.11929)
2. [Training Data-Efficient Image Transformers (Touvron et al., 2021)](https://arxiv.org/abs/2012.12877)
3. [Swin Transformer (Liu et al., 2021)](https://arxiv.org/abs/2103.14030)
4. [Attention Is All You Need (Vaswani et al., 2017)](https://arxiv.org/abs/1706.03762)
5. [PyTorch ViT Tutorial](https://pytorch.org/tutorials/intermediate/vt_tutorial.html)
