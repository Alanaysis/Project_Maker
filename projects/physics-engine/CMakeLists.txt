cmake_minimum_required(VERSION 3.14)
project(physics_engine VERSION 1.0.0 LANGUAGES CXX)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 选项
option(PHYSICS_ENGINE_BUILD_TESTS "Build tests" ON)
option(PHYSICS_ENGINE_BUILD_EXAMPLES "Build examples" ON)

# 源文件
set(SOURCES
    src/rigid_body.cpp
)

# 创建库
add_library(physics_engine ${SOURCES})

# 设置头文件目录
target_include_directories(physics_engine
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# 设置编译选项
target_compile_options(physics_engine PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:Clang>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
)

# 测试
if(PHYSICS_ENGINE_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# 示例
if(PHYSICS_ENGINE_BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

# 安装规则
include(GNUInstallDirs)

install(TARGETS physics_engine
    EXPORT physics_engine-targets
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)

install(DIRECTORY include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(EXPORT physics_engine-targets
    FILE physics_engine-config.cmake
    NAMESPACE physics_engine::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/physics_engine
)
