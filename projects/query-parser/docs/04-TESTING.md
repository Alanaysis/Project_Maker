# 04 - 测试阶段：查询解析器

## 测试策略

### 测试金字塔

```
        /\
       /  \  集成测试
      /----\
     /      \  单元测试
    /--------\
```

## 单元测试

### 1. Lexer 测试

#### 基本术语解析

```go
func TestLexerBasic(t *testing.T) {
    l := New("hello")
    tokens := l.Tokenize()
    // 验证: [TERM:"hello", EOF]
}
```

#### 短语解析

```go
func TestLexerPhrase(t *testing.T) {
    l := New(`"hello world"`)
    tokens := l.Tokenize()
    // 验证: [PHRASE:"hello world", EOF]
}
```

#### 布尔运算符

```go
func TestLexerBoolean(t *testing.T) {
    l := New("hello AND world OR NOT test")
    tokens := l.Tokenize()
    // 验证: [TERM, AND, TERM, OR, NOT, TERM, EOF]
}
```

#### 括号处理

```go
func TestLexerParentheses(t *testing.T) {
    l := New("(hello AND world)")
    tokens := l.Tokenize()
    // 验证: [LPAREN, TERM, AND, TERM, RPAREN, EOF]
}
```

### 2. Parser 测试

#### 简单术语

```go
func TestParserTerm(t *testing.T) {
    l := lexer.New("hello")
    tokens := l.Tokenize()
    p := New(tokens)
    node, _ := p.Parse()
    // 验证: node.String() == "hello"
}
```

#### AND 操作

```go
func TestParserAnd(t *testing.T) {
    l := lexer.New("hello AND world")
    tokens := l.Tokenize()
    p := New(tokens)
    node, _ := p.Parse()
    // 验证: node.String() == "(hello AND world)"
}
```

#### 运算符优先级

```go
func TestParserPrecedence(t *testing.T) {
    l := lexer.New("a OR b AND c")
    tokens := l.Tokenize()
    p := New(tokens)
    node, _ := p.Parse()
    // 验证: node.String() == "(a OR (b AND c))"
}
```

#### 括号优先级

```go
func TestParserParentheses(t *testing.T) {
    l := lexer.New("(a OR b) AND c")
    tokens := l.Tokenize()
    p := New(tokens)
    node, _ := p.Parse()
    // 验证: node.String() == "((a OR b) AND c)"
}
```

#### 错误处理

```go
func TestParserEmptyQuery(t *testing.T) {
    l := lexer.New("")
    tokens := l.Tokenize()
    p := New(tokens)
    _, err := p.Parse()
    // 验证: err != nil
}

func TestParserMismatchedParentheses(t *testing.T) {
    l := lexer.New("(hello")
    tokens := l.Tokenize()
    p := New(tokens)
    _, err := p.Parse()
    // 验证: err != nil
}
```

### 3. Executor 测试

#### 术语查询

```go
func TestExecuteTerm(t *testing.T) {
    idx := createTestIndex()
    ex := New(idx)
    node := ast.NewTerm("fox")
    results := ex.Execute(node)
    // 验证: 包含 doc1
}
```

#### 布尔 AND

```go
func TestExecuteAnd(t *testing.T) {
    idx := createTestIndex()
    ex := New(idx)
    node := ast.NewAnd(ast.NewTerm("fox"), ast.NewTerm("dog"))
    results := ex.Execute(node)
    // 验证: 包含 doc1 (同时包含 fox 和 dog)
}
```

#### 布尔 OR

```go
func TestExecuteOr(t *testing.T) {
    idx := createTestIndex()
    ex := New(idx)
    node := ast.NewOr(ast.NewTerm("cat"), ast.NewTerm("dog"))
    results := ex.Execute(node)
    // 验证: 包含 doc3 (cat) 和 doc5 (dog)
}
```

#### NOT 操作

```go
func TestExecuteNot(t *testing.T) {
    idx := createTestIndex()
    ex := New(idx)
    node := ast.NewNot(ast.NewTerm("lazy"))
    results := ex.Execute(node)
    // 验证: 不包含 doc1 和 doc3
}
```

