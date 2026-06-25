# 03 设计文档: C++ 性能优化项目

## 1. 系统架构

### 1.1 整体架构

```
cpp-performance-optimization/
├── CMakeLists.txt                   # 顶层构建配置
├── cmake/                           # CMake 模块
│   ├── CompilerOptions.cmake        # 编译器选项
│   ├── Sanitizers.cmake             # Sanitizer 配置
│   └── Benchmark.cmake              # 基准测试配置
├── include/
│   └── cpp_perf/                    # 公共头文件
│       ├── common/                  # 通用工具
│       │   ├── timer.h              # 计时器
│       │   ├── benchmark.h          # 基准测试框架
│       │   └── stats.h              # 统计分析
│       ├── memory/                  # 内存优化
│       │   ├── memory_pool.h        # 内存池
│       │   ├── allocator.h          # 自定义分配器
│       │   └── cache_utils.h        # 缓存工具
│       ├── compiler/                # 编译器优化
│       │   ├── inline_utils.h       # 内联工具
│       │   ├── simd_utils.h         # SIMD 工具
│       │   └── branch_utils.h       # 分支优化工具
│       ├── algorithm/               # 算法优化
│       │   ├── sort.h               # 排序算法
│       │   ├── search.h             # 搜索算法
│       │   └── parallel.h           # 并行算法
│       ├── data_structure/          # 数据结构
│       │   ├── flat_map.h           # 扁平化容器
│       │   ├── ring_buffer.h        # 环形缓冲区
│       │   └── lock_free.h          # 无锁结构
│       ├── io/                      # I/O 优化
│       │   ├── buffered_io.h        # 缓冲 I/O
│       │   ├── async_io.h           # 异步 I/O
│       │   └── mmap_io.h            # 内存映射 I/O
│       ├── concurrency/             # 并发优化
│       │   ├── thread_pool.h        # 线程池
│       │   ├── lock_free_queue.h    # 无锁队列
│       │   └── concurrent_map.h     # 并发容器
│       └── tools/                   # 性能工具
│           ├── perf_counter.h       # 性能计数器
│           └── memory_tracker.h     # 内存跟踪
├── src/                             # 实现源码
│   ├── memory/
│   │   ├── cache_friendly.cpp       # 缓存友好示例
│   │   ├── memory_pool.cpp          # 内存池实现
│   │   ├── move_semantics.cpp       # 移动语义示例
│   │   ├── sso_string.cpp           # SSO 字符串
│   │   └── custom_allocator.cpp     # 自定义分配器
│   ├── compiler/
│   │   ├── optimization_levels.cpp  # 优化级别对比
│   │   ├── inlining.cpp            # 内联优化
│   │   ├── vectorization.cpp        # 向量化
│   │   ├── branch_prediction.cpp    # 分支预测
│   │   └── lto_example.cpp          # LTO 示例
│   ├── algorithm/
│   │   ├── complexity.cpp           # 复杂度对比
│   │   ├── space_time_tradeoff.cpp  # 空间换时间
│   │   ├── parallel_algorithm.cpp   # 并行算法
│   │   └── lazy_evaluation.cpp      # 延迟计算
│   ├── data_structure/
│   │   ├── struct_layout.cpp        # 结构体布局
│   │   ├── flat_containers.cpp      # 扁平容器
│   │   ├── lock_free_structures.cpp # 无锁结构
│   │   └── cache_friendly_ds.cpp    # 缓存友好结构
│   ├── io/
│   │   ├── buffered_io.cpp          # 缓冲 I/O
│   │   ├── async_io.cpp             # 异步 I/O
│   │   ├── memory_mapping.cpp       # 内存映射
│   │   └── zero_copy.cpp            # 零拷贝
│   ├── concurrency/
│   │   ├── thread_pool.cpp          # 线程池
│   │   ├── lock_free.cpp            # 无锁编程
│   │   ├── false_sharing.cpp        # 伪共享
│   │   └── concurrency_patterns.cpp # 并发模式
│   ├── tools/
│   │   ├── benchmark_framework.cpp  # 基准测试框架
│   │   ├── perf_counters.cpp        # 性能计数器
│   │   └── memory_analysis.cpp      # 内存分析
│   └── case_studies/
│       ├── matrix_multiply.cpp      # 矩阵乘法
│       ├── string_processing.cpp    # 字符串处理
│       ├── hash_table.cpp           # 哈希表
│       ├── sorting.cpp              # 排序优化
│       └── json_parser.cpp          # JSON 解析器
├── tests/                           # 单元测试
│   ├── test_memory.cpp
│   ├── test_compiler.cpp
│   ├── test_algorithm.cpp
│   ├── test_data_structure.cpp
│   ├── test_io.cpp
│   ├── test_concurrency.cpp
│   └── test_tools.cpp
└── benchmarks/                      # 性能基准测试
    ├── bench_memory.cpp
    ├── bench_compiler.cpp
    ├── bench_algorithm.cpp
    ├── bench_data_structure.cpp
    ├── bench_io.cpp
    ├── bench_concurrency.cpp
    └── bench_case_studies.cpp
```

