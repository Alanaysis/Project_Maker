# 倒排索引 (Inverted Index)

> 实现倒排索引，理解搜索引擎核心

---

## 📖 项目描述 / Project Description

### 中文
这是一个倒排索引的学习项目，从零实现搜索引擎的核心数据结构。通过这个项目，你将理解现代搜索引擎（如 Elasticsearch、Lucene）底层是如何构建索引和搜索的。

### English
A learning project that implements an inverted index from scratch. Through this project, you will understand how modern search engines (Elasticsearch, Lucene) build indexes and perform searches at their core.

---

## 🎯 学习目标 / Learning Objectives

### 中文
1. **理解倒排索引**：掌握 term → document mapping 的核心概念
2. **掌握索引构建**：学习分词、词频统计、索引数据结构
3. **学会查询处理**：实现布尔查询（AND/OR）、短语查询、BM25 排序
4. **理解 TF-IDF 和 BM25**：掌握文档相关性评分算法
5. **学会索引持久化**：实现索引的保存和加载

### English
1. **Understand inverted index**: Master the core concept of term → document mapping
2. **Master index building**: Learn tokenization, term frequency computation, index data structures
3. **Learn query processing**: Implement boolean queries (AND/OR), phrase queries, BM25 ranking
4. **Understand TF-IDF and BM25**: Master document relevance scoring algorithms
5. **Learn index persistence**: Implement index save and load

---

## 🏗️ 项目结构 / Project Structure

```
inverted-index/
├── go.mod                    # Go module definition
├── README.md                 # This file
├── src/                      # Core library
│   ├── index.go              # Inverted index data structure, BM25, tokenization
│   ├── builder.go            # Index building pipeline
│   └── searcher.go           # Query execution and scoring
├── examples/                 # Demo programs
│   ├── 01_basic_demo.go      # Basic index building and search
│   ├── 02_boolean_query_demo.go  # AND/OR boolean queries
│   ├── 03_bm25_demo.go       # BM25 scoring algorithm
│   ├── 04_persistence_demo.go    # Index save/load
│   └── 05_phrase_query_demo.go   # Phrase queries
└── tests/                    # Unit tests
    └── index_test.go         # Comprehensive test suite
```

---

## 🚀 快速开始 / Quick Start

### 运行示例 / Run Examples

```bash
# 进入项目目录
cd projects/inverted-index

# 运行基础示例
go run examples/01_basic_demo.go

# 运行布尔查询示例
go run examples/02_boolean_query_demo.go

# 运行 BM25 评分示例
go run examples/03_bm25_demo.go

# 运行持久化示例
go run examples/04_persistence_demo.go

# 运行短语查询示例
go run examples/05_phrase_query_demo.go
```

### 运行测试 / Run Tests

```bash
# 运行所有测试
go test ./tests/

# 运行测试并显示覆盖率
go test ./tests/ -cover

# 运行基准测试
go test ./tests/ -bench=.

# 运行测试并显示详细输出
go test ./tests/ -v
```

---

## 📚 倒排索引理论 / Inverted Index Theory

### 什么是倒排索引？/ What is an Inverted Index?

倒排索引是搜索引擎的核心数据结构。与正向索引（document → terms）相反，倒排索引将 **term 映射到包含它的文档列表**。

An inverted index is the core data structure of search engines. Unlike a forward index (document → terms), an inverted index maps **terms to the list of documents containing them**.

### 核心概念 / Core Concepts

| 概念 | 说明 |
|------|------|
| **Term (词项)** | 从文本中提取的单词或 token |
| **Document (文档)** | 被索引的文本单元 |
| **Posting ( postings)** | 记录 term 在文档中的出现位置 |
| **Postings List ( postings 表)** | 某个 term 在所有文档中的 postings 集合 |
| **TF (词频)** | 某个 term 在文档中出现的次数 |
| **DF (文档频率)** | 包含某个 term 的文档数量 |
| **IDF (逆文档频率)** | log(总文档数 / DF)，衡量 term 的稀有程度 |

