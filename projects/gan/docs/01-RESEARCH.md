# 01-RESEARCH.md - GAN 调研文档

## 1. 技术背景

### 1.1 生成模型概述

生成模型是机器学习中的重要分支，目标是学习数据的分布，从而能够生成新的样本。

**生成模型的分类**：
- **显式密度估计**：显式建模数据分布 p(x)
  - VAE (变分自编码器)
  - PixelCNN
  - Flow 模型

- **隐式密度估计**：不显式建模分布，但能够采样
  - GAN (生成对抗网络)
  - Moment Matching Networks

### 1.2 GAN 的起源

GAN 由 Ian Goodfellow 等人在 2014 年提出，论文标题为 "Generative Adversarial Nets"。

**核心思想**：
受博弈论启发，通过两个网络的对抗训练来学习数据分布。

**创新点**：
- 提出对抗训练框架
- 不需要显式建模数据分布
- 可以生成高质量的样本

## 2. 核心原理

### 2.1 数学框架

GAN 的目标函数是一个极小极大博弈：

```
min_G max_D V(D, G) = E_{x~p_{data}}[log D(x)] + E_{z~p_z}[log(1 - D(G(z)))]
```

其中：
- G: 生成器，将噪声 z 映射到数据空间
- D: 判别器，输出图像是真实的概率
- p_{data}: 真实数据分布
- p_z: 噪声分布 (通常为标准正态分布)

### 2.2 训练过程

**判别器训练**：
```
max_D V(D, G) = E[log D(x)] + E[log(1 - D(G(z)))]
```
- 对真实图像，最大化 log D(x)
- 对生成图像，最大化 log(1 - D(G(z)))

**生成器训练**：
```
min_G V(D, G) = E[log(1 - D(G(z)))]
```
- 生成判别器认为是真实的图像

### 2.3 纳什均衡

在理想情况下，训练达到纳什均衡：
- 生成器生成的图像与真实图像无法区分
- 判别器对所有图像输出概率 0.5
- 此时 p_g = p_{data}

## 3. 网络架构

### 3.1 生成器架构

**基本结构**：
```
输入: 随机噪声 z (100 维)
    ↓
Linear(100, 256*7*7)
    ↓
Reshape(256, 7, 7)
    ↓
ConvTranspose2d + BatchNorm + ReLU (上采样)
    ↓
ConvTranspose2d + BatchNorm + ReLU (上采样)
    ↓
ConvTranspose2d + Tanh (输出)
    ↓
输出: 图像 (1, 28, 28)
```

**设计原则**：
- 使用反卷积 (ConvTranspose2d) 进行上采样
- 使用 BatchNorm 稳定训练
- 使用 ReLU 激活函数
- 输出层使用 Tanh (输出范围 [-1, 1])

### 3.2 判别器架构

**基本结构**：
```
输入: 图像 (1, 28, 28)
    ↓
Conv2d + LeakyReLU + Dropout (下采样)
    ↓
Conv2d + LeakyReLU + Dropout (下采样)
    ↓
Conv2d + LeakyReLU + Dropout (下采样)
    ↓
Linear + Sigmoid (分类)
    ↓
输出: 真/假概率 (0-1)
```

**设计原则**：
- 使用卷积进行下采样
- 使用 LeakyReLU 防止梯度消失
- 使用 Dropout 防止过拟合
- 输出层使用 Sigmoid (输出概率)

### 3.3 DCGAN 设计准则

DCGAN 提出了稳定 GAN 训练的设计准则：

1. 使用卷积层代替池化层
2. 在生成器和判别器中使用 BatchNorm
3. 移除全连接层
4. 生成器使用 ReLU，输出层使用 Tanh
5. 判别器使用 LeakyReLU

## 4. 训练技巧

### 4.1 标签平滑 (Label Smoothing)

将硬标签 (0/1) 转换为软标签 (0.1/0.9)：

