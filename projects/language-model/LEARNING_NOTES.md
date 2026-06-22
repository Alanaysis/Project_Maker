# 学习笔记 - N-gram 语言模型

## 1. 核心概念理解

### 1.1 什么是语言模型?

语言模型 (Language Model) 是对自然语言概率分布的建模。它的核心任务是：给定一个词序列，计算这个序列出现的概率。

**数学定义**：
$$P(w_1, w_2, ..., w_n)$$

**直觉理解**：
- "the cat sat on the mat" — 高概率（合理的句子）
- "cat the on sat mat the" — 低概率（不合理的句子）

语言模型回答的问题是：**这个句子有多"自然"？**

### 1.2 为什么需要 N-gram?

**问题**：直接计算 $P(w_1, w_2, ..., w_n)$ 需要统计所有可能的词序列，这是不可能的。

**解决方案**：使用马尔可夫假设，假设当前词只依赖于前 N-1 个词：

$$P(w_i | w_1, ..., w_{i-1}) \approx P(w_i | w_{i-N+1}, ..., w_{i-1})$$

```
Unigram (N=1):  P(w_i)                 — 词独立出现
Bigram (N=2):   P(w_i | w_{i-1})       — 只看前一个词
Trigram (N=3):  P(w_i | w_{i-2}, w_{i-1}) — 看前两个词
```

### 1.3 什么是困惑度?

困惑度 (Perplexity) 是衡量语言模型质量的标准指标。

**公式**：
$$PPL = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\log P(w_i | context)\right)$$

**直觉理解**：
- 困惑度 = 模型在每个位置上平均有多少个等可能的选择
- PPL = 1：完美模型，每次都猜对
- PPL = 10：模型在每个位置上"困惑"于 10 个候选词
- PPL = V (词汇表大小)：等同于随机猜测
- **PPL 越低越好**

## 2. 数学推导

### 2.1 概率链式法则

语言模型基于概率链式法则：

$$P(w_1, w_2, ..., w_n) = P(w_1) \cdot P(w_2|w_1) \cdot P(w_3|w_1,w_2) \cdots P(w_n|w_1,...,w_{n-1})$$

**示例**：
$$P(\text{the cat sat}) = P(\text{the}) \times P(\text{cat}|\text{the}) \times P(\text{sat}|\text{the cat})$$

### 2.2 最大似然估计

N-gram 概率通过最大似然估计 (MLE) 计算：

$$P_{MLE}(w_i | w_{i-N+1}, ..., w_{i-1}) = \frac{C(w_{i-N+1}, ..., w_i)}{C(w_{i-N+1}, ..., w_{i-1})}$$

**示例**：在语料 "the cat sat on the mat" 中：
- $C(\text{the, cat}) = 1$
- $C(\text{the}) = 2$
- $P(\text{cat}|\text{the}) = 1/2 = 0.5$

### 2.3 Add-k 平滑

给每个计数加上 k，避免零概率：

$$P_{Add-k}(w_i | context) = \frac{C(context, w_i) + k}{C(context) + k \cdot V}$$

**示例**：k=1, V=1000
- $C(\text{the, cat}) = 1$, $C(\text{the}) = 2$
- $P_{Add-k}(\text{cat}|\text{the}) = \frac{1+1}{2+1000} = \frac{2}{1002} \approx 0.002$

### 2.4 困惑度推导

$$PPL = \exp\left(-\frac{1}{N}\sum_{i=1}^{N}\log P(w_i|context)\right)$$

等价于：
$$PPL = \exp(H)$$

其中 H 是交叉熵：
$$H = -\frac{1}{N}\sum_{i=1}^{N}\log P(w_i|context)$$

## 3. 实现细节

### 3.1 N-gram 统计

```python
# 添加边界标记
padded = ["<BOS>"] * (n-1) + sentence + ["<EOS>"]

# 滑动窗口提取 N-gram
for i in range(len(padded) - n + 1):
    ngram = tuple(padded[i:i+n])
    context = ngram[:-1]
    ngram_counts[ngram] += 1
    context_counts[context] += 1
```

**设计决策**：
- 使用 `<BOS>` 标记句子开始
- 使用 `<EOS>` 标记句子结束
- 使用元组作为字典键

