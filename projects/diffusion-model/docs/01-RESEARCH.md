# 技术调研报告

## 1. 扩散模型概述

### 1.1 背景

扩散模型是近年来图像生成领域最重要的突破之一。与 GAN（生成对抗网络）和 VAE（变分自编码器）相比，扩散模型具有以下优势：

- **训练稳定性**：不存在模式崩溃（mode collapse）问题
- **生成质量**：能够生成高质量、高分辨率的图像
- **理论基础**：有坚实的概率论基础
- **灵活性**：易于扩展到各种任务

### 1.2 发展历程

| 年份 | 模型 | 主要贡献 |
|------|------|----------|
| 2015 | Diffusion Processes | 首次提出扩散过程的概念 |
| 2020 | DDPM | 简化训练过程，证明扩散模型的有效性 |
| 2020 | DDIM | 提出确定性采样，加速生成过程 |
| 2021 | Improved DDPM | 改进噪声调度和方差学习 |
| 2021 | Classifier Guidance | 引入分类器引导，提高条件生成质量 |
| 2022 | Classifier-Free Guidance | 无需分类器的引导方法 |
| 2022 | Stable Diffusion | 潜空间扩散，大幅降低计算成本 |

## 2. 核心技术调研

### 2.1 DDPM（Denoising Diffusion Probabilistic Models）

**论文**：https://arxiv.org/abs/2006.11239

**核心思想**：
- 定义前向扩散过程，逐步向数据添加噪声
- 学习反向去噪过程，从噪声中恢复数据
- 使用神经网络预测噪声

**关键公式**：

前向过程：
```
q(x_t | x_{t-1}) = N(x_t; √(1-β_t) * x_{t-1}, β_t * I)
```

反向过程：
```
p_θ(x_{t-1} | x_t) = N(x_{t-1}; μ_θ(x_t, t), Σ_θ(x_t, t))
```

训练目标：
```
L_simple = E_{t,x_0,ε} [||ε - ε_θ(√(ᾱ_t) * x_0 + √(1-ᾱ_t) * ε, t)||²]
```

**优点**：
- 训练简单稳定
- 生成质量高
- 理论基础完善

**缺点**：
- 采样速度慢（需要数百步）
- 计算成本高

### 2.2 DDIM（Denoising Diffusion Implicit Models）

**论文**：https://arxiv.org/abs/2010.02502

**核心改进**：
- 提出非马尔可夫前向过程
- 允许确定性采样
- 可以使用更少的采样步数

**关键公式**：
```
x_{t-1} = √(ᾱ_{t-1}) * pred_x0 + √(1-ᾱ_{t-1}-σ_t²) * pred_dir + σ_t * ε
```

**优点**：
- 采样速度快 10-50 倍
- 可以进行语义插值
- 保持生成质量

### 2.3 改进的 DDPM

**论文**：https://arxiv.org/abs/2102.09672

**主要改进**：
- 余弦噪声调度
- 学习方差
- 改进的采样策略

## 3. 网络架构调研

### 3.1 UNet

**为什么选择 UNet**：
- 跳跃连接保留细节信息
- 多尺度特征提取
- 适合像素级预测任务

**关键组件**：
- 编码器：下采样提取特征
- 解码器：上采样恢复细节
- 跳跃连接：连接编码器和解码器
- 时间嵌入：注入时间信息

### 3.2 时间嵌入

**正弦位置编码**：
```python
def sinusoidal_embedding(t, dim):
    half_dim = dim // 2
    emb = math.log(10000) / (half_dim - 1)
    emb = torch.exp(torch.arange(half_dim) * -emb)
    emb = t[:, None] * emb[None, :]
    emb = torch.cat([emb.sin(), emb.cos()], dim=-1)
    return emb
```

**作用**：
- 告诉模型当前的时间步
- 类似于 Transformer 中的位置编码
- 帮助模型区分不同噪声水平

### 3.3 注意力机制

**自注意力**：
- 捕获长距离依赖
- 提高生成质量
- 通常在低分辨率特征图上使用

**实现**：
```python
class SelfAttention(nn.Module):
    def __init__(self, channels):
        self.norm = nn.GroupNorm(channels)
        self.attention = nn.MultiheadAttention(channels, num_heads=4)

    def forward(self, x):
        B, C, H, W = x.shape
        h = self.norm(x)
        h = h.view(B, C, H*W).transpose(1, 2)
        h, _ = self.attention(h, h, h)
        h = h.transpose(1, 2).view(B, C, H, W)
        return h + x
```

