# C++ 代码规范和风格

一个完整的 C++ 代码规范和风格参考项目，涵盖命名规范、代码格式、类设计、内存管理、并发编程等核心主题。

## 项目简介

本项目旨在帮助开发者掌握 C++ 代码规范和最佳实践，通过实际示例展示良好代码与糟糕代码的区别。

## 学习目标

1. 掌握 C++ 命名规范和代码格式
2. 理解头文件设计和类设计原则
3. 学会内存管理和资源管理最佳实践
4. 掌握并发编程规范和错误处理
5. 了解代码审查流程和工具配置

## 项目结构

```
cpp-coding-standards/
├── examples/                    # 代码示例
│   ├── 01-naming/              # 命名规范示例
│   ├── 02-formatting/          # 代码格式示例
│   ├── 03-header-files/        # 头文件规范示例
│   ├── 04-class-design/        # 类设计示例
│   ├── 05-function-design/     # 函数设计示例
│   ├── 06-memory-management/   # 内存管理示例
│   ├── 07-concurrency/         # 并发编程示例
│   ├── 08-error-handling/      # 错误处理示例
│   ├── 09-comments/            # 注释规范示例
│   └── 10-tools/               # 工具配置示例
├── docs/                        # 文档
│   ├── 01_RESEARCH.md          # 市场调研
│   ├── 02_REQUIREMENTS.md      # 需求分析
│   ├── 03_DESIGN.md            # 技术设计
│   ├── 04_PRODUCT.md           # 产品思考
│   └── 05_DEVELOPMENT.md       # 开发手册
├── include/                     # 头文件
├── src/                         # 源代码
├── tests/                       # 测试文件
├── tools/                       # 工具配置
│   ├── .clang-format           # Clang-Format 配置
│   ├── .clang-tidy             # Clang-Tidy 配置
│   └── .editorconfig           # EditorConfig 配置
├── CMakeLists.txt               # CMake 配置
└── README.md                    # 本文件
```

## 快速开始

### 环境要求

- C++17/20 编译器（GCC 10+, Clang 12+, MSVC 2019+）
- CMake 3.16+
- Clang-Format 12+（可选）
- Clang-Tidy 12+（可选）

### 编译运行

```bash
# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译所有示例
cmake --build .

# 运行特定示例
./examples/01-naming/naming_demo
./examples/02-formatting/formatting_demo
```

### 使用工具

```bash
# 格式化代码
clang-format -i -style=file examples/**/*.cpp

# 静态分析
clang-tidy -p build examples/**/*.cpp
```

## 规范分类

### 1. 命名规范
- 变量命名（camelCase, snake_case, PascalCase）
- 函数命名、类命名、常量命名
- 宏命名、命名空间命名

### 2. 代码格式
- 缩进风格、大括号风格
- 行长度限制、空格使用
- 空行使用、注释格式

### 3. 头文件规范
- 头文件保护、#include 顺序
- 前向声明、模块化设计

### 4. 类设计规范
- 成员顺序、访问控制
- 构造/析构函数设计
- 运算符重载、友元使用

### 5. 函数设计规范
- 函数长度、参数设计
- 返回值设计、异常规范

### 6. 内存管理规范
- 智能指针使用、RAII 应用
- 资源管理最佳实践

### 7. 并发规范
- 线程安全、原子操作
- 锁使用、异步编程

### 8. 错误处理规范
- 异常使用、错误码
- 断言使用、日志规范

### 9. 注释规范
- 文件注释、函数注释
- 类注释、TODO/FIXME

### 10. 工具配置
- Clang-Format、Clang-Tidy
- EditorConfig、IDE 配置

## 学习路径

### 初学者
1. 命名规范 → 代码格式 → 注释规范
2. 理解基本风格要求

### 进阶者
3. 头文件规范 → 类设计 → 函数设计
4. 掌握设计原则

### 高级者
5. 内存管理 → 并发编程 → 错误处理
6. 工具配置 → 代码审查

## 参考资源

- [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [LLVM Coding Standards](https://llvm.org/docs/CodingStandards.html)
- [Mozilla C++ Style Guide](https://firefox-source-docs.mozilla.org/code-quality/coding-style/index.html)
