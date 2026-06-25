# 05 - 开发手册

## 编译环境配置

### 1. 编译器安装

#### GCC 13+

**Ubuntu/Debian:**
```bash
# 添加 PPA
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt update

# 安装 GCC 13
sudo apt install g++-13

# 设置默认版本
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100

# 验证
g++ --version
```

**macOS:**
```bash
# 使用 Homebrew
brew install gcc@13

# 验证
g++-13 --version
```

**Windows:**
- 下载 MSYS2: https://www.msys2.org/
- 安装 MinGW-w64 GCC 13+
- 添加到 PATH

#### Clang 17+

**Ubuntu/Debian:**
```bash
# 添加 LLVM 仓库
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 17

# 安装
sudo apt install clang-17

# 设置默认版本
sudo update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-17 100

# 验证
clang++ --version
```

**macOS:**
```bash
# Xcode Command Line Tools 包含 Clang
xcode-select --install

# 或使用 Homebrew
brew install llvm@17

# 验证
clang++ --version
```

**Windows:**
- 下载 LLVM: https://releases.llvm.org/
- 安装并添加到 PATH

#### MSVC 2022 17.5+

**Windows:**
1. 下载 Visual Studio 2022: https://visualstudio.microsoft.com/
2. 安装时选择 "C++ 桌面开发" 工作负载
3. 确保安装 MSVC v143 和 Windows SDK

### 2. CMake 安装

#### Linux
```bash
# Ubuntu/Debian
sudo apt install cmake

# 或使用 snap
sudo snap install cmake --classic

# 验证
cmake --version
```

#### macOS
```bash
# Homebrew
brew install cmake

# 验证
cmake --version
```

#### Windows
- 下载 CMake: https://cmake.org/download/
- 安装时选择 "Add CMake to the system PATH"

### 3. 编辑器配置

#### VS Code

**推荐插件:**
- C/C++ (Microsoft)
- CMake Tools
- C++ TestMate

**settings.json:**
```json
{
    "cmake.configureOnOpen": true,
    "cmake.generator": "Ninja",
    "C_Cpp.default.cppStandard": "c++23",
    "C_Cpp.default.compilerPath": "/usr/bin/g++-13"
}
```

#### CLion

**配置步骤:**
1. 打开 Settings/Preferences
2. 导航到 Build, Execution, Deployment > Toolchains
3. 设置 C++ 编译器为 GCC 13+ 或 Clang 17+
4. 导航到 CMake
5. 设置 C++ 标准为 C++23

## 编译说明

### 1. 使用 CMake 构建

#### 基本构建流程

```bash
# 进入项目目录
cd /home/siok/project_copyninja/projects/cpp23-features

# 创建构建目录 (out-of-source 构建)
mkdir build
cd build

# 配置项目
cmake ..

# 或者指定编译器
cmake -DCMAKE_CXX_COMPILER=g++-13 ..

# 编译
cmake --build .

# 或者指定并行编译数
cmake --build . -j$(nproc)
```

#### 构建选项

```bash
# Debug 构建
cmake -DCMAKE_BUILD_TYPE=Debug ..
cmake --build .

# Release 构建
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .

# 指定安装路径
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
cmake --build .
sudo cmake --install .
```

#### 使用 Ninja 构建系统

```bash
# 安装 Ninja
sudo apt install ninja-build  # Linux
brew install ninja              # macOS

# 使用 Ninja 构建
cmake -G Ninja ..
ninja
```

### 2. 单独编译示例

#### 使用 g++

```bash
# 进入示例目录
cd /home/siok/project_copyninja/projects/cpp23-features/examples

# 编译单个文件
g++ -std=c++23 -o expected_example expected_example.cpp

# 带调试信息编译
g++ -std=c++23 -g -o expected_example expected_example.cpp

# 带优化编译
g++ -std=c++23 -O2 -o expected_example expected_example.cpp

# 运行
./expected_example
```

#### 使用 clang++

```bash
# 编译
clang++ -std=c++23 -o expected_example expected_example.cpp

# 运行
./expected_example
```

#### 使用 MSVC (Windows)

```cmd
# 编译
cl /std:c++23 /EHsc expected_example.cpp

# 运行
expected_example.exe
```

### 3. 编译选项说明

#### 标准选项
- `-std=c++23`: 启用 C++23 标准
- `-std=c++2b`: C++23 的早期名称 (某些编译器使用)

#### 警告选项
- `-Wall`: 启用所有常见警告
- `-Wextra`: 启用额外警告
- `-Wpedantic`: 严格标准检查
- `-Werror`: 将警告视为错误

#### 优化选项
- `-O0`: 无优化 (调试用)
- `-O1`: 基本优化
- `-O2`: 推荐优化级别
- `-O3`: 最高优化
- `-Os`: 优化大小
- `-Ofast`: 最高性能 (可能不符合标准)

