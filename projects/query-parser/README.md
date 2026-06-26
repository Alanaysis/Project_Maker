# Query Parser (查询解析器)

A learning project implementing a search query parser in Go, covering boolean queries, phrase queries, fuzzy matching, wildcards, and range queries.

一个用 Go 实现的搜索查询解析器学习项目，涵盖布尔查询、短语查询、模糊匹配、通配符和范围查询。

---

## Learning Objectives / 学习目标

### English
- Understand query parsing and recursive descent parsing
- Master boolean query construction (AND, OR, NOT)
- Learn relevance scoring and ranking
- Implement fuzzy matching with Levenshtein distance
- Build wildcard and range query support

### 中文
- 理解查询解析和递归下降解析
- 掌握布尔查询构建（AND、OR、NOT）
- 学习相关性评分和排序
- 使用 Levenshtein 距离实现模糊匹配
- 构建通配符和范围查询支持

---

## Query Language Grammar / 查询语言语法

```
Query      → OrExpr
OrExpr     → AndExpr (OR AndExpr)*
AndExpr    → NotExpr (AND NotExpr)*
NotExpr    → Primary | NOT NotExpr
Primary    → Phrase | Range | Grouped | FuzzyTerm | WildcardTerm | BoostedTerm | Term
FuzzyTerm  → Term ~ [LevDistance]
WildcardTerm → Term *
BoostedTerm → Term ^ Number
Phrase     → " PhraseContent "
Range      → [ Lower TO Upper ] | { Lower TO Upper }
Grouped    → ( OrExpr )
Term       → [a-zA-Z0-9_]+
```

### Operator Precedence / 运算符优先级 (highest to lowest / 从高到低)

1. Parentheses `()` - grouping
2. Phrase queries `""` - exact phrase matching
3. Range queries `[]`, `{}` - value ranges
4. Fuzzy `~` - edit distance matching
5. Wildcard `*` - pattern matching
6. Boost `^` - relevance weight
7. `NOT` - negation
8. `AND` - intersection
9. `OR` - union

### Examples / 示例

```
# Simple term search
golang

# Boolean query
golang AND python

# Phrase query
"web framework"

# Fuzzy query (typo tolerance)
golan~

# Wildcard query
go*

# Range query
price:[10 TO 100]

# Complex query
golang AND (web OR "web framework")~1
```

---

## Project Structure / 项目结构

```
query-parser/
├── go.mod              # Go module definition
├── README.md           # This file
├── src/                # Core library
│   ├── types.go        # Type definitions (Token, QueryNode, etc.)
│   ├── tokenizer.go    # Lexical tokenizer
│   ├── parser.go       # Recursive descent parser
│   ├── normalize.go    # Query normalization & tree visualization
│   └── executors.go    # Fuzzy matching, wildcards, scoring
├── examples/           # Demo programs
│   ├── boolean_query.go     # Boolean query parsing
│   ├── phrase_query.go      # Phrase query matching
│   ├── fuzzy_query.go       # Fuzzy matching with Levenshtein distance
│   ├── query_tree.go        # Query tree visualization
│   └── query_execution.go   # Query execution against documents
└── tests/              # Unit tests
    └── queryparser_test.go
```

---

## How to Run Examples / 如何运行示例

### Prerequisites / 前置条件

- Go 1.22 or later

### Run all examples / 运行所有示例

```bash
cd projects/query-parser

# Boolean query demo
go run examples/boolean_query.go

# Phrase query demo
go run examples/phrase_query.go

# Fuzzy query demo
go run examples/fuzzy_query.go

# Query tree visualization
go run examples/query_tree.go

# Query execution demo
go run examples/query_execution.go
```

### Run tests / 运行测试

```bash
# Run all tests
go test ./tests/

# Run with verbose output
go test ./tests/ -v

# Run with coverage
go test ./tests/ -cover
```

---

## Core Concepts / 核心概念

### 1. Query Parsing Flow / 查询解析流程

```
查询字符串 → Tokenizer → TokenStream → Parser → QueryTree → Execution → Ranking
```

1. **Tokenizer**: Breaks the query string into tokens (words, operators, punctuation)
2. **Parser**: Uses recursive descent to build an AST from the token stream
3. **QueryTree**: The parsed representation with node types for each query kind
4. **Execution**: Evaluates the tree against document collections
5. **Ranking**: Scores and sorts results by relevance

### 2. Boolean Queries / 布尔查询

- **AND**: Intersection of matching documents (all terms must appear)
- **OR**: Union of matching documents (any term can appear)
- **NOT**: Set difference (exclude documents matching the term)

### 3. Fuzzy Matching / 模糊匹配

Uses Levenshtein distance to find terms similar to the query term:

```
golang → golan  (distance: 1, score: 0.60)
golang → golng  (distance: 1, score: 0.60)
golang → xyz    (distance: 4, no match)
```

### 4. Phrase Queries / 短语查询

Exact term ordering within a quoted string:

```
"web framework" → matches "web framework" but NOT "framework web"
```

### 5. Wildcard Queries / 通配符查询

- `*` matches zero or more characters
- `?` matches exactly one character

```
go*    → matches "go", "golang", "gopher"
g?lang → matches "golang", "glang"
```

---

## Learning Path / 学习路径

1. **Start with** `examples/boolean_query.go` - understand basic parsing
2. **Then** `examples/phrase_query.go` - learn phrase matching
3. **Then** `examples/fuzzy_query.go` - study Levenshtein distance
4. **Then** `examples/query_tree.go` - visualize the AST
5. **Finally** `examples/query_execution.go` - see full execution pipeline

---

## License

This is a learning project. Feel free to use and modify.

这是一个学习项目，可以自由使用和修改。
