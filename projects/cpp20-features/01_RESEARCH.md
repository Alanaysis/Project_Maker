# 01_RESEARCH.md - 市场调研

## C++20 标准背景

### 发布历史

- **2020年12月**：C++20 标准正式发布（ISO/IEC 14882:2020）
- 这是继 C++11 之后最大的一次标准更新
- 引入了 4 个重量级特性：Concepts、Ranges、Coroutines、Modules

### 为什么需要 C++20？

| 问题 | C++17 现状 | C++20 解决方案 |
|------|-----------|---------------|
| 模板错误信息难读 | SFINAE 技巧复杂 | Concepts 提供清晰约束 |
| STL 算法组合困难 | 迭代器模式繁琐 | Ranges 管道操作 |
| 异步编程复杂 | 回调/Future 不够灵活 | Coroutines 原生支持 |
| 编译速度慢 | 头文件包含机制 | Modules 消除重复解析 |
| 比较运算符冗余 | 需要定义多个运算符 | <=> 自动生成 |
| 格式化输出不安全 | printf/iostream 各有问题 | std::format 类型安全 |

---

## 四大特性概述

### 1. Concepts（概念）

**定义**：对模板参数的命名约束，让模板编程更加安全和清晰。

**核心价值**：
- 改善模板错误信息（从几百行减少到几行）
- 提供文档化的接口约束
- 支持重载决议基于约束

**示例场景**：
```cpp
// 以前：SFINAE 难以理解
template<typename T, typename = std::enable_if_t<std::is_integral_v<T>>>
T gcd(T a, T b);

// 现在：清晰的约束
template <std::integral T>
T gcd(T a, T b);
```

### 2. Ranges（范围）

**定义**：对 STL 算法的重大升级，支持惰性求值和管道操作。

**核心价值**：
- 管道操作符 `|` 链式组合算法
- 惰性求值，避免不必要的计算
- 视图（Views）不拥有数据，零开销抽象
- 投影（Projections）简化复杂排序

**示例场景**：
```cpp
// 以前：嵌套调用
auto it = std::find_if(vec.begin(), vec.end(), [](int x){ return x > 5; });

// 现在：管道操作
auto result = vec | std::views::filter([](int x){ return x > 5; })
                  | std::views::transform([](int x){ return x * x; });
```

### 3. Coroutines（协程）

**定义**：无栈协程，支持挂起和恢复的异步编程原语。

**核心价值**：
- `co_await` 异步等待
- `co_yield` 生成器
- `co_return` 协程返回
- 编译器自动管理状态机

**示例场景**：
```cpp
Generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        int temp = a + b;
        a = b;
        b = temp;
    }
}
```

### 4. Modules（模块）

**定义**：替代头文件的模块系统，提升编译速度和封装性。

**核心价值**：
- 消除头文件重复解析
- 避免宏污染
- 更好的封装（export 控制可见性）
- 加速编译

---

## 与 C++17 的区别

### 语言特性对比

| 特性 | C++17 | C++20 |
|------|-------|-------|
| 模板约束 | SFINAE/enable_if | Concepts |
| 数据处理 | STL 算法 + 迭代器 | Ranges + Views |
| 异步编程 | future/promise | Coroutines |
| 代码组织 | 头文件 | Modules |
| 比较运算符 | 手动定义 | <=> 自动生成 |
| 编译期计算 | constexpr | consteval/constinit |
| 格式化 | printf/iostream | std::format |
| 内存视图 | string_view | + span |
| 线程管理 | std::thread | jthread |
| 同步原语 | mutex/condition_variable | + latch/barrier/semaphore |

### 标准库新增

| 类别 | C++20 新增 |
|------|-----------|
| 格式化 | std::format, std::format_to |
| 容器视图 | std::span |
| 范围 | std::ranges::*, std::views::* |
| 线程 | std::jthread, std::stop_token |
| 同步 | std::latch, std::barrier, std::counting_semaphore |
| 调试 | std::source_location |
| 概念 | std::concept (integral, floating_point, etc.) |

---

## 行业采用情况

### 主流编译器支持

- **GCC**: 10+ 版本支持大部分特性
- **Clang**: 13+ 版本支持核心特性
- **MSVC**: 19.29+ 版本支持大部分特性

### 实际应用场景

1. **游戏引擎**：Ranges 用于数据处理管道，Coroutines 用于游戏逻辑
2. **Web 服务器**：Coroutines 用于异步 I/O
3. **数据库**：Concepts 用于泛型查询接口
4. **嵌入式**：consteval 用于编译期配置
5. **库开发**：Concepts 改善模板 API 的可用性

---

## 学习资源

### 官方文档
- [C++20 标准](https://en.cppreference.com/w/cpp/20)
- [C++20 编译器支持](https://en.cppreference.com/w/cpp/compiler_support/20)

### 推荐书籍
- 《C++20 - The Complete Guide》- Nicolai M. Josuttis
- 《C++ Templates: The Complete Guide》- 第二版
- 《Effective C++20》- Scott Meyers 风格

### 在线资源
- [C++20 Features](https://www.learncpp.com/cpp-tutorial/introduction-to-c20/)
- [Compiler Explorer](https://godbolt.org/) - 在线测试不同编译器
