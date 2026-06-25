# C++ 技巧开发手册

## 1. 开发环境配置

### 1.1 编译器要求

#### GCC (GNU Compiler Collection)
- **最低版本**: GCC 10.0
- **推荐版本**: GCC 12.0+
- **安装方法**:
  ```bash
  # Ubuntu/Debian
  sudo apt update
  sudo apt install gcc-12 g++-12

  # CentOS/RHEL
  sudo yum install gcc-toolset-12

  # macOS
  brew install gcc@12
  ```

#### Clang
- **最低版本**: Clang 12.0
- **推荐版本**: Clang 15.0+
- **安装方法**:
  ```bash
  # Ubuntu/Debian
  sudo apt install clang-15

  # macOS (Xcode 自带)
  xcode-select --install

  # 或使用 LLVM 官方源
  wget https://apt.llvm.org/llvm.sh
  chmod +x llvm.sh
  sudo ./llvm.sh 15
  ```

#### MSVC (Microsoft Visual C++)
- **最低版本**: MSVC 2019 (16.0)
- **推荐版本**: MSVC 2022 (17.0+)
- **安装方法**:
  - 下载 Visual Studio 2022 Community
  - 选择 "使用 C++ 的桌面开发" 工作负载
  - 确保安装 Windows 10/11 SDK

### 1.2 构建工具

#### CMake
- **最低版本**: CMake 3.16
- **推荐版本**: CMake 3.20+
- **安装方法**:
  ```bash
  # Ubuntu/Debian
  sudo apt install cmake

  # macOS
  brew install cmake

  # Windows
  # 从 https://cmake.org/download/ 下载安装

  # 验证安装
  cmake --version
  ```

#### Make (可选)
- **用途**: Unix 系统的默认构建工具
- **安装方法**:
  ```bash
  # Ubuntu/Debian
  sudo apt install build-essential

  # macOS
  xcode-select --install
  ```

#### Ninja (可选)
- **用途**: 更快的构建工具
- **安装方法**:
  ```bash
  # Ubuntu/Debian
  sudo apt install ninja-build

  # macOS
  brew install ninja

  # 使用 Ninja 构建
  cmake -G Ninja ..
  ninja
  ```

### 1.3 开发工具

#### 代码编辑器

**Visual Studio Code (推荐)**
- 安装 C/C++ 扩展
- 安装 CMake Tools 扩展
- 配置 `settings.json`:
  ```json
  {
    "C_Cpp.default.cppStandard": "c++17",
    "cmake.configureOnOpen": true,
    "cmake.buildDirectory": "${workspaceFolder}/build"
  }
  ```

**CLion (专业选择)**
- 自动 CMake 支持
- 内置调试器
- 代码重构工具

**Vim/Neovim**
- 安装 coc.nvim 或 YouCompleteMe
- 配置 clangd 语言服务器

#### 调试工具

**GDB (GNU Debugger)**
```bash
# 安装
sudo apt install gdb

# 基本使用
gdb ./bin/type_trick_01
(gdb) break main
(gdb) run
(gdb) next
(gdb) print variable
(gdb) backtrace
```

**LLDB (LLVM Debugger)**
```bash
# 安装 (macOS 自带)
xcode-select --install

# 基本使用
lldb ./bin/type_trick_01
(lldb) breakpoint set --name main
(lldb) run
(lldb) next
(lldb) print variable
(lldb) bt
```

#### 静态分析工具

**Clang-Tidy**
```bash
# 安装
sudo apt install clang-tidy

# 使用
clang-tidy src/type_tricks/01_type_id.cpp -- -std=c++17
```

**Cppcheck**
```bash
# 安装
sudo apt install cppcheck

# 使用
cppcheck --enable=all src/
```

#### 内存分析工具

**Valgrind**
```bash
# 安装
sudo apt install valgrind

# 内存泄漏检查
valgrind --leak-check=full ./bin/type_trick_01

# 性能分析
valgrind --tool=callgrind ./bin/type_trick_01
callgrind_annotate callgrind.out.XXXXX
```

**AddressSanitizer**
```bash
# 编译时启用
g++ -fsanitize=address -g -o program program.cpp

# 运行
./program
```

