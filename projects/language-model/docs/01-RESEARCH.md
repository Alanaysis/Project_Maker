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
- **2003年**：Bengio 提出前馈神经网络语言模型 (FFNN LM)
- **2010年代**：RNN/LSTM 语言模型
- **2017年至今**：Transformer 和预训练语言模型 (GPT, BERT)

## 2. 核心原理

### 2.1 概率链式法则

$$P(w_1, w_2, ..., w_n) = \prod_{i=1}^{n} P(w_i | w_1, ..., w_{i-1})$$

### 2.2 马尔可夫假设

$$P(w_i | w_1, ..., w_{i-1}) \approx P(w_i | w_{i-N+1}, ..., w_{i-1})$$

| 模型 | 假设 | 公式 |
|------|------|------|
| Unigram | 词独立 | $P(w_i)$ |
| Bigram | 一阶马尔可夫 | $P(w_i \| w_{i-1})$ |
| Trigram | 二阶马尔可夫 | $P(w_i \| w_{i-2}, w_{i-1})$ |

### 2.3 概率估计

N-gram 概率通过最大似然估计 (MLE) 计算：

$$P_{MLE}(w_i | w_{i-N+1}, ..., w_{i-1}) = \frac{C(w_{i-N+1}, ..., w_i)}{C(w_{i-N+1}, ..., w_{i-1})}$$

## 3. 平滑技术

### 3.1 数据稀疏问题

由于训练语料有限，许多合理的 N-gram 从未出现，导致零概率问题。

### 3.2 拉普拉斯平滑 (Add-k)

最简单的平滑方法，给每个 N-gram 计数加上常数 k：

$$P_{Add-k}(w_i | context) = \frac{C(context, w_i) + k}{C(context) + k \cdot V}$$

| k 值 | 效果 |
|------|------|
| k = 0 | 无平滑（MLE） |
| k = 0.01 | 微小平滑 |
| k = 1 | 拉普拉斯平滑 |
| k > 1 | 更强平滑 |

### 3.3 Good-Turing 平滑

核心思想：用出现 r+1 次的 N-gram 数量来重新估计出现 r 次的 N-gram 概率。

$$r^* = (r+1) \cdot \frac{N_{r+1}}{N_r}$$

其中 $N_r$ 是出现恰好 $r$ 次的 N-gram 的数量。

**限制**：需要足够大的语料来可靠估计 $N_r$，高频计数不做调整。

### 3.4 Kneser-Ney 平滑

目前 N-gram 模型中最有效的平滑方法之一。

**核心思想**：低阶分布不是基于词频，而是基于词的"续接能力"。

$$P_{KN}(w) = \frac{|\{v : C(v, w) > 0\}|}{|\{(v', w') : C(v', w') > 0\}|}$$

**完整公式**（以 Bigram 为例）：

$$P_{KN}(w|w_{i-1}) = \frac{\max(C(w_{i-1}, w) - d, 0)}{C(w_{i-1})} + \lambda(w_{i-1}) \cdot P_{KN}(w)$$

其中 $d$ 是折扣值（通常 0.75），$\lambda$ 是归一化常数。

### 3.5 平滑方法对比

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 拉普拉斯 | 简单 | 过度平滑 | 教学、基线 |
| Good-Turing | 理论基础好 | 需要大语料 | 中等规模 |
| Kneser-Ney | 最佳效果 | 实现复杂 | 生产环境 |

## 4. 神经语言模型

### 4.1 前馈神经网络 LM (Bengio et al., 2003)

**里程碑论文**: "A Neural Probabilistic Language Model"

**架构**:
```
输入: N-1 个词的 one-hot → 词嵌入矩阵 C
隐藏层: h = tanh(C(x) @ W1 + b1)
输出层: y = softmax(h @ W2 + b2)
```

**贡献**:
- 首次引入词嵌入 (word embedding) 概念
- 自动学习词之间的语义关系
- 解决了 N-gram 的泛化问题

### 4.2 RNN 语言模型

**优势**:
- 理论上可以捕捉任意长度的上下文
- 参数在时间步之间共享
- 处理变长序列

**问题**:
- 梯度消失/爆炸
- 难以捕捉长距离依赖

### 4.3 LSTM 语言模型

**门控机制**:
- **遗忘门** (Forget Gate): 决定丢弃哪些信息
- **输入门** (Input Gate): 决定存储哪些新信息
- **输出门** (Output Gate): 决定输出哪些信息
- **记忆单元** (Cell State): 长期记忆

**优势**:
- 通过门控机制解决梯度消失
- 能更好地捕捉长距离依赖
- 在许多 NLP 任务上超越 RNN

### 4.4 神经 LM 对比

| 模型 | 上下文长度 | 训练速度 | 长距离依赖 |
|------|-----------|----------|-----------|
| FFNN | 固定 (N-1) | 快 | 差 |
| RNN | 任意 | 中 | 差 (梯度消失) |
| LSTM | 任意 | 慢 | 好 (门控) |
| Transformer | 任意 | 快 | 好 (注意力) |

## 5. 评估指标

### 5.1 困惑度 (Perplexity)

$$PPL = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\log P(w_i | context)\right)$$

**直觉理解**：困惑度表示模型在每个位置上平均有多少个等可能的选择。

| 模型 | 典型 PPL |
|------|----------|
| Unigram | ~1000 |
| Bigram | ~100 |
| Trigram | ~50-100 |
| LSTM | ~30-80 |
| Transformer | ~15-30 |

### 5.2 交叉熵 (Cross-Entropy)

$$H = -\frac{1}{N}\sum_{i=1}^{N}\log_b P(w_i | context)$$

$$PPL = b^H$$

### 5.3 BLEU 分数

用于机器翻译质量评估：
$$BLEU = BP \cdot \exp\left(\sum_{n=1}^{N} w_n \log p_n\right)$$

### 5.4 词错误率 (WER)

用于语音识别评估：WER = (S + D + I) / N

## 6. N-gram 的局限性

### 6.1 长距离依赖

N-gram 模型只能捕捉 N-1 个词的上下文，无法建模长距离依赖。

### 6.2 数据稀疏

随着 N 增大，N-gram 的种类呈指数增长。

### 6.3 泛化能力

N-gram 模型无法泛化到训练语料中未见过的模式。神经语言模型通过词嵌入解决了这个问题。

## 7. 实现方案

### 7.1 技术栈

- **语言**：Python
- **依赖**：NumPy（神经语言模型）
- **测试**：pytest

### 7.2 模块设计

```
src/
├── vocabulary.py     # 词汇表和分词
├── ngram.py          # N-gram 统计和概率
├── language_model.py # 统一接口
├── smoothing.py      # 平滑技术
├── neural_lm.py      # 神经语言模型
├── evaluation.py     # 评估指标
└── applications.py   # 应用
```

## 8. 参考资料

1. Jurafsky, D. & Martin, J. (2023). Speech and Language Processing
2. Manning, C. & Schuetze, H. (1999). Foundations of Statistical NLP
3. Bengio, Y. et al. (2003). A Neural Probabilistic Language Model
4. Chen, S. & Goodman, J. (1999). An Empirical Study of Smoothing Techniques
5. [N-gram - Wikipedia](https://en.wikipedia.org/wiki/N-gram)
6. [Perplexity - Wikipedia](https://en.wikipedia.org/wiki/Perplexity)
7. [Kneser-Ney Smoothing - Wikipedia](https://en.wikipedia.org/wiki/Kneser%E2%80%93Ney_smoothing)
