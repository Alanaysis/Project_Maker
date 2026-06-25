# 语言模型 - N-gram 从零实现

从零实现 N-gram 语言模型、平滑技术、神经语言模型，以及文本生成、拼写纠错、输入法等应用。

## 学习目标

- 理解语言模型的基本概念和概率链式法则
- 掌握 N-gram 统计方法 (Unigram, Bigram, Trigram)
- 学会拉普拉斯、Good-Turing、Kneser-Ney 平滑技术
- 实现前馈神经网络、RNN、LSTM 语言模型
- 掌握困惑度 (Perplexity) 和交叉熵 (Cross-Entropy) 评估
- 实现文本生成、拼写纠错、输入法等应用

## 项目结构

```
language-model/
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
│   ├── vocabulary.py       # 词汇表模块
│   ├── ngram.py            # N-gram 模型
│   ├── language_model.py   # 语言模型接口
│   ├── smoothing.py        # 平滑技术 (Laplace/Good-Turing/Kneser-Ney)
│   ├── neural_lm.py        # 神经语言模型 (FFNN/RNN/LSTM)
│   ├── evaluation.py       # 评估指标 (困惑度/交叉熵/BLEU)
│   └── applications.py     # 应用 (文本生成/拼写纠错/输入法)
└── tests/                  # 测试
    ├── test_vocabulary.py  # 词汇表测试
    ├── test_ngram.py       # N-gram 测试
    ├── test_language_model.py # 语言模型测试
    ├── test_smoothing.py   # 平滑技术测试
    ├── test_neural_lm.py   # 神经语言模型测试
    ├── test_evaluation.py  # 评估指标测试
    └── test_applications.py # 应用测试
```

## 核心概念

### 什么是语言模型?

语言模型 (Language Model) 是对自然语言概率分布的建模。给定一个词序列 $w_1, w_2, ..., w_n$，语言模型计算该序列出现的概率：

$$P(w_1, w_2, ..., w_n)$$

### N-gram 模型

N-gram 模型基于马尔可夫假设，假设当前词只依赖于前 N-1 个词：

$$P(w_i | w_1, ..., w_{i-1}) \approx P(w_i | w_{i-N+1}, ..., w_{i-1})$$

| N-gram | 名称 | 公式 |
|--------|------|------|
| N=1 | Unigram | $P(w_i)$ |
| N=2 | Bigram | $P(w_i \| w_{i-1})$ |
| N=3 | Trigram | $P(w_i \| w_{i-2}, w_{i-1})$ |

### 平滑技术

由于数据稀疏问题，许多 N-gram 在训练语料中从未出现。平滑技术用于处理零概率问题：

| 方法 | 核心思想 | 公式 |
|------|----------|------|
| 拉普拉斯 (Add-k) | 给每个计数加 k | $P(w\|c) = \frac{C(c,w)+k}{C(c)+kV}$ |
| Good-Turing | 用 r+1 次计数重估 r 次计数 | $r^* = (r+1) \cdot N_{r+1}/N_r$ |
| Kneser-Ney | 基于词的续接能力 | $P_{KN}(w) = \|\{v:C(v,w)>0\}\| / \|\{(v',w'):C(v',w')>0\}\|$ |

### 神经语言模型

| 模型 | 架构 | 特点 |
|------|------|------|
| FFNN | 输入嵌入 -> 隐藏层 -> 输出 | Bengio et al. (2003)，学习词嵌入 |
| RNN | 循环隐藏层 | 理论上可建模任意长度上下文 |
| LSTM | 门控循环单元 | 遗忘门/输入门/输出门，解决梯度消失 |

### 评估指标

| 指标 | 公式 | 说明 |
|------|------|------|
| 困惑度 (PPL) | $\exp(-\frac{1}{N}\sum\log P(w_i))$ | 越低越好，表示模型"困惑"于多少候选词 |
| 交叉熵 (H) | $-\frac{1}{N}\sum\log_2 P(w_i)$ | PPL 的对数形式，单位为 bit |
| BLEU | $BP \cdot \exp(\sum w_n \log p_n)$ | 翻译质量评估 |

## 快速开始

### 安装依赖

```bash
pip install pytest numpy
```

### 使用示例

```python
from src.language_model import LanguageModel

# 准备训练语料
corpus = [
    "the cat sat on the mat",
    "the dog sat on the rug",
    "the cat ate the fish",
    "the dog chased the cat",
    "a cat and a dog played together",
    "the fish swam in the pond",
]

# 创建并训练模型
lm = LanguageModel(n=2, smoothing="add_k", k=1.0)
lm.train(corpus)

# 计算句子概率
log_prob = lm.probability("the cat sat on the mat")
print(f"对数概率: {log_prob:.4f}")

# 生成文本
text = lm.generate(seed="the", max_length=10, temperature=0.8)
print(f"生成文本: {text}")

# 计算困惑度
ppl = lm.perplexity(["the cat sat on the mat"])
print(f"困惑度: {ppl:.2f}")
```

### 平滑技术

