# C++ 性能优化技巧 - 开发手册

## 1. 环境准备

### 1.1 编译器要求
| 编译器 | 最低版本 | 推荐版本 |
|--------|---------|---------|
| GCC | 9.0 | 12.0+ |
| Clang | 10.0 | 15.0+ |
| MSVC | 2019 | 2022 |

### 1.2 构建工具
- CMake: 3.14+
- Make: 任意版本
- Ninja (可选): 1.10+

### 1.3 系统要求
- Linux: 推荐 (支持 perf)
- macOS: 支持
- Windows: 部分支持

### 1.4 可选依赖
- Google Benchmark: 用于基准测试
- Intel TBB: 用于并行算法
- OpenMP: 用于并行循环

## 2. 编译说明

### 2.1 基本编译
```bash
# 进入项目目录
cd projects/cpp-performance-optimization

# 创建构建目录
mkdir build && cd build

# 配置 (Release 模式)
cmake -DCMAKE_BUILD_TYPE=Release ..

# 编译
make -j$(nproc)

# 或使用 Ninja
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release ..
ninja
```

### 2.2 编译选项

#### Debug 模式
```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
```
- 禁用优化 (-O0)
- 启用调试符号 (-g)
- 启用断言
- 适合调试

#### Release 模式
```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
```
- 启用优化 (-O3)
- 禁用调试符号
- 启用 NDEBUG
- 适合性能测试

#### Release with Debug Info
```bash
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
```
- 启用优化 (-O2)
- 启用调试符号 (-g)
- 适合性能分析

### 2.3 高级编译选项

#### 启用 LTO (Link-Time Optimization)
```bash
cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_LTO=ON ..
```

#### 启用 Sanitizer
```bash
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON ..
```
- AddressSanitizer: 检测内存错误
- UndefinedBehaviorSanitizer: 检测未定义行为

#### 指定 SIMD 指令集
```bash
# SSE2 (默认)
cmake -DCMAKE_CXX_FLAGS="-msse2" ..

# AVX2
cmake -DCMAKE_CXX_FLAGS="-mavx2" ..

# AVX-512
cmake -DCMAKE_CXX_FLAGS="-mavx512f" ..

# 原生指令集
cmake -DCMAKE_CXX_FLAGS="-march=native" ..
```

#### 启用 OpenMP
```bash
cmake -DUSE_OPENMP=ON ..
```

## 3. 运行方式

### 3.1 运行单个示例
```bash
# 运行内存优化示例
./src/memory/cache_friendly
./src/memory/soa_vs_aos
./src/memory/memory_alignment

# 运行编译器优化示例
./src/compiler/inlining
./src/compiler/vectorization

# 运行算法优化示例
./src/algorithm/simd_optimization
./src/algorithm/parallelization
```

### 3.2 运行所有测试
```bash
# 使用 CTest
ctest --output-on-failure

# 或使用脚本
../scripts/run_benchmarks.sh
```

### 3.3 生成报告
```bash
../scripts/generate_report.sh
```

## 4. 性能分析

### 4.1 使用 perf

#### 基本性能分析
```bash
# 记录性能数据
perf record -g ./src/memory/cache_friendly

# 查看报告
perf report

# 实时统计
perf stat ./src/memory/cache_friendly
```

#### 缓存分析
```bash
# 缓存未命中分析
perf stat -e cache-misses,cache-references ./src/memory/cache_friendly

# 详细缓存分析
perf c2c record ./src/memory/cache_friendly
perf c2c report
```

#### 分支预测分析
```bash
perf stat -e branch-misses,branches ./src/compiler/branch_prediction
```

### 4.2 使用 Valgrind

#### 缓存分析
```bash
valgrind --tool=cachegrind ./src/memory/cache_friendly
cg_annotate cachegrind.out.<pid>
```

#### Callgrind 分析
```bash
valgrind --tool=callgrind ./src/memory/cache_friendly
callgrind_annotate callgrind.out.<pid>
```

### 4.3 使用 Google Benchmark

#### 安装
```bash
# Ubuntu/Debian
sudo apt-get install libbenchmark-dev

# 或从源码编译
git clone https://github.com/google/benchmark.git
cd benchmark
cmake -E make_directory "build"
cmake -DBENCHMARK_DOWNLOAD_DEPENDENCIES=ON -DCMAKE_BUILD_TYPE=Release -S . -B build
cmake --build build --config Release
sudo cmake --install build
```

