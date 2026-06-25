# 开发手册

## 1. 开发环境

### 1.1 系统要求

**操作系统**
- Linux (推荐 Ubuntu 20.04+, Fedora 32+)
- macOS (10.15+)
- Windows (需要 MinGW 或 WSL)

**编译器**
- GCC 7+ (推荐 GCC 9+)
- Clang 5+ (推荐 Clang 10+)
- MSVC 2017+ (Visual Studio 2017+)

**构建工具**
- CMake 3.16+
- Make 或 Ninja

**其他工具**
- Git (版本控制)
- GDB 或 LLDB (调试)
- Valgrind (内存检查，仅 Linux)

### 1.2 安装依赖

**Ubuntu/Debian**
```bash
sudo apt update
sudo apt install build-essential cmake git
sudo apt install gdb valgrind  # 可选
```

**Fedora/RHEL**
```bash
sudo dnf install gcc-c++ cmake git
sudo dnf install gdb valgrind  # 可选
```

**macOS**
```bash
# 安装 Xcode 命令行工具
xcode-select --install

# 安装 CMake (使用 Homebrew)
brew install cmake

# 安装 GDB (可选)
brew install gdb
```

**Windows (使用 MSYS2)**
```bash
# 安装 MSYS2: https://www.msys2.org/
# 在 MSYS2 终端中运行：
pacman -S mingw-w64-x86_64-gcc
pacman -S mingw-w64-x86_64-cmake
pacman -S mingw-w64-x86_64-make
```

### 1.3 IDE 配置

**VS Code**
```json
// .vscode/settings.json
{
    "C_Cpp.default.cppStandard": "c++17",
    "C_Cpp.default.configurationProvider": "ms-vscode.cmake-tools",
    "cmake.buildDirectory": "${workspaceFolder}/build",
    "cmake.configureOnOpen": true
}
```

**CLion**
- 打开项目目录
- 自动检测 CMakeLists.txt
- 配置工具链

**Vim/Neovim**
```vim
" 使用 coc.nvim 或 YouCompleteMe
" 配置 compile_commands.json
set makeprg=cmake\ --build\ build
```

## 2. 编译说明

### 2.1 基本编译

```bash
# 进入项目目录
cd projects/simple-compiler

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake ..

# 编译项目
make -j$(nproc)
```

### 2.2 编译选项

**Debug 模式**
```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
```
- 包含调试信息
- 不优化
- 启用断言

**Release 模式**
```bash
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
```
- 优化代码
- 移除调试信息
- 更好的性能

**RelWithDebInfo 模式**
```bash
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..
make -j$(nproc)
```
- 优化代码
- 保留调试信息
- 适合性能分析

### 2.3 自定义选项

**指定编译器**
```bash
# 使用 GCC
cmake -DCMAKE_CXX_COMPILER=g++ ..

# 使用 Clang
cmake -DCMAKE_CXX_COMPILER=clang++ ..
```

**指定安装路径**
```bash
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..
make install
```

**启用/禁用测试**
```bash
# 启用测试（默认）
cmake -DBUILD_TESTS=ON ..

# 禁用测试
cmake -DBUILD_TESTS=OFF ..
```

### 2.4 使用 Ninja

```bash
# 使用 Ninja 替代 Make
cmake -G Ninja ..
ninja
```

### 2.5 交叉编译

```bash
# 创建工具链文件
cat > toolchain.cmake << EOF
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(CMAKE_C_COMPILER arm-linux-gnueabihf-gcc)
set(CMAKE_CXX_COMPILER arm-linux-gnueabihf-g++)

set(CMAKE_FIND_ROOT_PATH /usr/arm-linux-gnueabihf)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
EOF

# 使用工具链文件
cmake -DCMAKE_TOOLCHAIN_FILE=toolchain.cmake ..
```

## 3. 运行方式

### 3.1 基本运行

**运行编译器**
```bash
# 运行程序
./bin/simple_compiler program.simp

# 交互式模式
./bin/simple_compiler

# 查看帮助
./bin/simple_compiler --help
```

**运行计算器**
```bash
# 命令行模式
./bin/calculator "2 + 3 * 4"

# 交互式模式
./bin/calculator
```

**运行脚本解释器**
```bash
# 运行脚本文件
./bin/script_interpreter examples/fibonacci.simp

# 交互式模式
./bin/script_interpreter
```

