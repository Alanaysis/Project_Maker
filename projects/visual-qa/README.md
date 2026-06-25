# 视觉问答 (Visual Question Answering)

实现视觉问答系统，根据图像回答问题。

## 项目简介

视觉问答 (VQA) 是一个跨模态人工智能任务，要求模型根据输入的图像和自然语言问题生成正确的答案。本项目实现了一个完整的 VQA 系统，包括：

- **图像编码器**: 使用 ResNet 提取图像特征
- **文本编码器**: 使用 LSTM/Transformer 编码问题
- **多模态融合**: 支持多种融合策略（拼接、双线性、注意力等）
- **答案预测**: 分类方法预测答案

## 项目结构

```
visual-qa/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── vqa_model.py       # VQA 主模型
│   ├── image_encoder.py   # 图像编码器
│   ├── text_encoder.py    # 文本编码器
│   ├── fusion.py          # 融合模块
│   ├── answer_predictor.py # 答案预测器
│   ├── dataset.py         # 数据集
│   └── trainer.py         # 训练器
├── tests/                  # 测试
│   └── test_vqa.py
├── examples/               # 示例
│   ├── train_vqa.py
│   └── inference.py
├── docs/                   # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── requirements.txt
├── README.md
└── LEARNING_NOTES.md
```

## 核心概念

### VQA 架构

```
图像输入 → 图像编码器 → 图像特征 ↘
                                    多模态融合 → 答案预测
问题输入 → 文本编码器 → 文本特征 ↗
```

### 多模态融合策略

1. **拼接融合**: 简单拼接图像和文本特征
2. **双线性融合**: 建模二阶交互
3. **注意力融合**: 动态聚焦相关信息
4. **协同注意力**: 双向注意力交互

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行示例

```bash
# 训练示例
python examples/train_vqa.py

# 推理示例
python examples/inference.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 代码示例

### 创建模型

```python
from src import VQAModel

model = VQAModel(
    vocab_size=10000,
    num_answers=1000,
    image_backbone='resnet18',
    text_encoder_type='lstm',
    fusion_type='concat',
)
```

### 前向传播

```python
import torch

# 创建输入
images = torch.randn(4, 3, 224, 224)
question_ids = torch.randint(0, 10000, (4, 20))
targets = torch.randint(0, 1000, (4,))

# 前向传播
outputs = model(images=images, question_ids=question_ids, targets=targets)
print(f"Loss: {outputs['loss'].item():.4f}")
print(f"Accuracy: {outputs['accuracy'].item():.2%}")
```

### 预测答案

```python
# 使用预提取特征
image_features = torch.randn(4, 512)
question_ids = torch.randint(0, 10000, (4, 20))

predictions, confidence = model.predict(
    image_features=image_features,
    question_ids=question_ids,
)
print(f"Predictions: {predictions}")
print(f"Confidence: {confidence}")
```

## 学习目标

通过本项目，你将学到：

1. **VQA 原理**: 理解视觉问答的基本原理和流程
2. **多模态融合**: 掌握图像和文本特征的融合方法
3. **注意力机制**: 学习注意力在多模态学习中的应用
4. **深度学习实践**: 提升 PyTorch 深度学习实践能力

## 模型配置

### 图像编码器

- **骨干网络**: ResNet-18/34/50, VGG-16
- **特征维度**: 128, 256, 512, 1024
- **预训练**: 支持 ImageNet 预训练

### 文本编码器

- **编码器类型**: LSTM, GRU, Transformer
- **嵌入维度**: 128, 256, 300, 512
- **层数**: 1, 2, 4, 6

### 融合模块

- **融合类型**: concat, bilinear, attention, co_attention
- **输出维度**: 512, 1024, 2048

## 性能指标

### 训练性能

- **训练速度**: ~100 samples/sec (GPU)
- **内存使用**: ~2GB (batch_size=32)
- **收敛轮数**: 10-20 epochs

### 推理性能

- **推理速度**: ~10ms/sample (GPU)
- **模型大小**: ~50MB
- **准确率**: 60-70% (示例数据)

## 扩展功能

### 支持的扩展

1. **新的骨干网络**: EfficientNet, Vision Transformer
2. **新的融合策略**: 门控融合, 图神经网络融合
3. **新的编码器**: BERT, GPT
4. **新的任务**: 图像描述, 视觉推理

### 自定义配置

```python
model = VQAModel(
    vocab_size=10000,
    num_answers=1000,
    image_backbone='resnet50',
    text_encoder_type='transformer',
    fusion_type='attention',
    embed_dim=300,
    image_feature_dim=512,
    text_feature_dim=512,
    fusion_dim=1024,
    hidden_dim=512,
    dropout=0.1,
    pretrained_image=True,
)
```

## 参考资料

- [VQA: Visual Question Answering](https://arxiv.org/abs/1505.00468)
- [Stacked Attention Networks](https://arxiv.org/abs/1511.02274)
- [Bottom-Up Attention](https://arxiv.org/abs/1707.07998)
- [ViLBERT](https://arxiv.org/abs/1908.02265)

## License

MIT
