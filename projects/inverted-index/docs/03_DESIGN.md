# 03 - 设计文档

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      SearchEngine                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Tokenizer│→ │ StopWords│→ │ Stemmer  │→ │ Indexer  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                          ↓  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Results  │← │ Ranker   │← │ Query    │← │ Index    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 2. 模块设计

### 2.1 核心模块

```
src/
├── tokenizer.py        # 分词器
├── stopwords.py        # 停用词过滤
├── stemmer.py          # 词干提取
├── lemmatizer.py       # 词形还原
├── index.py            # 索引实现
│   ├── InvertedIndex   # 基本倒排索引
│   ├── PositionalIndex # 位置索引
│   └── CompressedIndex # 压缩索引
├── query.py            # 查询处理
│   ├── QueryParser     # 查询解析器
│   └── QueryExecutor   # 查询执行器
├── ranking.py          # 排序算法
│   ├── TFIDFRanker     # TF-IDF排序
│   └── BM25Ranker      # BM25排序
└── search_engine.py    # 搜索引擎
    ├── SearchEngine    # 完整搜索引擎
    └── SimpleSearchEngine # 简化版
```

### 2.2 数据结构

#### Document（文档）
```python
@dataclass
class Document:
    doc_id: str          # 文档ID
    title: str           # 标题
    content: str         # 内容
    metadata: Dict       # 元数据
```

#### PostingEntry（倒排列表条目）
```python
@dataclass
class PostingEntry:
    doc_id: str          # 文档ID
    term_frequency: int  # 词频
    positions: List[int] # 位置列表
```

#### QueryNode（查询节点）
```python
@dataclass
class QueryNode:
    query_type: QueryType  # 查询类型
    value: Optional[str]   # 查询值
    children: Optional[List['QueryNode']]  # 子节点
```

## 3. 类设计

### 3.1 InvertedIndex

```
+-------------------+
|   InvertedIndex   |
+-------------------+
| - index           | Dict[str, List[PostingEntry]]
| - documents       | Dict[str, Document]
| - doc_count       | int
| - avg_doc_length  | float
| - doc_lengths     | Dict[str, int]
+-------------------+
| + add_document()  |
| + remove_document()|
| + get_postings()  |
| + get_doc_freq()  |
| + save() / load() |
+-------------------+
```

### 3.2 QueryParser

```
+-------------------+
|   QueryParser     |
+-------------------+
| + parse()         | → QueryNode
+-------------------+
```

### 3.3 Ranker

```
+-------------------+
|   Ranker (ABC)    |
+-------------------+
| + score()         | → float
| + rank()          | → List[tuple]
+-------------------+
        ↑
   ┌────┴────┐
   │         │
+--+--+   +--+--+
|TFIDF|   | BM25 |
+-----+   +------+
```

## 4. 查询处理流程

```
输入查询字符串
      ↓
  QueryParser.parse()
      ↓
  QueryNode (查询树)
      ↓
  QueryExecutor.execute()
      ↓
  Set[doc_id] (候选文档)
      ↓
  Ranker.rank()
      ↓
  List[SearchResult] (排序结果)
```

## 5. 索引构建流程

```
输入文档
    ↓
Tokenizer.tokenize()
    ↓
StopWordsFilter.filter()
    ↓
Stemmer.stem()
    ↓
构建倒排列表
    ↓
更新索引
```

## 6. 压缩算法设计

### 6.1 可变字节编码

```
数字: 300
二进制: 100101100
编码: [0x02, 0x2C]  # 2字节而非4字节
```

### 6.2 差分编码

```
原始ID: [10, 15, 20, 30]
差分值: [10, 5, 5, 10]
```

## 7. 接口设计

### 7.1 SearchEngine API

```python
engine = SearchEngine()

# 添加文档
engine.add_document(doc_id, title, content)
engine.add_documents(documents)

# 搜索
results = engine.search("query string")
results = engine.search("query", method="bm25", top_k=10)

# 统计
stats = engine.get_statistics()

# 持久化
engine.save_index("index.json")
engine.load_index("index.json")
```

### 7.2 SimpleSearchEngine API

```python
engine = SimpleSearchEngine()

# 索引文档
engine.index_documents([{"title": "...", "content": "..."}])

# 搜索
results = engine.search("query", top_k=5)
```