**运行 DSL 示例**
```bash
./bin/dsl_example
```

### 3.2 调试选项

**查看词法分析结果**
```bash
./bin/simple_compiler --lex program.simp
```

**查看语法树**
```bash
./bin/simple_compiler --parse program.simp
```

**查看语义分析**
```bash
./bin/simple_compiler --semantic program.simp
```

**查看中间代码**
```bash
./bin/simple_compiler --ir program.simp
```

**查看优化后的代码**
```bash
./bin/simple_compiler --optimize program.simp
```

**查看生成的汇编**
```bash
./bin/simple_compiler --codegen program.simp
```

**查看所有阶段**
```bash
./bin/simple_compiler --all program.simp
```

### 3.3 交互式模式

**启动 REPL**
```bash
./bin/simple_compiler
```

**使用示例**
```
Simple Compiler REPL v1.0
Type 'exit' or 'quit' to exit.

>>> let x = 10;
>>> let y = 20;
>>> print(x + y);
30
>>> fn add(a, b) { return a + b; }
>>> print(add(3, 4));
7
>>> exit
Goodbye!
```

### 3.4 评估表达式

```bash
./bin/simple_compiler -e "2 + 3 * 4"
```

## 4. 测试

### 4.1 运行测试

**运行所有测试**
```bash
cd build
ctest
```

**运行特定测试**
```bash
./bin/compiler_tests
```

**详细输出**
```bash
ctest --verbose
```

### 4.2 测试类型

**单元测试**
```bash
# 词法分析器测试
./bin/compiler_tests test_lexer

# 语法分析器测试
./bin/compiler_tests test_parser

# 解释器测试
./bin/compiler_tests test_interpreter
```

**集成测试**
```bash
# 测试完整编译流程
./bin/simple_compiler --all examples/hello.simp
```

**性能测试**
```bash
# 测试编译速度
time ./bin/simple_compiler examples/fibonacci.simp

# 测试执行速度
time ./bin/script_interpreter examples/fibonacci.simp
```

### 4.3 编写测试

**测试文件结构**
```cpp
#include "lexer.hpp"
#include "parser.hpp"
#include "interpreter.hpp"
#include <iostream>
#include <cassert>

using namespace compiler;

void test_feature_name() {
    std::cout << "Testing feature..." << std::endl;
    
    // 测试代码
    Lexer lexer("let x = 10;");
    auto tokens = lexer.tokenize();
    
    // 断言
    assert(tokens.size() > 0);
    assert(tokens[0].type == TokenType::LET);
    
    std::cout << "  Passed!" << std::endl;
}

int main() {
    test_feature_name();
    return 0;
}
```

### 4.4 测试覆盖

**检查测试覆盖**
```bash
# 编译时启用覆盖率
cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="--coverage" ..
make -j$(nproc)

# 运行测试
ctest

# 生成覆盖率报告
gcov src/*.cpp
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 5. 调试

### 5.1 使用 GDB

**启动 GDB**
```bash
gdb ./bin/simple_compiler
```

**常用命令**
```
(gdb) break main          # 设置断点
(gdb) run program.simp    # 运行程序
(gdb) next                # 单步执行
(gdb) step                # 进入函数
(gdb) print variable      # 打印变量
(gdb) backtrace           # 查看调用栈
(gdb) continue            # 继续执行
(gdb) quit                # 退出
```

**调试特定函数**
```bash
(gdb) break Lexer::nextToken
(gdb) run
```

**查看 AST**
```bash
(gdb) break Parser::parse
(gdb) run
(gdb) print ast->print()
```

### 5.2 使用 LLDB

**启动 LLDB**
```bash
lldb ./bin/simple_compiler
```

**常用命令**
```
(lldb) breakpoint set --name main
(lldb) run program.simp
(lldb) next
(lldb) step
(lldb) print variable
(lldb) bt
(lldb) continue
(lldb) quit
```

### 5.3 使用 Valgrind

**内存检查**
```bash
valgrind --leak-check=full ./bin/simple_compiler program.simp
```

**性能分析**
```bash
valgrind --tool=callgrind ./bin/simple_compiler program.simp
callgrind_annotate callgrind.out.*
```

### 5.4 调试技巧

**添加调试输出**
```cpp
#ifdef DEBUG
std::cout << "DEBUG: " << variable << std::endl;
#endif
```

**使用断言**
```cpp
assert(condition && "Error message");
```

**日志系统**
```cpp
enum class LogLevel { DEBUG, INFO, WARNING, ERROR };

