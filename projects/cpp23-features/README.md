# C++23 新特性实践

一个全面的 C++23 新特性学习和实践项目，包含所有主要语言特性和标准库改进的示例代码。

## 项目简介

本项目旨在帮助 C++ 开发者快速掌握 C++23 标准引入的新特性。每个特性都有独立的示例文件，配有详细注释，可以单独编译运行。

## 快速开始

### 环境要求

- **编译器**: GCC 13+、Clang 17+ 或 MSVC 2022 17.5+
- **构建工具**: CMake 3.27+
- **操作系统**: Linux、macOS、Windows

### 编译运行

```bash
# 进入项目目录
cd projects/cpp23-features

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译所有示例
cmake --build .

# 运行特定示例
./examples/expected_example
./examples/mdspan_example

# 或者运行所有示例
ctest --output-on-failure
```

### 单独编译单个文件

```bash
# 使用 GCC
g++ -std=c++23 -o expected_example examples/expected_example.cpp
./expected_example

# 使用 Clang
clang++ -std=c++23 -o expected_example examples/expected_example.cpp
./expected_example
```

## 特性分类

### 语言特性

| 特性 | 文件 | 说明 |
|------|------|------|
| 多维下标运算符 | `multidimensional_subscript.cpp` | 支持 operator[] 多个参数 |
| if consteval | `if_consteval.cpp` | 编译期常量求值判断 |
| static operator | `static_operator.cpp` | 静态运算符重载 |
| 推断 this | `deducing_this.cpp` | 显式对象参数 |
| 标记不可达代码 | `unreachable.cpp` | std::unreachable() |
| 假设属性 | `assume_attribute.cpp` | [[assume]] 属性 |
| 字符编码转换 | `encoding.cpp` | 编码转换工具 |

### 标准库特性

| 特性 | 文件 | 说明 |
|------|------|------|
| std::expected | `expected_example.cpp` | 错误处理 |
| std::mdspan | `mdspan_example.cpp` | 多维数组视图 |
| std::generator | `generator_example.cpp` | 协程生成器 |
| std::print | `print_example.cpp` | 格式化输出 |
| std::stacktrace | `stacktrace_example.cpp` | 堆栈跟踪 |
| std::flat_map | `flat_map_example.cpp` | 扁平容器 |
| std::move_only_function | `move_only_function_example.cpp` | 移动语义函数 |
| std::out_ptr | `out_ptr_example.cpp` | 输出指针适配 |

### Ranges 特性

| 特性 | 文件 | 说明 |
|------|------|------|
| ranges::to | `ranges_to_example.cpp` | 容器转换 |
| ranges::chunk | `ranges_chunk_example.cpp` | 分块视图 |
| ranges::slide | `ranges_slide_example.cpp` | 滑动窗口 |
| ranges::zip | `ranges_zip_example.cpp` | 并行迭代 |
| ranges::enumerate | `ranges_enumerate_example.cpp` | 带索引迭代 |
| ranges::cartesian_product | `ranges_cartesian_product_example.cpp` | 笛卡尔积 |
| ranges::chunk_by | `ranges_chunk_by_example.cpp` | 按条件分块 |
| adjacent_view | `adjacent_view_example.cpp` | 相邻元素视图 |
| views::as_const | `views_as_const_example.cpp` | 常量视图 |
| views::as_rvalue | `views_as_rvalue_example.cpp` | 右值视图 |
| views::join_with | `views_join_with_example.cpp` | 连接视图 |
| views::stride | `views_stride_example.cpp` | 步长视图 |
| views::cache_latest | `views_cache_latest_example.cpp` | 缓存最新 |

### 其他改进