### 1.2 模块依赖关系

```
                    ┌─────────────┐
                    │   common    │
                    │  (timer,    │
                    │  benchmark, │
                    │  stats)     │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    memory     │ │   compiler    │ │   algorithm   │
│  (pool,       │ │  (inline,     │ │  (sort,       │
│   allocator,  │ │   simd,       │ │   search,     │
│   cache)      │ │   branch)     │ │   parallel)   │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ data_structure│ │      io       │ │  concurrency  │
│  (flat,       │ │  (buffered,   │ │  (thread_pool,│
│   lock_free,  │ │   async,      │ │   lock_free,  │
│   cache)      │ │   mmap)       │ │   patterns)   │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │    tools    │
                    │  (perf,     │
                    │   memory)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ case_studies│
                    │  (matrix,   │
                    │   string,   │
                    │   hash,     │
                    │   sort,     │
                    │   json)     │
                    └─────────────┘
```

## 2. 文件组织规范

### 2.1 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | snake_case | `memory_pool.h`, `thread_pool.cpp` |
| 类名 | PascalCase | `MemoryPool`, `ThreadPool` |
| 函数名 | snake_case | `allocate()`, `deallocate()` |
| 变量名 | snake_case | `buffer_size`, `thread_count` |
| 常量 | kPascalCase | `kMaxBufferSize`, `kDefaultThreadCount` |
| 宏 | UPPER_SNAKE_CASE | `ENABLE_SIMD`, `CACHE_LINE_SIZE` |
| 命名空间 | snake_case | `cpp_perf::memory`, `cpp_perf::algorithm` |
| 模板参数 | PascalCase | `typename ValueType`, `typename Allocator` |

### 2.2 文件头模板

```cpp
/**
 * @file memory_pool.h
 * @brief 内存池实现
 *
 * 实现固定大小和可变大小的内存池，减少频繁的堆内存分配开销。
 *
 * @author [作者名]
 * @date [日期]
 * @version 1.0
 *
 * @note 本文件是 C++ 性能优化项目的一部分
 */

#ifndef CPP_PERF_MEMORY_MEMORY_POOL_H
#define CPP_PERF_MEMORY_MEMORY_POOL_H

// ... 文件内容 ...

#endif  // CPP_PERF_MEMORY_MEMORY_POOL_H
```

### 2.3 类设计模板

```cpp
namespace cpp_perf {
namespace memory {

/**
 * @brief 固定大小内存池
 *
 * @tparam T 对象类型
 * @tparam PoolSize 池中对象数量
 *
 * 使用示例:
 * @code
 * MemoryPool<MyObject, 1024> pool;
 * auto* obj = pool.allocate();
 * // 使用 obj...
 * pool.deallocate(obj);
 * @endcode
 */
template <typename T, size_t PoolSize>
class MemoryPool {
 public:
    // 类型定义
    using value_type = T;
    using pointer = T*;
    using const_pointer = const T*;
    using size_type = size_t;

    // 构造和析构
    MemoryPool();
    ~MemoryPool();

    // 禁止拷贝
    MemoryPool(const MemoryPool&) = delete;
    MemoryPool& operator=(const MemoryPool&) = delete;

    // 允许移动
    MemoryPool(MemoryPool&& other) noexcept;
    MemoryPool& operator=(MemoryPool&& other) noexcept;

    // 核心接口
    pointer allocate();
    void deallocate(pointer p);
    size_type available() const;
    size_type capacity() const;
    bool owns(pointer p) const;

 private:
    // 内部实现
    struct Block {
        alignas(T) char data[sizeof(T)];
        Block* next;
    };

    Block blocks_[PoolSize];
    Block* free_list_;
    size_type available_;
};

}  // namespace memory
}  // namespace cpp_perf
```

## 3. 设计模式

### 3.1 RAII 模式

用于资源管理，确保资源在作用域结束时自动释放:

