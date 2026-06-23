# 01 - 研究阶段：查询解析器

## 核心概念

### 1. 查询解析器的作用

查询解析器是搜索引擎的核心组件，负责将用户输入的查询字符串转换为可执行的查询结构。

**核心循环**：
```
查询字符串 → 解析 → 查询树 → 执行 → 排序
```

### 2. 查询类型

#### 2.1 术语查询（Term Query）
- 最简单的查询类型
- 搜索包含特定词语的文档
- 示例：`hello`

#### 2.2 布尔查询（Boolean Query）
- **AND**：两个条件都必须满足
- **OR**：至少一个条件满足
- **NOT**：排除满足条件的文档
- 示例：`hello AND world`、`cat OR dog`、`NOT spam`

#### 2.3 短语查询（Phrase Query）
- 搜索包含精确短语的文档
- 用双引号包围
- 示例：`"hello world"`

#### 2.4 组合查询
- 使用括号控制优先级
- 示例：`(hello OR hi) AND world`

### 3. 查询解析流程

```
输入: "quick AND fox OR dog"
  ↓
词法分析（Lexer）
  → [quick] [AND] [fox] [OR] [dog]
  ↓
语法分析（Parser）
  → AST: (quick AND fox) OR dog
  ↓
执行（Executor）
  → 搜索索引，获取匹配文档
  ↓
排序（Ranking）
  → 按相关性排序结果
```

### 4. AST（抽象语法树）

查询被解析为树形结构：

```
OR
├── AND
│   ├── Term("quick")
│   └── Term("fox")
└── Term("dog")
```

### 5. 相关性排序

#### 5.1 TF-IDF 算法
- **TF（词频）**：词语在文档中出现的次数
- **IDF（逆文档频率）**：包含该词语的文档数量的倒数
- **TF-IDF = TF × IDF**

#### 5.2 BM25 算法
- TF-IDF 的改进版本
- 考虑文档长度归一化
- 更精确的相关性计算

## 参考资源

1. **Lucene Query Parser Syntax**
   - https://lucene.apache.org/core/queryparser.html
   - 工业级查询解析器参考

2. **Elasticsearch Query DSL**
   - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
   - 现代搜索引擎查询语言

3. **Boolean Algebra**
   - 布尔查询的数学基础
   - 集合论与查询组合
