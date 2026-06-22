cmake_minimum_required(VERSION 3.16)

# 项目定义
project(heterogeneous-computing
    VERSION 0.1.0
    DESCRIPTION "CPU+GPU 异构计算框架"
    LANGUAGES CXX
)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 构建选项
option(ENABLE_CUDA "Enable CUDA support" OFF)
option(ENABLE_OPENCL "Enable OpenCL support" OFF)
option(BUILD_TESTS "Build tests" ON)
option(BUILD_EXAMPLES "Build examples" ON)

# 检测 CUDA
if(ENABLE_CUDA)
    find_package(CUDA QUIET)
    if(CUDA_FOUND)
        message(STATUS "CUDA found: ${CUDA_VERSION}")
        enable_language(CUDA)
        add_definitions(-DHETEROGENEOUS_ENABLE_CUDA)
    else()
        message(WARNING "CUDA not found, disabling CUDA support")
        set(ENABLE_CUDA OFF)
    endif()
endif()

# 检测 OpenCL
if(ENABLE_OPENCL)
    find_package(OpenCL QUIET)
    if(OpenCL_FOUND)
        message(STATUS "OpenCL found: ${OpenCL_VERSION}")
        add_definitions(-DHETEROGENEOUS_ENABLE_OPENCL)
    else()
        message(WARNING "OpenCL not found, disabling OpenCL support")
        set(ENABLE_OPENCL OFF)
    endif()
endif()

# 源文件
set(LIB_SOURCES
    src/task.cpp
    src/device.cpp
    src/memory.cpp
    src/scheduler.cpp
    src/executor.cpp
)

# 头文件
set(LIB_HEADERS
    include/heterogeneous/core.h
    include/heterogeneous/task.h
    include/heterogeneous/device.h
    include/heterogeneous/memory.h
    include/heterogeneous/scheduler.h
    include/heterogeneous/executor.h
    include/utils/timer.h
)

# 创建库
add_library(heterogeneous STATIC ${LIB_SOURCES})

# 设置包含目录
target_include_directories(heterogeneous
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# 链接依赖
target_link_libraries(heterogeneous
    PUBLIC
        Threads::Threads
)

# 查找线程库
find_package(Threads REQUIRED)

# CUDA 依赖
if(ENABLE_CUDA)
    target_link_libraries(heterogeneous
        PUBLIC
            ${CUDA_LIBRARIES}
    )
    target_include_directories(heterogeneous
        PUBLIC
            ${CUDA_INCLUDE_DIRS}
    )
endif()

# OpenCL 依赖
if(ENABLE_OPENCL)
    target_link_libraries(heterogeneous
        PUBLIC
            OpenCL::OpenCL
    )
endif()

# 设置编译选项
target_compile_options(heterogeneous PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:Clang>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
)

# 测试
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# 示例
if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

# 安装
install(TARGETS heterogeneous
    EXPORT heterogeneous-targets
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(DIRECTORY include/
    DESTINATION include
)

install(EXPORT heterogeneous-targets
    FILE heterogeneous-config.cmake
    NAMESPACE heterogeneous::
    DESTINATION lib/cmake/heterogeneous
)

# 打印配置信息
message(STATUS "=== Heterogeneous Computing Framework ===")
message(STATUS "Version: ${PROJECT_VERSION}")
message(STATUS "CUDA support: ${ENABLE_CUDA}")
message(STATUS "OpenCL support: ${ENABLE_OPENCL}")
message(STATUS "Build tests: ${BUILD_TESTS}")
message(STATUS "Build examples: ${BUILD_EXAMPLES}")
message(STATUS "==========================================")