| 特性 | 文件 | 说明 |
|------|------|------|
| optional 范围转换 | `optional_ranges_example.cpp` | optional 与 ranges 结合 |
| tuple/pair 改进 | `tuple_pair_example.cpp` | 结构化绑定改进 |
| constexpr 扩展 | `constexpr_example.cpp` | 更多 constexpr 支持 |
| bitset 改进 | `bitset_example.cpp` | bitset 新方法 |
| string::contains | `string_contains_example.cpp` | 字符串查找 |
| ranges 算法 | `ranges_algorithms_example.cpp` | 更多算法 |

## 学习路径

### 初学者路径

1. **基础特性**: `if_consteval` -> `constexpr_example` -> `string_contains_example`
2. **容器改进**: `flat_map_example` -> `bitset_example` -> `tuple_pair_example`
3. **Ranges 入门**: `ranges_to_example` -> `ranges_enumerate_example` -> `ranges_chunk_example`

### 中级路径

1. **错误处理**: `expected_example` -> `stacktrace_example`
2. **视图操作**: `mdspan_example` -> `views_as_const_example` -> `views_stride_example`
3. **高级 Ranges**: `ranges_zip_example` -> `ranges_slide_example` -> `ranges_cartesian_product_example`

### 高级路径

1. **语言特性**: `deducing_this` -> `static_operator` -> `multidimensional_subscript`
2. **协程**: `generator_example` -> `move_only_function_example`
3. **底层工具**: `unreachable` -> `assume_attribute` -> `out_ptr_example`

## 项目结构

```
cpp23-features/
├── CMakeLists.txt
├── README.md
├── 01_RESEARCH.md
├── 02_REQUIREMENTS.md
├── 03_DESIGN.md
├── 04_PRODUCT.md
├── 05_DEVELOPMENT.md
└── examples/
    ├── expected_example.cpp
    ├── mdspan_example.cpp
    ├── generator_example.cpp
    ├── print_example.cpp
    ├── stacktrace_example.cpp
    ├── flat_map_example.cpp
    ├── ranges_to_example.cpp
    ├── ranges_chunk_example.cpp
    ├── ranges_slide_example.cpp
    ├── ranges_zip_example.cpp
    ├── ranges_enumerate_example.cpp
    ├── ranges_cartesian_product_example.cpp
    ├── ranges_chunk_by_example.cpp
    ├── adjacent_view_example.cpp
    ├── views_as_const_example.cpp
    ├── views_as_rvalue_example.cpp
    ├── views_join_with_example.cpp
    ├── views_stride_example.cpp
    ├── views_cache_latest_example.cpp
    ├── multidimensional_subscript.cpp
    ├── if_consteval.cpp
    ├── static_operator.cpp
    ├── deducing_this.cpp
    ├── unreachable.cpp
    ├── assume_attribute.cpp
    ├── encoding.cpp
    ├── move_only_function_example.cpp
    ├── out_ptr_example.cpp
    ├── optional_ranges_example.cpp
    ├── tuple_pair_example.cpp
    ├── constexpr_example.cpp
    ├── bitset_example.cpp
    ├── string_contains_example.cpp
    └── ranges_algorithms_example.cpp
```

## 编译器支持

| 特性 | GCC 13 | Clang 17 | MSVC 2022 |
|------|--------|----------|-----------|
| std::expected | ✅ | ✅ | ✅ |
| std::mdspan | ✅ | ✅ | ✅ |
| std::generator | ✅ | ✅ | ✅ |
| std::print | ✅ | ✅ | ✅ |
| std::stacktrace | ✅ | ✅ | ✅ |
| std::flat_map | ✅ | ✅ | ✅ |
| ranges::to | ✅ | ✅ | ✅ |
| Deducing this | ✅ | ✅ | ✅ |
| if consteval | ✅ | ✅ | ✅ |

## 参考资源

- [C++23 标准文档](https://en.cppreference.com/w/cpp/23)
- [C++23 特性列表](https://en.cppreference.com/w/cpp/23)
- [Compiler Support](https://en.cppreference.com/w/cpp/compiler_support/23)

## 许可证

本项目采用 MIT 许可证。
