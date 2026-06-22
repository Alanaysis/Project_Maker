# 02 - 设计：系统架构

## 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    CLI (cmd/main.go)                 │
│              交互式搜索界面                            │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Tokenizer   │ │    Index     │ │    Query     │
│              │ │              │ │              │
│ - 分词       │ │ - 索引构建   │ │ - 查询解析   │
│ - 停用词过滤 │ │ - 布尔查询   │ │ - AND/OR/NOT │
│ - 位置追踪   │ │ - BM25 排序  │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

## 核心数据结构

### Document
```go
type Document struct {
    ID      string
    Title   string
    Content string
}
```

### Posting
```go
type Posting struct {
    DocID     string
    Positions []int  // 词项在文档中的位置
    TermFreq  int    // 词项在文档中的频率
}
```

### PostingList
```go
type PostingList struct {
    Term     string
    Postings []Posting
}
```

### InvertedIndex
```go
type InvertedIndex struct {
    index       map[string]*PostingList  // 词项 -> 倒排表
    documents   map[string]*Document     // 文档ID -> 文档
    docLengths  map[string]int           // 文档ID -> 文档长度
    totalTokens int                      // 总词项数
}
```

## 模块设计

### Tokenizer 模块

**职责**：文本分词和预处理

**接口**：
```go
type Tokenizer struct {
    stopWords map[string]bool
}

func New() *Tokenizer
func (t *Tokenizer) Tokenize(text string) []string
func (t *Tokenizer) TokenizeWithPositions(text string) []Token
```

**处理流程**：
1. 按非字母数字字符分割
2. 转换为小写
3. 过滤停用词
4. 返回词项列表（可选带位置信息）

### Index 模块

**职责**：索引构建和查询

**接口**：
```go
type Indexer struct {
    index     *InvertedIndex
    tokenizer *tokenizer.Tokenizer
}

func NewIndexer() *Indexer
func (idx *Indexer) AddDocument(doc Document) error
func (idx *Indexer) RemoveDocument(docID string) error
func (idx *Indexer) Search(query string) []SearchResult
func (idx *Indexer) GetStats() IndexStats
```

**索引构建流程**：
1. 验证文档（检查 ID 唯一性）
2. 合并标题和内容
3. 分词（调用 Tokenizer）
4. 构建词项位置映射
5. 更新倒排表
6. 更新文档元数据和统计信息

**查询处理流程**：
1. 解析查询字符串
2. 根据操作符选择评估策略
3. 对候选文档计算 BM25 分数
4. 按分数降序排序
5. 生成搜索结果摘要

### Query 模块

**职责**：查询字符串解析

**接口**：
```go
type Query struct {
    Operator Operator  // AND, OR, NOT
    Terms    []string  // 查询词项
    Raw      string    // 原始查询字符串
}

func ParseQuery(raw string) *Query
```

**支持的语法**：
- `"term1 term2"` -> AND 查询
- `"term1 OR term2"` -> OR 查询
- `"NOT term1"` -> NOT 查询
- `"term1 AND term2"` -> 显式 AND 查询

## BM25 评分算法

```go
func calculateScore(docID string, terms []string) float64 {
    k1 := 1.2
    b := 0.75

    for each term:
        tf = term frequency in document
        df = number of documents containing term
        docLen = document length
        avgDocLen = average document length
        numDocs = total number of documents

        tfNorm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * docLen / avgDocLen))
        idf = log((numDocs - df + 0.5) / (df + 0.5) + 1)
        score += tfNorm * idf

    return score
}
```

## 线程安全

使用 `sync.RWMutex` 保护共享状态：
- 读操作（Search, GetStats, GetDocument）使用读锁
- 写操作（AddDocument, RemoveDocument）使用写锁

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 空文档 ID | 返回错误 |
| 重复文档 ID | 返回错误 |
| 删除不存在的文档 | 返回错误 |
| 空查询 | 返回空结果 |
| 查询无匹配 | 返回空结果 |
