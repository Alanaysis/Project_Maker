# Word2Vec 词向量训练

## 项目简介

实现 Word2Vec 词向量训练，包括 Skip-gram 模型、负采样优化、词向量训练和相似词查询功能。

## 学习目标

- 理解词向量原理
- 掌握 Skip-gram/CBOW 模型架构
- 学会负采样优化技术

## 技术栈

- **主语言**: Python
- **框架**: 无（纯 NumPy 实现）
- **依赖**: NumPy

## 核心循环

```
语料 → 词频统计 → 模型训练 → 词向量
```

## 项目结构

```
word2vec/
├── README.md                 # 项目说明
├── LEARNING_NOTES.md         # 学习笔记
├── docs/                     # 文档目录
│   ├── 01-RESEARCH.md       # 调研文档
│   ├── 02-DESIGN.md         # 设计文档
│   ├── 03-IMPLEMENTATION.md # 实现文档
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发文档
├── src/                      # 源代码
│   ├── __init__.py
│   ├── vocabulary.py         # 词汇表处理
│   ├── skipgram.py           # Skip-gram 模型
│   ├── negative_sampling.py  # 负采样
│   ├── trainer.py            # 训练器
│   └── word2vec.py           # 主模块
├── tests/                    # 测试代码
│   ├── __init__.py
│   ├── test_vocabulary.py
│   ├── test_skipgram.py
│   ├── test_negative_sampling.py
│   └── test_word2vec.py
└── examples/                 # 示例
    └── train_example.py
```

## 快速开始

```python
from src.word2vec import Word2Vec

# 准备语料
corpus = [
    "the king loves the queen",
    "the queen loves the king",
    "the prince is the son of the king",
    "the princess is the daughter of the queen"
]

# 创建模型
model = Word2Vec(vector_size=50, window=5, min_count=1, negative=5)

# 训练
model.train(corpus, epochs=100)

# 查询相似词
similar = model.most_similar("king", topn=3)
print(similar)
```

## 最小可用版本

- [x] 实现 Skip-gram 模型
- [x] 实现负采样
- [x] 词向量训练
- [x] 相似词查询

## 参考资料

- [Efficient Estimation of Word Representations in Vector Space](https://arxiv.org/abs/1301.3781)
- [Distributed Representations of Words and Phrases and their Compositionality](https://arxiv.org/abs/1310.4546)