### 1.4 环境验证

创建验证脚本 `scripts/verify_environment.sh`:

```bash
#!/bin/bash

echo "=== C++ 开发环境验证 ==="

# 检查编译器
echo "检查编译器..."
if command -v g++ &> /dev/null; then
    GCC_VERSION=$(g++ --version | head -n1)
    echo "✓ GCC: $GCC_VERSION"
else
    echo "✗ GCC 未安装"
fi

if command -v clang++ &> /dev/null; then
    CLANG_VERSION=$(clang++ --version | head -n1)
    echo "✓ Clang: $CLANG_VERSION"
else
    echo "✗ Clang 未安装"
fi

# 检查 CMake
echo "检查 CMake..."
if command -v cmake &> /dev/null; then
    CMAKE_VERSION=$(cmake --version | head -n1)
    echo "✓ CMake: $CMAKE_VERSION"
else
    echo "✗ CMake 未安装"
fi

# 检查 C++17 支持
echo "检查 C++17 支持..."
cat > /tmp/test_cpp17.cpp << 'EOF'
#include <iostream>
#include <optional>
#include <variant>
#include <any>

int main() {
    std::optional<int> opt = 42;
    std::variant<int, double> var = 3.14;
    std::any a = std::string("hello");
    std::cout << "C++17 支持正常" << std::endl;
    return 0;
}
EOF

if g++ -std=c++17 -o /tmp/test_cpp17 /tmp/test_cpp17.cpp 2>/dev/null; then
    echo "✓ C++17 支持正常"
    rm -f /tmp/test_cpp17
else
    echo "✗ C++17 支持异常"
fi

rm -f /tmp/test_cpp17.cpp

echo "=== 验证完成 ==="
```

## 2. 构建指南

### 2.1 快速开始

```bash
# 1. 克隆项目
git clone <repository-url>
cd cpp-tricks-and-tips

# 2. 创建构建目录
mkdir build && cd build

# 3. 配置项目
cmake ..

# 4. 编译所有技巧
cmake --build .

# 5. 运行示例
./bin/type_trick_01
```

### 2.2 详细构建步骤

#### 步骤 1: 获取源代码

```bash
# 克隆仓库
git clone <repository-url>
cd cpp-tricks-and-tips

# 查看项目结构
ls -la
```

#### 步骤 2: 配置构建系统

```bash
# 创建构建目录 (out-of-source 构建)
mkdir build
cd build

# 配置项目 (默认使用 Make)
cmake ..

# 或使用 Ninja (更快)
cmake -G Ninja ..

# 指定编译器
cmake -DCMAKE_CXX_COMPILER=g++-12 ..

# 指定构建类型
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake -DCMAKE_BUILD_TYPE=Debug ..

# 启用测试
cmake -DBUILD_TESTS=ON ..
```

#### 步骤 3: 编译项目

```bash
# 使用 Make 编译
cmake --build .

# 或指定并行编译数
cmake --build . -j$(nproc)

# 使用 Ninja 编译
ninja

# 编译特定目标
cmake --build . --target type_trick_01

# 查看所有可用目标
cmake --build . --target help
```

#### 步骤 4: 运行示例

```bash
# 运行特定技巧示例
./bin/type_trick_01
./bin/template_trick_03

# 运行所有测试
ctest

# 运行测试并显示输出
ctest --output-on-failure

# 运行特定测试
ctest -R type_trick
```

### 2.3 高级构建选项

#### 使用 Presets (CMake 3.19+)

创建 `CMakePresets.json`:
```json
{
  "version": 3,
  "configurePresets": [
    {
      "name": "default",
      "displayName": "Default Config",
      "generator": "Unix Makefiles",
      "binaryDir": "${sourceDir}/build",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release",
        "CMAKE_CXX_STANDARD": "17"
      }
    },
    {
      "name": "debug",
      "displayName": "Debug Config",
      "inherits": "default",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Debug"
      }
    },
    {
      "name": "ninja",
      "displayName": "Ninja Config",
      "generator": "Ninja",
      "inherits": "default"
    }
  ],
  "buildPresets": [
    {
      "name": "default",
      "configurePreset": "default"
    }
  ],
  "testPresets": [
    {
      "name": "default",
      "configurePreset": "default",
      "output": {
        "outputOnFailure": true
      }
    }
  ]
}
```

