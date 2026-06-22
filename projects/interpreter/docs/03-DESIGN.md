# 03 - 技术设计：解释器

## 1. 整体架构

```
源代码字符串
    |
    v
+----------+
|   Lexer  |  词法分析
+----------+
    |
    v
+----------+
|  Tokens  |  Token流
+----------+
    |
    v
+----------+
|  Parser  |  语法分析
+----------+
    |
    v
+----------+
|   AST    |  抽象语法树
+----------+
    |
    v
+----------+
|Interp.   |  解释执行
+----------+
    |
    v
  输出结果
```

## 2. 文件结构

```
interpreter/
├── main.go           # 入口点和REPL
├── token.go          # Token类型定义
├── lexer.go          # 词法分析器
├── ast.go            # AST节点定义
├── parser.go         # 语法分析器
├── object.go         # 运行时对象
├── env.go            # 环境（作用域管理）
├── interpreter.go    # 解释器/求值器
├── *_test.go         # 测试文件
├── examples/         # 示例脚本
└── docs/             # 文档
```

## 3. 词法分析器设计

### 3.1 Token类型

```go
type TokenType int

const (
    ILLEGAL TokenType = iota
    EOF

    // 字面量
    NUMBER  // 123, 3.14
    STRING  // "hello"
    IDENT   // 变量名

    // 关键字
    LET      // let
    FN       // fn
    IF       // if
    ELSE     // else
    WHILE    // while
    RETURN   // return
    PRINT    // print
    TRUE     // true
    FALSE    // false
    AND      // and
    OR       // or
    NOT      // not

    // 运算符
    PLUS     // +
    MINUS    // -
    STAR     // *
    SLASH    // /
    PERCENT  // %
    ASSIGN   // =
    EQ       // ==
    NEQ      // !=
    LT       // <
    GT       // >
    LTE      // <=
    GTE      // >=

    // 分隔符
    LPAREN   // (
    RPAREN   // )
    LBRACE   // {
    RBRACE   // }
    COMMA    // ,
    SEMICOL  // ;
)
```

### 3.2 Lexer结构

```go
type Lexer struct {
    input   string  // 输入源代码
    pos     int     // 当前位置
    readPos int     // 下一个读取位置
    ch      byte    // 当前字符
    line    int     // 当前行号
    col     int     // 当前列号
}
```

### 3.3 核心方法

- `NewLexer(input string) *Lexer` - 创建新的词法分析器
- `NextToken() Token` - 获取下一个Token
- `readChar()` - 读取下一个字符
- `peekChar()` - 预览下一个字符
- `readIdentifier()` - 读取标识符
- `readNumber()` - 读取数字
- `readString()` - 读取字符串
- `skipWhitespace()` - 跳过空白
- `skipComment()` - 跳过注释

### 3.4 关键字识别

使用map将关键字字符串映射到Token类型：

```go
var keywords = map[string]TokenType{
    "let":    LET,
    "fn":     FN,
    "if":     IF,
    "else":   ELSE,
    "while":  WHILE,
    "return": RETURN,
    "print":  PRINT,
    "true":   TRUE,
    "false":  FALSE,
    "and":    AND,
    "or":     OR,
    "not":    NOT,
}
```

## 4. 语法分析器设计

### 4.1 递归下降解析

使用递归下降方法，每个语法规则对应一个解析函数。

### 4.2 运算符优先级

```go
const (
    _ int = iota
    LOWEST
    OR_PREC      // or
    AND_PREC     // and
    EQUALS       // == !=
    LESSGREATER  // < > <= >=
    SUM          // + -
    PRODUCT      // * / %
    PREFIX       // -X or !X
    CALL         // myFunction(X)
)

var precedences = map[TokenType]int{
    OR:     OR_PREC,
    AND:    AND_PREC,
    EQ:     EQUALS,
    NEQ:    EQUALS,
    LT:     LESSGREATER,
    GT:     LESSGREATER,
    LTE:    LESSGREATER,
    GTE:    LESSGREATER,
    PLUS:   SUM,
    MINUS:  SUM,
    STAR:   PRODUCT,
    SLASH:  PRODUCT,
    PERCENT: PRODUCT,
    LPAREN: CALL,
}
```

### 4.3 Parser结构

```go
type Parser struct {
    lexer   *Lexer
    curTok  Token  // 当前Token
    peekTok Token  // 下一个Token
    errors  []string
}
```

### 4.4 解析流程

1. `Parse() *Program` - 解析整个程序
2. `parseStatement() Statement` - 解析语句
3. `parseExpression(precedence int) Expression` - 解析表达式（优先级爬升）

### 4.5 语句解析

