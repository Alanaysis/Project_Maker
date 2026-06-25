# 实现细节文档

## 1. 实现概述

本文档详细描述了 DDPM（Denoising Diffusion Probabilistic Model）的实现细节，包括核心算法、关键组件和实现技巧。

## 2. 噪声调度器实现

### 2.1 线性噪声调度

```python
def _linear_schedule(self) -> torch.Tensor:
    """
    创建线性噪声调度

    beta_t 从 beta_start 线性增加到 beta_end
    通常：beta_start = 0.0001, beta_end = 0.02
    """
    return torch.linspace(self.beta_start, self.beta_end, self.num_timesteps)
```

**实现要点**：
- 使用 `torch.linspace` 生成均匀分布的 beta 值
- 确保 beta 值在 (0, 1) 范围内
- 典型值：beta_start = 0.0001, beta_end = 0.02

### 2.2 余弦噪声调度

```python
def _cosine_schedule(self) -> torch.Tensor:
    """
    创建余弦噪声调度

    来自论文：Improved Denoising Diffusion Probabilistic Models
    优点：避免后期噪声过大，提高生成质量
    """
    steps = self.num_timesteps + 1
    x = torch.linspace(0, self.num_timesteps, steps)

    # 余弦函数计算 alpha_cumprod
    alphas_cumprod = torch.cos(((x / self.num_timesteps) + 0.008) / 1.008 * torch.pi * 0.5) ** 2
    alphas_cumprod = alphas_cumprod / alphas_cumprod[0]

    # 从 alpha_cumprod 计算 beta
    betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])

    return torch.clip(betas, 0.0001, 0.9999)
```

**实现要点**：
- 使用余弦函数生成更平滑的噪声调度
- 添加小的偏移量（0.008）避免数值问题
- 使用 `torch.clip` 确保 beta 在合理范围内

### 2.3 前向扩散过程

```python
def add_noise(
    self,
    x_0: torch.Tensor,
    t: torch.Tensor,
    noise: torch.Tensor = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    前向扩散过程：向干净图像添加噪声

    数学公式：
    x_t = sqrt(alpha_t) * x_0 + sqrt(1 - alpha_t) * epsilon

    其中：
    - alpha_t = prod(1 - beta_s) for s=1 to t
    - epsilon ~ N(0, I)
    """
    if noise is None:
        noise = torch.randn_like(x_0)

    # 获取时间步 t 对应的调度值
    sqrt_alpha = self.sqrt_alphas_cumprod[t].view(-1, 1, 1, 1)
    sqrt_one_minus_alpha = self.sqrt_one_minus_alphas_cumprod[t].view(-1, 1, 1, 1)

    # 前向过程：x_t = sqrt(alpha_t) * x_0 + sqrt(1 - alpha_t) * epsilon
    x_t = sqrt_alpha * x_0 + sqrt_one_minus_alpha * noise

    return x_t, noise
```

**实现要点**：
- 使用预计算的调度值，避免重复计算
- 支持自定义噪声输入（便于测试和调试）
- 使用 `.view(-1, 1, 1, 1)` 进行广播操作

## 3. UNet 实现

### 3.1 时间嵌入

```python
class SinusoidalPositionEmbeddings(nn.Module):
    """
    正弦位置编码

    类似于 Transformer 中的位置编码
    用于告诉模型当前的时间步

    数学公式：
    PE(t, 2i) = sin(t / 10000^(2i/d))
    PE(t, 2i+1) = cos(t / 10000^(2i/d))
    """

    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, time: torch.Tensor) -> torch.Tensor:
        device = time.device
        half_dim = self.dim // 2

        # 计算频率
        embeddings = math.log(10000) / (half_dim - 1)
        embeddings = torch.exp(torch.arange(half_dim, device=device) * -embeddings)

        # 计算正弦和余弦
        embeddings = time[:, None] * embeddings[None, :]
        embeddings = torch.cat((embeddings.sin(), embeddings.cos()), dim=-1)

        return embeddings
```

**实现要点**：
- 使用对数空间的频率，确保不同时间步有不同的编码
- 同时使用正弦和余弦函数，提供更丰富的信息
- 输出维度是输入维度的两倍

