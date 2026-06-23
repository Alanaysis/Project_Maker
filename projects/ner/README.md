# NER 序列标注 - BiLSTM-CRF 命名实体识别

使用 BiLSTM-CRF 实现命名实体识别系统，理解序列标注的核心原理。

## 学习目标

- 理解序列标注问题的本质
- 掌握 CRF (条件随机场) 算法
- 学会 BiLSTM-CRF 架构
- 实现完整的 NER 系统

## 项目结构

```
ner/
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档
│   ├── 01-RESEARCH.md      # 调研文档
│   ├── 02-DESIGN.md        # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md       # 测试文档
│   └── 05-DEVELOPMENT.md   # 开发文档
├── src/                    # 源代码
│   ├── __init__.py         # 包初始化
│   ├── crf.py              # CRF 层实现
│   ├── model.py            # BiLSTM-CRF 模型
│   ├── dataset.py          # 数据处理
│   ├── evaluator.py        # 评估器
│   └── trainer.py          # 训练器
├── tests/                  # 测试
│   └── test_ner.py         # 测试套件
└── examples/               # 示例
    └── train.py            # 训练示例
```

## 核心概念

### 什么是序列标注?

序列标注是 NLP 中的基础任务，为输入序列中的每个元素分配一个标签。

```
输入:  John  works  at  Google  in  New    York
输出:  B-PER  O     O   B-ORG  O   B-LOC  I-LOC
```

常见应用:
- 命名实体识别 (NER)
- 词性标注 (POS Tagging)
- 分块 (Chunking)

### BIO 标注方案

```
B-XXX: 实体 XXX 的开始 (Begin)
I-XXX: 实体 XXX 的内部 (Inside)
O:     非实体 (Outside)

示例:
  John lives in New York
  B-PER O O B-LOC I-LOC
```

### 为什么需要 CRF?

纯 LSTM 的问题:
```
LSTM 独立预测每个位置的标签 → 可能产生非法序列

例如:
  B-PER I-LOC  ← 非法! I-LOC 不能跟在 B-PER 后面
  B-PER I-PER  ← 合法
```

CRF 的作用:
```
CRF 学习标签之间的转移规则 → 保证输出合法序列

转移矩阵:
         B-PER  I-PER  B-LOC  I-LOC  O
B-PER   [ 0.1   0.9   -0.5   -0.5   0.2]  ← B-PER 后面大概率是 I-PER
I-PER   [ 0.3   0.8   -0.5   -0.5   0.4]  ← I-PER 后面可以是 I-PER 或 O
B-LOC   [-0.5   0.1    0.1    0.9   0.2]  ← B-LOC 后面大概率是 I-LOC
...
```

### BiLSTM-CRF 架构

```
输入 tokens
    ↓
┌─────────────────┐
│  Embedding Layer │  将离散 token 映射为连续向量
└────────┬────────┘
         ↓
┌─────────────────┐
│   BiLSTM Layer  │  捕获上下文信息 (前向 + 后向)
└────────┬────────┘
         ↓
┌─────────────────┐
│   Linear Layer  │  映射到标签空间 (发射分数)
└────────┬────────┘
         ↓
┌─────────────────┐
│    CRF Layer    │  建模标签转移关系
└────────┬────────┘
         ↓
输出标签序列
```

## 快速开始

```python
import torch
from src.model import BiLSTM_CRF
from src.dataset import Vocabulary, TagVocabulary, create_sample_data

# 准备数据
sentences, tags = create_sample_data()
vocab = Vocabulary()
vocab.build(sentences)
tag_vocab = TagVocabulary()
tag_vocab.build(tags)

# 创建模型
model = BiLSTM_CRF(
    vocab_size=len(vocab),
    num_tags=len(tag_vocab),
    embedding_dim=64,
    hidden_dim=128
)

# 训练...
```

## 核心循环

```
文本 → 编码 → 序列标注 → 实体提取
```

## 数学原理

### CRF 的概率模型

给定输入序列 x 和标签序列 y:

```
P(y|x) = exp(Score(x, y)) / Z(x)

Score(x, y) = Σ emission_score(x_i, y_i) + Σ transition_score(y_{i-1}, y_i)

Z(x) = Σ_y exp(Score(x, y))  (配分函数，所有可能路径的分数和)
```

### 训练目标

最大化正确标签序列的对数似然:

```
L = log P(y*|x) = Score(x, y*) - log Z(x)
```

### 维特比解码

找到最优标签序列:

```
y* = argmax_y Score(x, y)
```

使用动态规划 (维特比算法) 高效求解。
