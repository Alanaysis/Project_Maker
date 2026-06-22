# 01 - 市场调研：解释器

## 1. 什么是解释器？

解释器是一种程序，它直接执行用某种编程语言编写的指令，而不需要预先编译成机器码。与编译器不同，解释器逐行读取源代码，分析并立即执行。

### 1.1 解释器 vs 编译器

| 特性 | 解释器 | 编译器 |
|------|--------|--------|
| 执行方式 | 逐行解释执行 | 先编译再执行 |
| 执行速度 | 较慢 | 较快 |
| 错误发现 | 运行时发现 | 编译时发现 |
| 调试 | 容易，可交互 | 较难 |
| 代表语言 | Python, Ruby, JavaScript (部分) | C, C++, Rust |

### 1.2 现代语言的趋势

现代语言往往采用混合策略：
- **Python**: 编译为字节码，然后在虚拟机上解释执行
- **Java**: 编译为字节码，JIT编译执行
- **JavaScript**: V8引擎先解释执行，热点代码JIT编译

## 2. 常见的解释器架构

### 2.1 树遍历解释器（Tree-Walking Interpreter）

**工作原理**：
1. 解析源代码生成AST（抽象语法树）
2. 递归遍历AST节点
3. 对每个节点执行相应的操作

**优点**：
- 实现简单直观
- 容易理解和调试
- 适合学习和原型开发

**缺点**：
- 执行速度较慢
- 每次执行都需要遍历树

**代表实现**：早期的CPython、MRI Ruby

### 2.2 字节码解释器（Bytecode Interpreter）

**工作原理**：
1. 将源代码编译为字节码（中间表示）
2. 虚拟机逐条执行字节码指令

**优点**：
- 执行速度较快
- 字节码比AST更紧凑
- 可以进行优化

**缺点**：
- 实现复杂度较高
- 需要额外的编译步骤

**代表实现**：CPython (PVM)、Lua VM、JVM

### 2.3 JIT编译器（Just-In-Time Compiler）

**工作原理**：
1. 初始阶段解释执行
2. 识别热点代码
3. 将热点代码编译为机器码
4. 直接执行机器码

**优点**：
- 热点代码执行速度极快
- 兼顾启动速度和运行速度

**缺点**：
- 实现非常复杂
- 需要运行时编译环境

**代表实现**：V8 (JavaScript)、JVM HotSpot

## 3. 解释器的核心组件

### 3.1 词法分析器（Lexer/Tokenizer）

**作用**：将源代码字符流转换为Token流

**示例**：
```
输入: let x = 5 + 3;
输出: [LET] [IDENT:"x"] [ASSIGN] [NUMBER:5] [PLUS] [NUMBER:3] [SEMICOL]
```

**关键概念**：
- 有限状态机（FSM）
- 正则表达式匹配
- Token类型定义

### 3.2 语法分析器（Parser）

**作用**：将Token流转换为抽象语法树（AST）

**常见方法**：
- 递归下降解析（Recursive Descent）
- 运算符优先级解析（Operator Precedence）
- LR/LALR解析器生成器（yacc/bison）

**关键概念**：
- 上下文无关文法（CFG）
- BNF表示法
- AST节点设计

### 3.3 抽象语法树（AST）

**作用**：表示程序的结构化表示

**示例**（`let x = 5 + 3;`）：
```
LetStatement
├── Name: Identifier("x")
└── Value: InfixExpression
    ├── Left: NumberLiteral(5)
    ├── Operator: "+"
    └── Right: NumberLiteral(3)
```

### 3.4 求值器/解释器（Evaluator）

**作用**：遍历AST并执行计算

**关键概念**：
- 环境（Environment）：存储变量绑定
- 作用域（Scope）：变量的可见范围
- 调用栈（Call Stack）：函数调用管理

## 4. 变量作用域

### 4.1 词法作用域（Lexical Scoping）

变量的作用域在代码编写时就确定了，而不是在运行时。

```
let x = 10;

fn foo() {
    print x;  // 可以访问外层的 x
}

fn bar() {
    let x = 20;  // 创建新的局部变量
    print x;     // 打印 20
}

foo();  // 打印 10
bar();  // 打印 20
print x;  // 仍然打印 10
```

### 4.2 作用域链

当查找变量时，解释器会沿着作用域链向上查找：
1. 当前函数作用域
2. 外层函数作用域
3. 全局作用域

### 4.3 闭包（Closure）

函数可以捕获其定义时的环境，即使在外层函数返回后仍然可以访问。

```
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

## 5. 现有实现参考

### 5.1 Crafting Interpreters (Bob Nystrom)

- **语言**：Java/C
- **架构**：树遍历 + 字节码
- **特点**：优秀的教程，循序渐进
- **链接**：https://craftinginterpreters.com/

### 5.2 Writing An Interpreter In Go (Thorsten Ball)

- **语言**：Go
- **架构**：树遍历
- **特点**：代码简洁，适合Go开发者
- **链接**：https://interpreterbook.com/

### 5.3 Go实现的脚本语言

| 名称 | 特点 | 链接 |
|------|------|------|
| GopherLua | Lua 5.1 VM | https://github.com/yuin/gopher-lua |
| Tengo | 脚本语言 | https://github.com/d5/tengo |
| Expr | 表达式引擎 | https://github.com/expr-lang/expr |
| Anko | 类Go语法 | https://github.com/mattn/anko |

## 6. 设计决策

### 6.1 我们的选择：树遍历解释器

**原因**：
1. **学习价值高**：清晰展示解释器的完整流程
2. **实现简单**：不需要字节码和虚拟机
3. **调试容易**：直接在AST上操作
4. **适合教学**：代码量适中，容易理解

### 6.2 语言特性规划

**最小可用版本**：
- 变量声明和赋值
- 算术运算
- 比较和逻辑运算
- 条件语句（if/else）
- 循环（while）
- 函数定义和调用
- 字符串操作
- 内置函数
- 注释

**未来扩展**：
- 数组/列表
- 字典/哈希表
- 类和对象
- 模块系统
- 错误处理（try/catch）

## 7. 学习路径

1. **理解词法分析**：学习如何将字符转换为Token
2. **理解语法分析**：学习如何构建AST
3. **理解AST设计**：学习如何设计节点类型
4. **理解求值过程**：学习如何遍历AST执行
5. **理解作用域**：学习环境和闭包
6. **理解内置函数**：学习如何扩展语言能力

## 8. 总结

解释器是理解编程语言实现的基础。通过实现一个简单的树遍历解释器，我们可以深入理解：

- 编程语言是如何工作的
- 代码是如何被执行的
- 变量和作用域是如何管理的
- 函数调用是如何实现的

这些知识对于编写更好的代码、理解语言设计决策、开发DSL和构建编译器工具都有重要的帮助。
