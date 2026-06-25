cmake_minimum_required(VERSION 3.14)
project(cpp-performance-optimization LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# 构建类型
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Release 优化选项
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O3 -march=native)
    add_definitions(-DNDEBUG)
endif()

# Debug 选项
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-O0 -g)
endif()

# LTO 选项
option(ENABLE_LTO "Enable Link-Time Optimization" OFF)
if(ENABLE_LTO)
    set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)
    message(STATUS "LTO enabled")
endif()

# Sanitizer 选项
option(ENABLE_SANITIZERS "Enable Address and UB Sanitizers" OFF)
if(ENABLE_SANITIZERS)
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address,undefined)
    message(STATUS "Sanitizers enabled")
endif()

# OpenMP 选项
option(USE_OPENMP "Enable OpenMP support" OFF)
if(USE_OPENMP)
    find_package(OpenMP)
    if(OpenMP_CXX_FOUND)
        add_compile_options(${OpenMP_CXX_FLAGS})
        message(STATUS "OpenMP enabled")
    endif()
endif()

# 线程库
find_package(Threads REQUIRED)

# 包含目录
include_directories(${PROJECT_SOURCE_DIR}/include)

# 子目录
add_subdirectory(src/memory)
add_subdirectory(src/compiler)
add_subdirectory(src/algorithm)
add_subdirectory(src/data_structure)
add_subdirectory(src/io)
add_subdirectory(src/concurrency)
add_subdirectory(src/tools)
add_subdirectory(src/case_studies)

# 信息输出
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")