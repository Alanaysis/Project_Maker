# 01 - 调研文档

## 1. 项目背景

### 1.1 什么是语言模型?

语言模型 (Language Model, LM) 是自然语言处理的基础任务之一，目标是对自然语言序列的概率分布进行建模。给定一个词序列 $w_1, w_2, ..., w_n$，语言模型计算该序列出现的概率：

$$P(w_1, w_2, ..., w_n)$$

语言模型是许多 NLP 任务的核心组件：
- 文本生成
- 语音识别
- 机器翻译
- 拼写检查
- 信息检索

### 1.2 历史发展

- **1948年**：Shannon 提出用 N-gram 模型建模英文文本
- **1980年代**：N-gram 模型在语音识别中广泛应用
- **1990年代**：Kneser-Ney 平滑方法提出
- **2000年代**：神经语言模型开始出现
- **2010年代**：RNN/LSTM 语言模型
- **2017年至今**：Transformer 和预训练语言模型 (GPT, BERT)

### 1.3 应用领域

- 文本自动生成
- 语音识别系统
- 机器翻译系统
- 搜索引擎查询补全
- 拼写检查和纠错

## 2. 核心原理

### 2.1 概率链式法则

语言模型的核心是概率链式法则 (Chain Rule)：

$$P(w_1, w_2, ..., w_n) = \prod_{i=1}^{n} P(w_i | w_1, ..., w_{i-1})$$

例如，计算 "the cat sat" 的概率：

$$P(\text{the cat sat}) = P(\text{the}) \times P(\text{cat}|\text{the}) \times P(\text{sat}|\text{the cat})$$

### 2.2 马尔可夫假设

直接计算 $P(w_i | w_1, ..., w_{i-1})$ 需要极长的历史，计算和存储都不现实。N-gram 模型使用马尔可夫假设简化：

**N 阶马尔可夫假设**：当前词只依赖于前 N-1 个词

$$P(w_i | w_1, ..., w_{i-1}) \approx P(w_i | w_{i-N+1}, ..., w_{i-1})$$

| 模型 | 假设 | 公式 |
|------|------|------|
| Unigram | 词独立 | $P(w_i)$ |
| Bigram | 一阶马尔可夫 | $P(w_i \| w_{i-1})$ |
| Trigram | 二阶马尔可夫 | $P(w_i \| w_{i-2}, w_{i-1})$ |

### 2.3 概率估计

N-gram 概率通过最大似然估计 (MLE) 计算：

$$P_{MLE}(w_i | w_{i-N+1}, ..., w_{i-1}) = \frac{C(w_{i-N+1}, ..., w_i)}{C(w_{i-N+1}, ..., w_{i-1})}$$

其中 $C(\cdot)$ 表示 N-gram 在语料中的出现次数。

**示例**：计算 Bigram 概率

在语料 "the cat sat on the mat" 中：
- $C(\text{the, cat}) = 1$
- $C(\text{the}) = 2$
- $P(\text{cat}|\text{the}) = 1/2 = 0.5$

## 3. 平滑技术

### 3.1 数据稀疏问题

由于训练语料有限，许多合理的 N-gram 从未出现，导致零概率问题。

**示例**：如果 "quantum physics" 从未在训练语料中出现：
$$P_{MLE}(\text{physics}|\text{quantum}) = 0$$

这意味着包含 "quantum physics" 的任何句子概率都为零，这显然不合理。

### 3.2 Add-k 平滑 (Lidstone 平滑)

最简单的平滑方法，给每个 N-gram 计数加上一个小常数 k：

$$P_{Add-k}(w_i | context) = \frac{C(context, w_i) + k}{C(context) + k \cdot V}$$

其中 $V$ 是词汇表大小。

| k 值 | 效果 |
|------|------|
| k = 0 | 无平滑（MLE） |
| k = 0.01 | 微小平滑 |
| k = 1 | 拉普拉斯平滑 |
| k > 1 | 更强平滑 |

