# 03 - 实现：核心代码解析

## 实现概览

本项目实现了三个核心模块：Tokenizer、Index 和 Query。

## 1. 分词器实现

### 设计思路

分词器负责将原始文本转换为标准化的词项列表。核心步骤：
1. 按非字母数字字符分割
2. 转小写
3. 过滤停用词

### 关键代码

```go
func (t *Tokenizer) Tokenize(text string) []string {
    words := strings.FieldsFunc(text, func(r rune) bool {
        return !unicode.IsLetter(r) && !unicode.IsDigit(r)
    })

    var tokens []string
    for _, w := range words {
        w = strings.ToLower(w)
        if len(w) > 0 && !t.stopWords[w] {
            tokens = append(tokens, w)
        }
    }
    return tokens
}
```

### 停用词表

内置常见英文停用词（约 100 个），包括：
- 冠词：a, an, the
- 介词：in, on, at, to, for
- 代词：he, she, it, they
- 连词：and, or, but

## 2. 索引构建实现

### 添加文档流程

```go
func (idx *Indexer) AddDocument(doc Document) error {
    // 1. 验证
    if doc.ID == "" { return error }

    // 2. 加锁
    idx.index.mu.Lock()
    defer idx.index.mu.Unlock()

    // 3. 检查重复
    if exists { return error }

    // 4. 分词
    tokens := idx.tokenizer.TokenizeWithPositions(fullText)

    // 5. 存储文档元数据
    idx.index.documents[doc.ID] = &doc
    idx.index.docLengths[doc.ID] = len(tokens)
    idx.index.totalTokens += len(tokens)

    // 6. 构建倒排表
    for term, positions := range termPositions {
        pl.Postings = append(pl.Postings, Posting{
            DocID:     doc.ID,
            Positions: positions,
            TermFreq:  len(positions),
        })
    }
}
```

### 删除文档流程

```go
func (idx *Indexer) RemoveDocument(docID string) error {
    // 1. 查找文档
    // 2. 获取文档所有词项
    // 3. 从每个词项的倒排表中移除该文档
    // 4. 如果倒排表为空，删除词项
    // 5. 更新统计信息
}
```

## 3. 查询处理实现

### 布尔查询

**AND 查询**：从第一个词项的倒排表开始，逐步与其他词项的倒排表求交集。

```go
func (idx *Indexer) evaluateAND(terms []string) map[string]bool {
    result := docs containing first term
    for each remaining term:
        remove from result if not in term's posting list
    return result
}
```

**OR 查询**：收集所有词项的倒排表的并集。

**NOT 查询**：从全集文档中排除包含指定词项的文档。

### BM25 评分

```go
func (idx *Indexer) calculateScore(docID string, terms []string) float64 {
    k1 := 1.2   // 词频饱和参数
    b := 0.75   // 长度归一化参数

    for each term:
        tf = 词项在文档中的频率
        df = 包含该词项的文档数
        docLen = 文档长度
        avgDocLen = 平均文档长度
        numDocs = 总文档数

        // BM25 公式
        tfNorm = (tf * (k1+1)) / (tf + k1*(1-b+b*docLen/avgDocLen))
        idf = log((numDocs-df+0.5)/(df+0.5) + 1)
        score += tfNorm * idf
}
```

## 4. 并发安全

使用 `sync.RWMutex` 实现读写分离：

- `RLock()` 用于读操作（Search, GetStats, GetDocument）
- `Lock()` 用于写操作（AddDocument, RemoveDocument）

```go
type InvertedIndex struct {
    mu sync.RWMutex
    // ...
}
```

## 5. 搜索结果

```go
type SearchResult struct {
    DocID   string   // 文档 ID
    Title   string   // 文档标题
    Score   float64  // BM25 分数
    Snippet string   // 摘要（高亮查询词）
}
```

摘要生成逻辑：
1. 截取文档内容前 200 字符
2. 用 `**` 包裹匹配的查询词
3. 最多显示 30 个词

## 实现中的关键决策

1. **分词策略**：选择空格+标点分割，适合英文；中文需要 jieba 等分词器
2. **停用词**：内置常见英文停用词，支持自定义
3. **评分算法**：选择 BM25 而非简单 TF-IDF，因为 BM25 有长度归一化
4. **并发控制**：使用 RWMutex 而非 Mutex，提高读并发性能
5. **内存存储**：纯内存实现，适合学习；生产环境需要持久化
