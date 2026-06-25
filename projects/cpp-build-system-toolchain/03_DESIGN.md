# C++ 构建系统和工具链 - 技术设计

## 1. 文件组织

### 1.1 整体结构
```
cpp-build-system-toolchain/
├── README.md                    # 项目总览
├── 01_RESEARCH.md              # 市场调研
├── 02_REQUIREMENTS.md          # 需求分析
├── 03_DESIGN.md                # 技术设计（本文件）
├── 05_DEVELOPMENT.md           # 开发手册
│
├── cmake-basics/               # CMake 基础
│   ├── CMakeLists.txt
│   ├── src/
│   │   ├── hello.cpp
│   │   └── math_utils.cpp
│   └── include/
│       └── math_utils.h
│
├── cmake-advanced/             # CMake 高级
│   ├── CMakeLists.txt
│   ├── generator-expressions/
│   ├── custom-commands/
│   └── external-projects/
│
├── cmake-presets/              # CMake Presets
│   ├── CMakeLists.txt
│   ├── CMakePresets.json
│   └── src/
│
├── meson-basics/               # Meson
│   ├── meson.build
│   └── src/
│
├── bazel-basics/               # Bazel
│   ├── BUILD
│   ├── WORKSPACE
│   └── src/
│
├── xmake-basics/               # xmake
│   ├── xmake.lua
│   └── src/
│
├── scons-basics/               # SCons
│   ├── SConstruct
│   └── src/
│
├── makefile-basics/            # Makefile
│   ├── Makefile
│   └── src/
│
├── vcpkg-example/              # vcpkg
│   ├── CMakeLists.txt
│   ├── vcpkg.json
│   └── src/
│
├── conan-example/              # Conan
│   ├── CMakeLists.txt
│   ├── conanfile.txt
│   └── src/
│
├── fetchcontent-example/       # FetchContent
│   ├── CMakeLists.txt
│   └── src/
│
├── git-submodule-example/      # Git Submodule
│   ├── CMakeLists.txt
│   └── third_party/
│
├── gcc-toolchain/              # GCC
│   ├── CMakeLists.txt
│   ├── toolchain-gcc.cmake
│   └── src/
│
├── clang-toolchain/            # Clang
│   ├── CMakeLists.txt
│   ├── toolchain-clang.cmake
│   └── src/
│
├── msvc-toolchain/             # MSVC
│   ├── CMakeLists.txt
│   └── src/
│
├── cross-compile/              # 交叉编译
│   ├── CMakeLists.txt
│   ├── toolchain-arm.cmake
│   └── src/
│
├── clang-tidy-example/         # Clang-Tidy
│   ├── CMakeLists.txt
│   ├── .clang-tidy
│   └── src/
│
├── cppcheck-example/           # Cppcheck
│   ├── CMakeLists.txt
│   └── src/
│
├── sanitizers-example/         # Sanitizers
│   ├── CMakeLists.txt
│   └── src/
│
├── valgrind-example/           # Valgrind
│   ├── CMakeLists.txt
│   └── src/
│
├── gtest-example/              # Google Test
│   ├── CMakeLists.txt
│   ├── src/
│   └── tests/
│
├── ctest-example/              # CTest
│   ├── CMakeLists.txt
│   └── tests/
│
├── code-coverage/              # 代码覆盖率
│   ├── CMakeLists.txt
│   └── src/
│
├── fuzzing-example/            # 模糊测试
│   ├── CMakeLists.txt
│   └── src/
│
├── ci-github/                  # GitHub Actions
│   └── .github/workflows/
│
├── ci-gitlab/                  # GitLab CI
│   └── .gitlab-ci.yml
│
├── ci-jenkins/                 # Jenkins
│   └── Jenkinsfile
│
└── project-template/           # 项目模板
    ├── CMakeLists.txt
    ├── cmake/
    ├── include/
    ├── src/
    └── tests/
```

## 2. 示例设计

### 2.1 CMake 基础示例
- **hello_world**: 最简单的 CMake 项目
- **library_example**: 静态库/动态库创建
- **multi_target**: 多目标管理
- **install_example**: 安装规则配置

### 2.2 CMake 高级示例
- **generator_expr**: Generator Expressions 使用
- **custom_command**: 自定义命令和目标
- **fetch_content**: FetchContent 拉取依赖
- **toolchain_file**: 工具链文件编写

### 2.3 包管理器示例
- **vcpkg_json**: vcpkg.json 配置
- **conanfile**: Conan 配置文件
- **fetch_dep**: FetchContent 拉取第三方库

### 2.4 编译器示例
- **optimization_levels**: 不同优化级别对比
- **warning_flags**: 编译器警告配置
- **sanitizer_flags**: Sanitizer 编译选项

### 2.5 测试示例
- **basic_test**: Google Test 基础
- **parameterized_test**: 参数化测试
- **mock_test**: Mock 测试
- **fixture_test**: 测试夹具

### 2.6 CI/CD 示例
- **multi_platform**: 多平台构建矩阵
- **code_quality**: 代码质量检查
- **release**: 自动发布流程

## 3. CMakeLists.txt 设计模式

### 3.1 现代 CMake 模式
```cmake
# 使用 target_* 命令而非全局命令
target_include_directories(mylib PUBLIC include)
target_link_libraries(myapp PRIVATE mylib)
target_compile_features(myapp PRIVATE cxx_std_17)

# 使用 Generator Expressions
target_compile_definitions(mylib PRIVATE
    $<$<CONFIG:Debug>:DEBUG_MODE>
    $<$<PLATFORM_ID:Windows>:WIN32>
)
```

### 3.2 依赖管理模式
```cmake
# FetchContent 模式
include(FetchContent)
FetchContent_Declare(
    fmt
    GIT_REPOSITORY https://github.com/fmtlib/fmt.git
    GIT_TAG 10.1.1
)
FetchContent_MakeAvailable(fmt)
```

## 4. 代码风格

### 4.1 C++ 代码风格
- 使用 C++17/20 标准
- 遵循 Google C++ Style Guide
- 使用 snake_case 命名
- 类名使用 PascalCase

### 4.2 CMake 代码风格
- 使用小写命令
- 每个目标独立配置
- 使用 `cmake_minimum_required` 指定最低版本
- 使用 `project()` 声明项目信息
