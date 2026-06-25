# 04 - 产品思考：C++ 编译期计算

## 学习目标

### 初级目标：理解编译期计算的概念

**完成标准**：
- 能够解释 constexpr、consteval、constinit 的区别
- 能够编写简单的 constexpr 函数
- 能够使用编译期断言验证结果

**学习时间**：2-3 天

### 中级目标：掌握编译期数据结构和算法

**完成标准**：
- 能够实现 fixed_string、compile_time_array 等数据结构
- 能够实现编译期数学函数和排序算法
- 能够在实际项目中应用编译期计算

**学习时间**：1 周

### 高级目标：深入理解和应用

**完成标准**：
- 能够设计复杂的编译期系统（状态机、反射等）
- 能够优化编译时间和运行时性能
- 能够解决编译期计算的常见问题

**学习时间**：2 周

## 关键要点

### 1. constexpr 不仅仅是常量

**常见误解**：constexpr 只是用来定义常量。

**正确理解**：constexpr 表示"可以在编译期求值"，但也可以在运行时求值。

```cpp
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

// 编译期使用
constexpr int compile_time_result = factorial(10);  // 编译期计算

// 运行时使用
int runtime_n = 10;
int runtime_result = factorial(runtime_n);  // 运行时计算
```

### 2. consteval 强制编译期求值

**使用场景**：当你需要确保函数必须在编译期求值时。

```cpp
consteval int must_be_constexpr(int n) {
    return n * n;
}

// 正确：编译期调用
constexpr int result = must_be_constexpr(10);

// 错误：不能在运行时调用
int runtime_n = 10;
// int result = must_be_constexpr(runtime_n);  // 编译错误
```

### 3. constinit 解决静态初始化顺序问题

**问题**：全局变量的初始化顺序在不同翻译单元之间是未定义的。

```cpp
// 问题代码
int global_a = 1;
int global_b = global_a + 1;  // 可能先于 global_a 初始化
```

**解决方案**：使用 constinit 保证常量初始化。

```cpp
constinit int global_a = 1;
constinit int global_b = global_a + 1;  // 保证在编译期初始化
```

### 4. 编译期计算有成本

**编译时间**：复杂的编译期计算会增加编译时间。

**代码膨胀**：模板实例化可能导致代码体积增大。

**调试困难**：编译期代码无法用传统调试器调试。

**最佳实践**：
- 只在确实需要时使用编译期计算
- 优先考虑可读性和维护性
- 测量编译时间和运行时性能

### 5. 编译期计算的限制

**不能做的事情**：
- 不能使用堆内存（new/delete）
- 不能使用虚函数
- 不能使用异常（C++20 前）
- 不能访问全局变量（除非 constinit）
- 不能进行 I/O 操作

**可以做的事情**：
- 基本算术运算
- 条件分支和循环
- 数组和结构体操作
- 模板实例化
- 编译期断言

## 学习建议

### 1. 从简单开始

不要一开始就尝试复杂的编译期计算。从简单的 constexpr 函数开始，逐步增加复杂度。

### 2. 多写编译期断言

使用 `static_assert` 验证每个编译期计算的结果，确保正确性。

### 3. 理解编译器错误

编译期计算的错误信息可能很复杂。学会阅读和理解编译器错误信息。

### 4. 测试边界情况

编译期计算的边界情况可能与运行时不同。特别注意整数溢出、除零等问题。

### 5. 性能测试

不要假设编译期计算一定更快。测量实际性能，根据数据做决策。

## 常见陷阱

### 1. 过度使用 constexpr

```cpp
// 不好：过度使用 constexpr
constexpr int add(int a, int b) { return a + b; }
constexpr int result = add(3, 4);  // 没有必要

// 好：只在需要时使用
int result = 3 + 4;  // 更简单清晰
```

### 2. 忽略编译时间

```cpp
// 不好：复杂的编译期计算
constexpr auto huge_array = generate_array<10000>();  // 编译时间很长

// 好：只在必要时使用编译期计算
const auto huge_array = generate_array<10000>();  // 运行时计算
```

### 3. 混淆 constexpr 和 const

```cpp
// constexpr：编译期常量
constexpr int x = 42;  // 编译期确定

// const：运行时常量
const int y = get_value();  // 运行时确定

// 关键区别：
// - constexpr 必须在编译期确定
// - const 可以在运行时确定
```

### 4. 忽略 C++ 版本差异

```cpp
// C++11：只允许一条 return 语句
constexpr int factorial_11(int n) {
    return (n <= 1) ? 1 : n * factorial_11(n - 1);
}

// C++14：允许局部变量和循环
constexpr int factorial_14(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}
```

## 项目价值

### 1. 技术深度

编译期计算是 C++ 高级特性，掌握它能显著提升技术水平。

### 2. 性能优化

编译期计算是性能优化的重要手段，特别是在高性能计算、游戏开发等领域。

### 3. 类型安全

编译期计算提供更强的类型安全性，减少运行时错误。

### 4. 零成本抽象

编译期计算是 C++ 零成本抽象的核心，使得高级抽象不会带来运行时开销。

### 5. 职业发展

掌握编译期计算是成为 C++ 专家的重要标志，对职业发展有显著帮助。