使用方法:
```bash
# 配置
cmake --preset default

# 构建
cmake --build --preset default

# 测试
ctest --preset default
```

#### 交叉编译

创建工具链文件 `cmake/arm-toolchain.cmake`:
```cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR arm)

set(CMAKE_C_COMPILER arm-linux-gnueabihf-gcc)
set(CMAKE_CXX_COMPILER arm-linux-gnueabihf-g++)

set(CMAKE_FIND_ROOT_PATH /usr/arm-linux-gnueabihf)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

使用方法:
```bash
cmake -DCMAKE_TOOLCHAIN_FILE=cmake/arm-toolchain.cmake ..
```

### 2.4 构建问题排查

#### 常见问题

**问题 1: CMake 版本过低**
```
CMake Error: CMake 3.16 or higher is required.
```
**解决方案**: 升级 CMake 到 3.16+

**问题 2: 编译器不支持 C++17**
```
error: 'optional' is not a member of 'std'
```
**解决方案**: 使用支持 C++17 的编译器版本

**问题 3: 找不到头文件**
```
fatal error: common.hpp: No such file or directory
```
**解决方案**: 确保 include 目录正确配置

**问题 4: 链接错误**
```
undefined reference to `pthread_create'
```
**解决方案**: 链接 pthread 库 `-lpthread`

#### 调试构建问题

```bash
# 查看详细构建信息
cmake --build . --verbose

# 查看 CMake 配置
cmake -L ..

# 清理并重新构建
rm -rf build/*
cd build
cmake ..
cmake --build .
```

## 3. 开发流程

### 3.1 添加新技巧

#### 步骤 1: 确定分类和编号

1. 确定技巧所属分类 (如 `type_tricks`)
2. 确定技巧编号 (如 `06`)
3. 确定技巧名称 (如 `type_erasure`)

#### 步骤 2: 创建源文件

在对应目录创建文件 `src/type_tricks/06_type_erasure.cpp`:

```cpp
/**
 * @file 06_type_erasure.cpp
 * @brief 类型擦除技巧演示
 * @author Your Name
 * @date 2024
 *
 * 本文件演示 C++ 类型擦除技术。
 *
 * 技巧要点:
 * 1. 类型擦除的基本概念
 * 2. 使用虚函数实现类型擦除
 * 3. 使用 std::function 实现类型擦除
 * 4. 自定义类型擦除容器
 *
 * 应用场景:
 * - 实现类型无关的容器
 * - 回调函数存储
 * - 接口抽象
 *
 * 编译命令:
 * g++ -std=c++17 -o type_erasure 06_type_erasure.cpp
 */

#include <iostream>
#include <memory>
#include <vector>
#include <functional>

// ... 实现代码 ...

int main() {
    std::cout << "C++ 类型擦除技巧演示\n" << std::endl;

    // ... 示例代码 ...

    return 0;
}

/*
 * 编译和运行:
 *
 * g++ -std=c++17 -o type_erasure 06_type_erasure.cpp
 * ./type_erasure
 *
 * 注意事项:
 * 1. 类型擦除会带来一定的性能开销
 * 2. 需要权衡类型安全和灵活性
 * 3. 考虑使用模板作为替代方案
 */
```

#### 步骤 3: 更新 CMakeLists.txt

编辑 `src/type_tricks/CMakeLists.txt`:

```cmake
# 添加新的技巧目标
add_executable(type_trick_06 06_type_erasure.cpp)
target_link_libraries(type_trick_06 PRIVATE common_utils)

# 添加到测试
add_test(NAME type_trick_06 COMMAND type_trick_06)
```

#### 步骤 4: 更新文档

更新 `src/type_tricks/README.md`:

```markdown
| 06 | 类型擦除 | 06_type_erasure.cpp | ⭐⭐⭐ | 类型擦除技术 |
```

更新主 `README.md` 的技巧列表。

#### 步骤 5: 测试和验证

```bash
# 重新构建
cd build
cmake --build . --target type_trick_06

# 运行测试
ctest -R type_trick_06 --output-on-failure

# 静态分析
clang-tidy ../src/type_tricks/06_type_erasure.cpp -- -std=c++17
```

