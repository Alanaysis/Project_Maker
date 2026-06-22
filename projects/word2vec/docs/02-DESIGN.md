# Word2Vec 设计文档

## 1. 架构设计

### 1.1 模块划分

```
word2vec/
├── vocabulary.py      # 词汇表管理
├── skipgram.py        # Skip-gram 模型
├── negative_sampling.py # 负采样实现
├── trainer.py         # 训练器
└── word2vec.py        # 主接口
```

### 1.2 模块依赖关系

```
word2vec.py
    ├── trainer.py
    │   ├── skipgram.py
    │   └── negative_sampling.py
    └── vocabulary.py
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
        pass
        
    def get_negative_samples(self, positive: int, k: int) -> np.ndarray:
        """获取负样本"""
        pass
```

### 2.2 SkipGramModel 类

```python
class SkipGramModel:
    """Skip-gram 模型"""
    
    def __init__(self, vocab_size: int, vector_size: int):
        self.W_in = np.random.uniform(...)  # 输入矩阵
        self.W_out = np.zeros(...)           # 输出矩阵
        
    def forward(self, center: int, context: int, negatives: np.ndarray) -> Tuple:
        """前向传播"""
        pass
        
    def backward(self, ... ) -> None:
        """反向传播"""
        pass
```

### 2.3 Trainer 类

```python
class Trainer:
    """训练器"""
    
    def __init__(self, model, vocabulary, learning_rate, negative_samples):
        pass
        
    def train(self, corpus, epochs) -> None:
        """训练模型"""
        pass
        
    def generate_training_data(self, corpus) -> List[Tuple]:
        """生成训练数据"""
        pass
```

### 2.4 Word2Vec 类

```python
class Word2Vec:
    """Word2Vec 主接口"""
    
    def __init__(self, vector_size, window, min_count, negative):
        pass
        
    def train(self, corpus, epochs) -> None:
        """训练模型"""
        pass
        
    def get_vector(self, word) -> np.ndarray:
        """获取词向量"""
        pass
        
    def most_similar(self, word, topn) -> List[Tuple]:
        """查询相似词"""
        pass
```

## 3. 数据流设计

### 3.1 训练流程

```
原始语料
    ↓
分词处理
    ↓
构建词汇表
    ↓
生成训练对 (center, context)
    ↓
负采样
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
    vector_size=100,    # 向量维度
    window=5,           # 上下文窗口大小
    min_count=5,        # 最小词频
    negative=5,         # 负样本数量
    learning_rate=0.025 # 学习率
)

model.train(
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

# 词类比
result = model.analogy("king", "man", "woman")  # -> queen
```

## 5. 存储设计

### 5.1 模型保存

```python
model.save("model.npz")
# 保存内容:
# - W_in: 输入矩阵
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
| 词不在词汇表中 | 返回 None 或抛出 KeyError |
| 训练数据不足 | 打印警告 |
| 参数不合法 | 抛出 ValueError |

## 7. 性能优化

### 7.1 内存优化

- 使用 float32 替代 float64
- 限制词汇表大小
- 批量处理训练数据

### 7.2 计算优化

- 向量化操作
- 避免 Python 循环
- 使用 NumPy 广播机制
