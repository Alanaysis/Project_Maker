# Word2Vec 词向量训练

## 项目简介

实现完整的 Word2Vec 词向量训练系统，包括 CBOW 和 Skip-gram 两种模型架构，负采样和层次 Softmax 两种优化方式，以及词相似度、词类比、t-SNE 可视化等评估功能。

## 学习目标

- 理解词向量原理和分布式假设
- 掌握 CBOW 和 Skip-gram 模型架构
- 学会负采样和层次 Softmax 优化技术
- 理解降采样对训练的影响
- 使用词向量解决实际 NLP 任务

## 技术栈

- **主语言**: Python
- **框架**: 无（纯 NumPy 实现）
- **依赖**: NumPy, matplotlib (可选，用于可视化)

## 核心循环

```
语料 → 降采样 → 词频统计 → 模型训练 → 词向量 → 评估/应用
```

## 项目结构

```
word2vec/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现文档
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/                         # 源代码
│   ├── __init__.py
│   ├── vocabulary.py            # 词汇表处理
│   ├── skipgram.py              # Skip-gram 模型
│   ├── cbow.py                  # CBOW 模型
│   ├── negative_sampling.py     # 负采样
│   ├── hierarchical_softmax.py  # 层次 Softmax
│   ├── subsampling.py           # 降采样
│   ├── evaluation.py            # 评估模块
│   ├── applications.py          # 应用模块
│   ├── trainer.py               # 训练器
│   └── word2vec.py              # 主模块
├── tests/                       # 测试代码
│   ├── __init__.py
│   ├── test_vocabulary.py
│   ├── test_skipgram.py
│   ├── test_cbow.py
│   ├── test_negative_sampling.py
│   ├── test_hierarchical_softmax.py
│   ├── test_subsampling.py
│   ├── test_evaluation.py
│   ├── test_applications.py
│   └── test_word2vec.py
└── examples/                    # 示例
    ├── train_example.py         # 基础训练示例
    ├── text_classification.py   # 文本分类
    ├── sentiment_analysis.py    # 情感分析
    └── word_clustering.py       # 词聚类
```

## 快速开始

### 基础用法（Skip-gram + 负采样）

```python
from src.word2vec import Word2Vec

# 准备语料
corpus = [
    ["the", "king", "loves", "the", "queen"],
    ["the", "queen", "loves", "the", "king"],
    ["the", "prince", "is", "the", "son", "of", "the", "king"],
    ["the", "princess", "is", "the", "daughter", "of", "the", "queen"]
]

# 创建模型（默认 Skip-gram + 负采样）
model = Word2Vec(vector_size=50, window=5, min_count=1, negative=5)

# 训练
model.train(corpus, epochs=100)

# 查询相似词
similar = model.most_similar("king", topn=3)
print(similar)

# 词类比: king - man + woman = ?
result = model.analogy("king", "man")
print(result)
```

### CBOW 模型

```python
# 使用 CBOW 模型
model = Word2Vec(
    vector_size=100,
    window=5,
    min_count=1,
    model_type='cbow'  # 切换到 CBOW
)
model.train(corpus, epochs=100)
```

### 层次 Softmax

```python
# 使用层次 Softmax 优化
model = Word2Vec(
    vector_size=100,
    window=5,
    min_count=1,
    use_hs=True  # 使用层次 Softmax
)
model.train(corpus, epochs=100)
```

### 降采样

```python
# 配置降采样
model = Word2Vec(
    vector_size=100,
    window=5,
    min_count=1,
    subsample_threshold=1e-3  # 降采样阈值
)
model.train(corpus, epochs=100)
```

### 评估

```python
from src.evaluation import WordSimilarityEvaluator, AnalogyEvaluator, TSNEVisualizer

# 词相似度评估
evaluator = WordSimilarityEvaluator(model.model.W_in, model.vocab.word2idx)
sim = evaluator.cosine_similarity("king", "queen")
print(f"king - queen similarity: {sim:.4f}")

# t-SNE 可视化
visualizer = TSNEVisualizer()
words = list(model.vocab.word2idx.keys())[:50]
vectors = np.array([model.get_vector(w) for w in words])
visualizer.visualize(vectors, words, method='pca')
```

### 应用示例

```python
from src.applications import TextClassifier, SentimentAnalyzer, WordClusterer

# 文本分类
classifier = TextClassifier(model.model.W_in, model.vocab.word2idx)
classifier.train(train_sentences, train_labels)
prediction = classifier.predict(["the", "king", "rules"])

# 情感分析
analyzer = SentimentAnalyzer(model.model.W_in, model.vocab.word2idx)
analyzer.build_sentiment_lexicon(["good", "great"], ["bad", "terrible"])
result = analyzer.analyze(["this", "is", "great"])

# 词聚类
clusterer = WordClusterer(model.model.W_in, model.vocab.word2idx, model.vocab.idx2word)
clusters = clusterer.cluster(["king", "queen", "man", "woman"], k=2)
```

## 核心功能

| 功能 | 状态 | 说明 |
|------|------|------|
| Skip-gram 模型 | ✅ | 给定中心词，预测上下文词 |
| CBOW 模型 | ✅ | 给定上下文词，预测中心词 |
| 负采样 | ✅ | 将多分类转为二分类 |
| 层次 Softmax | ✅ | 使用 Huffman 树加速 |
| 降采样 | ✅ | 高频词随机丢弃 |
| 词相似度 | ✅ | 余弦相似度计算 |
| 词类比 | ✅ | king - man + woman = queen |
| t-SNE 可视化 | ✅ | PCA/t-SNE 降维可视化 |
| 文本分类 | ✅ | 基于词向量的文本分类 |
| 情感分析 | ✅ | 基于情感词典的分析 |
| 词聚类 | ✅ | K-Means 语义聚类 |
| 模型保存/加载 | ✅ | npz 格式存储 |

## 参考资料

- [Efficient Estimation of Word Representations in Vector Space](https://arxiv.org/abs/1301.3781) - Mikolov et al., 2013
- [Distributed Representations of Words and Phrases and their Compositionality](https://arxiv.org/abs/1310.4546) - Mikolov et al., 2013
- [word2vec Parameter Learning Explained](https://arxiv.org/abs/1411.2738) - Rong et al., 2014
