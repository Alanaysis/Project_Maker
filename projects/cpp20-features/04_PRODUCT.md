# 04_PRODUCT.md - 产品思考

## 学习目标

### 知识目标

完成本项目学习后，应该能够：

1. **理解 C++20 四大特性**的原理和适用场景
2. **掌握所有语言特性**的语法和使用方法
3. **熟练使用标准库新增组件**解决实际问题
4. **能够组合多个特性**构建现代 C++ 应用

### 技能目标

| 技能 | 级别 | 说明 |
|------|------|------|
| Concepts | 熟练 | 能够定义和使用概念约束模板 |
| Ranges | 熟练 | 能够使用管道操作处理数据 |
| Coroutines | 理解 | 理解协程原理，能使用 Generator |
| Modules | 了解 | 了解模块系统的基本用法 |
| 三向比较 | 熟练 | 能够为自定义类型实现 <=> |
| consteval/constinit | 理解 | 理解编译期计算的三种形式 |
| Lambda 改进 | 熟练 | 能够使用模板 Lambda |
| std::format | 熟练 | 能够格式化各种类型 |
| std::span | 熟练 | 能够使用 span 作为函数参数 |
| jthread/stop_token | 理解 | 理解协作式取消机制 |
| 同步原语 | 了解 | 了解 latch/barrier/semaphore |

---

## 关键要点

### 1. Concepts 的价值

**问题**：模板编程中，错误信息往往长达数百行，难以定位问题。

**解决方案**：Concepts 提供命名约束，错误信息清晰指向约束违反。

**关键点**：
- `concept` 定义约束
- `requires` 表达式定义复杂约束
- 约束可以组合（合取/析取）
- `requires` 子句和 `requires` 块是不同的

### 2. Ranges 的设计哲学

**问题**：STL 算法组合困难，需要嵌套调用或多次遍历。

**解决方案**：Ranges 提供管道操作，一次遍历完成多个操作。

**关键点**：
- Views 是惰性的，不立即计算
- 管道操作符 `|` 链式组合
- 投影（Projection）简化复杂操作
- 范围算法替代传统 STL 算法

### 3. Coroutines 的理解

**关键点**：
- C++20 协程是无栈协程（Stackless）
- 协程框架是底层 API，需要自己实现 Generator/Task
- `co_await`、`co_yield`、`co_return` 是三个关键字
- Promise 类型控制协程行为

### 4. 现代 C++ 编程风格

```cpp
// 旧风格
template<typename T>
typename std::enable_if<std::is_integral<T>::value, T>::type
gcd(T a, T b) { ... }

// 现代风格
template <std::integral T>
T gcd(T a, T b) { ... }
```

---

## 常见陷阱

### 1. Concepts

```cpp
// 错误：requires 表达式 vs requires 子句
template <typename T>
void f(T) requires requires(T t) { t.size(); }  // 注意两个 requires
```

### 2. Ranges

```cpp
// 注意：views 是惰性的，不会立即执行
auto v = data | std::views::transform(expensive_op);
// 此时 expensive_op 未被调用！
for (auto x : v) { ... }  // 遍历时才执行
```

### 3. Coroutines

```cpp
// Generator 的生命周期管理很重要
Generator<int> g = fibonacci();
// g 离开作用域时会销毁协程句柄
```

### 4. std::format

```cpp
// 自定义类型需要特化 std::formatter
template <>
struct std::formatter<MyType> {
    auto parse(std::format_parse_context& ctx);
    auto format(const MyType& val, std::format_context& ctx) const;
};
```

---

## 学习建议

1. **按顺序学习**：从简单特性开始，逐步到复杂特性
2. **动手实践**：每个示例都要编译运行，尝试修改代码
3. **对比理解**：对比 C++17 和 C++20 的写法差异
4. **查阅文档**：结合 cppreference.com 深入理解
5. **综合应用**：最后看综合示例，理解特性如何协作
