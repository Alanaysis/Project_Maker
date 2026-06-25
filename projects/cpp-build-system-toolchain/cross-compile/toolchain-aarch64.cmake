# ============================================================================
# AArch64 (ARM64) 交叉编译工具链文件
# 本文件配置 CMake 进行 AArch64 Linux 交叉编译
#
# 使用方法:
#   cmake -B build -DCMAKE_TOOLCHAIN_FILE=toolchain-aarch64.cmake
#
# 前置要求:
#   sudo apt-get install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
# ============================================================================

# 目标系统信息
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# 交叉编译器
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)

# 查找行为配置
set(CMAKE_FIND_ROOT_PATH /usr/aarch64-linux-gnu)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
