# Diffusion Model - DDPM 实现

> 实现扩散模型，理解图像生成的前沿技术

## 项目简介

本项目实现了 **Denoising Diffusion Probabilistic Models (DDPM)**，这是当前最先进的图像生成技术之一。通过学习如何从噪声中逐步恢复图像，模型能够生成高质量的新图像。

### 核心概念

扩散模型的核心思想是：
1. **前向扩散**：逐步向图像添加高斯噪声，直到变成纯噪声
2. **反向去噪**：学习从噪声中逐步恢复图像的过程
3. **图像生成**：从随机噪声开始，通过反向过程生成新图像

```
图像 → 前向扩散（加噪） → 噪声预测网络 → 反向去噪 → 生成图像
```

## 快速开始

### 安装依赖

```bash
cd projects/diffusion-model
pip install -r requirements.txt
```

### 训练模型

```bash
# 使用默认参数训练
python examples/train_mnist.py

# 自定义参数训练
python examples/train_mnist.py \
    --epochs 100 \
    --batch-size 64 \
    --lr 1e-4 \
    --timesteps 500
```

### 生成图像

```bash
# 从训练好的模型生成图像
python examples/generate_samples.py \
    --checkpoint ./checkpoints/best_model.pt \
    --num-samples 16

# 使用DDIM加速采样
python examples/generate_samples.py \
    --checkpoint ./checkpoints/best_model.pt \
    --use-ddim \
    --ddim-steps 50

# 可视化反向过程
python examples/generate_samples.py \
    --checkpoint ./checkpoints/best_model.pt \
    --visualize
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_scheduler.py -v
pytest tests/test_unet.py -v
pytest tests/test_diffusion.py -v
```

## 项目结构

```
diffusion-model/
├── README.md                 # 项目说明文档
├── LEARNING_NOTES.md         # 学习笔记
├── requirements.txt          # Python 依赖
├── src/                      # 源代码
│   ├── __init__.py          # 包初始化
│   ├── diffusion.py         # 扩散模型核心实现
│   ├── unet.py              # UNet 噪声预测网络
│   ├── scheduler.py         # 噪声调度器
│   └── utils.py             # 工具函数
├── tests/                    # 测试代码
│   ├── test_scheduler.py    # 噪声调度器测试
│   ├── test_unet.py         # UNet 测试
│   └── test_diffusion.py    # 扩散模型测试
├── examples/                 # 示例代码
│   ├── train_mnist.py       # MNIST 训练脚本
│   └── generate_samples.py  # 图像生成脚本
└── docs/                     # 文档
    ├── 01-RESEARCH.md       # 技术调研
    ├── 02-ARCHITECTURE.md   # 架构设计
    ├── 03-IMPLEMENTATION.md # 实现细节
    ├── 04-TESTING.md        # 测试说明
    └── 05-DEVELOPMENT.md    # 开发指南
```

## 核心组件

### 1. 噪声调度器 (NoiseScheduler)

控制前向扩散过程中的噪声添加：

```python
from src.scheduler import NoiseScheduler

scheduler = NoiseScheduler(
    num_timesteps=1000,
    beta_start=0.0001,
    beta_end=0.02,
    schedule_type="linear"  # 或 "cosine"
)

# 前向扩散：向图像添加噪声
x_t, noise = scheduler.add_noise(x_0, t)
```

**关键公式**：
- 前向过程：`q(x_t | x_0) = N(x_t; √(α_t) * x_0, (1 - α_t) * I)`
- 其中 `α_t = ∏(1 - β_s)` for s=1 to t

### 2. UNet 噪声预测网络

用于预测添加到图像中的噪声：

```python
from src.unet import SimpleUNet, UNet

# 简化版 UNet（适用于 MNIST）
model = SimpleUNet(
    in_channels=1,
    out_channels=1,
    time_emb_dim=128
)

# 完整版 UNet（带注意力机制）
model = UNet(
    in_channels=1,
    out_channels=1,
    hidden_channels=[64, 128, 256],
    attention=True
)

# 预测噪声
noise_pred = model(x_t, t)
```

**网络特点**：
- 时间嵌入：使用正弦位置编码表示时间步
- 跳跃连接：U-Net 结构保留细节信息
- 注意力机制：捕获长距离依赖关系

