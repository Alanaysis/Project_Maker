# 05_DEVELOPMENT.md - 开发手册

## 环境配置

### 编译器安装

#### Ubuntu/Debian

```bash
# GCC 12 (推荐)
sudo apt update
sudo apt install g++-12

# Clang 16
sudo apt install clang-16

# 验证版本
g++-12 --version
clang++-16 --version
```

#### macOS

```bash
# 使用 Homebrew
brew install gcc@12
brew install llvm

# Xcode 自带的 Clang 通常版本较新
xcode-select --install
```

#### Windows

```bash
# Visual Studio 2022 (MSVC 19.29+)
# 下载 Visual Studio 2022 Community
# 安装时选择 "使用 C++ 的桌面开发"

# 或使用 MinGW-w64
# 下载 https://winlibs.com/
```

### CMake 安装

```bash
# Ubuntu
sudo apt install cmake

# macOS
brew install cmake

# Windows
# 下载 https://cmake.org/download/
```

---

## 编译说明

### 基本编译

```bash
cd projects/cpp20-features

# 创建构建目录
mkdir -p build && cd build

# 配置（指定编译器）
cmake .. -DCMAKE_CXX_COMPILER=g++-12

# 编译所有示例
make -j$(nproc)

# 或者使用 Ninja（更快）
cmake .. -G Ninja -DCMAKE_CXX_COMPILER=g++-12
ninja
```

### 编译单个示例

```bash
# 只编译 concepts 示例
make 01_concepts

# 编译并运行
make 01_concepts && ./01_concepts
```

### 指定编译器

```bash
# 使用 GCC
cmake .. -DCMAKE_CXX_COMPILER=g++-12

# 使用 Clang
cmake .. -DCMAKE_CXX_COMPILER=clang++-16

# 使用 MSVC (Windows)
cmake .. -G "Visual Studio 17 2022"
```

---

## 运行方式

### 运行单个示例

```bash
cd build

# 运行概念示例
./01_concepts

# 运行范围示例
./02_ranges

# 运行协程示例
./03_coroutines
```

### 运行所有测试

```bash
cd build

# 使用 CTest 运行所有测试
ctest --output-on-failure

# 详细输出
ctest -V

# 运行特定测试
ctest -R concepts
```

### 一键编译运行

```bash
# 编译并运行所有示例
cd build && cmake .. && make -j$(nproc) && ctest --output-on-failure
```

---

## 调试

### 使用 GDB

```bash
# 编译时添加调试信息
cmake .. -DCMAKE_BUILD_TYPE=Debug
make 01_concepts

# 使用 GDB 调试
gdb ./01_concepts
(gdb) break main
(gdb) run
(gdb) next
(gdb) print variable
```

### 使用 LLDB (macOS)

```bash
lldb ./01_concepts
(lldb) break set --name main
(lldb) run
(lldb) next
(lldb) print variable
```

### 使用 VS Code

1. 安装 C/C++ 扩展
2. 创建 `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug",
            "type": "cppdbg",
            "request": "launch",
            "program": "${workspaceFolder}/build/${fileBasenameNoExtension}",
            "args": [],
            "stopAtEntry": false,
            "cwd": "${workspaceFolder}/build",
            "environment": [],
            "externalConsole": false,
            "MIMode": "gdb",
            "setupCommands": [
                {
                    "description": "Enable pretty-printing",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": true
                }
            ],
            "preLaunchTask": "build",
            "miDebuggerPath": "/usr/bin/gdb"
        }
    ]
}
```

---

## 常见问题

### Q1: 编译错误 "concepts is not a module"

**原因**：编译器版本太旧，不支持 C++20 Concepts。

**解决**：升级到 GCC 10+ 或 Clang 10+。

### Q2: 编译错误 "std::format is not a member of std"

**原因**：编译器版本不支持 std::format。

**解决**：
- GCC: 升级到 13+
- Clang: 升级到 17+
- 或使用 {fmt} 库作为替代

### Q3: 协程编译错误

**原因**：需要添加编译器标志。

**解决**：
```bash
# GCC
cmake .. -DCMAKE_CXX_FLAGS="-fcoroutines"

# Clang 通常默认支持
```

### Q4: 模块编译失败

**原因**：模块支持在不同编译器上差异较大。

**解决**：本项目暂未包含模块示例（04），因为编译器支持不一致。

---

## 代码规范

### 命名规范

- 函数：`snake_case`
- 类型：`PascalCase`
- 常量：`UPPER_SNAKE_CASE`
- 文件：`数字_特性名.cpp`

### 注释规范

```cpp
/**
 * 文件名.cpp - 特性名称
 *
 * 简要描述
 *
 * 核心要点：
 * 1. 要点一
 * 2. 要点二
 */

// ============================================================
// 1. 分节标题
// ============================================================

void function() {
    // 行内注释
}
```

### 代码风格

- 使用 4 空格缩进
- 每行不超过 100 字符
- 函数之间空一行
- 使用 `auto` 减少冗余类型声明
