# 简易编译器 (Simple Compiler)

一个完整的编译器实现项目，涵盖编译器前端、中间代码、后端和解释器的核心技术。

## 项目简介

本项目是一个教学级的编译器实现，使用 C++17/20 编写，包含：

- **词法分析器 (Lexer)** - 将源代码转换为 token 流
- **语法分析器 (Parser)** - 构建抽象语法树 (AST)
- **语义分析器** - 类型检查和作用域分析
- **中间代码生成** - 三地址码和 SSA 形式
- **代码优化** - 常量折叠、死代码消除等
- **目标代码生成** - x86-64 汇编生成
- **解释器** - 直接解释执行和虚拟机

## 快速开始

### 环境要求

- C++17 或更高版本
- CMake 3.16+
- 支持 C++17 的编译器（GCC 7+, Clang 5+, MSVC 2017+）

### 编译

```bash
# 克隆项目
cd projects/simple-compiler

# 创建构建目录
mkdir build && cd build

# 配置
cmake ..

# 编译
make -j$(nproc)
```

### 运行

```bash
# 运行编译器
./bin/simple_compiler examples/hello.simp

# 运行计算器
./bin/calculator "2 + 3 * 4"

# 运行脚本解释器
./bin/script_interpreter examples/fibonacci.simp

# 运行 DSL 示例
./bin/dsl_example

# 运行测试
./bin/compiler_tests
```

## 技术分类

### 1. 词法分析 (Lexer)

词法分析器将源代码字符串转换为 token 流。

**支持的 token 类型：**
- 关键字：`let`, `var`, `const`, `if`, `else`, `while`, `for`, `fn`, `return`, `class`
- 标识符：变量名、函数名
- 字面量：整数、浮点数、字符串、布尔值
- 运算符：`+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `>`, `&&`, `||`, `!`
- 分隔符：`(`, `)`, `{`, `}`, `[`, `]`, `,`, `;`, `:`

**文件：**
- `include/token.hpp` - Token 定义
- `include/lexer.hpp` - 词法分析器接口
- `src/lexer.cpp` - 词法分析器实现

### 2. 语法分析 (Parser)

语法分析器使用递归下降法构建抽象语法树。

**支持的语法：**
- 变量声明：`let x: int = 10;`
- 函数定义：`fn add(a: int, b: int): int { ... }`
- 类定义：`class Point { x: int; y: int; }`
- 控制流：`if`, `while`, `for`, `return`
- 表达式：算术、比较、逻辑、函数调用、数组访问

**文件：**
- `include/ast.hpp` - AST 节点定义
- `include/parser.hpp` - 语法分析器接口
- `src/parser.cpp` - 语法分析器实现

### 3. 语义分析

语义分析器执行类型检查和作用域分析。

**功能：**
- 类型检查和类型推导
- 作用域分析和名称解析
- 变量定义检查
- 函数调用验证

**文件：**
- `include/semantic.hpp` - 语义分析器接口
- `src/semantic.cpp` - 语义分析器实现

### 4. 中间代码生成

生成三地址码形式的中间表示。

**特点：**
- SSA（静态单赋值）形式
- 基本块划分
- 控制流图

**文件：**
- `include/ir.hpp` - IR 定义
- `src/ir.cpp` - IR 生成器实现

### 5. 代码优化

实现多种编译器优化技术。

**优化 Pass：**
- **常量折叠** - 编译时计算常量表达式
- **死代码消除** - 移除无用代码
- **公共子表达式消除** - 避免重复计算
- **循环优化** - 循环不变量外提
- **强度削减** - 将昂贵操作替换为便宜操作
- **内联优化** - 函数内联

**文件：**
- `include/optimizer.hpp` - 优化器接口
- `src/optimizer.cpp` - 优化器实现

### 6. 目标代码生成

生成 x86-64 汇编代码。

**功能：**
- 寄存器分配（线性扫描算法）
- 栈帧管理
- 函数调用约定
- 汇编指令生成

**文件：**
- `include/codegen.hpp` - 代码生成器接口
- `src/codegen.cpp` - 代码生成器实现

### 7. 解释器

提供多种执行方式。

**执行模式：**
- **直接解释执行** - 遍历 AST 执行
- **栈式虚拟机** - 基于栈的字节码虚拟机
- **寄存式虚拟机** - 基于寄存器的字节码虚拟机

**文件：**
- `include/interpreter.hpp` - 解释器接口
- `src/interpreter.cpp` - 解释器实现

### 8. 实际应用

包含多个实际应用示例。

**示例：**
- **计算器** - 支持变量和函数的计算器
- **脚本语言** - 完整的脚本语言解释器
- **DSL 实现** - 领域特定语言示例

**文件：**
- `examples/main.cpp` - 编译器主程序
- `examples/calculator.cpp` - 计算器示例
- `examples/script_interpreter.cpp` - 脚本解释器示例
- `examples/dsl_example.cpp` - DSL 示例

## 学习路径

### 初学者路径

1. **理解词法分析**
   - 阅读 `include/token.hpp` 了解 token 类型
   - 阅读 `src/lexer.cpp` 了解如何识别 token
   - 运行测试：`./bin/compiler_tests`

2. **理解语法分析**
   - 阅读 `include/ast.hpp` 了解 AST 节点
   - 阅读 `src/parser.cpp` 了解递归下降解析
   - 尝试修改语法规则

3. **理解解释执行**
   - 阅读 `src/interpreter.cpp` 了解如何执行 AST
   - 运行计算器示例：`./bin/calculator`

### 中级路径

4. **理解语义分析**
   - 阅读 `src/semantic.cpp` 了解类型检查
   - 尝试添加新的类型检查规则

5. **理解中间代码**
   - 阅读 `include/ir.hpp` 了解 IR 表示
   - 阅读 `src/ir.cpp` 了解代码生成

6. **理解代码优化**
   - 阅读 `src/optimizer.cpp` 了解优化技术
   - 尝试实现新的优化 pass

### 高级路径

7. **理解代码生成**
   - 阅读 `src/codegen.cpp` 了解汇编生成
   - 学习 x86-64 汇编语言

8. **理解虚拟机**
   - 阅读 `src/interpreter.cpp` 中的虚拟机实现
   - 比较栈式和寄存式虚拟机

9. **扩展编译器**
   - 添加新的语言特性
   - 实现新的优化技术
   - 支持新的目标平台

## 编译运行

### 编译选项

```bash
# Debug 模式（包含调试信息）
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式（优化）
cmake -DCMAKE_BUILD_TYPE=Release ..

