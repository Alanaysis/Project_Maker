# NER 序列标注 - 命名实体识别系统

完整的命名实体识别 (NER) 系统实现，涵盖从规则方法到深度学习的多种技术方案。

## 学习目标

- 理解序列标注问题的本质和标注方案 (BIO / BIOES)
- 掌握基于规则的 NER (正则匹配、词典匹配)
- 掌握统计模型 NER (HMM、CRF)
- 掌握深度学习 NER (BiLSTM、BiLSTM-CRF)
- 实现完整的评估体系 (Accuracy、Precision、Recall、F1)

## 项目结构

```
ner/
├── README.md               # 项目说明
├── LEARNING_NOTES.md       # 学习笔记
├── docs/                   # 文档
│   ├── 01_RESEARCH.md      # 调研文档
│   ├── 02_REQUIREMENTS.md  # 需求文档
│   ├── 03_DESIGN.md        # 设计文档
│   ├── 04_PRODUCT.md       # 产品文档
│   └── 05_DEVELOPMENT.md   # 开发文档
├── src/                    # 源代码
│   ├── __init__.py         # 包初始化
│   ├── schemes.py          # 标注方案 (BIO / BIOES)
│   ├── dataset.py          # 数据处理
│   ├── hmm.py              # HMM 模型
│   ├── standalone_crf.py   # 独立 CRF 模型
│   ├── bilstm.py           # 独立 BiLSTM 模型
│   ├── crf.py              # PyTorch CRF 层
│   ├── model.py            # BiLSTM-CRF 模型
│   ├── evaluator.py        # 评估器
│   ├── trainer.py          # 训练器
│   └── rules/              # 基于规则的 NER
│       ├── __init__.py
│       ├── regex_ner.py    # 正则匹配
│       └── dict_ner.py     # 词典匹配
├── tests/                  # 测试
│   └── test_ner.py         # 测试套件
└── examples/               # 示例
    └── train.py            # 训练示例
```

## 技术方案总览

### 1. 基于规则

| 方法 | 文件 | 适用场景 |
|------|------|---------|
| 正则匹配 | `src/rules/regex_ner.py` | 日期、电话、邮箱等格式化实体 |
| 词典匹配 | `src/rules/dict_ner.py` | 已知实体集合 (人名库、地名库) |

### 2. 统计模型

| 方法 | 文件 | 特点 |
|------|------|------|
| HMM | `src/hmm.py` | 生成式模型，训练快，适合小数据 |
| CRF | `src/standalone_crf.py` | 判别式模型，可使用丰富特征 |

### 3. 深度学习

| 方法 | 文件 | 特点 |
|------|------|------|
| BiLSTM | `src/bilstm.py` | 独立预测每个位置 |
| BiLSTM-CRF | `src/model.py` + `src/crf.py` | 结合上下文和标签依赖 |

### 4. 标注方案

| 方案 | 文件 | 特点 |
|------|------|------|
| BIO | `src/schemes.py` | 简单直观，Begin/Inside/Outside |
| BIOES | `src/schemes.py` | 信息更丰富，Begin/Inside/Outside/End/Single |

### 5. 评估指标

| 指标 | 说明 |
|------|------|
| Accuracy | token 级别准确率 |
| Precision | 实体级别精确率 |
| Recall | 实体级别召回率 |
| F1 | 精确率和召回率的调和平均 |

### 6. 实体类型

| 类型 | 说明 | 示例 |
|------|------|------|
| PER | 人名 | John, 张三 |
| LOC | 地名 | New York, 北京 |
| ORG | 机构名 | Google, 清华大学 |

## 核心概念

### 序列标注

序列标注是 NLP 中的基础任务，为输入序列中的每个元素分配一个标签。

```
输入:  John  works  at  Google  in  New    York
输出:  B-PER  O     O   B-ORG  O   B-LOC  I-LOC
```

### BIO 标注方案

```
B-XXX: 实体 XXX 的开始 (Begin)
I-XXX: 实体 XXX 的内部 (Inside)
O:     非实体 (Outside)

示例:
  John lives in New York
  B-PER O O B-LOC I-LOC
```

### BIOES 标注方案

```
B-XXX: 多 token 实体的开始 (Begin)
I-XXX: 多 token 实体的内部 (Inside)
O:     非实体 (Outside)
E-XXX: 多 token 实体的结束 (End)
S-XXX: 单 token 实体 (Single)

示例:
  John lives in New    York     and Paris
  S-PER O  O  B-LOC E-LOC     O S-LOC
```

