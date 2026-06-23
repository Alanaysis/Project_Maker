# 学习笔记：查询解析器

## 项目概述

本项目实现了一个搜索查询解析器，支持布尔查询、短语查询和相关性排序。通过这个项目，我深入理解了搜索引擎的核心组件和查询处理流程。

## 核心概念学习

### 1. 查询解析流程

```
查询字符串 → 词法分析 → 语法分析 → AST → 执行 → 排序
```

**学习要点**：
- 词法分析（Lexer）将字符串转换为 token 序列
- 语法分析（Parser）将 token 序列转换为 AST
- 执行器遍历 AST 执行查询
- 相关性排序决定结果顺序

### 2. 递归下降解析

递归下降是一种自顶向下的语法分析方法：

```go
func parseOr() {
    left = parseAnd()
    while current == OR {
        right = parseAnd()
        left = new Or(left, right)
    }
    return left
}
```

**学习要点**：
- 每个语法规则对应一个函数
- 优先级通过函数调用层次体现
- 最低优先级的规则最先被解析

### 3. 运算符优先级

| 优先级 | 操作符 | 说明 |
|--------|--------|------|
| 1 (最高) | `()` | 括号改变优先级 |
| 2 | `NOT` | 逻辑非 |
| 3 | `AND` | 逻辑与 |
| 4 (最低) | `OR` | 逻辑或 |

**学习要点**：
- 优先级决定了表达式的解析方式
- `a OR b AND c` 解析为 `a OR (b AND c)`
- 括号可以改变默认优先级

### 4. 布尔查询

布尔查询基于集合论：

- **AND（交集）**：`A ∩ B`
- **OR（并集）**：`A ∪ B`
- **NOT（差集）**：`U - A`

**学习要点**：
- AND 操作返回同时满足两个条件的文档
- OR 操作返回满足至少一个条件的文档
- NOT 操作排除满足条件的文档

### 5. 倒排索引

倒排索引是搜索引擎的核心数据结构：

```
术语 → 文档ID列表
"quick" → [doc1, doc2, doc4]
"fox" → [doc1, doc2]
```

**学习要点**：
- 术语到文档的映射
- 支持快速的术语搜索
- 空间换时间的典型应用

### 6. 相关性排序

使用 TF-IDF 算法计算相关性：

```
TF（词频）= 术语在文档中出现的次数
IDF（逆文档频率）= log(总文档数 / 包含该术语的文档数)
TF-IDF = TF × IDF
```

**学习要点**：
- TF 高表示术语在文档中频繁出现
- IDF 高表示术语在文档集合中不常见
- TF-IDF 综合考虑词频和文档频率

## 技术实现学习

### 1. Go 语言特性

#### 接口和类型系统

```go
type TokenType int

const (
    TokenTerm     TokenType = iota
    TokenPhrase
    TokenAnd
    // ...
)
```

**学习要点**：
- iota 常量生成器
- 类型定义增强代码可读性
- 常量分组提高代码组织性

#### 并发安全

```go
type Index struct {
    mu        sync.RWMutex
    documents map[string]*Document
}

func (idx *Index) Search(term string) []string {
    idx.mu.RLock()
    defer idx.mu.RUnlock()
    // ...
}
```

**学习要点**：
- 读写锁保护共享数据
- defer 确保锁释放
- 读操作使用 RLock

#### 错误处理

```go
func (p *Parser) Parse() (*ast.Node, error) {
    if p.currentToken().Type == lexer.TokenEOF {
        return nil, fmt.Errorf("empty query")
    }
    // ...
}
```

**学习要点**：
- Go 的错误返回模式
- 提供有意义的错误信息
- 错误传播和处理

### 2. 数据结构设计

#### AST 节点

```go
type Node struct {
    Type     NodeType
    Value    string
    Left     *Node
    Right    *Node
    Children []*Node
}
```

**学习要点**：
- 递归结构表示树形数据
- 不同节点类型使用不同字段
- 灵活的设计支持多种查询类型

#### Token 设计

```go
type Token struct {
    Type    TokenType
    Literal string
}
```

**学习要点**：
- 类型和值的分离
- 支持多种 token 类型
- 保留原始文本用于调试

### 3. 算法实现

#### 集合操作

```go
func intersect(a, b []string) []string {
    set := make(map[string]bool)
    for _, s := range a {
        set[s] = true
    }
    var result []string
    for _, s := range b {
        if set[s] {
            result = append(result, s)
        }
    }
    return result
}
```

**学习要点**：
- 使用 map 实现快速查找
- 时间复杂度 O(n + m)
- 空间复杂度 O(n)

#### 分词算法

```go
func tokenize(text string) []string {
    text = strings.ToLower(text)
    var terms []string
    current := make([]byte, 0, 32)
    
    for i := 0; i < len(text); i++ {
        ch := text[i]
        if ch >= 'a' && ch <= 'z' || ch >= '0' && ch <= '9' {
            current = append(current, ch)
        } else {
            if len(current) > 0 {
                terms = append(terms, string(current))
                current = current[:0]
            }
        }
    }
    return terms
}
```

