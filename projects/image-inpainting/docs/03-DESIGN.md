# 技术设计文档 - 图像修复

## 1. 架构概述

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ImageInpainter Pipeline                   │
│                                                             │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Input    │    │ Mask         │    │ Context Encoder  │  │
│  │  Image    │───▶│ Generation   │───▶│ (U-Net)          │  │
│  └──────────┘    └──────────────┘    └────────┬─────────┘  │
│                                               │              │
│                                               ▼              │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Output   │◀──│ Blending     │◀──│ PatchGAN         │  │
│  │  Image    │    │              │    │ Discriminator     │  │
│  └──────────┘    └──────────────┘    └──────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 模块划分

| 模块 | 职责 | 文件位置 |
|------|------|----------|
| Context Encoder | U-Net 生成器 + PatchGAN 判别器 | `src/context_encoder.py` |
| Mask | 掩码生成（中心、矩形、不规则） | `src/mask.py` |
| Losses | 重建损失 + 对抗损失 | `src/losses.py` |
| Metrics | PSNR、SSIM 评估指标 | `src/metrics.py` |
| Pipeline | 高级封装（训练、推理、评估） | `src/inpainting.py` |

## 2. 核心流程

### 主流程：图像修复推理

```
输入图像 (C, H, W)
    │
    ▼
生成掩码 (1, H, W)  ─────┐
    │                     │
    ▼                     │
应用掩码：masked = img * (1 - mask)
    │
    ▼
拼接输入：[masked_image, mask] (4, H, W)
    │
    ▼
┌─────────────────────────────────┐
│         U-Net Generator          │
│                                 │
│  Encoder Path:                  │
│    4ch → 64 → 128 → 256 → 512  │
│    ↓   ↓   ↓    ↓    ↓    ↓   │
│  128  64  32   16    8    4    │
│                                 │
│  Bottleneck:                    │
│    512 → 512                    │
│    4x4 → 1x1                   │
│                                 │
│  Decoder Path (with skips):     │
│    512 → 512 → 512 → 512       │
│    ↓    ↓    ↓    ↓            │
│    4    8   16   32             │
│    +skip connections            │
│                                 │
│  Output: Tanh → 3ch             │
│    32 → 64 → 128               │
└─────────────────────────────────┘
    │
    ▼
混合输出：result = img * (1 - mask) + output * mask
    │
    ▼
修复图像 (3, H, W)
```

### 训练流程

```
For each epoch:
  For each batch:
    ┌─────────────────────────────────────┐
    │         Train Discriminator          │
    │                                     │
    │  real_pair = [real_img, masked_img]  │
    │  fake_pair = [fake_img, masked_img]  │
    │                                     │
    │  D_loss = Hinge(D(real), D(fake))   │
    │  Update D                           │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │          Train Generator             │
    │                                     │
    │  fake_img = G(input)                │
    │  fake_pair = [fake_img, masked_img] │
    │                                     │
    │  rec_loss = L1(fake, real)          │
    │  adv_loss = -log(D(fake))           │
    │  G_loss = rec + 0.001 * adv         │
    │  Update G                           │
    └─────────────────────────────────────┘
```

## 3. 数据设计

### 核心数据结构

```python
# 图像张量
image: Tensor  # shape: (C, H, W) or (B, C, H, W), range: [-1, 1]

# 掩码张量
mask: Tensor   # shape: (1, H, W) or (B, 1, H, W), values: {0, 1}
               # 1 = masked (missing) region, 0 = known region

# 输入张量（送入生成器）
input: Tensor  # shape: (4, H, W) = [R, G, B, Mask]

# 判别器输入对
disc_input: Tensor  # shape: (6, H, W) = [image_pair, condition]
```

### 掩码设计

| 掩码类型 | 生成方式 | 适用场景 |
|----------|----------|----------|
| 中心掩码 | 固定位置矩形 | 基准评估 |
| 随机矩形 | 随机位置和大小 | 训练数据增强 |
| 不规则掩码 | 随机笔画模拟 | 真实损坏场景 |

## 4. 接口设计

### 公共 API