### 3.2 添加新分类

#### 步骤 1: 创建目录结构

```bash
mkdir -p src/new_category
```

#### 步骤 2: 创建 CMakeLists.txt

创建 `src/new_category/CMakeLists.txt`:

```cmake
# 新分类技巧

# 01: 技巧名称
add_executable(new_trick_01 01_trick_name.cpp)
target_link_libraries(new_trick_01 PRIVATE common_utils)

# 添加到测试
add_test(NAME new_trick_01 COMMAND new_trick_01)
```

#### 步骤 3: 创建 README.md

创建 `src/new_category/README.md`:

```markdown
# 新分类 (New Category)

## 概述

本目录包含 C++ 新分类技巧。

## 技巧列表

| 编号 | 技巧名称 | 文件名 | 难度 | 描述 |
|------|----------|--------|------|------|
| 01 | 技巧名称 | 01_trick_name.cpp | ⭐⭐ | 技巧描述 |

## 学习建议

1. 学习建议 1
2. 学习建议 2

## 编译和运行

```bash
g++ -std=c++17 -o trick 01_trick_name.cpp
./trick
```
```

#### 步骤 4: 更新主 CMakeLists.txt

编辑主 `CMakeLists.txt`:

```cmake
add_subdirectory(src/new_category)
```

#### 步骤 5: 更新主 README.md

更新项目的分类列表。

### 3.3 代码风格指南

#### 命名规范

```cpp
// 命名空间: snake_case
namespace cpp_tricks {

// 类名: PascalCase
class ScopedTimer {
public:
    // 公有成员函数: snake_case
    void start_timer();

private:
    // 私有成员变量: snake_case + 尾下划线
    std::string name_;
    int count_;
};

// 函数名: snake_case
void print_info(const std::string& message);

// 变量名: snake_case
int local_variable = 42;

// 常量: UPPER_SNAKE_CASE
const int MAX_BUFFER_SIZE = 1024;

// 模板参数: PascalCase
template <typename ElementType>
class Container {};

} // namespace cpp_tricks
```

#### 代码组织

```cpp
// 1. 文件头注释
/**
 * @file filename.cpp
 * @brief 简要描述
 * @author 作者
 * @date 日期
 */

// 2. 包含头文件 (按顺序)
#include "corresponding_header.hpp"  // 对应头文件

#include <cstdio>      // C 系统头文件
#include <cstring>

#include <iostream>     // C++ 标准库
#include <vector>
#include <string>

#include <third_party/library.hpp>  // 第三方库

#include "project_header.hpp"  // 项目内头文件

// 3. 命名空间
namespace cpp_tricks {

// 4. 常量定义
constexpr int kMaxSize = 1024;

// 5. 类型定义
using StringVector = std::vector<std::string>;

// 6. 辅助函数
namespace {

void helper_function() {
    // 实现
}

} // anonymous namespace

// 7. 主要实现
void main_function() {
    // 实现
}

} // namespace cpp_tricks
```

#### 注释规范

```cpp
/**
 * @brief 函数简要描述
 *
 * 详细描述函数的功能、参数、返回值等。
 *
 * @param param1 参数1描述
 * @param param2 参数2描述
 * @return 返回值描述
 * @throw exception_type 异常描述
 *
 * @code
 * // 使用示例
 * int result = function(1, 2);
 * @endcode
 *
 * @note 注意事项
 * @warning 警告信息
 * @see 相关函数或类
 */
int function(int param1, int param2);

// 行内注释: 解释复杂逻辑
int result = complex_calculation();  // 计算结果

// TODO 注释
// TODO: 实现此功能

// FIXME 注释
// FIXME: 修复此 Bug

// HACK 注释
// HACK: 临时解决方案
```

### 3.4 版本控制

#### Git 工作流

```bash
# 1. 克隆仓库
git clone <repository-url>
cd cpp-tricks-and-tips

# 2. 创建特性分支
git checkout -b feature/new-trick

# 3. 开发和提交
git add src/type_tricks/06_type_erasure.cpp
git commit -m "feat: 添加类型擦除技巧"

# 4. 推送到远程
git push origin feature/new-trick

# 5. 创建 Pull Request
# 在 GitHub 上创建 PR

# 6. 代码审查和合并
# 审查通过后合并到主分支
```

