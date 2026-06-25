# 开发手册

## 环境准备

### 操作系统支持

| 操作系统 | 版本 | 编译器 | 状态 |
|----------|------|--------|------|
| Ubuntu | 20.04+ | GCC 9+, Clang 10+ | 推荐 |
| macOS | 11+ | Apple Clang 13+ | 支持 |
| Windows | 10+ | MSVC 2019+ | 支持 |

### 编译器要求

#### GCC
```bash
# 安装 GCC 11
sudo apt install gcc-11 g++-11

# 验证版本
gcc-11 --version
```

#### Clang
```bash
# 安装 Clang 14
sudo apt install clang-14

# 验证版本
clang-14 --version
```

#### MSVC
```
Visual Studio 2019 或 2022
安装 "C++ 桌面开发" 工作负载
```

### CMake

```bash
# 安装 CMake 3.15+
sudo apt install cmake

# 或从源码安装
wget https://github.com/Kitware/CMake/releases/download/v3.28.0/cmake-3.28.0-linux-x86_64.sh
chmod +x cmake-3.28.0-linux-x86_64.sh
sudo ./cmake-3.28.0-linux-x86_64.sh --prefix=/usr/local
```

### 包管理器

#### vcpkg（推荐）

```bash
# 克隆 vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
./bootstrap-vcpkg.sh

# 设置环境变量
export VCPKG_ROOT=/path/to/vcpkg
export PATH=$VCPKG_ROOT:$PATH
```

#### Conan

```bash
# 安装 Conan
pip install conan

# 验证安装
conan --version

# 创建默认配置
conan profile detect
```

## 编译说明

### 快速开始

```bash
# 克隆项目
git clone <repository-url>
cd cpp-third-party-libraries

# 创建构建目录
mkdir build && cd build

# 配置项目
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译所有示例
cmake --build . -j$(nproc)

# 运行示例
./bin/container_example
```

### 详细编译选项

#### CMake 选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `CMAKE_BUILD_TYPE` | Release | 构建类型 |
| `CMAKE_CXX_STANDARD` | 17 | C++ 标准 |
| `BUILD_CONTAINERS` | ON | 构建容器示例 |
| `BUILD_SERIALIZATION` | ON | 构建序列化示例 |
| `BUILD_NETWORKING` | ON | 构建网络示例 |
| `BUILD_CONCURRENCY` | ON | 构建并发示例 |
| `BUILD_TESTING` | ON | 构建测试示例 |
| `BUILD_LOGGING` | ON | 构建日志示例 |
| `BUILD_MATH` | ON | 构建数学示例 |
| `BUILD_GRAPHICS` | OFF | 构建图形示例 |
| `BUILD_UTILS` | ON | 构建工具示例 |

#### 使用 vcpkg

```bash
# 配置项目（使用 vcpkg）
cmake .. \
  -DCMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake \
  -DCMAKE_BUILD_TYPE=Release

# 编译
cmake --build . -j$(nproc)
```

#### 使用 Conan

```bash
# 安装依赖
conan install . --build=missing -s build_type=Release

# 配置项目
cmake .. \
  -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake \
  -DCMAKE_BUILD_TYPE=Release

# 编译
cmake --build . -j$(nproc)
```

#### 使用 FetchContent

```bash
# 直接配置（依赖会自动下载）
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
cmake --build . -j$(nproc)
```

### 单独编译示例

```bash
# 编译特定示例
cmake --build . --target boost_container_flat_map

# 编译特定目录的所有示例
cmake --build . --target containers
```

## 运行方式

### 运行单个示例

```bash
# 运行容器示例
./bin/boost_container_flat_map

# 运行序列化示例
./bin/protobuf_example

# 运行网络示例
./bin/cpp_httplib_server
```

### 运行所有示例

```bash
# 运行所有示例脚本
./run_all_examples.sh
```

### 测试运行

```bash
# 运行所有测试
ctest --output-on-failure

# 运行特定测试
ctest -R "boost_container*"
```

## 常见问题

### 1. 编译错误

#### 问题：找不到头文件
```
fatal error: xxx.h: No such file or directory
```

**解决方案**：
```bash
# 检查依赖是否安装
dpkg -l | grep libboost-dev

# 安装缺失的依赖
sudo apt install libboost-all-dev

# 或使用包管理器
vcpkg install boost
```

#### 问题：链接错误
```
undefined reference to `xxx'
```

**解决方案**：
```bash
# 检查库文件是否存在
find /usr -name "libboost_*"

# 确保链接了正确的库
target_link_libraries(my_target PRIVATE Boost::container)
```

#### 问题：C++ 标准不支持
```
error: 'xxx' is not a member of 'std'
```

**解决方案**：
```cmake
# 确保设置了正确的 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
```

### 2. 运行时错误

#### 问题：动态库找不到
```
error while loading shared libraries: libxxx.so
```

**解决方案**：
```bash
# 添加库路径
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# 或使用 rpath
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
```

#### 问题：段错误
```
Segmentation fault (core dumped)
```

**解决方案**：
```bash
# 使用调试模式编译
cmake .. -DCMAKE_BUILD_TYPE=Debug

