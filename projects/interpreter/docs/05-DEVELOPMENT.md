# 05 - 开发手册：解释器

## 1. 环境准备

### 1.1 系统要求

- Go 1.22 或更高版本
- Git（可选，用于版本控制）

### 1.2 安装Go

```bash
# Ubuntu/Debian
sudo apt install golang-go

# macOS
brew install go

# 或从官网下载
# https://golang.org/dl/
```

### 1.3 验证安装

```bash
go version
# 输出: go version go1.22.2 linux/arm64
```

## 2. 项目结构

```
interpreter/
├── main.go              # 入口点和REPL
├── token.go             # Token类型定义
├── lexer.go             # 词法分析器
├── ast.go               # AST节点定义
├── parser.go            # 语法分析器
├── object.go            # 运行时对象
├── env.go               # 环境（作用域管理）
├── interpreter.go       # 解释器/求值器
├── lexer_test.go        # 词法分析器测试
├── parser_test.go       # 语法分析器测试
├── interpreter_test.go  # 解释器测试
├── go.mod               # Go模块定义
├── README.md            # 项目说明
├── LEARNING_NOTES.md    # 学习笔记模板
├── docs/                # 文档
│   ├── 01-RESEARCH.md
│   ├── 02-REQUIREMENTS.md
│   ├── 03-DESIGN.md
│   ├── 04-PRODUCT.md
│   └── 05-DEVELOPMENT.md
└── examples/            # 示例脚本
    ├── fibonacci.mini
    ├── factorial.mini
    ├── fizzbuzz.mini
    ├── closure.mini
    ├── higherorder.mini
    ├── primes.mini
    └── stringops.mini
```

## 3. 构建和运行

### 3.1 编译

```bash
cd projects/interpreter
go build -o interpreter .
```

### 3.2 运行REPL

```bash
./interpreter
```

### 3.3 运行脚本文件

```bash
./interpreter run examples/fibonacci.mini
# 或
./interpreter examples/fibonacci.mini
```

### 3.4 查看版本

```bash
./interpreter version
```

### 3.5 查看帮助

```bash
./interpreter help
```

## 4. 测试

### 4.1 运行所有测试

```bash
go test -v ./...
```

### 4.2 运行特定测试

```bash
# 词法分析器测试
go test -v -run TestNextToken

# 语法分析器测试
go test -v -run TestLetStatement

# 解释器测试
go test -v -run TestNumberExpressions
```

### 4.3 查看测试覆盖率

```bash
go test -cover ./...
```

### 4.4 生成覆盖率报告

```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## 5. 开发流程

### 5.1 添加新的Token类型

1. 在 `token.go` 中添加新的 `TokenType` 常量
2. 在 `TokenType.String()` 方法中添加对应的字符串
3. 如果是关键字，在 `keywords` map 中添加映射
4. 在 `lexer.go` 中添加识别逻辑
5. 添加测试用例

**示例**：添加 `FOR` 关键字

```go
// token.go
const (
    // ... 其他Token
    FOR  // for
)

// keywords map
var keywords = map[string]TokenType{
    // ... 其他关键字
    "for": FOR,
}
```

### 5.2 添加新的AST节点

1. 在 `ast.go` 中定义新的节点结构
2. 实现 `Node` 接口（`TokenLiteral()` 和 `String()`）
3. 如果是语句，实现 `Statement` 接口
4. 如果是表达式，实现 `Expression` 接口

**示例**：添加 `ForStatement`

```go
// ast.go
type ForStatement struct {
    Token     Token // the FOR token
    Init      Statement
    Condition Expression
    Update    Statement
    Body      *BlockStatement
}

func (fs *ForStatement) statementNode()       {}
func (fs *ForStatement) TokenLiteral() string { return fs.Token.Literal }
func (fs *ForStatement) String() string {
    return "for " + fs.Init.String() + " " +
           fs.Condition.String() + " " +
           fs.Update.String() + " " +
           fs.Body.String()
}
```

### 5.3 添加新的语法规则

1. 在 `parser.go` 中添加新的解析函数
2. 在 `parseStatement()` 中添加新的case
3. 如果涉及表达式，更新优先级表
4. 添加测试用例

**示例**：解析 `for` 循环

```go
// parser.go
func (p *Parser) parseForStatement() *ForStatement {
    stmt := &ForStatement{Token: p.curTok}

    p.nextToken()
    stmt.Init = p.parseStatement()

    p.nextToken()
    stmt.Condition = p.parseExpression(LOWEST)

    p.nextToken()
    stmt.Update = p.parseStatement()

    if !p.expectPeek(LBRACE) {
        return nil
    }

    stmt.Body = p.parseBlockStatement()
    return stmt
}
```

### 5.4 添加新的内置函数

1. 在 `interpreter.go` 中定义新的内置函数
2. 在 `NewInterpreter()` 中注册到 `builtins` map
3. 在 `interpEvalBlock()` 中也注册（用于闭包）
4. 添加测试用例

**示例**：添加 `toUpperCase` 函数

```go
// interpreter.go
func builtinToUpper(args ...Object) Object {
    if len(args) != 1 {
        return &Error{Message: fmt.Sprintf("wrong number of arguments: expected 1, got %d", len(args))}
    }
    if str, ok := args[0].(*Str); ok {
        return &Str{Value: strings.ToUpper(str.Value)}
    }
    return &Error{Message: fmt.Sprintf("argument to `toUpperCase` not supported, got %s", args[0].Type())}
}

