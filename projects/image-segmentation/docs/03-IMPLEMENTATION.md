# 03 - 实现文档：图像分割

## 1. 实现概述

本项目从零实现 U-Net 语义分割网络，使用 PyTorch 框架。代码分为 7 个模块，总计约 600 行 Python 代码。

### 1.1 文件清单

| 文件 | 行数 | 职责 |
|------|------|------|
| blocks.py | ~100 | DoubleConv, Down, Up 基础构建块 |
| encoder.py | ~80 | 编码器（收缩路径） |
| decoder.py | ~80 | 解码器（扩张路径） |
| unet.py | ~100 | 完整 U-Net 模型 |
| dataset.py | ~80 | 数据集工具和合成数据生成 |
| loss.py | ~70 | DiceLoss 和 BCEDiceLoss |
| train.py | ~120 | 训练器和评估指标 |

## 2. 核心实现

### 2.1 DoubleConv 块

```python
class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels, mid_channels=None, use_batch_norm=True):
        # Conv2d -> BN -> ReLU -> Conv2d -> BN -> ReLU
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, 3, padding=1, bias=not use_batch_norm),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, 3, padding=1, bias=not use_batch_norm),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )
```

**设计要点**：
- padding=1 保持空间尺寸不变
- bias=False 当使用 BatchNorm 时（BN 已有偏置项）
- inplace=True 节省内存

### 2.2 Down 块（编码器）

```python
class Down(nn.Module):
    def __init__(self, in_channels, out_channels, use_batch_norm=True):
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels, use_batch_norm=use_batch_norm),
        )
```

**设计要点**：
- MaxPool2d(2) 将空间尺寸减半
- 通道数翻倍增加特征丰富度

### 2.3 Up 块（解码器）

```python
class Up(nn.Module):
    def __init__(self, in_channels, out_channels, use_bilinear=True, use_batch_norm=True):
        if use_bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels, mid_channels=in_channels // 2)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, 2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x, skip):
        x = self.up(x)
        # 处理尺寸不匹配
        diff_h = skip.size(2) - x.size(2)
        diff_w = skip.size(3) - x.size(3)
        x = F.pad(x, [diff_w // 2, diff_w - diff_w // 2,
                       diff_h // 2, diff_h - diff_h // 2])
        x = torch.cat([skip, x], dim=1)
        return self.conv(x)
```

**设计要点**：
- 尺寸不匹配处理：奇数尺寸时需要 padding
- 跳跃连接：沿通道维度拼接编码器特征

### 2.4 Encoder

```python
class Encoder(nn.Module):
    def forward(self, x):
        skips = [self.inc(x)]        # 第一层（无下采样）
        for down in self.down_blocks:
            skips.append(down(skips[-1]))
        bottleneck = skips.pop()      # 最后一层作为瓶颈
        return skips, bottleneck
```

**设计要点**：
- 保存每一层的输出用于跳跃连接
- 瓶颈层从 skips 中分离出来

### 2.5 Decoder

```python
class Decoder(nn.Module):
    def forward(self, bottleneck, skips):
        x = bottleneck
        for i, up in enumerate(self.up_blocks):
            skip_idx = self.n_levels - 1 - i  # 从深到浅
            x = up(x, skips[skip_idx])
        return self.outc(x)  # 1x1 卷积输出
```

**设计要点**：
- 从深到浅处理跳跃连接
- 最终 1x1 卷积映射到输出通道数

## 3. 损失函数实现

### 3.1 Dice Loss

```python
class DiceLoss(nn.Module):
    def forward(self, pred, target):
        pred = torch.sigmoid(pred)  # 将 logits 转为概率
        pred_flat = pred.view(B, C, -1)
        target_flat = target.view(B, C, -1)
        intersection = (pred_flat * target_flat).sum(dim=2)
        union = pred_flat.sum(dim=2) + target_flat.sum(dim=2)
        dice = (2 * intersection + smooth) / (union + smooth)
        return 1 - dice.mean()
```

### 3.2 BCEDiceLoss

```python
class BCEDiceLoss(nn.Module):
    def forward(self, pred, target):
        bce = F.binary_cross_entropy_with_logits(pred, target)
        dice = self.dice_loss(pred, target)
        return 0.5 * bce + 0.5 * dice
```

## 4. 训练实现

### 4.1 Trainer 类

```python
class Trainer:
    def train_epoch(self, dataloader):
        self.model.train()
        for images, masks in dataloader:
            predictions = self.model(images)
            loss = self.loss_fn(predictions, masks)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def validate(self, dataloader):
        self.model.eval()
        with torch.no_grad():
            for images, masks in dataloader:
                predictions = self.model(images)
                # 计算 loss, IoU, Dice
```

### 4.2 评估指标

```python
def compute_iou(pred, target, threshold=0.5):
    pred_binary = (torch.sigmoid(pred) > threshold).float()
    intersection = (pred_binary * target).sum()
    union = pred_binary.sum() + target.sum() - intersection
    return (intersection / union).item()
```

## 5. 合成数据生成

```python
def create_synthetic_dataset(n_samples, image_size, seed=42):
    # 生成随机图像
    images = np.random.randn(n_samples, 3, image_size, image_size)
    # 生成圆形掩码
    for i in range(n_samples):
        center = random_center()
        radius = random_radius()
        mask = (distance_to_center <= radius)
        masks[i, 0] = mask
        images[i] += mask * 0.5  # 掩码区域更亮
```

**设计要点**：
- 生成简单的几何形状作为分割目标
- 图像中掩码区域有明显亮度差异
- 支持可重复的随机种子

## 6. 关键实现细节

### 6.1 尺寸不匹配处理

当输入尺寸不是 2 的幂时，编码器和解码器的特征图尺寸可能不匹配。解决方案：

```python
diff_h = skip.size(2) - x.size(2)
diff_w = skip.size(3) - x.size(3)
x = F.pad(x, [diff_w // 2, diff_w - diff_w // 2,
               diff_h // 2, diff_h - diff_h // 2])
```

### 6.2 内存优化

- 使用 `inplace=True` 的 ReLU
- 梯度检查点（未实现，但可扩展）
- 混合精度训练（未实现，但可扩展）

### 6.3 参数量计算

标准 U-Net (base_channels=64, n_levels=4) 约 31M 参数：
- 编码器：~12M
- 瓶颈层：~4M
- 解码器：~15M

## 7. 已知限制

1. 不支持动态输入尺寸（需要预先知道尺寸）
2. 未实现梯度检查点
3. 未实现混合精度训练
4. 未实现分布式训练
5. 合成数据较简单，仅用于测试
