# 01 - 研究：倒排索引基础

## 什么是倒排索引

倒排索引（Inverted Index）是一种索引数据结构，用于存储从"词项"到"文档"的映射关系。它是搜索引擎的核心组件。

### 正排索引 vs 倒排索引

**正排索引（Forward Index）**：文档 -> 词项列表
```
doc1 -> ["go", "programming", "language"]
doc2 -> ["python", "scripting", "language"]
```

**倒排索引（Inverted Index）**：词项 -> 文档列表
```
"go"         -> [doc1]
"programming" -> [doc1]
"language"    -> [doc1, doc2]
"python"      -> [doc2]
"scripting"   -> [doc2]
```

## 倒排索引的组成

### 1. 词典（Dictionary）
所有唯一词项的集合，通常使用哈希表或 B+ 树实现。

### 2. 倒排表（Posting List）
每个词项对应一个倒排表，包含：
- 文档 ID
- 词项频率（TF）
- 词项位置（可选，用于短语查询）

### 示例

```
词典:
  "go"    -> PostingList[{doc1, tf=2, pos=[0,5]}]
  "is"    -> PostingList[{doc1, tf=1, pos=[1]}, {doc2, tf=1, pos=[1]}]
  "lang"  -> PostingList[{doc1, tf=1, pos=[3]}, {doc2, tf=1, pos=[3]}]
```

## 索引构建流程

```
1. 文档采集
   ↓
2. 文档预处理（去噪、格式化）
   ↓
3. 分词（Tokenization）
   ↓
4. 词项处理（小写化、去停用词、词干提取）
   ↓
5. 构建倒排表
   ↓
6. 索引持久化
```

## 布尔查询处理

### AND 查询
求多个词项倒排表的交集。

```
"programming" ∩ "language"
= [doc1] ∩ [doc1, doc2]
= [doc1]
```

### OR 查询
求多个词项倒排表的并集。

```
"go" ∪ "python"
= [doc1] ∪ [doc2]
= [doc1, doc2]
```

### NOT 查询
从全集文档中排除包含特定词项的文档。

```
ALL - "python"
= [doc1, doc2, doc3] - [doc2]
= [doc1, doc3]
```

## 相关性排序

### TF-IDF
- **TF（词频）**：词项在文档中出现的频率
- **IDF（逆文档频率）**：词项在所有文档中的稀有程度

```
TF-IDF = TF × IDF
IDF = log(N / df)
```

### BM25
改进的 TF-IDF 算法，考虑了文档长度归一化：

```
score = IDF × (tf × (k1 + 1)) / (tf + k1 × (1 - b + b × dl / avgdl))
```

- k1 = 1.2（词频饱和参数）
- b = 0.75（长度归一化参数）
- dl = 文档长度
- avgdl = 平均文档长度

## 关键技术点

1. **分词策略**：空格分词、中文分词、n-gram
2. **停用词过滤**：去除常见无意义词（the, is, a...）
3. **索引压缩**：差值编码、变长编码
4. **动态更新**：增量索引、索引合并
5. **分布式索引**：文档分片、查询路由
