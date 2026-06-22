# 解释器

[English](README_EN.md) | [中文]

## 学习目标

通过这个项目，你将掌握：
- [ ] 理解解释器架构（词法分析、语法分析、AST、执行）
- [ ] 掌握AST遍历和求值
- [ ] 学会变量作用域和闭包

## 技术栈

| 技术 | 用途 | 学习难度 | 官方文档 |
|------|------|----------|----------|
| Go | 主语言 | 中 | [go.dev](https://go.dev/) |
| 递归下降解析 | 语法分析 | 中 | - |
| 树遍历 | AST执行 | 低 | - |

## 重点难点

### 重点1：词法分析（Lexer）
**为什么重要**：将字符流转换为Token流是解释器的第一步
**关键代码**：`lexer.go:NextToken()`
**理解要点**：
- 有限状态机的概念
- 如何识别关键字和标识符
- 如何处理字符串和数字

### 重点2：语法分析（Parser）
**为什么重要**：将Token流转换为AST是解释器的核心
**关键代码**：`parser.go:parseExpression()`
**理解要点**：
- 递归下降解析
- 运算符优先级
- 错误处理

### 重点3：变量作用域（Environment）
**为什么重要**：作用域决定了变量的可见性和生命周期
**关键代码**：`env.go:Environment`
**理解要点**：
- 词法作用域
- 作用域链
- 闭包的工作原理

## 值得思考

### 1. 为什么选择树遍历而不是字节码？
**背景**：解释器有多种实现方式
**权衡**：树遍历简单但慢，字节码复杂但快
**结论**：对于学习目的，树遍历更直观

### 2. 如何处理运算符优先级？
**背景**：`1 + 2 * 3` 应该等于 `7` 而不是 `9`
**权衡**：递归下降 vs 优先级爬升
**结论**：使用优先级爬升更优雅

### 3. 闭包是如何工作的？
**背景**：函数可以捕获外部变量
**权衡**：值捕获 vs 引用捕获
**结论**：使用环境链实现引用捕获

## 快速开始

### 环境要求
- Go 1.22 或更高版本

### 安装
```bash
cd projects/interpreter

# 编译
go build -o interpreter .
```

### 运行
```bash
# 运行REPL
./interpreter

# 运行脚本文件
./interpreter run examples/fibonacci.mini

# 查看帮助
./interpreter help
```

### 测试
```bash
# 运行所有测试
go test -v ./...

# 运行特定测试
go test -v -run TestNumberExpressions
```

## 语言语法

### 变量
```
let x = 5;
let name = "hello";
x = 10;
```

### 运算
```
// 算术
5 + 3 * 2    // 11
(5 + 3) * 2  // 16

// 比较
x > 5        // true
x == 10      // true

// 逻辑
true and false  // false
not true        // false

// 字符串
"hello" + " " + "world"  // "hello world"
```

### 控制流
```
// 条件
if x > 5 {
    print "big";
} else {
    print "small";
}

// 循环
let i = 0;
while i < 10 {
    print i;
    i = i + 1;
}
```

### 函数
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

// 闭包
fn makeCounter() {
    let count = 0;
    fn increment() {
        count = count + 1;
        return count;
    }
    return increment;
}

let counter = makeCounter();
print counter();  // 1
print counter();  // 2
```

### 内置函数
```
len("hello")    // 5
str(42)         // "42"
number("42")    // 42
abs(-5)         // 5
sqrt(16)        // 4
floor(3.7)      // 3
```

## 相关资源

- [Crafting Interpreters](https://craftinginterpreters.com/) - 优秀的解释器教程
- [Writing An Interpreter In Go](https://interpreterbook.com/) - Go语言实现
- [Go AST Package](https://pkg.go.dev/go/ast) - Go标准库AST

## 学习路径

建议学习顺序：
1. 阅读 [01-RESEARCH.md](docs/01-RESEARCH.md) 了解市场背景
2. 阅读 [02-REQUIREMENTS.md](docs/02-REQUIREMENTS.md) 理解需求
3. 阅读 [03-DESIGN.md](docs/03-DESIGN.md) 学习设计
4. 阅读 [04-PRODUCT.md](docs/04-PRODUCT.md) 理解产品思维
5. 阅读 [05-DEVELOPMENT.md](docs/05-DEVELOPMENT.md) 开始开发
6. 运行 [examples/](examples/) 中的示例
7. 阅读源代码，重点关注 标记的部分
8. 完成 [LEARNING_NOTES.md](LEARNING_NOTES.md) 中的练习

## 项目结构

```
interpreter/
├── README.md              # 项目说明
├── docs/                  # 文档
│   ├── 01-RESEARCH.md     # 市场调研
│   ├── 02-REQUIREMENTS.md # 需求分析
│   ├── 03-DESIGN.md       # 技术设计
│   ├── 04-PRODUCT.md      # 产品思维
│   └── 05-DEVELOPMENT.md  # 开发手册
├── examples/              # 示例脚本
├── main.go                # 入口点和REPL
├── token.go               # Token类型定义
├── lexer.go               # 词法分析器
├── ast.go                 # AST节点定义
├── parser.go              # 语法分析器
├── object.go              # 运行时对象
├── env.go                 # 环境（作用域管理）
├── interpreter.go         # 解释器/求值器
├── *_test.go              # 测试文件
└── LEARNING_NOTES.md      # 学习笔记模板
```
