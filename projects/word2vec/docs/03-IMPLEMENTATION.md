# Word2Vec 实现文档

## 1. 实现概述

本项目使用纯 NumPy 实现 Word2Vec，支持：
- **模型架构**：Skip-gram 和 CBOW
- **优化方式**：负采样和层次 Softmax
- **训练技巧**：降采样、动态窗口、学习率衰减

## 2. 核心实现

### 2.1 词汇表实现 (vocabulary.py)

```python
class Vocabulary:
    def __init__(self, min_count=5):
        self.min_count = min_count
        self.word2idx = {}
        self.idx2word = {}
        self.word_freq = {}

    def build(self, corpus):
        """构建词汇表"""
        # 1. 统计词频
        counter = Counter()
        for sentence in corpus:
            counter.update(sentence)

        # 2. 过滤低频词并建立映射
        idx = 0
        for word, freq in counter.most_common():
            if freq >= self.min_count:
                self.word2idx[word] = idx
                self.idx2word[idx] = word
                self.word_freq[word] = freq
                idx += 1
```

### 2.2 Skip-gram 模型实现 (skipgram.py)

```python
class SkipGramModel:
    def __init__(self, vocab_size, vector_size):
        # Xavier 初始化
        scale = np.sqrt(6.0 / (vocab_size + vector_size))
        self.W_in = np.random.uniform(-scale, scale, (vocab_size, vector_size))
        self.W_out = np.random.uniform(-scale, scale, (vocab_size, vector_size)) * 0.01

    def forward(self, center_idx, context_idx, neg_indices):
        """前向传播"""
        v_center = self.W_in[center_idx]
        v_context = self.W_out[context_idx]
        v_neg = self.W_out[neg_indices]

        pos_score = sigmoid(np.dot(v_context, v_center))
        neg_scores = sigmoid(-np.dot(v_neg, v_center))

        loss = -np.log(pos_score + 1e-10) - np.sum(np.log(neg_scores + 1e-10))
        return loss, v_center, v_context, v_neg, pos_score, neg_scores
```

### 2.3 CBOW 模型实现 (cbow.py)

```python
class CBOWModel:
    def forward(self, context_indices, center_idx, neg_indices):
        """前向传播"""
        # 上下文词向量平均 -> 隐藏层
        context_vectors = self.W_in[context_indices]
        h = np.mean(context_vectors, axis=0)

        v_center = self.W_out[center_idx]
        v_neg = self.W_out[neg_indices]

        pos_score = sigmoid(np.dot(v_center, h))
        neg_scores = sigmoid(-np.dot(v_neg, h))

        loss = -np.log(pos_score + 1e-10) - np.sum(np.log(neg_scores + 1e-10))
        return loss, h, v_center, v_neg, pos_score, neg_scores

    def backward(self, context_indices, center_idx, neg_indices,
                 h, v_center, v_neg, pos_sig, neg_sig, lr):
        """反向传播"""
        n_context = len(context_indices)

        # 对隐藏层的梯度
        grad_h = (pos_sig - 1) * v_center + np.sum(
            (1 - neg_sig).reshape(-1, 1) * v_neg, axis=0)

        # 更新输出层
        self.W_out[center_idx] -= lr * (pos_sig - 1) * h
        self.W_out[neg_indices] -= lr * (1 - neg_sig).reshape(-1, 1) * h

        # 更新输入层（上下文词向量）
        grad_each = grad_h / n_context
        for idx in context_indices:
            self.W_in[idx] -= lr * grad_each
```

### 2.4 负采样实现 (negative_sampling.py)

```python
class NegativeSampler:
    def __init__(self, vocab_size, word_freqs, table_size=1000000):
        self.table = self._build_table(word_freqs)

    def _build_table(self, word_freqs):
        """构建负采样查找表"""
        # 使用词频的 3/4 次方
        powered = np.power(word_freqs.astype(np.float64), 0.75)
        powered /= powered.sum()

        # 构建累积分布
        table = np.zeros(self.table_size, dtype=np.int32)
        cumsum = np.cumsum(powered)

        j = 0
        for i in range(self.table_size):
            while j < len(cumsum) - 1 and i / self.table_size > cumsum[j]:
                j += 1
            table[i] = j
        return table

    def sample(self, positive, k):
        """采样 k 个负样本"""
        negatives = []
        while len(negatives) < k:
            idx = np.random.randint(0, self.table_size)
            neg = int(self.table[idx])
            if neg != positive and neg not in negatives:
                negatives.append(neg)
        return np.array(negatives, dtype=np.int32)
```

