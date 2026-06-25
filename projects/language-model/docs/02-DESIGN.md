# 02 - 设计文档

## 1. 架构设计

### 1.1 整体架构

```
                    +----------------------+
                    |   LanguageModel      |
                    +----------------------+
                           |
            +--------------+--------------+
            |                             |
    +-------v-------+           +--------v--------+
    |  Vocabulary   |           |   NGramModel    |
    | (vocabulary.py)|           |   (ngram.py)    |
    +----------------+           +-----------------+

    +----------------+           +-----------------+
    |  Smoothing     |           |  NeuralLM       |
    |  (smoothing.py)|           |  (neural_lm.py) |
    +----------------+           +-----------------+
    | - Laplace      |           | - FFNN          |
    | - Good-Turing  |           | - RNN           |
    | - Kneser-Ney   |           | - LSTM          |
    +----------------+           +-----------------+

    +----------------+           +-----------------+
    |  Evaluation    |           |  Applications   |
    | (evaluation.py)|           |(applications.py)|
    +----------------+           +-----------------+
    | - Perplexity   |           | - TextGenerator |
    | - CrossEntropy |           | - SpellingCorrector|
    | - BLEU/WER     |           | - InputMethod   |
    +----------------+           +-----------------+
```

### 1.2 数据流

```
原始文本列表
       │
       v
+------------------+
| Vocabulary       |
| .tokenize()      |  文本 → 词列表
| .build()         |  构建词汇表
+--------+---------+
         │
    +----+----+
    |         |
    v         v
+--------+  +-----------+
| NGram  |  | NeuralLM  |
| Model  |  | (FFNN/    |
|        |  |  RNN/LSTM) |
+---+----+  +-----+-----+
    |              |
    v              v
+------------------+
| Evaluation       |
| .perplexity()    |  困惑度评估
| .cross_entropy() |  交叉熵
+--------+---------+
         │
         v
+------------------+
| Applications     |
| .generate()      |  文本生成
| .correct()       |  拼写纠错
| .complete()      |  输入法
+------------------+
```

## 2. 模块设计

### 2.1 词汇表模块 (vocabulary.py)

**职责**：分词、词汇表管理、ID 映射

**特殊标记**：
| 标记 | ID | 用途 |
|------|----|------|
| `<PAD>` | 0 | 填充 |
| `<UNK>` | 1 | 未知词 |
| `<BOS>` | 2 | 句子开始 |
| `<EOS>` | 3 | 句子结束 |

### 2.2 N-gram 模块 (ngram.py)

**职责**：N-gram 统计、概率计算、文本生成

支持 Unigram (N=1)、Bigram (N=2)、Trigram (N=3) 以及更高阶的 N-gram。

### 2.3 平滑技术模块 (smoothing.py)

**职责**：实现多种平滑方法，解决零概率问题

| 类 | 方法 | 核心思想 |
|----|------|----------|
| `LaplaceSmoothing` | Add-k | 给每个计数加常数 k |
| `GoodTuringSmoothing` | Good-Turing | 用高频计数重估低频计数 |
| `KneserNeySmoothing` | Kneser-Ney | 基于词的续接能力 |

### 2.4 神经语言模型模块 (neural_lm.py)

**职责**：实现基于神经网络的语言模型

| 类 | 架构 | 训练 |
|----|------|------|
| `FeedforwardNeuralLM` | 嵌入拼接 → 隐藏层(tanh) → 输出(softmax) | 反向传播 |
| `RNNLanguageModel` | 嵌入 → RNN 隐藏层 → 输出(softmax) | BPTT |
| `LSTMLanguageModel` | 嵌入 → LSTM 门控层 → 输出(softmax) | BPTT |

**LSTM 门控机制**:
- 遗忘门 (Forget Gate): 决定丢弃哪些信息
- 输入门 (Input Gate): 决定存储哪些新信息
- 输出门 (Output Gate): 决定输出哪些信息

### 2.5 评估模块 (evaluation.py)

**职责**：提供语言模型评估指标

| 指标 | 说明 |
|------|------|
| 困惑度 (Perplexity) | 模型在每个位置上的平均等价选择数 |
| 交叉熵 (Cross-Entropy) | 困惑度的对数形式 |
| BPC | 每字符比特数，用于字符级模型 |
| WER | 词错误率，用于语音识别评估 |
| BLEU | 翻译质量评估 |