```python
from src.smoothing import LaplaceSmoothing, GoodTuringSmoothing, KneserNeySmoothing

# 拉普拉斯平滑
laplace = LaplaceSmoothing(k=1.0)
prob = laplace.probability(ngram_count=2, context_count=10, vocab_size=100)

# Good-Turing 平滑
gt = GoodTuringSmoothing(k_threshold=5)
gt.fit(ngram_counts)
prob = gt.probability(ngram_count=1, context_count=10, vocab_size=100)

# Kneser-Ney 平滑
kn = KneserNeySmoothing(discount=0.75)
kn.fit(ngram_counts, context_counts, vocab)
prob = kn.probability(("the", "cat"))
```

### 神经语言模型

```python
from src.neural_lm import FeedforwardNeuralLM, LSTMLanguageModel
import numpy as np

# 前馈神经网络 LM
ffnn = FeedforwardNeuralLM(vocab_size=100, embedding_dim=32, hidden_dim=64)
contexts = np.array([[0, 1], [2, 3], [1, 0]])
targets = np.array([5, 6, 7])
loss = ffnn.train_step(contexts, targets)
ppl = ffnn.perplexity(contexts, targets)

# LSTM 语言模型
lstm = LSTMLanguageModel(vocab_size=100, embedding_dim=32, hidden_dim=64)
loss, h, c = lstm.train_step([0, 1, 2, 3], [1, 2, 3, 4])
probs, h, c = lstm.predict_proba([0, 1, 2])
```

### 评估指标

```python
from src.evaluation import EvaluationMetrics
import math

# 困惑度
ppl = EvaluationMetrics.perplexity([math.log(0.5), math.log(0.3)])

# 交叉熵
ce = EvaluationMetrics.cross_entropy([math.log(0.5), math.log(0.3)], base=2.0)

# PPL 和交叉熵的关系: PPL = 2^H
assert abs(ppl - 2 ** ce) < 1e-6

# BLEU 分数
bleu = EvaluationMetrics.bleu_score(
    ["the", "cat", "sat"],
    [["the", "cat", "sat"]])
```

### 拼写纠错

```python
from src.applications import SpellingCorrector

corrector = SpellingCorrector(lm)
corrected = corrector.correct_text("the cat st on the mat")
suggestions = corrector.suggest("cat", n=5)
```

### 输入法

```python
from src.applications import InputMethod

ime = InputMethod(lm)
candidates = ime.complete_prefix("ca", context="the", n=5)
next_words = ime.predict_next_words("the cat", n=5)
```

### 运行测试

```bash
cd projects/language-model
python3 -m pytest tests/ -v
```

## 模块概览

| 模块 | 文件 | 功能 | 测试数 |
|------|------|------|--------|
| 词汇表 | vocabulary.py | 分词、词表管理、编码解码 | 9 |
| N-gram | ngram.py | Unigram/Bigram/Trigram 统计模型 | 20 |
| 语言模型 | language_model.py | 统一接口、训练、生成、评估 | 17 |
| 平滑技术 | smoothing.py | Laplace/Good-Turing/Kneser-Ney | 19 |
| 神经语言模型 | neural_lm.py | FFNN/RNN/LSTM | 34 |
| 评估指标 | evaluation.py | PPL/Cross-Entropy/WER/BLEU | 38 |
| 应用 | applications.py | 文本生成/拼写纠错/输入法 | 18 |
| **总计** | | | **155** |

## 数学原理

### 链式法则

$$P(w_1, w_2, ..., w_n) = P(w_1) \cdot P(w_2|w_1) \cdot P(w_3|w_1,w_2) \cdots P(w_n|w_1,...,w_{n-1})$$

### 困惑度推导

$$PPL = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\log P(w_i|context)\right)$$

- PPL = 1: 完美预测
- PPL = V: 等同于随机猜测（V 是词汇表大小）

### Good-Turing 平滑

$$r^* = (r+1) \cdot \frac{N_{r+1}}{N_r}$$

其中 $N_r$ 是出现恰好 $r$ 次的 N-gram 数量。

### Kneser-Ney 平滑

$$P_{KN}(w|w_{i-1}) = \frac{\max(C(w_{i-1},w)-d,0)}{C(w_{i-1})} + \lambda(w_{i-1}) \cdot P_{KN}(w)$$

其中低阶分布基于续接概率：$P_{KN}(w) = |\{v:C(v,w)>0\}| / |\{(v',w'):C(v',w')>0\}|$

## 参考资料

- [Speech and Language Processing - Jurafsky & Martin](https://web.stanford.edu/~jurafsky/slp3/)
- [Foundations of Statistical NLP - Manning & Schuetze](https://nlp.stanford.edu/fsnlp/)
- [A Neural Probabilistic Language Model - Bengio et al. (2003)](https://www.jmlr.org/papers/volume3/bengio03a/bengio03a.pdf)
- [An Empirical Study of Smoothing Techniques - Chen & Goodman (1999)](https://arxiv.org/abs/cmp-lg/9906015)

## License

MIT

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
