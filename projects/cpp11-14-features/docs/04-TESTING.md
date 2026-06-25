# C++11/14 新特性测试文档

## 1. 测试概述

本文档描述了 C++11/14 新特性项目的测试策略和测试用例。

## 2. 测试框架

使用 Google Test (gtest) 框架进行单元测试。

### 2.1 安装 Google Test

```bash
# Ubuntu/Debian
sudo apt-get install libgtest-dev

# macOS
brew install googletest

# 从源码安装
git clone https://github.com/google/googletest.git
cd googletest
mkdir build && cd build
cmake ..
make
sudo make install
```

### 2.2 编译测试

```bash
mkdir build && cd build
cmake ..
make
```

### 2.3 运行测试

```bash
# 运行所有测试
ctest

# 运行特定测试
./test_move_semantics
./test_lambda

# 显示详细输出
ctest --output-on-failure
```

## 3. 测试用例

### 3.1 移动语义测试

| 测试名称 | 描述 |
|---------|------|
| MoveConstructor | 测试移动构造函数 |
| MoveAssignment | 测试移动赋值运算符 |
| CopyConstructor | 测试拷贝构造函数 |
| CopyAssignment | 测试拷贝赋值运算符 |
| StdMove | 测试 std::move |
| ContainerMove | 测试容器移动 |
| UniquePtrMove | 测试 unique_ptr 移动 |
| NoexceptMove | 测试 noexcept 标记 |
| MovedFromState | 测试移动后状态 |
| SelfMoveAssignment | 测试自移动赋值 |

### 3.2 Lambda 表达式测试

| 测试名称 | 描述 |
|---------|------|
| BasicLambda | 测试基本 Lambda |
| LambdaCall | 测试 Lambda 调用 |
| CaptureByValue | 测试值捕获 |
| CaptureByReference | 测试引用捕获 |
| ImplicitCaptureByValue | 测试隐式值捕获 |
| ImplicitCaptureByReference | 测试隐式引用捕获 |
| LambdaWithAlgorithms | 测试 Lambda 与算法 |
| LambdaAsParameter | 测试 Lambda 作为参数 |
| Closure | 测试 Lambda 闭包 |
| GenericLambda | 测试泛型 Lambda |
| LambdaWithContainers | 测试 Lambda 与容器 |
| LambdaWithAccumulate | 测试 Lambda 与累积 |
| MutableLambda | 测试 mutable Lambda |
| LambdaWithStrings | 测试 Lambda 与字符串 |

### 3.3 智能指针测试

| 测试名称 | 描述 |
|---------|------|
| UniquePtrBasic | 测试 unique_ptr 基本操作 |
| UniquePtrMove | 测试 unique_ptr 移动 |
| UniquePtrReset | 测试 unique_ptr 重置 |
| UniquePtrRelease | 测试 unique_ptr 释放所有权 |
| UniquePtrContainer | 测试 unique_ptr 与容器 |
| SharedPtrBasic | 测试 shared_ptr 基本操作 |
| SharedPtrSharing | 测试 shared_ptr 共享 |
| SharedPtrMove | 测试 shared_ptr 移动 |
| SharedPtrReset | 测试 shared_ptr 重置 |
| WeakPtrBasic | 测试 weak_ptr 基本操作 |
| WeakPtrLock | 测试 weak_ptr 锁定 |
| WeakPtrExpired | 测试 weak_ptr 过期 |
| SharedPtrRefCount | 测试 shared_ptr 引用计数 |
| CustomDeleter | 测试自定义删除器 |
| WeakPtrBreakCycle | 测试 weak_ptr 打破循环引用 |
| Polymorphism | 测试智能指针与多态 |
| MakeFunctions | 测试 make_unique 和 make_shared |
| UniquePtrArray | 测试智能指针数组 |

### 3.4 并发编程测试

| 测试名称 | 描述 |
|---------|------|
| BasicThread | 测试线程创建和执行 |
| MultipleThreads | 测试多个线程 |
| Mutex | 测试互斥锁 |
| ConditionVariable | 测试条件变量 |
| FuturePromise | 测试 future 和 promise |
| Async | 测试 async |
| Atomic | 测试原子操作 |
| ThreadSafeQueue | 测试线程安全的队列 |
| ThreadLocalStorage | 测试线程局部存储 |
| ThreadId | 测试线程 ID |
| ThreadSleep | 测试线程睡眠 |
| TryLock | 测试 try_lock |

### 3.5 可变参数模板测试