```cpp
class ScopedTimer {
 public:
    explicit ScopedTimer(const std::string& name)
        : name_(name), start_(std::chrono::high_resolution_clock::now()) {}

    ~ScopedTimer() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start_);
        std::cout << name_ << ": " << duration.count() << " ns" << std::endl;
    }

 private:
    std::string name_;
    std::chrono::high_resolution_clock::time_point start_;
};

// 使用
void benchmark_function() {
    ScopedTimer timer("benchmark_function");
    // 函数体...
}  // 自动打印耗时
```

### 3.2 策略模式

用于可配置的优化策略:

```cpp
// 内存分配策略
struct MallocPolicy {
    static void* allocate(size_t size) { return std::malloc(size); }
    static void deallocate(void* ptr) { std::free(ptr); }
};

struct PoolPolicy {
    static void* allocate(size_t size) { return pool.allocate(size); }
    static void deallocate(void* ptr) { pool.deallocate(ptr); }
};

// 使用策略的容器
template <typename T, typename AllocPolicy = MallocPolicy>
class Vector {
    // ...
};
```

### 3.3 CRTP 模式

用于静态多态，避免虚函数开销:

```cpp
template <typename Derived>
class OptimizedContainer {
 public:
    void push_back(const T& value) {
        static_cast<Derived*>(this)->push_back_impl(value);
    }

    size_t size() const {
        return static_cast<const Derived*>(this)->size_impl();
    }
};

class FastVector : public OptimizedContainer<FastVector, int> {
 public:
    void push_back_impl(const int& value) {
        // 具体实现
    }

    size_t size_impl() const {
        return size_;
    }
};
```

### 3.4 模板策略模式

用于编译期配置:

```cpp
template <size_t BlockSize = 4096, size_t Alignment = 64>
class AlignedAllocator {
    static_assert(BlockSize % Alignment == 0, "BlockSize must be multiple of Alignment");
    // ...
};
```

### 3.5 类型擦除模式

用于运行时多态的同时保持值语义:

```cpp
class AnyCallable {
    struct Concept {
        virtual ~Concept() = default;
        virtual void invoke() = 0;
    };

    template <typename F>
    struct Model : Concept {
        F func;
        explicit Model(F f) : func(std::move(f)) {}
        void invoke() override { func(); }
    };

    std::unique_ptr<Concept> impl_;

 public:
    template <typename F>
    AnyCallable(F f) : impl_(std::make_unique<Model<F>>(std::move(f))) {}

    void operator()() { impl_->invoke(); }
};
```

## 4. 代码风格指南

### 4.1 格式规范

- **缩进**: 2 个空格 (不使用 Tab)
- **行宽**: 80 字符 (最大 100 字符)
- **花括号**: 放在行尾 (函数、类、控制结构)
- **空格**: 操作符前后加空格，逗号后加空格
- **空行**: 函数之间空一行，逻辑块之间空一行

### 4.2 头文件规范

- 使用 `#ifndef`/`#define`/`#endif` 头文件保护
- 包含顺序: 对应头文件、C 库、C++ 库、其他库、项目头文件
- 前向声明优先于 `#include`
- 头文件自包含 (可以独立编译)

### 4.3 类设计规范

- 成员变量使用 `snake_case_` 后缀
- 构造函数初始化列表顺序与声明顺序一致
- 虚函数使用 `override` 关键字
- 禁止在构造函数和析构函数中调用虚函数

### 4.4 函数设计规范

- 函数长度不超过 50 行
- 参数不超过 4 个
- 返回值优先使用返回值而非输出参数
- 使用 `const` 修饰不修改的参数和成员函数

### 4.5 注释规范

- 文件头注释: 描述文件用途和版权
- 类注释: 描述类的用途和使用方法
- 函数注释: 描述函数的功能、参数、返回值
- 复杂逻辑注释: 解释为什么这样做

### 4.6 性能相关规范

- 热路径函数标记 `__attribute__((always_inline))` 或 `__forceinline`
- 数据对齐使用 `alignas`
- 缓存行大小使用常量 `kCacheLineSize`
- 分支提示使用 `[[likely]]`/`[[unlikely]]`

## 5. 测试框架设计

### 5.1 测试结构

```
tests/
├── test_main.cpp              # 测试入口
├── test_memory.cpp            # 内存优化测试
├── test_compiler.cpp          # 编译器优化测试
├── test_algorithm.cpp         # 算法优化测试
├── test_data_structure.cpp    # 数据结构测试
├── test_io.cpp                # I/O 优化测试
├── test_concurrency.cpp       # 并发优化测试
├── test_tools.cpp             # 工具测试
└── test_case_studies.cpp      # 案例研究测试
```