### 索引构建流程 / Index Building Process

```
文档 → 分词 → 词频统计 → 索引构建 → 查询 → 结果

1. 文档输入: "Go is fast and simple"
2. 分词: ["go", "is", "fast", "and", "simple"]
3. 词频统计: {go:1, is:1, fast:1, and:1, simple:1}
4. 索引构建:
   go     → [Doc1@pos0]
   is     → [Doc1@pos1]
   fast   → [Doc1@pos2]
   and    → [Doc1@pos3]
   simple → [Doc1@pos4]
```

### BM25 排序算法 / BM25 Ranking Algorithm

BM25 是现代搜索引擎最常用的排序函数：

```
score(d,q) = Σ TF(t,d) × (k1+1) / (TF(t,d) + k1×(1-b+b×|d|/avgdl)) × IDF(t)

其中:
  TF(t,d)  = t 在 d 中的词频
  |d|      = 文档 d 的长度
  avgdl    = 平均文档长度
  IDF(t)   = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
  k1       = 词频饱和参数 (通常 1.2-2.0)
  b        = 文档长度归一化参数 (通常 0.75)
```

**关键特性 / Key Features:**
- **词频饱和**: 词频越高，额外贡献越小（ diminishing returns）
- **长度归一化**: 长文档中的高频词不会比短文档中的低频词更有优势
- **IDF 加权**: 稀有词比常见词获得更高的权重

---

## 🔧 查询类型 / Query Types

| 查询类型 | 语法 | 说明 |
|----------|------|------|
| 单词查询 | `search` | 查找包含该词的所有文档 |
| AND 查询 | `go AND rust` | 查找同时包含两个词的文档 |
| OR 查询 | `go OR rust` | 查找包含任一词的文档 |
| 短语查询 | `"machine learning"` | 查找包含完整短语的文档 |

---

## 📊 运行示例输出 / Example Output

### 基础示例 / Basic Demo
```
=== Inverted Index - Basic Demo ===

Index built: 5 documents, 15 terms

=== Term: 'programming' ===
Document Frequency (DF): 4
Term Frequencies (TF):
  Document 1: TF=1
  Document 2: TF=1
  Document 3: TF=1
  Document 4: TF=1
  Document 5: TF=1

=== Search Results ===
Query: "go"
  [1] Doc 1: score=1.2345 (TF=2)
  [2] Doc 5: score=0.9876 (TF=1)
  [3] Doc 3: score=0.6543 (TF=1)
```

### BM25 评分示例 / BM25 Scoring Demo
```
=== BM25 Scoring for term 'go' ===
Config       | Doc    | TF       | DocLen   | Score    |
-------------+--------+----------+----------+----------+
Standard     | 1      | 4        | 9        | 0.8923   |
             | 5      | 1        | 10       | 0.4521   |
             | 6      | 7        | 8        | 0.7834   |
```

---

## 🧠 学习路径建议 / Learning Path

1. **阅读源码** `src/index.go` - 理解倒排索引的数据结构
2. **运行示例** `01_basic_demo.go` - 观察索引构建过程
3. **阅读 BM25 理论** - 理解评分算法
4. **运行示例** `03_bm25_demo.go` - 观察 BM25 评分
5. **运行测试** - 理解测试覆盖的场景
6. **扩展练习**:
   - 添加中文分词器（如 jieba 类似的分词）
   - 添加 TF-IDF 排序
   - 添加查询自动补全
   - 添加索引压缩（如 gamma 编码）

---

## 📝 扩展练习 / Extension Exercises

1. **中文分词**: 添加基于词典的中文分词支持
2. **TF-IDF 排序**: 实现传统的 TF-IDF 评分
3. **查询自动补全**: 添加前缀树（Trie）支持自动补全
4. **索引压缩**: 实现 gamma 编码压缩 postings list
5. **增量索引**: 支持向已有索引中添加新文档
6. **查询日志分析**: 添加查询频率统计和热门查询分析

---

## 📄 License

MIT License
