# 超分辨率设计文档

## 1. 系统架构

### 1.1 整体架构

```
super-resolution/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── models.py          # 模型实现
│   ├── dataset.py         # 数据集
│   ├── trainer.py         # 训练器
│   ├── evaluator.py       # 评估器
│   └── utils.py           # 工具函数
├── tests/                  # 测试代码
├── docs/                   # 文档
├── examples/               # 示例
├── train.py                # 训练脚本
├── evaluate.py             # 评估脚本
└── requirements.txt        # 依赖包
```

### 1.2 模块划分

**核心模块**：
- `models.py`：模型定义
- `dataset.py`：数据处理
- `trainer.py`：训练逻辑
- `evaluator.py`：评估逻辑

**工具模块**：
- `utils.py`：通用工具函数

**脚本模块**：
- `train.py`：训练入口
- `evaluate.py`：评估入口
- `demo.py`：演示入口

## 2. 模型设计

### 2.1 SRCNN

**架构图**：
```
输入(低分辨率) → 插值上采样 → Conv1(9x9, 64) → ReLU → Conv2(1x1, 32) → ReLU → Conv3(5x5, 3) → 输出(高分辨率)
```

**类设计**：
```python
class SRCNN(nn.Module):
    def __init__(self, num_channels=3, num_features=64, hidden_features=32):
        super().__init__()
        self.feature_extraction = nn.Sequential(
            nn.Conv2d(num_channels, num_features, kernel_size=9, padding=4),
            nn.ReLU(inplace=True)
        )
        self.non_linear_mapping = nn.Sequential(
            nn.Conv2d(num_features, hidden_features, kernel_size=1),
            nn.ReLU(inplace=True)
        )
        self.reconstruction = nn.Conv2d(hidden_features, num_channels, kernel_size=5, padding=2)

    def forward(self, x):
        features = self.feature_extraction(x)
        mapped = self.non_linear_mapping(features)
        output = self.reconstruction(mapped)
        return output
```

**设计考虑**：
- 使用 9x9 大卷积核提取特征
- 使用 1x1 卷积进行特征映射
- 使用 5x5 卷积重建图像
- 先插值上采样再处理

### 2.2 ESPCN

**架构图**：
```
输入(低分辨率) → Conv1(5x5, 64) → Tanh → Conv2(3x3, 64) → Tanh → Conv3(3x3, C*r^2) → PixelShuffle → 输出(高分辨率)
```

**类设计**：
```python
class ESPCN(nn.Module):
    def __init__(self, scale_factor=2, num_channels=3, num_features=64):
        super().__init__()
        self.scale_factor = scale_factor
        self.feature_extraction = nn.Sequential(
            nn.Conv2d(num_channels, num_features, kernel_size=5, padding=2),
            nn.Tanh()
        )
        self.feature_mapping = nn.Sequential(
            nn.Conv2d(num_features, num_features, kernel_size=3, padding=1),
            nn.Tanh()
        )
        self.sub_pixel = nn.Conv2d(
            num_features,
            num_channels * scale_factor * scale_factor,
            kernel_size=3,
            padding=1
        )
        self.pixel_shuffle = nn.PixelShuffle(scale_factor)

    def forward(self, x):
        features = self.feature_extraction(x)
        mapped = self.feature_mapping(features)
        sub_pixel_features = self.sub_pixel(mapped)
        output = self.pixel_shuffle(sub_pixel_features)
        return output
```

**设计考虑**：
- 在低分辨率空间提取特征（计算效率高）
- 使用 Tanh 激活函数
- 使用 Pixel Shuffle 进行上采样
- 参数量少

### 2.3 EDSR

**架构图**：
```
输入 → Conv(浅层特征) → [残差块] x N → Conv → PixelShuffle → Conv → 输出
```

