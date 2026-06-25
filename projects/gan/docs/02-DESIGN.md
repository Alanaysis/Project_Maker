# 02-DESIGN.md - GAN 设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      GAN Framework                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐         ┌──────────────┐              │
│  │  Generator   │ ──────→ │ Discriminator│              │
│  │    (G)       │         │    (D)       │              │
│  └──────────────┘         └──────────────┘              │
│         ↑                         │                     │
│         │                         ↓                     │
│    Random Noise z           Real/Fake Score              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
gan/
├── src/
│   ├── __init__.py         # 包初始化
│   ├── generator.py        # 生成器模块
│   ├── discriminator.py    # 判别器模块
│   ├── gan.py              # GAN 框架
│   └── trainer.py          # 训练器模块
├── tests/
│   └── test_gan.py         # 测试套件
└── examples/
    ├── train_mnist.py      # MNIST 训练示例
    └── simple_example.py   # 简单示例
```

## 2. 类设计

### 2.1 Generator 类

**职责**：
- 将随机噪声映射到图像空间
- 学习数据分布
- 生成逼真的图像

**接口设计**：
```python
class Generator(nn.Module):
    def __init__(self, latent_dim, img_channels, img_size, hidden_dims):
        """初始化生成器"""
        
    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        
    def sample_noise(self, batch_size, device) -> torch.Tensor:
        """生成随机噪声"""
        
    def generate(self, batch_size, device) -> torch.Tensor:
        """生成图像"""
