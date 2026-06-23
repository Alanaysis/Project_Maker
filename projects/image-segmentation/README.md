# 图像分割 (Image Segmentation)

从零实现 U-Net 语义分割网络，深入理解编码器-解码器架构和跳跃连接的核心原理。

## 学习目标

- **理解语义分割**：像素级分类任务，为图像中的每个像素分配一个类别标签
- **掌握 U-Net 架构**：编码器-解码器结构，通过跳跃连接融合多尺度特征
- **学会上采样**：双线性插值与转置卷积两种上采样方式的原理和区别

## 核心循环

```
图像 → 编码器 → 解码器 → 分割图
```

1. **编码器 (Encoder)**：逐步下采样图像，提取多尺度特征（池化 + 卷积）
2. **瓶颈层 (Bottleneck)**：最深层的特征表示，包含最抽象的语义信息
3. **解码器 (Decoder)**：逐步上采样恢复分辨率，通过跳跃连接融合编码器特征
4. **分割图 (Segmentation Map)**：像素级分类输出，与输入图像同尺寸

## 项目结构

```
image-segmentation/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/
│   ├── __init__.py
│   ├── blocks.py               # 基础构建块 (DoubleConv, Down, Up)
│   ├── encoder.py              # 编码器实现
│   ├── decoder.py              # 解码器实现
│   ├── unet.py                 # U-Net 完整模型
│   ├── dataset.py              # 数据集工具
│   ├── loss.py                 # 损失函数 (DiceLoss, BCEDiceLoss)
│   └── train.py                # 训练工具
└── tests/
    ├── __init__.py
    ├── test_blocks.py           # 构建块测试
    ├── test_encoder.py          # 编码器测试
    ├── test_decoder.py          # 解码器测试
    ├── test_unet.py             # U-Net 测试
    ├── test_loss.py             # 损失函数测试
    └── test_dataset.py          # 数据集和训练测试
```

## 快速开始

### 基本使用

```python
import torch
from src import UNet

# 创建 U-Net 模型
model = UNet(
    in_channels=3,       # RGB 输入
    out_channels=1,      # 二值分割
    base_channels=64,    # 基础通道数
    n_levels=4,          # 4 层编码器/解码器
)

# 输入图像 (batch=1, channels=3, height=256, width=256)
x = torch.randn(1, 3, 256, 256)

# 前向传播
output = model(x)
print(f"输入形状: {x.shape}")      # (1, 3, 256, 256)
print(f"输出形状: {output.shape}")  # (1, 1, 256, 256)
print(f"参数量: {model.count_parameters():,}")

# 预测分割掩码
mask = model.predict(x, threshold=0.5)
print(f"掩码形状: {mask.shape}")    # (1, 1, 256, 256)
```

### 使用合成数据训练

```python
import torch
from torch.utils.data import DataLoader
from src import UNet, SegmentationDataset, BCEDiceLoss
from src.dataset import create_synthetic_dataset
from src.train import Trainer

# 生成合成数据
images, masks = create_synthetic_dataset(n_samples=100, image_size=128)
dataset = SegmentationDataset(images=images, masks=masks)
loader = DataLoader(dataset, batch_size=8, shuffle=True)

# 创建模型和训练器
model = UNet(in_channels=3, out_channels=1, base_channels=32, n_levels=3)
trainer = Trainer(model, learning_rate=1e-3)

# 训练
history = trainer.fit(loader, n_epochs=10, verbose=True)
```

### 多类分割

```python
model = UNet(
    in_channels=3,
    out_channels=5,     # 5 个类别
    base_channels=64,
    n_levels=4,
)

x = torch.randn(1, 3, 256, 256)
output = model(x)       # (1, 5, 256, 256)
```

## 核心算法

### 1. 跳跃连接 (Skip Connections)

```python
# 编码器保存中间特征
skips = [encoder_level_1, encoder_level_2, ...]

# 解码器逐层融合
x = bottleneck
for i, up in enumerate(up_blocks):
    x = up(x, skips[n_levels - 1 - i])  # 上采样 + 拼接 + 卷积
```

**原理**：编码器丢失的空间信息通过跳跃连接传递给解码器，解决了深层网络中空间信息丢失的问题。

### 2. 上采样 (Upsampling)

```python
# 方式一：双线性插值 + 卷积
self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

# 方式二：转置卷积
self.up = nn.ConvTranspose2d(in_ch, in_ch // 2, kernel_size=2, stride=2)
```

**原理**：双线性插值更平滑但学习能力弱；转置卷积可以学习上采样方式但可能产生棋盘伪影。

### 3. Dice Loss

```python
def dice_loss(pred, target, smooth=1.0):
    pred = torch.sigmoid(pred)
    intersection = (pred * target).sum()
    return 1 - (2. * intersection + smooth) / (pred.sum() + target.sum() + smooth)
```

**原理**：Dice 系数衡量预测与真值的重叠度，对类别不平衡问题比 BCE 更鲁棒。

## 关键概念

### 语义分割 vs 目标检测 vs 实例分割

| 任务 | 输出 | 关键区别 |
|------|------|----------|
| 语义分割 | 像素级类别标签 | 同类物体不区分实例 |
| 目标检测 | 边界框 + 类别 | 只给出粗略位置 |
| 实例分割 | 像素级实例标签 | 同类物体区分不同实例 |

### 编码器-解码器架构

- **编码器**：逐步压缩空间信息，提取语义特征
- **解码器**：逐步恢复空间分辨率，生成像素级预测
- **跳跃连接**：融合低层细节和高层语义

### 上采样方式对比

| 方式 | 优点 | 缺点 |
|------|------|------|
| 双线性插值 | 平滑、无参数 | 学习能力弱 |
| 转置卷积 | 可学习 | 可能产生棋盘伪影 |
| 最近邻插值 | 简单、快速 | 不平滑 |

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行构建块测试
pytest tests/test_blocks.py -v

# 运行 U-Net 测试
pytest tests/test_unet.py -v

# 运行损失函数测试
pytest tests/test_loss.py -v

# 运行数据集和训练测试
pytest tests/test_dataset.py -v
```

## 参考资料

- [Ronneberger et al. (2015). U-Net: Convolutional Networks for Biomedical Image Segmentation. MICCAI.](https://arxiv.org/abs/1505.04597)
- [Long et al. (2015). Fully Convolutional Networks for Semantic Segmentation. CVPR.](https://arxiv.org/abs/1411.4038)
- [PyTorch Segmentation Models](https://github.com/qubvel/segmentation_models.pytorch)

## License

This project is for educational purposes.

---

[返回 AI 模块](../AI_README.md) | [返回主目录](../../README.md)