### 2.5 层次 Softmax 实现 (hierarchical_softmax.py)

```python
class HierarchicalSoftmax:
    def __init__(self, vocab_size, vector_size, word_freqs):
        # 构建 Huffman 树
        self.root, self.word_nodes = self._build_huffman_tree(word_freqs)

        # 收集内部节点
        self.inner_nodes = []
        self._collect_inner_nodes(self.root)

        # 内部节点参数
        self.W_inner = np.zeros((len(self.inner_nodes), vector_size))

        # 预计算路径
        self.word_paths = {}
        self._precompute_paths()

    def forward_backward(self, context_vector, center_idx, lr):
        """前向+反向传播"""
        path = self.word_paths[center_idx]
        loss = 0.0

        for node_idx, code in path:
            w = self.W_inner[node_idx]
            score = sigmoid(np.dot(w, context_vector))

            if code == 1:
                loss -= np.log(score + 1e-10)
                grad = (score - 1) * context_vector
            else:
                loss -= np.log(1 - score + 1e-10)
                grad = score * context_vector

            self.W_inner[node_idx] -= lr * grad

        return loss
```

### 2.6 降采样实现 (subsampling.py)

```python
class SubSampler:
    def __init__(self, word_freq, total_words, threshold=1e-3):
        self.keep_probs = {}
        for word, freq in word_freq.items():
            f = freq / total_words
            prob = (np.sqrt(f / threshold) + 1) * (threshold / f)
            self.keep_probs[word] = min(1.0, prob)

    def subsample_corpus(self, corpus):
        """对语料进行降采样"""
        result = []
        for sentence in corpus:
            subsampled = [w for w in sentence
                         if np.random.random() < self.keep_probs.get(w, 1.0)]
            if len(subsampled) > 0:
                result.append(subsampled)
        return result
```

## 3. 关键算法

### 3.1 Sigmoid 函数

```python
def sigmoid(x):
    """数值稳定的 sigmoid"""
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))
```

### 3.2 余弦相似度

```python
def cosine_similarity(v1, v2):
    """计算余弦相似度"""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
```

### 3.3 梯度裁剪

```python
def clip_gradient(grad, max_norm=5.0):
    """梯度裁剪"""
    norm = np.linalg.norm(grad)
    if norm > max_norm:
        grad = grad * (max_norm / norm)
    return grad
```

## 4. 调试技巧

### 4.1 检查梯度

```python
def check_gradient(model, center, context, neg, epsilon=1e-5):
    """数值梯度检查"""
    # 计算解析梯度
    loss, v_center, v_context, v_neg, pos_sig, neg_sig = \
        model.forward(center, context, neg)

    # 数值梯度
    grad_numerical = np.zeros_like(model.W_in[center])
    for i in range(len(grad_numerical)):
        model.W_in[center, i] += epsilon
        loss_plus, *_ = model.forward(center, context, neg)

        model.W_in[center, i] -= 2 * epsilon
        loss_minus, *_ = model.forward(center, context, neg)

        grad_numerical[i] = (loss_plus - loss_minus) / (2 * epsilon)
        model.W_in[center, i] += epsilon

    return grad_numerical
```

### 4.2 监控训练

- 打印损失变化
- 检查词向量范数
- 测试相似词查询
- 监控学习率衰减

## 5. 性能数据

| 语料大小 | 词汇量 | 模型 | 训练时间 | 内存占用 |
|----------|--------|------|----------|----------|
| 1MB | 5K | Skip-gram | 10s | 50MB |
| 1MB | 5K | CBOW | 5s | 50MB |
| 10MB | 20K | Skip-gram | 2min | 200MB |
| 100MB | 100K | Skip-gram | 30min | 1GB |
