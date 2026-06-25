# C++ 性能优化技巧 - 技术设计

## 1. 项目结构

```
cpp-performance-optimization/
├── CMakeLists.txt              # 主构建文件
├── README.md                   # 项目说明
├── 01_RESEARCH.md              # 调研报告
├── 02_REQUIREMENTS.md          # 需求分析
├── 03_DESIGN.md                # 技术设计
├── 04_PRODUCT.md               # 产品思考
├── 05_DEVELOPMENT.md           # 开发手册
├── include/                    # 公共头文件
│   ├── benchmark.hpp           # 基准测试框架
│   ├── timer.hpp               # 计时工具
│   └── utils.hpp               # 工具函数
├── src/
│   ├── memory/                 # 内存优化
│   │   ├── CMakeLists.txt
│   │   ├── cache_friendly.cpp
│   │   ├── soa_vs_aos.cpp
│   │   ├── memory_alignment.cpp
│   │   ├── prefetching.cpp
│   │   ├── memory_pool.cpp
│   │   └── small_buffer_optimization.cpp
│   ├── compiler/               # 编译器优化
│   │   ├── CMakeLists.txt
│   │   ├── inlining.cpp
│   │   ├── loop_unrolling.cpp
│   │   ├── vectorization.cpp
│   │   ├── branch_prediction.cpp
│   │   └── lto_demo.cpp
│   ├── algorithm/              # 算法优化
│   │   ├── CMakeLists.txt
│   │   ├── time_complexity.cpp
│   │   ├── space_complexity.cpp
│   │   ├── constant_factor.cpp
│   │   ├── parallelization.cpp
│   │   └── simd_optimization.cpp
│   ├── data_structure/         # 数据结构优化
│   │   ├── CMakeLists.txt
│   │   ├── compact_structures.cpp
│   │   ├── lock_free.cpp
│   │   ├── concurrent_structures.cpp
│   │   └── cache_friendly_container.cpp
│   ├── io/                     # I/O 优化
│   │   ├── CMakeLists.txt
│   │   ├── buffered_io.cpp
│   │   ├── async_io.cpp
│   │   ├── mmap_demo.cpp
│   │   └── batch_operations.cpp
│   ├── concurrency/            # 并发优化
│   │   ├── CMakeLists.txt
│   │   ├── thread_pool.cpp
│   │   ├── task_scheduler.cpp
│   │   ├── lock_free_programming.cpp
│   │   ├── atomic_optimization.cpp
│   │   └── false_sharing.cpp
│   ├── tools/                  # 工具和测量
│   │   ├── CMakeLists.txt
│   │   ├── benchmark_framework.cpp
│   │   ├── perf_counters.cpp
│   │   └── micro_benchmark.cpp
│   └── case_studies/           # 实际案例
│       ├── CMakeLists.txt
│       ├── vector_operations.cpp
│       ├── matrix_multiplication.cpp
│       ├── string_processing.cpp
│       ├── hash_table.cpp
│       └── sorting_optimization.cpp
└── scripts/                    # 辅助脚本
    ├── run_benchmarks.sh
    └── generate_report.sh
```

## 2. 代码规范

### 2.1 文件命名
- 源文件: `snake_case.cpp`
- 头文件: `snake_case.hpp`
- CMake 文件: `CMakeLists.txt`

### 2.2 代码风格
- 使用 4 空格缩进
- 花括号换行 (Allman 风格)
- 类名: PascalCase
- 函数名: camelCase 或 snake_case
- 常量: UPPER_SNAKE_CASE
- 命名空间: lowercase

### 2.3 注释规范
- 文件头注释说明文件用途
- 类和函数使用 Doxygen 风格注释
- 关键代码行内注释
- 复杂算法添加详细说明

