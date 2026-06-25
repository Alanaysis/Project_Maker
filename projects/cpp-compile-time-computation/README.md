# C++ 编译期计算

一个系统化的 C++ 编译期计算学习项目，涵盖 constexpr、consteval、constinit 等核心技术，从基础概念到实际应用。

## 项目简介

编译期计算是现代 C++ 最重要的特性之一。它允许程序在编译阶段完成尽可能多的工作，从而显著减少运行时开销、提升类型安全性并实现零成本抽象。

本项目提供：

- 完整的编译期计算知识体系
- 每个特性独立的源文件和详细注释
- 实际应用场景的示例代码
- 编译期与运行时的性能对比
- C++11/14/17/20 各版本特性的演进说明

## 快速开始

```bash
# 配置
cmake -B build -DCMAKE_BUILD_TYPE=Release

# 编译所有示例
cmake --build build

# 运行测试
cd build && ctest --output-on-failure

# 运行单个示例
./build/example_constexpr_basics
```

## 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                   编译期计算技术栈                              │
├─────────────────────────────────────────────────────────────┤
│  constexpr   │ 编译期可求值的函数和变量（C++11+）              │
│  consteval   │ 必须在编译期求值的立即函数（C++20）              │
│  constinit   │ 保证常量初始化，避免静态初始化顺序问题（C++20）   │
│  template    │ 模板元编程，类型级别的计算                       │
│  concepts    │ 编译期类型约束（C++20）                         │
└─────────────────────────────────────────────────────────────┘
```

## 学习路径

### 第一阶段：基础（01-03）

| 序号 | 文件 | 内容 |
|------|------|------|
| 01 | `constexpr_basics.cpp` | constexpr 函数、变量、类的用法 |
| 02 | `consteval.cpp` | 立即函数与 constexpr 的区别 |
| 03 | `constinit.cpp` | 常量初始化与静态初始化顺序 |

### 第二阶段：数据结构（04-07）

| 序号 | 文件 | 内容 |
|------|------|------|
| 04 | `fixed_string.cpp` | 编译期字符串 |
| 05 | `compile_time_array.cpp` | 编译期数组 |
| 06 | `compile_time_map.cpp` | 编译期映射 |
| 07 | `compile_time_set.cpp` | 编译期集合 |

### 第三阶段：算法（08-11）

| 序号 | 文件 | 内容 |
|------|------|------|
| 08 | `math_functions.cpp` | 编译期数学函数 |
| 09 | `compile_time_sort.cpp` | 编译期排序算法 |
| 10 | `compile_time_hash.cpp` | 编译期哈希函数 |
| 11 | `compile_time_regex.cpp` | 编译期正则表达式匹配 |

### 第四阶段：应用（12-16）

| 序号 | 文件 | 内容 |
|------|------|------|
| 12 | `config_parser.cpp` | 编译期配置解析 |
| 13 | `lookup_table.cpp` | 编译期查找表生成 |
| 14 | `unit_conversion.cpp` | 编译期单位转换 |
| 15 | `state_machine.cpp` | 编译期状态机 |
| 16 | `reflection.cpp` | 编译期反射（基础） |

### 第五阶段：进阶（17-18）

| 序号 | 文件 | 内容 |
|------|------|------|
| 17 | `performance_benchmark.cpp` | 编译期 vs 运行时性能测试 |
| 18 | `best_practices.cpp` | 最佳实践和常见陷阱 |

## 编译运行

### 前置要求

- C++ 编译器：GCC 12+、Clang 15+ 或 MSVC 2022+
- CMake 3.16+

### 编译单个示例

```bash
g++ -std=c++20 -I include examples/constexpr_basics.cpp -o constexpr_basics
```

### 编译所有示例

```bash
cmake -B build && cmake --build build
```

## 文件结构

```
cpp-compile-time-computation/
├── CMakeLists.txt
├── README.md
├── docs/
│   ├── 01_RESEARCH.md        # 市场调研
│   ├── 02_REQUIREMENTS.md     # 需求分析
│   ├── 03_DESIGN.md          # 技术设计
│   ├── 04_PRODUCT.md         # 产品思考
│   └── 05_DEVELOPMENT.md     # 开发手册
├── include/
│   └── compile_time/
│       ├── fixed_string.hpp   # 编译期字符串
│       ├── array.hpp          # 编译期数组
│       ├── map.hpp            # 编译期映射
│       ├── set.hpp            # 编译期集合
│       ├── math.hpp           # 编译期数学函数
│       ├── hash.hpp           # 编译期哈希
│       ├── regex.hpp          # 编译期正则
│       ├── config.hpp         # 编译期配置
│       ├── lookup.hpp         # 编译期查找表
│       ├── unit.hpp           # 编译期单位转换
│       ├── state_machine.hpp  # 编译期状态机
│       └── reflection.hpp     # 编译期反射
├── examples/
│   ├── constexpr_basics.cpp
│   ├── consteval.cpp
│   ├── constinit.cpp
│   ├── ...（更多示例）
├── tests/
│   └── compile_time_tests.cpp
└── benchmarks/
    └── performance_benchmark.cpp
```
