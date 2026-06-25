# Word2Vec 设计文档

## 1. 架构设计

### 1.1 模块划分

```
word2vec/
├── vocabulary.py           # 词汇表管理
├── skipgram.py             # Skip-gram 模型
├── cbow.py                 # CBOW 模型
├── negative_sampling.py    # 负采样实现
├── hierarchical_softmax.py # 层次 Softmax
├── subsampling.py          # 降采样
├── evaluation.py           # 评估模块
├── applications.py         # 应用模块
├── trainer.py              # 训练器
└── word2vec.py             # 主接口
```

### 1.2 模块依赖关系

```
word2vec.py
    ├── trainer.py
    │   ├── skipgram.py
    │   ├── cbow.py
    │   ├── negative_sampling.py
    │   └── hierarchical_softmax.py
    ├── vocabulary.py
    └── subsampling.py

evaluation.py (独立模块)

applications.py
    └── 依赖 word_vectors 和 word2idx
```

## 2. 类设计

### 2.1 Vocabulary 类

```python
class Vocabulary:
    """词汇表管理类"""

    def __init__(self, min_count: int = 5):
        self.min_count = min_count
        self.word2idx: Dict[str, int] = {}
        self.idx2word: Dict[int, str] = {}
        self.word_freq: Dict[str, int] = {}

    def build(self, corpus: List[List[str]]) -> None:
        """构建词汇表"""

    def get_idx(self, word: str) -> Optional[int]:
        """获取词的索引"""

    def get_word(self, idx: int) -> Optional[str]:
        """获取索引对应的词"""

    def get_neg_table(self, table_size: int = 1000000) -> np.ndarray:
        """获取负采样查找表"""
```

### 2.2 SkipGramModel 类

```python
class SkipGramModel:
    """Skip-gram 模型"""

    def __init__(self, vocab_size: int, vector_size: int):
        self.W_in = np.random.uniform(...)  # 输入矩阵
        self.W_out = np.random.uniform(...) # 输出矩阵

    def forward(self, center_idx, context_idx, neg_indices) -> Tuple:
        """前向传播"""

    def backward(self, ...) -> None:
        """反向传播"""
```

### 2.3 CBOWModel 类

```python
class CBOWModel:
    """CBOW 模型"""

    def __init__(self, vocab_size: int, vector_size: int):
        self.W_in = np.random.uniform(...)  # 上下文词向量
        self.W_out = np.random.uniform(...) # 中心词向量

    def forward(self, context_indices, center_idx, neg_indices) -> Tuple:
        """前向传播：平均上下文向量 -> 预测中心词"""

    def backward(self, ...) -> None:
        """反向传播"""
```

### 2.4 NegativeSampler 类

```python
class NegativeSampler:
    """负采样器"""

    def __init__(self, vocab_size, word_freqs, table_size=1000000):
        self.table = self._build_table(word_freqs)

    def sample(self, positive: int, k: int) -> np.ndarray:
        """采样 k 个负样本"""
```

### 2.5 HierarchicalSoftmax 类

```python
class HierarchicalSoftmax:
    """层次 Softmax"""

    def __init__(self, vocab_size, vector_size, word_freqs):
        self.root, self.word_nodes = self._build_huffman_tree(word_freqs)
        self.W_inner = np.zeros(...)  # 内部节点参数

    def forward_backward(self, context_vector, center_idx, lr) -> float:
        """前向+反向传播"""
```

### 2.6 SubSampler 类

```python
class SubSampler:
    """降采样器"""

    def __init__(self, word_freq, total_words, threshold=1e-3):
        self.keep_probs = self._compute_keep_probs()

    def subsample_corpus(self, corpus) -> List[List[str]]:
        """对语料进行降采样"""
```

### 2.7 Trainer 类

```python
class Trainer:
    """训练器"""

    def __init__(self, model, vocabulary, optimizer, window, learning_rate,
                 negative, model_type, use_hs):
        pass

    def train(self, corpus, epochs) -> List[float]:
        """训练模型"""

    def generate_pairs(self, corpus) -> List[Tuple[int, int]]:
        """生成 Skip-gram 训练对"""

    def generate_cbow_data(self, corpus) -> List[Tuple[np.ndarray, int]]:
        """生成 CBOW 训练数据"""
```

### 2.8 Word2Vec 类

```python
class Word2Vec:
    """Word2Vec 主接口"""

    def __init__(self, vector_size, window, min_count, negative,
                 learning_rate, model_type, use_hs, subsample_threshold):
        pass

    def train(self, corpus, epochs) -> List[float]:
        """训练模型"""

    def get_vector(self, word) -> np.ndarray:
        """获取词向量"""

    def most_similar(self, word, topn) -> List[Tuple[str, float]]:
        """查询相似词"""

    def analogy(self, positive, negative, topn) -> List[Tuple[str, float]]:
        """词类比"""
```

## 3. 数据流设计

### 3.1 训练流程

```
原始语料
    ↓
降采样（可选）
    ↓
构建词汇表
    ↓
生成训练数据
    ├── Skip-gram: (center, context) 对
    └── CBOW: (context_indices, center) 对
    ↓
优化计算
    ├── 负采样: 采样 k 个负样本
    └── 层次 Softmax: Huffman 树路径
    ↓
前向传播
    ↓
计算损失
    ↓
反向传播
    ↓
更新参数
```

### 3.2 预测流程

```
输入词
    ↓
查找词索引
    ↓
获取词向量
    ↓
计算余弦相似度
    ↓
排序返回 TopN
```

## 4. 接口设计

### 4.1 训练接口

```python
model = Word2Vec(
    vector_size=100,         # 向量维度
    window=5,                # 上下文窗口大小
    min_count=5,             # 最小词频
    negative=5,              # 负样本数量
    learning_rate=0.025,     # 学习率
    model_type='skipgram',   # 模型类型
    use_hs=False,            # 是否使用层次 Softmax
    subsample_threshold=1e-3 # 降采样阈值
)

losses = model.train(
    corpus=tokenized_corpus,  # 分词后的语料
    epochs=100                # 训练轮数
)
```

### 4.2 查询接口

```python
# 获取词向量
vector = model.get_vector("king")

# 相似词查询
similar = model.most_similar("king", topn=10)

# 词相似度
sim = model.similarity("king", "queen")

# 词类比: king - man + woman = ?
result = model.analogy("king", "man", topn=5)
```

## 5. 存储设计

### 5.1 模型保存

```python
model.save("model.npz")
# 保存内容:
# - W_in: 输入矩阵
# - W_out: 输出矩阵
# - word2idx: 词到索引映射
# - 模型参数配置
```

### 5.2 模型加载

```python
model = Word2Vec.load("model.npz")
```

## 6. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 词汇表为空 | 抛出 ValueError |
| 词不在词汇表中 | 返回 None |
| 训练数据不足 | 打印警告 |
| 参数不合法 | 抛出 ValueError |

## 7. 性能优化

### 7.1 内存优化

- 使用 float64 保证精度
- 限制词汇表大小
- 批量处理训练数据

### 7.2 计算优化

- 向量化操作
- 避免 Python 循环
- 使用 NumPy 广播机制
- 预计算负采样查找表
- 预计算 Huffman 树路径