void log(LogLevel level, const std::string& message) {
    if (level >= currentLogLevel) {
        std::cerr << "[" << levelToString(level) << "] " << message << std::endl;
    }
}
```

## 6. 代码规范

### 6.1 命名规范

**类名**：PascalCase
```cpp
class Lexer { };
class Parser { };
class SemanticAnalyzer { };
```

**函数名**：camelCase
```cpp
Token nextToken();
ExprPtr parseExpression();
void analyzeStatement();
```

**变量名**：camelCase
```cpp
int currentLine;
std::string sourceCode;
TokenType tokenType;
```

**常量**：UPPER_SNAKE_CASE
```cpp
const int MAX_TOKEN_LENGTH = 100;
const std::string VERSION = "1.0.0";
```

**枚举值**：UPPER_SNAKE_CASE
```cpp
enum class TokenType {
    INTEGER,
    FLOAT,
    STRING,
    IDENTIFIER
};
```

### 6.2 代码格式

**缩进**：4个空格
```cpp
void function() {
    if (condition) {
        doSomething();
    }
}
```

**行宽**：80字符（推荐），120字符（最大）

**括号风格**：K&R风格
```cpp
if (condition) {
    // ...
} else {
    // ...
}

void function() {
    // ...
}
```

**空格**
```cpp
// 运算符周围
int x = a + b;

// 逗号后
function(a, b, c);

// 控制语句后
if (condition) {
    // ...
}
```

### 6.3 注释规范

**文件头注释**
```cpp
/**
 * @file lexer.hpp
 * @brief 词法分析器
 * @author Your Name
 * @date 2024-01-01
 */
```

**类注释**
```cpp
/**
 * 词法分析器
 * 
 * 将源代码字符串转换为token流
 */
class Lexer {
    // ...
};
```

**函数注释**
```cpp
/**
 * 获取下一个token
 * 
 * @return 下一个token
 * @throws LexerError 如果遇到非法字符
 */
Token nextToken();
```

**行内注释**
```cpp
// 跳过空白字符
while (isWhitespace(peek())) {
    advance();
}
```

### 6.4 头文件规范

**Include Guard**
```cpp
#pragma once
// 或
#ifndef LEXER_HPP
#define LEXER_HPP
// ...
#endif
```

**Include 顺序**
```cpp
// 1. 对应的头文件
#include "lexer.hpp"

// 2. 系统头文件
#include <string>
#include <vector>
#include <memory>

// 3. 第三方库头文件
// ...

