# 学习笔记 - Diffusion Model

## 项目概述

**项目名称**：Diffusion Model - DDPM 实现

**学习目标**：
- 理解扩散模型原理
- 掌握前向扩散和反向去噪
- 学会 DDPM 训练

**技术栈**：Python + PyTorch

**完成日期**：2024 年

---

## 核心概念学习

### 1. 什么是扩散模型？

扩散模型是一类生成模型，其核心思想是：
1. **前向过程**：逐步向数据添加噪声，直到变成纯噪声
2. **反向过程**：学习从噪声中逐步恢复数据的过程

```
干净图像 → 添加噪声 → 添加噪声 → ... → 纯噪声
   x_0   →    x_1   →    x_2   → ... →   x_T

纯噪声 → 去除噪声 → 去除噪声 → ... → 生成图像
  x_T  →   x_{T-1} →  x_{T-2} → ... →   x_0
```

### 2. 数学原理

#### 2.1 前向过程

前向过程是一个马尔可夫链，每一步添加少量高斯噪声：

```
q(x_t | x_{t-1}) = N(x_t; √(1-β_t) * x_{t-1}, β_t * I)
```

其中 β_t 是噪声调度，控制每一步添加多少噪声。

**重要性质**：可以直接从 x_0 采样任意时间步的 x_t：

```
q(x_t | x_0) = N(x_t; √(ᾱ_t) * x_0, (1-ᾱ_t) * I)
```

其中 ᾱ_t = ∏(1-β_s) for s=1 to t

#### 2.2 反向过程

反向过程也是马尔可夫链，每一步去除少量噪声：

```
p_θ(x_{t-1} | x_t) = N(x_{t-1}; μ_θ(x_t, t), Σ_θ(x_t, t))
```

其中 μ_θ 和 Σ_θ 是神经网络预测的参数。

#### 2.3 训练目标

训练目标是预测添加的噪声：

```
L = E_{t, x_0, ε} [||ε - ε_θ(√(ᾱ_t) * x_0 + √(1-ᾱ_t) * ε, t)||²]
```

其中 ε 是实际添加的噪声，ε_θ 是模型预测的噪声。

### 3. 关键组件

#### 3.1 噪声调度器

噪声调度器控制前向扩散过程：

```python
class NoiseScheduler:
    def __init__(self, num_timesteps, beta_start, beta_end):
        self.betas = torch.linspace(beta_start, beta_end, num_timesteps)
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)

    def add_noise(self, x_0, t, noise):
        sqrt_alpha = self.sqrt_alphas_cumprod[t]
        sqrt_one_minus_alpha = self.sqrt_one_minus_alphas_cumprod[t]
        return sqrt_alpha * x_0 + sqrt_one_minus_alpha * noise
```

**学习心得**：
- β_t 从 0.0001 线性增加到 0.02
- ᾱ_t 从接近 1 单调递减到接近 0
- 预计算所有参数，避免重复计算

#### 3.2 UNet

UNet 用于预测添加的噪声：

```python
class UNet(nn.Module):
    def __init__(self, in_channels, out_channels):
        # 编码器（下采样）
        self.enc1 = Block(in_channels, 64)
        self.enc2 = Block(64, 128)
        self.enc3 = Block(128, 256)

        # 解码器（上采样）
        self.dec3 = Block(256 + 256, 128)  # 跳跃连接
        self.dec2 = Block(128 + 128, 64)
        self.dec1 = Block(64 + 64, out_channels)

    def forward(self, x, t):
        # 时间嵌入
        t_emb = sinusoidal_embedding(t)

        # 编码
        e1 = self.enc1(x)
        e2 = self.enc2(downsample(e1))
        e3 = self.enc3(downsample(e2))

        # 解码 + 跳跃连接
        d3 = self.dec3(cat(upsample(b), e3))
        d2 = self.dec2(cat(upsample(d3), e2))
        d1 = self.dec1(cat(upsample(d2), e1))

        return d1
```

**学习心得**：
- 跳跃连接保留细节信息
- 时间嵌入告诉模型当前噪声水平
- 使用 GroupNorm 而不是 BatchNorm

