# 03 - 实现文档

## 1. 实现概述

本文档记录 N-gram 语言模型的实现细节，包括关键代码片段、设计决策和实现难点。

## 2. 词汇表实现

### 2.1 分词

```python
@staticmethod
def tokenize(text: str) -> List[str]:
    """简单分词：按空格分割，转换为小写"""
    return text.lower().split()
```

**实现要点**：
- 使用空格分割，简单高效
- 转换为小写，统一大小写
- 适用于英文文本，中文需要额外分词

### 2.2 词汇表构建

```python
def build(self, corpus: List[List[str]]) -> "Vocabulary":
    """从语料库构建词汇表"""
    # 统计词频
    self._token_freq = Counter()
    for sentence in corpus:
        self._token_freq.update(sentence)

    # 按词频排序，添加到词汇表
    idx = len(self.SPECIAL_TOKENS)
    for token, freq in self._token_freq.most_common():
        if freq >= self.min_freq and token not in self._token2id:
            self._token2id[token] = idx
            self._id2token[idx] = token
            idx += 1

    self._built = True
    return self
```

**实现要点**：
- 使用 Counter 统计词频
- 按词频降序排列
- 过滤低频词
- 特殊标记占前 4 个 ID

### 2.3 编码和解码

```python
def encode(self, tokens: List[str]) -> List[int]:
    """将词列表转换为ID列表"""
    unk_id = self.unk_id
    token2id = self._token2id
    return [token2id.get(t, unk_id) for t in tokens]

def decode(self, ids: List[int]) -> List[str]:
    """将ID列表转换为词列表"""
    id2token = self._id2token
    unk = self.UNK
    return [id2token.get(i, unk) for i in ids]
```

**实现要点**：
- 未知词映射到 UNK
- 使用字典查找，O(1) 复杂度

## 3. N-gram 模型实现

### 3.1 训练

```python
def train(self, corpus: List[List[str]]) -> "NGramModel":
    """训练 N-gram 模型"""
    self._ngram_counts = Counter()
    self._context_counts = Counter()
    self._vocab = set()

    for sentence in corpus:
        # 收集词汇
        self._vocab.update(sentence)

        # 添加开始和结束标记
        padded = ["<BOS>"] * (self.n - 1) + sentence + ["<EOS>"]

        # 统计 N-gram
        for i in range(len(padded) - self.n + 1):
            ngram = tuple(padded[i:i + self.n])
            context = ngram[:-1]
            self._ngram_counts[ngram] += 1
            self._context_counts[context] += 1

    self._trained = True
    return self
```

**实现要点**：
- 添加 `<BOS>` 和 `<EOS>` 标记
- 使用滑动窗口提取 N-gram
- 同时统计 N-gram 和上下文计数
- 使用 Counter 简化计数

### 3.2 概率计算

```python
def probability(self, ngram: Tuple[str, ...]) -> float:
    """计算 N-gram 的条件概率"""
    context = ngram[:-1]
    ngram_count = self._ngram_counts.get(ngram, 0)
    context_count = self._context_counts.get(context, 0)

    if self.smoothing == "none":
        if context_count == 0:
            return 0.0
        return ngram_count / context_count

    elif self.smoothing == "add_k":
        denominator = context_count + self.k * self.vocab_size
        if denominator == 0:
            return 0.0
        return (ngram_count + self.k) / denominator
```

**实现要点**：
- 支持无平滑和 Add-k 平滑
- 处理零计数情况
- 返回浮点数概率

### 3.3 困惑度计算

```python
def perplexity(self, corpus: List[List[str]]) -> float:
    """计算困惑度"""
    total_log_prob = 0.0
    total_words = 0

    for sentence in corpus:
        padded = ["<BOS>"] * (self.n - 1) + sentence + ["<EOS>"]

        for i in range(self.n - 1, len(padded)):
            ngram = tuple(padded[i - self.n + 1:i + 1])
            prob = self.probability(ngram)

            if prob <= 0:
                return float('inf')

            total_log_prob += math.log(prob)
            total_words += 1

    if total_words == 0:
        return float('inf')

    avg_log_prob = total_log_prob / total_words
    return math.exp(-avg_log_prob)
```

**实现要点**：
- 在对数空间计算，避免数值下溢
- 处理零概率情况
- 计算平均对数概率后取指数

### 3.4 文本生成

