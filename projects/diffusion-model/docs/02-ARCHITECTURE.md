# 架构设计文档

## 1. 系统架构概述

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Diffusion Model System                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   UNet      │  │  Scheduler  │  │  Trainer    │         │
│  │  (Noise     │  │  (Noise     │  │  (Training  │         │
│  │  Predictor) │  │  Process)   │  │  Loop)      │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │
│         └────────────────┼────────────────┘                │
│                          │                                 │
│                    ┌─────▼─────┐                           │
│                    │ Diffusion │                           │
│                    │   Model   │                           │
│                    └─────┬─────┘                           │
│                          │                                 │
│  ┌───────────────────────┼───────────────────────┐         │
│  │                       │                       │         │
│  ▼                       ▼                       ▼         │
│ ┌─────────┐      ┌─────────────┐         ┌─────────┐      │
│ │Training │      │  Sampling   │         │Evaluation│      │
│ │  Loss   │      │  Process    │         │ Metrics  │      │
│ └─────────┘      └─────────────┘         └─────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

| 模块 | 职责 | 主要类 |
|------|------|--------|
| Scheduler | 噪声调度 | `NoiseScheduler` |
| UNet | 噪声预测 | `UNet`, `SimpleUNet` |
| Diffusion | 核心逻辑 | `DiffusionModel` |
| Trainer | 训练管理 | `DiffusionTrainer` |
| Utils | 工具函数 | 各种辅助函数 |

## 2. 详细设计

### 2.1 噪声调度器设计

#### 2.1.1 类结构

```python
class NoiseScheduler:
    """
    噪声调度器

    职责：
    - 管理噪声水平（beta schedule）
    - 计算前向扩散参数
    - 提供采样接口
    """

    def __init__(self, num_timesteps, beta_start, beta_end, schedule_type):
        # 初始化参数
        pass

    def add_noise(self, x_0, t, noise=None):
        """前向扩散：向图像添加噪声"""
        pass

    def sample_timestep(self, batch_size, device):
        """采样时间步"""
        pass
```

#### 2.1.2 关键数据结构

```python
# 噪声调度参数
betas: Tensor[T]                    # 噪声水平
alphas: Tensor[T]                   # 1 - betas
alphas_cumprod: Tensor[T]           # 累积乘积
sqrt_alphas_cumprod: Tensor[T]      # √(ᾱ_t)
sqrt_one_minus_alphas_cumprod: Tensor[T]  # √(1-ᾱ_t)

# 反向过程参数
sqrt_recip_alphas: Tensor[T]        # √(1/α_t)
posterior_variance: Tensor[T]       # 后验方差
```

#### 2.1.3 设计决策

**为什么预计算所有参数**：
- 避免重复计算
- 加速训练和采样
- 便于调试和可视化

**为什么支持多种调度**：
- 线性调度：简单直观，便于理解
- 余弦调度：效果更好，改进版本使用
- 便于实验对比

### 2.2 UNet 设计

#### 2.2.1 类结构

```python
class SimpleUNet(nn.Module):
    """
    简化版 UNet

    适用于：
    - MNIST 等小图像
    - 教学和实验
    - 快速原型开发
    """

    def __init__(self, in_channels, out_channels, time_emb_dim):
        # 编码器
        self.enc1 = Block(in_channels, 64)
        self.enc2 = Block(64, 128)
        self.enc3 = Block(128, 256)

        # 瓶颈层
        self.bottleneck = Block(256, 256)

        # 解码器
        self.dec3 = Block(256 + 256, 128)
        self.dec2 = Block(128 + 128, 64)
        self.dec1 = Block(64 + 64, out_channels)

    def forward(self, x, t):
        # 编码
        e1 = self.enc1(x)
        e2 = self.enc2(downsample(e1))
        e3 = self.enc3(downsample(e2))

        # 瓶颈
        b = self.bottleneck(e3)
        b += time_projection(t)

        # 解码
        d3 = self.dec3(cat(upsample(b), e3))
        d2 = self.dec2(cat(upsample(d3), e2))
        d1 = self.dec1(cat(upsample(d2), e1))

        return d1


class UNet(nn.Module):
    """
    完整版 UNet

    特点：
    - 多尺度特征提取
    - 注意力机制
    - 残差连接
    - 适用于更复杂的任务
    """
```

#### 2.2.2 关键组件