**类设计**：
```python
class ResidualBlock(nn.Module):
    def __init__(self, num_features):
        super().__init__()
        self.conv1 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(num_features, num_features, kernel_size=3, padding=1)

    def forward(self, x):
        residual = x
        out = self.relu(self.conv1(x))
        out = self.conv2(out)
        out = out + residual
        return out

class EDSR(nn.Module):
    def __init__(self, scale_factor=2, num_channels=3, num_features=64, num_blocks=16):
        super().__init__()
        self.shallow_feature = nn.Conv2d(num_channels, num_features, kernel_size=3, padding=1)
        self.deep_feature = nn.Sequential(*[ResidualBlock(num_features) for _ in range(num_blocks)])
        self.upsample = nn.Sequential(
            nn.Conv2d(num_features, num_features * scale_factor * scale_factor, kernel_size=3, padding=1),
            nn.PixelShuffle(scale_factor)
        )
        self.reconstruction = nn.Conv2d(num_features, num_channels, kernel_size=3, padding=1)

    def forward(self, x):
        shallow = self.shallow_feature(x)
        deep = self.deep_feature(shallow)
        upsampled = self.upsample(deep + shallow)
        output = self.reconstruction(upsampled)
        return output
```

**设计考虑**：
- 使用残差块构建深层网络
- 去除批归一化层（提高性能）
- 使用残差缩放（训练稳定性）

## 3. 数据设计

### 3.1 数据集类

**SRDataset**：
```python
class SRDataset(Dataset):
    def __init__(self, hr_dir, scale_factor=2, patch_size=96, is_training=True, augment=True):
        self.hr_dir = hr_dir
        self.scale_factor = scale_factor
        self.patch_size = patch_size
        self.is_training = is_training
        self.augment = augment
        self.hr_images = list_images(hr_dir)

    def __getitem__(self, idx):
        hr_image = load_image(self.hr_images[idx])
        if self.is_training:
            hr_image = random_crop(hr_image, self.patch_size)
            if self.augment:
                hr_image = augment(hr_image)
        lr_image = downsample(hr_image, self.scale_factor)
        return to_tensor(lr_image), to_tensor(hr_image)
```

**SRTestDataset**：
```python
class SRTestDataset(Dataset):
    def __init__(self, hr_dir, lr_dir=None, scale_factor=2):
        self.hr_dir = hr_dir
        self.lr_dir = lr_dir
        self.scale_factor = scale_factor
        self.hr_images = list_images(hr_dir)
        self.lr_images = list_images(lr_dir) if lr_dir else None

    def __getitem__(self, idx):
        hr_image = load_image(self.hr_images[idx])
        if self.lr_images:
            lr_image = load_image(self.lr_images[idx])
        else:
            lr_image = downsample(hr_image, self.scale_factor)
        return to_tensor(lr_image), to_tensor(hr_image)
```

### 3.2 数据处理流程

**训练数据**：
1. 加载高分辨率图像
2. 随机裁剪训练块
3. 数据增强（翻转、旋转）
4. 降采样生成低分辨率图像
5. 转换为张量

**测试数据**：
1. 加载高分辨率图像
2. 调整尺寸（可被缩放因子整除）
3. 降采样生成低分辨率图像
4. 转换为张量

## 4. 训练设计

### 4.1 训练器类

```python
class SRTrainer:
    def __init__(self, model_name, scale_factor=2, device=None, learning_rate=1e-4, checkpoint_dir='checkpoints'):
        self.model = get_model(model_name, scale_factor=scale_factor)
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=20, gamma=0.5)

    def train(self, train_dir, val_dir=None, epochs=100, batch_size=16, patch_size=96):
        train_loader = create_dataloader(train_dir, batch_size, patch_size)
        val_loader = create_dataloader(val_dir, batch_size) if val_dir else None

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader) if val_loader else None
            self.scheduler.step()
            self.save_checkpoint(epoch)
```

### 4.2 训练流程

```
开始
  ↓
加载数据集
  ↓
创建模型
  ↓
定义损失函数
  ↓
定义优化器
  ↓
循环 epochs:
  ↓
  训练一个 epoch:
    ↓
    遍历训练数据:
      ↓
      前向传播
      ↓
      计算损失
      ↓
      反向传播
      ↓
      更新参数
    ↓
  验证（如果有）:
    ↓
    遍历验证数据:
      ↓
      前向传播
      ↓
      计算损失
    ↓
  更新学习率
  ↓
  保存检查点
  ↓
结束
```

### 4.3 损失函数

**MSE Loss**：
```python
criterion = nn.MSELoss()
loss = criterion(output, target)
```

**L1 Loss**：
```python
criterion = nn.L1Loss()
loss = criterion(output, target)
```

### 4.4 优化器

**Adam**：
```python
optimizer = optim.Adam(model.parameters(), lr=1e-4, betas=(0.9, 0.999))
```

**学习率调度**：
```python
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)
```