```python
def generate(self, max_length=50, temperature=1.0, seed=None):
    """生成文本"""
    # 初始化上下文
    if seed is not None:
        context = ["<BOS>"] * (self.n - 2) + [seed.lower()]
    else:
        context = ["<BOS>"] * (self.n - 1)

    generated = []

    for _ in range(max_length):
        # 获取下一个词的概率分布
        candidates = self._get_next_word_probs(
            tuple(context[-(self.n - 1):])
        )

        if not candidates:
            break

        # 应用温度
        if temperature != 1.0:
            candidates = self._apply_temperature(candidates, temperature)

        # 采样
        next_word = self._sample(candidates)

        if next_word == "<EOS>":
            break

        generated.append(next_word)
        context.append(next_word)

    return generated
```

**实现要点**：
- 支持种子词
- 支持温度控制
- 遇到 `<EOS>` 停止

### 3.5 温度采样

```python
@staticmethod
def _apply_temperature(probs, temperature):
    """应用温度参数"""
    adjusted = {}
    for word, prob in probs.items():
        adjusted[word] = math.log(prob) / temperature

    # 转换回概率空间并归一化
    max_log = max(adjusted.values())
    total = 0.0
    for word in adjusted:
        adjusted[word] = math.exp(adjusted[word] - max_log)
        total += adjusted[word]

    for word in adjusted:
        adjusted[word] /= total

    return adjusted
```

**实现要点**：
- 在对数空间应用温度
- 减去最大值避免溢出
- 归一化确保概率和为 1

### 3.6 累积分布采样

```python
@staticmethod
def _sample(probs):
    """根据概率分布采样"""
    words = list(probs.keys())
    weights = list(probs.values())

    # 归一化
    total = sum(weights)
    weights = [w / total for w in weights]

    # 累积分布采样
    r = random.random()
    cumulative = 0.0
    for word, weight in zip(words, weights):
        cumulative += weight
        if r <= cumulative:
            return word

    return words[-1]
```

**实现要点**：
- 使用累积分布函数 (CDF)
- 随机数落在哪个区间就选哪个词
- 最后一个词作为兜底

## 4. 语言模型实现

### 4.1 训练流程

```python
def train(self, texts: List[str]) -> "LanguageModel":
    """训练语言模型"""
    # 分词
    tokenized = [Vocabulary.tokenize(text) for text in texts]

    # 构建词汇表
    self.vocabulary.build(tokenized)

    # 训练 N-gram 模型
    self.ngram_model.train(tokenized)

    return self
```

### 4.2 全面评估

```python
def evaluate(self, test_texts: List[str]) -> Dict[str, float]:
    """全面评估模型"""
    ppl = self.perplexity(test_texts)

    # 计算平均句子长度
    total_words = sum(len(Vocabulary.tokenize(t)) for t in test_texts)
    avg_len = total_words / len(test_texts) if test_texts else 0

    # 计算词汇覆盖率
    test_tokens = set()
    for text in test_texts:
        test_tokens.update(Vocabulary.tokenize(text))
    train_vocab = self.ngram_model.get_vocab()
    covered = test_tokens & train_vocab
    coverage = len(covered) / len(test_tokens) if test_tokens else 0

    return {
        "perplexity": ppl,
        "avg_sentence_length": avg_len,
        "vocab_coverage": coverage,
        "test_vocab_size": len(test_tokens),
        "train_vocab_size": len(train_vocab),
    }
```

## 5. 实现难点

### 5.1 零概率问题

**问题**：未见过的 N-gram 概率为零

**解决方案**：
- Add-k 平滑：给每个计数加上 k
- 对数空间计算：避免 log(0)

### 5.2 数值下溢

**问题**：连乘很多小概率导致浮点下溢

**解决方案**：
- 使用对数空间：log(P1 * P2) = log(P1) + log(P2)
- 困惑度计算在对数空间进行

### 5.3 生成质量

**问题**：简单的 N-gram 生成可能不够流畅

**解决方案**：
- 温度控制：调节随机性
- 贪婪生成：选择最可能的词
- 增加训练数据

## 6. 测试策略

### 6.1 单元测试

- 词汇表：构建、编码、解码、特殊标记
- N-gram：训练、计数、概率、生成
- 边界条件：空输入、未训练状态

### 6.2 集成测试

- 完整训练-评估-生成流程
- 不同 N 值和参数组合
- 模型质量验证

### 6.3 测试数据

- 简单语料：验证基本功能
- 重复语料：验证计数正确性
- 新语料：验证泛化能力
