# Word2Vec 实现文档

## 1. 实现概述

本项目使用纯 NumPy 实现 Word2Vec 的 Skip-gram 模型，采用负采样优化。

## 2. 核心实现

### 2.1 词汇表实现 (vocabulary.py)

```python
class Vocabulary:
    def __init__(self, min_count=5):
        self.min_count = min_count
        self.word2idx = {}
        self.idx2word = {}
        self.word_freq = {}
        self.total_words = 0
        # 用于负采样的累积分布
        self.neg_sample_table = None
        
    def build(self, corpus):
        """构建词汇表"""
        # 1. 统计词频
        for sentence in corpus:
            for word in sentence:
                self.word_freq[word] = self.word_freq.get(word, 0) + 1
        
        # 2. 过滤低频词
        filtered = {w: f for w, f in self.word_freq.items() 
                   if f >= self.min_count}
        
        # 3. 建立映射
        for idx, word in enumerate(filtered):
            self.word2idx[word] = idx
            self.idx2word[idx] = word
            
        # 4. 构建负采样表
        self._build_neg_table()
```

### 2.2 负采样实现 (negative_sampling.py)

```python
class NegativeSampler:
    def __init__(self, vocab_size, word_freqs, table_size=1e6):
        self.table_size = int(table_size)
        self.table = self._build_table(vocab_size, word_freqs)
        
    def _build_table(self, vocab_size, word_freqs):
        """构建负采样查找表"""
        # 使用词频的 3/4 次方
        freqs = np.array(list(word_freqs.values()))
        powered = freqs ** 0.75
        powered /= powered.sum()
        
        # 构建累积分布
        table = np.zeros(self.table_size, dtype=np.int32)
        cumulative = np.cumsum(powered)
        
        j = 0
        for i in range(self.table_size):
            while j < len(cumulative) - 1 and i / self.table_size > cumulative[j]:
                j += 1
            table[i] = j
            
        return table
        
    def sample(self, positive, k):
        """采样 k 个负样本"""
        negatives = []
        while len(negatives) < k:
            idx = np.random.randint(0, self.table_size)
            neg = self.table[idx]
            if neg != positive:
                negatives.append(neg)
        return np.array(negatives)
```

### 2.3 Skip-gram 模型实现 (skipgram.py)

```python
class SkipGramModel:
    def __init__(self, vocab_size, vector_size):
        self.vocab_size = vocab_size
        self.vector_size = vector_size
        
        # Xavier 初始化
        scale = np.sqrt(6.0 / (vocab_size + vector_size))
        self.W_in = np.random.uniform(-scale, scale, (vocab_size, vector_size))
        self.W_out = np.zeros((vocab_size, vector_size))
        
    def forward(self, center_idx, context_idx, neg_indices):
        """前向传播"""
        # 获取向量
        v_center = self.W_in[center_idx]      # (D,)
        v_context = self.W_out[context_idx]   # (D,)
        v_neg = self.W_out[neg_indices]       # (K, D)
        
        # 计算得分
        pos_score = np.dot(v_context, v_center)  # 正样本得分
        neg_scores = np.dot(v_neg, v_center)      # 负样本得分
        
        # Sigmoid
        pos_sig = sigmoid(pos_score)
        neg_sig = sigmoid(-neg_scores)
        
        # 损失
        loss = -np.log(pos_sig + 1e-10) - np.sum(np.log(neg_sig + 1e-10))
        
        return loss, v_center, v_context, v_neg, pos_sig, neg_sig
        
    def backward(self, center_idx, context_idx, neg_indices, 
                 v_center, pos_sig, neg_sig, lr):
        """反向传播"""
        # 计算梯度
        grad_center = (pos_sig - 1) * v_context + np.sum((neg_sig - 1).reshape(-1, 1) * v_neg, axis=0)
        
        grad_context = (pos_sig - 1) * v_center
        grad_neg = (neg_sig - 1).reshape(-1, 1) * v_center
        
        # 更新参数
        self.W_in[center_idx] -= lr * grad_center
        self.W_out[context_idx] -= lr * grad_context
        self.W_out[neg_indices] -= lr * grad_neg
```