# 使用 GDB 调试
gdb ./bin/example
(gdb) run
(gdb) bt
```

### 3. 性能问题

#### 问题：编译时间过长
```
解决方案：
1. 使用预编译头
2. 减少头文件依赖
3. 使用并行编译
4. 考虑使用 ccache
```

#### 问题：运行时性能差
```
解决方案：
1. 使用 Release 模式编译
2. 启用优化选项
3. 使用性能分析工具
4. 检查内存分配
```

## 开发工具

### 推荐 IDE

#### Visual Studio Code
```json
// .vscode/settings.json
{
    "cmake.configureOnOpen": true,
    "cmake.buildDirectory": "${workspaceFolder}/build",
    "C_Cpp.default.configurationProvider": "ms-vscode.cmake-tools"
}
```

#### CLion
```
1. 打开项目目录
2. 自动检测 CMakeLists.txt
3. 配置工具链和 CMake 选项
```

#### Visual Studio
```
1. 打开 CMakeLists.txt
2. 选择配置（x64-Release）
3. 生成缓存并编译
```

### 调试工具

#### GDB
```bash
# 编译调试版本
cmake .. -DCMAKE_BUILD_TYPE=Debug

# 运行调试器
gdb ./bin/example

# 常用命令
(gdb) break main      # 设置断点
(gdb) run             # 运行程序
(gdb) next            # 单步执行
(gdb) print var       # 打印变量
(gdb) backtrace       # 查看调用栈
(gdb) quit            # 退出
```

#### Valgrind
```bash
# 检查内存泄漏
valgrind --leak-check=full ./bin/example

# 检查性能
valgrind --tool=callgrind ./bin/example
kcachegrind callgrind.out.*
```

#### Sanitizers
```cmake
# 启用 AddressSanitizer
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -fno-omit-frame-pointer")

# 启用 UndefinedBehaviorSanitizer
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=undefined")
```

### 代码质量工具

#### Clang-Tidy
```bash
# 运行 clang-tidy
clang-tidy src/*.cpp -- -std=c++17 -I include
```

#### Cppcheck
```bash
# 运行 cppcheck
cppcheck --enable=all --std=c++17 src/
```

#### Include-What-You-Use
```bash
# 运行 iwyu
iwyu -- -std=c++17 src/*.cpp
```

## 贡献指南

### 代码风格

#### 命名规范
```
- 类名：PascalCase
- 函数名：camelCase 或 snake_case
- 变量名：snake_case
- 常量名：UPPER_SNAKE_CASE
- 文件名：snake_case
```

#### 代码格式
```cpp
// 使用 4 空格缩进
void example() {
    if (condition) {
        doSomething();
    }
}

// 大括号单独一行
void function()
{
    // 代码
}
```

#### 注释规范
```cpp
/**
 * @brief 函数简述
 * @details 函数详述
 * @param param 参数说明
 * @return 返回值说明
 */
int function(int param);
```

### 提交规范

#### Commit 消息格式
```
<类型>(<范围>): <主题>

<正文>

<脚注>
```

#### 类型
```
feat: 新功能
fix: 修复
docs: 文档
style: 格式
refactor: 重构
test: 测试
chore: 构建/工具
```

#### 示例
```
feat(containers): 添加 Boost.Container 示例

- 添加 flat_map 示例
- 添加 stable_vector 示例
- 添加 CMakeLists.txt

Closes #123
```

### Pull Request 流程

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到 Fork
5. 创建 Pull Request
6. 等待代码审查
7. 合并到主分支

## 持续集成

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y cmake libboost-all-dev
    
    - name: Configure
      run: cmake -B build -DCMAKE_BUILD_TYPE=Release
    
    - name: Build
      run: cmake --build build -j$(nproc)
    
    - name: Test
      run: cd build && ctest --output-on-failure
```

### Docker

```dockerfile
# Dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN cmake -B build -DCMAKE_BUILD_TYPE=Release
RUN cmake --build build -j$(nproc)

CMD ["./build/bin/example"]
```

## 版本发布

### 版本号规范

```
主版本.次版本.修订号 (Major.Minor.Patch)

- 主版本：不兼容的 API 变更
- 次版本：新增功能，向后兼容
- 修订号：Bug 修复
```

### 发布流程

1. 更新版本号
2. 更新 CHANGELOG
3. 创建 Git Tag
4. 构建发布包
5. 发布到 GitHub Releases

## 总结

本开发手册涵盖了：
1. 环境准备和依赖安装
2. 详细的编译说明
3. 运行和测试方法
4. 常见问题解决方案
5. 开发工具推荐
6. 贡献指南
7. 持续集成配置

遵循本手册，可以顺利地编译、运行和贡献本项目。