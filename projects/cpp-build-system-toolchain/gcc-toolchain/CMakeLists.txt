cmake_minimum_required(VERSION 3.16)

# ============================================================================
# GCC 工具链示例
# 本文件展示 GCC 编译器的选项和优化设置
# ============================================================================

project(GccToolchain
    VERSION 1.0.0
    DESCRIPTION "GCC 工具链示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. GCC 特定编译选项
# ============================================================================
add_executable(gcc_demo src/gcc_demo.cpp)

target_compile_options(gcc_demo PRIVATE
    # 基本警告
    -Wall
    -Wextra
    -Wpedantic

    # 额外警告
    -Wshadow
    -Wnon-virtual-dtor
    -Wold-style-cast
    -Wcast-align
    -Wunused
    -Woverloaded-virtual
    -Wconversion
    -Wsign-conversion
    -Wnull-dereference
    -Wdouble-promotion
    -Wformat=2

    # GCC 特有警告
    -Wmisleading-indentation
    -Wduplicated-cond
    -Wduplicated-branches
    -Wlogical-op
    -Wuseless-cast
)

# ============================================================================
# 2. 优化级别示例
# ============================================================================
# O0 - 无优化（调试）
# O1 - 基本优化
# O2 - 推荐优化级别
# O3 - 最大优化
# Os - 优化大小
# Ofast - 最大速度（可能不符合标准）

# ============================================================================
# 3. 链接选项
# ============================================================================
target_link_options(gcc_demo PRIVATE
    # 链接时优化
    # -flto

    # 显示所有警告
    # -Wl,--warn-common
)

# ============================================================================
# 4. Sanitizer 支持
# ============================================================================
option(ENABLE_ASAN "Enable AddressSanitizer" OFF)
option(ENABLE_UBSAN "Enable UndefinedBehaviorSanitizer" OFF)

if(ENABLE_ASAN)
    target_compile_options(gcc_demo PRIVATE -fsanitize=address -fno-omit-frame-pointer)
    target_link_options(gcc_demo PRIVATE -fsanitize=address)
endif()

if(ENABLE_UBSAN)
    target_compile_options(gcc_demo PRIVATE -fsanitize=undefined)
    target_link_options(gcc_demo PRIVATE -fsanitize=undefined)
endif()

# ============================================================================
# 5. 构建类型配置
# ============================================================================
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -DDEBUG")
set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG")
set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "-O2 -g -DNDEBUG")
set(CMAKE_CXX_FLAGS_MINSIZEREL "-Os -DNDEBUG")