### 3.3 Kneser-Ney 平滑

更高级的平滑方法，考虑词的"续接能力"：

**核心思想**：一个词的概率不仅取决于它出现的频率，还取决于它能跟在多少种不同的词后面。

**低阶分布**：
$$P_{KN}(w) = \frac{|\{v : C(v, w) > 0\}|}{|\{(v', w') : C(v', w') > 0\}|}$$

Kneser-Ney 平滑是目前 N-gram 模型中最有效的平滑方法之一。

## 4. 评估指标

### 4.1 困惑度 (Perplexity)

困惑度是评估语言模型的标准指标：

$$PPL = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\log P(w_i | context)\right)$$

**直觉理解**：
- 困惑度 = 模型在每个位置上平均有多少个等可能的选择
- PPL = 1：完美模型
- PPL = V：等同于随机猜测（V 是词汇表大小）
- PPL 越低越好

**示例**：
- 英语 Unigram 模型：PPL ≈ 1000
- 英语 Bigram 模型：PPL ≈ 100
- 英语 Trigram 模型：PPL ≈ 50-100
- 人类水平：PPL ≈ 20-50

### 4.2 交叉熵 (Cross-Entropy)

$$H = -\frac{1}{N}\sum_{i=1}^{N}\log_2 P(w_i | context)$$

$$PPL = 2^H$$

交叉熵是困惑度的对数形式，更便于比较不同模型。

### 4.3 词汇覆盖率

$$\text{Coverage} = \frac{|\text{测试集词汇} \cap \text{训练集词汇}|}{|\text{测试集词汇}|}$$

词汇覆盖率反映了模型对新文本的适用程度。

## 5. N-gram 的局限性

### 5.1 长距离依赖

N-gram 模型只能捕捉 N-1 个词的上下文，无法建模长距离依赖。

**示例**：
- "The **cat** that sat on the mat **was** hungry"
- Bigram 无法捕捉 "cat" 和 "was" 之间的关系

### 5.2 数据稀疏

随着 N 增大，N-gram 的种类呈指数增长，数据稀疏问题更加严重。

| N | 可能的 N-gram 数量 (V=10000) |
|---|------------------------------|
| 1 | 10,000 |
| 2 | 100,000,000 |
| 3 | 1,000,000,000,000 |

### 5.3 泛化能力

N-gram 模型无法泛化到训练语料中未见过的模式。

## 6. 实现方案

### 6.1 技术栈

- **语言**：Python
- **依赖**：无（纯 Python 实现）
- **测试**：pytest

### 6.2 模块设计

```
src/
├── vocabulary.py     # 词汇表和分词
├── ngram.py          # N-gram 统计和概率
└── language_model.py # 统一接口
```

### 6.3 核心接口

```python
class LanguageModel:
    def train(self, texts: List[str]) -> "LanguageModel"
    def probability(self, text: str) -> float
    def perplexity(self, texts: List[str]) -> float
    def generate(self, seed: str, max_length: int) -> str
```

## 7. 风险评估

### 7.1 技术风险

- **零概率问题**：需要平滑技术处理
- **内存占用**：N-gram 计数表可能很大
- **生成质量**：简单的 N-gram 生成可能不够流畅

### 7.2 应对措施

- 实现 Add-k 平滑
- 使用 defaultdict 存储计数
- 支持温度控制改善生成质量

## 8. 参考资料

1. Jurafsky, D. & Martin, J. (2023). Speech and Language Processing
2. Manning, C. & Schuetze, H. (1999). Foundations of Statistical NLP
3. Chen, S. & Goodman, J. (1999). An Empirical Study of Smoothing Techniques
4. [N-gram - Wikipedia](https://en.wikipedia.org/wiki/N-gram)
5. [Perplexity - Wikipedia](https://en.wikipedia.org/wiki/Perplexity)