| 测试名称 | 描述 |
|---------|------|
| Basic | 测试可变参数模板基础 |
| Recursive | 测试递归展开 |
| PerfectForwarding | 测试完美转发 |
| Tuple | 测试元组 |
| PackExpansion | 测试参数包展开 |
| Inheritance | 测试可变参数模板与继承 |
| FunctionApplication | 测试可变参数模板与函数应用 |
| EventSystem | 测试可变参数模板与事件系统 |
| ContainerInit | 测试可变参数模板与容器初始化 |

### 3.6 constexpr 测试

| 测试名称 | 描述 |
|---------|------|
| Factorial | 测试 constexpr 函数 |
| Variables | 测试 constexpr 变量 |
| Fibonacci | 测试 constexpr 函数（C++14 风格） |
| Class | 测试 constexpr 类 |
| Array | 测试 constexpr 与数组 |
| Conditional | 测试 constexpr 条件判断 |
| Loop | 测试 constexpr 循环 |
| Template | 测试 constexpr 与模板 |
| StaticAssert | 测试 constexpr 与 static_assert |
| StringLength | 测试 constexpr 字符串长度 |
| GCD | 测试 constexpr 最大公约数 |
| LCM | 测试 constexpr 最小公倍数 |
| RuntimeMix | 测试 constexpr 与运行时混合 |
| Recursion | 测试 constexpr 递归深度 |

### 3.7 auto 和 decltype 测试

| 测试名称 | 描述 |
|---------|------|
| BasicAuto | 测试 auto 基本类型推导 |
| AutoWithReferences | 测试 auto 与引用 |
| AutoWithConst | 测试 auto 与 const |
| BasicDecltype | 测试 decltype 基本用法 |
| DecltypeWithExpressions | 测试 decltype 与表达式 |
| AutoWithContainers | 测试 auto 与容器 |
| AutoWithRangeFor | 测试 auto 与范围 for |
| AutoWithMap | 测试 auto 与 map |
| TrailingReturnType | 测试返回类型后置 |
| AutoReturnType | 测试 C++14 返回类型推导 |
| DecltypeAuto | 测试 decltype(auto) |
| AutoWithLambda | 测试 auto 与 Lambda |
| AutoWithInitializerList | 测试 auto 与初始化列表 |
| TypeTraits | 测试类型特征 |
| AutoWithPointers | 测试 auto 与指针 |
| AutoWithConstPointers | 测试 auto 与 const 指针 |

### 3.8 范围 for 循环测试

| 测试名称 | 描述 |
|---------|------|
| Basic | 测试基本范围 for |
| Auto | 测试 auto 范围 for |
| Reference | 测试引用范围 for |
| ConstReference | 测试 const 引用范围 for |
| List | 测试 list 范围 for |
| Map | 测试 map 范围 for |
| Set | 测试 set 范围 for |
| Array | 测试数组范围 for |
| InitializerList | 测试初始化列表范围 for |
| String | 测试字符串范围 for |
| Nested | 测试嵌套范围 for |
| CustomContainer | 测试自定义容器 |
| ModifyElements | 测试修改容器元素 |
| WithAlgorithms | 测试范围 for 与算法 |
| Performance | 测试范围 for 性能 |

### 3.9 初始化列表测试

| 测试名称 | 描述 |
|---------|------|
| Basic | 测试基本初始化列表 |
| Empty | 测试空初始化列表 |
| Map | 测试 map 初始化列表 |
| Set | 测试 set 初始化列表 |
| Nested | 测试嵌套初始化列表 |
| CustomClass | 测试自定义类使用初始化列表 |
| FunctionParameter | 测试初始化列表作为函数参数 |
| Auto | 测试初始化列表与 auto |
| Assignment | 测试初始化列表与赋值 |
| Insert | 测试初始化列表与 insert |
| AggregateInitialization | 测试聚合初始化 |
| NestedAggregate | 测试嵌套聚合初始化 |
| InitializerListProperties | 测试 initializer_list 特性 |
| WithAlgorithms | 测试初始化列表与算法 |
| Strings | 测试初始化列表与字符串 |
| MixedTypes | 测试初始化列表与混合类型 |

## 4. 测试覆盖率

```bash
# 生成覆盖率报告
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="--coverage"
make
ctest
gcovr -r .. --html --html-details -o coverage.html
```

## 5. 持续集成

### 5.1 GitHub Actions

```yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y cmake libgtest-dev
    - name: Build
      run: |
        mkdir build && cd build
        cmake ..
        make
    - name: Test
      run: |
        cd build
        ctest --output-on-failure
```

## 6. 测试最佳实践

1. **测试独立性**：每个测试应该独立运行，不依赖其他测试
2. **测试命名**：使用描述性的测试名称
3. **测试覆盖**：覆盖正常路径和边界情况
4. **测试速度**：保持测试快速运行
5. **测试可读性**：测试代码应该易于理解
