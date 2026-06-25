# GAN 生成对抗网络 - 从零实现

从零实现生成对抗网络 (GAN)，理解图像生成的对抗训练原理。

## 学习目标

- 理解 GAN 的对抗训练原理和纳什均衡
- 掌握生成器和判别器的网络设计
- 学会训练稳定性技巧（标签平滑、噪声标签等）
- 实现完整的 GAN 图像生成系统

## 项目结构

```
gan/
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档
│   ├── 01-RESEARCH.md      # 调研文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发文档
├── src/                    # 源代码
│   ├── __init__.py         # 包初始化
│   ├── generator.py        # 生成器实现
│   ├── discriminator.py    # 判别器实现
│   ├── gan.py              # GAN 框架
│   └── trainer.py          # 训练器
├── tests/                  # 测试
│   └── test_gan.py         # 测试套件
└── examples/               # 示例
    ├── train_mnist.py      # MNIST 训练示例
    └── simple_example.py   # 简单示例
```

## 核心概念

### 什么是 GAN?

生成对抗网络 (Generative Adversarial Network) 是一种生成模型，由两个神经网络组成：

1. **生成器 (Generator)**: 从随机噪声生成图像
2. **判别器 (Discriminator)**: 区分真实图像和生成图像

```
随机噪声 z ~ N(0,1)
        ↓
    生成器 G
        ↓
    假图像 G(z)
        ↓
    判别器 D ← 真实图像 x
        ↓
    真/假概率
```

### 对抗训练

GAN 的训练是一个极小极大博弈：

```
min_G max_D V(D, G) = E[log D(x)] + E[log(1 - D(G(z)))]
```

- **判别器目标**: 最大化 log D(x) + log(1 - D(G(z)))
  - 对真实图像输出高概率
  - 对生成图像输出低概率

- **生成器目标**: 最大化 log D(G(z))
  - 生成判别器认为是真实的图像

### 纳什均衡

理想情况下，训练达到纳什均衡：
- 生成器生成的图像与真实图像无法区分
- 判别器对所有图像输出概率 0.5

## 快速开始

### 安装依赖

```bash
pip install torch torchvision matplotlib numpy pytest
```

### 使用示例

```python
from src import GAN

# 创建 GAN
gan = GAN(
    latent_dim=100,
    img_channels=1,
    img_size=28,
    lr=0.0002,
    beta1=0.5
)

# 训练
for epoch in range(100):
    for real_images in dataloader:
        stats = gan.train_step(real_images)
        print(f"D_loss: {stats['d_loss']:.4f}, G_loss: {stats['g_loss']:.4f}")

# 生成图像
samples = gan.generate_samples(n_samples=16, device="cpu")
```

### 运行简单示例

```bash
cd projects/gan
python examples/simple_example.py
```

### 运行 MNIST 训练

```bash
cd projects/gan
python examples/train_mnist.py
```

### 运行测试

```bash
cd projects/gan
python -m pytest tests/ -v
```

## 网络架构

### 生成器 (Generator)

```
输入: 随机噪声 z (100 维)
    ↓
Linear(100, 256*7*7)
    ↓
Reshape(256, 7, 7)
    ↓
ConvTranspose2d(256, 128, 4, 2, 1) + BatchNorm + ReLU
    ↓
ConvTranspose2d(128, 64, 4, 2, 1) + BatchNorm + ReLU
    ↓
ConvTranspose2d(64, 1, 4, 2, 1) + Tanh
    ↓
输出: 图像 (1, 28, 28)
```

### 判别器 (Discriminator)

```
输入: 图像 (1, 28, 28)
    ↓
Conv2d(1, 64, 4, 2, 1) + LeakyReLU + Dropout
    ↓
Conv2d(64, 128, 4, 2, 1) + LeakyReLU + Dropout
    ↓
Conv2d(128, 256, 4, 2, 1) + LeakyReLU + Dropout
    ↓
Linear(256*3*3, 1) + Sigmoid
    ↓
输出: 真/假概率 (0-1)
```

## 训练稳定性技巧

### 1. 标签平滑 (Label Smoothing)

将硬标签 (0/1) 转换为软标签 (0.1/0.9)：

```python
real_labels = torch.ones(batch_size, 1) * 0.9  # 而不是 1.0
fake_labels = torch.zeros(batch_size, 1) + 0.1  # 而不是 0.0
```

### 2. 噪声标签 (Noisy Labels)

随机翻转部分标签：

```python
noise_mask = torch.rand_like(labels) < 0.05
labels[noise_mask] = 1 - labels[noise_mask]
```

### 3. 批次归一化 (Batch Normalization)

在生成器中使用 BatchNorm 稳定训练。

### 4. Dropout

在判别器中使用 Dropout 防止过拟合。

### 5. 学习率调整

使用 Adam 优化器，beta1=0.5：

```python
optimizer = Adam(params, lr=0.0002, betas=(0.5, 0.999))
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| latent_dim | 噪声向量维度 | 100 |
| img_channels | 图像通道数 (1=灰度, 3=RGB) | 1 |
| img_size | 图像尺寸 | 28 |
| lr | 学习率 | 0.0002 |
| beta1 | Adam 优化器 beta1 | 0.5 |
| beta2 | Adam 优化器 beta2 | 0.999 |
| label_smoothing | 标签平滑系数 | 0.1 |
| n_critic | 判别器训练次数比率 | 1 |

## 数学原理

### GAN 损失函数

**判别器损失**:
$$L_D = -\mathbb{E}_{x \sim p_{data}}[\log D(x)] - \mathbb{E}_{z \sim p_z}[\log(1 - D(G(z)))]$$

**生成器损失**:
$$L_G = -\mathbb{E}_{z \sim p_z}[\log D(G(z))]$$

### 优化目标

**判别器**: 最大化 $V(D, G) = \mathbb{E}[\log D(x)] + \mathbb{E}[\log(1 - D(G(z)))]$

**生成器**: 最小化 $\mathbb{E}[\log(1 - D(G(z)))]$

或等价地最大化 $\mathbb{E}[\log D(G(z))]$（非饱和损失）

### 纳什均衡条件

当 $p_g = p_{data}$ 时达到纳什均衡：
- $D^*(x) = \frac{1}{2}$ 对所有 x
- $G$ 生成与真实数据分布相同的样本

## 常见问题

### 1. 模式崩溃 (Mode Collapse)

生成器只生成少量相似的样本。

**解决方案**:
- 使用 minibatch discrimination
- 增加生成器训练次数
- 使用不同的损失函数

### 2. 训练不稳定

损失震荡或不收敛。

**解决方案**:
- 使用标签平滑
- 降低学习率
- 使用梯度惩罚

### 3. 生成质量差

生成的图像模糊或不真实。

**解决方案**:
- 增加网络容量
- 训练更长时间
- 调整超参数

## 参考资料

- [Goodfellow et al. (2014). Generative Adversarial Nets](https://arxiv.org/abs/1406.2661)
- [Radford et al. (2015). Unsupervised Representation Learning with DCGAN](https://arxiv.org/abs/1511.06434)
- [GAN 原理详解](https://www.leiphone.com/category/yanxishe/Mo9YUJvnDCAabcdef.html)
- [PyTorch GAN 教程](https://pytorch.org/tutorials/beginner/dcgan_faces_tutorial.html)

## License

MIT

---

[返回 AI 模块](../AI_README.md) | [返回主目录](../../README.md)