### 3.2 残差块

```python
class ResidualBlock(nn.Module):
    """
    残差块

    结构：
    x -> GroupNorm -> SiLU -> Conv -> + time_emb -> GroupNorm -> SiLU -> Dropout -> Conv -> + shortcut
    """

    def __init__(self, in_channels, out_channels, time_emb_dim, dropout=0.1):
        super().__init__()

        # 第一个卷积块
        self.norm1 = nn.GroupNorm(8, in_channels)
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)

        # 时间嵌入投影
        self.time_mlp = nn.Sequential(
            nn.SiLU(),
            nn.Linear(time_emb_dim, out_channels)
        )

        # 第二个卷积块
        self.norm2 = nn.GroupNorm(8, out_channels)
        self.dropout = nn.Dropout(dropout)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)

        # 跳跃连接（如果输入输出通道数不同）
        if in_channels != out_channels:
            self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1)
        else:
            self.shortcut = nn.Identity()

    def forward(self, x, time_emb):
        # 保存输入用于残差连接
        h = x

        # 第一个卷积块
        h = self.norm1(h)
        h = F.silu(h)
        h = self.conv1(h)

        # 添加时间嵌入
        time_emb = self.time_mlp(time_emb)
        h = h + time_emb[:, :, None, None]

        # 第二个卷积块
        h = self.norm2(h)
        h = F.silu(h)
        h = self.dropout(h)
        h = self.conv2(h)

        # 残差连接
        return h + self.shortcut(x)
```

**实现要点**：
- 使用 GroupNorm 而不是 BatchNorm，对批次大小不敏感
- 使用 SiLU（Swish）激活函数，梯度行为更好
- 时间嵌入通过广播机制添加到特征图
- 使用 Dropout 防止过拟合

### 3.3 注意力块

```python
class AttentionBlock(nn.Module):
    """
    自注意力块

    用于捕获长距离依赖关系
    通常在低分辨率特征图上使用（计算成本高）
    """

    def __init__(self, channels, num_heads=4):
        super().__init__()
        self.norm = nn.GroupNorm(8, channels)
        self.attention = nn.MultiheadAttention(
            embed_dim=channels,
            num_heads=num_heads,
            batch_first=True
        )

    def forward(self, x):
        B, C, H, W = x.shape

        # 归一化
        h = self.norm(x)

        # 重塑为序列格式 [B, C, H, W] -> [B, H*W, C]
        h = h.view(B, C, H * W).transpose(1, 2)

        # 自注意力
        h, _ = self.attention(h, h, h)

        # 重塑回原始格式 [B, H*W, C] -> [B, C, H, W]
        h = h.transpose(1, 2).view(B, C, H, W)

        # 残差连接
        return h + x
```

**实现要点**：
- 使用 PyTorch 内置的 MultiheadAttention，效率更高
- batch_first=True 简化维度处理
- 使用残差连接保持梯度流

### 3.4 完整 UNet