### 3.2 概率计算

```python
def probability(ngram):
    context = ngram[:-1]
    ngram_count = ngram_counts.get(ngram, 0)
    context_count = context_counts.get(context, 0)

    if smoothing == "add_k":
        return (ngram_count + k) / (context_count + k * vocab_size)
```

**设计决策**：
- 使用字典查找，O(1) 复杂度
- 支持多种平滑方法

### 3.3 困惑度计算

```python
def perplexity(corpus):
    total_log_prob = 0.0
    total_words = 0

    for sentence in corpus:
        for ngram in extract_ngrams(sentence):
            prob = probability(ngram)
            if prob <= 0:
                return float('inf')
            total_log_prob += math.log(prob)
            total_words += 1

    avg_log_prob = total_log_prob / total_words
    return math.exp(-avg_log_prob)
```

**设计决策**：
- 在对数空间计算，避免数值下溢
- 处理零概率情况

### 3.4 文本生成

```python
def generate(seed, max_length, temperature):
    context = ["<BOS>"] * (n-1) + [seed]

    for _ in range(max_length):
        # 获取下一个词的概率分布
        probs = get_next_word_probs(context)

        # 应用温度
        if temperature != 1.0:
            probs = apply_temperature(probs, temperature)

        # 采样
        next_word = sample(probs)

        if next_word == "<EOS>":
            break

        generated.append(next_word)
        context.append(next_word)
```

**设计决策**：
- 支持温度控制
- 支持种子词
- 遇到 `<EOS>` 停止

### 3.5 温度采样

```python
def apply_temperature(probs, temperature):
    # 转换到对数空间
    adjusted = {w: math.log(p) / temperature for w, p in probs.items()}

    # 转换回概率空间
    max_log = max(adjusted.values())
    adjusted = {w: math.exp(lp - max_log) for w, lp in adjusted.items()}

    # 归一化
    total = sum(adjusted.values())
    return {w: p / total for w, p in adjusted.items()}
```

**温度的作用**：
- temperature < 1.0：更确定性，选择高概率词
- temperature = 1.0：标准采样
- temperature > 1.0：更随机，探索更多可能

## 4. 调试经验

### 4.1 常见问题

**问题 1**：困惑度为 inf
- 原因：遇到零概率的 N-gram
- 解决：使用平滑技术

**问题 2**：生成的文本不连贯
- 原因：N 值太小或训练数据不足
- 解决：增大 N 或增加训练数据

**问题 3**：生成的文本总是重复
- 原因：温度太低
- 解决：增大温度

### 4.2 调试技巧

1. 打印 N-gram 计数，检查统计是否正确
2. 计算已知句子的概率，验证概率计算
3. 比较不同 N 值的困惑度
4. 可视化生成的文本质量

## 5. 性能优化

### 5.1 数据结构选择

- 使用 `Counter` 存储 N-gram 计数
- 使用 `set` 存储词汇表
- 使用字典实现 O(1) 查找

### 5.2 计算优化

- 预存上下文计数，避免重复计算
- 在对数空间计算，避免数值问题
- 使用局部变量缓存，减少属性查找

## 6. 与其他方法对比

| 方法 | 优点 | 缺点 |
|------|------|------|
| N-gram | 简单、快速、可解释 | 无法捕捉长距离依赖 |
| RNN LM | 能捕捉长距离依赖 | 训练慢、难以并行 |
| Transformer LM | 强大的建模能力 | 参数多、需要大量数据 |

## 7. 进一步学习

- [ ] Kneser-Ney 平滑
- [ ] 字符级语言模型
- [ ] 神经网络语言模型
- [ ] 预训练语言模型 (GPT, BERT)
- [ ] 语言模型在下游任务中的应用

## 8. 总结

通过从零实现 N-gram 语言模型，我深入理解了：
1. 语言模型的基本概念和数学原理
2. N-gram 统计方法和马尔可夫假设
3. 平滑技术解决数据稀疏问题
4. 困惑度作为评估指标的含义
5. 文本生成的概率采样方法

**最有价值的收获**：
- 理解了语言模型如何将"语言"转化为"概率"
- 体会了简单模型也能捕捉语言规律的美妙
- 认识到平滑技术的重要性
- 理解了困惑度的直觉含义