#### 使用
```cpp
#include <benchmark/benchmark.h>

static void BM_VectorPushBack(benchmark::State& state) {
    for (auto _ : state) {
        std::vector<int> v;
        for (int i = 0; i < state.range(0); ++i) {
            v.push_back(i);
        }
    }
}
BENCHMARK(BM_VectorPushBack)->Arg(1 << 10)->Arg(1 << 20);

BENCHMARK_MAIN();
```

### 4.4 查看汇编输出

#### 使用 Compiler Explorer (Godbolt)
- 访问 https://godbolt.org/
- 粘贴代码查看汇编
- 对比不同编译器的输出

#### 本地查看
```bash
# 生成汇编文件
g++ -S -O3 -masm=intel source.cpp -o output.s

# 使用 objdump
objdump -d -M intel ./binary | less
```

## 5. 调试技巧

### 5.1 性能调试
```cpp
// 使用 RAII 计时器
{
    Timer t("Operation");
    // 要计时的代码
}

// 使用性能计数器
{
    PerfCounter counter;
    counter.start();
    // 要测量的代码
    counter.stop();
    counter.print();
}
```

### 5.2 内存调试
```bash
# AddressSanitizer
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON ..
make
./binary

# Valgrind
valgrind --leak-check=full ./binary
```

### 5.3 并发调试
```bash
# ThreadSanitizer
cmake -DCMAKE_CXX_FLAGS="-fsanitize=thread" ..
make
./binary
```

## 6. 最佳实践

### 6.1 编译最佳实践
1. 开发时使用 Debug 模式
2. 性能测试使用 Release 模式
3. 启用 -march=native 获取原生指令集
4. 使用 LTO 获得额外性能提升
5. 使用 Sanitizer 检测问题

### 6.2 测试最佳实践
1. 多次运行取平均值
2. 预热运行让 CPU 缓存稳定
3. 隔离测试避免干扰
4. 记录测试环境信息
5. 对比多个编译器

### 6.3 分析最佳实践
1. 先用 perf 找到热点
2. 用 cachegrind 分析缓存
3. 用 callgrind 分析调用
4. 查看汇编理解编译器行为
5. 对比优化前后数据

## 7. 常见问题

### 7.1 编译错误

**问题**: 找不到头文件
```bash
fatal error: xxx.hpp: No such file or directory
```
**解决**: 检查 include 路径设置

**问题**: 链接错误
```bash
undefined reference to `xxx'
```
**解决**: 检查链接库设置

### 7.2 运行错误

**问题**: 段错误
```
Segmentation fault (core dumped)
```
**解决**: 使用 AddressSanitizer 定位

**问题**: 数据竞争
```
WARNING: ThreadSanitizer: data race
```
**解决**: 使用 ThreadSanitizer 定位

### 7.3 性能问题

**问题**: 优化没有效果
**解决**: 
1. 确认使用 Release 模式
2. 检查是否优化了热点代码
3. 使用性能分析工具验证

**问题**: 性能不稳定
**解决**:
1. 增加运行次数
2. 关闭后台程序
3. 固定 CPU 频率

## 8. 开发工具推荐

### 8.1 IDE
- CLion: C++ 专业 IDE
- Visual Studio Code: 轻量级
- Visual Studio: Windows 平台

### 8.2 性能工具
- perf: Linux 性能分析
- Intel VTune: 专业性能分析
- AMD uProf: AMD 平台分析
- Valgrind: 内存分析

### 8.3 在线工具
- Compiler Explorer: 查看汇编
- Quick C++ Benchmark: 在线基准测试
- C++ Insights: 理解语言特性

## 9. 贡献指南

### 9.1 添加新示例
1. 在对应目录创建 .cpp 文件
2. 遵循代码模板
3. 更新 CMakeLists.txt
4. 添加注释和文档
5. 测试编译和运行

### 9.2 代码规范
- 使用 4 空格缩进
- 遵循命名规范
- 添加必要注释
- 保持代码简洁

### 9.3 提交规范
- 一个提交一个功能
- 清晰的提交信息
- 测试通过
- 文档更新

## 10. 参考资源

### 10.1 书籍
- 《Effective Modern C++》
- 《C++ High Performance》
- 《Optimizing software in C++》

### 10.2 网站
- CppCon 演讲
- Agner Fog 优化手册
- Quick C++ Benchmark
- Compiler Explorer

### 10.3 工具文档
- GCC 文档
- LLVM 文档
- Intel Intrinsics Guide
- perf 文档