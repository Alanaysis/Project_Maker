# C++11/14 新特性实践

系统学习 C++11/14 的核心新特性，包括移动语义、Lambda 表达式、智能指针、并发编程等。

## 项目概述

本项目通过实际代码示例和测试，帮助开发者掌握 C++11/14 的核心新特性。每个特性都有独立的示例程序和测试用例，便于学习和实践。

### 学习目标

- 理解移动语义和右值引用
- 掌握 Lambda 表达式
- 学会智能指针和并发编程
- 掌握可变参数模板和 constexpr
- 熟练使用 auto、decltype、范围 for 等语法特性

### 核心内容

```
移动语义 → 右值引用 → 完美转发 → Lambda → 智能指针 → 并发
```

## 特性清单

| 特性 | 示例文件 | 测试文件 | 说明 |
|-----|---------|---------|------|
| 移动语义和右值引用 | `01_move_semantics.cpp` | `test_move_semantics.cpp` | 避免不必要的拷贝 |
| Lambda 表达式 | `02_lambda.cpp` | `test_lambda.cpp` | 匿名函数和闭包 |
| 智能指针 | `03_smart_pointers.cpp` | `test_smart_pointers.cpp` | 资源自动管理 |
| 并发编程 | `04_threads.cpp` | `test_threads.cpp` | 多线程和同步 |
| 可变参数模板 | `05_variadic_templates.cpp` | `test_variadic_templates.cpp` | 可变参数函数和类 |
| constexpr | `06_constexpr.cpp` | `test_constexpr.cpp` | 编译期计算 |
| auto 和 decltype | `07_auto_decltype.cpp` | `test_auto_decltype.cpp` | 类型推导 |
| 范围 for 循环 | `08_range_for.cpp` | `test_range_for.cpp` | 简化容器遍历 |
| 初始化列表 | `09_initializer_list.cpp` | `test_initializer_list.cpp` | 统一初始化语法 |

## 快速开始

### 环境要求

- C++14 兼容的编译器（GCC 5.0+、Clang 3.4+、MSVC 19.0+）
- CMake 3.10+
- Google Test（用于测试）

### 安装依赖

```bash
# Ubuntu/Debian
sudo apt-get install cmake libgtest-dev

# macOS
brew install cmake googletest

# Windows (使用 vcpkg)
vcpkg install gtest
```

### 构建项目

```bash
# 克隆项目
git clone <repository-url>
cd projects/cpp11-14-features

# 使用构建脚本
chmod +x build.sh
./build.sh build

# 或手动构建
mkdir build && cd build
cmake ..
make
```

### 运行示例

```bash
# 运行所有示例
./build.sh examples

# 运行单个示例
./build/01_move_semantics

# 使用运行脚本（交互式菜单）
chmod +x run.sh
./run.sh

# 直接运行指定示例
./run.sh 1
./run.sh 01_move_semantics
```

### 运行测试

```bash
# 运行所有测试
./build.sh test

# 或使用 ctest
cd build
ctest --output-on-failure
```

## 项目结构

```
cpp11-14-features/
├── CMakeLists.txt              # 主 CMake 配置
├── README.md                   # 本文件
├── build.sh                    # 构建脚本
├── run.sh                      # 运行脚本
├── docs/                       # 文档目录
│   ├── 01-RESEARCH.md          # 市场调研
│   ├── 02-DESIGN.md            # 项目设计
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发指南
├── examples/                   # 示例代码
│   ├── 01_move_semantics.cpp
│   ├── 02_lambda.cpp
│   ├── 03_smart_pointers.cpp
│   ├── 04_threads.cpp
│   ├── 05_variadic_templates.cpp
│   ├── 06_constexpr.cpp
│   ├── 07_auto_decltype.cpp
│   ├── 08_range_for.cpp
│   └── 09_initializer_list.cpp
├── tests/                      # 测试代码
│   ├── CMakeLists.txt
│   ├── test_move_semantics.cpp
│   ├── test_lambda.cpp
│   ├── test_smart_pointers.cpp
│   ├── test_threads.cpp
│   ├── test_variadic_templates.cpp
│   ├── test_constexpr.cpp
│   ├── test_auto_decltype.cpp
│   ├── test_range_for.cpp
│   └── test_initializer_list.cpp
├── include/                    # 头文件
└── LEARNING_NOTES.md           # 学习笔记
```