## 4. 训练策略调研

### 4.1 数据预处理

**归一化**：
- 将图像归一化到 [-1, 1] 范围
- 与噪声分布匹配
- 便于训练

**数据增强**：
- 随机水平翻转
- 不建议使用裁剪（会改变数字结构）

### 4.2 优化器选择

**常用选择**：
- Adam 优化器
- 学习率：2e-4 到 1e-4
- 权重衰减：0 或很小

**学习率调度**：
- 余弦退火
- 或固定学习率

### 4.3 训练技巧

**梯度裁剪**：
```python
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
```

**EMA（指数移动平均）**：
- 使用 EMA 模型进行采样
- 提高生成质量
- 通常衰减率 0.9999

**混合精度训练**：
- 使用 float16 加速训练
- 节省显存
- PyTorch AMP 支持

## 5. 评估指标调研

### 5.1 FID（Fréchet Inception Distance）

**计算方法**：
1. 提取真实图像和生成图像的 Inception 特征
2. 计算两个分布的 Fréchet 距离

**公式**：
```
FID = ||μ_r - μ_g||² + Tr(Σ_r + Σ_g - 2√(Σ_r * Σ_g))
```

**解释**：
- 越低越好
- 衡量生成图像的质量和多样性
- 需要大量样本（通常 50K）

### 5.2 IS（Inception Score）

**计算方法**：
1. 计算生成图像的类别概率
2. 计算 KL 散度

**公式**：
```
IS = exp(E[KL(p(y|x) || p(y))])
```

**解释**：
- 越高越好
- 衡量生成图像的质量和多样性
- 与人类判断相关性较好

### 5.3 其他指标

- **LPIPS**：感知相似度
- **SSIM**：结构相似度
- **PSNR**：峰值信噪比

## 6. 现有实现调研

### 6.1 主流开源实现

| 仓库 | 特点 | 链接 |
|------|------|------|
| lucidrains/denoising-diffusion-pytorch | 代码清晰，易于理解 | GitHub |
| hojonathanho/diffusion | 原始实现 | GitHub |
| microsoft/guided-diffusion | 工业级实现 | GitHub |
| CompVis/stable-diffusion | Stable Diffusion 实现 | GitHub |

### 6.2 本项目的定位

**目标**：
- 教育和学习目的
- 清晰易懂的代码结构
- 完整的文档和注释
- 便于实验和修改

**设计原则**：
- 模块化设计
- 详细的文档
- 完整的测试
- 易于扩展

## 7. 技术选型

### 7.1 框架选择

**PyTorch**：
- 动态计算图，易于调试
- 丰富的社区资源
- 与研究社区紧密集成

### 7.2 模型架构

**UNet**：
- 适合图像生成任务
- 跳跃连接保留细节
- 易于理解和实现

### 7.3 噪声调度

**线性调度**：
- 简单直观
- 作为基线方法
- 便于理解原理

**余弦调度**：
- 效果更好
- 避免后期噪声过大
- 改进版本使用

## 8. 参考资源

### 8.1 核心论文

1. Ho et al., "Denoising Diffusion Probabilistic Models", NeurIPS 2020
2. Song et al., "Denoising Diffusion Implicit Models", ICLR 2021
3. Nichol et al., "Improved Denoising Diffusion Probabilistic Models", 2021

### 8.2 教程和博客

1. Lilian Weng, "What are Diffusion Models?", 2021
2. Hugging Face, "The Annotated Diffusion Model", 2022
3. Stanford CS236, "Deep Generative Models", 2023

### 8.3 开源代码

1. lucrains/denoising-diffusion-pytorch
2. hojonathanho/diffusion
3. openai/guided-diffusion

## 9. 总结

### 9.1 技术总结

扩散模型是当前最先进的图像生成技术之一，具有：
- 稳定的训练过程
- 高质量的生成结果
- 灵活的条件生成能力

### 9.2 学习路径

1. **理解数学基础**：概率论、随机过程
2. **学习核心算法**：DDPM、DDIM
3. **实现基础模型**：UNet、噪声调度
4. **实验和调优**：不同参数、不同数据集
5. **探索高级技术**：条件生成、高分辨率生成

### 9.3 未来方向

- 加速采样（一致性模型等）
- 更好的条件生成
- 视频生成
- 3D 生成
- 多模态生成