### 为什么需要 CRF?

纯 LSTM 的问题:
```
LSTM 独立预测每个位置的标签 -> 可能产生非法序列

例如:
  B-PER I-LOC  <- 非法! I-LOC 不能跟在 B-PER 后面
  B-PER I-PER  <- 合法
```

CRF 的作用:
```
CRF 学习标签之间的转移规则 -> 保证输出合法序列

转移矩阵:
         B-PER  I-PER  B-LOC  I-LOC  O
B-PER   [ 0.1   0.9   -0.5   -0.5   0.2]  <- B-PER 后面大概率是 I-PER
I-PER   [ 0.3   0.8   -0.5   -0.5   0.4]  <- I-PER 后面可以是 I-PER 或 O
B-LOC   [-0.5   0.1    0.1    0.9   0.2]  <- B-LOC 后面大概率是 I-LOC
```

### 模型架构对比

```
方法             训练难度  准确度  速度   适用场景
─────────────────────────────────────────────────
正则匹配         无需训练  高(限)  最快   格式化实体
词典匹配         无需训练  高(限)  快     已知实体集合
HMM              低        中      快     小数据集
CRF              中        较高    中     中等数据集
BiLSTM           中        较高    较慢   中大数据集
BiLSTM-CRF       高        最高    较慢   大数据集
```

## 快速开始

### 基于规则的 NER

```python
from src.rules import RegexNER, DictNER

# 正则匹配
regex_ner = RegexNER()
entities = regex_ner.recognize("请拨打 13812345678 联系我")
# [('PHONE', '13812345678', 4, 15)]

# 词典匹配
dict_ner = DictNER()
dict_ner.add_entity("北京", "LOC")
dict_ner.add_entity("清华大学", "ORG")
entities = dict_ner.recognize("我去了北京市清华大学")
```

### HMM NER

```python
from src.hmm import HMM
from src.dataset import create_sample_data

sentences, tags = create_sample_data()

hmm = HMM(smooth=1e-6)
hmm.fit(sentences, tags)

predicted = hmm.predict(["John", "works", "at", "Google"])
# ['B-PER', 'O', 'O', 'B-ORG']
```

### CRF NER

```python
from src.standalone_crf import StandaloneCRF
from src.dataset import create_sample_data

sentences, tags = create_sample_data()

crf = StandaloneCRF(learning_rate=0.01, max_iterations=50)
crf.fit(sentences, tags)

predicted = crf.predict(["John", "works", "at", "Google"])
# ['B-PER', 'O', 'O', 'B-ORG']
```

### BiLSTM-CRF NER

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

### 标注方案转换

```python
from src.schemes import (
    BIOEncoder, BIOESEncoder, bio_to_bioes, bioes_to_bio
)

# BIO 编码
bio_tags = BIOEncoder.encode([("PER", 0, 1), ("LOC", 3, 4)], 5)
# ['B-PER', 'I-PER', 'O', 'B-LOC', 'I-LOC']

# 转换为 BIOES
bioes_tags = bio_to_bioes(bio_tags)
# ['B-PER', 'E-PER', 'O', 'B-LOC', 'E-LOC']

# BIOES 解码
entities = BIOESEncoder.decode(bioes_tags)
# [('PER', 0, 1), ('LOC', 3, 4)]
```

## 数学原理

### CRF 的概率模型

给定输入序列 x 和标签序列 y:

```
P(y|x) = exp(Score(x, y)) / Z(x)

Score(x, y) = sum(emission_score(x_i, y_i)) + sum(transition_score(y_{i-1}, y_i))

Z(x) = sum_y exp(Score(x, y))  (配分函数，所有可能路径的分数和)
```

### HMM 的概率模型

```
P(X, Y) = P(y_1) * prod(P(y_t | y_{t-1})) * prod(P(x_t | y_t))

参数:
- pi: 初始概率 P(y_1)
- A:  转移概率 P(y_t | y_{t-1})
- B:  发射概率 P(x_t | y_t)
```

### 维特比解码

找到最优标签序列:

```
y* = argmax_y Score(x, y)
```

使用动态规划 (维特比算法) 高效求解。

## 运行测试

```bash
cd projects/ner
python -m pytest tests/ -v
```

## 运行训练示例

```bash
cd projects/ner
python examples/train.py
```

## 参考文献

1. **Conditional Random Fields**: Lafferty et al., 2001
2. **BiLSTM-CRF for NER**: Lample et al., 2016
3. **BERT for NER**: Devlin et al., 2019
