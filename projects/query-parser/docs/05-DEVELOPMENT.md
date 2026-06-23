# 05 - 开发阶段：查询解析器

## 开发环境

### 系统要求

- Go 1.21+
- Git
- 文本编辑器或 IDE

### 项目初始化

```bash
# 创建项目目录
mkdir -p projects/query-parser
cd projects/query-parser

# 初始化 Go 模块
go mod init query-parser

# 创建目录结构
mkdir -p cmd/parser internal/{lexer,parser,ast,executor,index} docs examples
```

## 核心开发步骤

### 第一步：实现词法分析器

1. **定义 Token 类型**

```go
// internal/lexer/token.go
type TokenType int

const (
    TokenTerm     TokenType = iota
    TokenPhrase
    TokenAnd
    TokenOr
    TokenNot
    TokenLParen
    TokenRParen
    TokenEOF
)
```

2. **实现 Lexer**

```go
// internal/lexer/lexer.go
type Lexer struct {
    input  string
    pos    int
    tokens []Token
}

func (l *Lexer) Tokenize() []Token {
    // 循环处理输入字符串
    // 跳过空白
    // 读取短语（引号包围）
    // 读取单词
    // 识别关键字（AND、OR、NOT）
    return l.tokens
}
```

3. **编写测试**

```go
// internal/lexer/lexer_test.go
func TestLexerBasic(t *testing.T) {
    l := New("hello AND world")
    tokens := l.Tokenize()
    // 验证 token 序列
}
```

### 第二步：实现 AST 节点

1. **定义节点类型**

```go
// internal/ast/node.go
type NodeType int

const (
    NodeTerm     NodeType = iota
    NodePhrase
    NodeAnd
    NodeOr
    NodeNot
)
```

2. **实现节点方法**

```go
type Node struct {
    Type     NodeType
    Value    string
    Left     *Node
    Right    *Node
    Children []*Node
}

func (n *Node) String() string {
    // 返回字符串表示
}

func (n *Node) CollectTerms() []string {
    // 收集所有术语
}
```

### 第三步：实现语法分析器

1. **递归下降解析**

```go
// internal/parser/parser.go
type Parser struct {
    tokens []lexer.Token
    pos    int
}

func (p *Parser) Parse() (*ast.Node, error) {
    return p.parseOr()
}

func (p *Parser) parseOr() (*ast.Node, error) {
    left := p.parseAnd()
    for current == OR {
        right := p.parseAnd()
        left = ast.NewOr(left, right)
    }
    return left
}

func (p *Parser) parseAnd() (*ast.Node, error) {
    left := p.parseNot()
    for current == AND || current == TERM || current == PHRASE {
        right := p.parseNot()
        left = ast.NewAnd(left, right)
    }
    return left
}

func (p *Parser) parseNot() (*ast.Node, error) {
    if current == NOT {
        child := p.parsePrimary()
        return ast.NewNot(child)
    }
    return p.parsePrimary()
}

func (p *Parser) parsePrimary() (*ast.Node, error) {
    // 处理术语、短语、括号
}
```

2. **编写测试**

```go
// internal/parser/parser_test.go
func TestParserAnd(t *testing.T) {
    // 测试 AND 操作解析
}

func TestParserPrecedence(t *testing.T) {
    // 测试运算符优先级
}
```

### 第四步：实现倒排索引

1. **定义数据结构**

```go
// internal/index/index.go
type Index struct {
    documents map[string]*Document
    index     map[string]map[string]bool
}

type Document struct {
    ID      string
    Content string
}
```

2. **实现核心方法**

```go
func (idx *Index) AddDocument(doc *Document) {
    // 添加文档并建立索引
}

func (idx *Index) Search(term string) []string {
    // 搜索包含术语的文档
}

func (idx *Index) GetDocument(id string) *Document {
    // 获取文档内容
}
```

3. **实现分词器**

```go
func tokenize(text string) []string {
    // 转换为小写
    // 按空白和标点分割
    return terms
}
```

### 第五步：实现执行器

1. **查询执行**

