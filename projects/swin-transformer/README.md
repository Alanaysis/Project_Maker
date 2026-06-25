# Swin Transformer

实现 Swin Transformer，理解滑动窗口注意力机制。

## 项目简介

Swin Transformer（Shifted Window Transformer）是一种层级式视觉 Transformer 架构，由微软亚洲研究院于 2021 年提出。它通过滑动窗口注意力机制实现了线性计算复杂度，同时保持了强大的特征提取能力。

### 核心特性

- **窗口注意力（Window Attention）**：在局部窗口内计算自注意力，复杂度从 O(n²) 降至 O(n)
- **移位窗口（Shifted Window）**：通过移位窗口实现跨窗口信息流动
- **层级特征（Hierarchical Features）**：类似 CNN 的多尺度特征图
- **相对位置偏置（Relative Position Bias）**：可学习的相对位置编码

## 学习目标

- 理解 Swin Transformer 架构设计
- 掌握窗口注意力机制的实现
- 学会层级特征提取方法
- 了解移位窗口的工作原理

## 项目结构

```
projects/swin-transformer/
├── src/
│   ├── __init__.py
│   ├── patch_embedding.py      # Patch 嵌入和合并
│   ├── window_attention.py     # 窗口注意力机制
│   ├── shifted_window.py       # 移位窗口 Transformer 块
│   └── swin_transformer.py     # 主模型
├── tests/
│   └── test_swin_transformer.py
├── examples/
│   └── example_usage.py
├── docs/
│   ├── 01-RESEARCH.md          # 调研报告
│   ├── 02-ARCHITECTURE.md      # 架构设计
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试策略
│   └── 05-DEVELOPMENT.md       # 开发指南
├── README.md
└── LEARNING_NOTES.md
```

## 快速开始

### 环境要求

- Python 3.8+
- PyTorch 1.9+

### 安装依赖

```bash
pip install torch torchvision
```

### 运行示例

```bash
cd /home/siok/project_copyninja/projects/swin-transformer
python examples/example_usage.py
```

### 运行测试

```bash
python -m pytest tests/ -v
```

## 核心概念

### 1. 窗口注意力

传统的全局自注意力计算复杂度为 O(n²)，其中 n 是 patch 数量。窗口注意力将特征图划分为不重叠的窗口，在每个窗口内独立计算注意力：

```
全局注意力: O(n²) = O(3136²) ≈ 9.8M
窗口注意力: O(n × w²) = O(3136 × 49) ≈ 153K
加速比: 64x
```

### 2. 移位窗口

单纯的窗口注意力缺乏跨窗口信息交流。移位窗口通过在相邻层之间移动窗口位置来解决这个问题：

```
第 1 层（常规窗口）:     第 2 层（移位窗口）:
+---+---+---+---+      +-----+-----+-----+
| 1 | 2 | 3 | 4 |      |  A  |  B  |  C  |
+---+---+---+---+      +-----+-----+-----+
| 5 | 6 | 7 | 8 |      |  D  |  E  |  F  |
+---+---+---+---+      +-----+-----+-----+
```

### 3. 层级特征

Swin Transformer 通过 Patch Merging 在不同阶段之间下采样，生成多尺度特征图：

```
Stage 1: 56×56 (1/4 分辨率)
Stage 2: 28×28 (1/8 分辨率)
Stage 3: 14×14 (1/16 分辨率)
Stage 4: 7×7 (1/32 分辨率)
```

### 4. 相对位置偏置

使用可学习的相对位置偏置代替绝对位置编码，更好地捕捉 token 之间的空间关系。

## 使用示例

### 基本用法

```python
import torch
from src.swin_transformer import swin_tiny_patch4_window7_224

# 创建模型
model = swin_tiny_patch4_window7_224(num_classes=10)

# 创建输入
x = torch.randn(1, 3, 224, 224)

# 前向传播
output = model(x)
print(f"输出形状: {output.shape}")  # (1, 10)
```

### 特征提取

```python
# 提取特征（不包含分类头）
features = model.forward_features(x)
print(f"特征形状: {features.shape}")  # (1, 768)
```

### 自定义模型

```python
from src.swin_transformer import SwinTransformer

model = SwinTransformer(
    img_size=32,
    patch_size=4,
    in_channels=3,
    num_classes=100,
    embed_dim=64,
    depths=(2, 2, 2),
    num_heads=(2, 4, 8),
    window_size=4,
)
```

## 模型变体

| 模型 | 嵌入维度 | 深度 | 注意力头 | 参数量 |
|------|---------|------|---------|--------|
| Swin-Tiny | 96 | 2,2,6,2 | 3,6,12,24 | ~28M |
| Swin-Small | 96 | 2,2,18,2 | 3,6,12,24 | ~50M |
| Swin-Base | 128 | 2,2,18,2 | 4,8,16,32 | ~88M |

## 技术细节

### 复杂度分析

| 操作 | 全局注意力 | 窗口注意力 |
|------|-----------|-----------|
| 时间复杂度 | O(n² × C) | O(n × w² × C) |
| 空间复杂度 | O(n²) | O(n × w²) |
| 224×224 图像 | 9.8M | 153K |

其中：
- n = patch 数量 (3136)
- w = 窗口大小 (7)
- C = 嵌入维度 (96)

### 数据流

```
图像 (224×224×3)
    ↓
Patch Embedding (4×4 patches → 96-dim)
    ↓
Stage 1: 2× ShiftedWindowBlock (56×56, dim=96)
    ↓
Patch Merging (56×56 → 28×28, dim=192)
    ↓
Stage 2: 2× ShiftedWindowBlock (28×28, dim=192)
    ↓
Patch Merging (28×28 → 14×14, dim=384)
    ↓
Stage 3: 6× ShiftedWindowBlock (14×14, dim=384)
    ↓
Patch Merging (14×14 → 7×7, dim=768)
    ↓
Stage 4: 2× ShiftedWindowBlock (7×7, dim=768)
    ↓
Layer Norm → Global Average Pooling
    ↓
Classification Head (768 → num_classes)
```

## 性能基准

### ImageNet 分类

| 模型 | 分辨率 | Top-1 准确率 |
|------|--------|-------------|
| Swin-T | 224 | 81.3% |
| Swin-S | 224 | 83.0% |
| Swin-B | 224 | 83.5% |
| Swin-L | 384 | 87.3% |

### COCO 目标检测

| 模型 | Backbone | AP (box) |
|------|----------|----------|
| Cascade Mask R-CNN | Swin-T | 50.4 |
| Cascade Mask R-CNN | Swin-S | 51.9 |
| Cascade Mask R-CNN | Swin-B | 53.0 |

## 扩展阅读

### 论文

- [Swin Transformer: Hierarchical Vision Transformer using Shifted Windows](https://arxiv.org/abs/2103.14030)
- [Swin Transformer V2: Scaling Up Capacity and Resolution](https://arxiv.org/abs/2111.09883)

### 相关工作

- [ViT: An Image is Worth 16x16 Words](https://arxiv.org/abs/2010.11929)
- [DeiT: Training data-efficient image transformers](https://arxiv.org/abs/2012.12877)
- [PVT: Pyramid Vision Transformer](https://arxiv.org/abs/2102.12122)

### 代码库

- [官方实现](https://github.com/microsoft/Swin-Transformer)
- [timm 库](https://github.com/huggingface/pytorch-image-models)

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目仅用于学习目的。

## 致谢

- 感谢微软亚洲研究院的 Swin Transformer 论文
- 感谢 PyTorch 团队提供的优秀框架
- 感谢开源社区的贡献