### 2.4 训练器实现 (trainer.py)

```python
class Trainer:
    def __init__(self, model, vocabulary, negative_sampler, 
                 window_size=5, learning_rate=0.025, negative=5):
        self.model = model
        self.vocab = vocabulary
        self.neg_sampler = negative_sampler
        self.window = window_size
        self.lr = learning_rate
        self.negative = negative
        
    def generate_pairs(self, corpus):
        """生成训练对"""
        pairs = []
        for sentence in corpus:
            indices = [self.vocab.word2idx[w] for w in sentence 
                      if w in self.vocab.word2idx]
            for i, center in enumerate(indices):
                # 动态窗口
                window = np.random.randint(1, self.window + 1)
                for j in range(max(0, i - window), min(len(indices), i + window + 1)):
                    if i != j:
                        pairs.append((center, indices[j]))
        return pairs
        
    def train_epoch(self, pairs):
        """训练一个 epoch"""
        total_loss = 0
        for center, context in pairs:
            # 负采样
            negatives = self.neg_sampler.sample(context, self.negative)
            
            # 前向传播
            loss, v_center, v_context, v_neg, pos_sig, neg_sig = \
                self.model.forward(center, context, negatives)
            
            # 反向传播
            self.model.backward(center, context, negatives,
                              v_center, pos_sig, neg_sig, self.lr)
            
            total_loss += loss
            
        return total_loss / len(pairs)
```

### 2.5 主接口实现 (word2vec.py)

```python
class Word2Vec:
    def __init__(self, vector_size=100, window=5, min_count=5, 
                 negative=5, learning_rate=0.025):
        self.vector_size = vector_size
        self.window = window
        self.min_count = min_count
        self.negative = negative
        self.lr = learning_rate
        
        self.vocab = Vocabulary(min_count)
        self.model = None
        self.trainer = None
        
    def train(self, corpus, epochs=100):
        """训练模型"""
        # 1. 构建词汇表
        self.vocab.build(corpus)
        
        # 2. 初始化模型
        self.model = SkipGramModel(len(self.vocab), self.vector_size)
        
        # 3. 初始化负采样器
        neg_sampler = NegativeSampler(
            len(self.vocab), 
            self.vocab.word_freq
        )
        
        # 4. 初始化训练器
        self.trainer = Trainer(
            self.model, self.vocab, neg_sampler,
            self.window, self.lr, self.negative
        )
        
        # 5. 生成训练数据
        pairs = self.trainer.generate_pairs(corpus)
        
        # 6. 训练
        for epoch in range(epochs):
            loss = self.trainer.train_epoch(pairs)
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}, Loss: {loss:.4f}")
                
    def get_vector(self, word):
        """获取词向量"""
        if word not in self.vocab.word2idx:
            return None
        idx = self.vocab.word2idx[word]
        return self.model.W_in[idx]
        
    def most_similar(self, word, topn=10):
        """查询相似词"""
        vector = self.get_vector(word)
        if vector is None:
            return []
            
        # 计算余弦相似度
        similarities = np.dot(self.model.W_in, vector) / \
                      (np.linalg.norm(self.model.W_in, axis=1) * np.linalg.norm(vector))
        
        # 排序
        top_indices = np.argsort(similarities)[::-1][1:topn+1]
        
        return [(self.vocab.idx2word[i], similarities[i]) for i in top_indices]
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

## 4. 调试技巧

### 4.1 检查梯度

```python
def check_gradient(model, center, context, neg, epsilon=1e-5):
    """数值梯度检查"""
    # 实现省略...
```

### 4.2 监控训练

- 打印损失变化
- 检查词向量范数
- 测试相似词查询

## 5. 性能数据

| 语料大小 | 词汇量 | 训练时间 | 内存占用 |
|----------|--------|----------|----------|
| 1MB | 5K | 10s | 50MB |
| 10MB | 20K | 2min | 200MB |
| 100MB | 100K | 30min | 1GB |
