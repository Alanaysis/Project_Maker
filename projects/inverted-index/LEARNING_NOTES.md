# 学习笔记：倒排索引

## 核心概念

### 倒排索引是什么？

倒排索引是搜索引擎的核心数据结构。它建立了从"词项"到"文档"的反向映射。

**正排索引**：文档 → 词项列表
**倒排索引**：词项 → 文档列表

### 为什么需要倒排索引？

想象搜索 "programming"：
- **正排索引**：需要遍历每个文档，检查是否包含 "programming" → O(N)
- **倒排索引**：直接查找 "programming" 的倒排表 → O(1)

## 关键数据结构

### Posting（倒排表项）
```go
type Posting struct {
    DocID     string   // 文档 ID
    Positions []int    // 词项在文档中的位置
    TermFreq  int      // 词项频率
}
```

### PostingList（倒排表）
```go
type PostingList struct {
    Term     string      // 词项
    Postings []Posting   // 包含该词项的所有文档
}
```

## 布尔查询原理

### AND 查询（交集）
```
term1 的倒排表 ∩ term2 的倒排表
```

优化：从最短的倒排表开始遍历。

### OR 查询（并集）
```
term1 的倒排表 ∪ term2 的倒排表
```

### NOT 查询（差集）
```
全集文档 - 包含 term 的文档
```

## 相关性排序

### TF-IDF
- **TF（词频）**：词项在文档中出现次数越多，越相关
- **IDF（逆文档频率）**：词项在越少文档中出现，越有区分度

### BM25 改进
- 增加文档长度归一化
- 词频饱和（避免长文档过度加权）
- 参数 k1 和 b 可调

## 分词的重要性

分词是索引构建的第一步，直接影响搜索质量。

### 英文分词
- 按空格和标点分割
- 转小写
- 过滤停用词

### 中文分词挑战
- 没有自然分隔符
- 需要词典或统计模型
- 歧义切分问题

## 并发控制

读写锁（RWMutex）：
- 多个读操作可以并发
- 写操作互斥
- 读多写少场景性能优于互斥锁

## 实际应用

### 搜索引擎
Google、Bing 等搜索引擎的核心。

### 数据库索引
MySQL、PostgreSQL 的全文索引。

### 文档检索
Elasticsearch、Solr 等搜索引擎。

## 学习收获

1. 理解了倒排索引的数据结构设计
2. 掌握了布尔查询的实现方法
3. 学会了 BM25 相关性排序算法
4. 理解了分词在搜索引擎中的重要性
5. 实践了 Go 的并发控制（RWMutex）

## 参考资源

- [Inverted Index - Wikipedia](https://en.wikipedia.org/wiki/Inverted_index)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/)