- `parseLetStatement()` - 解析变量声明
- `parseAssignStatement()` - 解析变量赋值
- `parseReturnStatement()` - 解析返回语句
- `parsePrintStatement()` - 解析打印语句
- `parseFunctionStatement()` - 解析函数声明
- `parseIfStatement()` - 解析条件语句
- `parseWhileStatement()` - 解析循环
- `parseBlockStatement()` - 解析代码块

### 4.6 表达式解析

- `parseIdentifier()` - 解析标识符
- `parseNumberLiteral()` - 解析数字
- `parseStringLiteral()` - 解析字符串
- `parseBooleanLiteral()` - 解析布尔值
- `parsePrefixExpression()` - 解析前缀表达式
- `parseInfixExpression()` - 解析中缀表达式
- `parseGroupedExpression()` - 解析括号表达式
- `parseCallExpression()` - 解析函数调用

## 5. AST设计

### 5.1 节点接口

```go
type Node interface {
    TokenLiteral() string
    String() string
}

type Statement interface {
    Node
    statementNode()
}

type Expression interface {
    Node
    expressionNode()
}
```

### 5.2 语句节点

| 节点 | 用途 |
|------|------|
| Program | 程序根节点 |
| LetStatement | `let x = expr;` |
| AssignStatement | `x = expr;` |
| ReturnStatement | `return expr;` |
| PrintStatement | `print expr;` |
| ExpressionStatement | `expr;` |
| BlockStatement | `{ stmts }` |
| IfStatement | `if cond { } else { }` |
| WhileStatement | `while cond { }` |
| FunctionStatement | `fn name(params) { }` |

### 5.3 表达式节点

| 节点 | 用途 |
|------|------|
| Identifier | 变量名 |
| NumberLiteral | 数字 |
| StringLiteral | 字符串 |
| BooleanLiteral | true/false |
| PrefixExpression | `-x`, `not x` |
| InfixExpression | `x + y` |
| CallExpression | `fn(args)` |

## 6. 运行时对象设计

### 6.1 对象类型

```go
type Object interface {
    Type() ObjectType
    Inspect() string
}
```

| 类型 | 说明 |
|------|------|
| Number | 浮点数 |
| Str | 字符串 |
| Boolean | 布尔值 |
| Null | 空值 |
| ReturnValue | 返回值包装 |
| Function | 用户定义函数 |
| BuiltinFunction | 内置函数 |
| Error | 运行时错误 |

### 6.2 环境（作用域）

```go
type Environment struct {
    store map[string]Object  // 变量存储
    outer *Environment       // 外层环境
}
```

**关键方法**：
- `NewEnvironment()` - 创建顶层环境
- `NewEnclosedEnvironment(outer)` - 创建子环境
- `Get(name)` - 查找变量（沿作用域链）
- `Set(name, val)` - 设置变量

## 7. 解释器设计

### 7.1 Interpreter结构

```go
type Interpreter struct {
    env      *Environment
    output   *strings.Builder
    builtins map[string]*BuiltinFunction
}
```

### 7.2 求值流程

```go
func (interp *Interpreter) Eval(node Node) Object {
    switch n := node.(type) {
    case *Program:
        return interp.evalProgram(n)
    case *LetStatement:
        return interp.evalLetStatement(n)
    // ... 其他节点类型
    }
}
```

### 7.3 作用域管理

- 每个函数调用创建新的环境
- 环境链接到定义时的环境（闭包）
- 变量查找沿作用域链向上

### 7.4 函数调用

```go
func applyFunction(fn *Function, args []Object) Object {
    // 1. 创建新环境
    extendedEnv := NewEnclosedEnvironment(fn.Env)

    // 2. 绑定参数
    for i, param := range fn.Params {
        extendedEnv.Set(param.Value, args[i])
    }

    // 3. 执行函数体
    result := Eval(fn.Body, extendedEnv)

    // 4. 解包返回值
    if retVal, ok := result.(*ReturnValue); ok {
        return retVal.Value
    }
    return result
}
```

## 8. 关键设计决策

### 8.1 为什么用递归下降？

- 实现简单直观
- 容易理解和调试
- 适合小型语言
- 错误信息清晰

### 8.2 为什么用map存储变量？

- O(1)查找时间
- 实现简单
- 适合教学目的

### 8.3 为什么用接口？

- Go的惯用方式
- 支持多态
- 类型安全

### 8.4 为什么用树遍历？

- 最简单的解释器架构
- 容易理解执行流程
- 适合学习目的

## 9. 测试策略

### 9.1 单元测试

- 词法分析器：测试各种Token类型
- 语法分析器：测试各种语法结构
- 解释器：测试各种执行场景

### 9.2 集成测试

- 完整程序执行
- 错误处理
- 边界情况

### 9.3 示例程序

- Fibonacci
- Factorial
- FizzBuzz
- 闭包演示
- 高阶函数