#### 调试选项
- `-g`: 生成调试信息
- `-fsanitize=address`: 地址消毒器
- `-fsanitize=undefined`: 未定义行为消毒器

## 运行方式

### 1. 运行单个示例

```bash
# 进入构建目录
cd build/examples

# 运行特定示例
./expected_example
./mdspan_example
./generator_example

# 查看输出
./expected_example 2>&1 | less
```

### 2. 运行所有示例

```bash
# 使用 CTest
cd build
ctest --output-on-failure

# 或使用脚本
for exe in examples/*_example; do
    echo "Running $exe..."
    ./$exe
    echo "---"
done
```

### 3. 运行特定类别

```bash
# 运行所有 Ranges 示例
for exe in examples/ranges_*; do
    echo "Running $exe..."
    ./$exe
    echo "---"
done
```

## 调试

### 1. 使用 GDB

```bash
# 编译带调试信息
g++ -std=c++23 -g -o expected_example expected_example.cpp

# 启动 GDB
gdb ./expected_example

# GDB 常用命令
(gdb) break main        # 设置断点
(gdb) run               # 运行程序
(gdb) next              # 单步执行
(gdb) step              # 进入函数
(gdb) print variable    # 打印变量
(gdb) backtrace         # 查看调用栈
(gdb) quit              # 退出
```

### 2. 使用 LLDB

```bash
# 编译带调试信息
clang++ -std=c++23 -g -o expected_example expected_example.cpp

# 启动 LLDB
lldb ./expected_example

# LLDB 常用命令
(lldb) breakpoint set --name main  # 设置断点
(lldb) run                          # 运行程序
(lldb) next                         # 单步执行
(lldb) step                         # 进入函数
(lldb) print variable               # 打印变量
(lldb) bt                           # 查看调用栈
(lldb) quit                         # 退出
```

### 3. 使用 Valgrind

```bash
# 安装 Valgrind
sudo apt install valgrind

# 检查内存泄漏
valgrind --leak-check=full ./expected_example

# 检查未初始化内存
valgrind --tool=memcheck ./expected_example
```

### 4. 使用 AddressSanitizer

```bash
# 编译启用消毒器
g++ -std=c++23 -fsanitize=address -g -o expected_example expected_example.cpp

# 运行
./expected_example
```

## 常见问题

### 1. 编译错误

#### 问题: 不支持 C++23
```
error: unrecognized option '-std=c++23'
```

**解决方案:**
- 升级编译器版本
- 使用 `-std=c++2b` 替代

#### 问题: 缺少头文件
```
fatal error: expected: No such file or directory
```

**解决方案:**
- 确保编译器版本足够新
- 检查标准库安装

### 2. 链接错误

#### 问题: 未定义引用
```
undefined reference to `std::stacktrace::current()'
```

**解决方案:**
- 链接正确的库
- 添加 `-lstdc++_libbacktrace` (GCC)
- 添加 `-lstdc++` (Clang)

### 3. 运行时错误

#### 问题: 段错误
**解决方案:**
- 使用调试器定位问题
- 检查数组越界
- 检查空指针

## 性能测试

### 1. 使用 time

```bash
# 测量执行时间
time ./expected_example
```

### 2. 使用 Google Benchmark

```cpp
#include <benchmark/benchmark.h>

static void BM_Example(benchmark::State& state) {
    for (auto _ : state) {
        // 测试代码
    }
}
BENCHMARK(BM_Example);

BENCHMARK_MAIN();
```

### 3. 使用 perf

```bash
# 安装 perf
sudo apt install linux-tools-common

# 性能分析
perf record ./expected_example
perf report
```

## 代码规范

### 1. 命名规范

- **文件名**: 小写字母 + 下划线
- **函数名**: 小写字母 + 下划线
- **变量名**: 小写字母 + 下划线
- **类名**: 大驼峰
- **常量**: 大写字母 + 下划线

### 2. 代码风格

- 使用 4 空格缩进
- 每行不超过 100 字符
- 使用空行分隔逻辑块
- 注释使用中文

### 3. 注释规范

- 文件头注释包含文件说明和编译命令
- 函数注释说明用途和参数
- 关键代码添加行内注释

## 持续集成

### GitHub Actions 示例

```yaml
name: C++23 Examples

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install GCC 13
        run: |
          sudo add-apt-repository ppa:ubuntu-toolchain-r/test
          sudo apt update
          sudo apt install g++-13
      
      - name: Configure
        run: cmake -DCMAKE_CXX_COMPILER=g++-13 -B build
      
      - name: Build
        run: cmake --build build
      
      - name: Test
        run: cd build && ctest --output-on-failure
```

## 总结

本开发手册提供了完整的编译、运行和调试指南。开发者可以根据自己的环境选择合适的工具和方法。

关键要点：
1. 确保编译器版本支持 C++23
2. 使用 CMake 管理构建过程
3. 掌握调试工具的使用
4. 遵循代码规范
