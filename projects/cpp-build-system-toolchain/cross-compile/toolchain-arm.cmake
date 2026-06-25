# ============================================================================
# ARM 交叉编译工具链文件
# 本文件配置 CMake 进行 ARM Linux 交叉编译
#
# 使用方法:
#   cmake -B build -DCMAKE_TOOLCHAIN_FILE=toolchain-arm.cmake
#
# 前置要求:
#   sudo apt-get install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf
# ============================================================================

# 目标系统信息
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR arm)

# 交叉编译器
set(CMAKE_C_COMPILER arm-linux-gnueabihf-gcc)
set(CMAKE_CXX_COMPILER arm-linux-gnueabihf-g++)

# sysroot（可选）
# set(CMAKE_SYSROOT /usr/arm-linux-gnueabihf)

# 查找行为配置
set(CMAKE_FIND_ROOT_PATH /usr/arm-linux-gnueabihf)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# ARM 特定编译选项
set(CMAKE_C_FLAGS_INIT "-march=armv7-a -mfloat-abi=hard -mfpu=neon")
set(CMAKE_CXX_FLAGS_INIT "-march=armv7-a -mfloat-abi=hard -mfpu=neon")
