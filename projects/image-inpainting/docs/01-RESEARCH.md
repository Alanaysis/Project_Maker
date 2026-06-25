# 市场调研报告 - 图像修复

## 1. 问题定义

### 要解决的问题

图像修复（Image Inpainting）是指从损坏或有缺失区域的图像中恢复出完整图像的技术。核心挑战是如何生成语义合理、视觉连贯的缺失内容。

### 为什么这个问题重要

- **文化遗产保护**：修复老旧照片、历史文献中的损坏部分
- **照片编辑**：移除图像中不需要的物体（如电线、水印）
- **医学影像**：补全缺失的医学扫描数据
- **视频后期**：视频修复和特效合成
- **自动驾驶**：传感器数据缺失时的场景重建

## 2. 同类型项目概览

| 项目 | GitHub Stars | 核心特点 | 技术栈 | 最后更新 | 链接 |
|------|--------------|----------|--------|----------|------|
| DeepFill v2 | 3.5k | 门控卷积，自由形状修复 | TensorFlow | 2019 | [GitHub](https://github.com/JiahuiYu/generative_inpainting) |
| LaMa | 4k+ | 傅里叶卷积，大掩码修复 | PyTorch | 2021 | [GitHub](https://github.com/advimman/lama) |
| MAT | 1k+ | Transformer 架构 | PyTorch | 2021 | [GitHub](https://github.com/fenglinglwb/MAT) |
| Palette | 2k+ | 条件扩散模型 | PyTorch | 2022 | [GitHub](https://github.com/JingyunLiang/Palette) |
| Stable Diffusion Inpainting | 10k+ | 文本引导的扩散修复 | PyTorch | 2023 | [HuggingFace](https://huggingface.co/runwayml/stable-diffusion-inpainting) |

## 3. 技术变体分析

### 核心循环的变体

**基础版本：上下文编码器（Context Encoder）**
```
损坏图像 → 掩码 → 编码器 → 瓶颈层 → 解码器 → 修复图像
```
- 发力方向：端到端学习图像补全
- 为什么这么做：编码器-解码器结构可以学习图像的语义表示
- 适用场景：矩形掩码、中心区域修复

**变体1：门控卷积（Gated Convolution）**
```
损坏图像 → 掩码 → 门控卷积编码器 → 注意力模块 → 门控卷积解码器 → 修复图像
```
- 发力方向：解决普通卷积对无效像素的处理问题
- 为什么这么做：门控机制可以自动学习哪些像素应该被信任
- 适用场景：自由形状掩码、不规则损坏

**变体2：注意力机制增强（Attention-based）**
```
损坏图像 → 编码器 → 自注意力 + 上下文注意力 → 解码器 → 修复图像
```
- 发力方向：利用远距离依赖关系生成连贯内容
- 为什么这么做：卷积感受野有限，注意力可以捕获全局信息
- 适用场景：大面积缺失、需要语义一致性的场景

**变体3：扩散模型（Diffusion-based）**
```
损坏图像 + 噪声 → 掩码条件 → 迭代去噪 → 修复图像
```
- 发力方向：生成多样化的高质量修复结果
- 为什么这么做：扩散模型在图像生成质量上表现优异
- 适用场景：需要高质量、多样化的修复结果

## 4. 技术演进路径

```
传统方法     深度学习     GAN-based      Transformer    扩散模型
(PDE/统计)  (CNN)      (上下文编码器)   (MAT/SwinIR)   (Palette/SD)
    ↓          ↓            ↓               ↓              ↓
 纹理填充   端到端学习   对抗训练增强    全局注意力    迭代去噪生成
 手工特征   特征学习    视觉质量提升    长距离依赖    多样化输出
```

## 5. 各项目的发力方向

| 项目 | 主要发力方向 | 为什么选择这个方向 |
|------|--------------|-------------------|
| Context Encoder | 端到端学习 | 首次将深度学习引入图像修复 |
| DeepFill v2 | 门控卷积 | 解决不规则掩码的处理问题 |
| LaMa | 傅里叶特征 | 大掩码下保持高频细节 |
| MAT | Transformer | 全局上下文建模 |
| Palette | 条件扩散 | 高质量多模态生成 |

## 6. 我们的选择

基于调研，我们选择 **上下文编码器 + 对抗训练** 作为本项目的实现方案。

### 选择理由

1. **学习价值高**：Context Encoder 是图像修复领域的开山之作，理解它有助于掌握后续所有方法
2. **架构清晰**：U-Net 编码器-解码器 + 跳跃连接 + PatchGAN，每个组件都有明确的作用
3. **难度适中**：比扩散模型简单，比传统方法有深度，适合学习
4. **可扩展性强**：在此基础上可以轻松添加门控卷积、注意力等高级特性

### 学习价值

- 理解编码器-解码器架构在图像修复中的应用
- 掌握 GAN 训练的技巧（判别器-生成器交替训练）
- 学习重建损失与对抗损失的平衡
- 了解掩码设计对修复质量的影响

## 7. 延伸阅读

- [Context Encoders: Feature Learning by Inpainting (CVPR 2016)](https://arxiv.org/abs/1604.07379)
- [Generative Image Inpainting with Contextual Attention (CVPR 2018)](https://arxiv.org/abs/1801.07892)
- [Image Inpainting for Irregular Holes Using Partial Convolutions (ECCV 2018)](https://arxiv.org/abs/1804.07777)
- [LaMa: Resolution-robust Large Mask Inpainting (CVPR 2021)](https://arxiv.org/abs/2109.07161)
- [图像修复技术综述](https://arxiv.org/abs/2007.01310)
