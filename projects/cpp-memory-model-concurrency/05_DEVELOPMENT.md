# 开发手册：C++ 内存模型和并发

## 环境要求

### 编译器
- GCC 10+ (推荐 GCC 12)
- Clang 12+ (推荐 Clang 15)
- MSVC 2019+ (推荐 MSVC 2022)

### 构建工具
- CMake 3.16+
- Make 或 Ninja

### 依赖库
- POSIX 线程库 (Linux/macOS)
- Windows 线程库 (Windows)

## 编译说明

### 基本编译
```bash
# 创建构建目录
mkdir build && cd build

# 配置 CMake
cmake ..

# 编译所有目标
make -j$(nproc)

# 或使用 Ninja
cmake -G Ninja ..
ninja
```

### 编译模式
```bash
# Debug 模式（包含调试信息，无优化）
cmake .. -DCMAKE_BUILD_TYPE=Debug

# Release 模式（优化性能）
cmake .. -DCMAKE_BUILD_TYPE=Release

# RelWithDebInfo 模式（优化 + 调试信息）
cmake .. -DCMAKE_BUILD_TYPE=RelWithDebInfo
```

### 单独编译某个示例
```bash
make memory_location
make atomic_basics
make lock_free_stack
```

## 运行方式

### 运行单个示例
```bash
# 进入构建目录
cd build

# 运行示例
./memory_location
./atomic_basics
./lock_free_stack
./thread_pool
```

### 运行所有示例
```bash
# 使用脚本运行所有示例
for exe in memory_location object_model value_categories lifetime; do
    echo "=== Running $exe ==="
    ./$exe
    echo ""
done
```

## 调试工具

### ThreadSanitizer (TSan)
检测数据竞争和其他线程错误。
```bash
cmake .. -DCMAKE_CXX_FLAGS="-fsanitize=thread -g"
make -j$(nproc)
./memory_location
```

### AddressSanitizer (ASan)
检测内存错误。
```bash
cmake .. -DCMAKE_CXX_FLAGS="-fsanitize=address -g"
make -j$(nproc)
./memory_location
```

### Valgrind
检测内存泄漏和线程错误。
```bash
valgrind --tool=helgrind ./memory_location
valgrind --tool=drd ./memory_location
```

### GDB 调试
```bash
gdb ./memory_location
(gdb) run
(gdb) thread apply all bt
```

## 性能分析

### perf
```bash
perf record -g ./atomic_performance
perf report
```

### Google Benchmark
```bash
# 如果安装了 Google Benchmark
cmake .. -DBUILD_BENCHMARKS=ON
make -j$(nproc)
./benchmark_all
```

## 常见问题

### Q: 编译错误 "atomic is not a member of std"
A: 确保使用 C++11 或更高标准，并包含 `<atomic>` 头文件。

### Q: 运行时死锁
A: 检查锁的获取顺序，确保所有线程以相同顺序获取锁。

### Q: 无锁程序比有锁慢
A: 可能是竞争太低，无锁的额外开销超过了锁的开销。尝试增加线程数。

### Q: TSan 报告数据竞争
A: 检查是否有未同步的共享数据访问，使用原子操作或互斥量保护。

## 最佳实践

### 1. 代码风格
- 使用 4 空格缩进
- 类名使用 PascalCase
- 函数名使用 snake_case
- 常量使用 kPascalCase

### 2. 注释规范
- 每个文件开头有版权和描述注释
- 关键代码段有解释注释
- 复杂算法有步骤注释

### 3. 错误处理
- 使用断言验证前置条件
- 使用异常处理运行时错误
- 使用 std::optional 表示可能失败的操作

### 4. 测试策略
- 单元测试验证正确性
- 压力测试验证并发安全
- 性能测试验证效率