```python
real_labels = torch.ones(batch_size, 1) * 0.9  # 而不是 1.0
fake_labels = torch.zeros(batch_size, 1) + 0.1  # 而不是 0.0
```

**作用**：防止判别器过于自信，给生成器更多学习机会。

### 4.2 噪声标签 (Noisy Labels)

随机翻转部分标签：

```python
noise_mask = torch.rand_like(labels) < 0.05
labels[noise_mask] = 1 - labels[noise_mask]
```

**作用**：增加训练的鲁棒性。

### 4.3 批次归一化 (Batch Normalization)

在生成器中使用 BatchNorm：

```python
nn.BatchNorm2d(num_features)
```

**作用**：
- 稳定训练
- 加速收敛
- 允许使用更高的学习率

### 4.4 Dropout

在判别器中使用 Dropout：

```python
nn.Dropout2d(p=0.25)
```

**作用**：防止判别器过拟合。

### 4.5 学习率调整

使用 Adam 优化器，beta1=0.5：

```python
optimizer = Adam(params, lr=0.0002, betas=(0.5, 0.999))
```

**参数说明**：
- lr: 学习率，推荐 0.0002
- beta1: 一阶矩估计的指数衰减率，推荐 0.5
- beta2: 二阶矩估计的指数衰减率，推荐 0.999

## 5. 常见问题与解决方案

### 5.1 模式崩溃 (Mode Collapse)

**表现**：生成器只生成少量相似的样本。

**原因**：生成器找到了欺骗判别器的"捷径"。

**解决方案**：
- 使用 minibatch discrimination
- 增加生成器训练次数
- 使用不同的损失函数 (如 WGAN)

### 5.2 训练不稳定

**表现**：损失震荡或不收敛。

**原因**：生成器和判别器的能力不平衡。

**解决方案**：
- 使用标签平滑
- 降低学习率
- 调整训练比例 (n_critic)
- 使用梯度惩罚

### 5.3 生成质量差

**表现**：生成的图像模糊或不真实。

**原因**：网络容量不足或训练不充分。

**解决方案**：
- 增加网络容量
- 训练更长时间
- 调整超参数
- 使用更好的架构 (如 StyleGAN)

### 5.4 梯度消失

**表现**：D_loss → 0，生成器学不到东西。

**原因**：判别器太强，生成器梯度消失。

**解决方案**：
- 使用非饱和损失
- 调整训练比例
- 使用 WGAN

## 6. GAN 变体

### 6.1 DCGAN (Deep Convolutional GAN)

**改进**：
- 使用卷积层代替全连接层
- 使用 BatchNorm
- 使用 ReLU/LeakyReLU

**贡献**：
- 提出稳定 GAN 训练的设计准则
- 证明 GAN 可以学习有意义的表示

### 6.2 WGAN (Wasserstein GAN)

**改进**：
- 使用 Wasserstein 距离代替 JS 散度
- 使用梯度惩罚 (Gradient Penalty)

**优势**：
- 更稳定的训练
- 有意义的损失指标
- 减少模式崩溃

### 6.3 Conditional GAN

**改进**：
- 生成器和判别器都接收条件信息
- 可以控制生成内容

**应用**：
- 文本到图像生成
- 图像到图像翻译
- 类别条件生成

### 6.4 StyleGAN

**改进**：
- 引入风格控制
- 使用映射网络
- 使用自适应实例归一化 (AdaIN)

**优势**：
- 生成更高质量的图像
- 可以控制生成风格
- 渐进式训练

## 7. 应用场景

### 7.1 图像生成

- 人脸生成 (StyleGAN)
- 场景生成
- 艺术创作

### 7.2 图像编辑

- 风格迁移
- 图像修复 (Inpainting)
- 超分辨率

### 7.3 数据增强

- 生成训练数据
- 平衡数据集
- 合成数据

### 7.4 其他应用