### 2.6 应用模块 (applications.py)

**职责**：基于语言模型的实际应用

| 类 | 应用 | 方法 |
|----|------|------|
| `TextGenerator` | 文本生成 | 随机采样、多样生成、前缀续写 |
| `SpellingCorrector` | 拼写纠错 | 编辑距离 + 语言模型排序 |
| `InputMethod` | 输入法 | 前缀补全 + 语言模型排序 |

## 3. 数据结构设计

### 3.1 N-gram 计数存储

使用 `Counter` 存储 N-gram 计数：

```python
_ngram_counts: Dict[Tuple[str, ...], int] = Counter()
# 示例: {("the", "cat"): 2, ("cat", "sat"): 1}

_context_counts: Dict[Tuple[str, ...], int] = Counter()
# 示例: {("the",): 5, ("cat",): 2}
```

### 3.2 神经网络权重

```python
# FFNN
embeddings: np.ndarray   # (vocab_size, embedding_dim)
W_hidden: np.ndarray     # (input_dim, hidden_dim)
W_output: np.ndarray     # (hidden_dim, vocab_size)

# LSTM
embeddings: np.ndarray   # (vocab_size, embedding_dim)
W: np.ndarray            # (concat_dim, 4 * hidden_dim)  -- 4 gates
W_hy: np.ndarray         # (hidden_dim, vocab_size)
```

## 4. 算法设计

### 4.1 Good-Turing 平滑

```
1. 统计频率分布 N_r = |{ngram: count(ngram) = r}|
2. 计算调整计数 r* = (r+1) * N_{r+1} / N_r
3. 使用 r* 替代原始计数计算概率
4. 对高频计数 (r > k) 不做调整
```

### 4.2 Kneser-Ney 平滑

```
1. 折扣: C'(w_{i-1}, w) = max(C(w_{i-1}, w) - d, 0)
2. 归一化: lambda = (d / C(w_{i-1})) * |{w: C(w_{i-1}, w) > 0}|
3. 低阶分布: P_KN(w) = |{v: C(v,w)>0}| / |{(v',w'): C(v',w')>0}|
4. 最终: P(w|w_{i-1}) = C'/C + lambda * P_KN(w)
```

### 4.3 LSTM 前向传播

```
for each time step t:
    concat = [x_t, h_{t-1}]
    f = sigmoid(W_f @ concat + b_f)     # 遗忘门
    i = sigmoid(W_i @ concat + b_i)     # 输入门
    g = tanh(W_g @ concat + b_g)        # 候选值
    o = sigmoid(W_o @ concat + b_o)     # 输出门
    c_t = f * c_{t-1} + i * g           # 更新记忆
    h_t = o * tanh(c_t)                 # 隐藏状态
```

### 4.4 拼写纠错算法

```
1. 生成候选词 (编辑距离 1 和 2)
2. 过滤出词汇表中的已知词
3. 使用语言模型对候选词评分
4. 返回概率最高的候选词
```

## 5. 错误处理

### 5.1 输入验证

```python
if n < 1: raise ValueError("n 必须为正整数")
if temperature <= 0: raise ValueError("temperature 必须为正数")
if discount <= 0 or discount >= 1: raise ValueError("discount 必须在 (0,1) 之间")
if not self._trained: raise RuntimeError("模型尚未训练")
```

## 6. 性能设计

### 6.1 时间复杂度

| 操作 | 复杂度 |
|------|--------|
| N-gram 训练 | O(S * L) |
| N-gram 概率计算 | O(1) |
| 生成 | O(M * V) |
| 困惑度 | O(S * L) |
| FFNN 训练 | O(B * (I*H + H*V)) |
| LSTM 训练 | O(T * (4 * (E+H) * H + H * V)) |

### 6.2 空间复杂度

- N-gram 计数：O(min(S * L, V^N))
- FFNN 权重：O(V*E + I*H + H*V)
- LSTM 权重：O(V*E + 4*(E+H)*H + H*V)

## 7. 测试设计

### 7.1 测试覆盖

| 模块 | 测试数 |
|------|--------|
| Vocabulary | 9 |
| NGramModel | 20 |
| LanguageModel | 17 |
| Smoothing | 19 |
| NeuralLM | 34 |
| Evaluation | 38 |
| Applications | 18 |
| **总计** | **155** |
