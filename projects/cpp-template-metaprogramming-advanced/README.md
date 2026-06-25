# C++ 模板元编程进阶

一个全面的 C++17/20 模板元编程学习项目，涵盖高级模板技术、编译期算法、类型计算和实际应用。

## 项目简介

本项目通过实际代码示例深入讲解 C++ 模板元编程的高级技术。所有示例都可以编译运行，包含详细的中文注释。

## 核心特性

### 高级模板技术
- **表达式模板** - 延迟求值，避免临时对象
- **CRTP** - 奇异递归模板模式，编译期多态
- **Mixin 模式** - 模板组合，灵活的功能扩展
- **策略类** - 编译期行为配置
- **标签分发** - 编译期分支消除

### 编译期算法
- 编译期排序（冒泡、选择、插入）
- 编译期查找（线性、二分）
- 编译期 Map/Filter/Reduce
- 编译期值列表操作

### 类型计算
- 类型列表操作（push/pop/at/concat/reverse）
- 类型计数与统计
- 类型索引与查找
- 类型转换链
- 类型集合操作（并集、交集、差集）

### 高级 SFINAE
- 成员函数检测（void_t 技巧）
- 运算符检测
- 复杂表达式检测
- C++20 requires 表达式和 Concepts

### 模板设计模式
- 策略模式（Policy-based Design）
- 访问者模式（编译期多态）
- 编译期状态机
- 依赖注入

### 实际应用
- 编译期正则表达式
- 单位系统（类型安全的物理量）
- 矩阵运算优化（表达式模板）
- 序列化框架
- ORM 框架基础

## 快速开始

### 环境要求
- C++20 兼容编译器（GCC 10+, Clang 12+, MSVC 2019+）
- CMake 3.16+

### 编译运行

```bash
# 进入项目目录
cd projects/cpp-template-metaprogramming-advanced

# 创建构建目录
mkdir build && cd build

# 配置
cmake ..

# 编译所有示例
cmake --build .

# 运行特定示例
./examples/example_expression_templates
./examples/example_crtp
./examples/example_compile_time_sort

# 运行测试
./tests/test_type_list
./tests/test_compile_time_algorithms
./tests/test_sfinae
./tests/test_applications
```

## 学习路径

### 入门级
1. 类型列表 (`type_list.hpp`) - 模板元编程的基础数据结构
2. 类型计数 (`type_counting.hpp`) - 统计和去重
3. 编译期排序 (`sort.hpp`) - 编译期算法入门

### 中级
4. 表达式模板 (`expression_templates.hpp`) - 延迟求值技术
5. CRTP (`crtp.hpp`) - 编译期多态
6. 策略类 (`policy_classes.hpp`) - 编译期配置
7. 标签分发 (`tag_dispatching.hpp`) - 编译期分支

### 高级
8. Mixin 模式 (`mixin.hpp`) - 模板组合
9. 编译期状态机 (`state_machine.hpp`)
10. C++20 Concepts (`requires_expressions.hpp`)
11. 单位系统 (`units_system.hpp`) - 实际应用
12. 矩阵运算 (`matrix_operations.hpp`) - 性能优化

## 项目结构

```
cpp-template-metaprogramming-advanced/
├── CMakeLists.txt
├── README.md
├── docs/                           # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_REQUIREMENTS.md
│   ├── 03_DESIGN.md
│   ├── 04_PRODUCT.md
│   └── 05_DEVELOPMENT.md
├── include/                        # 头文件库
│   ├── advanced_templates/         # 高级模板技术
│   │   ├── expression_templates.hpp
│   │   ├── crtp.hpp
│   │   ├── mixin.hpp
│   │   ├── policy_classes.hpp
│   │   └── tag_dispatching.hpp
│   ├── compile_time/               # 编译期算法
│   │   ├── algorithms.hpp
│   │   ├── sort.hpp
│   │   ├── search.hpp
│   │   └── map_filter_reduce.hpp
│   ├── type_computation/           # 类型计算
│   │   ├── type_list.hpp
│   │   ├── type_counting.hpp
│   │   └── type_conversion.hpp
│   ├── sfinae/                     # SFINAE 与 Concepts
│   │   ├── member_detection.hpp
│   │   └── requires_expressions.hpp
│   ├── design_patterns/            # 模板设计模式
│   │   ├── policy_design.hpp
│   │   ├── visitor.hpp
│   │   ├── state_machine.hpp
│   │   └── dependency_injection.hpp
│   └── applications/               # 实际应用
│       ├── units_system.hpp
│       ├── matrix_operations.hpp
│       ├── serialization.hpp
│       ├── orm_basic.hpp
│       └── compile_time_regex.hpp
├── examples/                       # 示例程序
│   ├── expression_templates.cpp
│   ├── crtp.cpp
│   ├── mixin.cpp
│   ├── policy_classes.cpp
│   ├── tag_dispatching.cpp
│   ├── compile_time_sort.cpp
│   ├── compile_time_search.cpp
│   ├── compile_time_map_filter_reduce.cpp
│   ├── type_list_ops.cpp
│   ├── type_computation.cpp
│   ├── sfinae_detection.cpp
│   ├── requires_expressions.cpp
│   ├── policy_design.cpp
│   ├── compile_time_state_machine.cpp
│   ├── compile_time_visitor.cpp
│   ├── dependency_injection.cpp
│   ├── units_system.cpp
│   ├── matrix_operations.cpp
│   ├── serialization.cpp
│   ├── orm_basic.cpp
│   └── compile_time_regex.cpp
└── tests/                          # 单元测试
    ├── type_list.cpp
    ├── compile_time_algorithms.cpp
    ├── sfinae.cpp
    └── applications.cpp
```

## 编译期断言

本项目大量使用 `static_assert` 进行编译期验证：

```cpp
// 类型列表操作在编译期完成
using sorted = tmp::bubble_sort<int, 5, 3, 8, 1, 9>;
static_assert(tmp::is_sorted<sorted>, "Should be sorted");
static_assert(tmp::value_at<sorted, 0> == 1, "First element should be 1");

// SFINAE 检测在编译期完成
static_assert(tmp::has_size_v<std::vector<int>>, "vector has size()");
static_assert(!tmp::has_size_v<int>, "int has no size()");

// 正则匹配在编译期完成
static_assert(tmp::regex::Digits::match("12345", 5), "Is digits");
static_assert(tmp::regex::is_valid_ipv4("192.168.1.1", 11), "Valid IPv4");
```

## 关键概念

### 表达式模板
表达式模板通过延迟求值避免创建临时对象，将多个运算融合为一次遍历。

### CRTP
奇异递归模板模式通过将派生类作为模板参数传递给基类，实现编译期多态。

### 策略类
策略类通过模板参数配置类的行为，在编译期确定运行时行为。

### 标签分发
标签分发通过空类型标签选择不同的函数重载，消除运行时分支。

### Concepts (C++20)
Concepts 提供了比 SFINAE 更清晰的语法来表达类型约束。

## 参考资源

- 《C++ Templates: The Complete Guide》
- 《Modern C++ Design》Andrei Alexandrescu
- C++ Reference: https://cppreference.com
- C++ Core Guidelines: https://isocpp.github.io/CppCoreGuidelines/