### 2.4 示例代码模板
```cpp
/**
 * @file example.cpp
 * @brief 示例文件说明
 * 
 * 详细说明这个文件展示的优化技术
 */

#include <iostream>
#include <chrono>
#include <vector>
#include <algorithm>

// 工具函数和类定义

/**
 * @brief 未优化版本
 * 
 * 说明为什么这个版本性能较差
 */
void unoptimizedVersion()
{
    // 实现
}

/**
 * @brief 优化版本
 * 
 * 说明使用了什么优化技术
 */
void optimizedVersion()
{
    // 实现
}

/**
 * @brief 基准测试
 */
void benchmark()
{
    constexpr int ITERATIONS = 1000;
    
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < ITERATIONS; ++i) {
        unoptimizedVersion();
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto unopt_time = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
    
    start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < ITERATIONS; ++i) {
        optimizedVersion();
    }
    end = std::chrono::high_resolution_clock::now();
    auto opt_time = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
    
    std::cout << "未优化: " << unopt_time.count() << " ns\n";
    std::cout << "优化后: " << opt_time.count() << " ns\n";
    std::cout << "加速比: " << static_cast<double>(unopt_time.count()) / opt_time.count() << "x\n";
}

int main()
{
    std::cout << "=== 示例名称 ===\n\n";
    
    std::cout << "--- 功能演示 ---\n";
    // 功能演示代码
    
    std::cout << "\n--- 性能对比 ---\n";
    benchmark();
    
    return 0;
}
```

## 3. 模块设计

### 3.1 内存优化模块设计

#### 缓存友好设计
```cpp
// 核心演示内容:
// 1. 行优先 vs 列优先遍历
// 2. 数据局部性优化
// 3. 缓存行大小影响
// 4. 预取技术

// 关键数据结构:
struct CacheFriendlyData {
    std::vector<int> data;
    size_t rows, cols;
    
    // 行优先访问 (缓存友好)
    int& at(size_t r, size_t c) { return data[r * cols + c]; }
    
    // 列优先访问 (缓存不友好)
    int& at_col_major(size_t r, size_t c) { return data[c * rows + r]; }
};
```

#### SoA vs AoS
```cpp
// AoS - Array of Structures
struct ParticleAoS {
    float x, y, z;      // 位置
    float vx, vy, vz;   // 速度
    float r, g, b, a;   // 颜色
};
std::vector<ParticleAoS> particles_aos;

// SoA - Structure of Arrays
struct ParticlesSoA {
    std::vector<float> x, y, z;
    std::vector<float> vx, vy, vz;
    std::vector<float> r, g, b, a;
};
```

### 3.2 编译器优化模块设计

#### 向量化示例
```cpp
// 需要展示:
// 1. 自动向量化条件
// 2. 手动 SIMD 内置函数
// 3. 对齐要求
// 4. 向量化友好的代码模式

// 自动向量化友好的代码
void vectorizeFriendly(float* a, float* b, float* c, size_t n)
{
    // 编译器可以自动向量化这个循环
    for (size_t i = 0; i < n; ++i) {
        c[i] = a[i] + b[i];
    }
}

// 手动 SIMD 优化 (SSE)
#include <immintrin.h>
void vectorAddSSE(float* a, float* b, float* c, size_t n)
{
    for (size_t i = 0; i < n; i += 4) {
        __m128 va = _mm_load_ps(&a[i]);
        __m128 vb = _mm_load_ps(&b[i]);
        __m128 vc = _mm_add_ps(va, vb);
        _mm_store_ps(&c[i], vc);
    }
}
```

### 3.3 算法优化模块设计

#### SIMD 优化示例
```cpp
// 向量点积计算
// 1. 朴素实现
// 2. 循环展开
// 3. SIMD 实现
// 4. 并行 SIMD

float dotProductNaive(const float* a, const float* b, size_t n)
{
    float sum = 0.0f;
    for (size_t i = 0; i < n; ++i) {
        sum += a[i] * b[i];
    }
    return sum;
}

float dotProductSIMD(const float* a, const float* b, size_t n)
{
    __m128 sum = _mm_setzero_ps();
    for (size_t i = 0; i < n; i += 4) {
        __m128 va = _mm_load_ps(&a[i]);
        __m128 vb = _mm_load_ps(&b[i]);
        sum = _mm_add_ps(sum, _mm_mul_ps(va, vb));
    }
    // 水平求和
    sum = _mm_hadd_ps(sum, sum);
    sum = _mm_hadd_ps(sum, sum);
    return _mm_cvtss_f32(sum);
}
```

### 3.4 并发优化模块设计

