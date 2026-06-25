# C++ 奇技淫巧集锦

## 项目介绍

C++ 奇技淫巧集锦是一个系统性的 C++ 高级技巧与最佳实践集合。本项目收录了 35 个精心挑选的 C++ 技巧，涵盖类型操控、模板元编程、内存管理、并发编程、性能优化等多个领域。

每个技巧都以独立的 `.cpp` 文件呈现，包含详细注释、实际应用示例和常见陷阱说明。无论是准备技术面试、提升代码质量，还是深入理解 C++ 语言特性，本项目都能提供实用的参考价值。

## 技巧分类

| 分类 | 技巧数量 | 难度等级 | 描述 |
|------|----------|----------|------|
| 类型技巧 (Type Tricks) | 5 | ⭐⭐ | 类型萃取、类型转换、SFINAE 等 |
| 模板技巧 (Template Tricks) | 5 | ⭐⭐⭐ | 变参模板、模板特化、CRTP 等 |
| 内存技巧 (Memory Tricks) | 5 | ⭐⭐⭐ | 智能指针、内存池、分配器等 |
| 并发技巧 (Concurrency Tricks) | 5 | ⭐⭐⭐⭐ | 原子操作、锁优化、无锁编程等 |
| 优化技巧 (Optimization Tricks) | 5 | ⭐⭐⭐ | 编译期计算、缓存优化、移动语义等 |
| 实用工具 (Utility Tools) | 5 | ⭐⭐ | 调试技巧、类型打印、计时器等 |
| 代码风格 (Code Style) | 5 | ⭐⭐ | RAII、命名规范、错误处理等 |

## 快速开始

### 环境要求

- **编译器**: GCC 10+, Clang 12+, MSVC 2019+
- **构建工具**: CMake 3.16+
- **C++ 标准**: C++17 或 C++20

### 构建与运行

```bash
# 克隆项目
git clone <repository-url>
cd cpp-tricks-and-tips

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译所有技巧示例
cmake --build .

# 运行特定技巧示例
./bin/type_trick_01      # 运行类型技巧示例
./bin/template_trick_03  # 运行模板技巧示例

# 运行所有示例
ctest --output-on-failure
```

### 单独编译某个技巧

```bash
# 只编译特定文件
g++ -std=c++17 -I../include ../src/type_tricks/01_type_id.cpp -o type_id_demo
./type_id_demo
```

## 项目结构

```
cpp-tricks-and-tips/
├── CMakeLists.txt              # 主 CMake 配置文件
├── README.md                   # 项目说明文档
├── docs/                       # 文档目录
│   ├── 01_RESEARCH.md          # 市场调研
│   ├── 02_REQUIREMENTS.md      # 需求分析
│   ├── 03_DESIGN.md            # 技术设计
│   ├── 04_PRODUCT.md           # 产品思维
│   └── 05_DEVELOPMENT.md       # 开发手册
├── include/                    # 公共头文件
│   ├── common.hpp              # 通用工具宏和函数
│   ├── type_utils.hpp          # 类型工具库
│   └── benchmark.hpp           # 性能测试工具
├── src/                        # 源代码目录
│   ├── type_tricks/            # 类型技巧
│   │   ├── 01_type_id.cpp
│   │   ├── 02_type_conversion.cpp
│   │   ├── 03_sfinae.cpp
│   │   ├── 04_type_traits.cpp
│   │   └── 05_if_constexpr.cpp
│   ├── template_tricks/        # 模板技巧
│   │   ├── 01_variadic_templates.cpp
│   │   ├── 02_template_specialization.cpp
│   │   ├── 03_crtp.cpp
│   │   ├── 04_sfinae_advanced.cpp
│   │   └── 05_concepts.cpp
│   ├── memory_tricks/          # 内存技巧
│   │   ├── 01_smart_pointers.cpp
│   │   ├── 02_memory_pool.cpp
│   │   ├── 03_custom_allocator.cpp
│   │   ├── 04_placement_new.cpp
│   │   └── 05_raii.cpp
│   ├── concurrency_tricks/     # 并发技巧
│   │   ├── 01_atomics.cpp
│   │   ├── 02_lock_guard.cpp
│   │   ├── 03_thread_pool.cpp
│   │   ├── 04_lock_free.cpp
│   │   └── 05_async.cpp
│   ├── optimization_tricks/    # 优化技巧
│   │   ├── 01_move_semantics.cpp
│   │   ├── 02_constexpr.cpp
│   │   ├── 03_cache_optimization.cpp
│   │   ├── 04_sso.cpp
│   │   └── 05_loop_unrolling.cpp
│   ├── utility_tools/          # 实用工具
│   │   ├── 01_debug_print.cpp
│   │   ├── 02_type_printer.cpp
│   │   ├── 03_timer.cpp
│   │   ├── 04_scope_guard.cpp
│   │   └── 05_any_variant.cpp
│   └── code_style/             # 代码风格
│       ├── 01_raii_patterns.cpp
│       ├── 02_naming_conventions.cpp
│       ├── 03_error_handling.cpp
│       ├── 04_modern_cpp_style.cpp
│       └── 05_best_practices.cpp
├── tests/                      # 测试目录
│   ├── test_type_tricks.cpp
│   ├── test_template_tricks.cpp
│   └── ...
└── examples/                   # 综合示例
    └── real_world_examples.cpp
```