# 生成文档
make doc
```

### 运行测试

```bash
# 运行所有测试
ctest

# 运行特定测试
./bin/compiler_tests
```

### 使用编译器

```bash
# 查看帮助
./bin/simple_compiler --help

# 查看词法分析结果
./bin/simple_compiler --lex file.simp

# 查看语法树
./bin/simple_compiler --parse file.simp

# 查看中间代码
./bin/simple_compiler --ir file.simp

# 查看优化后的代码
./bin/simple_compiler --optimize file.simp

# 查看生成的汇编
./bin/simple_compiler --codegen file.simp

# 运行程序
./bin/simple_compiler --run file.simp

# 交互式模式
./bin/simple_compiler
```

## 项目结构

```
simple-compiler/
├── CMakeLists.txt          # CMake 配置
├── README.md               # 项目说明
├── include/                # 头文件
│   ├── token.hpp           # Token 定义
│   ├── lexer.hpp           # 词法分析器
│   ├── ast.hpp             # AST 节点
│   ├── parser.hpp          # 语法分析器
│   ├── semantic.hpp        # 语义分析器
│   ├── ir.hpp              # 中间表示
│   ├── optimizer.hpp       # 优化器
│   ├── codegen.hpp         # 代码生成器
│   └── interpreter.hpp     # 解释器
├── src/                    # 源文件
│   ├── lexer.cpp
│   ├── parser.cpp
│   ├── semantic.cpp
│   ├── ir.cpp
│   ├── optimizer.cpp
│   ├── codegen.cpp
│   └── interpreter.cpp
├── tests/                  # 测试文件
│   ├── test_lexer.cpp
│   ├── test_parser.cpp
│   └── test_interpreter.cpp
├── examples/               # 示例程序
│   ├── main.cpp
│   ├── calculator.cpp
│   ├── script_interpreter.cpp
│   └── dsl_example.cpp
└── docs/                   # 文档
    ├── 01_RESEARCH.md
    ├── 02_REQUIREMENTS.md
    ├── 03_DESIGN.md
    ├── 04_PRODUCT.md
    └── 05_DEVELOPMENT.md
```

## 语言参考

### 数据类型

- `int` - 整数类型
- `float` - 浮点类型
- `string` - 字符串类型
- `bool` - 布尔类型
- `void` - 空类型
- 数组：`int[]`, `string[]`

### 变量声明

```javascript
let x = 10;           // 不可变变量
var y = 20;           // 可变变量
const PI = 3.14;      // 常量
let z: int = 30;      // 带类型注解
```

### 函数定义

```javascript
fn add(a: int, b: int): int {
    return a + b;
}

// 带默认参数
fn greet(name: string = "World") {
    print("Hello, " + name + "!");
}
```

### 控制流

```javascript
// if 语句
if (x > 0) {
    print("positive");
} else if (x < 0) {
    print("negative");
} else {
    print("zero");
}

// while 循环
while (x > 0) {
    x = x - 1;
}

// for 循环
for (let i = 0; i < 10; i++) {
    print(i);
}
```

### 类定义

```javascript
class Point {
    x: int;
    y: int;

    fn init(x: int, y: int) {
        this.x = x;
        this.y = y;
    }

    fn distance(): float {
        return sqrt(this.x * this.x + this.y * this.y);
    }
}

let p = new Point(3, 4);
print(p.distance());  // 5.0
```

### 数组操作

```javascript
let arr = [1, 2, 3, 4, 5];
print(arr[0]);        // 1
print(len(arr));      // 5

arr[0] = 10;
print(arr[0]);        // 10
```

### 内置函数

- `print(...)` - 打印值
- `len(arr)` - 获取数组/字符串长度
- `str(x)` - 转换为字符串
- `int(x)` - 转换为整数
- `float(x)` - 转换为浮点数
- `abs(x)` - 绝对值
- `sqrt(x)` - 平方根
- `pow(x, y)` - 幂运算

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。

### 如何贡献

1. Fork 项目
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### 代码规范

- 使用 C++17 特性
- 遵循 Google C++ Style Guide
- 添加适当的注释
- 编写单元测试

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [Crafting Interpreters](https://craftinginterpreters.com/) - 编译器设计参考
- [Engineering a Compiler](https://www.elsevier.com/books/engineering-a-compiler/cooper/978-0-12-088478-0) - 编译器工程教材
- [LLVM Tutorial](https://llvm.org/docs/tutorial/) - LLVM 教程

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至：[your-email@example.com]

## 更新日志

### v1.0.0 (2024-01-01)

- 初始版本发布
- 实现完整的编译器前端
- 实现中间代码生成和优化
- 实现目标代码生成
- 实现解释器和虚拟机
- 添加计算器、脚本解释器和 DSL 示例