```go
// internal/executor/executor.go
func (e *Executor) Execute(node *ast.Node) []SearchResult {
    docIDs := e.executeNode(node)
    // 计算分数并排序
    return results
}

func (e *Executor) executeNode(node *ast.Node) []string {
    switch node.Type {
    case ast.NodeTerm:
        return e.executeTerm(node.Value)
    case ast.NodePhrase:
        return e.executePhrase(node.Value)
    case ast.NodeAnd:
        return e.executeAnd(node.Left, node.Right)
    case ast.NodeOr:
        return e.executeOr(node.Left, node.Right)
    case ast.NodeNot:
        return e.executeNot(node.Children[0])
    }
}
```

2. **实现布尔运算**

```go
func intersect(a, b []string) []string {
    // 交集
}

func union(a, b []string) []string {
    // 并集
}

func difference(a, b []string) []string {
    // 差集
}
```

3. **实现相关性排序**

```go
func (e *Executor) calculateScore(node *ast.Node, doc *Document) float64 {
    terms := node.CollectTerms()
    score := 0.0
    
    for _, term := range terms {
        count := countOccurrences(doc.Content, term)
        tf := float64(count)
        idf := 1 + totalDocs / docCount
        score += tf * idf
    }
    
    return score
}
```

### 第六步：实现命令行工具

```go
// cmd/parser/main.go
func main() {
    query := os.Args[1]
    
    // 创建示例索引
    idx := createSampleIndex()
    
    // 解析查询
    l := lexer.New(query)
    tokens := l.Tokenize()
    p := parser.New(tokens)
    ast, _ := p.Parse()
    
    // 执行查询
    ex := executor.New(idx)
    results := ex.Execute(ast)
    
    // 显示结果
    for _, result := range results {
        fmt.Printf("[Score: %.2f] %s: %s\n", result.Score, result.DocID, result.Content)
    }
}
```

## 调试技巧

### 1. 打印 AST

```go
fmt.Printf("AST: %s\n", node.String())
```

### 2. 打印 Token 序列

```go
for _, tok := range tokens {
    fmt.Printf("[%s: %s] ", tok.Type, tok.Literal)
}
```

### 3. 执行跟踪

```go
func (e *Executor) executeNode(node *ast.Node) []string {
    fmt.Printf("Executing: %s\n", node.String())
    // ...
}
```

## 常见问题

### 1. 括号不匹配

**症状**：解析错误 "expected ')'"

**原因**：缺少右括号

**解决**：检查查询字符串中的括号配对

### 2. 隐式 AND 不生效

**症状**：`quick fox` 解析为两个独立术语

**原因**：AND 操作未正确处理

**解决**：确保 `parseAnd()` 处理隐式 AND

### 3. 短语查询无结果

**症状**：`"brown fox"` 返回空结果

**原因**：短语验证逻辑错误

**解决**：检查 `executePhrase()` 中的 `strings.Contains()` 调用

### 4. 大小写问题

**症状**：`Hello` 和 `hello` 搜索结果不同

**原因**：分词器未转换为小写

**解决**：确保 `tokenize()` 函数将所有文本转换为小写

## 性能优化

### 1. 索引优化

- 使用更高效的倒排索引结构
- 添加文档频率统计
- 实现索引压缩

### 2. 查询优化

- 缓存常用查询结果
- 优化 AST 遍历算法
- 减少内存分配

### 3. 并发优化

- 使用读写锁保护索引
- 并行执行独立子查询
- 异步计算相关性分数

## 扩展功能

### 1. 通配符查询

支持 `*` 和 `?` 通配符：
- `fox*` 匹配 fox、foxes、foxing
- `f?x` 匹配 fox、fax

### 2. 模糊查询

支持拼写纠错：
- `~2` 表示最多 2 个字符差异
- `quikc~` 匹配 quick

### 3. 范围查询

支持数值和日期范围：
- `price:[10 TO 100]`
- `date:[2023-01-01 TO 2023-12-31]`

### 4. 字段查询

支持指定字段搜索：
- `title:hello`
- `content:world`

## 部署建议

### 1. 命令行工具

```bash
# 编译
go build -o parser cmd/parser/main.go

# 运行
./parser "hello AND world"
```

### 2. Docker 部署

```dockerfile
FROM golang:1.21-alpine
WORKDIR /app
COPY . .
RUN go build -o parser cmd/parser/main.go
CMD ["./parser"]
```

### 3. API 服务

可以扩展为 HTTP API 服务：
- POST /search
- 请求体：{ "query": "hello AND world" }
- 响应体：{ "results": [...] }