**残差块（ResidualBlock）**：
```python
class ResidualBlock(nn.Module):
    def __init__(self, in_ch, out_ch, time_emb_dim):
        self.norm1 = GroupNorm(in_ch)
        self.conv1 = Conv2d(in_ch, out_ch)
        self.time_mlp = Linear(time_emb_dim, out_ch)
        self.norm2 = GroupNorm(out_ch)
        self.conv2 = Conv2d(out_ch, out_ch)
        self.shortcut = Conv2d(in_ch, out_ch) if in_ch != out_ch else Identity()

    def forward(self, x, t_emb):
        h = self.conv1(silu(self.norm1(x)))
        h += self.time_mlp(t_emb)
        h = self.conv2(silu(self.norm2(h)))
        return h + self.shortcut(x)
```

**注意力块（AttentionBlock）**：
```python
class AttentionBlock(nn.Module):
    def __init__(self, channels):
        self.norm = GroupNorm(channels)
        self.attention = MultiheadAttention(channels, num_heads=4)

    def forward(self, x):
        B, C, H, W = x.shape
        h = self.norm(x)
        h = h.view(B, C, H*W).transpose(1, 2)
        h, _ = self.attention(h, h, h)
        h = h.transpose(1, 2).view(B, C, H, W)
        return h + x
```

**时间嵌入（SinusoidalPositionEmbeddings）**：
```python
class SinusoidalPositionEmbeddings(nn.Module):
    def __init__(self, dim):
        self.dim = dim

    def forward(self, t):
        half_dim = self.dim // 2
        embeddings = math.log(10000) / (half_dim - 1)
        embeddings = torch.exp(torch.arange(half_dim) * -embeddings)
        embeddings = t[:, None] * embeddings[None, :]
        return torch.cat([embeddings.sin(), embeddings.cos()], dim=-1)
```

#### 2.2.3 设计决策

**为什么使用跳跃连接**：
- 保留细节信息
- 缓解梯度消失
- 加速训练收敛

**为什么使用 GroupNorm**：
- 对批次大小不敏感
- 训练更稳定
- 适合小批次训练

**为什么使用 SiLU 激活**：
- 平滑的激活函数
- 梯度行为良好
- 在扩散模型中效果好

### 2.3 扩散模型设计

#### 2.3.1 类结构

```python
class DiffusionModel(nn.Module):
    """
    扩散模型核心类

    职责：
    - 整合 UNet 和 Scheduler
    - 实现训练逻辑
    - 实现采样逻辑
    """

    def __init__(self, model, scheduler, image_size, in_channels):
        self.model = model
        self.scheduler = scheduler

    def training_loss(self, x_0):
        """计算训练损失"""
        t = self.scheduler.sample_timestep(batch_size)
        noise = torch.randn_like(x_0)
        x_t, noise = self.scheduler.add_noise(x_0, t, noise)
        noise_pred = self.model(x_t, t)
        return F.mse_loss(noise_pred, noise)

    def sample(self, batch_size, device):
        """生成新图像"""
        x = torch.randn(batch_size, self.in_channels, self.image_size, self.image_size)

        for t in reversed(range(self.num_timesteps)):
            noise_pred = self.model(x, t)
            x = self.reverse_step(x, noise_pred, t)

        return x
```

#### 2.3.2 训练流程

```python
def train_epoch(model, dataloader, optimizer):
    model.train()

    for batch in dataloader:
        x_0 = batch

        # 前向传播
        loss = model.training_loss(x_0)

        # 反向传播
        optimizer.zero_grad()
        loss.backward()

        # 梯度裁剪
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

        # 更新参数
        optimizer.step()
```

#### 2.3.3 采样流程

```python
def sample(model, batch_size, device):
    model.eval()

    # 从纯噪声开始
    x = torch.randn(batch_size, 1, 28, 28).to(device)

    # 反向扩散
    for t in reversed(range(1000)):
        t_batch = torch.full((batch_size,), t, device=device)

        # 预测噪声
        noise_pred = model(x, t_batch)

        # 计算均值
        mean = compute_mean(x, noise_pred, t)

        # 添加噪声（最后一步不加）
        if t > 0:
            noise = torch.randn_like(x)
            variance = compute_variance(t)
            x = mean + variance * noise
        else:
            x = mean

    return x
```

### 2.4 训练器设计

#### 2.4.1 类结构

