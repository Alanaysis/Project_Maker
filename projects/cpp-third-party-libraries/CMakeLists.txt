cmake_minimum_required(VERSION 3.15)
project(CppThirdPartyLibraries VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准设置
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 输出目录设置
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 编译选项
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    add_compile_options(-Wall -Wextra -Wpedantic)
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    add_compile_options(/W4)
endif()

# 构建类型设置
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# 选项定义
option(BUILD_CONTAINERS "Build container examples" ON)
option(BUILD_SERIALIZATION "Build serialization examples" ON)
option(BUILD_NETWORKING "Build networking examples" ON)
option(BUILD_CONCURRENCY "Build concurrency examples" ON)
option(BUILD_TESTING "Build testing examples" ON)
option(BUILD_LOGGING "Build logging examples" ON)
option(BUILD_MATH "Build math examples" ON)
option(BUILD_GRAPHICS "Build graphics examples" OFF)
option(BUILD_UTILS "Build utils examples" ON)
option(BUILD_BUILD_TOOLS "Build tool examples" ON)

# 查找依赖
find_package(Threads REQUIRED)

# 子目录
if(BUILD_CONTAINERS)
    message(STATUS "Building container examples")
    add_subdirectory(containers)
endif()

if(BUILD_SERIALIZATION)
    message(STATUS "Building serialization examples")
    add_subdirectory(serialization)
endif()

if(BUILD_NETWORKING)
    message(STATUS "Building networking examples")
    add_subdirectory(networking)
endif()

if(BUILD_CONCURRENCY)
    message(STATUS "Building concurrency examples")
    add_subdirectory(concurrency)
endif()

if(BUILD_TESTING)
    message(STATUS "Building testing examples")
    add_subdirectory(testing)
endif()

if(BUILD_LOGGING)
    message(STATUS "Building logging examples")
    add_subdirectory(logging)
endif()

if(BUILD_MATH)
    message(STATUS "Building math examples")
    add_subdirectory(math)
endif()

if(BUILD_GRAPHICS)
    message(STATUS "Building graphics examples")
    add_subdirectory(graphics)
endif()

if(BUILD_UTILS)
    message(STATUS "Building utils examples")
    add_subdirectory(utils)
endif()

if(BUILD_BUILD_TOOLS)
    message(STATUS "Building build tool examples")
    add_subdirectory(build)
endif()

# 安装规则
install(DIRECTORY ${CMAKE_SOURCE_DIR}/examples DESTINATION share/doc/${PROJECT_NAME})
install(FILES README.md DESTINATION share/doc/${PROJECT_NAME})

# 打印配置信息
message(STATUS "")
message(STATUS "=== C++ Third Party Libraries Configuration ===")
message(STATUS "C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "================================================")
message(STATUS "")