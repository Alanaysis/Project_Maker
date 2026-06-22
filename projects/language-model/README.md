# 语言模型 - N-gram 从零实现

从零实现一个 N-gram 语言模型，理解语言模型的核心原理。

## 学习目标

- 理解语言模型的基本概念
- 掌握 N-gram 统计方法
- 学会困惑度 (Perplexity) 评估
- 实现完整的文本生成系统

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
│   └── language_model.py   # 语言模型接口
└── tests/                  # 测试
    ├── test_vocabulary.py  # 词汇表测试
    ├── test_ngram.py       # N-gram 测试
    └── test_language_model.py # 语言模型测试
```

## 核心概念

### 什么是语言模型?

语言模型 (Language Model) 是对自然语言概率分布的建模。给定一个词序列 $w_1, w_2, ..., w_n$，语言模型计算该序列出现的概率：

$$P(w_1, w_2, ..., w_n)$$

```
语料 → 分词 → N-gram 统计 → 概率模型 → 文本生成
```

### N-gram 模型

N-gram 模型是基于马尔可夫假设的语言模型，假设当前词只依赖于前 N-1 个词：

$$P(w_i | w_1, ..., w_{i-1}) \approx P(w_i | w_{i-N+1}, ..., w_{i-1})$$

| N-gram | 名称 | 公式 |
|--------|------|------|
| N=1 | Unigram | $P(w_i)$ |
| N=2 | Bigram | $P(w_i | w_{i-1})$ |
| N=3 | Trigram | $P(w_i | w_{i-2}, w_{i-1})$ |

### 困惑度 (Perplexity)

困惑度是衡量语言模型质量的标准指标，值越低表示模型越好：

$$PPL = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\log P(w_i | context)\right)$$

**直觉理解**：困惑度表示模型在每个位置上平均有多少个等可能的选择。困惑度为 10 表示模型在每个位置上"困惑"于 10 个候选词。

### 平滑技术

由于数据稀疏问题，许多 N-gram 在训练语料中从未出现。平滑技术用于处理零概率问题：

| 方法 | 公式 | 说明 |
|------|------|------|
| Add-k | $P(w\|c) = \frac{count(c,w) + k}{count(c) + kV}$ | 给每个计数加上 k |
| Kneser-Ney | 复杂公式 | 基于词的续接能力 |

## 快速开始

### 安装依赖

```bash
pip install pytest
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

# 贪婪生成（确定性）
text = lm.generate_greedy(seed="the", max_length=10)
print(f"贪婪生成: {text}")

# 计算困惑度
ppl = lm.perplexity(["the cat sat on the mat"])
print(f"困惑度: {ppl:.2f}")

# 全面评估
results = lm.evaluate(["the cat sat on the mat"])
print(f"评估结果: {results}")
```

### 运行测试

```bash
cd projects/language-model
python -m pytest tests/ -v
```

## 代码示例

### Unigram 模型

```python
from src.ngram import NGramModel

model = NGramModel(n=1, smoothing="add_k", k=1.0)
model.train([["the", "cat", "sat"], ["the", "dog", "ran"]])

# 词频统计
print(model.top_ngrams(5))
# [('the', 2), ('cat', 1), ('sat', 1), ...]

# 生成
words = model.generate(max_length=5)
print(" ".join(words))
```

### Bigram 模型

```python
model = NGramModel(n=2, smoothing="add_k", k=1.0)
model.train(corpus)

# 计算条件概率
prob = model.probability(("the", "cat"))
print(f"P(cat | the) = {prob:.4f}")

# 文本生成
words = model.generate(seed="the", max_length=10)
print(" ".join(words))
```

### Trigram 模型

```python
model = NGramModel(n=3, smoothing="add_k", k=1.0)
model.train(corpus)

# 困惑度评估
ppl = model.perplexity(test_corpus)
print(f"Trigram 困惑度: {ppl:.2f}")
```

### 温度控制

```python
lm = LanguageModel(n=2)
lm.train(corpus)

# 低温度：更确定性（选择高概率词）
text = lm.generate(seed="the", temperature=0.1)

# 标准温度
text = lm.generate(seed="the", temperature=1.0)

# 高温度：更随机
text = lm.generate(seed="the", temperature=2.0)
```

## 数学原理

### 链式法则

语言模型基于概率链式法则：

$$P(w_1, w_2, ..., w_n) = P(w_1) \cdot P(w_2|w_1) \cdot P(w_3|w_1,w_2) \cdots P(w_n|w_1,...,w_{n-1})$$

### 马尔可夫假设

N-gram 模型简化计算，假设当前词只依赖于前 N-1 个词：

- Unigram (N=1): $P(w_i)$ — 词独立出现
- Bigram (N=2): $P(w_i|w_{i-1})$ — 只依赖前一个词
- Trigram (N=3): $P(w_i|w_{i-2},w_{i-1})$ — 依赖前两个词

### 困惑度推导

$$PPL = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\log P(w_i|context)\right)$$

- 当 $PPL = 1$ 时，模型完美预测
- 当 $PPL = V$ (词汇表大小) 时，模型等同于随机猜测

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| n | N-gram 的 N 值 | 3 |
| smoothing | 平滑方法: "add_k", "none" | "add_k" |
| k | Add-k 平滑的 k 值 | 1.0 |
| min_freq | 最小词频 | 1 |
| max_length | 生成文本最大长度 | 50 |
| temperature | 生成温度参数 | 1.0 |

## 参考资料

- [Speech and Language Processing - Jurafsky & Martin](https://web.stanford.edu/~jurafsky/slp3/)
- [Foundations of Statistical NLP - Manning & Schuetze](https://nlp.stanford.edu/fsnlp/)
- [N-gram Language Model - Wikipedia](https://en.wikipedia.org/wiki/N-gram)

## License

MIT

---

[返回 NLP 模块](../NLP_README.md) | [返回主目录](../../README.md)
