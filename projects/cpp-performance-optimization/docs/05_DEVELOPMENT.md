# 05 开发文档: C++ 性能优化项目

## 1. 开发环境搭建

### 1.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 20.04 / macOS 11 / Windows 10 | Ubuntu 22.04 / macOS 13 / Windows 11 |
| 编译器 | GCC 9 / Clang 10 / MSVC 2019 | GCC 13 / Clang 17 / MSVC 2022 |
| CMake | 3.14 | 3.25+ |
| 内存 | 4GB | 16GB+ |
| 磁盘空间 | 1GB | 5GB+ |

### 1.2 依赖安装

**Ubuntu/Debian**:

```bash
# 基础工具
sudo apt update
sudo apt install -y build-essential cmake git

# 编译器 (如果需要更新版本)
sudo apt install -y gcc-13 g++-13
sudo apt install -y clang-17

# 性能工具
sudo apt install -y linux-tools-common linux-tools-generic
sudo apt install -y valgrind

# 可选: Google Benchmark
sudo apt install -y libbenchmark-dev
```

**macOS**:

```bash
# 安装 Xcode 命令行工具
xcode-select --install

# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install cmake
brew install llvm  # 最新 Clang
brew install google-benchmark
```

**Windows**:

```powershell
# 安装 Visual Studio 2019/2022 (含 C++ 工具链)
# 下载地址: https://visualstudio.microsoft.com/

# 安装 CMake
# 下载地址: https://cmake.org/download/

# 安装 Git
# 下载地址: https://git-scm.com/download/win

# 或者使用 vcpkg 安装依赖
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg install benchmark
```

### 1.3 IDE 配置

**VS Code**:

```json
// .vscode/settings.json
{
    "cmake.configureOnOpen": true,
    "cmake.buildDirectory": "${workspaceFolder}/build",
    "cmake.generator": "Ninja",
    "C_Cpp.default.configurationProvider": "ms-vscode.cmake-tools",
    "C_Cpp.default.cppStandard": "c++17",
    "files.associations": {
        "*.h": "cpp",
        "*.cpp": "cpp",
        "*.cmake": "cmake",
        "CMakeLists.txt": "cmake"
    }
}
```

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Current Test",
            "type": "cppdbg",
            "request": "launch",
            "program": "${workspaceFolder}/build/tests/${fileBasenameNoExtension}",
            "args": [],
            "stopAtEntry": false,
            "cwd": "${workspaceFolder}",
            "environment": [],
            "externalConsole": false,
            "MIMode": "gdb",
            "setupCommands": [
                {
                    "description": "Enable pretty-printing for gdb",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": true
                }
            ]
        }
    ]
}
```

**CLion**:

1. 打开项目目录
2. CLion 自动检测 CMakeLists.txt
3. 配置 CMake Profile: Release/Debug
4. 配置工具链: GCC/Clang

## 2. 构建系统

### 2.1 CMake 构建

**基本构建流程**:

```bash
# 克隆项目
cd projects/cpp-performance-optimization

# 创建构建目录 (out-of-source 构建)
mkdir -p build && cd build

# 配置
cmake ..

# 编译
cmake --build . -j$(nproc)

# 或者使用 make
make -j$(nproc)
```

**常用 CMake 选项**:

```bash
# Debug 模式 (禁用优化, 启用调试信息)
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式 (启用优化)
cmake -DCMAKE_BUILD_TYPE=Release ..

# RelWithDebInfo 模式 (优化 + 调试信息)
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..

# 指定编译器
cmake -DCMAKE_CXX_COMPILER=g++-13 ..
cmake -DCMAKE_CXX_COMPILER=clang++-17 ..

# 启用 LTO (链接时优化)
cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_LTO=ON ..

# 启用 Sanitizer
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON ..

# 指定安装路径
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
```

**CMakeLists.txt 结构**:

```cmake
# 顶层 CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(cpp-performance-optimization LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 编译选项
include(cmake/CompilerOptions.cmake)

# Sanitizer 配置
include(cmake/Sanitizers.cmake)