### 5.2 测试宏

```cpp
// 断言宏
#define PERF_ASSERT(cond) \
    do { \
        if (!(cond)) { \
            std::cerr << "Assertion failed: " << #cond \
                      << " at " << __FILE__ << ":" << __LINE__ << std::endl; \
            std::abort(); \
        } \
    } while (0)

#define PERF_ASSERT_EQ(a, b) PERF_ASSERT((a) == (b))
#define PERF_ASSERT_NE(a, b) PERF_ASSERT((a) != (b))
#define PERF_ASSERT_GT(a, b) PERF_ASSERT((a) > (b))
#define PERF_ASSERT_LT(a, b) PERF_ASSERT((a) < (b))

// 性能断言宏
#define PERF_ASSERT_FASTER_THAN(ns, threshold) \
    do { \
        if ((ns) > (threshold)) { \
            std::cerr << "Performance assertion failed: " << (ns) << " ns > " \
                      << (threshold) << " ns" << std::endl; \
        } \
    } while (0)
```

### 5.3 测试用例模板

```cpp
/**
 * @brief 测试内存池分配和释放
 *
 * 验证内存池的基本功能:
 * 1. 能够正确分配内存
 * 2. 能够正确释放内存
 * 3. 分配的内存对齐正确
 * 4. 池满时返回 nullptr
 */
void test_memory_pool_allocate_deallocate() {
    MemoryPool<int, 10> pool;

    // 测试分配
    int* p1 = pool.allocate();
    PERF_ASSERT(p1 != nullptr);
    PERF_ASSERT(pool.available() == 9);

    // 测试使用
    *p1 = 42;
    PERF_ASSERT_EQ(*p1, 42);

    // 测试释放
    pool.deallocate(p1);
    PERF_ASSERT(pool.available() == 10);

    // 测试对齐
    PERF_ASSERT_EQ(reinterpret_cast<uintptr_t>(p1) % alignof(int), 0);
}
```

### 5.4 基准测试模板

```cpp
/**
 * @brief 基准测试: 内存池 vs malloc
 *
 * 测试场景: 频繁分配释放小对象
 * 预期结果: 内存池比 malloc 快 5 倍以上
 */
void benchmark_memory_pool_vs_malloc() {
    constexpr size_t kIterations = 1000000;
    constexpr size_t kObjectSize = 64;

    // 测试 malloc
    auto malloc_time = measure_time([&]() {
        for (size_t i = 0; i < kIterations; ++i) {
            void* p = std::malloc(kObjectSize);
            std::free(p);
        }
    });

    // 测试内存池
    MemoryPool<kObjectSize, kIterations> pool;
    auto pool_time = measure_time([&]() {
        for (size_t i = 0; i < kIterations; ++i) {
            void* p = pool.allocate();
            pool.deallocate(p);
        }
    });

    // 输出结果
    std::cout << "malloc: " << malloc_time << " ns" << std::endl;
    std::cout << "pool:   " << pool_time << " ns" << std::endl;
    std::cout << "speedup: " << (double)malloc_time / pool_time << "x" << std::endl;

    // 验证性能
    PERF_ASSERT_FASTER_THAN(pool_time, malloc_time / 5);
}
```

### 5.5 测试运行配置

```cmake
# CMake 测试配置
enable_testing()

# 添加测试
add_test(NAME test_memory COMMAND test_memory)
add_test(NAME test_compiler COMMAND test_compiler)
add_test(NAME test_algorithm COMMAND test_algorithm)
add_test(NAME test_data_structure COMMAND test_data_structure)
add_test(NAME test_io COMMAND test_io)
add_test(NAME test_concurrency COMMAND test_concurrency)
add_test(NAME test_tools COMMAND test_tools)

# 基准测试
add_custom_target(benchmarks
    COMMAND bench_memory
    COMMAND bench_compiler
    COMMAND bench_algorithm
    COMMAND bench_data_structure
    COMMAND bench_io
    COMMAND bench_concurrency
    COMMAND bench_case_studies
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)
```

## 6. 构建系统设计

### 6.1 CMake 结构

```
CMakeLists.txt                     # 顶层配置
├── cmake/
│   ├── CompilerOptions.cmake      # 编译器选项
│   ├── Sanitizers.cmake           # Sanitizer 配置
│   └── Benchmark.cmake            # 基准测试配置
├── include/CMakeLists.txt         # 头文件安装
├── src/CMakeLists.txt             # 源码构建
├── tests/CMakeLists.txt           # 测试构建
└── benchmarks/CMakeLists.txt      # 基准测试构建
```