```python
class SimpleUNet(nn.Module):
    """
    简化版 UNet

    结构：
    - 3 层编码器（下采样）
    - 1 个瓶颈层
    - 3 层解码器（上采样）
    - 跳跃连接

    适用于 MNIST 等小图像（28x28 或 32x32）
    """

    def __init__(self, in_channels=1, out_channels=1, time_emb_dim=128):
        super().__init__()

        # 时间嵌入网络
        self.time_mlp = nn.Sequential(
            SinusoidalPositionEmbeddings(time_emb_dim),
            nn.Linear(time_emb_dim, time_emb_dim),
            nn.SiLU(),
            nn.Linear(time_emb_dim, time_emb_dim)
        )

        # 编码器
        self.enc1 = self._block(in_channels, 64)
        self.enc2 = self._block(64, 128)
        self.enc3 = self._block(128, 256)

        # 瓶颈层
        self.bottleneck = nn.Sequential(
            nn.Conv2d(256, 256, 3, padding=1),
            nn.GroupNorm(8, 256),
            nn.SiLU(),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.GroupNorm(8, 256),
            nn.SiLU()
        )

        # 时间嵌入投影
        self.time_proj = nn.Linear(time_emb_dim, 256)

        # 解码器
        self.dec3 = self._block(256 + 256, 128)
        self.dec2 = self._block(128 + 128, 64)
        self.dec1 = self._block(64 + 64, out_channels)

        # 下采样
        self.down = nn.MaxPool2d(2)

        # 上采样
        self.up3 = nn.ConvTranspose2d(256, 256, 2, stride=2)
        self.up2 = nn.ConvTranspose2d(128, 128, 2, stride=2)
        self.up1 = nn.ConvTranspose2d(64, 64, 2, stride=2)

    def _block(self, in_ch, out_ch):
        """创建卷积块"""
        return nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.GroupNorm(8, out_ch),
            nn.SiLU(),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.GroupNorm(8, out_ch),
            nn.SiLU()
        )

    def forward(self, x, t):
        # 时间嵌入
        t_emb = self.time_mlp(t)

        # 编码器
        e1 = self.enc1(x)
        e2 = self.enc2(self.down(e1))
        e3 = self.enc3(self.down(e2))

        # 瓶颈层 + 时间嵌入
        b = self.bottleneck(e3)
        t_proj = self.time_proj(t_emb)[:, :, None, None]
        b = b + t_proj

        # 解码器 + 跳跃连接
        d3 = self.up3(b)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        return d1
```

## 4. 扩散模型实现

### 4.1 训练损失计算

```python
def training_loss(self, x_0, noise=None):
    """
    计算训练损失

    数学公式：
    L = E_{t, x_0, epsilon} [||epsilon - epsilon_theta(x_t, t)||^2]

    步骤：
    1. 采样时间步 t
    2. 采样噪声 epsilon
    3. 前向扩散：x_t = sqrt(alpha_t) * x_0 + sqrt(1 - alpha_t) * epsilon
    4. 预测噪声：epsilon_pred = model(x_t, t)
    5. 计算损失：MSE(epsilon_pred, epsilon)
    """
    batch_size = x_0.shape[0]
    device = x_0.device

    # 采样随机时间步
    t = self.scheduler.sample_timestep(batch_size, device)

    # 采样噪声
    if noise is None:
        noise = torch.randn_like(x_0)

    # 前向扩散
    x_t, noise = self.scheduler.add_noise(x_0, t, noise)

    # 预测噪声
    noise_pred = self.model(x_t, t)

    # MSE 损失
    loss = F.mse_loss(noise_pred, noise)

    return loss
```

**实现要点**：
- 随机采样时间步，确保模型学习所有噪声水平
- 使用 MSE 损失，与理论推导一致
- 支持自定义噪声输入，便于调试

### 4.2 DDPM 采样

```python
@torch.no_grad()
def sample(self, batch_size, device, return_intermediates=False):
    """
    DDPM 采样算法

    数学公式：
    p_theta(x_{t-1} | x_t) = N(x_{t-1}; mu_theta(x_t, t), sigma_t^2)

    mu_theta = (1/sqrt(alpha_t)) * (x_t - (beta_t/sqrt(1 - alpha_t)) * epsilon_theta(x_t, t))

    步骤：
    1. 从 x_T ~ N(0, I) 开始
    2. 对于 t = T, T-1, ..., 1:
       - 预测噪声 epsilon_theta(x_t, t)
       - 计算均值 mu_theta
       - 采样 x_{t-1} = mu_theta + sigma_t * z (z ~ N(0, I))
    3. 返回 x_0
    """
    self.eval()

    # 从纯噪声开始
    x = torch.randn(batch_size, self.in_channels, self.image_size, self.image_size).to(device)

    intermediates = [x.clone()]

    # 反向扩散过程
    for t in tqdm(reversed(range(self.num_timesteps)), total=self.num_timesteps):
        t_batch = torch.full((batch_size,), t, device=device, dtype=torch.long)

        # 预测噪声
        noise_pred = self.model(x, t_batch)

        # 获取调度值
        alpha = self.scheduler.alphas[t]
        alpha_cumprod = self.scheduler.alphas_cumprod[t]
        beta = self.scheduler.betas[t]

        # 计算均值
        mean = self.scheduler.sqrt_recip_alphas[t] * (
            x - beta / self.scheduler.sqrt_one_minus_alphas_cumprod[t] * noise_pred
        )

        # 添加噪声（最后一步不加）
        if t > 0:
            noise = torch.randn_like(x)
            variance = torch.sqrt(self.scheduler.posterior_variance[t])
            x = mean + variance * noise
        else:
            x = mean

        # 存储中间结果
        if return_intermediates and t % (self.num_timesteps // 10) == 0:
            intermediates.append(x.clone())

    if return_intermediates:
        return x, intermediates

    return x
```

