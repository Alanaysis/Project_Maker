cmake_minimum_required(VERSION 3.16)

# ============================================================================
# 交叉编译示例
# 本文件展示如何配置 CMake 进行交叉编译
#
# 使用方法:
#   cmake -B build -DCMAKE_TOOLCHAIN_FILE=toolchain-arm.cmake
#   cmake --build build
# ============================================================================

project(CrossCompile
    VERSION 1.0.0
    DESCRIPTION "交叉编译示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 创建可执行文件
add_executable(cross_compile_demo src/cross_compile_demo.cpp)

# 创建库
add_library(mylib STATIC src/mylib.cpp)
target_include_directories(mylib PUBLIC include)

target_link_libraries(cross_compile_demo PRIVATE mylib)