#### 3.3 时间嵌入

时间嵌入类似于 Transformer 的位置编码：

```python
def sinusoidal_embedding(t, dim):
    half_dim = dim // 2
    emb = math.log(10000) / (half_dim - 1)
    emb = torch.exp(torch.arange(half_dim) * -emb)
    emb = t[:, None] * emb[None, :]
    return torch.cat([emb.sin(), emb.cos()], dim=-1)
```

**学习心得**：
- 不同时间步有不同的编码
- 使用正弦和余弦函数
- 帮助模型区分不同噪声水平

### 4. 训练过程

#### 4.1 训练循环

```python
for epoch in range(num_epochs):
    for batch in dataloader:
        x_0 = batch

        # 采样时间步
        t = torch.randint(0, T, (batch_size,))

        # 采样噪声
        noise = torch.randn_like(x_0)

        # 前向扩散
        x_t = scheduler.add_noise(x_0, t, noise)

        # 预测噪声
        noise_pred = model(x_t, t)

        # 计算损失
        loss = F.mse_loss(noise_pred, noise)

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

**学习心得**：
- 随机采样时间步，学习所有噪声水平
- MSE 损失与理论推导一致
- 梯度裁剪防止梯度爆炸

#### 4.2 训练技巧

1. **数据归一化**：将图像归一化到 [-1, 1]
2. **梯度裁剪**：`torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)`
3. **学习率**：通常使用 2e-4 到 1e-4
4. **批次大小**：128 或更大

### 5. 采样过程

#### 5.1 DDPM 采样

```python
def sample(model, batch_size):
    # 从纯噪声开始
    x = torch.randn(batch_size, 1, 28, 28)

    # 反向扩散
    for t in reversed(range(T)):
        noise_pred = model(x, t)

        # 计算均值
        mean = (1/√α_t) * (x - (β_t/√(1-ᾱ_t)) * noise_pred)

        # 添加噪声（最后一步不加）
        if t > 0:
            noise = torch.randn_like(x)
            x = mean + √(posterior_variance) * noise
        else:
            x = mean

    return x
