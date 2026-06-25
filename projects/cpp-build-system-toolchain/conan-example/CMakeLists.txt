cmake_minimum_required(VERSION 3.20)

# ============================================================================
# Conan 包管理器示例
# 本文件展示如何使用 Conan 管理 C++ 依赖
#
# 使用方法:
#   1. 安装依赖:
#      conan install . --output-folder=build --build=missing
#
#   2. 配置项目:
#      cd build && cmake .. -DCMAKE_TOOLCHAIN_FILE=conan_toolchain.cmake
#
#   3. 构建项目:
#      cmake --build build
# ============================================================================

project(ConanExample
    VERSION 1.0.0
    DESCRIPTION "Conan 包管理器示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找 Conan 安装的包
find_package(fmt REQUIRED)
find_package(spdlog REQUIRED)

# 创建可执行文件
add_executable(conan_demo src/conan_demo.cpp)

target_link_libraries(conan_demo
    PRIVATE
        fmt::fmt
        spdlog::spdlog
)