**实现要点**：
- 使用 `@torch.no_grad()` 节省内存
- 从纯噪声开始，逐步去噪
- 最后一步不添加噪声（确定性输出）
- 支持返回中间结果用于可视化

### 4.3 DDIM 采样

```python
@torch.no_grad()
def sample_ddim(self, batch_size, device, ddim_steps=50, eta=0.0):
    """
    DDIM 采样算法

    来自论文：Denoising Diffusion Implicit Models

    优点：
    - 可以使用更少的采样步数
    - 确定性采样（eta=0）
    - 可以进行语义插值

    数学公式：
    x_{t-1} = sqrt(alpha_{t-1}) * pred_x0 + sqrt(1 - alpha_{t-1} - sigma_t^2) * pred_dir + sigma_t * epsilon

    其中：
    - pred_x0 = (x_t - sqrt(1 - alpha_t) * epsilon_theta) / sqrt(alpha_t)
    - pred_dir = sqrt(1 - alpha_{t-1} - sigma_t^2) * epsilon_theta
    - sigma_t = eta * sqrt((1 - alpha_{t-1}) / (1 - alpha_t)) * sqrt(1 - alpha_t / alpha_{t-1})
    """
    self.eval()

    # 创建时间步序列
    step_size = self.num_timesteps // ddim_steps
    timesteps = list(range(0, self.num_timesteps, step_size))
    timesteps = list(reversed(timesteps))

    # 从纯噪声开始
    x = torch.randn(batch_size, self.in_channels, self.image_size, self.image_size).to(device)

    for i, t in enumerate(tqdm(timesteps)):
        t_batch = torch.full((batch_size,), t, device=device, dtype=torch.long)

        # 预测噪声
        noise_pred = self.model(x, t_batch)

        # 获取 alpha 值
        alpha_cumprod = self.scheduler.alphas_cumprod[t]
        alpha_cumprod_prev = self.scheduler.alphas_cumprod_prev[t] if t > 0 else torch.tensor(1.0)

        # 预测 x_0
        pred_x0 = (x - torch.sqrt(1 - alpha_cumprod) * noise_pred) / torch.sqrt(alpha_cumprod)
        pred_x0 = torch.clamp(pred_x0, -1, 1)

        # 计算方差
        sigma = eta * torch.sqrt((1 - alpha_cumprod_prev) / (1 - alpha_cumprod)) * torch.sqrt(1 - alpha_cumprod / alpha_cumprod_prev)

        # 计算方向
        pred_dir = torch.sqrt(1 - alpha_cumprod_prev - sigma ** 2) * noise_pred

        # 计算 x_{t-1}
        x = torch.sqrt(alpha_cumprod_prev) * pred_x0 + pred_dir

        # 添加随机性（eta > 0 时）
        if eta > 0 and i < len(timesteps) - 1:
            noise = torch.randn_like(x)
            x = x + sigma * noise

    return x
```

**实现要点**：
- 可以使用更少的时间步（如 50 步代替 1000 步）
- eta=0 时为确定性采样
- 使用 clamp 防止数值溢出

## 5. 训练器实现

### 5.1 训练循环

