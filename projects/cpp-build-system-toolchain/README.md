# C++ 构建系统和工具链

## 项目简介

本项目是一个全面的 C++ 构建系统和工具链学习库，涵盖主流构建系统、包管理器、编译器工具链、静态/动态分析工具、测试框架和 CI/CD 配置。每个工具都有独立的示例目录，配有详细注释和可运行的代码，适合 C++ 开发者系统学习现代构建工具链。

## 快速开始

```bash
# 克隆项目
cd projects/cpp-build-system-toolchain

# 编译 CMake 基础示例
cd cmake-basics
mkdir build && cd build
cmake ..
cmake --build .
./hello_world

# 编译 CMake 高级示例
cd ../../cmake-advanced
mkdir build && cd build
cmake ..
cmake --build .

# 运行测试
cd ../../gtest-example
mkdir build && cd build
cmake ..
cmake --build .
ctest --output-on-failure
```

## 工具分类

### 1. 构建系统

| 构建系统 | 目录 | 说明 |
|----------|------|------|
| CMake 基础 | cmake-basics/ | CMake 基本语法、目标管理、依赖管理 |
| CMake 高级 | cmake-advanced/ | Generator Expressions、Custom Commands、FetchContent |
| CMake Presets | cmake-presets/ | CMake Presets 配置管理 |
| Meson | meson-basics/ | Meson 构建系统基础 |
| Bazel | bazel-basics/ | Bazel 构建系统基础 |
| xmake | xmake-basics/ | xmake 构建系统基础 |
| SCons | scons-basics/ | SCons 构建系统基础 |
| Makefile | makefile-basics/ | Makefile 基础语法和规则 |

### 2. 包管理器

| 包管理器 | 目录 | 说明 |
|----------|------|------|
| vcpkg | vcpkg-example/ | Microsoft vcpkg 包管理器 |
| Conan | conan-example/ | Conan C++ 包管理器 |
| FetchContent | fetchcontent-example/ | CMake FetchContent 拉取依赖 |
| Git Submodule | git-submodule-example/ | Git 子模块管理依赖 |

### 3. 编译器工具链

| 工具链 | 目录 | 说明 |
|--------|------|------|
| GCC | gcc-toolchain/ | GCC 编译器选项和优化 |
| Clang | clang-toolchain/ | Clang 编译器选项和特性 |
| MSVC | msvc-toolchain/ | MSVC 编译器选项和配置 |
| 交叉编译 | cross-compile/ | 跨平台交叉编译配置 |

### 4. 静态分析

| 工具 | 目录 | 说明 |
|------|------|------|
| Clang-Tidy | clang-tidy-example/ | Clang-Tidy 静态分析配置和使用 |
| Cppcheck | cppcheck-example/ | Cppcheck 静态分析配置和使用 |

### 5. 动态分析

| 工具 | 目录 | 说明 |
|------|------|------|
| Sanitizers | sanitizers-example/ | ASan/TSan/MSan/UBSan 使用示例 |
| Valgrind | valgrind-example/ | Valgrind 内存检测使用示例 |

### 6. 测试框架

| 框架 | 目录 | 说明 |
|------|------|------|
| Google Test | gtest-example/ | Google Test 单元测试框架 |
| CTest | ctest-example/ | CMake CTest 测试集成 |
| 代码覆盖率 | code-coverage/ | gcov/lcov 代码覆盖率统计 |
| 模糊测试 | fuzzing-example/ | LibFuzzer/AFL 模糊测试 |

### 7. CI/CD

| 平台 | 目录 | 说明 |
|------|------|------|
| GitHub Actions | ci-github/ | GitHub Actions CI/CD 配置 |
| GitLab CI | ci-gitlab/ | GitLab CI/CD 配置 |
| Jenkins | ci-jenkins/ | Jenkins CI/CD Pipeline |

### 8. 项目模板

| 模板 | 目录 | 说明 |
|------|------|------|
| 现代 CMake 模板 | project-template/ | 完整的现代 CMake 项目结构 |

## 学习路径

### 初学者路径
1. **cmake-basics/** - 学习 CMake 基本语法
2. **makefile-basics/** - 理解 Makefile 基础
3. **gcc-toolchain/** - 了解 GCC 编译器
4. **gtest-example/** - 学习单元测试
5. **project-template/** - 使用项目模板

### 进阶路径
1. **cmake-advanced/** - 掌握 CMake 高级特性
2. **cmake-presets/** - 使用 CMake Presets
3. **vcpkg-example/** 或 **conan-example/** - 学习包管理
4. **clang-tidy-example/** - 配置静态分析
5. **sanitizers-example/** - 使用动态分析

### 高级路径
1. **cross-compile/** - 学习交叉编译
2. **fuzzing-example/** - 掌握模糊测试
3. **code-coverage/** - 配置代码覆盖率
4. **ci-github/** - 配置 CI/CD
5. **project-template/** - 构建完整项目模板

## 编译运行

### 前置要求

```bash
# Ubuntu/Debian
sudo apt-get install cmake g++ clang ninja-build

# macOS
brew install cmake gcc clang ninja

# Windows (使用 vcpkg)
# 安装 Visual Studio 2022 和 CMake
```

### 编译单个示例

```bash
# 使用 CMake
cd <example-directory>
mkdir build && cd build
cmake ..
cmake --build .

# 使用 Makefile
cd makefile-basics
make

# 使用 Meson
cd meson-basics
meson setup build
meson compile -C build

# 使用 Bazel
cd bazel-basics
bazel build //...

# 使用 xmake
cd xmake-basics
xmake
```

### 运行测试

```bash
# CTest
cd gtest-example
mkdir build && cd build
cmake ..
cmake --build .
ctest --output-on-failure

# 代码覆盖率
cd code-coverage
mkdir build && cd build
cmake -DENABLE_COVERAGE=ON ..
cmake --build .
ctest
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 目录结构

```
cpp-build-system-toolchain/
├── README.md                    # 本文件
├── 01_RESEARCH.md              # 市场调研
├── 02_REQUIREMENTS.md          # 需求分析
├── 03_DESIGN.md                # 技术设计
├── 05_DEVELOPMENT.md           # 开发手册
├── cmake-basics/               # CMake 基础
├── cmake-advanced/             # CMake 高级特性
├── cmake-presets/              # CMake Presets
├── meson-basics/               # Meson 构建系统
├── bazel-basics/               # Bazel 构建系统
├── xmake-basics/               # xmake 构建系统
├── scons-basics/               # SCons 构建系统
├── makefile-basics/            # Makefile 基础
├── vcpkg-example/              # vcpkg 包管理器
├── conan-example/              # Conan 包管理器
├── fetchcontent-example/       # CMake FetchContent
├── git-submodule-example/      # Git Submodule
├── gcc-toolchain/              # GCC 工具链
├── clang-toolchain/            # Clang 工具链
├── msvc-toolchain/             # MSVC 工具链
├── cross-compile/              # 交叉编译
├── clang-tidy-example/         # Clang-Tidy
├── cppcheck-example/           # Cppcheck
├── sanitizers-example/         # Sanitizers
├── valgrind-example/           # Valgrind
├── gtest-example/              # Google Test
├── ctest-example/              # CTest
├── code-coverage/              # 代码覆盖率
├── fuzzing-example/            # 模糊测试
├── ci-github/                  # GitHub Actions
├── ci-gitlab/                  # GitLab CI
├── ci-jenkins/                 # Jenkins
└── project-template/           # 现代 CMake 模板
```
