# C++ 构建系统和工具链 - 开发手册

## 1. 环境准备

### 1.1 Linux (Ubuntu/Debian)
```bash
# 安装基础工具
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build git

# 安装编译器
sudo apt-get install -y g++ clang

# 安装工具
sudo apt-get install -y clang-tidy cppcheck valgrind lcov

# 安装 Meson
pip3 install meson

# 安装 Conan
pip3 install conan

# 安装 vcpkg
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg && ./bootstrap-vcpkg.sh
```

### 1.2 macOS
```bash
# 安装 Xcode Command Line Tools
xcode-select --install

# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装工具
brew install cmake ninja gcc clang-format
brew install meson conan
```

### 1.3 Windows
```powershell
# 安装 Visual Studio 2022
# 安装 CMake
# 安装 Git

# 安装 vcpkg
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
```

## 2. 编译说明

### 2.1 CMake 项目编译
```bash
# 基本编译流程
cd <project-directory>
mkdir build && cd build
cmake ..
cmake --build .

# 使用 Ninja 后端
cmake -G Ninja ..
ninja

# 指定构建类型
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .

# 指定编译器
cmake -DCMAKE_CXX_COMPILER=clang++ ..
```

### 2.2 Meson 项目编译
```bash
cd meson-basics
meson setup build
meson compile -C build
```

### 2.3 Bazel 项目编译
```bash
cd bazel-basics
bazel build //...
```

### 2.4 xmake 项目编译
```bash
cd xmake-basics
xmake
```

### 2.5 Makefile 项目编译
```bash
cd makefile-basics
make
```

## 3. 运行方式

### 3.1 运行单个示例
```bash
# CMake 项目
cd cmake-basics/build
./hello_world

# Meson 项目
cd meson-basics/build
./hello_world
```

### 3.2 运行测试
```bash
# 使用 CTest
cd gtest-example/build
ctest --output-on-failure

# 直接运行测试
./run_tests
```

### 3.3 运行静态分析
```bash
# Clang-Tidy
cd clang-tidy-example/build
cmake --build . --target clang-tidy

# Cppcheck
cd cppcheck-example/build
cmake --build . --target cppcheck
```

### 3.4 运行动态分析
```bash
# AddressSanitizer
cd sanitizers-example/build
cmake -DENABLE_ASAN=ON ..
cmake --build .
./sanitizer_demo

# Valgrind
cd valgrind-example/build
valgrind --leak-check=full ./valgrind_demo
```

### 3.5 生成代码覆盖率
```bash
cd code-coverage/build
cmake -DENABLE_COVERAGE=ON ..
cmake --build .
ctest
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
# 打开 coverage_report/index.html 查看报告
```

## 4. 常见问题

### 4.1 CMake 版本过低
```
CMake Error: CMake was unable to find a build program corresponding to "Ninja"
```
解决方案：安装 Ninja 或使用 Make 生成器
```bash
sudo apt-get install ninja-build
# 或
cmake -G "Unix Makefiles" ..
```

### 4.2 编译器不支持 C++17
```
error: 'optional' is not a member of 'std'
```
解决方案：确保编译器版本足够新
```bash
g++ --version  # 需要 7+
clang++ --version  # 需要 5+
```

### 4.3 找不到第三方库
```
Could NOT find XXX (missing: XXX_DIR)
```
解决方案：使用包管理器安装或 FetchContent 拉取
```bash
# vcpkg
vcpkg install xxx

# Conan
conan install . --output-folder=build --build=missing
```

## 5. 工具链配置

### 5.1 GCC 工具链文件
```cmake
# toolchain-gcc.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_C_COMPILER gcc)
set(CMAKE_CXX_COMPILER g++)
set(CMAKE_CXX_FLAGS_INIT "-std=c++17")
```

### 5.2 Clang 工具链文件
```cmake
# toolchain-clang.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_CXX_FLAGS_INIT "-std=c++17")
```

### 5.3 交叉编译工具链文件
```cmake
# toolchain-arm.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_C_COMPILER arm-linux-gnueabihf-gcc)
set(CMAKE_CXX_COMPILER arm-linux-gnueabihf-g++)
set(CMAKE_FIND_ROOT_PATH /usr/arm-linux-gnueabihf)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```
