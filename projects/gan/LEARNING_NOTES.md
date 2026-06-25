# GAN 学习笔记

## 学习路径

### 第一阶段：理解 GAN 基础 (Week 1)

#### 1.1 GAN 的核心思想

GAN 的核心是**对抗训练**：两个网络相互博弈，共同进步。

**类比**：
- 生成器 = 造假币的人
- 判别器 = 警察
- 随着训练进行，造假技术越来越高，警察鉴别能力也越来越强
- 最终达到平衡：假币和真币无法区分

**数学表示**：
```
min_G max_D V(D, G) = E[log D(x)] + E[log(1 - D(G(z)))]
```

#### 1.2 网络架构理解

**生成器**：
- 输入：随机噪声向量 z (通常 100 维)
- 输出：生成的图像
- 关键：使用反卷积 (ConvTranspose2d) 上采样

**判别器**：
- 输入：图像 (真实或生成)
- 输出：图像是真实的概率 (0-1)
- 关键：使用卷积下采样

#### 1.3 训练过程

```
for each epoch:
    for each batch:
        # 1. 训练判别器
        real_loss = -log(D(real_images))
        fake_loss = -log(1 - D(G(noise)))
        d_loss = (real_loss + fake_loss) / 2
        
        # 2. 训练生成器
        g_loss = -log(D(G(noise)))
```

### 第二阶段：深入理解 (Week 2)

#### 2.1 为什么需要 GAN?

**传统生成方法**：
- VAE：显式建模数据分布，但生成图像模糊
- PixelCNN：自回归生成，但速度慢

**GAN 的优势**：
- 隐式建模数据分布
- 生成高质量图像
- 可以学习数据的复杂分布

#### 2.2 损失函数分析

**原始损失 (Non-saturating)**：
```
L_G = -E[log D(G(z))]
```

**为什么不用原始形式**：
```
L_G = E[log(1 - D(G(z)))]
```
因为在训练初期，生成器很弱，D(G(z)) ≈ 0，导致梯度消失。

**其他损失函数**：
- Wasserstein 距离
- Hinge 损失
- Least Squares GAN

#### 2.3 训练稳定性

**问题**：
- 模式崩溃：生成器只生成少量样本
- 训练不稳定：损失震荡
- 梯度消失/爆炸

**解决方案**：
- 标签平滑
- 噪声标签
- 批次归一化
- Dropout
- 学习率调整

### 第三阶段：实践与优化 (Week 3)

#### 3.1 实现细节

**权重初始化**：
```python
nn.init.normal_(m.weight, 0.0, 0.02)
```

**激活函数**：
- 生成器：ReLU (隐藏层) + Tanh (输出层)
- 判别器：LeakyReLU (隐藏层) + Sigmoid (输出层)

**优化器**：
```python
Adam(lr=0.0002, betas=(0.5, 0.999))
```

#### 3.2 调试技巧

**监控指标**：
- D_loss: 判别器损失
- G_loss: 生成器损失
- D_real_acc: 判别器对真实图像的准确率
- D_fake_acc: 判别器对生成图像的准确率

**健康训练的标志**：
- D_loss 稳定在 0.5-1.0
- G_loss 逐渐下降
- D_real_acc 和 D_fake_acc 都在 0.5-0.8

**问题诊断**：
- D_loss → 0: 判别器太强，生成器学不到东西
- G_loss → 0: 生成器欺骗了判别器，但可能模式崩溃
- D_real_acc → 1, D_fake_acc → 0: 判别器完美区分真假

#### 3.3 超参数调优

**学习率**：
- 推荐：0.0002
- 太大：训练不稳定
- 太小：收敛慢

**批次大小**：
- 推荐：64-128
- 太大：内存占用高
- 太小：训练不稳定

**噪声维度**：
- 推荐：100
- 太小：生成多样性不足
- 太大：计算开销大

### 第四阶段：进阶主题 (Week 4)

#### 4.1 GAN 变体

**DCGAN**：
- 使用卷积层代替全连接层
- 使用 BatchNorm
- 使用 ReLU/LeakyReLU

**WGAN**：
- 使用 Wasserstein 距离
- 使用梯度惩罚
- 更稳定的训练

**Conditional GAN**：
- 生成器和判别器都接收条件信息
- 可以控制生成内容

**StyleGAN**：
- 引入风格控制
- 生成更高质量的图像

#### 4.2 应用场景

**图像生成**：
- 人脸生成
- 场景生成
- 艺术创作

**图像编辑**：
- 风格迁移
- 图像修复
- 超分辨率

**数据增强**：
- 生成训练数据
- 平衡数据集

#### 4.3 评估指标

**FID (Fréchet Inception Distance)**：
- 计算生成图像和真实图像在特征空间的距离
- 越小越好

**IS (Inception Score)**：
- 衡量生成图像的质量和多样性
- 越大越好

**可视化评估**：
- 生成图像的视觉质量
- 多样性
- 真实性

## 关键概念总结

### 1. 对抗训练原理

```
生成器 G: z → x_fake (试图欺骗判别器)
判别器 D: x → [0,1] (试图区分真假)
```

### 2. 纳什均衡

当生成器生成的图像与真实图像无法区分时：
- D(x) = 0.5 对所有 x
- p_g = p_data

### 3. 训练技巧

- 标签平滑：防止判别器过强
- 噪声标签：增加鲁棒性
- 批次归一化：稳定训练
- Dropout：防止过拟合
- 学习率调整：控制训练速度

### 4. 常见问题与解决

| 问题 | 表现 | 解决方案 |
|------|------|----------|
| 模式崩溃 | 生成样本单一 | minibatch discrimination |
| 训练不稳定 | 损失震荡 | 标签平滑、降低学习率 |
| 生成模糊 | 图像质量差 | 增加网络容量、训练更久 |
| 梯度消失 | D_loss → 0 | 调整训练比例、使用不同损失 |

## 学习资源

### 论文
1. [Goodfellow et al. (2014). Generative Adversarial Nets](https://arxiv.org/abs/1406.2661)
2. [Radford et al. (2015). DCGAN](https://arxiv.org/abs/1511.06434)
3. [Arjovsky et al. (2017). Wasserstein GAN](https://arxiv.org/abs/1701.07875)

### 教程
1. [PyTorch GAN Tutorial](https://pytorch.org/tutorials/beginner/dcgan_faces_tutorial.html)
2. [GAN 原理详解](https://www.leiphone.com/category/yanxishe/Mo9YUJvnDCAabcdef.html)

### 代码库
1. [PyTorch GAN Zoo](https://github.com/facebookresearch/pytorch_GAN_zoo)
2. [GAN Lab](https://poloclub.github.io/ganlab/)

## 学习心得

### 理解的关键

1. **对抗的本质**：GAN 的核心是博弈论，两个玩家相互竞争
2. **隐式建模**：GAN 不显式建模数据分布，而是通过对抗学习
3. **训练艺术**：GAN 训练更像是一门艺术，需要大量调参

### 实践体会

1. **从小规模开始**：先用简单数据集验证代码
2. **监控训练过程**：及时发现问题并调整
3. **耐心调参**：GAN 训练需要时间和耐心

### 未来方向

1. **WGAN**：更稳定的训练
2. **StyleGAN**：更高质量的生成
3. **Conditional GAN**：可控生成
4. **Diffusion Models**：新一代生成模型
