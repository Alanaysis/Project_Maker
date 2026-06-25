# Vision Transformer (ViT) - 视觉 Transformer 图像分类

实现 Vision Transformer，理解视觉 Transformer 的核心原理：Patch Embedding、自注意力机制在视觉中的应用。

## 学习目标

- 理解 ViT 架构：图像如何通过 Transformer 进行分类
- 掌握 Patch Embedding：将图像分割为 patches 并线性嵌入
- 学会自注意力机制在视觉中的应用：Multi-Head Self-Attention
- 实现完整的 Vision Transformer 并在 MNIST/CIFAR-10 上训练

## 核心循环

```
图像 -> Patch Embedding -> Transformer 编码 -> [CLS] token -> 分类头 -> 输出
```

## 项目结构

```
vit/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── patch_embedding.py   # Patch Embedding 层
│   ├── attention.py         # Multi-Head Self-Attention
│   ├── transformer.py       # Transformer Encoder
│   ├── vit.py               # 完整 ViT 模型
│   ├── trainer.py           # 训练器
│   └── visualization.py     # 可视化工具
├── tests/
│   ├── test_patch_embedding.py  # Patch Embedding 测试
│   ├── test_attention.py        # 注意力测试
│   ├── test_transformer.py      # Transformer 测试
│   └── test_vit.py              # 完整模型测试
├── examples/
│   ├── compare_models.py        # 模型变体对比
│   └── attention_visualization.py # 注意力可视化
├── docs/
│   ├── 01-RESEARCH.md       # 研究文档
│   ├── 02-DESIGN.md         # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发文档
├── train.py                 # 训练脚本
├── demo.py                  # 演示脚本
├── requirements.txt         # 依赖包
├── README.md                # 项目说明
└── LEARNING_NOTES.md        # 学习笔记
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行演示

```bash
python demo.py
```

### 训练模型

```bash
# 使用 MNIST 数据集（默认，快速验证）
python train.py --epochs 5 --model tiny

# 使用 CIFAR-10 数据集
python train.py --dataset cifar10 --epochs 20 --model small

# 自定义参数
python train.py --epochs 10 --lr 1e-3 --batch_size 128 --model tiny
```

### 运行测试

```bash
pytest tests/ -v
```

### 运行示例

```bash
# 对比不同模型变体
python examples/compare_models.py

# 注意力可视化
python examples/attention_visualization.py
```

## 模型架构

### ViT 整体流程

```
输入图像 (B, 3, 224, 224)
    │
    ▼ Patch Embedding
    │ 将图像分割为 16x16 的 patches
    │ 每个 patch 线性投影为 768 维向量
    │ 添加 [CLS] token 和位置编码
    │ 输出: (B, 197, 768)
    │
    ▼ Transformer Encoder (x 12 层)
    │ 每层包含:
    │   - Layer Norm + Multi-Head Self-Attention + 残差连接
    │   - Layer Norm + Feed-Forward Network + 残差连接
    │ 输出: (B, 197, 768)
    │
    ▼ 取 [CLS] token
    │ (B, 197, 768) -> (B, 768)
    │
    ▼ 分类头
    │ Linear -> Tanh -> Linear
    │ 输出: (B, num_classes)
```

### 模型变体

| 模型 | 嵌入维度 | 深度 | 注意力头 | 参数量 | 适用场景 |
|------|----------|------|----------|--------|----------|
| ViT-Tiny | 192 | 4 | 3 | ~5.7M | 快速实验、小数据集 |
| ViT-Small | 384 | 8 | 6 | ~22M | 中等规模任务 |
| ViT-Base | 768 | 12 | 12 | ~86M | 标准任务 |

### 核心组件

#### 1. Patch Embedding

将图像分割为 patches 并线性嵌入：

```python
# 使用 Conv2d 实现（等价于手动分割 + 线性投影）
self.projection = nn.Conv2d(
    in_channels=3, out_channels=768,
    kernel_size=16, stride=16,
)
# 224x224 图像 -> 14x14 = 196 个 patches
```

#### 2. Multi-Head Self-Attention

每个 patch 关注所有其他 patches：

```python
# Q, K, V 投影
qkv = self.qkv(x)  # (B, N, 3*D)

# 计算注意力
attn = (Q @ K^T) / sqrt(d_k)  # (B, H, N, N)
attn = softmax(attn)
output = attn @ V  # (B, H, N, d_k)
```

#### 3. Transformer Encoder

多层 Transformer Block 堆叠：

```python
# Pre-LN 架构
x = x + self.attn(self.norm1(x))  # 自注意力 + 残差
x = x + self.ffn(self.norm2(x))   # 前馈网络 + 残差
```

## 核心概念

### Patch Embedding

将图像视为 patch 序列，每个 patch 是一个"视觉 token"。

```
图像 (224x224x3) -> 196 个 patches (16x16x3) -> 196 个嵌入向量 (768 维)
```

### 位置编码

为每个 patch 位置添加可学习的位置信息，让模型知道每个 patch 在图像中的位置。

```
z = patch_embedding + position_embedding
```

### CLS Token

在序列开头添加一个特殊的分类 token，通过自注意力聚合全局信息。

```
[CLS] [patch_1] [patch_2] ... [patch_196]
  ↓       ↓         ↓              ↓
  └───────┴─────────┴──────────────┘
            自注意力聚合
                  ↓
            分类预测
```

### Multi-Head Self-Attention

让每个 patch 能够"关注"所有其他 patches，捕获全局依赖关系。

```
Q = X @ W_Q  (查询)
K = X @ W_K  (键)
V = X @ W_V  (值)

Attention = softmax(Q @ K^T / sqrt(d_k)) @ V
```

## 训练技巧

| 技巧 | 说明 | 代码 |
|------|------|------|
| AdamW | 带权重衰减的 Adam | `optim.AdamW(lr=3e-4, weight_decay=0.01)` |
| Cosine Annealing | 余弦退火学习率调度 | `CosineAnnealingLR(T_max=epochs)` |
| Label Smoothing | 标签平滑，防止过度自信 | `CrossEntropyLoss(label_smoothing=0.1)` |
| 梯度裁剪 | 防止梯度爆炸 | `clip_grad_norm_(max_norm=1.0)` |

## 参考资料

1. [An Image is Worth 16x16 Words (Dosovitskiy et al., 2020)](https://arxiv.org/abs/2010.11929)
2. [Attention Is All You Need (Vaswani et al., 2017)](https://arxiv.org/abs/1706.03762)
3. [Training Data-Efficient Image Transformers (Touvron et al., 2021)](https://arxiv.org/abs/2012.12877)
4. [PyTorch ViT Tutorial](https://pytorch.org/tutorials/intermediate/vt_tutorial.html)
5. [Google ViT 实现](https://github.com/google-research/vision_transformer)

## 许可证

MIT License
