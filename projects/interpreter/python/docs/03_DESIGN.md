# 技术设计 - 解释器

## 1. 整体架构

```
源代码 -> 词法分析器 -> Token流 -> 语法分析器 -> AST -> 解释器 -> 执行结果
```

### 1.1 模块划分

```
src/
├── token.py        # Token类型定义
├── lexer.py        # 词法分析器
├── ast_nodes.py    # AST节点定义
├── parser.py       # 语法分析器
├── objects.py      # 运行时对象
├── environment.py  # 环境（作用域管理）
├── builtins.py     # 内置函数
└── interpreter.py  # 解释器/求值器
```

## 2. 词法分析器设计

### 2.1 Token类型

Token分为以下类别：
- **字面量**：NUMBER, STRING, TRUE, FALSE, NULL
- **标识符**：IDENT
- **运算符**：+, -, *, /, %, **, ==, !=, <, >, <=, >=, and, or, not
- **赋值**：=, +=, -=
- **分隔符**：(, ), {, }, [, ], ,, ;, :, .
- **关键字**：let, if, elif, else, while, for, in, fn, return, break, continue

### 2.2 词法分析流程

```
输入字符流
  ↓
跳过空白和注释
  ↓
识别Token类型
  ↓
生成Token对象
  ↓
输出Token流
```

### 2.3 关键设计决策

1. **关键字识别**：先读取完整标识符，再查表判断是否为关键字
2. **数字解析**：支持整数和浮点数，统一存储为float
3. **字符串解析**：支持转义序列（\n, \t, \\, \"）
4. **注释处理**：在词法分析阶段跳过，不生成Token

## 3. 语法分析器设计

### 3.1 AST节点层次

```
Node (基类)
├── Statement (语句)
│   ├── Program
│   ├── LetStatement
│   ├── ReturnStatement
│   ├── ExpressionStatement
│   ├── BlockStatement
│   ├── IfStatement
│   ├── WhileStatement
│   ├── ForStatement
│   ├── BreakStatement
│   └── ContinueStatement
└── Expression (表达式)
    ├── NumberLiteral
    ├── StringLiteral
    ├── BooleanLiteral
    ├── NullLiteral
    ├── ArrayLiteral
    ├── MapLiteral
    ├── Identifier
    ├── PrefixExpression
    ├── InfixExpression
    ├── AssignExpression
    ├── CallExpression
    ├── IndexExpression
    └── FunctionLiteral
```

### 3.2 运算符优先级

| 优先级 | 运算符 | 结合性 |
|--------|--------|--------|
| 1 | =, +=, -= | 右结合 |
| 2 | or | 左结合 |
| 3 | and | 左结合 |
| 4 | ==, !=, <, >, <=, >= | 左结合 |
| 5 | +, - | 左结合 |
| 6 | *, /, % | 左结合 |
| 7 | ** | 右结合 |
| 8 | -, !, not | 右结合（前缀）|
| 9 | (), [] | 左结合 |

### 3.3 优先级爬升算法

```python
def parse_expression(precedence):
    left = parse_prefix()
    while precedence < current_precedence():
        left = parse_infix(left)
    return left
```

## 4. 解释器设计

### 4.1 求值策略

使用模式匹配分派到对应的求值方法：

```python
def eval(node):
    match type(node).__name__:
        case "NumberLiteral": return Number(node.value)
        case "InfixExpression": return eval_infix(node)
        case "IfStatement": return eval_if(node)
        # ...
```

### 4.2 环境和作用域

```
全局环境
├── 变量: x, y, z
├── 函数: add, sub
└── 内置: print, len, ...

函数环境（闭包）
├── 参数: a, b
├── 局部变量: temp
└── outer -> 全局环境
```

### 4.3 闭包实现

闭包 = 函数 + 创建时的环境引用

```python
class Function:
    parameters: list[Identifier]
    body: BlockStatement
    env: Environment  # 闭包捕获的环境
```

### 4.4 控制流实现

- **return**：抛出ReturnValue信号，逐层传播到函数调用处
- **break**：抛出BreakSignal，传播到循环处
- **continue**：抛出ContinueSignal，传播到循环处

## 5. 内置函数设计

内置函数通过BuiltinFunction类实现，注册到全局环境：

```python
BUILTINS = {
    "print": BuiltinFunction("print", builtin_print),
    "len": BuiltinFunction("len", builtin_len),
    # ...
}
```

## 6. 错误处理

### 6.1 错误类型

- **LexerError**：词法分析错误（行号+列号）
- **ParserError**：语法分析错误（行号+列号）
- **RuntimeError**：运行时错误（行号）

### 6.2 错误报告

所有错误都包含位置信息，便于调试：
```
[行 5, 列 10] 语法错误: 期望 ASSIGN，得到 SEMICOLON
```
