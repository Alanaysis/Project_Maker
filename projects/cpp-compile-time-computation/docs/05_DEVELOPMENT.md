# 05 - 开发手册：C++ 编译期计算

## 环境配置

### 编译器要求

| 编译器 | 最低版本 | 推荐版本 |
|--------|---------|---------|
| GCC | 12.0 | 13.0+ |
| Clang | 15.0 | 17.0+ |
| MSVC | 2022 (17.0) | 2022 (17.5)+ |

### 检查编译器版本

```bash
# GCC
g++ --version

# Clang
clang++ --version

# MSVC
cl.exe
```

### CMake 配置

```bash
# 基本配置
cmake -B build -DCMAKE_BUILD_TYPE=Release

# 指定编译器
cmake -B build -DCMAKE_CXX_COMPILER=g++-13

# 生成 compile_commands.json
cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

## 编译说明

### 编译单个示例

```bash
# 使用 g++
g++ -std=c++20 -I include examples/constexpr_basics.cpp -o constexpr_basics

# 使用 clang++
clang++ -std=c++20 -I include examples/constexpr_basics.cpp -o constexpr_basics

# 开启优化
g++ -std=c++20 -O2 -I include examples/constexpr_basics.cpp -o constexpr_basics
```

### 编译所有示例

```bash
# 配置
cmake -B build -DCMAKE_BUILD_TYPE=Release

# 编译
cmake --build build -j$(nproc)

# 编译特定目标
cmake --build build --target example_constexpr_basics
```

### 编译并运行测试

```bash
# 配置
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# 编译测试
cmake --build build -j$(nproc)

# 运行所有测试
cd build && ctest --output-on-failure

# 运行特定测试
cd build && ctest -R constexpr_basics --output-on-failure
```

## 运行方式

### 运行示例

```bash
# 运行编译好的示例
./build/example_constexpr_basics

# 查看输出
./build/example_constexpr_basics 2>&1 | tee output.txt
```

### 运行测试

```bash
# 运行所有测试
cd build && ctest

# 运行特定测试
./build/test_compile_time_tests

# 详细输出
cd build && ctest -V
```

### 运行性能测试

```bash
# 编译性能测试
cmake --build build --target bench_performance_benchmark

# 运行性能测试
./build/bench_performance_benchmark
```

## 开发工作流

### 1. 添加新示例

```bash
# 1. 创建新文件
touch examples/new_example.cpp

# 2. 编写代码
# ... 编辑文件 ...

# 3. 编译测试
g++ -std=c++20 -I include examples/new_example.cpp -o new_example

# 4. 运行验证
./new_example

# 5. 添加 CMake 支持
# CMakeLists.txt 会自动扫描 examples/*.cpp
```

### 2. 添加新头文件

```bash
# 1. 创建头文件
touch include/compile_time/new_feature.hpp

# 2. 编写代码
# ... 编辑文件 ...

# 3. 更新 README.md
# 添加新特性的说明和示例

# 4. 创建示例文件
touch examples/new_feature_example.cpp
```

### 3. 添加新测试

```bash
# 1. 创建测试文件
touch tests/test_new_feature.cpp

# 2. 编写测试
# ... 编辑文件 ...

# 3. 运行测试
cd build && cmake .. && make test_new_feature
./test_new_feature
```

## 调试技巧

### 1. 编译期错误调试

**问题**：编译期计算的错误信息可能很复杂。

**解决方案**：

```bash
# 使用 -fsyntax-only 只检查语法
g++ -std=c++20 -fsyntax-only -I include examples/constexpr_basics.cpp

# 使用 -ftemplate-backtrace-limit=0 获取完整模板错误
g++ -std=c++20 -ftemplate-backtrace-limit=0 -I include examples/constexpr_basics.cpp

# 使用 -fconcepts-diagnostics-depth=2 获取概念错误详情
g++ -std=c++20 -fconcepts-diagnostics-depth=2 -I include examples/constexpr_basics.cpp
```

### 2. 运行时调试

```bash
# 使用 gdb 调试
g++ -std=c++20 -g -I include examples/constexpr_basics.cpp -o constexpr_basics_debug
gdb ./constexpr_basics_debug

# 使用 lldb 调试（macOS/Linux）
g++ -std=c++20 -g -I include examples/constexpr_basics.cpp -o constexpr_basics_debug
lldb ./constexpr_basics_debug
```

### 3. 查看编译器生成的代码

```bash
# 查看汇编代码
g++ -std=c++20 -S -I include examples/constexpr_basics.cpp -o constexpr_basics.s

# 使用 godbolt.org 在线查看
# 访问 https://godbolt.org/ 并粘贴代码
```

## 常见问题

### 1. 编译器不支持 C++20

**症状**：编译错误提示不支持 constexpr lambda、consteval 等特性。

**解决方案**：
- 升级编译器到支持 C++20 的版本
- 使用 `-std=c++17` 降级编译（部分特性不可用）

### 2. 编译时间过长

**症状**：编译示例需要很长时间。

**解决方案**：
- 减少编译期计算的复杂度
- 使用 `-O0` 禁用优化（调试时）
- 使用 `-j$(nproc)` 并行编译

### 3. 运行时错误

**症状**：编译通过但运行时崩溃。

**解决方案**：
- 检查是否有未定义行为
- 使用 `-fsanitize=address,undefined` 检测内存错误
- 添加更多运行时检查

### 4. 模板错误信息难以理解

**症状**：模板实例化错误信息很长且难以阅读。

**解决方案**：
- 使用 `-ftemplate-backtrace-limit=0` 获取完整错误
- 逐步简化代码，定位问题
- 使用 concepts（C++20）提供更好的错误信息

## 最佳实践

### 1. 代码风格

- 使用 4 空格缩进
- 每行不超过 100 字符
- 使用有意义的变量名
- 添加详细注释

### 2. 头文件组织

- 每个头文件使用 include guard
- 按功能分组
- 避免循环依赖

### 3. 测试策略

- 每个特性都有对应的测试
- 使用 `static_assert` 验证编译期结果
- 使用传统测试框架验证运行时行为

### 4. 性能优化

- 测量编译时间和运行时性能
- 避免过度使用编译期计算
- 使用 `-O2` 或 `-O3` 优化

## 工具推荐

### 1. 编译器

- **GCC**：功能完整，社区活跃
- **Clang**：错误信息清晰，支持最新标准
- **MSVC**：Windows 平台首选

### 2. 构建工具

- **CMake**：跨平台构建系统
- **Ninja**：快速构建工具
- **Meson**：现代化构建系统

### 3. 调试工具

- **GDB**：GNU 调试器
- **LLDB**：LLVM 调试器
- **Valgrind**：内存错误检测

### 4. 代码分析

- **Clang-Tidy**：代码规范检查
- **Include-What-You-Use**：头文件依赖分析
- **Cppcheck**：静态代码分析

## 参考资源

- [cppreference](https://en.cppreference.com/)：C++ 标准参考
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/)：C++ 核心指南
- [Compiler Explorer](https://godbolt.org/)：在线编译器
- [Quick C++ Benchmark](https://quick-bench.com/)：在线性能测试
