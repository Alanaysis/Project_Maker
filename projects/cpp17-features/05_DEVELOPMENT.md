# C++17 新特性实践项目 - 开发手册

## 编译说明

### 环境要求

#### 编译器

| 编译器 | 最低版本 | 推荐版本 | 备注 |
|--------|---------|---------|------|
| GCC | 7.0 | 9.0+ | 完整 C++17 支持 |
| Clang | 5.0 | 10.0+ | 完整 C++17 支持 |
| MSVC | 2017 15.7 | 2019+ | 完整 C++17 支持 |
| Intel C++ | 19.0 | 2021+ | 部分支持 |

#### 构建工具

- CMake: 3.8 或更高版本
- Make: GNU Make 4.0+（Linux/macOS）
- Visual Studio: 2017 或更高版本（Windows）

#### 操作系统

- Linux: Ubuntu 18.04+, CentOS 7+, Fedora 28+
- macOS: 10.13+
- Windows: 10+

### 编译步骤

#### Linux/macOS

```bash
# 1. 进入项目目录
cd cpp17-features

# 2. 创建构建目录
mkdir build
cd build

# 3. 配置 CMake
cmake ..

# 4. 编译
make

# 5. 运行示例
./optional_example
./variant_example
# ... 其他示例
```

#### Windows (Visual Studio)

```powershell
# 1. 打开 Developer Command Prompt
# 2. 进入项目目录
cd cpp17-features

# 3. 创建构建目录
mkdir build
cd build

# 4. 配置 CMake
cmake ..

# 5. 编译
cmake --build . --config Release

# 6. 运行示例
.\Release\optional_example.exe
```

### CMake 配置选项

#### 基本选项

```bash
# Debug 模式（包含调试信息）
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Release 模式（优化）
cmake -DCMAKE_BUILD_TYPE=Release ..

# 指定编译器
cmake -DCMAKE_CXX_COMPILER=g++-9 ..
cmake -DCMAKE_CXX_COMPILER=clang++-10 ..
```

#### 特殊选项

```bash
# 组合构建（所有示例合并为一个可执行文件）
cmake -DCOMBINED_BUILD=ON ..

# 启用并行算法支持（需要 TBB）
cmake -DENABLE_PARALLEL=ON ..

# 启用地址消毒器（调试内存问题）
cmake -DENABLE_ASAN=ON ..

# 启用未定义行为消毒器
cmake -DENABLE_UBSAN=ON ..
```

### 编译器特定配置

#### GCC

```bash
# 启用所有警告
cmake -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic" ..

# 启用地址消毒器
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address -g" ..

# 启用链接时优化
cmake -DCMAKE_CXX_FLAGS="-flto" ..
```

#### Clang

```bash
# 启用所有警告
cmake -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic" ..

# 启用地址消毒器
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address -g" ..

# 启用 ThreadSanitizer
cmake -DCMAKE_CXX_FLAGS="-fsanitize=thread -g" ..
```

#### MSVC

```bash
# 启用所有警告
cmake -DCMAKE_CXX_FLAGS="/W4" ..

# 启用地址消毒器
cmake -DCMAKE_CXX_FLAGS="/fsanitize=address" ..
```

## 运行方式

### 运行单个示例

```bash
# 编译并运行单个示例
g++ -std=c++17 -o optional_example optional_example.cpp
./optional_example
```

### 运行所有示例

```bash
# 使用 CMake 构建
mkdir build && cd build
cmake ..
make

# 运行所有示例
./optional_example
./variant_example
./any_example
./string_view_example
./structured_bindings
./if_constexpr_example
./fold_expressions
./inline_variables
./nested_namespaces
./attributes_example
./filesystem_example
./apply_example
./invoke_example
./gcd_lcm_example
./parallel_algorithms
./shared_mutex_example
./scoped_lock_example
./ctad_example
./auto_extensions
```

### 组合构建运行

```bash
# 组合构建
mkdir build && cd build
cmake -DCOMBINED_BUILD=ON ..
make

# 运行所有示例
./cpp17_features
```

## 调试

### 使用 GDB

```bash
# 编译调试版本
g++ -std=c++17 -g -o optional_example optional_example.cpp

# 启动 GDB
gdb ./optional_example

# GDB 常用命令
(gdb) break main          # 设置断点
(gdb) run                 # 运行程序
(gdb) next                # 单步执行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) quit                # 退出
```

### 使用 LLDB

