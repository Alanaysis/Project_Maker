cmake_minimum_required(VERSION 3.14)
project(MiniDB VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
add_compile_options(-Wall -Wextra -Wpedantic)

# Debug 模式选项
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    add_compile_options(-g -O0)
    add_definitions(-DDEBUG)
else()
    add_compile_options(-O2)
endif()

# Sanitizer 选项 (可选)
option(ENABLE_SANITIZER "Enable AddressSanitizer" OFF)
if(ENABLE_SANITIZER)
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address)
endif()

# 头文件目录
include_directories(${CMAKE_SOURCE_DIR}/include)

# ==================== 核心库 ====================

set(CORE_SOURCES
    src/core/status.cpp
    src/storage/disk_manager.cpp
    src/storage/buffer_pool.cpp
    src/storage/bplus_tree.cpp
    src/storage/table.cpp
    src/sql/tokenizer.cpp
    src/sql/parser.cpp
    src/sql/executor.cpp
    src/concurrency/transaction.cpp
    src/concurrency/lock_manager.cpp
)

# 创建静态库
add_library(minidb_core STATIC ${CORE_SOURCES})
target_include_directories(minidb_core PUBLIC ${CMAKE_SOURCE_DIR}/include)

# ==================== 测试 ====================

# 查找 Google Test
find_package(GTest QUIET)

if(GTest_FOUND)
    message(STATUS "Google Test found")

    # 测试源文件
    set(TEST_SOURCES
        tests/test_tokenizer.cpp
        tests/test_parser.cpp
        tests/test_disk_manager.cpp
        tests/test_buffer_pool.cpp
        tests/test_bplus_tree.cpp
        tests/test_table.cpp
        tests/test_lock_manager.cpp
    )

    add_executable(minidb_tests ${TEST_SOURCES})
    target_link_libraries(minidb_tests minidb_core GTest::gtest GTest::gtest_main)
else()
    message(STATUS "Google Test not found, building simple test runner")

    # 简单测试运行器
    add_executable(minidb_tests
        tests/simple_test.cpp
    )
    target_link_libraries(minidb_tests minidb_core)
endif()

# ==================== 示例 ====================

# 简单 CRUD 示例
add_executable(minidb_example examples/simple_crud.cpp)
target_link_libraries(minidb_example minidb_core)

# 并发访问示例
add_executable(minidb_concurrent examples/concurrent_access.cpp)
target_link_libraries(minidb_concurrent minidb_core pthread)

# ==================== 安装 ====================

install(TARGETS minidb_core
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib)

install(DIRECTORY include/ DESTINATION include)

# ==================== 打印信息 ====================

message(STATUS "")
message(STATUS "MiniDB Configuration:")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Sanitizer: ${ENABLE_SANITIZER}")
message(STATUS "")
