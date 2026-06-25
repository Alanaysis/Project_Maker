cmake_minimum_required(VERSION 3.16)

# ============================================================================
# 代码覆盖率示例
# 本文件展示如何使用 gcov/lcov 进行代码覆盖率统计
#
# 使用方法:
#   cmake -B build -DENABLE_COVERAGE=ON
#   cmake --build build
#   cd build && ctest
#   lcov --capture --directory . --output-file coverage.info
#   genhtml coverage.info --output-directory coverage_report
# ============================================================================

project(CodeCoverage
    VERSION 1.0.0
    DESCRIPTION "代码覆盖率示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. 覆盖率选项
# ============================================================================
option(ENABLE_COVERAGE "Enable code coverage" OFF)

if(ENABLE_COVERAGE)
    message(STATUS "Code coverage enabled")
    add_compile_options(--coverage -fprofile-arcs -ftest-coverage)
    add_link_options(--coverage)
endif()

# ============================================================================
# 2. 创建库
# ============================================================================
add_library(string_lib STATIC
    src/string_lib.cpp
)
target_include_directories(string_lib PUBLIC include)

# ============================================================================
# 3. 创建测试
# ============================================================================
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_executable(coverage_tests
    tests/test_string_lib.cpp
)

target_link_libraries(coverage_tests
    PRIVATE
        string_lib
        GTest::gtest_main
)

# ============================================================================
# 4. 注册测试
# ============================================================================
enable_testing()
include(GoogleTest)
gtest_discover_tests(coverage_tests)

# ============================================================================
# 5. 覆盖率报告目标
# ============================================================================
if(ENABLE_COVERAGE)
    find_program(LCOV lcov)
    find_program(GENHTML genhtml)

    if(LCOV AND GENHTML)
        add_custom_target(coverage
            # 清除旧数据
            COMMAND ${LCOV} --directory . --zerocounters

            # 运行测试
            COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure

            # 收集覆盖率数据
            COMMAND ${LCOV} --directory . --capture --output-file coverage.info

            # 过滤系统文件
            COMMAND ${LCOV} --remove coverage.info
                '/usr/*'
                '*/test/*'
                '*/gtest/*'
                --output-file coverage_filtered.info

            # 生成 HTML 报告
            COMMAND ${GENHTML} coverage_filtered.info
                --output-directory ${CMAKE_BINARY_DIR}/coverage_report

            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
            COMMENT "Generating code coverage report"
        )
    endif()
endif()
