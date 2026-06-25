# C++ 常见陷阱和最佳实践

## 项目简介

本项目收集并展示了 C++ 开发中常见的陷阱和最佳实践。每个陷阱都配有详细的代码示例，展示问题代码和正确做法，帮助开发者避免常见错误，编写更安全、更高效的 C++ 代码。

## 项目特点

- **实战导向**：每个陷阱都有可运行的代码示例
- **对比学习**：同时展示错误做法和正确做法
- **分类清晰**：按陷阱类型组织，便于查阅
- **现代 C++**：使用 C++17/20 特性，展示现代编程风格

## 陷阱分类

### 1. 内存陷阱 (Memory Pitfalls)
- 悬空指针 (Dangling Pointer)
- 内存泄漏 (Memory Leak)
- 双重释放 (Double Free)
- 缓冲区溢出 (Buffer Overflow)
- 野指针 (Wild Pointer)
- 使用已释放内存

### 2. 类型陷阱 (Type Pitfalls)
- 隐式转换陷阱
- 整数溢出
- 浮点精度问题
- 有符号/无符号混用
- 类型截断
- 空指针解引用

### 3. 模板陷阱 (Template Pitfalls)
- 模板实例化问题
- 模板特化陷阱
- SFINAE 陷阱
- 模板编译错误
- 依赖类型问题

### 4. 并发陷阱 (Concurrency Pitfalls)
- 数据竞争 (Data Race)
- 死锁 (Deadlock)
- 活锁 (Livelock)
- 原子操作陷阱
- 内存序陷阱
- 伪共享 (False Sharing)

### 5. 生命周期陷阱 (Lifetime Pitfalls)
- 对象生命周期
- 临时对象陷阱
- 引用悬挂
- 移动后使用
- 析构顺序

### 6. 异常安全陷阱 (Exception Safety Pitfalls)
- 异常安全级别
- 资源泄漏
- 异常传播
- noexcept 使用

### 7. 最佳实践 (Best Practices)
- 现代 C++ 风格
- RAII 应用
- 智能指针使用
- 值语义 vs 引用语义
- 常量正确性
- 命名规范

### 8. 代码质量 (Code Quality)
- 代码审查清单
- 静态分析工具
- 动态分析工具
- 测试策略
- 文档规范

## 快速开始

### 环境要求

- C++17 或更高版本的编译器（推荐 GCC 10+, Clang 12+, MSVC 2019+）
- CMake 3.16+
- 支持 POSIX 的系统（Linux/macOS）或 Windows

### 编译运行

```bash
# 克隆项目
cd projects/cpp-pitfalls-best-practices

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译
cmake --build .

# 运行所有示例
./bin/memory_pitfalls
./bin/type_pitfalls
./bin/template_pitfalls
./bin/concurrency_pitfalls
./bin/lifetime_pitfalls
./bin/exception_safety
./bin/best_practices
```

### 单独运行某个陷阱示例

```bash
# 编译单个文件
g++ -std=c++17 -o dangling_ptr ../src/memory/01_dangling_pointer.cpp
./dangling_ptr
```

## 学习路径

### 初学者路径
1. 内存陷阱 → 理解指针和内存管理
2. 类型陷阱 → 掌握类型系统
3. 生命周期陷阱 → 理解对象生命周期
4. 最佳实践 → 学习现代 C++ 风格

### 中级开发者路径
1. 模板陷阱 → 深入模板编程
2. 异常安全陷阱 → 掌握异常处理
3. 代码质量 → 提升代码质量

### 高级开发者路径
1. 并发陷阱 → 掌握多线程编程
2. 内存序陷阱 → 理解内存模型
3. 性能陷阱 → 优化代码性能

## 文件结构

```
cpp-pitfalls-best-practices/
├── README.md                    # 本文件
├── 01_RESEARCH.md              # 市场调研
├── 02_REQUIREMENTS.md          # 需求分析
├── 03_DESIGN.md                # 技术设计
├── 04_PRODUCT.md               # 产品思考
├── 05_DEVELOPMENT.md           # 开发手册
├── CMakeLists.txt              # 构建配置
└── src/
    ├── memory/                 # 内存陷阱
    │   ├── 01_dangling_pointer.cpp
    │   ├── 02_memory_leak.cpp
    │   ├── 03_double_free.cpp
    │   ├── 04_buffer_overflow.cpp
    │   ├── 05_wild_pointer.cpp
    │   └── 06_use_after_free.cpp
    ├── type/                   # 类型陷阱
    │   ├── 01_implicit_conversion.cpp
    │   ├── 02_integer_overflow.cpp
    │   ├── 03_floating_point.cpp
    │   ├── 04_signed_unsigned.cpp
    │   ├── 05_type_truncation.cpp
    │   └── 06_null_dereference.cpp
    ├── template/               # 模板陷阱
    │   ├── 01_instantiation.cpp
    │   ├── 02_specialization.cpp
    │   ├── 03_sfinae.cpp
    │   ├── 04_compile_errors.cpp
    │   └── 05_dependent_type.cpp
    ├── concurrency/            # 并发陷阱
    │   ├── 01_data_race.cpp
    │   ├── 02_deadlock.cpp
    │   ├── 03_livelock.cpp
    │   ├── 04_atomic_traps.cpp
    │   ├── 05_memory_order.cpp
    │   └── 06_false_sharing.cpp
    ├── lifetime/               # 生命周期陷阱
    │   ├── 01_object_lifetime.cpp
    │   ├── 02_temporary_object.cpp
    │   ├── 03_dangling_reference.cpp
    │   ├── 04_use_after_move.cpp
    │   └── 05_destruction_order.cpp
    ├── exception/              # 异常安全陷阱
    │   ├── 01_safety_levels.cpp
    │   ├── 02_resource_leak.cpp
    │   ├── 03_exception_propagation.cpp
    │   └── 04_noexcept.cpp
    ├── best_practices/         # 最佳实践
    │   ├── 01_modern_cpp.cpp
    │   ├── 02_raii.cpp
    │   ├── 03_smart_pointers.cpp
    │   ├── 04_value_semantics.cpp
    │   ├── 05_const_correctness.cpp
    │   └── 06_naming_conventions.cpp
    └── quality/                # 代码质量
        ├── 01_code_review.cpp
        ├── 02_static_analysis.cpp
        ├── 03_dynamic_analysis.cpp
        ├── 04_testing.cpp
        └── 05_documentation.cpp
```

## 贡献指南

欢迎贡献新的陷阱示例或改进建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/new-pitfall`)
3. 提交更改 (`git commit -m 'Add new pitfall example'`)
4. 推送到分支 (`git push origin feature/new-pitfall`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 参考资源

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [Effective Modern C++](https://www.oreilly.com/library/view/effective-modern-c/9781491908419/)
- [C++ Concurrency in Action](https://www.manning.com/books/c-plus-plus-concurrency-in-action)
- [Compiler Explorer](https://godbolt.org/)
- [Sanitizers](https://github.com/google/sanitizers)
