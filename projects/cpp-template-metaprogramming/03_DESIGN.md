# 技术设计

## 文件组织

### 头文件结构

```
include/
├── type_traits/          # 类型萃取
│   ├── basic_traits.hpp  # 基础类型判断
│   ├── type_transform.hpp # 类型转换
│   └── type_relations.hpp # 类型关系
├── sfinae/               # SFINAE 技术
│   ├── enable_if.hpp     # enable_if
│   ├── void_t.hpp        # void_t 技巧
│   └── expression_detector.hpp # 表达式检测
├── variadic/             # 参数包
│   ├── parameter_pack.hpp # 可变参数模板
│   └── fold_expressions.hpp # 折叠表达式
├── compile_time/         # 编译期数据结构
│   ├── type_list.hpp     # 类型列表
│   ├── integer_sequence.hpp # 整数序列
│   └── compile_time_string.hpp # 编译期字符串
└── utilities/            # 实用工具
    ├── type_erasure.hpp  # 类型擦除
    └── visitor.hpp       # 访问者模式
```

### 源文件结构

```
src/
├── 01_template_basics/   # 模板基础示例
│   ├── function_templates.cpp
│   ├── class_templates.cpp
│   ├── specialization.cpp
│   ├── non_type_params.cpp
│   └── template_template_params.cpp
├── 02_type_traits/       # 类型萃取示例
│   ├── basic_traits_demo.cpp
│   ├── type_transform_demo.cpp
│   └── type_relations_demo.cpp
├── 03_sfinae/            # SFINAE 示例
│   ├── enable_if_demo.cpp
│   ├── void_t_demo.cpp
│   └── expression_detector_demo.cpp
├── 04_parameter_pack/    # 参数包示例
│   ├── parameter_pack_demo.cpp
│   └── fold_expressions_demo.cpp
├── 05_compile_time_data/ # 编译期数据结构示例
│   ├── type_list_demo.cpp
│   ├── integer_sequence_demo.cpp
│   └── compile_time_string_demo.cpp
└── 06_practical_cases/   # 实用案例
    ├── factorial_fibonacci.cpp
    ├── type_erasure.cpp
    ├── visitor_pattern.cpp
    └── dependency_injection.cpp
```

## 设计原则

### 1. 模块化设计

- 每个头文件专注于一个主题
- 头文件之间最小依赖
- 使用命名空间隔离

### 2. 渐进式复杂度

- 从简单到复杂
- 每个示例独立可运行
- 逐步引入新概念

### 3. 实践导向

- 每个概念都有实际应用示例
- 包含编译期断言验证
- 包含实际应用场景

## 示例设计

### 示例结构

每个示例文件遵循以下结构：

```cpp
// 文件头注释
// 编译和运行说明

#include <iostream>
// 其他必要的头文件

// 1. 概念定义
// 2. 实现代码
// 3. 使用示例

int main() {
    std::cout << "=== 主题名称 ===" << std::endl;
    
    // 分节演示
    // 1. 基本用法
    // 2. 进阶用法
    // 3. 实际应用
    
    std::cout << "=== 演示完成 ===" << std::endl;
    return 0;
}
```

### 命名规范

- **命名空间**: `tmp` (template metaprogramming)
- **类名**: PascalCase
- **函数名**: snake_case
- **常量**: kPascalCase 或 SCREAMING_SNAKE_CASE
- **模板参数**: PascalCase

### 注释规范

```cpp
// 文件头注释
// =============================================================================
// filename.cpp - 简短描述
// =============================================================================
// 编译: g++ -std=c++17 -o filename filename.cpp
// 运行: ./filename
// =============================================================================

// 章节注释
// ---------------------------------------------------------------------------
// 1. 章节标题
// ---------------------------------------------------------------------------

// 功能注释
// 函数或类的简短描述
```

## 依赖关系

```
basic_traits.hpp
    ↓
type_transform.hpp
    ↓
type_relations.hpp
    ↓
enable_if.hpp / void_t.hpp
    ↓
expression_detector.hpp
    ↓
parameter_pack.hpp / fold_expressions.hpp
    ↓
type_list.hpp / integer_sequence.hpp
    ↓
compile_time_string.hpp
    ↓
type_erasure.hpp / visitor.hpp
```

## 编译配置

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.16)
project(cpp-template-metaprogramming LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${CMAKE_SOURCE_DIR}/include)

# 添加每个示例为独立的可执行文件
add_executable(function_templates src/01_template_basics/function_templates.cpp)
# ... 其他示例
```

### 编译选项

- **C++ 标准**: C++17 (最低) / C++20 (推荐)
- **优化级别**: -O2 (推荐)
- **警告**: -Wall -Wextra -Wpedantic
- **调试**: -g (调试时)