```

**属性**：
- `latent_dim`: 噪声向量维度
- `img_channels`: 输出图像通道数
- `img_size`: 输出图像尺寸
- `network`: 神经网络层

### 2.2 Discriminator 类

**职责**：
- 区分真实图像和生成图像
- 输出图像为真实的概率
- 提取图像特征

**接口设计**：
```python
class Discriminator(nn.Module):
    def __init__(self, img_channels, img_size, hidden_dims):
        """初始化判别器"""
        
    def forward(self, img: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        
    def predict(self, img: torch.Tensor) -> torch.Tensor:
        """预测图像是否为真实"""
        
    def get_features(self, img: torch.Tensor) -> torch.Tensor:
        """提取图像特征"""
```

**属性**：
- `img_channels`: 输入图像通道数
- `img_size`: 输入图像尺寸
- `network`: 卷积特征提取层
- `classifier`: 分类层

### 2.3 GAN 类

**职责**：
- 整合生成器和判别器
- 提供训练接口
- 管理优化器和损失函数

**接口设计**：
```python
class GAN(nn.Module):
    def __init__(self, latent_dim, img_channels, img_size, lr, beta1, beta2):
        """初始化 GAN"""
        
    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """前向传播 (仅生成器)"""
        
    def train_discriminator(self, real_images, batch_size) -> Dict:
        """训练判别器"""
        
    def train_generator(self, batch_size, device) -> Dict:
        """训练生成器"""
        
    def train_step(self, real_images) -> Dict:
        """执行一步训练"""
        
    def generate_samples(self, n_samples, device) -> torch.Tensor:
        """生成样本"""
        
    def get_training_stats(self) -> Dict:
        """获取训练统计"""
```

**属性**：
- `generator`: 生成器实例
- `discriminator`: 判别器实例
- `adversarial_loss`: 对抗损失函数
- `optimizer_G`: 生成器优化器
- `optimizer_D`: 判别器优化器
- `training_stats`: 训练统计

### 2.4 GANTrainer 类

**职责**：
- 执行完整训练循环
- 应用训练技巧
- 管理检查点和日志

**接口设计**：
```python
class GANTrainer:
    def __init__(self, gan, device, label_smoothing, noisy_labels, n_critic):
        """初始化训练器"""
        
    def train_epoch(self, dataloader, epoch) -> Dict:
        """训练一个 epoch"""
        
    def train(self, dataloader, n_epochs, ...) -> Dict:
        """执行完整训练"""
        
    def save_checkpoint(self, save_dir, epoch):
        """保存模型检查点"""
        
    def load_checkpoint(self, checkpoint_path):
        """加载模型检查点"""
```

**属性**：
- `gan`: GAN 模型实例
- `device`: 训练设备
- `label_smoothing`: 标签平滑系数
- `noisy_labels`: 是否使用噪声标签
- `n_critic`: 判别器训练次数比率
- `history`: 训练历史

## 3. 数据流设计

### 3.1 训练数据流

```
输入: 真实图像 x (batch_size, 1, 28, 28)
    ↓
┌─────────────────────────────────────┐
│         训练判别器 (D)              │
├─────────────────────────────────────┤
│ 1. 真实图像 → D → D(x)             │
│ 2. 噪声 z → G → G(z) → D → D(G(z))│
│ 3. 计算损失: -[log D(x) + log(1-D(G(z)))] │
│ 4. 反向传播，更新 D 参数           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│         训练生成器 (G)              │
├─────────────────────────────────────┤
│ 1. 噪声 z → G → G(z) → D → D(G(z))│
│ 2. 计算损失: -log D(G(z))          │
│ 3. 反向传播，更新 G 参数           │
└─────────────────────────────────────┘
    ↓
输出: 训练统计 (d_loss, g_loss, ...)
```

### 3.2 生成数据流

```
输入: 随机噪声 z (n_samples, 100)
    ↓
生成器 G
    ↓
输出: 生成图像 (n_samples, 1, 28, 28)
```

## 4. 网络架构设计

### 4.1 生成器架构

```
输入层: Linear(100, 256*7*7)
    ↓
Reshape: (256, 7, 7)
    ↓
隐藏层 1: ConvTranspose2d(256, 128, 4, 2, 1)
         BatchNorm2d(128)
         ReLU
    ↓
隐藏层 2: ConvTranspose2d(128, 64, 4, 2, 1)
         BatchNorm2d(64)
         ReLU
    ↓
输出层: ConvTranspose2d(64, 1, 4, 2, 1)
        Tanh
    ↓
输出: (1, 28, 28)
```

**设计决策**：
- 使用 ConvTranspose2d 进行上采样
- 使用 BatchNorm 稳定训练
- 使用 ReLU 激活函数
- 输出层使用 Tanh (输出范围 [-1, 1])

### 4.2 判别器架构

```
输入层: Conv2d(1, 64, 4, 2, 1)
        LeakyReLU(0.2)
        Dropout2d(0.25)
    ↓
隐藏层 1: Conv2d(64, 128, 4, 2, 1)
         LeakyReLU(0.2)
         Dropout2d(0.25)
    ↓
隐藏层 2: Conv2d(128, 256, 4, 2, 1)
         LeakyReLU(0.2)
         Dropout2d(0.25)
    ↓
分类层: Linear(256*3*3, 1)
        Sigmoid
    ↓
输出: (1,)
```

**设计决策**：
- 使用 Conv2d 进行下采样
- 使用 LeakyReLU 防止梯度消失
- 使用 Dropout 防止过拟合
- 输出层使用 Sigmoid (输出概率)

## 5. 损失函数设计

### 5.1 对抗损失

使用二元交叉熵损失 (BCE Loss)：

```python
criterion = nn.BCELoss()

# 判别器损失
d_loss = criterion(D(real_images), real_labels) + 
         criterion(D(G(z)), fake_labels)

# 生成器损失
g_loss = criterion(D(G(z)), real_labels)
```

**设计决策**：
- 使用 BCE Loss 而不是原始的 log 损失
- 生成器使用非饱和损失 (real_labels 而不是 fake_labels)

### 5.2 标签设计

**真实标签**：
```python
real_labels = torch.ones(batch_size, 1)  # 全 1
```

**生成标签**：
```python
fake_labels = torch.zeros(batch_size, 1)  # 全 0
```

**标签平滑**：
```python
real_labels = torch.ones(batch_size, 1) * 0.9  # 0.9 而不是 1.0
fake_labels = torch.zeros(batch_size, 1) + 0.1  # 0.1 而不是 0.0
```

## 6. 优化器设计

### 6.1 Adam 优化器

```python
optimizer_G = Adam(generator.parameters(), lr=0.0002, betas=(0.5, 0.999))
optimizer_D = Adam(discriminator.parameters(), lr=0.0002, betas=(0.5, 0.999))
```

**参数选择**：
- lr = 0.0002: 推荐学习率
- beta1 = 0.5: 一阶矩衰减率
- beta2 = 0.999: 二阶矩衰减率

**设计决策**：
- 为生成器和判别器使用独立的优化器
- 使用 Adam 而不是 SGD (自适应学习率)

## 7. 训练策略设计

### 7.1 训练比例

```python
n_critic = 1  # 判别器训练次数与生成器训练次数的比率
```

**设计决策**：
- 默认 1:1 训练
- 可以调整为 2:1 或 5:1

### 7.2 训练循环

```python
for epoch in range(n_epochs):
    for batch in dataloader:
        # 训练判别器
        for _ in range(n_critic):
            train_discriminator(batch)
        
        # 训练生成器
        train_generator()
```

### 7.3 早停策略

基于生成器损失的早停：

```python
if g_loss < best_g_loss:
    best_g_loss = g_loss
    save_best_model()
```

## 8. 评估设计

### 8.1 训练指标

**判别器指标**：
- `d_loss`: 判别器损失
- `d_real_acc`: 判别器对真实图像的准确率
- `d_fake_acc`: 判别器对生成图像的准确率

**生成器指标**：
- `g_loss`: 生成器损失

### 8.2 生成质量评估

**可视化评估**：
- 生成图像的视觉质量
- 多样性
- 真实性

**定量评估**：
- FID (Fréchet Inception Distance)
- IS (Inception Score)

## 9. 部署设计

### 9.1 模型保存

```python
checkpoint = {
    "generator_state_dict": generator.state_dict(),
    "discriminator_state_dict": discriminator.state_dict(),
    "optimizer_G_state_dict": optimizer_G.state_dict(),
    "optimizer_D_state_dict": optimizer_D.state_dict(),
    "history": training_history
}
torch.save(checkpoint, "checkpoint.pt")
```

### 9.2 模型加载

```python
checkpoint = torch.load("checkpoint.pt")
generator.load_state_dict(checkpoint["generator_state_dict"])
discriminator.load_state_dict(checkpoint["discriminator_state_dict"])
```

### 9.3 推理部署

```python
# 加载生成器
generator = Generator(latent_dim=100, img_channels=1, img_size=28)
generator.load_state_dict(checkpoint["generator_state_dict"])
generator.eval()

# 生成图像
z = torch.randn(16, 100)
images = generator(z)
```

## 10. 扩展性设计

### 10.1 支持不同图像尺寸

```python
# 28x28 图像
gan_28 = GAN(img_size=28)

# 64x64 图像
gan_64 = GAN(img_size=64)
```

### 10.2 支持不同通道数

```python
# 灰度图像
gan_gray = GAN(img_channels=1)

# RGB 图像
gan_rgb = GAN(img_channels=3)
```

### 10.3 支持不同架构

```python
# 自定义隐藏层维度
generator = Generator(hidden_dims=[512, 1024, 2048])
discriminator = Discriminator(hidden_dims=[256, 512, 1024])
```

## 11. 测试设计

### 11.1 单元测试

- 测试生成器前向传播
- 测试判别器前向传播
- 测试 GAN 训练步骤
- 测试梯度流动

### 11.2 集成测试

- 测试完整训练循环
- 测试模型保存/加载
- 测试设备转移

### 11.3 性能测试

- 测试训练速度
- 测试内存占用
- 测试生成速度

## 12. 总结

### 12.1 设计原则

1. **模块化**: 清晰的模块划分
2. **可扩展**: 支持不同的配置
3. **易用性**: 简洁的 API 设计
4. **稳定性**: 包含训练技巧

### 12.2 设计优势

1. **清晰的接口**: 每个类都有明确的职责
2. **灵活的配置**: 支持多种超参数
3. **完整的训练流程**: 包含训练、评估、保存
4. **易于扩展**: 可以轻松添加新功能

### 12.3 设计限制

1. **固定架构**: 网络结构相对固定
2. **单 GPU**: 不支持分布式训练
3. **基本功能**: 不包含高级功能 (如 WGAN)