# 子目录
add_subdirectory(src)
add_subdirectory(tests)
add_subdirectory(benchmarks)
```

### 2.2 编译器标志

**GCC/Clang 常用标志**:

| 标志 | 作用 | 适用场景 |
|------|------|----------|
| `-O0` | 禁用优化 | 调试 |
| `-O1` | 基本优化 | 快速编译 |
| `-O2` | 推荐优化 | 一般开发 |
| `-O3` | 激进优化 | 性能测试 |
| `-Os` | 优化大小 | 嵌入式 |
| `-g` | 调试信息 | 调试 |
| `-Wall -Wextra` | 所有警告 | 所有场景 |
| `-Werror` | 警告视为错误 | CI/CD |
| `-march=native` | 针对本机 CPU | 本机优化 |
| `-mavx2` | 启用 AVX2 | SIMD 优化 |
| `-flto` | 链接时优化 | 发布构建 |
| `-fno-omit-frame-pointer` | 保留帧指针 | 性能分析 |
| `-fsanitize=address` | 内存错误检测 | 测试 |
| `-fsanitize=thread` | 线程错误检测 | 测试 |
| `-pg` | 性能分析 | gprof 分析 |

**MSVC 常用标志**:

| 标志 | 作用 | 适用场景 |
|------|------|----------|
| `/Od` | 禁用优化 | 调试 |
| `/O1` | 优化大小 | 发布 |
| `/O2` | 优化速度 | 发布 |
| `/Zi` | 调试信息 | 调试 |
| `/W4` | 警告级别 4 | 所有场景 |
| `/WX` | 警告视为错误 | CI/CD |
| `/arch:AVX2` | 启用 AVX2 | SIMD 优化 |
| `/GL` | 全程序优化 | 发布 |
| `/fsanitize=address` | 内存错误检测 | 测试 |

**自定义 CMake 函数**:

```cmake
# cmake/CompilerOptions.cmake
function(set_cpp_perf_options target)
    # C++ 标准
    target_compile_features(${target} PUBLIC cxx_std_17)

    # 警告选项
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(${target} PRIVATE
            -Wall -Wextra -Wpedantic -Werror
            -Wno-unused-parameter
        )
    elseif(MSVC)
        target_compile_options(${target} PRIVATE /W4 /WX)
    endif()

    # 优化选项
    if(CMAKE_BUILD_TYPE STREQUAL "Release")
        if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
            target_compile_options(${target} PRIVATE -O3 -march=native)
        elseif(MSVC)
            target_compile_options(${target} PRIVATE /O2)
        endif()
    endif()

    # LTO
    if(ENABLE_LTO)
        set_property(TARGET ${target} PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)
    endif()
endfunction()
```

## 3. 运行基准测试

### 3.1 基准测试框架

项目使用自定义基准测试框架，兼容 Google Benchmark 接口:

```cpp
#include "cpp_perf/common/benchmark.h"

// 定义基准测试
void benchmark_memory_pool() {
    constexpr size_t kIterations = 10000;

    MemoryPool<int, 1024> pool;

    // 运行基准测试
    auto result = cpp_perf::run_benchmark("MemoryPool::allocate", kIterations, [&]() {
        auto* p = pool.allocate();
        pool.deallocate(p);
    });

    // 输出结果
    std::cout << result.name << ": "
              << result.mean_ns << " ns/op, "
              << result.ops_per_sec << " ops/sec" << std::endl;
}
```

### 3.2 运行基准测试

```bash
# 运行所有基准测试
cd build
./benchmarks/run_all_benchmarks

# 运行特定类别
./benchmarks/bench_memory
./benchmarks/bench_compiler
./benchmarks/bench_algorithm
./benchmarks/bench_data_structure
./benchmarks/bench_io
./benchmarks/bench_concurrency
./benchmarks/bench_case_studies

# 输出 JSON 格式
./benchmarks/run_all_benchmarks --benchmark_format=json > results.json

# 输出 CSV 格式
./benchmarks/run_all_benchmarks --benchmark_format=csv > results.csv
```

### 3.3 基准测试结果示例

```
---------------------------------------------------------------
Benchmark                     Time(ns)  Iterations  Ops/sec
---------------------------------------------------------------
MemoryPool::allocate             12.5      1000000   80000000
MemoryPool::deallocate            8.3      1000000  120000000
Malloc::allocate                156.2      1000000    6400000
Malloc::deallocate              142.8      1000000    7000000
---------------------------------------------------------------
CacheFriendly::traverse          45.2      1000000   22100000
CacheUnfriendly::traverse       187.5      1000000    5330000
---------------------------------------------------------------
```

### 3.4 基准测试编写指南

1. **使用 Release 模式编译**
   ```bash
   cmake -DCMAKE_BUILD_TYPE=Release ..
   ```

2. **预热运行**
   ```cpp
   // 预热
   for (int i = 0; i < 100; ++i) {
       benchmark_function();
   }
   
   // 正式测量
   auto result = run_benchmark(...);
   ```

3. **多次运行取平均**
   ```cpp
   constexpr int kRuns = 10;
   std::vector<double> times;
   
   for (int i = 0; i < kRuns; ++i) {
       times.push_back(measure_one_run());
   }
   
   auto stats = compute_statistics(times);
   ```

4. **避免编译器优化掉测试代码**
   ```cpp
   // 使用 volatile 防止优化
   volatile int result = benchmark_function();
   
   // 或者使用 Google Benchmark 的 DoNotOptimize
   benchmark::DoNotOptimize(result);
   ```

## 4. 调试和性能分析

### 4.1 调试技巧

**使用 GDB 调试**:

```bash
# 编译 Debug 版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
cmake --build .

