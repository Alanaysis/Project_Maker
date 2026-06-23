# 查询解析器 (Query Parser)

一个用 Go 实现的搜索查询解析器，支持布尔查询、短语查询和相关性排序。

## 项目概述

本项目实现了一个完整的查询解析器，展示了搜索引擎的核心查询处理流程：

```
查询字符串 → 解析 → 查询树 → 执行 → 排序
```

## 核心功能

### 1. 查询解析
- 词法分析：将查询字符串转换为 token 序列
- 语法分析：将 token 序列转换为抽象语法树 (AST)
- 支持复杂的查询语法

### 2. 布尔查询支持
- **AND**：逻辑与，两个条件都必须满足
- **OR**：逻辑或，至少一个条件满足
- **NOT**：逻辑非，排除满足条件的文档
- **隐式 AND**：相邻术语自动转换为 AND 操作

### 3. 短语查询
- 使用双引号包围的精确短语搜索
- 示例：`"hello world"`

### 4. 相关性排序
- 基于 TF-IDF 算法计算相关性分数
- 结果按分数降序排列
- 考虑词频和文档频率

## 项目结构

```
query-parser/
├── cmd/
│   └── parser/
│       └── main.go           # 命令行入口
├── internal/
│   ├── lexer/
│   │   ├── token.go          # Token 定义
│   │   ├── lexer.go          # 词法分析器
│   │   └── lexer_test.go     # 词法分析器测试
│   ├── parser/
│   │   ├── parser.go         # 语法分析器
│   │   └── parser_test.go    # 语法分析器测试
│   ├── ast/
│   │   └── node.go           # AST 节点定义
│   ├── executor/
│   │   ├── executor.go       # 查询执行器
│   │   └── executor_test.go  # 执行器测试
│   ├── index/
│   │   ├── index.go          # 倒排索引
│   │   └── index_test.go     # 索引测试
│   └── query_test.go         # 集成测试
├── examples/
│   └── queries.txt           # 查询示例
├── docs/                     # 文档目录
├── go.mod                    # Go 模块定义
└── README.md                 # 项目说明
```

## 快速开始

### 环境要求

- Go 1.21+

### 安装和运行

```bash
# 进入项目目录
cd projects/query-parser

# 运行示例查询
go run cmd/parser/main.go "hello AND world"
go run cmd/parser/main.go "cat OR dog"
go run cmd/parser/main.go `"brown fox"`
go run cmd/parser/main.go "(quick OR fast) AND fox"
```

### 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定包测试
go test ./internal/lexer/
go test ./internal/parser/
go test ./internal/executor/
go test ./internal/index/

# 运行集成测试
go test ./internal/

# 显示详细输出
go test -v ./...
```

## 查询语法

### 术语查询

搜索包含特定词语的文档：

```
hello
world
```

### 布尔查询

使用布尔运算符组合查询：

```
hello AND world    # 两个条件都必须满足
cat OR dog         # 至少一个条件满足
NOT spam           # 排除满足条件的文档
quick fox          # 隐式 AND（相邻术语）
```

### 短语查询

搜索包含精确短语的文档：

```
"hello world"
"brown fox"
```

### 括号分组

使用括号控制优先级：

```
(hello OR hi) AND world
(quick OR fast) AND "brown fox" NOT lazy
```

### 运算符优先级

| 优先级 | 操作符 | 描述 |
|--------|--------|------|
| 1 (最高) | `()` | 括号 |
| 2 | `NOT` | 逻辑非 |
| 3 | `AND` | 逻辑与 |
| 4 (最低) | `OR` | 逻辑或 |

## 示例查询

```bash
# 简单术语
go run cmd/parser/main.go "fox"

# 布尔 AND
go run cmd/parser/main.go "quick AND fox"

# 布尔 OR
go run cmd/parser/main.go "cat OR dog"

# NOT 操作
go run cmd/parser/main.go "quick NOT fox"

# 短语查询
go run cmd/parser/main.go `"brown fox"`

# 复杂查询
go run cmd/parser/main.go "(quick OR fast) AND fox"
```

## 核心组件

### 1. Lexer（词法分析器）

将查询字符串转换为 token 序列：

```go
l := lexer.New("hello AND world")
tokens := l.Tokenize()
// [TERM:"hello", AND, TERM:"world", EOF]
```

### 2. Parser（语法分析器）

将 token 序列转换为 AST：

```go
p := parser.New(tokens)
ast, err := p.Parse()
// AST: (hello AND world)
```

### 3. Executor（执行器）

执行查询并返回结果：

```go
ex := executor.New(index)
results := ex.Execute(ast)
// 返回按相关性排序的搜索结果
```

### 4. Index（索引）

存储文档并支持搜索：

```go
idx := index.New()
idx.AddDocument(&index.Document{ID: "doc1", Content: "Hello World"})
results := idx.Search("hello")
```

## 相关性排序

使用 TF-IDF 算法计算文档相关性：

```
TF（词频）= 术语在文档中出现的次数
IDF（逆文档频率）= 1 + 总文档数 / 包含该术语的文档数
TF-IDF = TF × IDF
```

**示例**：
- 文档 1: "The quick brown fox" - 搜索 "fox" 得分 = 1 × (1 + 5/2) = 3.5
- 文档 2: "A quick brown dog" - 搜索 "fox" 得分 = 0

## 测试覆盖

### 单元测试

- Lexer 测试：token 解析、关键字识别、括号处理
- Parser 测试：AST 构建、运算符优先级、错误处理
- Executor 测试：布尔运算、短语查询、相关性排序
- Index 测试：文档添加、术语搜索、大小写处理

### 集成测试

- 完整查询流程测试
- 复杂查询组合测试
- 隐式 AND 测试
- 相关性排序验证

## 学习要点

### 1. 查询解析
- 理解词法分析和语法分析的区别
- 掌握递归下降解析技术
- 学会处理运算符优先级

### 2. 布尔查询
- 理解集合论在查询中的应用
- 掌握交集、并集、差集操作
- 学会组合多个查询条件

### 3. 相关性排序
- 理解 TF-IDF 算法原理
- 掌握词频和文档频率的概念
- 学会计算文档相关性分数

### 4. 数据结构
- 理解倒排索引的工作原理
- 掌握 AST 的设计和遍历
- 学会使用 map 实现快速查找

## 扩展阅读

1. [Lucene Query Parser Syntax](https://lucene.apache.org/core/queryparser.html)
2. [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
3. [Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/)

## 许可证

MIT License
