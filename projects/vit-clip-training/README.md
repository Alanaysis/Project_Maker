# ViT/CLIP 模型训练框架

## 项目简介

本项目实现了一个完整的 Vision Transformer (ViT) 和 CLIP 对比学习训练框架。通过这个项目，你将深入理解：

- **Vision Transformer 架构**：如何将图像分割为 patch 并使用 Transformer 处理
- **对比学习**：如何通过对比损失函数学习图像和文本的对齐表示
- **多模态对齐**：如何将不同模态（图像和文本）映射到共享的嵌入空间

## 学习目标

### 核心知识

1. **Vision Transformer (ViT)**
   - Patch Embedding：将图像分割为固定大小的 patch
   - Position Embedding：为每个 patch 添加位置信息
   - Transformer Encoder：使用自注意力机制处理 patch 序列
   - [CLS] Token：聚合全局图像信息

2. **对比学习 (Contrastive Learning)**
   - InfoNCE Loss：CLIP 使用的对比损失函数
   - 温度参数 τ：控制 softmax 分布的锐度
   - 对称损失：同时优化图像到文本和文本到图像的方向

3. **CLIP 架构**
   - 双编码器设计：图像编码器 + 文本编码器
   - 共享嵌入空间：将不同模态映射到同一空间
   - 零样本分类：无需微调即可分类

### 学习难度标注

| 模块 | 难度 | 说明 |
|------|------|------|
| Patch Embedding | ⭐⭐ | 理解图像如何转换为序列 |
| Self-Attention | ⭐⭐⭐ | 核心机制，需要深入理解 |
| 对比损失 | ⭐⭐⭐ | 理解正负样本的定义 |
| CLIP 训练 | ⭐⭐⭐⭐ | 大规模训练的工程挑战 |
| 零样本分类 | ⭐⭐⭐⭐⭐ | 理解模型的泛化能力 |

## 技术栈

- **Python** 3.8+
- **PyTorch** 2.0+
- **torchvision**：图像处理和数据增强
- **transformers**：预训练模型和 tokenizer
- **numpy**：数值计算
- **pytest**：单元测试

## 项目结构

```
vit-clip-training/
├── README.md                    # 项目说明
├── requirements.txt             # 依赖列表
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-REQUIREMENTS.md      # 需求分析
│   ├── 03-DESIGN.md            # 技术设计
│   ├── 04-PRODUCT.md           # 产品思维
│   └── 05-DEVELOPMENT.md       # 开发手册
├── src/                         # 源代码
│   ├── __init__.py
│   ├── models/                  # 模型实现
│   │   ├── vit.py              # Vision Transformer
│   │   ├── text_encoder.py     # 文本编码器
│   │   └── clip.py             # CLIP 模型
│   ├── losses/                  # 损失函数
│   │   └── contrastive.py      # 对比损失
│   ├── data/                    # 数据处理
│   │   └── dataset.py          # 数据集实现
│   ├── training/                # 训练逻辑
│   │   └── trainer.py          # 训练器
│   └── utils/                   # 工具函数
│       └── metrics.py          # 评估指标
├── tests/                       # 单元测试
│   ├── test_vit.py
│   ├── test_clip.py
│   └── test_contrastive.py
├── examples/                    # 使用示例
│   ├── train_clip.py           # 训练示例
│   └── evaluate.py             # 评估示例
└── LEARNING_NOTES.md            # 学习笔记
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_vit.py -v
```

### 3. 运行训练示例

```bash
python examples/train_clip.py
```

### 4. 运行评估示例

```bash
python examples/evaluate.py
```

## 核心代码解析

### Vision Transformer (ViT)

```python
# ⭐ 关键创新：将图像视为 patch 序列
class PatchEmbedding(nn.Module):
    def forward(self, x):
        # x: (B, C, H, W) -> (B, num_patches, embed_dim)
        x = self.projection(x)  # 卷积提取 patch
        x = x.flatten(2).transpose(1, 2)  # 展平
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)  # 添加 CLS token
        x = x + self.position_embedding  # 添加位置编码
        return x
```

### CLIP 对比损失

```python
# ⭐ 对称对比损失
def clip_loss(image_features, text_features):
    # 计算相似度矩阵
    logits = image_features @ text_features.T / temperature

    # 对称损失
    labels = torch.arange(batch_size)
    loss_i2t = cross_entropy(logits, labels)
    loss_t2i = cross_entropy(logits.T, labels)

    return (loss_i2t + loss_t2i) / 2
```

## 重点难点

### ⭐ 重点

1. **Patch Embedding 的设计**
   - 为什么使用卷积实现 patch 提取？
   - 位置编码的作用是什么？
   - [CLS] token 如何聚合信息？

2. **自注意力机制**
   - Query, Key, Value 的含义
   - 注意力分数的计算
   - 多头注意力的优势

3. **对比学习的正负样本**
   - 正样本：匹配的图像-文本对
   - 负样本：batch 内其他样本
   - 温度参数的影响

### 💡 值得思考

1. **为什么 CLIP 使用因果掩码而不是双向注意力？**
   - 提示：考虑文本生成的需求

2. **大 batch size 为什么对对比学习很重要？**
   - 提示：考虑负样本的数量

3. **温度参数 τ 如何影响训练？**
   - 提示：考虑 softmax 分布的锐度

4. **CLIP 的零样本能力从何而来？**
   - 提示：考虑语言的泛化能力

## 相关资源

### 论文

- [An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale](https://arxiv.org/abs/2010.11929) - ViT 原论文
- [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020) - CLIP 原论文
- [Emerging Properties in Self-Supervised Vision Transformers](https://arxiv.org/abs/2104.14296) - DINO 论文

### 开源项目

- [OpenCLIP](https://github.com/mlfoundations/open_clip) - 开源 CLIP 实现
- [DINO](https://github.com/facebookresearch/dino) - 自监督 ViT 训练
- [timm](https://github.com/huggingface/pytorch-image-models) - PyTorch 图像模型库

### 教程和博客

- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) - Transformer 可视化讲解
- [ViT Paper Explained](https://www.youtube.com/watch?v=TrdevFK_am4) - ViT 论文解读
- [CLIP Paper Explained](https://www.youtube.com/watch?v=T9hPdK16scQ) - CLIP 论文解读

## 值得学习的地方

1. **架构设计思维**
   - 如何将 CNN 的归纳偏置与 Transformer 结合
   - 如何设计多模态对齐的架构

2. **工程实践**
   - 混合精度训练
   - 梯度累积
   - 学习率调度

3. **评估方法**
   - 检索评估指标
   - 零样本分类评估
   - 表示质量分析

## 下一步学习

完成本项目后，建议继续学习：

1. **DINOv2**：改进的自监督 ViT 训练
2. **BLIP/BLIP-2**：更先进的多模态模型
3. **Stable Diffusion**：基于 CLIP 的生成模型
4. **LLaVA**：大型语言-视觉模型

## 许可证

本项目仅供学习使用。
