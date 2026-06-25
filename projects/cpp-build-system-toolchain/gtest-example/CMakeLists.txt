cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Google Test 示例
# 本文件展示如何使用 Google Test 进行单元测试
# ============================================================================

project(GtestExample
    VERSION 1.0.0
    DESCRIPTION "Google Test 示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. 获取 Google Test
# ============================================================================
include(FetchContent)

FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)

# 设置 Google Test 选项
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(googletest)

# ============================================================================
# 2. 创建被测试的库
# ============================================================================
add_library(calculator STATIC
    src/calculator.cpp
)

target_include_directories(calculator PUBLIC include)

# ============================================================================
# 3. 创建测试程序
# ============================================================================
add_executable(calculator_tests
    tests/test_calculator.cpp
    tests/test_calculator_advanced.cpp
)

target_link_libraries(calculator_tests
    PRIVATE
        calculator
        GTest::gtest_main
)

# ============================================================================
# 4. 注册测试
# ============================================================================
enable_testing()

include(GoogleTest)
gtest_discover_tests(calculator_tests)