#### 提交规范

使用 Conventional Commits 规范:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(type_tricks): 添加类型擦除技巧

- 实现基本类型擦除
- 添加使用示例
- 更新文档

Closes #123
```

#### 分支管理

```
main (主分支)
├── develop (开发分支)
│   ├── feature/new-trick-1
│   ├── feature/new-trick-2
│   └── feature/new-category
├── release/v1.0 (发布分支)
└── hotfix/critical-bug (热修复分支)
```

## 4. 测试指南

### 4.1 测试策略

#### 单元测试
- 测试每个工具函数
- 测试边界条件
- 测试异常情况

#### 集成测试
- 测试技巧示例能否正确运行
- 测试技巧之间的兼容性

#### 性能测试
- 测试关键技巧的性能
- 建立性能基准

### 4.2 测试框架配置

#### Google Test 配置

在 `tests/CMakeLists.txt` 中:

```cmake
# 查找 Google Test
find_package(GTest REQUIRED)

# 添加测试可执行文件
add_executable(test_type_tricks test_type_tricks.cpp)
target_link_libraries(test_type_tricks
    PRIVATE
    GTest::gtest
    GTest::gtest_main
    common_utils
)

# 添加测试
add_test(NAME test_type_tricks COMMAND test_type_tricks)
```

#### 使用 FetchContent 获取 Google Test

```cmake
include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.12.1
)

# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(googletest)
```

### 4.3 编写测试

#### 测试文件模板

```cpp
/**
 * @file test_type_tricks.cpp
 * @brief 类型技巧单元测试
 */

#include <gtest/gtest.h>
#include "type_utils.hpp"

// 测试夹具
class TypeTricksTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 测试前准备
    }

    void TearDown() override {
        // 测试后清理
    }
};

// 测试用例
TEST_F(TypeTricksTest, TypeNameBasic) {
    // 测试基本类型名称
    EXPECT_EQ(cpp_tricks::type_name<int>(), "int");
    EXPECT_EQ(cpp_tricks::type_name<double>(), "double");
}

TEST_F(TypeTricksTest, TypeNameCustom) {
    // 测试自定义类型名称
    struct MyStruct {};
    EXPECT_FALSE(cpp_tricks::type_name<MyStruct>().empty());
}

// 参数化测试
class TypeParamTest : public ::testing::TestWithParam<std::pair<int, std::string>> {};

TEST_P(TypeParamTest, TypeId) {
    auto [expected_hash, expected_name] = GetParam();
    // 测试逻辑
}

INSTANTIATE_TEST_SUITE_P(
    BasicTypes,
    TypeParamTest,
    ::testing::Values(
        std::make_pair(0, "int"),
        std::make_pair(1, "double")
    )
);

// 主函数
int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

### 4.4 运行测试

```bash
# 构建测试
cd build
cmake --build . --target test_type_tricks

# 运行所有测试
ctest

# 运行特定测试
ctest -R type_trick

# 显示详细输出
ctest --output-on-failure

# 运行特定测试可执行文件
./test_type_tricks

# 运行特定测试用例
./test_type_tricks --gtest_filter=TypeTricksTest.TypeNameBasic

# 列出所有测试用例
./test_type_tricks --gtest_list_tests
```

### 4.5 测试覆盖率

#### 安装 gcov 和 lcov

```bash
# Ubuntu/Debian
sudo apt install gcovr lcov

# macOS
brew install gcovr lcov
```

#### 生成覆盖率报告

```bash
# 编译时启用覆盖率
cd build
cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="--coverage" ..
cmake --build .

# 运行测试
ctest

# 生成报告
gcovr -r .. --html --html-details -o coverage.html

# 或使用 lcov
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 5. 文档编写指南

### 5.1 代码注释

#### 文件头注释

每个源文件必须包含文件头注释:

```cpp
/**
 * @file filename.cpp
 * @brief 简要描述
 * @author 作者名称
 * @date 创建日期
 *
 * 详细描述文件内容、技巧要点、应用场景等。
 */