### 3. 扩散模型 (DiffusionModel)

整合所有组件的核心类：

```python
from src.diffusion import DiffusionModel

model = DiffusionModel(
    image_size=28,
    in_channels=1,
    num_timesteps=1000,
    model_type="simple"
)

# 计算训练损失
loss = model.training_loss(x_0)

# 生成新图像
samples = model.sample(batch_size=16)
```

**训练目标**：
- 损失函数：`L = MSE(ε_pred, ε)`
- 其中 `ε` 是添加的噪声，`ε_pred` 是模型预测的噪声

## 技术细节

### 扩散过程数学原理

**前向过程**（加噪）：
```
q(x_t | x_{t-1}) = N(x_t; √(1-β_t) * x_{t-1}, β_t * I)
```

**反向过程**（去噪）：
```
p_θ(x_{t-1} | x_t) = N(x_{t-1}; μ_θ(x_t, t), Σ_θ(x_t, t))
```

**训练目标**：
```
L_simple = E_{t,x_0,ε} [||ε - ε_θ(√(ᾱ_t) * x_0 + √(1-ᾱ_t) * ε, t)||²]
```

### 采样算法

**DDPM 采样**（原始算法）：
```
1. 从 x_T ~ N(0, I) 开始
2. 对于 t = T, T-1, ..., 1:
   - 预测噪声 ε_θ(x_t, t)
   - 计算均值 μ_θ
   - 添加噪声（t > 0 时）
3. 返回 x_0
```

**DDIM 采样**（加速版本）：
```
1. 从 x_T ~ N(0, I) 开始
2. 选择时间步子序列
3. 对于每个时间步:
   - 预测 x_0
   - 计算 x_{t-1}
4. 返回 x_0
```

## 性能指标

### 训练指标
- **损失函数**：MSE 损失，越低越好
- **FID 分数**：衡量生成图像质量（越低越好）
- **IS 分数**：衡量生成多样性（越高越好）

### 生成质量
- **清晰度**：生成图像是否清晰
- **多样性**：生成样本是否多样
- **真实性**：是否接近真实数据分布

## 学习资源

### 核心论文
- [Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) - DDPM 原始论文
- [Denoising Diffusion Implicit Models](https://arxiv.org/abs/2010.02502) - DDIM 加速采样
- [Improved Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2102.09672) - 改进版本

### 教程和博客
- [Lilian Weng's Blog](https://lilianweng.github.io/posts/2021-07-11-diffusion-models/) - 优秀的技术博客
- [Hugging Face Diffusion Course](https://huggingface.co/learn/diffusion-course) - 交互式教程
- [The Annotated Diffusion Model](https://huggingface.co/blog/annotated-diffusion) - 代码注释版

### 开源实现
- [lucidrains/denoising-diffusion-pytorch](https://github.com/lucidrains/denoising-diffusion-pytorch) - 流行实现
- [hojonathanho/diffusion](https://github.com/hojonathanho/diffusion) - 原始实现

## 常见问题

### Q: 为什么需要这么多时间步？
A: 更多时间步意味着更细粒度的噪声添加/去除，理论上能生成更高质量的图像。但 DDIM 等方法可以用更少的时间步达到类似效果。

### Q: 如何选择噪声调度？
A: 线性调度是最简单的，但余弦调度通常效果更好。具体选择取决于数据集和任务。

### Q: 训练需要多长时间？
A: 在 MNIST 上，使用 GPU 训练 50-100 个 epoch 通常可以得到不错的结果。对于更复杂的数据集，可能需要更长时间。

### Q: 如何提高生成质量？
A: 可以尝试：
- 增加模型容量（更多层、更多通道）
- 使用注意力机制
- 调整噪声调度
- 增加训练时间
- 使用更好的采样方法（如 DDIM）

## 下一步

完成本项目后，可以探索：
1. **条件生成**：根据标签生成特定数字
2. **图像编辑**：修复、风格迁移等
3. **更高分辨率**：生成 64x64 或更高分辨率图像
4. **其他数据集**：CIFAR-10、CelebA 等
5. **高级技术**：Classifier-Free Guidance、Latent Diffusion 等

## 许可证

本项目仅用于学习目的。

## 致谢

感谢 DDPM 论文作者 Jonathan Ho 等人的开创性工作，以及开源社区的各种实现参考。
