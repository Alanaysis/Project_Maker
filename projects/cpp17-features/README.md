# C++17 新特性实践

## 项目简介

本项目是一个全面的 C++17 新特性实践库，通过独立的示例代码展示 C++17 标准引入的所有主要语言和库特性。每个特性都有详细的注释和可运行的示例，适合 C++ 开发者学习和参考。

## 快速开始

```bash
# 编译项目
mkdir build && cd build
cmake ..
make

# 运行特定特性示例
./optional_example
./variant_example
./any_example
# ... 其他示例

# 或者直接编译单个文件
g++ -std=c++17 -o optional_example optional_example.cpp
./optional_example
```

## 特性分类

### 语言特性

| 特性 | 文件 | 说明 |
|------|------|------|
| std::optional | optional_example.cpp | 可选值包装器 |
| std::variant | variant_example.cpp | 类型安全的联合体 |
| std::any | any_example.cpp | 任意类型容器 |
| std::string_view | string_view_example.cpp | 字符串视图 |
| 结构化绑定 | structured_bindings.cpp | 解构绑定 |
| if constexpr | if_constexpr_example.cpp | 编译期条件分支 |
| 折叠表达式 | fold_expressions.cpp | 参数包展开 |
| 内联变量 | inline_variables.cpp | 内联变量定义 |
| 嵌套命名空间 | nested_namespaces.cpp | 嵌套命名空间语法 |
| 属性 | attributes_example.cpp | nodiscard/maybe_unused/fallthrough |

### 标准库特性

| 特性 | 文件 | 说明 |
|------|------|------|
| std::filesystem | filesystem_example.cpp | 文件系统操作 |
| std::apply | apply_example.cpp | 元组展开调用 |
| std::invoke | invoke_example.cpp | 通用可调用对象调用 |
| std::gcd/lcm | gcd_lcm_example.cpp | 最大公约数/最小公倍数 |
| 并行算法 | parallel_algorithms.cpp | 并行执行策略 |
| std::shared_mutex | shared_mutex_example.cpp | 共享互斥锁 |
| std::scoped_lock | scoped_lock_example.cpp | RAII 锁管理 |

### 类型推导

| 特性 | 文件 | 说明 |
|------|------|------|
| CTAD | ctad_example.cpp | 类模板参数推导 |
| auto 扩展 | auto_extensions.cpp | auto 在更多上下文中的使用 |

## 学习路径

建议按以下顺序学习：

1. **基础类型增强** - optional, variant, any, string_view
2. **语法改进** - 结构化绑定, if constexpr, 嵌套命名空间, 属性
3. **模板元编程** - 折叠表达式, CTAD, auto 扩展
4. **标准库增强** - filesystem, apply, invoke, gcd/lcm
5. **并发支持** - shared_mutex, scoped_lock, 并行算法
6. **变量特性** - 内联变量

## 编译运行

### 环境要求

- 编译器: GCC 7+, Clang 5+, MSVC 2017+
- CMake: 3.8+
- C++ 标准: C++17

### 编译选项

```bash
# Debug 模式
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式
cmake -DCMAKE_BUILD_TYPE=Release ..

# 指定编译器
cmake -DCMAKE_CXX_COMPILER=g++-9 ..
```

## 项目结构

```
cpp17-features/
├── CMakeLists.txt          # 构建配置
├── README.md               # 本文档
├── 01_RESEARCH.md          # 市场调研
├── 02_REQUIREMENTS.md      # 需求分析
├── 03_DESIGN.md            # 技术设计
├── 04_PRODUCT.md           # 产品思考
├── 05_DEVELOPMENT.md       # 开发手册
├── optional_example.cpp    # std::optional
├── variant_example.cpp     # std::variant
├── any_example.cpp         # std::any
├── string_view_example.cpp # std::string_view
├── structured_bindings.cpp # 结构化绑定
├── if_constexpr_example.cpp # if constexpr
├── fold_expressions.cpp    # 折叠表达式
├── inline_variables.cpp    # 内联变量
├── nested_namespaces.cpp   # 嵌套命名空间
├── attributes_example.cpp  # 属性
├── filesystem_example.cpp  # std::filesystem
├── apply_example.cpp       # std::apply
├── invoke_example.cpp      # std::invoke
├── gcd_lcm_example.cpp     # std::gcd/lcm
├── parallel_algorithms.cpp # 并行算法
├── shared_mutex_example.cpp # std::shared_mutex
├── scoped_lock_example.cpp # std::scoped_lock
├── ctad_example.cpp        # CTAD
└── auto_extensions.cpp     # auto 扩展
```

## 许可证

MIT License