```python
class DiffusionTrainer:
    """
    训练器

    职责：
    - 管理训练循环
    - 处理优化器
    - 保存检查点
    - 记录训练历史
    """

    def __init__(self, model, learning_rate, device):
        self.model = model
        self.optimizer = Adam(model.parameters(), lr=learning_rate)
        self.losses = []

    def train_epoch(self, dataloader):
        """训练一个 epoch"""
        pass

    def train(self, dataloader, num_epochs, sample_interval):
        """完整训练流程"""
        pass

    def save_checkpoint(self, path):
        """保存检查点"""
        pass

    def load_checkpoint(self, path):
        """加载检查点"""
        pass
```

## 3. 数据流设计

### 3.1 训练数据流

```
输入图像 x_0
    │
    ▼
采样时间步 t
    │
    ▼
采样噪声 ε
    │
    ▼
前向扩散: x_t = √(ᾱ_t) * x_0 + √(1-ᾱ_t) * ε
    │
    ▼
UNet 预测: ε_pred = UNet(x_t, t)
    │
    ▼
计算损失: L = MSE(ε_pred, ε)
    │
    ▼
反向传播和参数更新
```

### 3.2 采样数据流

```
采样初始噪声 x_T ~ N(0, I)
    │
    ▼
对于 t = T, T-1, ..., 1:
    │
    ├─→ 预测噪声: ε_pred = UNet(x_t, t)
    │
    ├─→ 计算均值: μ = (1/√α_t) * (x_t - (β_t/√(1-ᾱ_t)) * ε_pred)
    │
    └─→ 采样 x_{t-1} = μ + σ_t * z (z ~ N(0, I))
    │
    ▼
返回生成图像 x_0
```

## 4. 接口设计

### 4.1 核心接口

```python
# 噪声调度器接口
class NoiseScheduler(Protocol):
    def add_noise(self, x_0: Tensor, t: Tensor) -> Tuple[Tensor, Tensor]: ...
    def sample_timestep(self, batch_size: int, device: Device) -> Tensor: ...

# 模型接口
class NoisePredictor(Protocol):
    def forward(self, x: Tensor, t: Tensor) -> Tensor: ...

# 训练器接口
class Trainer(Protocol):
    def train_epoch(self, dataloader: DataLoader) -> float: ...
    def save_checkpoint(self, path: str) -> None: ...
```

### 4.2 配置接口

```python
@dataclass
class DiffusionConfig:
    image_size: int = 28
    in_channels: int = 1
    num_timesteps: int = 1000
    beta_start: float = 0.0001
    beta_end: float = 0.02
    schedule_type: str = "linear"
    model_type: str = "simple"
```

## 5. 扩展性设计

### 5.1 添加新的噪声调度

```python
class NewScheduler(NoiseScheduler):
    def _compute_betas(self):
        """实现新的 beta 计算逻辑"""
        pass
```

### 5.2 添加新的模型架构

```python
class NewModel(nn.Module):
    def forward(self, x, t):
        """实现新的模型架构"""
        pass
```

### 5.3 添加新的采样方法

```python
@torch.no_grad()
def new_sampling_method(model, scheduler, batch_size, device):
    """实现新的采样方法"""
    pass
```

## 6. 性能考虑

### 6.1 计算效率

**内存优化**：
- 使用梯度检查点
- 混合精度训练
- 梯度累积

**计算优化**：
- 预计算常用值
- 使用高效的注意力实现
- 并行处理

### 6.2 可扩展性

**水平扩展**：
- 数据并行
- 模型并行
- 分布式训练

**垂直扩展**：
- 更大的模型
- 更高的分辨率
- 更多的条件信息

## 7. 测试策略

### 7.1 单元测试

- 每个组件独立测试
- 边界条件测试
- 数值正确性测试

### 7.2 集成测试

- 组件间交互测试
- 端到端流程测试
- 性能基准测试

### 7.3 回归测试

- 已知问题修复验证
- 性能回归检测
- 兼容性测试

## 8. 总结

### 8.1 设计原则

1. **模块化**：各组件职责清晰，易于理解和维护
2. **可扩展**：支持添加新的组件和方法
3. **高效性**：优化计算和内存使用
4. **可测试**：便于编写和运行测试

### 8.2 权衡决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 模型架构 | UNet | 适合图像生成，效果好 |
| 噪声调度 | 线性+余弦 | 简单直观，便于理解 |
| 训练策略 | 简单 SGD | 教学目的，易于理解 |
| 采样方法 | DDPM + DDIM | 覆盖基础和改进方法 |

### 8.3 未来改进

1. **架构改进**：添加 Transformer、更大模型
2. **训练改进**：EMA、混合精度、分布式
3. **采样改进**：更多采样方法、更快的采样
4. **应用扩展**：条件生成、图像编辑、视频生成