// 在 NewInterpreter() 中添加：
interp.builtins["toUpperCase"] = &BuiltinFunction{Name: "toUpperCase", Fn: builtinToUpper}
```

## 6. 调试技巧

### 6.1 打印Token流

```go
func debugTokens(input string) {
    lexer := NewLexer(input)
    for {
        tok := lexer.NextToken()
        fmt.Printf("%-10s %q\n", tok.Type, tok.Literal)
        if tok.Type == EOF {
            break
        }
    }
}
```

### 6.2 打印AST

```go
func debugAST(input string) {
    parser := NewParser(input)
    program := parser.Parse()
    fmt.Println(program.String())
}
```

### 6.3 打印环境

```go
func debugEnv(env *Environment) {
    for name, val := range env.store {
        fmt.Printf("%s = %s\n", name, val.Inspect())
    }
    if env.outer != nil {
        fmt.Println("--- outer scope ---")
        debugEnv(env.outer)
    }
}
```

### 6.4 使用Delve调试器

```bash
# 安装Delve
go install github.com/go-delve/delve/cmd/dlv@latest

# 调试测试
dlv test -- -test.run TestNumberExpressions

# 调试程序
dlv debug . -- run examples/fibonacci.mini
```

## 7. 常见问题

### 7.1 编译错误

**问题**：`undefined: SomeType`

**解决**：检查是否正确导入包，或者类型是否在正确的文件中定义。

### 7.2 测试失败

**问题**：测试输出不匹配

**解决**：
1. 检查期望值是否正确
2. 检查是否有空白字符差异
3. 使用 `strings.TrimSpace()` 处理输出

### 7.3 运行时错误

**问题**：`undefined variable: x`

**解决**：
1. 检查变量是否已声明
2. 检查作用域是否正确
3. 检查变量名拼写

### 7.4 性能问题

**问题**：递归导致栈溢出

**解决**：
1. 减少递归深度
2. 使用迭代替代递归
3. 增加栈大小限制

## 8. 扩展指南

### 8.1 添加数组支持

1. 添加 `LBRACKET` 和 `RBRACKET` Token
2. 添加 `ArrayLiteral` 和 `IndexExpression` AST节点
3. 添加 `Array` 运行时对象
4. 添加数组相关的内置函数

### 8.2 添加字典支持

1. 添加 `COLON` Token
2. 添加 `DictLiteral` AST节点
3. 添加 `Dict` 运行时对象
4. 添加字典相关的内置函数

### 8.3 添加类支持

1. 添加 `CLASS` 和 `THIS` 关键字
2. 添加 `ClassStatement` 和 `MethodStatement` AST节点
3. 添加 `Class` 和 `Instance` 运行时对象
4. 实现方法调用和属性访问

### 8.4 添加模块系统

1. 添加 `IMPORT` 和 `EXPORT` 关键字
2. 添加 `ImportStatement` AST节点
3. 实现模块加载和缓存
4. 实现命名空间管理

## 9. 最佳实践

### 9.1 代码风格

- 使用 `gofmt` 格式化代码
- 遵循 Go 命名规范
- 添加适当的注释
- 保持函数简短

### 9.2 测试

- 每个公共函数都应该有测试
- 测试应该覆盖正常和异常情况
- 使用表格驱动测试
- 保持测试独立

### 9.3 错误处理

- 提供清晰的错误信息
- 包含行号和列号
- 使用有意义的错误类型
- 不要忽略错误

### 9.4 文档

- 每个文件都应该有包注释
- 每个公共函数都应该有文档注释
- 复杂的逻辑应该有行内注释
- 保持文档与代码同步

## 10. 学习资源

### 10.1 书籍

- [Crafting Interpreters](https://craftinginterpreters.com/) - Bob Nystrom
- [Writing An Interpreter In Go](https://interpreterbook.com/) - Thorsten Ball
- [Compilers: Principles, Techniques, and Tools](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools) - Aho, Lam, Sethi, Ullman

### 10.2 在线资源

- [Let's Build a Compiler](https://compilers.iecc.com/crenshaw/) - Jack Crenshaw
- [Parsing Techniques](https://dickgrune.com/Books/PTAPG_2nd_Edition/) - Dick Grune
- [Go AST Package](https://pkg.go.dev/go/ast) - Go标准库

### 10.3 视频教程

- [Computerphile - How interpreters work](https://www.youtube.com/watch?v=OjaATo7koLe)
- [Creel - Writing a Compiler](https://www.youtube.com/watch?v=vcSijXMaQ2E)

## 11. 总结

本手册提供了解释器项目的完整开发指南。通过遵循这些步骤和最佳实践，你可以：

1. 成功构建和运行解释器
2. 理解每个组件的工作原理
3. 扩展解释器添加新功能
4. 调试和解决常见问题

记住，这是一个**学习项目**。重点是理解原理，而不是追求完美。享受编程的乐趣！
