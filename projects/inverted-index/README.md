# 倒排索引 (Inverted Index)

## 项目概述

实现一个完整的倒排索引搜索引擎，理解搜索引擎的核心数据结构。支持文档索引、布尔查询、短语查询、通配符查询和相关性排序。

## 学习目标

- 理解倒排索引的数据结构和工作原理
- 掌握文档索引构建流程（分词 -> 停用词过滤 -> 词干提取 -> 倒排表）
- 学会布尔查询处理（AND / OR / NOT）
- 理解 TF-IDF / BM25 相关性排序算法
- 掌握索引压缩技术

## 技术栈

- 语言：Python 3.8+
- 依赖：无（纯标准库实现）

## 项目结构

```
inverted-index/
├── src/
│   ├── __init__.py
│   ├── tokenizer.py        # 分词器
│   ├── stopwords.py        # 停用词过滤
│   ├── stemmer.py          # 词干提取
│   ├── lemmatizer.py       # 词形还原
│   ├── index.py            # 索引实现（倒排/位置/压缩）
│   ├── query.py            # 查询处理（布尔/短语/通配符/模糊）
│   ├── ranking.py          # 排序算法（TF-IDF/BM25）
│   └── search_engine.py    # 搜索引擎
├── tests/
│   ├── test_tokenizer.py
│   ├── test_stopwords.py
│   ├── test_stemmer.py
│   ├── test_lemmatizer.py
│   ├── test_index.py
│   ├── test_query.py
│   └── test_ranking.py
├── examples/
│   ├── basic_search.py
│   └── document_retrieval.py
├── docs/
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── requirements.txt
└── README.md
```

## 快速开始

```bash
# 进入项目目录
cd projects/inverted-index

# 运行测试
python -m pytest tests/ -v

# 运行基本搜索示例
python examples/basic_search.py

# 运行文档检索示例
python examples/document_retrieval.py
```

## 核心功能

### 1. 文档处理

```python
from src.tokenizer import Tokenizer
from src.stopwords import StopWordsFilter
from src.stemmer import PorterStemmer
from src.lemmatizer import Lemmatizer

# 分词
tokenizer = Tokenizer()
tokens = tokenizer.tokenize("Python programming language")

# 停用词过滤
filter = StopWordsFilter()
filtered = filter.filter(tokens)

# 词干提取
stemmer = PorterStemmer()
stems = stemmer.stem_tokens(filtered)

# 词形还原
lemmatizer = Lemmatizer()
lemmas = lemmatizer.lemmatize_tokens(tokens)
```

### 2. 索引构建

```python
from src.index import InvertedIndex, PositionalIndex, CompressedIndex, Document

# 基本倒排索引
index = InvertedIndex()
index.add_document(Document(
    doc_id="1",
    title="Python Programming",
    content="Python is a popular programming language"
))

# 位置索引（支持短语查询）
positional_index = PositionalIndex()
positional_index.search_phrase("programming language")

# 压缩索引
compressed_index = CompressedIndex()
compressed_index.compress()
ratio = compressed_index.get_compression_ratio()
```

### 3. 查询处理

```python
from src.query import Query

query = Query(index)

# 单词查询
results = query.search("python")

# 布尔查询
results = query.search("python AND data")
results = query.search("python OR java")
results = query.search("python NOT java")

# 短语查询
results = query.search('"machine learning"')

# 通配符查询
results = query.search("py*")

# 模糊查询
results = query.search("pythn~")
```

### 4. 排序

```python
from src.ranking import TFIDFRanker, BM25Ranker

# TF-IDF 排序
tfidf = TFIDFRanker(index)
ranked = tfidf.rank(["python", "programming"], top_k=10)

# BM25 排序
bm25 = BM25Ranker(index)
ranked = bm25.rank(["python", "programming"], top_k=10)
```

### 5. 搜索引擎

```python
from src.search_engine import SearchEngine

# 创建搜索引擎
engine = SearchEngine()

# 添加文档
engine.add_documents([
    {"doc_id": "1", "title": "Python教程", "content": "Python编程入门"},
    {"doc_id": "2", "title": "机器学习", "content": "Python机器学习实战"},
])

# 搜索
results = engine.search("python", method="bm25", top_k=5)

for r in results:
    print(f"{r.title}: {r.score:.4f}")
    print(f"  {r.snippet}")
```

## 查询语法

| 查询类型 | 语法 | 示例 |
|----------|------|------|
| 单词查询 | word | python |
| AND查询 | w1 AND w2 | python AND data |
| OR查询 | w1 OR w2 | python OR java |
| NOT查询 | NOT word | NOT java |
| 短语查询 | "phrase" | "machine learning" |
| 通配符查询 | pattern | py* |
| 模糊查询 | word~ | pythn~ |

## 排序算法

### TF-IDF
- TF (Term Frequency): 词频
- IDF (Inverse Document Frequency): 逆文档频率
- Score = TF × IDF

### BM25
- 改进的 TF-IDF
- 考虑文档长度归一化
- 词频饱和处理
- 参数: k1=1.2, b=0.75

## 参考资源

- [Inverted Index - Wikipedia](https://en.wikipedia.org/wiki/Inverted_index)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Information Retrieval - Introduction to IR](https://nlp.stanford.edu/IR-book/)
- [Porter Stemming Algorithm](https://tartarus.org/martin/PorterStemmer/)