```

**学习心得**：
- 从纯噪声开始
- 逐步去除噪声
- 最后一步确定性输出

#### 5.2 DDIM 采样

DDIM 允许使用更少的采样步数：

```python
def sample_ddim(model, batch_size, ddim_steps=50):
    x = torch.randn(batch_size, 1, 28, 28)

    # 选择时间步子序列
    timesteps = list(range(0, T, T // ddim_steps))
    timesteps = list(reversed(timesteps))

    for t in timesteps:
        noise_pred = model(x, t)

        # 预测 x_0
        pred_x0 = (x - √(1-ᾱ_t) * noise_pred) / √(ᾱ_t)

        # 计算 x_{t-1}
        x = √(ᾱ_{t-1}) * pred_x0 + √(1-ᾱ_{t-1}) * noise_pred

    return x
```

**学习心得**：
- 可以使用 50 步代替 1000 步
- 采样速度快 20 倍
- 确定性采样（eta=0）

---

## 实现细节学习

### 1. 模块化设计

项目采用模块化设计：

```
src/
├── scheduler.py    # 噪声调度
├── unet.py        # UNet 网络
├── diffusion.py   # 核心逻辑
└── utils.py       # 工具函数
```

**学习心得**：
- 每个模块职责清晰
- 便于测试和维护
- 易于扩展和修改

### 2. 类型提示

使用类型提示提高代码可读性：

```python
def add_noise(
    self,
    x_0: torch.Tensor,
    t: torch.Tensor,
    noise: Optional[torch.Tensor] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """添加噪声到图像"""
    pass
```

**学习心得**：
- 提高代码可读性
- 便于 IDE 支持
- 减少运行时错误

### 3. 文档字符串

详细的文档字符串：

```python
def training_loss(self, x_0):
    """
    计算训练损失

    数学公式：
    L = E_{t, x_0, ε} [||ε - ε_θ(√(ᾱ_t) * x_0 + √(1-ᾱ_t) * ε, t)||²]

    Args:
        x_0: 干净图像 [B, C, H, W]

    Returns:
        MSE 损失
    """
    pass
```

**学习心得**：
- 包含数学公式
- 说明参数和返回值
- 便于理解和使用

### 4. 测试驱动开发

先写测试，再写实现：

```python
def test_add_noise():
    """测试前向扩散过程"""
    scheduler = NoiseScheduler(num_timesteps=100)

    x_0 = torch.randn(4, 1, 28, 28)
    t = torch.randint(0, 100, (4,))

    x_t, noise = scheduler.add_noise(x_0, t)

    # 验证形状
    assert x_t.shape == x_0.shape
    assert noise.shape == x_0.shape

    # 验证噪声被添加
    assert not torch.allclose(x_t, x_0)
```

**学习心得**：
- 确保代码正确性
- 便于重构
- 作为文档使用

---

## 调试经验

### 1. 常见问题

**问题 1：损失不下降**

原因：
- 学习率太大或太小
- 数据未正确归一化
- 梯度爆炸或消失

解决：
```python
# 检查数据范围
print(f"Data range: [{images.min():.3f}, {images.max():.3f}]")

# 检查梯度
for name, param in model.named_parameters():
    if param.grad is not None:
        print(f"{name}: grad_norm = {param.grad.norm():.6f}")

# 使用梯度裁剪
torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
```

**问题 2：生成质量差**

原因：
- 训练时间不足
- 模型容量不够
- 噪声调度不合适

解决：
```python
# 增加训练时间
num_epochs = 100

# 使用更大的模型
hidden_channels = [128, 256, 512]

# 尝试余弦调度
schedule_type = "cosine"
```

**问题 3：内存不足**

原因：
- 批次太大
- 模型太大
- 图像太大

解决：
```python
# 减小批次大小
batch_size = 16

# 使用梯度累积
accumulation_steps = 4

# 使用混合精度训练
from torch.cuda.amp import autocast
```

### 2. 调试技巧

**打印中间结果**：

```python
def training_loss(self, x_0):
    t = self.scheduler.sample_timestep(batch_size, device)
    noise = torch.randn_like(x_0)
    x_t, noise = self.scheduler.add_noise(x_0, t, noise)
    noise_pred = self.model(x_t, t)

    # 调试打印
    print(f"t: {t}")
    print(f"x_0 range: [{x_0.min():.3f}, {x_0.max():.3f}]")
    print(f"x_t range: [{x_t.min():.3f}, {x_t.max():.3f}]")
    print(f"noise_pred range: [{noise_pred.min():.3f}, {noise_pred.max():.3f}]")

    loss = F.mse_loss(noise_pred, noise)
    return loss
```

**可视化训练过程**：

```python
# 生成样本
samples = model.sample(batch_size=16)

# 保存图像
save_images(samples, "samples.png")
```

---

## 性能优化

### 1. 计算优化

**预计算调度值**：

```python
# 不好：每次计算
alpha = torch.prod(1 - betas[:t])

# 好：预计算
alphas_cumprod = torch.cumprod(1 - betas, dim=0)
alpha = alphas_cumprod[t]
```

**使用 @torch.no_grad()**：

```python
@torch.no_grad()
def sample(self, batch_size):
    # 采样时不需要梯度
    pass
```

### 2. 内存优化

**梯度检查点**：

```python
from torch.utils.checkpoint import checkpoint

def forward(self, x, t):
    # 使用梯度检查点节省内存
    h = checkpoint(self.enc1, x)
    h = checkpoint(self.enc2, h)
    return h
```

**混合精度训练**：

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

for batch in dataloader:
    with autocast():
        loss = model.training_loss(batch)

    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
```

### 3. 采样优化

**DDIM 采样**：

```python
# DDPM：1000 步
samples = model.sample(batch_size=16)

# DDIM：50 步（快 20 倍）
samples = model.sample_ddim(batch_size=16, ddim_steps=50)
```

---

## 学习资源

### 1. 核心论文

1. **DDPM**：https://arxiv.org/abs/2006.11239
   - 原始论文，必读
   - 详细推导前向和反向过程

2. **DDIM**：https://arxiv.org/abs/2010.02502
   - 加速采样方法
   - 确定性采样

3. **Improved DDPM**：https://arxiv.org/abs/2102.09672
   - 余弦噪声调度
   - 学习方差

### 2. 教程和博客

1. **Lilian Weng's Blog**：https://lilianweng.github.io/posts/2021-07-11-diffusion-models/
   - 优秀的技术博客
   - 详细的数学推导

2. **Hugging Face Diffusion Course**：https://huggingface.co/learn/diffusion-course
   - 交互式教程
   - 代码示例

3. **The Annotated Diffusion Model**：https://huggingface.co/blog/annotated-diffusion
   - 代码注释版
   - 便于理解实现

### 3. 开源实现

1. **lucidrains/denoising-diffusion-pytorch**：https://github.com/lucidrains/denoising-diffusion-pytorch
   - 流行实现
   - 代码清晰

2. **hojonathanho/diffusion**：https://github.com/hojonathanho/diffusion
   - 原始实现
   - 参考价值高

---

## 项目总结

### 1. 完成的功能

- [x] 噪声调度器（线性 + 余弦）
- [x] UNet 网络（简化版 + 完整版）
- [x] 扩散模型核心（DDPM + DDIM）
- [x] 训练器（训练循环 + 检查点）
- [x] 工具函数（可视化 + 评估）
- [x] 示例代码（训练 + 生成）
- [x] 测试用例（单元测试 + 集成测试）
- [x] 项目文档（README + 技术文档）

### 2. 学到的知识

**技术知识**：
- 扩散模型的数学原理
- UNet 架构设计
- 噪声调度策略
- 训练和采样算法

**工程知识**：
- 模块化设计
- 类型提示和文档
- 测试驱动开发
- 性能优化技巧

**调试经验**：
- 常见问题诊断
- 调试工具使用
- 性能分析方法

### 3. 未来改进

**技术改进**：
- 实现条件生成
- 支持更高分辨率
- 尝试更多采样方法
- 添加评估指标

**工程改进**：
- 添加 TensorBoard 支持
- 实现分布式训练
- 优化内存使用
- 添加更多示例

**文档改进**：
- 添加更多教程
- 完善 API 文档
- 添加视频讲解
- 翻译成英文

---

## 核心收获

### 1. 理论理解

**扩散模型的本质**：
- 学习数据分布的"去噪"过程
- 通过逐步添加噪声，将复杂分布转化为简单分布
- 通过学习去噪，从简单分布采样并恢复复杂分布

**与 GAN 的对比**：
- GAN：训练不稳定，容易模式崩溃
- 扩散模型：训练稳定，生成质量高
- 扩散模型：采样速度慢，需要加速方法

### 2. 实践经验

**PyTorch 编程**：
- 模块化设计（nn.Module）
- 自动微分（autograd）
- GPU 加速（device）
- 数据加载（DataLoader）

**深度学习工程**：
- 数据预处理
- 模型设计
- 训练策略
- 评估方法

### 3. 学习方法

**论文阅读**：
- 先读摘要和结论
- 理解核心思想
- 推导数学公式
- 实现代码验证

**代码实现**：
- 先实现最小版本
- 逐步添加功能
- 测试每个组件
- 优化性能

**调试技巧**：
- 打印中间结果
- 可视化训练过程
- 对比参考实现
- 查阅文档和论文

---

## 致谢

感谢以下资源的帮助：

1. **DDPM 论文作者**：Jonathan Ho 等人
2. **开源社区**：各种实现和教程
3. **PyTorch 团队**：优秀的深度学习框架
4. **学习社区**：讨论和交流

---

## 附录：常用命令

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

# 使用 DDIM 加速采样
python examples/generate_samples.py \
    --checkpoint ./checkpoints/best_model.pt \
    --use-ddim \
    --ddim-steps 50
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

### 代码格式化

```bash
# 格式化代码
black src/ tests/ examples/

# 检查代码风格
flake8 src/ tests/ examples/
```