```python
def train_epoch(self, dataloader):
    """
    训练一个 epoch

    步骤：
    1. 遍历数据加载器
    2. 计算训练损失
    3. 反向传播
    4. 梯度裁剪
    5. 更新参数
    """
    self.model.train()
    total_loss = 0.0
    num_batches = 0

    for batch in tqdm(dataloader):
        # 获取图像
        if isinstance(batch, (list, tuple)):
            images = batch[0]
        else:
            images = batch

        images = images.to(self.device)

        # 归一化到 [-1, 1]
        if images.min() >= 0 and images.max() <= 1:
            images = images * 2 - 1

        # 前向传播
        loss = self.model.training_loss(images)

        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()

        # 梯度裁剪
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

        # 更新参数
        self.optimizer.step()

        total_loss += loss.item()
        num_batches += 1

    return total_loss / num_batches
```

**实现要点**：
- 自动处理不同格式的数据（tensor 或 tuple）
- 自动归一化到 [-1, 1] 范围
- 使用梯度裁剪防止梯度爆炸

### 5.2 检查点管理

```python
def save_checkpoint(self, path):
    """保存检查点"""
    torch.save({
        'model_state_dict': self.model.state_dict(),
        'optimizer_state_dict': self.optimizer.state_dict(),
        'losses': self.losses
    }, path)

def load_checkpoint(self, path):
    """加载检查点"""
    checkpoint = torch.load(path, map_location=self.device)
    self.model.load_state_dict(checkpoint['model_state_dict'])
    self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    self.losses = checkpoint['losses']
```

**实现要点**：
- 保存模型和优化器状态
- 保存训练历史
- 使用 map_location 确保跨设备兼容性

## 6. 工具函数实现

### 6.1 图像保存

```python
def save_images(images, path, nrow=8):
    """保存图像网格"""
    from torchvision.utils import make_grid

    # 创建图像网格
    grid = make_grid(images, nrow=nrow, normalize=True, value_range=(-1, 1))
    grid = grid.permute(1, 2, 0).cpu().numpy()

    # 保存图像
    plt.figure(figsize=(10, 10))
    plt.imshow(grid)
    plt.axis('off')
    plt.savefig(path, bbox_inches='tight', dpi=150)
    plt.close()
```

### 6.2 可视化扩散过程

```python
def visualize_diffusion_process(images, timesteps, save_path=None):
    """可视化前向扩散过程"""
    fig, axes = plt.subplots(1, len(images), figsize=(3 * len(images), 3))

    for ax, img, t in zip(axes, images, timesteps):
        # 反归一化
        img = (img + 1) / 2
        img = img.permute(1, 2, 0).cpu().numpy()
        img = np.clip(img, 0, 1)

        ax.imshow(img, cmap='gray')
        ax.set_title(f't={t}')
        ax.axis('off')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.show()
```

## 7. 实现技巧总结

### 7.1 数值稳定性

1. **使用 GroupNorm 而不是 BatchNorm**：
   - 对批次大小不敏感
   - 训练更稳定

2. **梯度裁剪**：
   ```python
   torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
   ```

3. **使用 clamp 防止数值溢出**：
   ```python
   pred_x0 = torch.clamp(pred_x0, -1, 1)
   ```

### 7.2 计算效率

1. **预计算调度值**：
   - 避免重复计算
   - 加速训练和采样

2. **使用 @torch.no_grad()**：
   - 节省内存
   - 加速采样

3. **使用 torch.compile()**（PyTorch 2.0+）：
   - 自动优化计算图
   - 提高运行速度

### 7.3 代码组织

1. **模块化设计**：
   - 每个组件职责清晰
   - 便于测试和维护

2. **类型提示**：
   - 提高代码可读性
   - 便于 IDE 支持

3. **文档字符串**：
   - 详细说明功能
   - 包含数学公式

## 8. 常见问题和解决方案

### 8.1 训练不稳定

**问题**：损失震荡或不收敛

**解决方案**：
- 降低学习率
- 使用梯度裁剪
- 检查数据归一化

### 8.2 生成质量差

**问题**：生成图像模糊或有噪声

**解决方案**：
- 增加训练时间
- 使用更大的模型
- 尝试不同的噪声调度

### 8.3 内存不足

**问题**：GPU 内存不足

**解决方案**：
- 减小批次大小
- 使用梯度累积
- 使用混合精度训练

### 8.4 采样速度慢

**问题**：生成图像耗时过长

**解决方案**：
- 使用 DDIM 采样
- 减少采样步数
- 使用更快的采样方法