## 5. 评估设计

### 5.1 评估器类

```python
class SREvaluator:
    def __init__(self, model_name, scale_factor=2, device=None):
        self.model = get_model(model_name, scale_factor=scale_factor)

    def evaluate(self, test_dir):
        test_loader = create_dataloader(test_dir)
        psnr_list = []
        ssim_list = []

        for lr_images, hr_images in test_loader:
            sr_images = self.model(lr_images)
            psnr = calculate_psnr(sr_images, hr_images)
            ssim = calculate_ssim(sr_images, hr_images)
            psnr_list.append(psnr)
            ssim_list.append(ssim)

        return {
            'psnr': np.mean(psnr_list),
            'ssim': np.mean(ssim_list)
        }
```

### 5.2 评估指标

**PSNR**：
```python
def calculate_psnr(sr_image, hr_image, max_pixel=1.0):
    mse = torch.mean((sr_image - hr_image) ** 2)
    psnr = 10 * torch.log10(max_pixel ** 2 / mse)
    return psnr.item()
```

**SSIM**：
```python
def calculate_ssim(sr_image, hr_image, window_size=11):
    # 创建高斯窗口
    window = create_gaussian_window(window_size)

    # 计算均值
    mu_sr = conv2d(sr_image, window)
    mu_hr = conv2d(hr_image, window)

    # 计算方差和协方差
    sigma_sr_sq = conv2d(sr_image ** 2, window) - mu_sr ** 2
    sigma_hr_sq = conv2d(hr_image ** 2, window) - mu_hr ** 2
    sigma_sr_hr = conv2d(sr_image * hr_image, window) - mu_sr * mu_hr

    # 计算 SSIM
    c1 = 0.01 ** 2
    c2 = 0.03 ** 2
    ssim = (2 * mu_sr * mu_hr + c1) * (2 * sigma_sr_hr + c2) / \
           ((mu_sr ** 2 + mu_hr ** 2 + c1) * (sigma_sr_sq + sigma_hr_sq + c2))

    return ssim.mean()
```

## 6. 接口设计

### 6.1 命令行接口

**训练命令**：
```bash
python train.py \
    --model srcnn \
    --scale_factor 2 \
    --epochs 100 \
    --batch_size 16 \
    --learning_rate 1e-4 \
    --train_dir data/train \
    --val_dir data/val \
    --checkpoint_dir checkpoints
```

**评估命令**：
```bash
python evaluate.py \
    --model srcnn \
    --scale_factor 2 \
    --checkpoint checkpoints/best.pth \
    --test_dir data/test \
    --output_dir results
```

### 6.2 Python API

**模型创建**：
```python
from src.models import get_model

model = get_model('srcnn', num_channels=3, num_features=64)
```

**训练**：
```python
from src.trainer import SRTrainer

trainer = SRTrainer(model_name='srcnn', scale_factor=2)
history = trainer.train(train_dir='data/train', epochs=100)
```

**评估**：
```python
from src.evaluator import SREvaluator

evaluator = SREvaluator(model_name='srcnn', scale_factor=2)
evaluator.load_checkpoint('checkpoints/best.pth')
results = evaluator.evaluate(test_dir='data/test')
```

**图像超分辨率**：
```python
sr_image = evaluator.upscale_image('input.png', 'output.png')
```

## 7. 错误处理设计

### 7.1 输入验证

- 检查图像路径是否存在
- 检查图像格式是否支持
- 检查模型参数是否有效

### 7.2 异常处理

- 文件不存在异常
- 图像加载异常
- 模型加载异常
- 内存不足异常

### 7.3 错误消息

- 提供清晰的错误描述
- 提供解决建议
- 记录错误日志

## 8. 性能优化设计

### 8.1 数据加载优化

- 多线程数据加载
- 内存映射
- 数据预取

### 8.2 训练优化

- 混合精度训练
- 梯度累积
- 梯度裁剪

### 8.3 推理优化

- 模型量化
- 模型剪枝
- 批量推理

## 9. 扩展性设计

### 9.1 模型扩展

- 添加新模型只需实现 `nn.Module` 子类
- 在 `get_model` 函数中注册新模型

### 9.2 功能扩展

- 添加新损失函数
- 添加新评估指标
- 添加新数据增强方法

### 9.3 接口扩展

- 添加新的命令行参数
- 添加新的 Python API