```

#### 函数注释

每个函数必须包含 Doxygen 风格注释:

```cpp
/**
 * @brief 函数简要描述
 *
 * 详细描述函数功能。
 *
 * @param param1 参数1描述
 * @param param2 参数2描述
 * @return 返回值描述
 * @throw exception_type 异常描述
 */
```

#### 行内注释

复杂逻辑必须添加行内注释:

```cpp
// 使用 SFINAE 检测类型是否有 begin() 方法
template <typename T, typename = void>
struct has_begin : std::false_type {};

template <typename T>
struct has_begin<T, std::void_t<decltype(std::declval<T>().begin())>>
    : std::true_type {};
```

### 5.2 README 编写

#### 技巧 README 模板

```markdown
# 分类名称 (Category Name)

## 概述

简要描述本分类包含的技巧。

## 技巧列表

| 编号 | 技巧名称 | 文件名 | 难度 | 描述 |
|------|----------|--------|------|------|
| 01 | 技巧名称 | 01_trick.cpp | ⭐⭐ | 技巧描述 |

## 学习建议

1. 建议 1
2. 建议 2

## 编译和运行

```bash
# 编译单个技巧
g++ -std=c++17 -o trick 01_trick.cpp

# 运行
./trick
```

## 参考资源

- [链接名称](URL)
```

### 5.3 文档维护

#### 定期更新
- 每月检查文档准确性
- 更新过时的内容
- 补充新的示例

#### 版本同步
- 代码变更时同步更新文档
- 新增技巧时更新技巧列表
- 修复 Bug 时更新注意事项

## 6. 发布流程

### 6.1 版本号管理

使用语义化版本号 (Semantic Versioning):

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 修改
MINOR: 向下兼容的功能性新增
PATCH: 向下兼容的问题修正
```

示例:
- `1.0.0`: 初始发布版本
- `1.1.0`: 新增技巧分类
- `1.0.1`: Bug 修复

### 6.2 发布检查清单

#### 发布前检查

- [ ] 所有代码编译通过
- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新

#### 发布步骤

1. **创建发布分支**
   ```bash
   git checkout -b release/v1.0.0
   ```

2. **更新版本号**
   ```cmake
   project(cpp-tricks-and-tips VERSION 1.0.0 LANGUAGES CXX)
   ```

3. **更新 CHANGELOG**
   ```markdown
   # Changelog

   ## [1.0.0] - 2024-01-01

   ### Added
   - 初始版本发布
   - 包含 35 个 C++ 技巧
   ```

4. **提交和打标签**
   ```bash
   git add .
   git commit -m "release: v1.0.0"
   git tag -a v1.0.0 -m "Release v1.0.0"
   ```

5. **合并到主分支**
   ```bash
   git checkout main
   git merge release/v1.0.0
   git push origin main --tags
   ```

6. **创建 GitHub Release**
   - 在 GitHub 上创建新的 Release
   - 上传构建产物 (可选)
   - 编写 Release Notes

### 6.3 发布后工作

- 通知社区用户
- 更新文档网站 (如果有)
- 收集用户反馈
- 规划下一版本

## 7. 贡献指南

### 7.1 如何贡献

#### 报告问题

1. 使用 GitHub Issues 报告 Bug
2. 提供详细的问题描述
3. 包含复现步骤
4. 提供环境信息

#### 提交代码

1. Fork 项目仓库
2. 创建特性分支
3. 编写代码和测试
4. 提交 Pull Request

#### 改进文档

1. 修复文档错误
2. 补充缺失内容
3. 改进文档结构
4. 翻译文档

### 7.2 代码审查

#### 审查要点

- 代码风格是否符合规范
- 是否有编译警告
- 是否有内存泄漏
- 注释是否充分
- 测试是否完整

#### 审查流程

1. 提交 Pull Request
2. 自动化测试运行
3. 人工代码审查
4. 修改和重新审查
5. 合并到主分支

### 7.3 社区行为准则

- 尊重所有贡献者
- 建设性地提出意见
- 接受合理的批评
- 关注社区利益

## 8. 故障排除

### 8.1 编译问题

#### 问题: 编译器版本过低

