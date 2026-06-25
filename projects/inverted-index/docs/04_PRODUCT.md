# 04 - 产品文档

## 1. 产品概述

倒排索引搜索引擎是一个用于学习和理解搜索引擎核心原理的Python实现。

### 1.1 目标用户

- 学习信息检索的学生
- 对搜索引擎原理感兴趣的开发者
- 需要轻量级全文检索的项目

### 1.2 核心价值

- **教育性**：清晰展示搜索引擎工作原理
- **实用性**：可用于小型文档检索场景
- **可扩展性**：模块化设计，易于扩展

## 2. 功能说明

### 2.1 文档索引

支持添加、删除和更新文档。

```python
from src.search_engine import SearchEngine

engine = SearchEngine()
engine.add_document("doc1", "标题", "内容")
```

### 2.2 查询类型

| 查询类型 | 语法 | 示例 | 说明 |
|----------|------|------|------|
| 单词查询 | word | python | 查找包含该词的文档 |
| AND查询 | w1 AND w2 | python AND data | 查找包含所有词的文档 |
| OR查询 | w1 OR w2 | python OR java | 查找包含任一词的文档 |
| NOT查询 | NOT word | NOT java | 排除包含该词的文档 |
| 短语查询 | "phrase" | "machine learning" | 查找包含该短语的文档 |
| 通配符查询 | pattern | py* | 支持 * 和 ? |
| 模糊查询 | word~ | pythn~ | 容错查询 |

### 2.3 排序算法

#### TF-IDF
- 适合一般场景
- 计算简单高效

#### BM25
- 适合长文档
- 考虑文档长度归一化
- 参数可调

### 2.4 索引类型

| 类型 | 特点 | 适用场景 |
|------|------|----------|
| 基本索引 | 简单倒排列表 | 入门学习 |
| 位置索引 | 记录词汇位置 | 短语查询 |
| 压缩索引 | 可变字节编码 | 大规模数据 |

## 3. 使用指南

### 3.1 快速开始

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
results = engine.search("python")
for r in results:
    print(f"{r.title}: {r.score}")
```

### 3.2 高级用法

```python
# 使用BM25排序
results = engine.search("python", method="bm25", top_k=5)

# 使用位置索引支持短语查询
engine = SearchEngine('positional')
results = engine.search('"machine learning"')

# 保存和加载索引
engine.save_index("my_index.json")
engine.load_index("my_index.json")
```

### 3.3 命令行使用

```bash
# 运行示例
python examples/basic_search.py
python examples/document_retrieval.py

# 运行测试
python -m pytest tests/
```

## 4. 性能指标

### 4.1 基准测试

| 操作 | 100文档 | 1000文档 | 10000文档 |
|------|---------|----------|-----------|
| 索引构建 | <0.1s | <1s | <10s |
| 单词查询 | <1ms | <5ms | <20ms |
| 布尔查询 | <5ms | <20ms | <100ms |

### 4.2 内存使用

- 100文档：~1MB
- 1000文档：~10MB
- 10000文档：~100MB

## 5. 限制说明

1. 中文分词使用简单字符分割，不支持词典分词
2. 不支持分布式部署
3. 不支持实时增量索引
4. 内存索引，大规模数据需要持久化

## 6. 未来规划

- [ ] 集成 jieba 中文分词
- [ ] 支持索引持久化到数据库
- [ ] 添加 Web API 接口
- [ ] 支持分布式索引
- [ ] 添加更复杂的查询语法