**学习要点**：
- 状态机实现分词
- 字节级别的操作提高性能
- 处理边界情况

## 设计模式学习

### 1. 访问者模式

执行器遍历 AST 时使用了访问者模式的思想：

```go
func (e *Executor) executeNode(node *ast.Node) []string {
    switch node.Type {
    case ast.NodeTerm:
        return e.executeTerm(node.Value)
    case ast.NodePhrase:
        return e.executePhrase(node.Value)
    case ast.NodeAnd:
        return e.executeAnd(node.Left, node.Right)
    // ...
    }
}
```

**学习要点**：
- 根据节点类型执行不同操作
- 避免在节点中实现执行逻辑
- 提高代码的可扩展性

### 2. 工厂模式

创建节点使用工厂函数：

```go
func NewTerm(value string) *Node {
    return &Node{
        Type:  NodeTerm,
        Value: value,
    }
}

func NewAnd(left, right *Node) *Node {
    return &Node{
        Type:  NodeAnd,
        Left:  left,
        Right: right,
    }
}
```

**学习要点**：
- 封装对象创建逻辑
- 提供清晰的 API
- 简化客户端代码

### 3. 策略模式

不同的查询类型可以看作不同的策略：

- TermQuery：搜索单个术语
- PhraseQuery：搜索精确短语
- BooleanQuery：组合多个查询

**学习要点**：
- 将算法封装为独立的策略
- 支持运行时切换策略
- 提高代码的灵活性

## 测试学习

### 1. 单元测试

```go
func TestParserAnd(t *testing.T) {
    l := lexer.New("hello AND world")
    tokens := l.Tokenize()
    p := New(tokens)
    node, err := p.Parse()
    
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    
    if node.String() != "(hello AND world)" {
        t.Errorf("expected '(hello AND world)', got %s", node.String())
    }
}
```

**学习要点**：
- 测试应该独立且可重复
- 使用有意义的断言信息
- 测试边界情况和错误处理

### 2. 表驱动测试

```go
func TestParserPrecedence(t *testing.T) {
    tests := []struct {
        input    string
        expected string
    }{
        {"a OR b AND c", "(a OR (b AND c))"},
        {"a AND b OR c", "((a AND b) OR c)"},
    }
    
    for _, tt := range tests {
        t.Run(tt.input, func(t *testing.T) {
            // 测试逻辑
        })
    }
}
```

**学习要点**：
- 表驱动测试减少代码重复
- 使用子测试提高可读性
- 易于添加新的测试用例

### 3. 集成测试

```go
func TestIntegrationComplexQuery(t *testing.T) {
    idx := createTestIndex()
    l := lexer.New("(quick OR fast) AND fox")
    tokens := l.Tokenize()
    p := parser.New(tokens)
    ast, _ := p.Parse()
    ex := executor.New(idx)
    results := ex.Execute(ast)
    
    // 验证结果
}
```

**学习要点**：
- 测试组件间的交互
- 验证完整的查询流程
- 发现集成问题

## 性能优化学习

### 1. 内存优化

```go
// 使用预分配容量
current := make([]byte, 0, 32)

// 重用切片
result := result[:0]
```

**学习要点**：
- 预分配减少内存分配
- 重用切片减少 GC 压力
- 监控内存使用

### 2. 并发优化

```go
// 使用读写锁
idx.mu.RLock()
defer idx.mu.RUnlock()

// 并行执行独立查询
go func() {
    // 执行子查询
}()
```

**学习要点**：
- 读写锁提高并发性能
- 并行执行减少总时间
- 注意数据竞争问题

### 3. 算法优化

```go
// 使用 map 实现 O(1) 查找
set := make(map[string]bool)

// 批量处理减少函数调用
results := make([]string, 0, len(docs))
```

**学习要点**：
- 选择合适的数据结构
- 减少函数调用开销
- 批量处理提高效率

## 项目总结

### 成功实现

1. **词法分析器**：支持术语、短语、布尔运算符、括号
2. **语法分析器**：递归下降实现，支持运算符优先级
3. **AST**：灵活的树形结构，支持任意复杂查询
4. **执行器**：实现布尔查询和相关性排序
5. **倒排索引**：内存索引，支持快速搜索

### 学到的知识

1. **查询解析**：理解了搜索引擎的查询处理流程
2. **递归下降解析**：掌握了语法分析的核心技术
3. **布尔查询**：理解了集合论在查询中的应用
4. **相关性排序**：学习了 TF-IDF 算法原理
5. **Go 语言**：深入理解了类型系统、并发、错误处理

### 未来改进

1. 支持通配符查询
2. 实现模糊查询
3. 添加范围查询
4. 优化相关性算法
5. 支持持久化存储

## 参考资源

1. **Lucene Query Parser**
   - 工业级查询解析器参考
   - https://lucene.apache.org/core/queryparser.html

2. **Elasticsearch Query DSL**
   - 现代搜索引擎查询语言
   - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html

3. **Introduction to Information Retrieval**
   - 信息检索经典教材
   - 涵盖 TF-IDF、BM25 等算法

4. **Go 语言官方文档**
   - 学习 Go 语言特性
   - https://go.dev/doc/