```bash
# 编译调试版本
clang++ -std=c++17 -g -o optional_example optional_example.cpp

# 启动 LLDB
lldb ./optional_example

# LLDB 常用命令
(lldb) breakpoint set --name main  # 设置断点
(lldb) run                         # 运行程序
(lldb) next                        # 单步执行
(lldb) step                        # 进入函数
(lldb) print variable              # 打印变量
(lldb) bt                          # 查看调用栈
(lldb) quit                        # 退出
```

### 使用消毒器

#### 地址消毒器（ASan）

```bash
# 编译
g++ -std=c++17 -fsanitize=address -g -o test test.cpp

# 运行
./test

# 检测内存错误
# - 堆缓冲区溢出
# - 栈缓冲区溢出
# - 使用已释放内存
# - 内存泄漏
```

#### 未定义行为消毒器（UBSan）

```bash
# 编译
g++ -std=c++17 -fsanitize=undefined -g -o test test.cpp

# 运行
./test

# 检测未定义行为
# - 整数溢出
# - 空指针解引用
# - 数组越界
# - 类型转换错误
```

#### ThreadSanitizer（TSan）

```bash
# 编译
g++ -std=c++17 -fsanitize=thread -g -o test test.cpp

# 运行
./test

# 检测并发问题
# - 数据竞争
# - 死锁
# - 线程安全问题
```

## 测试

### 单元测试

```bash
# 编译单个测试
g++ -std=c++17 -DTEST_MODE -o test_optional optional_example.cpp

# 运行测试
./test_optional
```

### 集成测试

```bash
# 编译所有测试
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 运行所有测试
ctest --output-on-failure
```

### 编译器兼容性测试

```bash
# 测试 GCC 7
g++-7 -std=c++17 -Wall -Wextra -o test file.cpp

# 测试 GCC 8
g++-8 -std=c++17 -Wall -Wextra -o test file.cpp

# 测试 GCC 9
g++-9 -std=c++17 -Wall -Wextra -o test file.cpp

# 测试 Clang 5
clang++-5 -std=c++17 -Wall -Wextra -o test file.cpp

# 测试 Clang 6
clang++-6 -std=c++17 -Wall -Wextra -o test file.cpp
```

## 常见问题

### Q1: 编译错误 "filesystem: No such file or directory"

**原因**: GCC 7/8 需要链接 `stdc++fs` 库

**解决方案**:
```bash
g++ -std=c++17 -o test filesystem_example.cpp -lstdc++fs
```

或在 CMakeLists.txt 中添加：
```cmake
target_link_libraries(filesystem_example stdc++fs)
```

### Q2: 并行算法不工作

**原因**: 需要安装 TBB 库并启用并行支持

**解决方案**:
```bash
# 安装 TBB
sudo apt-get install libtbb-dev  # Ubuntu
brew install tbb                  # macOS

# 启用并行支持
cmake -DENABLE_PARALLEL=ON ..
```

### Q3: 编译警告 "unused variable"

**原因**: 示例代码中的变量可能未使用

**解决方案**: 使用 `[[maybe_unused]]` 属性
```cpp
[[maybe_unused]] int unused_var = 42;
```

### Q4: MSVC 编译错误 C4996

**原因**: MSVC 对某些标准函数发出弃用警告

**解决方案**: 添加预处理器定义
```cmake
target_compile_definitions(${target} PRIVATE _CRT_SECURE_NO_WARNINGS)
```

## 性能测试

### 编译时间测试

```bash
# 测量编译时间
time g++ -std=c++17 -o test file.cpp

# 测量并行编译时间
time make -j$(nproc)
```

### 运行时间测试

```bash
# 使用 time 命令
time ./test

# 使用 perf 工具
perf stat ./test
```

### 内存使用测试

```bash
# 使用 valgrind
valgrind --tool=memcheck ./test

# 使用 massif（堆分析）
valgrind --tool=massif ./test
ms_print massif.out.*
```

## 部署

### 打包发布

```bash
# 创建发布包
mkdir release
cp build/optional_example release/
cp build/variant_example release/
# ... 其他文件
tar -czf cpp17-features-linux-x64.tar.gz release/
```

### 跨平台编译

```bash
# 使用交叉编译工具链
cmake -DCMAKE_TOOLCHAIN_FILE=toolchain.cmake ..
```

## 维护

### 代码风格

- 使用 clang-format 格式化代码
- 遵循 Google C++ Style Guide
- 保持一致的命名规范

### 版本控制

- 使用 Git 进行版本控制
- 遵循 Git Flow 工作流
- 编写清晰的提交信息

### 文档更新

- 及时更新 README.md
- 保持代码注释与代码同步
- 记录所有变更