// 4. 项目内头文件
#include "token.hpp"
#include "ast.hpp"
```

## 7. 版本控制

### 7.1 Git 工作流

**分支策略**
- `main`：稳定版本
- `develop`：开发分支
- `feature/*`：功能分支
- `bugfix/*`：修复分支

**提交规范**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**
- `feat`：新功能
- `fix`：修复
- `docs`：文档
- `style`：格式
- `refactor`：重构
- `test`：测试
- `chore`：构建

**示例**
```
feat(lexer): add string literal support

- Add string token type
- Handle escape sequences
- Support multi-line strings

Closes #123
```

### 7.2 代码审查

**审查清单**
- [ ] 代码符合规范
- [ ] 测试覆盖充分
- [ ] 文档更新
- [ ] 性能考虑
- [ ] 错误处理

**审查流程**
1. 创建 Pull Request
2. 自动化测试
3. 人工审查
4. 合并代码

## 8. 持续集成

### 8.1 GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y cmake build-essential
    
    - name: Configure
      run: cmake -B build -DCMAKE_BUILD_TYPE=Release
    
    - name: Build
      run: cmake --build build
    
    - name: Test
      run: cd build && ctest
```

### 8.2 本地 CI

```bash
# 运行所有检查
./scripts/ci.sh
```

**ci.sh 脚本**
```bash
#!/bin/bash
set -e

echo "=== Building ==="
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)

echo "=== Testing ==="
ctest --verbose

echo "=== Done ==="
```

## 9. 性能优化

### 9.1 编译优化

**CMake 优化选项**
```bash
# 启用优化
cmake -DCMAKE_BUILD_TYPE=Release ..

# 启用链接时优化
cmake -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON ..
```

**编译器特定优化**
```bash
# GCC
cmake -DCMAKE_CXX_FLAGS="-O3 -march=native" ..

# Clang
cmake -DCMAKE_CXX_FLAGS="-O3 -march=native -flto" ..
```

### 9.2 运行时优化

**内存优化**
- 使用移动语义
- 避免不必要的拷贝
- 使用内存池

**算法优化**
- 选择合适的数据结构
- 避免重复计算
- 使用缓存

**I/O 优化**
- 使用缓冲
- 批量处理
- 异步 I/O

### 9.3 性能分析

**使用 perf**
```bash
perf record ./bin/simple_compiler program.simp
perf report
```

**使用 gprof**
```bash
# 编译时启用分析
cmake -DCMAKE_CXX_FLAGS="-pg" ..
make

# 运行程序
./bin/simple_compiler program.simp

# 生成报告
gprof ./bin/simple_compiler gmon.out > analysis.txt
```

**使用 Valgrind Callgrind**
```bash
valgrind --tool=callgrind ./bin/simple_compiler program.simp
callgrind_annotate callgrind.out.* > analysis.txt
```

## 10. 故障排除

### 10.1 常见问题

**编译错误**
```
error: 'std::variant' is not a member of 'std'
```
解决方案：确保使用 C++17 或更高版本
```bash
cmake -DCMAKE_CXX_STANDARD=17 ..
```

**链接错误**
```
undefined reference to 'compiler::Lexer::tokenize()'
```
解决方案：确保所有源文件都编译并链接

**运行时错误**
```
Segmentation fault
```
解决方案：使用 GDB 调试，检查空指针和数组越界

### 10.2 调试技巧

**启用调试输出**
```cpp
#define DEBUG
#ifdef DEBUG
std::cout << "DEBUG: " << __FILE__ << ":" << __LINE__ << std::endl;
#endif
```

**使用 AddressSanitizer**
```bash
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address" ..
make
./bin/simple_compiler program.simp
```

**使用 UBSan**
```bash
cmake -DCMAKE_CXX_FLAGS="-fsanitize=undefined" ..
make
./bin/simple_compiler program.simp
```

### 10.3 获取帮助

**查看日志**
```bash
# 查看构建日志
make 2>&1 | tee build.log

# 查看测试日志
ctest --verbose 2>&1 | tee test.log
```

**社区支持**
- 提交 Issue
- 查看文档
- 搜索解决方案

## 11. 发布流程

### 11.1 版本号

**语义化版本**
- 主版本号：不兼容的 API 修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

**示例**
```
v1.0.0 - 初始版本
v1.1.0 - 添加新功能
v1.1.1 - 修复 bug
v2.0.0 - 不兼容的更改
```

### 11.2 发布步骤

1. 更新版本号
2. 更新 CHANGELOG
3. 运行所有测试
4. 创建 Git 标签
5. 构建发布包
6. 发布到 GitHub

**创建标签**
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

**构建发布包**
```bash
# 创建源码包
git archive --format=tar.gz --prefix=simple-compiler-1.0.0/ v1.0.0 > simple-compiler-1.0.0.tar.gz

# 创建二进制包
cmake -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
cpack
```

### 11.3 更新日志

**格式**
```markdown
# Changelog

## [1.0.0] - 2024-01-01

### Added
- 词法分析器
- 语法分析器
- 语义分析器
- 中间代码生成
- 代码优化
- 代码生成
- 解释器

### Changed
- 无

### Fixed
- 无
```

## 12. 总结

本开发手册涵盖了：

1. **环境配置**：系统要求、依赖安装、IDE 配置
2. **编译说明**：基本编译、编译选项、自定义配置
3. **运行方式**：基本运行、调试选项、交互式模式
4. **测试指南**：运行测试、编写测试、测试覆盖
5. **调试技巧**：GDB、LLDB、Valgrind
6. **代码规范**：命名规范、代码格式、注释规范
7. **版本控制**：Git 工作流、代码审查
8. **持续集成**：GitHub Actions、本地 CI
9. **性能优化**：编译优化、运行时优化、性能分析
10. **故障排除**：常见问题、调试技巧
11. **发布流程**：版本号、发布步骤、更新日志

通过遵循这些指南，可以高效地开发和维护编译器项目。

---

[返回首页](../README.md)