# 启动 GDB
gdb ./tests/test_memory

# GDB 常用命令
(gdb) break test_function      # 设置断点
(gdb) run                      # 运行程序
(gdb) next                     # 单步执行
(gdb) step                     # 进入函数
(gdb) print variable           # 打印变量
(gdb) backtrace                # 查看调用栈
(gdb) watch variable           # 监视变量变化
(gdb) info locals              # 查看局部变量
(gdb) continue                 # 继续执行
```

**使用 LLDB 调试** (macOS):

```bash
# 启动 LLDB
lldb ./tests/test_memory

# LLDB 常用命令
(lldb) breakpoint set --name test_function  # 设置断点
(lldb) run                                    # 运行程序
(lldb) next                                   # 单步执行
(lldb) step                                   # 进入函数
(lldb) print variable                         # 打印变量
(lldb) bt                                     # 查看调用栈
(lldb) watchpoint set variable variable       # 监视变量
```

**使用 Sanitizer**:

```bash
# 启用 AddressSanitizer (检测内存错误)
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON ..
cmake --build .
./tests/test_memory

# 常见错误输出
# ==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x...
# ==12345==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x...
# ==12345==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x...
```

```bash
# 启用 ThreadSanitizer (检测线程错误)
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON ..
cmake --build .
./tests/test_concurrency

# 常见错误输出
# WARNING: ThreadSanitizer: data race (pid=12345)
#   Read at 0x... by thread T1:
#   Previous write at 0x... by thread T2:
```

```bash
# 启用 UndefinedBehaviorSanitizer (检测未定义行为)
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON ..
cmake --build .
./tests/test_algorithm

# 常见错误输出
# runtime error: signed integer overflow: 2147483647 + 1 cannot be represented
# runtime error: null pointer passed as argument 1
```

### 4.2 性能分析工具

**使用 perf (Linux)**:

```bash
# 安装 perf
sudo apt install linux-tools-common linux-tools-generic

# 编译 (保留帧指针)
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_FLAGS="-fno-omit-frame-pointer" ..
cmake --build .

# 采集性能数据
perf record -g ./benchmarks/bench_memory

# 查看报告
perf report

# 实时统计
perf stat ./benchmarks/bench_memory

# 输出示例
#  Performance counter stats for './benchmarks/bench_memory':
#
#          1,234.56 msec  task-clock                #    0.998 CPUs utilized
#                12       context-switches          #    9.723 /sec
#                 2       cpu-migrations            #    1.621 /sec
#           45,678       page-faults               #   37.001 K/sec
#    3,456,789,012       cycles                    #    2.800 GHz
#    2,345,678,901       instructions              #    0.68  insn per cycle
#      456,789,012       branches                  #  370.013 M/sec
#       12,345,678       branch-misses             #    2.70% of all branches
#    1,234,567,890       L1-dcache-loads           #    1.000 G/sec
#       45,678,901       L1-dcache-load-misses     #    3.70% of all L1-dcache loads
```

**使用 Valgrind**:

```bash
# 内存泄漏检测
valgrind --leak-check=full --show-leak-kinds=all ./tests/test_memory

# 输出示例
# ==12345== HEAP SUMMARY:
# ==12345==     in use at exit: 1,024 bytes in 1 blocks
# ==12345==   total heap usage: 100 allocs, 99 frees, 50,000 bytes allocated
# ==12345==
# ==12345== 1,024 bytes in 1 blocks are definitely lost in loss record 1 of 1
# ==12345==    at 0x...: malloc (vg_replace_malloc.c:...)
# ==12345==    by 0x...: main (test_memory.cpp:...)

# 缓存分析
valgrind --tool=cachegrind ./benchmarks/bench_memory

