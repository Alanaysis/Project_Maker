# 01 - 市场调研：C++ 编译期计算

## 编译期计算的历史

### C++98/03 时代：模板元编程

```cpp
// 经典的模板递归计算阶乘
template<int N>
struct Factorial {
    static constexpr int value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
    static constexpr int value = 1;
};

static_assert(Factorial<5>::value == 120);
```

这一时期的编译期计算完全依赖模板特化和递归，代码可读性差，调试困难。

### C++11：constexpr 的诞生

```cpp
constexpr int factorial(int n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}
static_assert(factorial(5) == 120);
```

C++11 引入 `constexpr` 关键字，使得编译期计算可以用普通函数语法编写。但限制较多：函数体只能有一条 return 语句。

### C++14：放宽 constexpr 限制

```cpp
constexpr int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}
```

C++14 允许 constexpr 函数包含局部变量、循环和条件分支。

### C++17：constexpr 的进一步扩展

- `constexpr if`：编译期条件分支
- `constexpr` lambda 表达式
- `std::string_view` 等新的 constexpr 友好类型

### C++20：consteval 和 constinit

- `consteval`：保证必须在编译期求值的立即函数
- `constinit`：保证常量初始化，避免静态初始化顺序问题
- 更多标准库函数支持 constexpr

### C++23：constexpr 的持续扩展

- `constexpr` std::unique_ptr
- `constexpr` std::optional
- 更多标准库算法支持 constexpr

## 应用场景

### 1. 零成本抽象

```cpp
// 编译期计算查找表，运行时直接查表
constexpr auto sine_table = generate_sine_table<360>();
// 运行时：O(1) 查表，无计算开销
```

### 2. 类型安全的配置

```cpp
// 编译期解析配置字符串
constexpr auto config = parse_config<"{port: 8080, host: \"localhost\"}">();
// 编译期验证配置正确性
```

### 3. 编译期状态机

```cpp
// 编译期生成状态转移表
constexpr auto fsm = make_state_machine<States, Events>();
// 运行时高效执行状态转移
```

### 4. 编译期字符串处理

```cpp
// 编译期字符串哈希
constexpr auto hash = compile_time_hash("hello");
// 用于 switch-case 字符串匹配
```

### 5. 单位转换系统

```cpp
// 编译期单位验证
constexpr auto distance = 100.0_m;
constexpr auto time = 9.58_s;
auto speed = distance / time;  // 编译期验证单位正确性
```

## 优缺点分析

### 优点

1. **性能提升**：将计算从运行时移到编译时，减少运行时开销
2. **类型安全**：编译期错误比运行时错误更容易修复
3. **零成本抽象**：高级抽象不会带来运行时开销
4. **代码可读性**：相比模板元编程，constexpr 代码更易理解
5. **调试友好**：编译期错误信息比模板错误更清晰

### 缺点

1. **编译时间增加**：复杂编译期计算会增加编译时间
2. **调试困难**：编译期代码无法用传统调试器调试
3. **限制较多**：constexpr 函数不能使用堆内存、虚函数等
4. **编译器差异**：不同编译器对 constexpr 的支持程度不同
5. **代码膨胀**：过度使用可能导致二进制体积增大

## 业界应用

| 公司/项目 | 应用场景 |
|-----------|---------|
| Google | protobuf 编译期反射 |
| Facebook | folly 编译期字符串处理 |
| Boost | Hana 元编程库 |
| Qt | moc 编译期元对象系统 |
| Unreal Engine | 编译期类型特征 |

## 参考资源

- [cppreference - constexpr](https://en.cppreference.com/w/cpp/language/constexpr)
- [cppreference - consteval](https://en.cppreference.com/w/cpp/language/consteval)
- [cppreference - constinit](https://en.cppreference.com/w/cpp/language/constinit)
- [C++ Best Practices](https://github.com/cppbest practices)