```python
class ImageInpainter:
    """图像修复管线"""

    def __init__(
        self,
        image_size: Tuple[int, int] = (128, 128),
        ngf: int = 64,           # 生成器滤波器数
        ndf: int = 64,           # 判别器滤波器数
        lambda_rec: float = 1.0, # 重建损失权重
        lambda_adv: float = 0.001, # 对抗损失权重
        device: Optional[str] = None,
    ): ...

    def inpaint(
        self,
        image: Tensor,   # (C, H, W) or (B, C, H, W)
        mask: Tensor,    # (1, H, W) or (B, 1, H, W)
        blend: bool = True,
    ) -> Tensor: ...

    def train_step(
        self,
        images: Tensor,  # (B, C, H, W)
        masks: Tensor,   # (B, 1, H, W)
    ) -> Dict[str, float]: ...

    def evaluate(
        self,
        images: Tensor,
        masks: Tensor,
    ) -> Dict[str, float]: ...

    def save(self, path: str) -> None: ...
    def load(self, path: str) -> None: ...
```

## 5. 技术选型

### 选型决策

| 决策点 | 选项A | 选项B | 选项C | 最终选择 |
|--------|-------|-------|-------|----------|
| 网络架构 | U-Net | ResNet | Transformer | U-Net |
| 判别器类型 | PatchGAN | GlobalGAN | Multi-scale | PatchGAN |
| 重建损失 | L1 | L2 | Perceptual | L1 |
| 对抗损失 | Hinge | Non-saturating | WGAN | Hinge |
| 激活函数 | ReLU | LeakyReLU | GELU | LeakyReLU(enc) + ReLU(dec) |

### 选择理由

**U-Net 选择原因**：
1. 跳跃连接保留空间细节，对图像修复至关重要
2. 编码器-解码器结构自然支持图像到图像的转换
3. 架构成熟，大量论文和代码可参考

**PatchGAN 选择原因**：
1. 关注局部纹理质量，正合图像修复的需求
2. 参数量少，训练稳定
3. 可应用于不同大小的图像

**L1 损失选择原因**：
1. 比 L2 产生更锐利的结果
2. 不会"平均"多个可能的预测
3. 对异常值更鲁棒

## 6. 设计决策与权衡

### 决策1：跳跃连接 vs 纯编码器-解码器

**背景**：是否在 U-Net 中使用跳跃连接

**方案对比**：

| 维度 | 纯编码器-解码器 | U-Net（跳跃连接） |
|------|----------------|------------------|
| 参数量 | 较少 | 较多 |
| 细节保留 | 差 | 好 |
| 语义理解 | 好 | 好 |
| 训练难度 | 较难 | 较易 |

**最终选择**：U-Net（跳跃连接）

**理由**：
1. 图像修复需要保留已知区域的细节
2. 跳跃连接帮助解码器恢复空间信息
3. 训练更稳定，收敛更快

### 决策2：损失函数权重

**背景**：重建损失和对抗损失的权重如何平衡

**权衡分析**：
- 重建损失过大 → 结果模糊但内容正确
- 对抗损失过大 → 结果锐利但可能有伪影
- 最佳平衡点需要实验确定

**最终选择**：lambda_rec=1.0, lambda_adv=0.001

**理由**：
1. 重建损失提供正确的基线
2. 对抗损失添加真实感但权重不能太大
3. 这个比例在实践中效果稳定

## 7. 扩展性设计

### 预留的扩展点

1. **门控卷积**：替换 `EncoderBlock` 和 `DecoderBlock` 中的普通卷积
2. **注意力机制**：在 U-Net 的瓶颈层添加自注意力
3. **多尺度判别器**：在不同分辨率下添加判别器
4. **感知损失**：添加 VGG 特征空间的损失

### 如何扩展

```python
# 示例：添加门控卷积
class GatedConv2d(nn.Module):
    def __init__(self, in_ch, out_ch, kernel_size, stride, padding):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, kernel_size, stride, padding)
        self.mask_conv = nn.Conv2d(in_ch, out_ch, kernel_size, stride, padding)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        features = self.conv(x)
        mask = self.sigmoid(self.mask_conv(x))
        return features * mask

# 替换 UNetGenerator 中的卷积层即可
```