# 输出示例
# ==12345== I   refs:      1,234,567,890
# ==12345== I1  misses:        1,234,567
# ==12345== LLi misses:          123,456
# ==12345== I1  miss rate:          0.10%
# ==12345== D   refs:        456,789,012
# ==12345== D1  misses:       12,345,678
# ==12345== LLd misses:        1,234,567
# ==12345== D1  miss rate:          2.70%

# 性能分析
valgrind --tool=callgrind ./benchmarks/bench_memory
callgrind_annotate callgrind.out.12345
```

**使用 Google Performance Tools (gperftools)**:

```bash
# 安装
sudo apt install google-perftools libgoogle-perftools-dev

# 编译链接
g++ -O2 -pg -o benchmark benchmark.cpp -lprofiler

# 运行并生成 profile
CPUPROFILE=prof.out ./benchmark

# 分析结果
pprof --text ./benchmark prof.out
pprof --pdf ./benchmark prof.out > profile.pdf
```

### 4.3 火焰图生成

```bash
# 使用 perf 采集数据
perf record -g -p $(pidof benchmark) -- sleep 30

# 生成火焰图 (需要 FlameGraph 工具)
git clone https://github.com/brendangregg/FlameGraph.git
perf script | ./FlameGraph/stackcollapse-perf.pl | ./FlameGraph/flamegraph.pl > flamegraph.svg

# 在浏览器中打开 flamegraph.svg
```

**火焰图解读**:
- X 轴: 采样比例 (越宽表示耗时越多)
- Y 轴: 调用栈深度 (越深表示调用层级越多)
- 颜色: 随机颜色，无特殊含义
- 热点: 宽的"平台"表示耗时多的函数

### 4.4 内存分析

**使用 Valgrind Massif (堆内存分析)**:

```bash
# 运行 Massif
valgrind --tool=massif ./benchmark

# 生成报告
ms_print massif.out.12345

# 输出示例
#     MB
#  3.072^                                                           #
#  2.816^                                                          ##
#  2.560^                                                         ###
#  2.304^                                                        ####
#  2.048^                                                       #####
#  1.792^                                                      ######
#  1.536^                                                     #######
#  1.280^                                                    ########
#  1.024^                                                   #########
#  0.768^                                                  ##########
#  0.512^                                                 ###########
#  0.256^                                                ############
#  0.000^################################################################
```

**使用 AddressSanitizer 内存统计**:

```bash
# 启用统计
ASAN_OPTIONS=print_stats=1 ./tests/test_memory

# 输出示例
# ==12345==AddressSanitizer: memory used 12345678 bytes
# ==12345==AddressSanitizer: malloc count: 1234
# ==12345==AddressSanitizer: free count: 1234
```

## 5. 测试指南

### 5.1 运行测试

```bash
# 运行所有测试
cd build
ctest --output-on-failure

# 运行特定测试
ctest -R memory

# 详细输出
ctest -V

# 并行运行测试
ctest -j$(nproc)

# 直接运行测试程序
./tests/test_memory
./tests/test_compiler --gtest_filter="*CacheFriendly*"
```

### 5.2 编写测试

**测试文件结构**:

```cpp
/**
 * @file test_memory.cpp
 * @brief 内存优化模块测试
 */

#include <gtest/gtest.h>
#include "cpp_perf/memory/memory_pool.h"

// 测试夹具
class MemoryPoolTest : public ::testing::Test {
 protected:
    void SetUp() override {
        pool = std::make_unique<cpp_perf::memory::MemoryPool<int, 1024>>();
    }

    void TearDown() override {
        pool.reset();
    }

    std::unique_ptr<cpp_perf::memory::MemoryPool<int, 1024>> pool;
};

// 测试用例
TEST_F(MemoryPoolTest, AllocateAndDeallocate) {
    auto* p = pool->allocate();
    ASSERT_NE(p, nullptr);
    
    *p = 42;
    EXPECT_EQ(*p, 42);
    
    pool->deallocate(p);
}

TEST_F(MemoryPoolTest, AllocateMultiple) {
    std::vector<int*> ptrs;
    
    for (int i = 0; i < 100; ++i) {
        auto* p = pool->allocate();
        ASSERT_NE(p, nullptr);
        *p = i;
        ptrs.push_back(p);
    }
    
    for (int i = 0; i < 100; ++i) {
        EXPECT_EQ(*ptrs[i], i);
        pool->deallocate(ptrs[i]);
    }
}

