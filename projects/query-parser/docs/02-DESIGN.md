# 02 - 设计阶段：查询解析器

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Query Parser                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  Lexer   │ →  │  Parser  │ →  │   AST    │              │
│  │ 词法分析器│    │ 语法分析器│    │抽象语法树│              │
│  └──────────┘    └──────────┘    └──────────┘              │
│                          ↓                                  │
│                   ┌──────────┐    ┌──────────┐             │
│                   │ Executor │ →  │  Index   │             │
│                   │  执行器  │    │  索引    │             │
│                   └──────────┘    └──────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. Lexer（词法分析器）
- 将查询字符串转换为 token 序列
- 处理：术语、短语、运算符、括号
- 大小写不敏感

#### 2. Parser（语法分析器）
- 将 token 序列转换为 AST
- 实现运算符优先级：NOT > AND > OR
- 支持括号改变优先级

#### 3. AST（抽象语法树）
- 节点类型：Term、Phrase、And、Or、Not
- 支持任意深度嵌套
- 提供遍历方法

#### 4. Executor（执行器）
- 遍历 AST，执行查询
- 实现布尔运算（交集、并集、差集）
- 计算相关性分数

#### 5. Index（索引）
- 内存倒排索引
- 支持文档添加和搜索
- 大小写不敏感匹配

## 数据模型

### Token（词法单元）

```go
type Token struct {
    Type    TokenType  // TERM, PHRASE, AND, OR, NOT, LPAREN, RPAREN, EOF
    Literal string     // 原始文本
}
```

### Node（AST 节点）

```go
type Node struct {
    Type     NodeType  // NodeTerm, NodePhrase, NodeAnd, NodeOr, NodeNot
    Value    string    // 用于 Term/Phrase 节点
    Left     *Node     // 用于二元操作
    Right    *Node     // 用于二元操作
    Children []*Node   // 用于 NOT 操作
}
```

### Document（文档）

```go
type Document struct {
    ID      string
    Content string
}
```

### SearchResult（搜索结果）

```go
type SearchResult struct {
    DocID   string
    Score   float64
    Content string
}
```

## 算法设计

### 1. 词法分析算法

```
输入: "quick AND fox"
处理:
  1. 跳过空白
  2. 读取单词 "quick"
  3. 识别为 TERM
  4. 跳过空白
  5. 读取 "AND"
  6. 识别为 AND 运算符
  7. 跳过空白
  8. 读取 "fox"
  9. 识别为 TERM
输出: [TERM:"quick", AND, TERM:"fox", EOF]
```

### 2. 语法分析算法（递归下降）

```
parseOr() {
    left = parseAnd()
    while current == OR {
        next()
        right = parseAnd()
        left = new Or(left, right)
    }
    return left
}

parseAnd() {
    left = parseNot()
    while current == AND || current == TERM || current == PHRASE {
        next()
        right = parseNot()
        left = new And(left, right)
    }
    return left
}

parseNot() {
    if current == NOT {
        next()
        child = parsePrimary()
        return new Not(child)
    }
    return parsePrimary()
}

parsePrimary() {
    if current == TERM {
        return new Term(value)
    } else if current == PHRASE {
        return new Phrase(value)
    } else if current == LPAREN {
        next()
        node = parseOr()
        expect(RPAREN)
        return node
    }
}
```

### 3. 执行算法

```
execute(node) {
    switch node.type {
    case Term:
        return index.Search(node.value)
    case Phrase:
        return executePhrase(node.value)
    case And:
        leftDocs = execute(node.left)
        rightDocs = execute(node.right)
        return intersect(leftDocs, rightDocs)
    case Or:
        leftDocs = execute(node.left)
        rightDocs = execute(node.right)
        return union(leftDocs, rightDocs)
    case Not:
        childDocs = execute(node.children[0])
        allDocs = index.AllDocuments()
        return difference(allDocs, childDocs)
    }
}
```

### 4. 相关性排序算法

```
score(document, query) {
    terms = query.CollectTerms()
    score = 0

    for term in terms {
        count = countOccurrences(document.content, term)
        tf = count
        docCount = index.Search(term).length
        idf = 1 + totalDocs / docCount
        score += tf * idf
    }

    return score
}
```

## 操作符优先级

| 优先级 | 操作符 | 描述 |
|--------|--------|------|
| 1 (最高) | `()` | 括号 |
| 2 | `NOT` | 逻辑非 |
| 3 | `AND` | 逻辑与 |
| 4 (最低) | `OR` | 逻辑或 |

## 错误处理

### 语法错误
- 空查询
- 括号不匹配
- 缺少操作数
- 未知 token

### 运行时错误
- 索引为空
- 文档不存在

## 测试策略

1. **单元测试**：测试每个组件独立功能
2. **集成测试**：测试组件间交互
3. **边界测试**：测试空查询、单个术语、复杂组合
