# 02 - 设计文档：图像分割

## 1. 架构设计

### 1.1 整体架构

本项目实现标准 U-Net 架构，由以下模块组成：

```
UNet
├── Encoder (编码器)
│   ├── DoubleConv (初始卷积)
│   └── Down x n_levels (下采样模块)
├── Decoder (解码器)
│   ├── Up x n_levels (上采样模块 + 跳跃连接)
│   └── Conv2d 1x1 (输出卷积)
└── Skip Connections (跳跃连接)
```

### 1.2 模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| DoubleConv | 两次 3x3 卷积 + BN + ReLU | (B, C_in, H, W) | (B, C_out, H, W) |
| Down | MaxPool + DoubleConv | (B, C, H, W) | (B, 2C, H/2, W/2) |
| Up | Upsample + Concat + DoubleConv | (B, C, H, W) + skip | (B, C/2, 2H, 2W) |
| Encoder | 特征提取 + 下采样 | (B, 3, H, W) | skips + bottleneck |
| Decoder | 特征恢复 + 上采样 | bottleneck + skips | (B, C_out, H, W) |
| UNet | 完整分割网络 | (B, 3, H, W) | (B, C_out, H, W) |

### 1.3 数据流

```
输入: (B, 3, 256, 256)
    |
    v
Encoder:
    inc: (B, 3, 256, 256) -> (B, 64, 256, 256)  [skip_0]
    down_0: -> (B, 128, 128, 128)  [skip_1]
    down_1: -> (B, 256, 64, 64)  [skip_2]
    down_2: -> (B, 512, 32, 32)  [skip_3]
    down_3: -> (B, 1024, 16, 16)  [bottleneck]
    |
    v
Decoder:
    up_0: (B, 1024, 16, 16) + skip_3 -> (B, 512, 32, 32)
    up_1: (B, 512, 32, 32) + skip_2 -> (B, 256, 64, 64)
    up_2: (B, 256, 64, 64) + skip_1 -> (B, 128, 128, 128)
    up_3: (B, 128, 128, 128) + skip_0 -> (B, 64, 256, 256)
    |
    v
输出: (B, 1, 256, 256)
```

## 2. 接口设计

### 2.1 UNet 类

```python
class UNet(nn.Module):
    def __init__(
        self,
        in_channels: int = 3,      # 输入通道数
        out_channels: int = 1,     # 输出通道数/类别数
        base_channels: int = 64,   # 基础通道数
        n_levels: int = 4,         # 编码器/解码器层数
        use_bilinear: bool = True, # 是否使用双线性上采样
        use_batch_norm: bool = True, # 是否使用批归一化
    )

    def forward(self, x: torch.Tensor) -> torch.Tensor
    def predict(self, x: torch.Tensor, threshold: float = 0.5) -> torch.Tensor
    def count_parameters(self) -> int
```

### 2.2 Encoder 类

```python
class Encoder(nn.Module):
    def __init__(
        self,
        in_channels: int = 3,
        base_channels: int = 64,
        n_levels: int = 4,
        use_batch_norm: bool = True,
    )

    def forward(self, x) -> Tuple[List[Tensor], Tensor]  # (skips, bottleneck)
```

### 2.3 Decoder 类

```python
class Decoder(nn.Module):
    def __init__(
        self,
        out_channels: int = 1,
        skip_channels: List[int] = None,
        base_channels: int = 64,
        n_levels: int = 4,
        use_bilinear: bool = True,
        use_batch_norm: bool = True,
    )

    def forward(self, bottleneck, skips) -> torch.Tensor
```

## 3. 设计决策

### 3.1 为什么选择 U-Net？

| 架构 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| FCN | 简单、端到端 | 空间信息丢失 | 粗粒度分割 |
| U-Net | 跳跃连接、细节恢复 | 计算量较大 | 医学影像、精细分割 |
| DeepLab | 多尺度特征 | 复杂 | 自然场景分割 |

选择 U-Net 的原因：
1. 架构清晰，适合学习
2. 跳跃连接是核心创新
3. 广泛应用于各种分割任务

### 3.2 双线性 vs 转置卷积

| 特性 | 双线性插值 | 转置卷积 |
|------|------------|----------|
| 参数量 | 无额外参数 | 有可学习参数 |
| 计算量 | 较小 | 较大 |
| 棋盘伪影 | 无 | 可能有 |
| 学习能力 | 弱 | 强 |

设计选择：默认使用双线性插值，因为：
1. 无棋盘伪影
2. 参数量更小
3. 实际效果差异不大

### 3.3 批归一化

默认启用批归一化，原因：
1. 稳定训练
2. 允许更大的学习率
3. 有一定的正则化效果

## 4. 通道数设计

### 4.1 标准配置 (base_channels=64)

| 层级 | 编码器通道 | 解码器通道 | 空间尺寸 |
|------|------------|------------|----------|
| 0 | 64 | 64 | H x W |
| 1 | 128 | 128 | H/2 x W/2 |
| 2 | 256 | 256 | H/4 x W/4 |
| 3 | 512 | 512 | H/8 x W/8 |
| 瓶颈 | 1024 | - | H/16 x W/16 |

### 4.2 轻量配置 (base_channels=16)

适用于资源受限场景，参数量减少约 16 倍。

## 5. 损失函数设计

### 5.1 Dice Loss

适合类别不平衡场景，直接优化 IoU 指标。

### 5.2 BCE + Dice 组合

结合两种损失的优势：
- BCE：稳定的像素级梯度
- Dice：对类别不平衡鲁棒

默认权重：BCE 0.5 + Dice 0.5

## 6. 训练策略

### 6.1 优化器

使用 Adam 优化器，初始学习率 1e-3。

### 6.2 学习率调度

使用 ReduceLROnPlateau：
- 监控验证损失
- patience=5
- factor=0.5

### 6.3 评估指标

- **IoU**：主要评估指标
- **Dice**：辅助评估指标
- **Loss**：训练监控

## 7. 可扩展性

### 7.1 支持的配置

- 任意输入通道数（灰度、RGB、多光谱）
- 任意输出类别数
- 可调节的网络深度和宽度
- 可选择的上采样方式

### 7.2 未来扩展方向

- 添加注意力机制
- 支持 DeepLab v3+
- 添加预训练编码器（ResNet、EfficientNet）
- 支持混合精度训练