TEST_F(MemoryPoolTest, PoolExhaustion) {
    cpp_perf::memory::MemoryPool<int, 2> small_pool;
    
    auto* p1 = small_pool.allocate();
    auto* p2 = small_pool.allocate();
    auto* p3 = small_pool.allocate();  // 应该返回 nullptr
    
    EXPECT_NE(p1, nullptr);
    EXPECT_NE(p2, nullptr);
    EXPECT_EQ(p3, nullptr);
    
    small_pool.deallocate(p1);
    small_pool.deallocate(p2);
}
```

### 5.3 测试覆盖率

```bash
# 安装覆盖率工具
sudo apt install lcov gcovr

# 编译启用覆盖率
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON ..
cmake --build .

# 运行测试
ctest

# 生成覆盖率报告
lcov --capture --directory . --output-file coverage.info
lcov --remove coverage.info '/usr/*' --output-file coverage.info
lcov --list coverage.info

# 生成 HTML 报告
genhtml coverage.info --output-directory coverage_report
```

## 6. 贡献指南

### 6.1 代码提交流程

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/cpp-performance-optimization.git
   cd cpp-performance-optimization
   ```

2. **创建特性分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **编写代码**
   - 遵循代码风格指南
   - 添加必要的注释
   - 编写测试用例

4. **运行测试**
   ```bash
   mkdir build && cd build
   cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON ..
   cmake --build .
   ctest --output-on-failure
   ```

5. **提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加内存池实现"
   ```

6. **推送并创建 PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### 6.2 提交信息规范

使用 Conventional Commits 格式:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整 (不影响功能)
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(memory): 实现固定大小内存池

- 支持固定大小对象的分配和释放
- 使用空闲链表管理空闲块
- 线程安全版本使用 mutex 保护

Closes #123
```

### 6.3 代码审查清单

提交 PR 前检查:

- [ ] 代码遵循项目风格指南
- [ ] 添加了必要的注释
- [ ] 编写了测试用例
- [ ] 所有测试通过
- [ ] Sanitizer 检查通过
- [ ] 性能基准测试通过 (如果适用)
- [ ] 文档已更新 (如果适用)

### 6.4 代码风格检查

```bash
# 使用 clang-format 格式化代码
find . -name "*.cpp" -o -name "*.h" | xargs clang-format -i

# 使用 clang-tidy 检查
clang-tidy src/*.cpp -- -std=c++17

# 使用 cppcheck 静态分析
cppcheck --enable=all src/
```

## 7. 常见问题

### 7.1 编译问题

**Q: 编译时报错 "undefined reference to ..."**

A: 链接错误，检查是否遗漏了源文件或库。

**Q: 编译时报错 "no matching function for call to ..."**

A: 函数签名不匹配，检查参数类型和数量。

**Q: CMake 找不到编译器**

A: 设置环境变量或使用 `-DCMAKE_CXX_COMPILER=...`。

### 7.2 运行问题

**Q: 基准测试结果不稳定**

A:
1. 使用 Release 模式编译
2. 增加预热次数
3. 关闭后台程序
4. 固定 CPU 频率

**Q: Sanitizer 报告误报**

A:
1. 检查代码是否有未定义行为
2. 使用 suppression 文件过滤
3. 更新编译器版本

### 7.3 性能问题

**Q: 优化后性能没有提升**

A:
1. 确认使用 Release 模式编译
2. 检查瓶颈是否正确
3. 检查编译器是否已自动优化
4. 使用 profiler 验证

**Q: 多线程版本比单线程慢**

A:
1. 检查是否有锁竞争
2. 检查是否有伪共享
3. 检查并行粒度是否足够
4. 检查线程数是否合理

## 8. 参考资源

### 8.1 工具文档

- [CMake 文档](https://cmake.org/cmake/help/latest/)
- [GCC 文档](https://gcc.gnu.org/onlinedocs/)
- [Clang 文档](https://clang.llvm.org/docs/)
- [perf 文档](https://perf.wiki.kernel.org/)
- [Valgrind 文档](https://valgrind.org/docs/manual/)
- [Google Test](https://github.com/google/googletest)
- [Google Benchmark](https://github.com/google/benchmark)

### 8.2 学习资源

- [CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/)
- [GCC Optimization Options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)
- [Clang Sanitizers](https://clang.llvm.org/docs/AddressSanitizer.html)
- [Linux perf Examples](http://www.brendangregg.com/perf.html)

---

[返回项目主页](../README.md) | [上一篇: 产品思维文档](./04_PRODUCT.md)