### 6.2 编译选项配置

```cmake
# cmake/CompilerOptions.cmake
function(set_cpp_perf_options target)
    target_compile_features(${target} PUBLIC cxx_std_17)

    # 通用警告选项
    target_compile_options(${target} PRIVATE
        -Wall -Wextra -Wpedantic -Werror
    )

    # 优化选项
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        target_compile_options(${target} PRIVATE -O3 -march=native)
    elseif(CMAKE_BUILD_TYPE STREQUAL "Debug")
        target_compile_options(${target} PRIVATE -O0 -g)
    elseif(CMAKE_BUILD_TYPE STREQUAL "RelWithDebInfo")
        target_compile_options(${target} PRIVATE -O2 -g)
    endif()

    # LTO 支持
    if(ENABLE_LTO)
        set_property(TARGET ${target} PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
    endif()
endfunction()
```

### 6.3 Sanitizer 配置

```cmake
# cmake/Sanitizers.cmake
function(enable_sanitizers target)
    if(ENABLE_SANITIZERS)
        if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
            target_compile_options(${target} PRIVATE
                -fsanitize=address,undefined
                -fno-omit-frame-pointer
            )
            target_link_options(${target} PRIVATE
                -fsanitize=address,undefined
            )
        elseif(MSVC)
            target_compile_options(${target} PRIVATE /fsanitize=address)
        endif()
    endif()
endfunction()
```

## 7. 错误处理设计

### 7.1 错误类型

```cpp
namespace cpp_perf {

enum class ErrorCode {
    kSuccess = 0,
    kOutOfMemory,          // 内存分配失败
    kInvalidArgument,      // 无效参数
    kBufferOverflow,       // 缓冲区溢出
    kThreadCreationFailed, // 线程创建失败
    kIoError,              // I/O 错误
};

class Error {
 public:
    Error() : code_(ErrorCode::kSuccess) {}
    explicit Error(ErrorCode code, std::string message = "")
        : code_(code), message_(std::move(message)) {}

    bool ok() const { return code_ == ErrorCode::kSuccess; }
    ErrorCode code() const { return code_; }
    const std::string& message() const { return message_; }

 private:
    ErrorCode code_;
    std::string message_;
};

}  // namespace cpp_perf
```

### 7.2 错误处理策略

| 场景 | 策略 | 示例 |
|------|------|------|
| 内存分配失败 | 返回 nullptr 或抛出异常 | `allocate()` |
| 参数无效 | 断言或返回错误码 | `set_size(-1)` |
| 缓冲区溢出 | 断言或边界检查 | `buffer[100]` |
| 线程创建失败 | 返回错误码 | `create_thread()` |
| I/O 错误 | 返回错误码 | `read_file()` |

## 8. 性能监控设计

### 8.1 计时器设计

```cpp
class Timer {
 public:
    void start() {
        start_ = std::chrono::high_resolution_clock::now();
    }

    void stop() {
        end_ = std::chrono::high_resolution_clock::now();
    }

    template <typename Duration = std::chrono::nanoseconds>
    int64_t elapsed() const {
        return std::chrono::duration_cast<Duration>(end_ - start_).count();
    }

 private:
    std::chrono::high_resolution_clock::time_point start_;
    std::chrono::high_resolution_clock::time_point end_;
};
```

### 8.2 统计分析设计

```cpp
class Statistics {
 public:
    void add(double value) {
        values_.push_back(value);
        sum_ += value;
        sum_sq_ += value * value;
        ++count_;
    }

    double mean() const { return sum_ / count_; }

    double stddev() const {
        double m = mean();
        return std::sqrt(sum_sq_ / count_ - m * m);
    }

    double median() const {
        auto sorted = values_;
        std::sort(sorted.begin(), sorted.end());
        return sorted[sorted.size() / 2];
    }

    double min() const {
        return *std::min_element(values_.begin(), values_.end());
    }

    double max() const {
        return *std::max_element(values_.begin(), values_.end());
    }

 private:
    std::vector<double> values_;
    double sum_ = 0;
    double sum_sq_ = 0;
    size_t count_ = 0;
};
```

---

[返回项目主页](../README.md) | [上一篇: 需求文档](./02_REQUIREMENTS.md) | [下一篇: 产品思维文档](./04_PRODUCT.md)
