# C++20 新特性实践

> 通过 17 个独立示例 + 1 个综合示例，系统学习 C++20 所有主要新特性

---

## 快速开始

### 环境要求

- C++ 编译器：GCC 10+、Clang 13+、MSVC 19.29+
- CMake 3.16+
- 操作系统：Linux、macOS、Windows

### 编译运行

```bash
# 克隆项目
cd projects/cpp20-features

# 创建构建目录
mkdir build && cd build

# 配置
cmake ..

# 编译所有示例
make -j$(nproc)

# 运行单个示例
./01_concepts
./02_ranges
./03_coroutines
# ...

# 运行所有测试
ctest --output-on-failure
```

### 快速体验

```bash
# 编译并运行概念示例
cd build && cmake .. && make 01_concepts && ./01_concepts
```

---

## 特性分类

### 四大核心特性

| 特性 | 文件 | 难度 | 描述 |
|------|------|------|------|
| 概念 (Concepts) | `01_concepts.cpp` | ⭐⭐⭐ | 约束模板参数，让模板编程更安全 |
| 范围 (Ranges) | `02_ranges.cpp` | ⭐⭐⭐⭐ | 惰性求值的数据处理管道 |
| 协程 (Coroutines) | `03_coroutines.cpp` | ⭐⭐⭐⭐⭐ | 无栈协程，挂起/恢复机制 |
| 模块 (Modules) | `04_modules/` | ⭐⭐⭐ | 替代头文件的模块系统 |

### 语言特性

| 特性 | 文件 | 难度 | 描述 |
|------|------|------|------|
| 三向比较 <=> | `05_spaceship_operator.cpp` | ⭐⭐ | 自动生成比较运算符 |
| consteval/constinit | `06_consteval_constinit.cpp` | ⭐⭐⭐ | 编译期计算增强 |
| 聚合初始化 | `07_aggregate_init.cpp` | ⭐⭐ | 更灵活的聚合类型初始化 |
| 范围 for 初始化 | `08_range_for_init.cpp` | ⭐ | for 循环支持初始化语句 |
| Lambda 改进 | `09_lambda_improvements.cpp` | ⭐⭐⭐ | 模板 Lambda、捕获改进 |
| [[no_unique_address]] | `10_no_unique_address.cpp` | ⭐⭐ | 空成员不占空间 |
| using enum | `11_using_enum.cpp` | ⭐ | 枚举成员引入作用域 |

### 标准库特性

| 特性 | 文件 | 难度 | 描述 |
|------|------|------|------|
| std::format | `12_std_format.cpp` | ⭐⭐ | 类型安全的格式化库 |
| std::span | `13_std_span.cpp` | ⭐⭐ | 非拥有的连续内存视图 |
| std::jthread | `14_std_jthread.cpp` | ⭐⭐⭐ | 自动合并的线程 |
| 同步原语 | `15_synchronization.cpp` | ⭐⭐⭐⭐ | latch、barrier、semaphore |
| std::source_location | `16_std_source_location.cpp` | ⭐⭐ | 编译期源代码位置信息 |
| std::stop_token | `17_std_stop_token.cpp` | ⭐⭐⭐ | 协作式线程取消机制 |

### 综合示例

| 文件 | 描述 |
|------|------|
| `18_comprehensive.cpp` | 综合运用多个 C++20 特性构建实际应用 |

---

## 学习路径

### 推荐学习顺序

```
入门路径（语言特性）:
  using_enum -> 范围for初始化 -> 聚合初始化 -> 三向比较 -> consteval/constinit
     ↓              ↓                ↓              ↓              ↓
  减少冗余      限制作用域        指定初始化器    自动比较      编译期计算

进阶路径（核心特性）:
  Concepts -> Ranges -> Lambda改进 -> [[no_unique_address]] -> format/span
     ↓          ↓          ↓                ↓                      ↓
  模板约束    数据管道    模板Lambda        EBO优化              现代API

高级路径（并发和系统）:
  jthread -> stop_token -> 同步原语 -> source_location -> Coroutines
     ↓          ↓            ↓              ↓                ↓
  自动管理    协作取消    barrier/sem     增强调试          异步编程
```

### 按难度分组

- **入门** (⭐-⭐⭐): using_enum, 范围for初始化, 聚合初始化, 三向比较, consteval/constinit, format, span, source_location, no_unique_address
- **中级** (⭐⭐⭐): Concepts, Lambda改进, jthread, stop_token
- **高级** (⭐⭐⭐⭐-⭐⭐⭐⭐⭐): Ranges, 同步原语, Coroutines

---

## 文件结构

```
cpp20-features/
├── CMakeLists.txt          # 构建配置
├── README.md               # 项目说明
├── 01_RESEARCH.md          # 市场调研
├── 02_REQUIREMENTS.md      # 需求分析
├── 03_DESIGN.md            # 技术设计
├── 04_PRODUCT.md           # 产品思考
├── 05_DEVELOPMENT.md       # 开发手册
└── src/
    ├── 01_concepts.cpp          # 概念
    ├── 02_ranges.cpp            # 范围
    ├── 03_coroutines.cpp        # 协程
    ├── 05_spaceship_operator.cpp # 三向比较
    ├── 06_consteval_constinit.cpp # consteval/constinit
    ├── 07_aggregate_init.cpp    # 聚合初始化
    ├── 08_range_for_init.cpp    # 范围for初始化
    ├── 09_lambda_improvements.cpp # Lambda改进
    ├── 10_no_unique_address.cpp # [[no_unique_address]]
    ├── 11_using_enum.cpp        # using enum
    ├── 12_std_format.cpp        # std::format
    ├── 13_std_span.cpp          # std::span
    ├── 14_std_jthread.cpp       # std::jthread
    ├── 15_synchronization.cpp   # 同步原语
    ├── 16_std_source_location.cpp # source_location
    ├── 17_std_stop_token.cpp    # stop_token
    └── 18_comprehensive.cpp     # 综合示例
```

---

## 关键要点速查

### Concepts
```cpp
template <std::integral T>           // 标准库概念
template <typename T> concept Addable = requires(T a, T b) { a + b; };  // 自定义
auto func(Concept auto param);       // 约束简写
```

### Ranges
```cpp
auto result = data | std::views::filter(...) | std::views::transform(...);
std::ranges::sort(container, {}, &Type::member);  // 投影排序
```

### Coroutines
```cpp
co_yield value;    // 产出值
co_await expr;     // 等待
co_return value;   // 返回
```

### Spaceship <=>
```cpp
auto operator<=>(const Type&) const = default;  // 自动生成所有比较
std::strong_ordering / weak_ordering / partial_ordering
```

### std::format
```cpp
std::format("{:<10} {:>6.2f}", name, value);  // 对齐、宽度、精度
```

---

## 编译器支持

| 特性 | GCC | Clang | MSVC |
|------|-----|-------|------|
| Concepts | 10+ | 10+ | 19.28+ |
| Ranges | 10+ | 16+ | 19.29+ |
| Coroutines | 10+ | 10+ | 19.28+ |
| Modules | 11+ | 16+ | 19.28+ |
| format | 13+ | 17+ | 19.29+ |
| jthread | 10+ | 13+ | 19.28+ |
| source_location | 11+ | 16+ | 19.29+ |

---

## 相关链接

- [返回系统模块](../SYSTEM_README.md)
- [C++20 标准](https://en.cppreference.com/w/cpp/20)
- [C++20 Compiler Support](https://en.cppreference.com/w/cpp/compiler_support/20)
