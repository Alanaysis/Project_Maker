# 解释器 - Python实现

一个用Python实现的Mini语言解释器，支持变量、函数、控制流和闭包。

## 学习目标

通过这个项目，你将掌握：
- [ ] 理解解释器架构（词法分析、语法分析、AST、执行）
- [ ] 掌握AST遍历和求值
- [ ] 学会变量作用域和闭包

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Python | 主语言 | 低 |
| 递归下降解析 | 语法分析 | 中 |
| 优先级爬升 | 运算符优先级 | 中 |
| 树遍历 | AST执行 | 低 |

## 重点难点

### 重点1：词法分析（Lexer）
**为什么重要**：将字符流转换为Token流是解释器的第一步
**关键代码**：`src/lexer.py:Lexer._read_token()`
**理解要点**：
- 有限状态机的概念
- 如何识别关键字和标识符
- 如何处理字符串和数字

### 重点2：语法分析（Parser）
**为什么重要**：将Token流转换为AST是解释器的核心
**关键代码**：`src/parser.py:Parser._parse_expression()`
**理解要点**：
- 递归下降解析
- 运算符优先级爬升
- 错误处理

### 重点3：变量作用域（Environment）
**为什么重要**：作用域决定了变量的可见性和生命周期
**关键代码**：`src/environment.py:Environment`
**理解要点**：
- 词法作用域
- 作用域链
- 闭包的工作原理

## 快速开始

### 环境要求
- Python 3.10 或更高版本
- pytest（可选，用于测试）

### 运行
```bash
cd projects/interpreter/python

# 启动REPL
python3 main.py

# 运行脚本
python3 main.py examples/calculator.mini

# 执行表达式
python3 main.py -e "sqrt(144)"

# 查看AST
python3 main.py --ast examples/calculator.mini
```

### 测试
```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试
python3 -m pytest tests/test_lexer.py -v
python3 -m pytest tests/test_parser.py -v
python3 -m pytest tests/test_interpreter.py -v
```

## 语言语法

### 变量
```javascript
let x = 5;
let name = "hello";
x = 10;
x += 1;
```

### 运算
```javascript
// 算术
5 + 3 * 2    // 11
(5 + 3) * 2  // 16
2 ** 10      // 1024

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
```javascript
// 条件
if x > 5 {
    println("big");
} elif x > 0 {
    println("positive");
} else {
    println("small");
}

// 循环
let i = 0;
while i < 10 {
    println(i);
    i += 1;
}

// for-in
for x in [1, 2, 3] {
    println(x);
}
```

### 函数
```javascript
// 定义
let add = fn(a, b) {
    return a + b;
};

// 调用
let result = add(1, 2);

// 递归
let factorial = fn(n) {
    if n <= 1 { return 1; }
    return n * factorial(n - 1);
};

// 闭包
let makeCounter = fn() {
    let count = 0;
    fn() {
        count += 1;
        return count;
    }
};

let counter = makeCounter();
println(counter());  // 1
println(counter());  // 2
```

### 内置函数
```javascript
len("hello")       // 5
str(42)            // "42"
number("42")       // 42
abs(-5)            // 5
sqrt(16)           // 4
floor(3.7)         // 3
upper("hello")     // "HELLO"
contains("hi", "i") // true
range(5)           // [0, 1, 2, 3, 4]
sort([3,1,2])      // [1, 2, 3]
```

## 相关资源

- [Crafting Interpreters](https://craftinginterpreters.com/) - 优秀的解释器教程
- [Writing An Interpreter In Go](https://interpreterbook.com/) - Go语言实现
- [Pratt Parsing](https://journal.stuffwithstuff.com/2011/03/19/pratt-parsers-expression-parsing-made-easy/) - 优先级爬升算法

## 学习路径

建议学习顺序：
1. 阅读 [01_RESEARCH.md](docs/01_RESEARCH.md) 了解市场背景
2. 阅读 [02_REQUIREMENTS.md](docs/02_REQUIREMENTS.md) 理解需求
3. 阅读 [03_DESIGN.md](docs/03_DESIGN.md) 学习设计
4. 阅读 [04_PRODUCT.md](docs/04_PRODUCT.md) 理解产品思维
5. 阅读 [05_DEVELOPMENT.md](docs/05_DEVELOPMENT.md) 开始开发
6. 运行 [examples/](examples/) 中的示例
7. 阅读源代码，重点关注词法分析和语法分析
8. 完成测试中的练习

## 项目结构

```
python/
├── README.md              # 项目说明
├── main.py                # 入口点和REPL
├── src/                   # 源代码
│   ├── token.py           # Token类型定义
│   ├── lexer.py           # 词法分析器
│   ├── ast_nodes.py       # AST节点定义
│   ├── parser.py          # 语法分析器
│   ├── objects.py         # 运行时对象
│   ├── environment.py     # 环境（作用域管理）
│   ├── builtins.py        # 内置函数
│   └── interpreter.py     # 解释器/求值器
├── tests/                 # 测试
│   ├── test_lexer.py      # 词法分析器测试
│   ├── test_parser.py     # 语法分析器测试
│   └── test_interpreter.py # 解释器测试
├── examples/              # 示例脚本
│   ├── fibonacci.mini     # 斐波那契数列
│   ├── calculator.mini    # 计算器
│   ├── closure.mini       # 闭包示例
│   ├── data_processing.mini # 数据处理
│   └── game.mini          # 猜数字游戏
└── docs/                  # 文档
    ├── 01_RESEARCH.md     # 市场调研
    ├── 02_REQUIREMENTS.md # 需求分析
    ├── 03_DESIGN.md       # 技术设计
    ├── 04_PRODUCT.md      # 产品思维
    └── 05_DEVELOPMENT.md  # 开发手册
```
