# 05 开发手册

## 开发环境

### 1. 编译器要求

| 编译器 | 最低版本 | 推荐版本 | 备注 |
|--------|----------|----------|------|
| GCC | 10 | 13+ | 支持 C++20 |
| Clang | 12 | 17+ | 支持 C++20 |
| MSVC | 2019 | 2022 | 支持 C++20 |

### 2. 构建工具

| 工具 | 最低版本 | 推荐版本 |
|------|----------|----------|
| CMake | 3.16 | 3.25+ |
| Make | 4.0 | 4.3+ |
| Ninja | 1.10 | 1.11+ |

### 3. 操作系统

| 操作系统 | 版本 | 备注 |
|----------|------|------|
| Linux | Ubuntu 20.04+ | 推荐 |
| macOS | 11+ | 支持 |
| Windows | 10+ | 需要 MSVC |

## 编译说明

### 1. 快速开始

```bash
# 克隆项目
cd projects/cpp-pitfalls-best-practices

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译
cmake --build .

# 运行示例
./bin/memory_pitfalls
```

### 2. 详细编译步骤

#### Linux/macOS

```bash
# 1. 检查编译器版本
g++ --version  # 或 clang++ --version

# 2. 检查 CMake 版本
cmake --version

# 3. 创建构建目录
mkdir -p build && cd build

# 4. 配置项目（Release 模式）
cmake -DCMAKE_BUILD_TYPE=Release ..

# 5. 编译（使用多核）
cmake --build . -j$(nproc)

# 6. 运行所有示例
ctest --output-on-failure
```

#### Windows (MSVC)

```powershell
# 1. 打开 Developer Command Prompt

# 2. 创建构建目录
mkdir build
cd build

# 3. 配置项目
cmake -G "Visual Studio 17 2022" ..

# 4. 编译
cmake --build . --config Release

# 5. 运行示例
.\bin\Release\memory_pitfalls.exe
```

### 3. CMake 选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `CMAKE_BUILD_TYPE` | Release | 构建类型 |
| `CMAKE_CXX_STANDARD` | 17 | C++ 标准 |
| `ENABLE_SANITIZERS` | OFF | 启用 Sanitizers |
| `ENABLE_TESTS` | ON | 启用测试 |

```bash
# 启用 Sanitizers
cmake -DENABLE_SANITIZERS=ON ..

# 使用 C++20
cmake -DCMAKE_CXX_STANDARD=20 ..

# Debug 模式
cmake -DCMAKE_BUILD_TYPE=Debug ..
```

## 运行方式

### 1. 运行单个示例

```bash
# 编译单个文件
g++ -std=c++17 -o dangling_ptr ../src/memory/01_dangling_pointer.cpp

# 运行
./dangling_ptr
```

### 2. 运行所有示例

```bash
# 使用 CTest 运行所有测试
cd build
ctest --output-on-failure

# 或者逐个运行
./bin/memory_pitfalls
./bin/type_pitfalls
./bin/template_pitfalls
./bin/concurrency_pitfalls
./bin/lifetime_pitfalls
./bin/exception_safety
./bin/best_practices
./bin/quality
```

### 3. 运行特定类别

```bash
# 只运行内存陷阱
./bin/memory_pitfalls

# 只运行并发陷阱
./bin/concurrency_pitfalls
```

## 调试说明

### 1. 使用 GDB 调试

```bash
# 编译 Debug 版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
cmake --build .

# 使用 GDB 调试
gdb ./bin/memory_pitfalls

# GDB 常用命令
(gdb) break main          # 设置断点
(gdb) run                 # 运行程序
(gdb) next                # 单步执行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) quit                # 退出
```

### 2. 使用 LLDB 调试

```bash
# 使用 LLDB 调试
lldb ./bin/memory_pitfalls

# LLDB 常用命令
(lldb) breakpoint set --name main  # 设置断点
(lldb) run                         # 运行程序
(lldb) next                        # 单步执行
(lldb) step                        # 进入函数
(lldb) print variable              # 打印变量
(lldb) bt                          # 查看调用栈
(lldb) quit                        # 退出
```

### 3. 使用 Sanitizers

#### AddressSanitizer (ASan)

```bash
# 编译时启用 ASan
g++ -std=c++17 -fsanitize=address -g -o program program.cpp

# 运行
./program

# ASan 会检测：
# - 内存泄漏
# - 缓冲区溢出
# - 使用已释放内存
# - 双重释放
```

#### ThreadSanitizer (TSan)

```bash
# 编译时启用 TSan
g++ -std=c++17 -fsanitize=thread -g -o program program.cpp

# 运行
./program

# TSan 会检测：
# - 数据竞争
# - 死锁
```

#### UndefinedBehaviorSanitizer (UBSan)

```bash
# 编译时启用 UBSan
g++ -std=c++17 -fsanitize=undefined -g -o program program.cpp

# 运行
./program

# UBSan 会检测：
# - 整数溢出
# - 空指针解引用
# - 未定义行为
```

## 静态分析

### 1. Clang-Tidy

```bash
# 使用 CMake 集成
cmake -DCMAKE_CXX_CLANG_TIDY=clang-tidy ..

# 或手动运行
clang-tidy src/memory/01_dangling_pointer.cpp -- -std=c++17
```

### 2. Cppcheck