#### 短语查询

```go
func TestExecutePhrase(t *testing.T) {
    idx := createTestIndex()
    ex := New(idx)
    node := ast.NewPhrase("brown fox")
    results := ex.Execute(node)
    // 验证: 包含 doc1 (包含 "brown fox" 子串)
}
```

#### 相关性排序

```go
func TestExecuteRelevanceSorting(t *testing.T) {
    idx := createTestIndex()
    ex := New(idx)
    node := ast.NewTerm("fox")
    results := ex.Execute(node)
    // 验证: 结果按分数降序排列
}
```

### 4. Index 测试

#### 文档添加

```go
func TestIndexAddDocument(t *testing.T) {
    idx := New()
    doc := &Document{ID: "doc1", Content: "Hello World"}
    idx.AddDocument(doc)
    // 验证: idx.DocumentCount() == 1
}
```

#### 术语搜索

```go
func TestIndexSearch(t *testing.T) {
    idx := New()
    // 添加多个文档
    // 搜索 "quick"
    // 验证: 返回包含 "quick" 的文档
}
```

#### 大小写不敏感

```go
func TestCaseInsensitiveSearch(t *testing.T) {
    idx := New()
    doc := &Document{ID: "doc1", Content: "Hello WORLD"}
    idx.AddDocument(doc)
    // 搜索 "hello"、"Hello"、"HELLO"
    // 验证: 都能匹配
}
```

## 集成测试

### 完整查询流程测试

```go
func TestIntegrationComplexQuery(t *testing.T) {
    idx := createTestIndex()
    
    // 查询: (quick OR fast) AND fox
    l := lexer.New("(quick OR fast) AND fox")
    tokens := l.Tokenize()
    p := parser.New(tokens)
    ast, _ := p.Parse()
    
    ex := executor.New(idx)
    results := ex.Execute(ast)
    
    // 验证: 结果包含 doc1
}
```

### 隐式 AND 测试

```go
func TestIntegrationImplicitAnd(t *testing.T) {
    idx := createTestIndex()
    
    // 查询: quick fox (隐式 AND)
    l := lexer.New("quick fox")
    tokens := l.Tokenize()
    p := parser.New(tokens)
    ast, _ := p.Parse()
    
    ex := executor.New(idx)
    results := ex.Execute(ast)
    
    // 验证: 结果包含 doc1
}
```

## 测试数据

### 测试文档集

```go
docs := []*index.Document{
    {ID: "doc1", Content: "The quick brown fox jumps over the lazy dog"},
    {ID: "doc2", Content: "A quick brown dog outpaces the fox"},
    {ID: "doc3", Content: "The lazy cat sleeps all day long"},
    {ID: "doc4", Content: "Quick brown foxes are very fast animals"},
    {ID: "doc5", Content: "The dog and cat are friends"},
}
```

### 测试查询

| 查询 | 预期结果 |
|------|----------|
| `fox` | doc1, doc2 |
| `quick AND fox` | doc1 |
| `cat OR dog` | doc3, doc5 |
| `quick NOT fox` | doc4 |
| `"brown fox"` | doc1 |
| `(quick OR fast) AND fox` | doc1 |

## 运行测试

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

# 运行特定测试
go test -run TestParserAnd ./internal/parser/
```

## 测试覆盖率

```bash
# 生成覆盖率报告
go test -coverprofile=coverage.out ./...

# 查看覆盖率
go tool cover -func=coverage.out

# 生成 HTML 报告
go tool cover -html=coverage.out -o coverage.html
```

## 测试结果示例

```
ok  query-parser/internal/lexer      0.002s  coverage: 95.0%
ok  query-parser/internal/parser     0.003s  coverage: 92.5%
ok  query-parser/internal/executor   0.004s  coverage: 88.0%
ok  query-parser/internal/index      0.002s  coverage: 90.0%
ok  query-parser/internal            0.005s  coverage: 85.0%
```
