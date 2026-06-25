# 图像描述 (Image Captioning)

实现基于 CNN + LSTM + Attention 的图像描述生成模型，自动为图像生成文字描述。

## 项目概述

本项目实现了一个完整的图像描述生成系统，核心架构为编码器-解码器（Encoder-Decoder）模式：
- **编码器**：使用预训练 ResNet 提取图像特征
- **注意力机制**：Bahdanau (Additive) 和 Scaled Dot-Product 两种注意力
- **解码器**：LSTM 循环神经网络逐词生成描述

### 核心流程

```
图像 -> CNN编码器(ResNet) -> 特征序列 -> LSTM解码器(带注意力) -> 文字描述
```

## 目录结构

```
projects/image-captioning/
├── README.md                   # 项目说明
├── LEARNING_NOTES.md           # 学习笔记
├── docs/
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-ARCHITECTURE.md      # 架构设计
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试说明
│   └── 05-DEVELOPMENT.md       # 开发指南
├── src/
│   ├── __init__.py
│   ├── encoder.py              # CNN 编码器
│   ├── attention.py            # 注意力机制
│   ├── decoder.py              # LSTM 解码器
│   ├── model.py                # 完整模型
│   ├── vocabulary.py           # 词汇表管理
│   ├── dataset.py              # 数据集处理
│   └── trainer.py              # 训练器
├── tests/
│   ├── test_encoder.py
│   ├── test_attention.py
│   ├── test_decoder.py
│   ├── test_model.py
│   ├── test_vocabulary.py
│   └── test_dataset.py
└── examples/
    └── example.py              # 完整示例
```

## 快速开始

### 依赖

- Python 3.10+
- PyTorch 2.0+
- torchvision
- Pillow

### 运行示例

```bash
cd projects/image-captioning
python examples/example.py
```

### 运行测试

```bash
cd projects/image-captioning
python tests/test_encoder.py
python tests/test_attention.py
python tests/test_decoder.py
python tests/test_model.py
python tests/test_vocabulary.py
python tests/test_dataset.py
```

## 核心模块

### CNNEncoder (`encoder.py`)
基于预训练 ResNet 的图像特征提取器。移除最后的全连接层，输出卷积特征图序列。

### Attention (`attention.py`)
两种注意力机制实现：
- **Bahdanau (Additive)**: score = V * tanh(W_h * h + W_v * v)
- **Scaled Dot-Product**: score = Q * K^T / sqrt(d_k)

### LSTMDecoder (`decoder.py`)
LSTM 解码器，在每个时间步：
1. 词嵌入 + 上下文向量 -> LSTM 输入
2. LSTM 更新隐藏状态
3. 注意力机制计算新上下文
4. 门控机制 + 输出层预测下一个词

### ImageCaptioningModel (`model.py`)
整合编码器和解码器的完整模型，支持训练和推理两种模式。

## 学习目标

- 理解图像描述（Image Captioning）的基本原理
- 掌握编码器-解码器（Encoder-Decoder）架构
- 学会注意力机制（Attention Mechanism）的实现
- 了解 Teacher Forcing 训练策略
- 理解贪心搜索和束搜索（Beam Search）解码策略
