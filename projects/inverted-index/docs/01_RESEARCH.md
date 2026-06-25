# 01 - 技术调研

## 1. 倒排索引概述

倒排索引（Inverted Index）是搜索引擎的核心数据结构，用于存储文档集合中词汇到文档的映射关系。

### 1.1 基本概念

- **正排索引**：文档 → 词汇列表
- **倒排索引**：词汇 → 文档列表

### 1.2 为什么需要倒排索引

- 快速定位包含特定词汇的文档
- 支持复杂的布尔查询
- 高效的全文检索

## 2. 核心算法

### 2.1 TF-IDF

**TF (Term Frequency)**：词频，衡量词汇在文档中出现的频率。

```
TF(t,d) = 词t在文档d中出现的次数 / 文档d的总词数
```

**IDF (Inverse Document Frequency)**：逆文档频率，衡量词汇的普遍重要性。

```
IDF(t) = log(N / df(t))
```

其中：
- N = 文档总数
- df(t) = 包含词汇t的文档数

**TF-IDF 得分**：
```
Score(t,d) = TF(t,d) × IDF(t)
```

### 2.2 BM25

BM25 是 TF-IDF 的改进版本，由 Robertson 等人提出。

```
Score(D,Q) = Σ IDF(qi) × (f(qi,D) × (k1+1)) / (f(qi,D) + k1×(1-b+b×|D|/avgdl))
```

参数：
- k1：词频饱和参数（通常 1.2-2.0）
- b：文档长度归一化参数（通常 0.75）
- |D|：文档长度
- avgdl：平均文档长度

### 2.3 编辑距离

用于模糊查询，计算两个字符串之间的最小编辑操作数（插入、删除、替换）。

```
edit_distance("kitten", "sitting") = 3
```

## 3. 文本处理技术

### 3.1 分词

- **英文分词**：按空格和标点分割
- **中文分词**：需要专门的分词算法（如 jieba）
- **混合分词**：处理中英文混合文本

### 3.2 停用词

常见但对检索无意义的词汇，如 "the", "is", "的", "是"。

### 3.3 词干提取

将词汇还原为词干形式，如：
- "running" → "run"
- "cats" → "cat"

### 3.4 词形还原

将词汇还原为词典形式，如：
- "is" → "be"
- "better" → "good"

## 4. 索引压缩

### 4.1 可变字节编码

使用变长编码存储整数，小数字使用更少的字节。

### 4.2 差分编码

存储文档ID的差值而非完整值，减少存储空间。

### 4.3 压缩比

典型压缩比：30%-50%

## 5. 参考资源

- [Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/)
- [Inverted Index - Wikipedia](https://en.wikipedia.org/wiki/Inverted_index)
- [BM25 Algorithm](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Porter Stemming Algorithm](https://tartarus.org/martin/PorterStemmer/)