- 视频生成
- 3D 对象生成
- 音频生成

## 8. 评估指标

### 8.1 FID (Fréchet Inception Distance)

**计算方法**：
1. 使用预训练的 Inception 网络提取特征
2. 计算生成图像和真实图像特征分布的距离

**公式**：
```
FID = ||μ_r - μ_g||^2 + Tr(Σ_r + Σ_g - 2(Σ_r Σ_g)^{1/2})
```

**特点**：
- 越小越好
- 考虑了质量和多样性
- 与人类感知相关

### 8.2 IS (Inception Score)

**计算方法**：
1. 使用预训练的 Inception 网络分类
2. 计算条件分布和边缘分布的 KL 散度

**公式**：
```
IS = exp(E[KL(p(y|x) || p(y))])
```

**特点**：
- 越大越好
- 衡量质量和多样性
- 不需要真实图像

### 8.3 可视化评估

**方法**：
- 直接观察生成图像
- 比较生成图像和真实图像
- 人类评估

**优点**：
- 直观
- 易于理解

**缺点**：
- 主观
- 不可量化

## 9. 工具与框架

### 9.1 PyTorch

**优势**：
- 动态计算图
- 易于调试
- 丰富的生态

**常用模块**：
- torch.nn: 神经网络模块
- torch.optim: 优化器
- torch.utils.data: 数据加载

### 9.2 TensorFlow

**优势**：
- 工业级部署
- 丰富的工具链
- 社区支持

**常用工具**：
- tf.keras: 高级 API
- tf.data: 数据管道
- TensorBoard: 可视化

### 9.3 其他工具

- **NVIDIA StyleGAN**: 高质量人脸生成
- **Hugging Face Diffusers**: 扩散模型库
- **OpenAI CLIP**: 图文理解

## 10. 学习资源

### 10.1 论文

1. [Goodfellow et al. (2014). Generative Adversarial Nets](https://arxiv.org/abs/1406.2661)
2. [Radford et al. (2015). Unsupervised Representation Learning with DCGAN](https://arxiv.org/abs/1511.06434)
3. [Arjovsky et al. (2017). Wasserstein GAN](https://arxiv.org/abs/1701.07875)
4. [Karras et al. (2019). StyleGAN](https://arxiv.org/abs/1812.04948)

### 10.2 教程

1. [PyTorch GAN Tutorial](https://pytorch.org/tutorials/beginner/dcgan_faces_tutorial.html)
2. [GAN 原理详解](https://www.leiphone.com/category/yanxishe/Mo9YUJvnDCAabcdef.html)
3. [GAN Lab](https://poloclub.github.io/ganlab/)

### 10.3 代码库

1. [PyTorch GAN Zoo](https://github.com/facebookresearch/pytorch_GAN_zoo)
2. [NVIDIA StyleGAN](https://github.com/NVlabs/stylegan)
3. [Hugging Face Diffusers](https://github.com/huggingface/diffusers)

## 11. 总结

### 11.1 GAN 的优势

- 可以生成高质量的样本
- 不需要显式建模数据分布
- 可以学习数据的复杂分布
- 应用广泛

### 11.2 GAN 的挑战

- 训练不稳定
- 模式崩溃
- 评估困难
- 调参困难

### 11.3 未来方向

- 更稳定的训练方法
- 更高质量的生成
- 更多的应用场景
- 与其他技术的结合

## 12. 项目规划

### 12.1 实现目标

1. 实现基本的 GAN 框架
2. 实现生成器和判别器
3. 实现对抗训练
4. 在 MNIST 数据集上验证
5. 探索训练技巧

### 12.2 技术选型

- 框架：PyTorch
- 数据集：MNIST
- 网络：DCGAN 架构
- 优化器：Adam

### 12.3 开发计划

1. Week 1: 实现基本框架
2. Week 2: 实现训练循环
3. Week 3: 调试和优化
4. Week 4: 文档和总结
