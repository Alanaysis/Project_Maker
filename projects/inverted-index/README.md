# 倒排索引 (Inverted Index)

## 项目概述

实现一个完整的倒排索引搜索引擎，理解搜索引擎的核心数据结构。支持文档索引、布尔查询和相关性排序。

## 学习目标

- 理解倒排索引的数据结构和工作原理
- 掌握文档索引构建流程（分词 -> 倒排表 -> 持久化）
- 学会布尔查询处理（AND / OR / NOT）
- 理解 TF-IDF / BM25 相关性排序算法

## 技术栈

- 语言：Go 1.21+
- 依赖：无（纯标准库）

## 项目结构

```
inverted-index/
├── cmd/
│   └── main.go              # 交互式搜索 CLI
├── internal/
│   ├── index/
│   │   ├── types.go          # 核心数据结构
│   │   ├── index.go          # 索引构建与查询
│   │   └── search.go         # 搜索结果类型
│   ├── tokenizer/
│   │   └── tokenizer.go      # 分词器
│   └── query/
│       └── parser.go         # 查询解析器
├── tests/
│   ├── tokenizer_test.go     # 分词器测试
│   ├── index_test.go         # 索引测试
│   └── query_test.go         # 查询解析测试
└── docs/
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 快速开始

```bash
# 运行测试
cd projects/inverted-index
go test ./tests/ -v

# 启动交互式搜索
go run cmd/main.go
```

## 核心功能

### 1. 文档索引
```go
idx := index.NewIndexer()
idx.AddDocument(index.Document{
    ID:      "doc1",
    Title:   "Go Programming",
    Content: "Go is a compiled language",
})
```

### 2. 布尔查询
```go
// AND 查询（默认）
results := idx.Search("programming language")

// OR 查询
results := idx.Search("Go OR Python")

// NOT 查询
results := idx.Search("NOT Python")
```

### 3. 相关性排序
搜索结果按 BM25 算法评分排序，词频（TF）和逆文档频率（IDF）共同决定排名。

## 核心循环

```
文档 → 分词(Tokenizer) → 索引构建(AddDocument) → 查询解析(ParseQuery) → 结果排序(BM25) → 搜索结果
```

## 参考资源

- [Inverted Index - Wikipedia](https://en.wikipedia.org/wiki/Inverted_index)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Information Retrieval - Introduction to IR](https://nlp.stanford.edu/IR-book/)
