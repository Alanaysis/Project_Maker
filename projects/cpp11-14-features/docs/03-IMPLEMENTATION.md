# C++11/14 新特性实现文档

## 1. 实现概述

本文档记录了 C++11/14 新特性项目的实现细节，包括每个特性的核心实现思路和关键代码。

## 2. 特性实现

### 2.1 移动语义和右值引用

**实现要点**：
1. 定义具有资源所有权的类（如 Buffer）
2. 实现移动构造函数和移动赋值运算符
3. 使用 `noexcept` 标记移动操作
4. 使用 `std::move` 进行资源转移

**关键代码**：
```cpp
Buffer(Buffer&& other) noexcept
    : data_(other.data_), size_(other.size_) {
    other.data_ = nullptr;
    other.size_ = 0;
}

Buffer& operator=(Buffer&& other) noexcept {
    if (this != &other) {
        delete[] data_;
        data_ = other.data_;
        size_ = other.size_;
        other.data_ = nullptr;
        other.size_ = 0;
    }
    return *this;
}
```

**测试策略**：
- 验证移动后源对象状态
- 验证资源所有权转移
- 性能对比测试（移动 vs 拷贝）

### 2.2 Lambda 表达式

**实现要点**：
1. 基本 Lambda 语法
2. 捕获列表（值捕获、引用捕获）
3. 泛型 Lambda（C++14）
4. 与 STL 算法配合使用

**关键代码**：
```cpp
// 基本 Lambda
auto add = [](int a, int b) { return a + b; };

// 值捕获
int x = 10;
auto capture_val = [x]() { return x; };

// 引用捕获
auto capture_ref = [&x]() { x += 5; return x; };

// 泛型 Lambda (C++14)
auto generic_add = [](auto a, auto b) { return a + b; };
```

**测试策略**：
- 验证 Lambda 调用结果
- 验证捕获行为
- 验证泛型 Lambda 多态性

### 2.3 智能指针

**实现要点**：
1. `unique_ptr` 独占所有权
2. `shared_ptr` 共享所有权
3. `weak_ptr` 打破循环引用
4. 自定义删除器

**关键代码**：
```cpp
// unique_ptr
auto ptr = std::make_unique<int>(42);

// shared_ptr
auto shared = std::make_shared<int>(42);
auto shared2 = shared;  // 引用计数 +1

// weak_ptr
std::weak_ptr<int> weak = shared;
if (auto locked = weak.lock()) {
    // 使用 locked
}
```

**测试策略**：
- 验证所有权语义
- 验证引用计数
- 验证循环引用解决方案

### 2.4 线程库

**实现要点**：
1. `std::thread` 基本使用
2. `std::mutex` 互斥锁
3. `std::condition_variable` 条件变量
4. 线程池实现

**关键代码**：
```cpp
// 基本线程
std::thread t([]() { /* 工作 */ });
t.join();

// 互斥锁
std::mutex mtx;
{
    std::lock_guard<std::mutex> lock(mtx);
    // 临界区
}

// 条件变量
std::condition_variable cv;
std::mutex mtx;
bool ready = false;

// 等待线程
std::unique_lock<std::mutex> lock(mtx);
cv.wait(lock, [&]{ return ready; });

// 通知线程
{
    std::lock_guard<std::mutex> lock(mtx);
    ready = true;
}
cv.notify_one();
```

**测试策略**：
- 验证线程创建和销毁
- 验证互斥锁保护
- 验证条件变量同步
- 压力测试线程池

### 2.5 可变参数模板

**实现要点**：
1. 参数包展开
2. 递归展开模式
3. 折叠表达式（C++17，但概念在 C++14 中重要）

**关键代码**：
```cpp
// 基本可变参数模板
template<typename... Args>
void print(Args... args) {
    // C++17 折叠表达式
    // (std::cout << ... << args) << std::endl;

    // C++14 递归展开
    print_one(args...);
}

template<typename T>
void print_one(T&& t) {
    std::cout << t << std::endl;
}

template<typename T, typename... Args>
void print_one(T&& t, Args&&... args) {
    std::cout << t << " ";
    print_one(args...);
}
```

**测试策略**：
- 验证不同参数数量
- 验证不同类型参数
- 验证完美转发

### 2.6 constexpr

**实现要点**：
1. 编译期计算
2. constexpr 函数限制
3. constexpr 变量

**关键代码**：
```cpp
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

constexpr int fib(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// C++14 放宽了 constexpr 限制
constexpr int compute() {
    int result = 0;
    for (int i = 0; i < 10; ++i) {
        result += i;
    }
    return result;
}
```

**测试策略**：
- 验证编译期计算
- 验证运行时使用
- 验证性能提升

### 2.7 auto 和 decltype

**实现要点**：
1. `auto` 类型推导规则
2. `decltype` 类型推导
3. 返回类型后置

**关键代码**：
```cpp
// auto 基本用法
auto i = 42;           // int
auto d = 3.14;         // double
auto s = "hello";      // const char*
auto v = std::vector<int>{1, 2, 3};

// decltype 用法
int x = 10;
decltype(x) y = 20;   // int

// 返回类型后置
template<typename T, typename U>
auto add(T t, U u) -> decltype(t + u) {
    return t + u;
}
```

**测试策略**：
- 验证类型推导正确性
- 验证与模板配合
- 验证返回类型后置

### 2.8 范围 for 循环

**实现要点**：
1. 基本语法
2. 自定义类型支持
3. 引用和值遍历

**关键代码**：
```cpp
// 基本用法
std::vector<int> v = {1, 2, 3, 4, 5};
for (auto& elem : v) {
    std::cout << elem << " ";
}

// 自定义类型
class MyContainer {
    std::vector<int> data_;
public:
    auto begin() { return data_.begin(); }
    auto end() { return data_.end(); }
};

// 使用示例
MyContainer c;
for (auto& elem : c) {
    // 处理 elem
}
```

**测试策略**：
- 验证遍历正确性
- 验证自定义类型支持
- 验证性能

### 2.9 初始化列表

**实现要点**：
1. 统一初始化语法
2. `std::initializer_list`
3. 聚合初始化

**关键代码**：
```cpp
// 基本初始化
int arr[]{1, 2, 3, 4, 5};
std::vector<int> v{1, 2, 3, 4, 5};
std::map<std::string, int> m{{"one", 1}, {"two", 2}};

// std::initializer_list
class MyVector {
    std::vector<int> data_;
public:
    MyVector(std::initializer_list<int> init) : data_(init) {}
};

// 使用示例
MyVector mv{1, 2, 3, 4, 5};
```

**测试策略**：
- 验证初始化语法
- 验证 initializer_list 使用
- 验证聚合初始化

## 3. 构建系统

### 3.1 CMake 配置

```cmake
cmake_minimum_required(VERSION 3.10)
project(cpp11-14-features LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 主可执行文件
add_executable(main main.cpp)

# 测试
enable_testing()
add_subdirectory(tests)
```

### 3.2 构建脚本

```bash
#!/bin/bash
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

## 4. 测试框架

使用 Google Test 框架：

```cpp
#include <gtest/gtest.h>

TEST(FeatureTest, BasicTest) {
    EXPECT_EQ(1 + 1, 2);
}
```

## 5. 文档生成

使用 Markdown 生成文档，包含：
- 项目说明
- API 文档
- 使用示例
- 最佳实践