#### 线程池设计
```cpp
class ThreadPool {
public:
    ThreadPool(size_t numThreads);
    ~ThreadPool();
    
    template<typename F, typename... Args>
    auto enqueue(F&& f, Args&&... args) 
        -> std::future<typename std::result_of<F(Args...)>::type>;
    
private:
    std::vector<std::thread> workers;
    std::queue<std::function<void()>> tasks;
    std::mutex queue_mutex;
    std::condition_variable condition;
    bool stop;
};

// 使用示例
ThreadPool pool(4);
auto result = pool.enqueue([](int a, int b) { return a + b; }, 1, 2);
```

### 3.5 I/O 优化模块设计

#### 内存映射文件
```cpp
class MemoryMappedFile {
public:
    MemoryMappedFile(const std::string& filename);
    ~MemoryMappedFile();
    
    const char* data() const;
    size_t size() const;
    
private:
    int fd;
    void* mapped;
    size_t file_size;
};

// 使用示例
MemoryMappedFile file("large_data.bin");
const char* data = file.data();
// 直接访问文件内容，无需 read/write
```

## 4. 基准测试设计

### 4.1 基准测试框架
```cpp
class Benchmark {
public:
    struct Result {
        double mean_ns;
        double median_ns;
        double stddev_ns;
        size_t iterations;
    };
    
    template<typename F>
    Result run(const std::string& name, F&& func, size_t iterations = 1000);
    
    static void compare(const std::string& name, 
                       const Result& baseline, 
                       const Result& optimized);
};

// 使用示例
Benchmark bench;
auto result1 = bench.run("Naive", [](){ naiveVersion(); });
auto result2 = bench.run("Optimized", [](){ optimizedVersion(); });
Benchmark::compare("Vectorization", result1, result2);
```

### 4.2 计时工具
```cpp
class Timer {
public:
    Timer() : start(std::chrono::high_resolution_clock::now()) {}
    
    ~Timer() {
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
        std::cout << "Elapsed: " << duration.count() << " ns\n";
    }
    
private:
    std::chrono::high_resolution_clock::time_point start;
};

// RAII 风格使用
{
    Timer t;
    // 要计时的代码
}
```

## 5. 构建系统设计

### 5.1 主 CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.14)
project(cpp-performance-optimization LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 优化选项
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O3 -march=native)
endif()

# LTO 选项
option(ENABLE_LTO "Enable Link-Time Optimization" OFF)
if(ENABLE_LTO)
    set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
endif()

# 子目录
add_subdirectory(src/memory)
add_subdirectory(src/compiler)
add_subdirectory(src/algorithm)
add_subdirectory(src/data_structure)
add_subdirectory(src/io)
add_subdirectory(src/concurrency)
add_subdirectory(src/tools)
add_subdirectory(src/case_studies)
```

### 5.2 模块 CMakeLists.txt 示例
```cmake
# src/memory/CMakeLists.txt

add_executable(cache_friendly cache_friendly.cpp)
target_include_directories(cache_friendly PRIVATE ${PROJECT_SOURCE_DIR}/include)

add_executable(soa_vs_aos soa_vs_aos.cpp)
target_include_directories(soa_vs_aos PRIVATE ${PROJECT_SOURCE_DIR}/include)

# ... 其他目标
```

## 6. 测试策略

### 6.1 单元测试
- 每个优化示例可独立运行
- 验证优化后结果正确性
- 检查内存泄漏

### 6.2 性能测试
- 多次运行取平均值
- 记录标准差
- 对比优化前后性能
- 生成性能报告

### 6.3 集成测试
- 构建所有示例
- 运行所有基准测试
- 验证跨平台兼容性

## 7. 文档设计

### 7.1 代码内文档
- 文件头注释
- 类和函数文档
- 关键算法说明
- 优化技巧解释

### 7.2 外部文档
- README.md: 项目概述
- 调研报告: 背景知识
- 需求分析: 功能规格
- 技术设计: 实现细节
- 开发手册: 使用说明

## 8. 扩展设计

### 8.1 添加新优化示例
1. 在对应目录创建 .cpp 文件
2. 遵循代码模板
3. 更新 CMakeLists.txt
4. 添加文档说明

### 8.2 添加新优化类别
1. 创建新的 src 子目录
2. 添加 CMakeLists.txt
3. 更新主 CMakeLists.txt
4. 更新 README.md