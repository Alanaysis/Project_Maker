# CLIP 实现

实现 CLIP (Contrastive Language-Image Pre-training) 对比学习模型，理解图文对齐原理。

## 项目简介

CLIP 是 OpenAI 提出的多模态学习模型，通过对比学习将图像和文本映射到同一嵌入空间。本项目实现了 CLIP 的核心架构，包括：

- **双编码器架构**：图像编码器（类 ResNet）和文本编码器（Transformer）
- **对比学习训练**：对称交叉熵损失函数
- **零样本分类**：利用图文相似度进行分类

## 项目结构

```
clip/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── clip_model.py      # CLIP 主模型
│   ├── encoders.py        # 图像/文本编码器
│   ├── contrastive_loss.py # 对比损失函数
│   ├── trainer.py         # 训练器
│   └── dataset.py         # 数据集工具
├── tests/                  # 测试
│   ├── test_clip.py
│   └── test_trainer.py
├── examples/               # 示例
│   ├── train_clip.py
│   └── zero_shot.py
├── docs/                   # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── requirements.txt
├── LEARNING_NOTES.md
└── README.md
```

## 核心概念

### CLIP 架构

```
图像输入 → 图像编码器 → 图像嵌入 ↘
                                    对比损失
文本输入 → 文本编码器 → 文本嵌入 ↗
```

### 对比学习

对比学习的核心思想是：
1. **正样本对**：匹配的图像-文本对应该有高相似度
2. **负样本对**：不匹配的图像-文本对应该有低相似度
3. **对称损失**：同时优化图像到文本和文本到图像的方向

### 零样本分类

零样本分类流程：
1. 编码测试图像得到图像嵌入
2. 编码类别描述得到文本嵌入
3. 计算图像与各类别的相似度
4. 选择相似度最高的类别作为预测结果

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行示例

```bash
# 训练示例
python examples/train_clip.py

# 零样本分类示例
python examples/zero_shot.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 代码示例

### 创建模型

```python
from src import CLIP

model = CLIP(
    embed_dim=512,
    vocab_size=10000,
    text_num_heads=8,
    text_num_layers=6,
)
```

### 前向传播

```python
import torch

# 创建输入
images = torch.randn(4, 3, 224, 224)
input_ids = torch.randint(0, 10000, (4, 77))

# 训练模式
loss, metrics = model(images, input_ids)
print(f"Loss: {loss.item():.4f}")
print(f"I2T Accuracy: {metrics['i2t_acc']:.2%}")
```

### 获取嵌入

```python
# 编码图像
image_embeddings = model.encode_image(images)

# 编码文本
text_embeddings = model.encode_text(input_ids)

# 计算相似度
similarity = model.get_similarity(images, input_ids)
```

## 学习目标

通过本项目，你将学到：

1. **CLIP 原理**：理解对比学习如何对齐视觉和语言表示
2. **双编码器架构**：掌握图像和文本编码器的设计
3. **对比损失**：理解对称交叉熵损失的工作原理
4. **零样本学习**：学会利用预训练模型进行零样本分类

## 参考资料

- [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020)
- [CLIP GitHub Repository](https://github.com/openai/CLIP)
- [Contrastive Learning Survey](https://arxiv.org/abs/2010.00747)

## License

MIT