## 学习路径

### 入门阶段 (1-2 周)
- 代码风格 (Code Style) - 建立良好的编程习惯
- 实用工具 (Utility Tools) - 掌握调试和开发效率工具

### 进阶阶段 (2-3 周)
- 类型技巧 (Type Tricks) - 理解 C++ 类型系统
- 优化技巧 (Optimization Tricks) - 学习性能优化方法

### 高级阶段 (3-4 周)
- 模板技巧 (Template Tricks) - 掌握模板元编程
- 内存技巧 (Memory Tricks) - 深入内存管理

### 专家阶段 (4+ 周)
- 并发技巧 (Concurrency Tricks) - 精通并发编程
- 综合实战 - 完成 `examples/` 中的综合项目

## 技巧速查表

### 类型技巧
| 编号 | 技巧名称 | 关键字 |
|------|----------|--------|
| 01 | 类型标识 | `typeid`, `type_info` |
| 02 | 类型转换 | `static_cast`, `dynamic_cast` |
| 03 | SFINAE | `enable_if`, `void_t` |
| 04 | 类型萃取 | `type_traits`, `is_same` |
| 05 | if constexpr | `constexpr if`, 编译期分支 |

### 模板技巧
| 编号 | 技巧名称 | 关键字 |
|------|----------|--------|
| 01 | 变参模板 | `parameter pack`, `fold expression` |
| 02 | 模板特化 | `template specialization` |
| 03 | CRTP | `Curiously Recurring Template Pattern` |
| 04 | 高级 SFINAE | `detection idiom`, `is_detected` |
| 05 | Concepts | `requires`, `concept` |

### 内存技巧
| 编号 | 技巧名称 | 关键字 |
|------|----------|--------|
| 01 | 智能指针 | `unique_ptr`, `shared_ptr` |
| 02 | 内存池 | `memory pool`, `object pool` |
| 03 | 自定义分配器 | `allocator`, `allocator_traits` |
| 04 | Placement new | `placement new`, `construct_at` |
| 05 | RAII | `Resource Acquisition Is Initialization` |

### 并发技巧
| 编号 | 技巧名称 | 关键字 |
|------|----------|--------|
| 01 | 原子操作 | `atomic`, `memory_order` |
| 02 | 锁守卫 | `lock_guard`, `unique_lock` |
| 03 | 线程池 | `thread pool`, `task queue` |
| 04 | 无锁编程 | `lock-free`, `CAS` |
| 05 | 异步编程 | `async`, `future`, `promise` |

### 优化技巧
| 编号 | 技巧名称 | 关键字 |
|------|----------|--------|
| 01 | 移动语义 | `std::move`, `rvalue reference` |
| 02 | constexpr | `constexpr`, `consteval` |
| 03 | 缓存优化 | `cache line`, `data locality` |
| 04 | SSO | `Small String Optimization` |
| 05 | 循环展开 | `loop unrolling`, `pragma unroll` |

## 参考资源

### 推荐书籍
- 《Effective Modern C++》 - Scott Meyers
- 《C++ Templates: The Complete Guide》 - David Vandevoorde
- 《The C++ Programming Language》 - Bjarne Stroustrup
- 《C++ Concurrency in Action》 - Anthony Williams

### 在线资源
- [CppCon Talks](https://www.youtube.com/user/CppCon)
- [C++ Reference](https://en.cppreference.com/)
- [CppStories](https://www.cppstories.com/)
- [Godbolt Compiler Explorer](https://godbolt.org/)

## 贡献指南

欢迎提交新的技巧或改进现有代码：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/new-trick`)
3. 提交更改 (`git commit -m 'Add new type trick'`)
4. 推送到远程分支 (`git push origin feature/new-trick`)
5. 创建 Pull Request

### 代码规范
- 每个技巧文件必须包含详细注释
- 代码必须能在 GCC 10+ 和 Clang 12+ 上编译通过
- 提供实际应用场景示例

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
