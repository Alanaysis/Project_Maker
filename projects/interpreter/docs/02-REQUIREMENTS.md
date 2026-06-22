# 02 - 需求分析：解释器

## 1. 项目目标

实现一个简易的脚本语言解释器，支持基本的变量、运算、控制流、函数等特性。

### 1.1 学习目标

- 理解解释器架构（词法分析、语法分析、AST、执行）
- 掌握AST遍历和求值
- 学会变量作用域和闭包

### 1.2 核心价值

通过亲手实现一个解释器，深入理解编程语言的工作原理。

## 2. 功能需求

### 2.1 词法分析器（Lexer）

**输入**：源代码字符串

**输出**：Token流

**支持的Token类型**：

| 类型 | 示例 | 说明 |
|------|------|------|
| 关键字 | let, fn, if, else, while, return, print, true, false | 语言保留字 |
| 标识符 | x, myVar, add | 变量和函数名 |
| 数字 | 42, 3.14 | 整数和浮点数 |
| 字符串 | "hello", "world" | 双引号字符串 |
| 运算符 | +, -, *, /, %, =, ==, !=, <, >, <=, >= | 算术和比较运算 |
| 逻辑运算 | and, or, not | 逻辑运算 |
| 分隔符 | (, ), {, }, ,, ; | 语法分隔 |
| 注释 | // this is a comment | 单行注释 |

### 2.2 语法分析器（Parser）

**输入**：Token流

**输出**：抽象语法树（AST）

**支持的语法结构**：

#### 变量声明
```
let x = 5;
let name = "hello";
let result = 1 + 2;
```

#### 变量赋值
```
x = 10;
name = "world";
```

#### 表达式
```
// 算术
5 + 3 * 2
(5 + 3) * 2
10 / 2 - 1

// 比较
x > 5
y == 10
name != "hello"

// 逻辑
x > 5 and y < 10
not false
a or b

// 字符串
"hello" + " " + "world"
```

#### 条件语句
```
if x > 5 {
    print "big";
}

if x > 5 {
    print "big";
} else {
    print "small";
}

// 嵌套
if x > 10 {
    print "very big";
} else if x > 5 {
    print "big";
} else {
    print "small";
}
```

#### 循环
```
let i = 0;
while i < 10 {
    print i;
    i = i + 1;
}
```

#### 函数
```
// 定义
fn add(a, b) {
    return a + b;
}

// 调用
let result = add(1, 2);

// 递归
fn factorial(n) {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}
```

#### 打印语句
```
print "hello";
print 42;
print x;
print 1 + 2;
```

#### 注释
```
// 这是单行注释
let x = 5; // 行内注释
```

### 2.3 AST节点

| 节点类型 | 说明 |
|----------|------|
| Program | 程序根节点 |
| LetStatement | 变量声明 |
| AssignStatement | 变量赋值 |
| ReturnStatement | 返回语句 |
| PrintStatement | 打印语句 |
| ExpressionStatement | 表达式语句 |
| BlockStatement | 代码块 |
| IfStatement | 条件语句 |
| WhileStatement | 循环语句 |
| FunctionStatement | 函数声明 |
| Identifier | 标识符 |
| NumberLiteral | 数字字面量 |
| StringLiteral | 字符串字面量 |
| BooleanLiteral | 布尔字面量 |
| PrefixExpression | 前缀表达式 |
| InfixExpression | 中缀表达式 |
| CallExpression | 函数调用 |

### 2.4 解释器（Interpreter）

**功能**：
- 遍历AST并执行
- 管理变量环境
- 支持函数调用和递归
- 支持闭包
- 提供内置函数

**内置函数**：

| 函数 | 说明 | 示例 |
|------|------|------|
| len(str) | 字符串长度 | len("hello") // 5 |
| str(val) | 转换为字符串 | str(42) // "42" |
| number(str) | 转换为数字 | number("42") // 42 |
| abs(n) | 绝对值 | abs(-5) // 5 |
| sqrt(n) | 平方根 | sqrt(16) // 4 |
| floor(n) | 向下取整 | floor(3.7) // 3 |
| input() | 读取输入 | let x = input(); |

### 2.5 交互模式（REPL）

- 交互式命令行
- 逐行输入和执行
- 错误恢复
- 内置命令（help, version, quit）

### 2.6 文件执行

- 从文件加载和执行脚本
- 支持命令行参数

## 3. 非功能需求

### 3.1 性能

- 词法分析：O(n)，n为源代码长度
- 语法分析：O(n)
- 执行：取决于程序复杂度

### 3.2 错误处理

**词法错误**：
- 非法字符
- 未闭合的字符串

**语法错误**：
- 缺少分号
- 括号不匹配
- 意外的Token

**运行时错误**：
- 未定义的变量
- 类型不匹配
- 除以零
- 函数参数数量错误

### 3.3 可扩展性

- 易于添加新的Token类型
- 易于添加新的AST节点
- 易于添加新的内置函数

### 3.4 代码质量

- 清晰的代码结构
- 适当的注释
- 完整的测试覆盖

## 4. 技术约束

- **语言**：Go 1.22
- **依赖**：无外部依赖
- **平台**：跨平台（Linux, macOS, Windows）

## 5. 验收标准

### 5.1 基础功能

- [x] 词法分析器正确识别所有Token类型
- [x] 语法分析器正确构建AST
- [x] 解释器正确执行基本程序
- [x] 变量声明和赋值正常工作
- [x] 算术运算结果正确
- [x] 比较和逻辑运算正常工作

### 5.2 控制流

- [x] if/else条件语句正常工作
- [x] while循环正常工作
- [x] 嵌套控制流正常工作

### 5.3 函数

- [x] 函数定义和调用正常工作
- [x] 递归调用正常工作
- [x] 闭包正常工作
- [x] 高阶函数正常工作

### 5.4 错误处理

- [x] 词法错误有清晰的错误信息
- [x] 语法错误有清晰的错误信息
- [x] 运行时错误有清晰的错误信息

### 5.5 测试

- [x] 词法分析器测试通过
- [x] 语法分析器测试通过
- [x] 解释器测试通过
- [x] 示例程序可以正确执行