```bash
# 运行 Cppcheck
cppcheck --enable=all --std=c++17 src/

# 生成报告
cppcheck --enable=all --std=c++17 --xml --xml-version=2 src/ 2> report.xml
```

### 3. 集成到 CI/CD

```yaml
# GitHub Actions 示例
name: Static Analysis
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install tools
        run: |
          sudo apt-get update
          sudo apt-get install -y clang-tidy cppcheck
      - name: Run clang-tidy
        run: |
          cmake -B build -DCMAKE_CXX_CLANG_TIDY=clang-tidy .
          cmake --build build
      - name: Run cppcheck
        run: cppcheck --enable=all --std=c++17 src/
```

## 代码格式化

### 1. Clang-Format

```bash
# 格式化单个文件
clang-format -i src/memory/01_dangling_pointer.cpp

# 格式化所有文件
find src/ -name "*.cpp" -exec clang-format -i {} \;

# 检查格式
clang-format --dry-run --Werror src/**/*.cpp
```

### 2. 格式化配置

项目根目录创建 `.clang-format` 文件：

```yaml
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 100
AllowShortFunctionsOnASingleLine: None
AllowShortIfStatementsOnASingleLine: false
AllowShortLoopsOnASingleLine: false
```

## 测试说明

### 1. 单元测试

```bash
# 编译测试
cmake -DENABLE_TESTS=ON ..
cmake --build .

# 运行测试
ctest --output-on-failure

# 运行特定测试
ctest -R memory_pitfalls
```

### 2. 集成测试

```bash
# 编译所有示例
cmake --build .

# 运行所有示例并检查退出码
for bin in ./bin/*; do
    echo "Running $bin..."
    $bin || echo "FAILED: $bin"
done
```

### 3. 性能测试

```bash
# 编译性能测试
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .

# 运行性能测试
./bin/performance_test
```

## 文档生成

### 1. Doxygen

```bash
# 安装 Doxygen
sudo apt-get install doxygen

# 生成文档
doxygen Doxyfile

# 查看文档
open docs/html/index.html
```

### 2. Doxygen 配置

创建 `Doxyfile`：

```
PROJECT_NAME = "C++ Pitfalls and Best Practices"
OUTPUT_DIRECTORY = docs
INPUT = src/
RECURSIVE = YES
EXTRACT_ALL = YES
GENERATE_LATEX = NO
```

## 发布流程

### 1. 版本管理

```bash
# 更新版本号
# 在 CMakeLists.txt 中修改版本号
project(CppPitfallsBestPractices VERSION 1.1.0)

# 创建标签
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
```

### 2. 发布检查清单

- [ ] 所有代码可编译
- [ ] 所有测试通过
- [ ] 静态分析无严重警告
- [ ] 文档更新
- [ ] 版本号更新
- [ ] CHANGELOG 更新

### 3. 发布步骤

```bash
# 1. 更新版本号
# 2. 更新 CHANGELOG
# 3. 提交更改
git add .
git commit -m "Release version 1.1.0"

# 4. 创建标签
git tag -a v1.1.0 -m "Release version 1.1.0"

# 5. 推送到远程
git push origin main
git push origin v1.1.0

# 6. 创建 GitHub Release
gh release create v1.1.0 --title "Version 1.1.0" --notes "Release notes"
```

## 常见问题

### 1. 编译错误

#### 问题：找不到 C++17 特性
```
error: 'optional' is not a member of 'std'
```

**解决方案**：
```bash
# 确保使用 C++17 标准
cmake -DCMAKE_CXX_STANDARD=17 ..
```

#### 问题：链接错误
```
undefined reference to `std::filesystem::...'
```

**解决方案**：
```bash
# 链接 stdc++fs 库
target_link_libraries(target stdc++fs)
```

### 2. 运行错误

#### 问题：段错误
```
Segmentation fault (core dumped)
```

**解决方案**：
```bash
# 使用 GDB 调试
gdb ./program
(gdb) run
(gdb) backtrace
```

#### 问题：内存泄漏
```
ERROR: LeakSanitizer: detected memory leaks
```

**解决方案**：
```bash
# 使用 ASan 检测
g++ -fsanitize=address -g program.cpp
./a.out
```

### 3. 性能问题

#### 问题：编译时间过长

**解决方案**：
```bash
# 使用并行编译
cmake --build . -j$(nproc)

# 使用 ccache
export CC="ccache gcc"
export CXX="ccache g++"
```

## 贡献指南

### 1. 代码规范

- 遵循 Google C++ Style Guide
- 使用 4 空格缩进
- 行宽限制 100 字符
- 使用有意义的变量名

### 2. 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

### 3. Pull Request 流程

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到 Fork
5. 创建 Pull Request
6. 等待审查
7. 合并代码

## 工具推荐

### 1. IDE

| IDE | 平台 | 特点 |
|-----|------|------|
| Visual Studio Code | 跨平台 | 轻量、插件丰富 |
| CLion | 跨平台 | 功能强大 |
| Visual Studio | Windows | 集成度高 |
| Xcode | macOS | Apple 生态 |

### 2. 编辑器插件

- C/C++ (Microsoft)
- CMake Tools
- Clang-Format
- GitLens

### 3. 命令行工具

- `gdb` / `lldb`: 调试器
- `valgrind`: 内存检测
- `strace` / `ltrace`: 系统调用跟踪
- `perf`: 性能分析
