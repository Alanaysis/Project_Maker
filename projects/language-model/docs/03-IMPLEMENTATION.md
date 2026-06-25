# 03 - 实现文档

## 1. 实现概述

本文档记录语言模型的实现细节，包括 N-gram 模型、平滑技术、神经语言模型、评估指标和应用模块。

## 2. 词汇表实现

### 2.1 分词

```python
@staticmethod
def tokenize(text: str) -> List[str]:
    return text.lower().split()
```

### 2.2 词汇表构建

使用 `Counter` 统计词频，按词频降序排列，过滤低频词，特殊标记占前 4 个 ID。

## 3. N-gram 模型实现

### 3.1 训练

添加 `<BOS>` 和 `<EOS>` 标记，使用滑动窗口提取 N-gram，同时统计 N-gram 和上下文计数。

### 3.2 概率计算

支持无平滑和 Add-k 平滑，处理零计数情况。

### 3.3 困惑度计算

在对数空间计算，避免数值下溢。PPL = exp(-avg_log_prob)。

### 3.4 文本生成

支持种子词、温度控制。温度在对数空间应用，减去最大值避免溢出，归一化确保概率和为 1。

## 4. 平滑技术实现

### 4.1 拉普拉斯平滑 (LaplaceSmoothing)

```python
P(w|c) = (C(c,w) + k) / (C(c) + k * V)
```

最简单的平滑方法。k=1 为标准拉普拉斯平滑。

### 4.2 Good-Turing 平滑 (GoodTuringSmoothing)

```python
r_star = (r + 1) * N_{r+1} / N_r
```

核心步骤：
1. 统计频率分布 N_r（出现恰好 r 次的 N-gram 数量）
2. 计算调整计数 r* = (r+1) * N_{r+1} / N_r
3. 使用 r* 替代原始计数
4. 对高频计数 (r > k_threshold) 不做调整，避免稀疏数据导致的不稳定

### 4.3 Kneser-Ney 平滑 (KneserNeySmoothing)

```python
P_KN(w|w_{i-1}) = max(C(w_{i-1},w) - d, 0) / C(w_{i-1}) + lambda * P_continuation(w)
```

核心思想：低阶分布基于词的"续接能力"而非词频。
- P_continuation(w) = |{v: C(v,w)>0}| / |{(v',w'): C(v',w')>0}|
- 折扣 d 通常取 0.75

## 5. 神经语言模型实现

### 5.1 前馈神经网络 (FeedforwardNeuralLM)

基于 Bengio et al. (2003) 的经典架构：

```
输入: N-1 个词的嵌入拼接
  → 隐藏层 (tanh 激活)
  → 输出层 (softmax)
```

**前向传播**:
1. 查找词嵌入并拼接: x = [emb(w1), emb(w2), ..., emb(w_{N-1})]
2. 隐藏层: h = tanh(x @ W_hidden + b_hidden)
3. 输出层: y = softmax(h @ W_output + b_output)

**反向传播**:
1. 输出层梯度: d_y = probs - one_hot(target)
2. 隐藏层梯度: d_h = (d_y @ W_output.T) * tanh'(z_hidden)
3. 嵌入梯度: 通过 d_x 传播到对应的嵌入向量

### 5.2 RNN 语言模型 (RNNLanguageModel)

```
输入词嵌入 → RNN 隐藏层 → 输出层 (softmax)
```

**RNN 更新**:
```
h_t = tanh(x_t @ W_xh + h_{t-1} @ W_hh + b_h)
y_t = softmax(h_t @ W_hy + b_y)
```

**BPTT 训练**:
- 从最后一个时间步向前传播梯度
- 梯度裁剪 (-5, 5) 防止梯度爆炸

### 5.3 LSTM 语言模型 (LSTMLanguageModel)

```
输入词嵌入 → LSTM 门控层 → 输出层 (softmax)
```

**LSTM 单步计算**:
```python
concat = [x_t, h_{t-1}]
f = sigmoid(concat @ W[:, :H] + b[:H])           # 遗忘门
i = sigmoid(concat @ W[:, H:2H] + b[H:2H])       # 输入门
g = tanh(concat @ W[:, 2H:3H] + b[2H:3H])        # 候选值
o = sigmoid(concat @ W[:, 3H:4H] + b[3H:4H])     # 输出门
c_t = f * c_{t-1} + i * g                          # 更新记忆
h_t = o * tanh(c_t)                                 # 隐藏状态
```

**设计要点**:
- 遗忘门偏置初始化为 1.0，帮助学习长期依赖
- 4 个门共享一个权重矩阵 W，减少参数量
- BPTT 反向传播通过时间展开

## 6. 评估指标实现

### 6.1 困惑度 (Perplexity)

```python
PPL = exp(-1/N * sum(log P(w_i | context)))
```

### 6.2 交叉熵 (Cross-Entropy)

```python
H = -1/N * sum(log_b P(w_i | context))
PPL = b^H
```

支持任意底数（默认 base=2，单位为 bit）。

### 6.3 BLEU 分数

```python
BLEU = BP * exp(sum(w_n * log p_n))
```

- BP: Brevity Penalty，惩罚过短的翻译
- p_n: n-gram 精度
- 跳过无法提取的 n-gram 阶数

### 6.4 词错误率 (WER)

使用编辑距离（动态规划）计算：WER = (S + D + I) / N

## 7. 应用实现

### 7.1 拼写纠错 (SpellingCorrector)

```
1. 生成候选词:
   - 编辑距离 1: 删除、交换、替换、插入
   - 编辑距离 2: 两次编辑距离 1 操作
2. 过滤出词汇表中的已知词
3. 使用语言模型对候选词评分
4. 返回概率最高的候选词
```

优先返回已知词 > 编辑距离 1 > 编辑距离 2。

### 7.2 输入法 (InputMethod)

```
1. 前缀补全: 找到以输入前缀开头的所有词
2. 使用语言模型对候选词排序
3. 支持上下文感知的预测
```

## 8. 实现难点

### 8.1 零概率问题
- 平滑技术避免零概率
- 对数空间计算避免 log(0)

### 8.2 数值下溢
- 连乘小概率导致浮点下溢
- 解决: 对数空间计算

### 8.3 梯度消失/爆炸
- RNN 中长序列的梯度问题
- 解决: LSTM 门控机制 + 梯度裁剪

### 8.4 LSTM 维度匹配
- 拼接向量 [x, h] 的维度分割需注意 embedding_dim 与 hidden_dim 的区别
- 反向传播中 d_concat 的前 embedding_dim 维是输入梯度，后 hidden_dim 维是隐藏状态梯度
