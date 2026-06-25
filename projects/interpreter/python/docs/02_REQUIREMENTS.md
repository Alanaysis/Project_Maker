# 需求分析 - 解释器

## 1. 功能需求

### 1.1 词法分析
- [x] 支持整数和浮点数
- [x] 支持字符串字面量（双引号）
- [x] 支持布尔字面量（true/false）
- [x] 支持null字面量
- [x] 支持标识符和关键字
- [x] 支持算术运算符（+, -, *, /, %, **）
- [x] 支持比较运算符（==, !=, <, >, <=, >=）
- [x] 支持逻辑运算符（and, or, not）
- [x] 支持赋值运算符（=, +=, -=）
- [x] 支持单行和多行注释
- [x] 支持字符串转义序列

### 1.2 语法分析
- [x] 变量声明（let）
- [x] 表达式语句
- [x] return语句
- [x] if/elif/else条件语句
- [x] while循环
- [x] for-in循环
- [x] break和continue
- [x] 函数定义和调用
- [x] 数组字面量
- [x] 映射字面量
- [x] 索引访问
- [x] 运算符优先级（9级）

### 1.3 解释执行
- [x] 数字运算
- [x] 字符串操作
- [x] 布尔逻辑
- [x] 变量作用域
- [x] 函数调用
- [x] 闭包
- [x] 递归
- [x] 短路求值

### 1.4 内置函数
- [x] 输出：print, println, input
- [x] 类型转换：str, number, bool, type
- [x] 字符串：len, upper, lower, trim, split, join, replace, contains, starts_with, ends_with
- [x] 数组：push, pop, sort, reverse, range
- [x] 数学：abs, sqrt, floor, ceil, round, min, max

### 1.5 错误处理
- [x] 词法错误（意外字符、未终止字符串）
- [x] 语法错误（期望的Token不匹配）
- [x] 运行时错误（类型不匹配、除以零、未定义变量）

## 2. 非功能需求

### 2.1 性能
- 树遍历解释器，适合学习和原型开发
- 不追求极致性能

### 2.2 可维护性
- 模块化设计（词法、语法、执行分离）
- 清晰的代码结构
- 完善的测试覆盖

### 2.3 可扩展性
- 易于添加新的语言特性
- 易于添加新的内置函数
- 支持自定义数据类型

## 3. 用例

### 3.1 脚本执行
```
python main.py script.mini
```

### 3.2 交互式REPL
```
python main.py
>>> 1 + 2
3
```

### 3.3 表达式求值
```
python main.py -e "sqrt(144)"
12
```

### 3.4 AST查看
```
python main.py --ast script.mini
```
