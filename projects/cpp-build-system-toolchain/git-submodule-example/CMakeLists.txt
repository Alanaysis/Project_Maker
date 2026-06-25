cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Git Submodule 示例
# 本文件展示如何使用 Git Submodule 管理第三方依赖
#
# 使用方法:
#   1. 添加子模块:
#      git submodule add https://github.com/fmtlib/fmt.git third_party/fmt
#      git submodule add https://github.com/google/googletest.git third_party/googletest
#
#   2. 初始化子模块:
#      git submodule update --init --recursive
#
#   3. 构建项目:
#      cmake -B build && cmake --build build
# ============================================================================

project(GitSubmoduleExample
    VERSION 1.0.0
    DESCRIPTION "Git Submodule 示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. 添加子模块
# ============================================================================
# 注意: 实际使用时需要先执行 git submodule add 命令

# fmt 库
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/fmt/CMakeLists.txt)
    add_subdirectory(third_party/fmt)
endif()

# Google Test
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/third_party/googletest/CMakeLists.txt)
    set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
    add_subdirectory(third_party/googletest)
endif()

# ============================================================================
# 2. 创建主程序
# ============================================================================
add_executable(submodule_demo src/submodule_demo.cpp)

if(TARGET fmt::fmt)
    target_link_libraries(submodule_demo PRIVATE fmt::fmt)
    target_compile_definitions(submodule_demo PRIVATE HAS_FMT)
endif()

# ============================================================================
# 3. 创建测试
# ============================================================================
if(TARGET GTest::gtest_main)
    add_executable(submodule_tests tests/test_main.cpp)
    target_link_libraries(submodule_tests PRIVATE GTest::gtest_main)
    enable_testing()
    add_test(NAME submodule_tests COMMAND submodule_tests)
endif()