**错误信息**:
```
error: 'optional' is not a member of 'std'
```

**解决方案**:
```bash
# 检查编译器版本
g++ --version

# 升级编译器
sudo apt install g++-12

# 使用新版本编译
cmake -DCMAKE_CXX_COMPILER=g++-12 ..
```

#### 问题: CMake 版本过低

**错误信息**:
```
CMake Error: CMake 3.16 or higher is required.
```

**解决方案**:
```bash
# 检查 CMake 版本
cmake --version

# 升级 CMake
sudo apt install cmake

# 或从源码安装最新版本
```

### 8.2 运行时问题

#### 问题: 段错误 (Segmentation Fault)

**调试方法**:
```bash
# 使用 GDB 调试
gdb ./bin/type_trick_01
(gdb) run
(gdb) backtrace

# 使用 AddressSanitizer
g++ -fsanitize=address -g -o program program.cpp
./program
```

#### 问题: 内存泄漏

**检测方法**:
```bash
# 使用 Valgrind
valgrind --leak-check=full ./bin/type_trick_01

# 使用 AddressSanitizer
g++ -fsanitize=leak -g -o program program.cpp
./program
```

### 8.3 构建问题

#### 问题: 找不到库

**错误信息**:
```
cannot find -lpthread
```

**解决方案**:
```cmake
# 在 CMakeLists.txt 中添加
target_link_libraries(your_target PRIVATE pthread)
```

#### 问题: 头文件路径错误

**错误信息**:
```
fatal error: common.hpp: No such file or directory
```

**解决方案**:
```cmake
# 确保包含目录正确
include_directories(${CMAKE_SOURCE_DIR}/include)
```

## 9. 性能优化指南

### 9.1 编译优化

#### 优化级别

```bash
# 无优化 (调试)
g++ -O0 -g -o program program.cpp

# 基本优化
g++ -O1 -o program program.cpp

# 推荐优化
g++ -O2 -o program program.cpp

# 最大优化
g++ -O3 -o program program.cpp

# 大小优化
g++ -Os -o program program.cpp
```

#### 链接时优化 (LTO)

```bash
# 启用 LTO
g++ -flto -O2 -o program program.cpp

# CMake 启用 LTO
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
```

### 9.2 运行时性能分析

#### 使用 Perf

```bash
# 安装 perf
sudo apt install linux-tools-common linux-tools-generic

# 记录性能数据
perf record -g ./bin/type_trick_01

# 分析性能数据
perf report

# 生成火焰图
perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

#### 使用 Valgrind Callgrind

```bash
# 运行 Callgrind
valgrind --tool=callgrind ./bin/type_trick_01

# 分析结果
callgrind_annotate callgrind.out.XXXXX
```

### 9.3 内存优化

#### 减少内存分配

```cpp
// 预分配内存
std::vector<int> vec;
vec.reserve(1000);  // 预分配

// 使用内存池
class MemoryPool {
    // 实现
};

// 使用小对象优化
class SmallBuffer {
    char buffer_[32];  // 栈上小缓冲区
    char* data_;
};
```

#### 避免内存碎片

```cpp
// 使用自定义分配器
template <typename T>
class PoolAllocator {
    // 实现
};

// 使用对象池
class ObjectPool {
    // 实现
};
```

## 10. 最佳实践总结

### 10.1 开发最佳实践

1. **遵循编码规范**: 保持代码风格一致
2. **编写清晰注释**: 解释复杂逻辑和设计决策
3. **进行代码审查**: 确保代码质量
4. **编写测试**: 保证代码正确性
5. **持续集成**: 自动化构建和测试

### 10.2 性能最佳实践

1. **测量再优化**: 使用性能分析工具
2. **避免过早优化**: 先保证正确性
3. **使用移动语义**: 减少不必要的拷贝
4. **优化数据结构**: 选择合适的数据结构
5. **利用缓存**: 提高数据局部性

### 10.3 维护最佳实践

1. **版本控制**: 使用 Git 管理代码
2. **文档同步**: 代码变更时更新文档
3. **定期重构**: 保持代码整洁
4. **技术债务**: 及时处理已知问题
5. **知识分享**: 团队内部技术交流
