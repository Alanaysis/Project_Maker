# 开发手册 - 解释器

## 1. 环境配置

### 1.1 系统要求
- Python 3.10 或更高版本
- pytest（测试框架）

### 1.2 安装依赖
```bash
pip install pytest
```

### 1.3 项目结构
```
python/
├── main.py              # 主入口（REPL和脚本执行）
├── src/
│   ├── __init__.py
│   ├── token.py         # Token类型定义
│   ├── lexer.py         # 词法分析器
│   ├── ast_nodes.py     # AST节点定义
│   ├── parser.py        # 语法分析器
│   ├── objects.py       # 运行时对象
│   ├── environment.py   # 环境（作用域管理）
│   ├── builtins.py      # 内置函数
│   └── interpreter.py   # 解释器/求值器
├── tests/
│   ├── __init__.py
│   ├── test_lexer.py    # 词法分析器测试
│   ├── test_parser.py   # 语法分析器测试
│   └── test_interpreter.py  # 解释器测试
├── examples/
│   ├── fibonacci.mini   # 斐波那契数列
│   ├── calculator.mini  # 计算器
│   ├── closure.mini     # 闭包示例
│   ├── data_processing.mini  # 数据处理
│   └── game.mini        # 猜数字游戏
└── docs/
    ├── 01_RESEARCH.md   # 市场调研
    ├── 02_REQUIREMENTS.md  # 需求分析
    ├── 03_DESIGN.md     # 技术设计
    ├── 04_PRODUCT.md    # 产品思维
    └── 05_DEVELOPMENT.md  # 开发手册
```

## 2. 快速开始

### 2.1 启动REPL
```bash
cd projects/interpreter/python
python3 main.py
```

### 2.2 运行脚本
```bash
python3 main.py examples/calculator.mini
```

### 2.3 执行表达式
```bash
python3 main.py -e "sqrt(144)"
```

### 2.4 查看AST
```bash
python3 main.py --ast examples/calculator.mini
```

## 3. 测试

### 3.1 运行所有测试
```bash
python3 -m pytest tests/ -v
```

### 3.2 运行特定测试
```bash
python3 -m pytest tests/test_lexer.py -v
python3 -m pytest tests/test_parser.py -v
python3 -m pytest tests/test_interpreter.py -v
```

### 3.3 测试覆盖率
```bash
python3 -m pytest tests/ --cov=src
```

## 4. 语言语法参考

### 4.1 变量
```javascript
let x = 5;
let name = "hello";
let flag = true;
let nothing = null;

x = 10;        // 赋值
x += 5;        // 复合赋值
x -= 3;
```

### 4.2 数据类型
```javascript
// 数字
42
3.14
-5

// 字符串
"hello"
"line1\nline2"

// 布尔
true
false

// null
null

// 数组
[1, 2, 3]
["a", "b", "c"]

// 映射
{"name": "Alice", "age": 30}
```

### 4.3 运算符
```javascript
// 算术
5 + 3     // 8
5 - 3     // 2
5 * 3     // 15
10 / 3    // 3.333...
10 % 3    // 1
2 ** 10   // 1024

// 比较
5 == 5    // true
5 != 3    // true
5 < 3     // false
5 > 3     // true
5 <= 5    // true
5 >= 3    // true

// 逻辑
true and false  // false
true or false   // true
not true        // false
!false          // true
```

### 4.4 控制流
```javascript
// if/elif/else
if x > 10 {
    print("big");
} elif x > 5 {
    print("medium");
} else {
    print("small");
}

// while
let i = 0;
while i < 10 {
    print(i);
    i += 1;
}

// for-in
for x in [1, 2, 3] {
    print(x);
}

// break/continue
while true {
    if x > 10 { break; }
    if x % 2 == 0 { continue; }
    x += 1;
}
```

### 4.5 函数
```javascript
// 定义
let add = fn(a, b) {
    return a + b;
};

// 调用
add(1, 2);  // 3

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
counter();  // 1
counter();  // 2
```

### 4.6 内置函数
```javascript
// 输出
print("hello", "world");
println("hello");

// 类型转换
str(42)          // "42"
number("42")     // 42
bool(1)          // true
type(42)         // "number"

// 字符串
len("hello")     // 5
upper("hello")   // "HELLO"
lower("HELLO")   // "hello"
trim("  hi  ")   // "hi"
split("a,b,c", ",")  // ["a", "b", "c"]
join(["a","b"], "-")  // "a-b"
contains("hello", "ell")  // true

// 数组
push([1,2], 3)   // [1, 2, 3]
pop([1,2,3])     // 3
sort([3,1,2])    // [1, 2, 3]
reverse([1,2,3]) // [3, 2, 1]
range(5)         // [0, 1, 2, 3, 4]

// 数学
abs(-5)          // 5
sqrt(16)         // 4
floor(3.7)       // 3
ceil(3.2)        // 4
round(3.5)       // 4
min(3, 5)        // 3
max(3, 5)        // 5
```

## 5. 添加新特性

### 5.1 添加新的Token类型
1. 在 `token.py` 的 `TokenType` 枚举中添加新类型
2. 在 `lexer.py` 的 `_read_token` 方法中添加识别逻辑
3. 添加测试

### 5.2 添加新的AST节点
1. 在 `ast_nodes.py` 中定义新的节点类
2. 在 `parser.py` 中添加解析逻辑
3. 在 `interpreter.py` 中添加求值逻辑
4. 添加测试

### 5.3 添加新的内置函数
1. 在 `builtins.py` 中实现函数
2. 在 `BUILTINS` 字典中注册
3. 添加测试

## 6. 常见问题

### Q: 为什么选择树遍历而不是字节码？
A: 树遍历更直观，适合学习。字节码需要额外的编译步骤和虚拟机，复杂度更高。

### Q: 如何处理运算符优先级？
A: 使用优先级爬升算法。每个运算符有优先级数字，数字越大优先级越高。

### Q: 闭包是如何工作的？
A: 闭包是函数加上创建时的环境引用。当函数访问外部变量时，会沿着环境链查找。

### Q: 如何扩展语言？
A: 按照"添加新特性"的步骤，在词法、语法、执行三个层面分别添加支持。