## 学习路线

### 阶段 1：基础语法

1. **auto 和 decltype**
   - 理解类型推导规则
   - 学会使用 auto 简化代码
   - 掌握 decltype 的使用场景

2. **范围 for 循环**
   - 基本语法和使用
   - 值遍历 vs 引用遍历
   - 自定义容器支持

3. **初始化列表**
   - 统一初始化语法
   - std::initializer_list
   - 聚合初始化

### 阶段 2：核心特性

4. **右值引用**
   - 左值 vs 右值
   - 右值引用语法
   - 引用折叠规则

5. **移动语义**
   - 移动构造函数
   - 移动赋值运算符
   - std::move 的使用

6. **完美转发**
   - std::forward 的作用
   - 万能引用
   - 参数转发

### 阶段 3：函数式编程

7. **Lambda 表达式**
   - 基本语法
   - 捕获列表
   - 泛型 Lambda
   - 与 STL 算法配合

### 阶段 4：资源管理

8. **智能指针**
   - unique_ptr
   - shared_ptr
   - weak_ptr
   - 自定义删除器

### 阶段 5：并发编程

9. **线程库**
   - std::thread
   - std::mutex
   - std::condition_variable
   - std::future 和 std::promise

### 阶段 6：高级特性

10. **可变参数模板**
    - 参数包展开
    - 递归展开模式
    - 完美转发

11. **constexpr**
    - 编译期计算
    - constexpr 函数
    - constexpr 类

## 最佳实践

### 移动语义

```cpp
// 好的做法
std::vector<int> createVector() {
    std::vector<int> v(1000);
    return v;  // 移动而非拷贝
}

// 避免的做法
std::vector<int> v = createVector();
std::vector<int> v2 = v;  // 不必要的拷贝
```

### Lambda 表达式

```cpp
// 好的做法
auto add = [](int a, int b) { return a + b; };

// 避免的做法
std::function<int(int, int)> add = [](int a, int b) { return a + b; };
```

### 智能指针

```cpp
// 好的做法
auto ptr = std::make_unique<int>(42);

// 避免的做法
int* ptr = new int(42);
// ... 可能忘记 delete
```

### 并发编程

```cpp
// 好的做法
std::mutex mtx;
{
    std::lock_guard<std::mutex> lock(mtx);
    // 临界区
}

// 避免的做法
mtx.lock();
// ... 可能抛出异常
mtx.unlock();
```

## 常见问题

### Q: 什么时候使用 unique_ptr，什么时候使用 shared_ptr？

A: 优先使用 `unique_ptr`，只在需要共享所有权时使用 `shared_ptr`。`unique_ptr` 零开销，性能更好。

### Q: Lambda 捕获使用值还是引用？

A: 如果需要修改外部变量，使用引用捕获（`[&x]`）。如果只是读取，使用值捕获（`[x]`）更安全。

### Q: 移动后的对象还能使用吗？

A: 移动后的对象处于有效但未指定的状态。可以销毁或重新赋值，但不应该读取其值。

### Q: constexpr 函数有什么限制？

A: C++11 中 constexpr 函数只能包含一个 return 语句。C++14 放宽了限制，可以包含循环、局部变量等。

## 参考资源

### 书籍

- [C++ Primer (第5版)](https://book.douban.com/subject/25708312/)
- [Effective Modern C++](https://book.douban.com/subject/25923597/)
- [C++ Concurrency in Action](https://book.douban.com/subject/26386275/)

### 在线资源

- [cppreference.com](https://en.cppreference.com/)
- [learncpp.com](https://www.learncpp.com/)
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)

### 视频教程

- [CppCon](https://www.youtube.com/user/CppCon)
- [C++ Weekly](https://www.youtube.com/channel/UCxHAlbZQNFU2LgEtiqd23KQ)

## 贡献指南

欢迎贡献代码、文档或提出问题！

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
