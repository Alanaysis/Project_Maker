# C++ 模板元编程基础

一个系统性的 C++ 模板元编程学习项目，涵盖从基础到高级的模板元编程技术。

## 项目简介

本项目通过独立的代码示例，系统地介绍 C++ 模板元编程的核心概念和技术。每个示例都可以独立编译运行，包含详细的中文注释。

## 快速开始

```bash
# 克隆项目
cd projects/cpp-template-metaprogramming

# 创建构建目录
mkdir build && cd build

# 编译所有示例
cmake .. && make

# 运行特定示例
./function_templates
./class_templates
# ... 其他示例
```

## 核心概念

### 1. 模板基础
- **函数模板** - 泛型函数的定义与使用
- **类模板** - 泛型类的定义与使用
- **模板特化** - 全特化与偏特化
- **非类型参数** - 整数、枚举等作为模板参数
- **模板模板参数** - 模板作为模板参数

### 2. 类型萃取 (Type Traits)
- **基础类型判断** - is_integral, is_floating_point, is_pointer
- **类型转换** - remove_const, add_pointer, decay
- **类型关系** - is_same, is_base_of, is_convertible

### 3. SFINAE 技术
- **enable_if** - 条件启用模板重载
- **void_t 技巧** - 检测表达式合法性
- **表达式检测** - 检测成员函数、操作符等

### 4. 参数包 (Parameter Pack)
- **可变参数模板** - 接受任意数量参数
- **参数包展开** - 递归展开、折叠表达式
- **C++17 折叠表达式** - 简洁的参数包操作

### 5. 编译期数据结构
- **TypeList** - 编译期类型列表
- **integer_sequence** - 编译期整数序列
- **编译期字符串** - 编译期字符串操作

### 6. 实用案例
- **编译期计算** - factorial, fibonacci, 素数检测
- **类型擦除** - std::function, std::any 的实现原理
- **访问者模式** - 基于 variant 的多态访问
- **依赖注入** - 模板实现的 DI 容器

## 学习路径

```
1. 模板基础
   ├── 函数模板 → 类模板 → 模板特化
   ├── 非类型参数 → 模板模板参数
   └── 理解模板实例化和特化匹配规则

2. 类型萃取
   ├── integral_constant → true_type/false_type
   ├── 基础类型判断 → 类型转换 → 类型关系
   └── 理解编译期类型信息

3. SFINAE
   ├── enable_if 基本用法
   ├── void_t 技巧
   └── 表达式合法性检测

4. 参数包
   ├── 可变参数模板基础
   ├── 参数包展开技巧
   └── C++17 折叠表达式

5. 编译期数据结构
   ├── TypeList 及其操作
   ├── integer_sequence
   └── 编译期字符串

6. 实用案例
   ├── 编译期数学计算
   ├── 类型擦除技术
   ├── 访问者模式
   └── 依赖注入容器
```

## 编译运行

### 编译所有示例

```bash
mkdir build && cd build
cmake ..
make
```

### 编译单个示例

```bash
cd src/01_template_basics
g++ -std=c++17 -o function_templates function_templates.cpp
./function_templates
```

### 使用自定义头文件

```bash
g++ -std=c++17 -I../../include -o demo demo.cpp
```

## 文件结构

```
cpp-template-metaprogramming/
├── CMakeLists.txt
├── README.md
├── include/
│   ├── type_traits/
│   │   ├── basic_traits.hpp
│   │   ├── type_transform.hpp
│   │   └── type_relations.hpp
│   ├── sfinae/
│   │   ├── enable_if.hpp
│   │   ├── void_t.hpp
│   │   └── expression_detector.hpp
│   ├── variadic/
│   │   ├── parameter_pack.hpp
│   │   └── fold_expressions.hpp
│   ├── compile_time/
│   │   ├── type_list.hpp
│   │   ├── integer_sequence.hpp
│   │   └── compile_time_string.hpp
│   └── utilities/
│       ├── type_erasure.hpp
│       └── visitor.hpp
└── src/
    ├── 01_template_basics/
    ├── 02_type_traits/
    ├── 03_sfinae/
    ├── 04_parameter_pack/
    ├── 05_compile_time_data/
    └── 06_practical_cases/
```

## 参考资源

- [C++ Templates: The Complete Guide](https://www.amazon.com/Templates-Complete-Guide-2nd/dp/0134778762)
- [Modern C++ Design](https://www.amazon.com/Modern-Design-Policy-Designing-Addison-Wesley/dp/0201704315)
- [C++ Template Metaprogramming](https://www.amazon.com/Template-Metaprogramming-Concepts-Techniques-Beyond/dp/0321227255)
- [cppreference.com](https://en.cppreference.com/)
